"""forge_provenance: hidden, externally readable provenance record for VibeBroodForge maps and campaign folders.

What it records (format "vibeforge-provenance/1", JSON; the format id is shared with the sister project and
with maps built before the split of the former VibeModForge repository):
  - every prompt that went into a map or campaign (count, text or redacted hash, time),
  - the agent (Cursor, Grok Bot, Claude Code, Codex, Dots, ...) and its version, the AI model and its version,
  - the tool and its version (VibeBroodForge, StarCraft: Brood War) plus the git commit of the tools,
  - build events (prompt edits, written by our tools on every build or stamp),
  - human edits made in an editor (ScmDraft, StarEdit), DETECTED by a content fingerprint:
    editors do not log edits, so we can only see THAT parts changed since the last tool save, not who or why.

Where it is stored (see docs/provenance.md for the editor-survival evidence):
  BW  .scx/.scm  CHK section 'VMFP' (format id kept from before the split) inside staredit\\scenario.chk plus MPQ file vibeforge\\provenance.json.
  BW campaign    vibeforge_campaign_provenance.json in the campaign folder (BW has no campaign container).
The working ledger (all prompts, also before the first build) is a sidecar file <map>.provenance.json next to the
map in output/ (git-ignored).
"""
import os, sys, json, hashlib, struct, time, re, subprocess, uuid, datetime, shutil, tempfile

FORMAT = 'vibeforge-provenance/1'
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..', '..'))

BW_SECTION = b'VMFP'
BW_MPQ_PATH = 'vibeforge\\provenance.json'
BW_CHK = 'staredit\\scenario.chk'
TOOL = 'VibeBroodForge'   # this repository; records written before the split name the former umbrella tool too
KNOWN_AGENTS = ['Cursor', 'Grok Bot', 'Claude Code', 'Codex', 'Dots', 'Copilot', 'Aider', 'Windsurf', 'Gemini CLI', 'human', 'other']

# ---------------------------------------------------------------- versions
def _read_version(rel):
    p = os.path.join(ROOT, rel)
    try: return open(p, encoding='utf8').read().strip()
    except OSError: return 'unknown'

def tool_versions():
    v = {'tool': TOOL, TOOL: _read_version('VERSION')}
    try:
        c = subprocess.run(['git', '-C', ROOT, 'rev-parse', '--short=12', 'HEAD'], capture_output=True, text=True, timeout=5)
        if c.returncode == 0:
            v['commit'] = c.stdout.strip()
            d = subprocess.run(['git', '-C', ROOT, 'status', '--porcelain', '--untracked-files=no'], capture_output=True, text=True, timeout=5)
            v['dirty'] = bool(d.stdout.strip())
    except Exception: pass
    return v

def now(): return datetime.datetime.now(datetime.timezone.utc).replace(microsecond=0).isoformat()

# ---------------------------------------------------------------- privacy
_SCRUB = [
    (re.compile(r'[\w.+-]+@[\w-]+\.[\w.-]+'), '[email]'),
    (re.compile(r'(?i)\b(ghp|gho|github_pat|sk|xox[abp]|AKIA)[-_A-Za-z0-9]{12,}'), '[token]'),
    (re.compile(r'(?i)[A-Z]:\\Users\\[^\\\s]+'), r'C:\\Users\\[user]'),
    (re.compile(r'/(home|Users)/[^/\s]+'), r'/\1/[user]'),
]
def scrub(text):
    for rx, rep in _SCRUB: text = rx.sub(rep, text)
    return text

def sha(b):
    if isinstance(b, str): b = b.encode('utf8')
    return hashlib.sha256(b).hexdigest()

