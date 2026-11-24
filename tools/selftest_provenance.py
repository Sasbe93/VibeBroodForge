"""Self-test for the provenance record (tools/provenance.py selftest).

Maps (.scx) and campaign folders: log prompts, build (through the real writers' hooks), read back, simulate a human
edit in an editor (terrain byte, trigger text, an extra unit), detect it, record it, rebuild over it.
Optional real map: VBF_SELFTEST_SCX = path of an existing map (copied, never modified)."""
import os, sys, json, struct, shutil, tempfile
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, 'lib'))
import forge_provenance as P

FAILS = []
def ok(cond, msg):
    print(('  ok   ' if cond else '  FAIL ') + msg)
    if not cond: FAILS.append(msg)

KW = dict(agent='Cursor', agent_version='2.1.0', model='test-model', model_version='2026-11')

def chk_min(units=1):
    W = H = 64
    sec = [(b'VER ', struct.pack('<H', 205)), (b'DIM ', struct.pack('<HH', W, H)), (b'ERA ', struct.pack('<H', 0)),
           (b'MTXM', b'\x10\x00' * (W * H)), (b'UNIT', b''.join(struct.pack('<IHHHHHHBB', i, 100 + 32 * i, 100, 0, 0, 0, 0, 0, 0) + b'\0' * 18 for i in range(units))),
           (b'TRIG', b'\0' * 2400), (b'STR ', struct.pack('<HH', 1, 4) + b'\0')]
    return b''.join(k + struct.pack('<I', len(v)) + v for k, v in sec)

def build_bw(path, chk):
    """the same steps as sclib.Map.save: hook_bw, then the MPQ with CHK + JSON file"""
    from eudplib.bindings._rust import mpqapi
    chk2, js = P.hook_bw(path, chk, {})
    t = path + '.chk'; open(t, 'wb').write(chk2); open(t + '.p', 'wb').write(js)
    if os.path.exists(path): os.remove(path)
    m = mpqapi.MPQ.create(path, 3, 64); m.add_file(P.BW_CHK, t); m.add_file(P.BW_MPQ_PATH, t + '.p'); m.compact(); del m
    os.remove(t); os.remove(t + '.p')

def edit_bw(path):
    chk, other = P.read_bw(path)
    secs = P.chk_sections(chk); out = b''
    for k, v in secs:
        if k == b'MTXM': v = bytearray(v); v[2 * (40 * 64 + 40)] = 0x22; v = bytes(v)
        if k == b'UNIT': v = v + struct.pack('<IHHHHHHBB', 99, 500, 500, 7, 0, 0, 0, 0, 0) + b'\0' * 18
        out += k + struct.pack('<I', len(v)) + v
    rec, _ = P.record_from_bw(chk, other)
    P.write_bw(path, out, other, rec)   # keeps the old record = what an editor that keeps VMFP would leave

def test_bw(d):
    print('.scx')
    m = os.path.join(d, 'T.scx')
    P.add_prompt([m], 'Make a BW rescue mission', **dict(KW, agent='Grok Bot', agent_version='1.0'))
    build_bw(m, chk_min())
    rec, cur, loc = P.read_map(m)
    ok(rec and loc.startswith('CHK section'), 'record readable from ' + str(loc))
    ok(rec['events'][-1]['tools'].get('tool') == 'VibeBroodForge' and rec['events'][-1]['tools']['VibeBroodForge'] not in (None, 'unknown'), 'VibeBroodForge version recorded')
    ok(P.check(m)[0] == 'unchanged', 'fresh build: no human edit')
    edit_bw(m)
    st, diff = P.check(m)
    ok(st == 'human_edit' and 'terrain' in diff and 'units' in diff, 'human edit detected: ' + P.describe_diff(diff))
    ok('7+1' in diff.get('units', ''), 'unit diff names the added unit type (7 = SCV)')
    P.check(m, record=True); ok(P.check(m)[0] == 'unchanged', 'human edit recorded')
    # editor dropped the CHK section but kept the MPQ file
    chk, other = P.read_bw(m)
    stripped = b''.join(k + struct.pack('<I', len(v)) + v for k, v in P.chk_sections(chk) if k != P.BW_SECTION)
    from eudplib.bindings._rust import mpqapi
    t = m + '.c'; open(t, 'wb').write(stripped); j = m + '.j'; open(j, 'wb').write(other[P.BW_MPQ_PATH]); os.remove(m)
    q = mpqapi.MPQ.create(m, 3, 64); q.add_file(P.BW_CHK, t); q.add_file(P.BW_MPQ_PATH, j); q.compact(); del q
    rec, cur, loc = P.read_map(m)
    ok(rec and 'MPQ file' in loc, 'fallback: record read from the MPQ file when the CHK section is gone')
    # campaign folder
    shutil.copy(m, os.path.join(d, 'T2.scx'))
    crec, out = P.campaign_bw(d)
    ok(os.path.exists(out) and len(crec['maps']) == 2, 'BW campaign summary written: ' + os.path.basename(out))

def test_real(d):
    for env in ('VBF_SELFTEST_SCX',):
        src = os.environ.get(env)
        if not src: continue
        print('real map', os.path.basename(src))
        m = os.path.join(d, 'real' + os.path.splitext(src)[1]); shutil.copy(src, m)
        P.add_prompt([m], 'stamp test', **KW)
        before = P.read_map(m)[1]
        P.stamp(m)
        rec, cur, loc = P.read_map(m)
        ok(rec is not None and P.check(m)[0] == 'unchanged', 'stamped and read back from ' + loc)
        ok(cur['sha'] == before['sha'], 'stamping changed no map content (fingerprint identical)')

def main(keep=False):
    d = tempfile.mkdtemp(prefix='prov_selftest_')
    try:
        test_bw(d); test_real(d)
    finally:
        if keep: print('kept', d)
        else: shutil.rmtree(d, ignore_errors=True)
    print('provenance selftest: %s' % ('OK' if not FAILS else '%d FAIL' % len(FAILS)))
    return 1 if FAILS else 0

if __name__ == '__main__': sys.exit(main('--keep' in sys.argv))