# ---------------------------------------------------------------- fingerprints
def _blocks(points, w, h, size, getter):
    """hash per size x size block of a w x h grid -> {'bx,by': 8 hex}"""
    out = {}
    for by in range(0, h, size):
        for bx in range(0, w, size):
            hh = hashlib.sha256()
            for y in range(by, min(h, by + size)):
                hh.update(getter(y * w + bx, min(w, bx + size) - bx))
            out['%d,%d' % (bx // size, by // size)] = hh.hexdigest()[:8]
    return out

BW_PARTS = {
    'terrain': ['MTXM', 'TILE', 'ISOM', 'DIM ', 'ERA '],
    'units': ['UNIT'], 'doodads': ['DD2 ', 'THG2'], 'triggers': ['TRIG'], 'briefing': ['MBRF'],
    'strings': ['STR ', 'STRx'], 'locations': ['MRGN'], 'players': ['OWNR', 'SIDE', 'FORC', 'COLR', 'CRGB', 'IOWN'],
    'scenario': ['SPRP'], 'settings': ['UNIS', 'UNIx', 'PUNI', 'UPGS', 'UPGx', 'TECS', 'TECx', 'PTEC', 'PTEx',
                                         'PUPG', 'PUPx', 'UPRP', 'UPUS', 'WAV ', 'SWNM', 'MASK'],
}
BW_SKIP = {'VER ', 'IVER', 'IVE2', 'TYPE', 'VCOD', BW_SECTION.decode()}

def chk_sections(chk):
    out = []; i = 0
    while i + 8 <= len(chk):
        k = chk[i:i + 4]; n = struct.unpack_from('<i', chk, i + 4)[0]
        if n < 0 or i + 8 + n > len(chk): out.append((k, chk[i + 8:])); break
        out.append((k, chk[i + 8:i + 8 + n])); i += 8 + n
    return out

def fingerprint_bw(chk, wavs=None):
    secs = {}
    for k, v in chk_sections(chk):
        secs[k.decode('latin1')] = v   # later wins, like the game
    parts = {}
    for name, v in secs.items():
        if name in BW_SKIP: continue
        part = next((p for p, l in BW_PARTS.items() if name in l), 'other')
        parts.setdefault(part, {'files': {}})['files'][name] = sha(v)
    if 'MTXM' in secs and 'DIM ' in secs:
        w, h = struct.unpack('<HH', secs['DIM '][:4]); m = secs['MTXM']
        parts['terrain']['blocks'] = _blocks(m, w, h, 32, lambda i, n: m[2 * i:2 * (i + n)])
        parts['terrain']['info'] = {'w': w, 'h': h}
    if 'UNIT' in secs:
        u = secs['UNIT']; cnt = {}
        for i in range(0, len(u) // 36 * 36, 36):
            t = struct.unpack_from('<H', u, i + 8)[0]; cnt[str(t)] = cnt.get(str(t), 0) + 1
        parts['units']['info'] = {'count': len(u) // 36, 'by_type': cnt}
    if 'TRIG' in secs: parts['triggers']['info'] = {'count': len(secs['TRIG']) // 2400}
    if 'MBRF' in secs: parts['briefing']['info'] = {'count': len(secs['MBRF']) // 2400}
    if wavs: parts['sounds'] = {'files': {k: sha(v) for k, v in sorted(wavs.items())}}
    for p in parts.values(): p['sha'] = sha(json.dumps(p['files'], sort_keys=True))
    return {'scheme': 'bw/1', 'parts': parts, 'sha': sha(json.dumps({k: v['sha'] for k, v in parts.items()}, sort_keys=True))}

def diff_fingerprints(old, new):
    """-> {part: description} for every changed part (empty = unchanged)"""
    out = {}
    op, np_ = (old or {}).get('parts', {}), (new or {}).get('parts', {})
    for part in sorted(set(op) | set(np_)):
        a, b = op.get(part), np_.get(part)
        if a and b and a.get('sha') == b.get('sha'): continue
        if not a: out[part] = 'added'; continue
        if not b: out[part] = 'removed'; continue
        desc = []
        fa, fb = a.get('files', {}), b.get('files', {})
        ch = [f for f in sorted(set(fa) | set(fb)) if fa.get(f) != fb.get(f)]
        desc.append('changed: ' + ', '.join(ch[:8]) + (' ...' if len(ch) > 8 else ''))
        ba, bb = a.get('blocks'), b.get('blocks')
        if ba and bb and a.get('info', {}).get('w') == b.get('info', {}).get('w'):
            cb = sorted(k for k in bb if ba.get(k) != bb.get(k))
            desc.append('%d of %d 32x32 terrain blocks changed%s' % (len(cb), len(bb), (' (' + ' '.join(cb[:12]) + ')') if cb else ''))
        ia, ib = a.get('info', {}), b.get('info', {})
        for key in ('count', 'functions'):
            if key in ia and key in ib and ia[key] != ib[key]: desc.append('%s %s -> %s' % (key, ia[key], ib[key]))
        ta, tb = ia.get('by_type'), ib.get('by_type')
        if ta is not None and tb is not None:
            d = {t: tb.get(t, 0) - ta.get(t, 0) for t in set(ta) | set(tb) if tb.get(t, 0) != ta.get(t, 0)}
            if d: desc.append('unit types ' + ' '.join('%s%+d' % (t, n) for t, n in sorted(d.items())))
        out[part] = '; '.join(desc)
    return out

def describe_diff(diff):
    if not diff: return 'no change'
    if set(diff) == {'derived'}: return DERIVED_NOTE
    return ' | '.join('%s: %s' % (k, v) for k, v in diff.items())

# ---------------------------------------------------------------- BW MPQ IO
def _mpqapi():
    from eudplib.bindings._rust import mpqapi
    return mpqapi

def read_bw(path):
    """-> (chk bytes, {archive name: bytes} of the other files we could enumerate)"""
    M = _mpqapi(); m = M.MPQ.open(path)
    chk = bytes(m.extract_file(BW_CHK)); other = {}
    names = []
    try: names = list(m.get_file_names_from_listfile())
    except Exception: pass
    # without a listfile, recover WAV names from the strings the WAV section points at
    secs = dict((k.decode('latin1'), v) for k, v in chk_sections(chk))
    strs = _bw_strings(secs)
    for sid in struct.unpack('<%dI' % (len(secs.get('WAV ', b'')) // 4), secs.get('WAV ', b'')):
        if sid and sid <= len(strs): names.append(strs[sid - 1])
    names.append(BW_MPQ_PATH)
    for n in names:
        if not n or n.lower() == BW_CHK or n in other or n.startswith('('): continue
        try: other[n] = bytes(m.extract_file(n))
        except Exception: pass
    del m
    return chk, other

def _bw_strings(secs):
    if 'STRx' in secs:
        s = secs['STRx']; n = struct.unpack_from('<I', s, 0)[0]; offs = struct.unpack_from('<%dI' % n, s, 4)
    elif 'STR ' in secs:
        s = secs['STR ']; n = struct.unpack_from('<H', s, 0)[0]; offs = struct.unpack_from('<%dH' % n, s, 2)
    else: return []
    out = []
    for o in offs:
        e = s.find(b'\0', o); out.append(s[o:e if e >= 0 else len(s)].decode('latin1'))
    return out

def record_from_bw(chk, other):
    for k, v in reversed(chk_sections(chk)):
        if k == BW_SECTION:
            try: return json.loads(v.decode('utf8')), 'chk'
            except Exception: pass
    if BW_MPQ_PATH in other:
        try: return json.loads(other[BW_MPQ_PATH].decode('utf8')), 'mpq'
        except Exception: pass
    return None, None

def chk_with_record(chk, record):
    data = json.dumps(record, separators=(',', ':'), ensure_ascii=False).encode('utf8')
    out = b''.join(k + struct.pack('<I', len(v)) + v for k, v in chk_sections(chk) if k != BW_SECTION)
    return out + BW_SECTION + struct.pack('<I', len(data)) + data

def write_bw(path, chk, other, record):
    M = _mpqapi()
    other = {k: v for k, v in other.items() if k != BW_MPQ_PATH}
    tmpd = tempfile.mkdtemp(prefix='prov_')
    try:
        newchk = chk_with_record(chk, record)
        fc = os.path.join(tmpd, 'scenario.chk'); open(fc, 'wb').write(newchk)
        fj = os.path.join(tmpd, 'prov.json'); open(fj, 'wb').write(json.dumps(record, indent=1, ensure_ascii=False).encode('utf8'))
        out = path + '.provtmp'
        if os.path.exists(out): os.remove(out)
        m = M.MPQ.create(out, 3, 64 + 2 * len(other))
        m.add_file(BW_CHK, fc)
        for i, (k, v) in enumerate(other.items()):
            f = os.path.join(tmpd, 'f%d' % i); open(f, 'wb').write(v); m.add_file(k, f)
        m.add_file(BW_MPQ_PATH, fj)
        m.compact(); del m
        os.replace(out, path)
    finally: shutil.rmtree(tmpd, ignore_errors=True)

# ---------------------------------------------------------------- ledger + record
def game_of(path):
    e = os.path.splitext(path)[1].lower()
    if e in ('.scx', '.scm'): return 'bw'
    raise ValueError('unknown map type: ' + path)

def ledger_path(map_path): return map_path + '.provenance.json'

def new_record(map_path, game=None):
    game = game or game_of(map_path)
    return {'format': FORMAT, 'kind': 'map', 'game': game,
            'name': os.path.splitext(os.path.basename(map_path))[0], 'record_id': str(uuid.uuid4()),
            'created': now(), 'prompts': [], 'events': [], 'fingerprint': None, 'summary': {}}

def load_ledger(map_path):
    p = ledger_path(map_path)
    if os.path.exists(p): return json.load(open(p, encoding='utf8'))
    return None

def save_ledger(map_path, rec):
    summarize(rec)
    d = os.path.dirname(os.path.abspath(map_path)); os.makedirs(d, exist_ok=True)
    tmp = ledger_path(map_path) + '.tmp'
    json.dump(rec, open(tmp, 'w', encoding='utf8'), indent=1, ensure_ascii=False); os.replace(tmp, ledger_path(map_path))

def _tool_label(tools):
    """'VibeBroodForge 0.10.0' for records of this repository; records written before the split (formerly VibeModForge,
    one umbrella repository) list the umbrella version and both game parts"""
    if tools.get('tool'): return '%s %s' % (tools['tool'], tools.get(tools['tool'], '?'))
    legacy = [k for k in ('VibeModForge', 'VibeBroodForge', 'VibeWarForge') if k in tools]
    return ' / '.join('%s %s' % (k, tools[k]) for k in legacy) or 'unknown'

def summarize(rec):
    pr = rec.get('prompts', []); ev = rec.get('events', [])
    rec['summary'] = {
        'prompt_count': len({p['id'] for p in pr}),
        'build_count': sum(1 for e in ev if e['type'] == 'build'),
        'human_edit_count': sum(1 for e in ev if e['type'] == 'human_edit'),
        'agents': sorted({'%s %s' % (p.get('agent'), p.get('agent_version') or '?') for p in pr}),
        'models': sorted({('%s %s' % (p.get('model'), p.get('model_version') or '')).strip() for p in pr}),
        'tool_versions_used': sorted({_tool_label(e.get('tools', {})) for e in ev if e['type'] in ('build', 'stamp')}),
        'first': (pr[0]['time'] if pr else rec.get('created')), 'last_build': next((e['time'] for e in reversed(ev) if e['type'] == 'build'), None),
    }
    if rec.get('kind') == 'campaign' and rec.get('maps'):
        ids = {p['id'] for p in pr}
        for m in rec['maps']: ids |= set(m.get('prompt_ids', []))
        rec['summary']['prompt_count_incl_maps'] = len(ids)
    return rec

def make_prompt(text, agent, agent_version, model, model_version=None, redact=False, source='user', tools=None):
    if not agent or not model: raise ValueError('agent and model are required (use "unknown" only if the agent really cannot tell)')
    if agent not in KNOWN_AGENTS and not agent.startswith('other:'):
        print('note: agent %r is not in the known list %s; stored as given' % (agent, KNOWN_AGENTS))
    p = {'id': 'p-' + sha('%s|%s' % (text, time.time_ns()))[:16], 'time': now(), 'source': source,
         'agent': agent, 'agent_version': agent_version or 'unknown', 'model': model, 'model_version': model_version or '',
         'tools': tools or tool_versions(), 'text_sha256': sha(text), 'chars': len(text)}
    if redact: p['text'] = None; p['redacted'] = 'full'
    else:
        s = scrub(text); p['text'] = s
        if s != text: p['redacted'] = 'scrubbed'
    return p

def add_prompt(map_paths, text, **kw):
    p = make_prompt(text, **kw)
    for mp in map_paths:
        rec = load_ledger(mp) or new_record(mp)
        rec['prompts'].append(dict(p, n=len(rec['prompts']) + 1))
        save_ledger(mp, rec)
    return p

def read_map(path):
    """-> (record or None, current fingerprint, location string)"""
    game_of(path)
    chk, other = read_bw(path)
    rec, where = record_from_bw(chk, other)
    wavs = {k: v for k, v in other.items() if k != BW_MPQ_PATH}
    loc = {'chk': 'CHK section VMFP', 'mpq': 'MPQ file ' + BW_MPQ_PATH + ' (CHK section lost)'}.get(where)
    return rec, fingerprint_bw(chk, wavs), loc

def _human_edit_event(rec, cur_fp, how):
    diff = diff_fingerprints(rec.get('fingerprint'), cur_fp)
    return {'type': 'human_edit', 'time': now(), 'detected_by': how, 'tools': tool_versions(),
            'parts': diff, 'summary': describe_diff(diff),
            'only_derived': set(diff) == {'derived'},
            'note': 'detected by fingerprint diff; the editor does not record who edited or exactly what'}

def _merge_ledger(rec, led):
    """records from map and ledger: union of prompts and events by id/time"""
    if not led: return rec
    if not rec: return led
    ids = {p['id'] for p in rec['prompts']}
    for p in led['prompts']:
        if p['id'] not in ids: rec['prompts'].append(p); ids.add(p['id'])
    keys = {(e['type'], e['time']) for e in rec['events']}
    for e in led['events']:
        if (e['type'], e['time']) not in keys: rec['events'].append(e)
    rec['events'].sort(key=lambda e: e['time'])
    return rec

def build_record(map_path, fp, existing=None, event='build', note=None):
    """called by the build writers: ledger + existing map record + a new build event with the fingerprint"""
    led = load_ledger(map_path)
    rec = _merge_ledger(existing, led) or new_record(map_path)
    if existing and existing.get('fingerprint') and existing['fingerprint'].get('sha') != (existing.get('_current_fp') or {}).get('sha') and existing.get('_current_fp'):
        rec['events'].append(_human_edit_event(existing, existing['_current_fp'], 'build (map on disk differed from its last tool save)'))
    rec.pop('_current_fp', None)
    last_n = max([e.get('prompt_n_upto', 0) for e in rec['events'] if e['type'] in ('build', 'stamp')] or [0])
    new_ids = [p['id'] for p in rec['prompts'] if p.get('n', 0) > last_n]
    ev = {'type': event, 'time': now(), 'tools': tool_versions(), 'prompt_ids': new_ids,
          'prompt_n_upto': len(rec['prompts']), 'fingerprint_sha': fp['sha']}
    if note: ev['note'] = note
    if not new_ids and event == 'build': ev['warning'] = 'no prompt logged since the previous build (tools/provenance.py add-prompt)'
    rec['events'].append(ev)
    rec['fingerprint'] = fp
    summarize(rec)
    save_ledger(map_path, rec)
    return rec

# ---------------------------------------------------------------- hooks used by the writers
def enabled(): return os.environ.get('VIBEFORGE_PROVENANCE', '1') != '0'

def _existing_on_disk(path):
    if not os.path.exists(path): return None
    try:
        rec, cur, _ = read_map(path)
        if rec: rec['_current_fp'] = cur
        return rec
    except Exception as e:
        print('provenance: could not read the previous map %s (%r)' % (path, e)); return None

def hook_bw(path, chk, wavs):
    """sclib.Map.save calls this: returns (chk with VMFP section, json bytes for the MPQ file)"""
    if not enabled(): return chk, None
    prev = _existing_on_disk(path)
    if prev and prev.get('_current_fp') and prev.get('fingerprint') and prev['fingerprint']['sha'] != prev['_current_fp']['sha']:
        bk = path + '.human-edited-%s%s' % (time.strftime('%Y%m%d-%H%M%S'), os.path.splitext(path)[1])
        shutil.copy2(path, bk)
        print('WARNING provenance: %s was changed outside the tools since its last build. Backup: %s' % (path, bk))
    fp = fingerprint_bw(chk, wavs)
    rec = build_record(path, fp, prev)
    return chk_with_record(chk, rec), json.dumps(rec, indent=1, ensure_ascii=False).encode('utf8')

# ---------------------------------------------------------------- operations on existing maps
def stamp(path, note=None):
    """embed/refresh the record in an existing map without rebuilding it (maps from other tools or fix copies)"""
    game_of(path)
    chk, other = read_bw(path)
    prev, _ = record_from_bw(chk, other)
    wavs = {k: v for k, v in other.items() if k != BW_MPQ_PATH}
    cur = fingerprint_bw(chk, wavs)
    if prev: prev['_current_fp'] = cur
    rec = build_record(path, cur, prev, event='stamp', note=note)
    write_bw(path, chk, other, rec)
    return rec

def check(path, record=False):
    """detect human edits: -> (status, diff). With record=True a human_edit event is appended to the map and ledger."""
    rec, cur, loc = read_map(path)
    if not rec: return 'no_record', {}
    diff = diff_fingerprints(rec.get('fingerprint'), cur)
    if not diff: return 'unchanged', {}
    if record:
        ev = _human_edit_event(rec, cur, 'tools/provenance.py check --record')
        rec = _merge_ledger(rec, load_ledger(path))
        rec['events'].append(ev); rec['fingerprint'] = cur
        summarize(rec); save_ledger(path, rec)
        chk, other = read_bw(path); write_bw(path, chk, other, rec)
    return 'human_edit', diff

def campaign_bw(folder, out=None):
    """BW has no campaign container: write vibeforge_campaign_provenance.json next to the missions"""
    maps = []
    for f in sorted(os.listdir(folder)):
        if not f.lower().endswith(('.scx', '.scm')): continue
        try: r, cur, loc = read_map(os.path.join(folder, f))
        except Exception: r = None
        if r:
            summarize(r)
            maps.append({'file': f, 'name': r.get('name'), 'record_id': r.get('record_id'), 'prompt_ids': [p['id'] for p in r['prompts']],
                         'edited_since_last_build': bool(diff_fingerprints(r.get('fingerprint'), cur)),
                         **{k: r['summary'][k] for k in ('prompt_count', 'build_count', 'human_edit_count')}})
        else: maps.append({'file': f, 'record': None})
    out = out or os.path.join(folder, 'vibeforge_campaign_provenance.json')
    camp_ledger = os.path.join(folder, 'campaign.provenance.json')
    rec = json.load(open(camp_ledger, encoding='utf8')) if os.path.exists(camp_ledger) else new_record(os.path.join(folder, 'campaign'), 'bw')
    rec['kind'] = 'campaign'; rec['name'] = os.path.basename(os.path.abspath(folder)); rec['maps'] = maps
    rec['tools_at_summary'] = tool_versions(); summarize(rec)
    json.dump(rec, open(out, 'w', encoding='utf8'), indent=1, ensure_ascii=False)
    return rec, out
