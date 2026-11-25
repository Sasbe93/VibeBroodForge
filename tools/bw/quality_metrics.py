"""Quality metrics for a StarCraft: Brood War campaign mission, compared with the reference band in docs/quality-bar.md.

The predelivery check finds known mistakes; it does not measure how rich a map is. This tool measures what a player
sees and feels at once (terrain variety, dressing, ramps, scripted content, voiced lines, waves) and compares it with
the band measured on reference missions built with this repository. Below the band is a WARN: a prompt to look at the
map again, not proof of bad quality. A map far below the band in several rows is not delivery quality, and
tools/deliver.py refuses it unless the design note explains why (QUALITY_BAND_OK: <reason>).

Copied triggers count once (dedupe: same actions apart from switches, waits, comments, locations and strings), and
a WARN appears when half of the rows or more sit within 10 % of the band minimum (built for the metric).

usage: python3 tools/bw/quality_metrics.py MAP.scx [MAP2.scx ...] [--json]
Run from the repository root. Needs the tileset files (docs/bw-terrain-setup.md). Read-only: the map is never changed.
"""
import sys, os, json, struct, collections
ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..'))
os.chdir(ROOT); sys.path.insert(0, 'tools/bw'); sys.path.insert(0, 'tools/lib/bw')
import numpy as np
from scipy import ndimage as nd
import check_story_delivery as C, resback, base_elevation as BE

# Reference band (min_ok, typical) measured on three campaign missions built with this repository (Badlands and
# Desert, 128x128): M6 Sluice Gates, M7 The Poisoned Well, BK6 The Hollow Crowns. Minimum = what the references
# reach (BK6 is below on doodad types), typical = their median. Keep this table and docs/quality-bar.md in sync.
BAND = {
    'ground_types_used':      (5, 6),
    'distinct_doodad_types':  (30, 44),
    'ramp_groups':            (3, 8),
    'triggers':               (80, 91),
    'trigger_actions':        (700, 747),
    'transmissions':          (20, 25),
    'briefing_voice_lines':   (5, 6),
    'spawn_actions':          (100, 160),
    'order_actions':          (80, 106),
}
INFO_ONLY = ('copied_triggers', 'doodad_tiles_per_1k', 'placed_doodads', 'elevation_levels', 'walkable_share', 'objective_updates', 'preplaced_units', 'computer_players', 'ai_script_runs', 'map_size')
# trigger action ids (StarEdit): 7 Transmission, 12 Set Mission Objectives, 15/16 Run AI Script (at Location),
# 44 Create Unit, 46 Order; briefing action ids: 2 Play WAV, 8 Transmission
A_TRANS, A_OBJ, A_AI, A_AI_LOC, A_CREATE, A_ORDER = 7, 12, 15, 16, 44, 46
B_WAV, B_TRANS = 2, 8


def terrain(S, W, H):
    """-> (flat terrain types covering >= 0.5% of the map, tiles that belong to a tile doodad, tile doodad ids, tileset).
    Flat type = CV5 group whose four edges are the same type; tile doodad = CV5 group of type 1 with a doodad id."""
    era = struct.unpack('<H', S['ERA '][:2])[0] & 7
    cv5 = open(resback.TS + resback.ERA[era] + '.cv5', 'rb').read()
    mt = np.array(struct.unpack(f'<{W * H}H', (S.get('MTXM') or S['TILE'])[:2 * W * H]))
    cnt = collections.Counter(); dtiles = 0; dids = set()
    for g, n in zip(*np.unique(mt >> 4, return_counts=True)):
        if g * 52 + 18 > len(cv5): continue
        hd = struct.unpack_from('<9H', cv5, int(g) * 52)
        if hd[0] == 1 and hd[6]: dtiles += int(n); dids.add(hd[6])
        elif hd[0] != 1 and hd[2] == hd[3] == hd[4] == hd[5]: cnt[hd[2]] += int(n)
    return sum(1 for v in cnt.values() if v >= 0.005 * W * H), dtiles, dids, resback.ERA[era]


def level_crossings(h, w):
    """walkable places where the ground level changes (ramps and slopes): connected groups of at least 4 tiles"""
    H, W = h.shape; ch = np.zeros((H, W), bool)
    for dy, dx in ((0, 1), (1, 0)):
        a = w[:H - dy, :W - dx] & w[dy:, dx:] & (h[:H - dy, :W - dx] != h[dy:, dx:]); ch[:H - dy, :W - dx] |= a; ch[dy:, dx:] |= a
    lab, n = nd.label(ch, structure=np.ones((3, 3)))
    return sum(1 for s in (nd.sum(ch, lab, range(1, n + 1)) if n else []) if s >= 4)


MASKED = {4, 13, 47}       # Wait, Set Switch, Comment: differ between copies without changing what the player sees
FLOOR_MARGIN = 1.10        # a value within 10 % above the band minimum sits 'on the floor'


def dedupe(T):
    """drop copies: a trigger whose actions (type, unit, player, count; switches, waits, comments and locations
    ignored; a different text line is a different trigger) repeat an earlier trigger with 3 or more such actions counts once (t1031: 34 copies of one wave
    trigger lifted the trigger, spawn and order rows to the band floor)"""
    seen = set(); out = []; copies = 0
    for c, al, own in T:
        sig = tuple((a[26], struct.unpack_from('<H', a, 24)[0], struct.unpack_from('<I', a, 16)[0], a[27],
                     struct.unpack_from('<I', a, 4)[0] if a[26] in (7, 9, 12) else 0) for a in al if a[26] not in MASKED)
        if len(sig) >= 3 and sig in seen: copies += 1; continue
        seen.add(sig); out.append((c, al, own))
    return out, copies


def measure(path):
    S = C._sections(path)
    W, H = struct.unpack('<HH', S['DIM '][:4]); tiles = W * H
    T0 = C._trigs(S.get('TRIG', b''))
    try:                                      # triggers that can only run after a hard victory do not count (review t1036)
        import opening_review as _O; _tv, _dead = _O.dead_triggers(path)
        T0 = [t for i, t in enumerate(T0) if i not in _dead]
    except Exception: pass
    T, copies = dedupe(T0); B = C._trigs(S.get('MBRF', b''))
    acts = collections.Counter(a[26] for _, al, _ in T for a in al)
    bacts = collections.Counter(a[26] for _, al, _ in B for a in al)
    dd = S.get('DD2 ', b''); ndd = len(dd) // 8
    gt, dtiles, dids, tileset = terrain(S, W, H)
    types = dids | {struct.unpack_from('<H', dd, i * 8)[0] for i in range(ndd)}
    h, w = BE.heights(S)
    lv = collections.Counter(h[w].ravel().tolist())
    levels = sum(1 for v in lv.values() if v >= 0.02 * max(1, w.sum()))
    un = S.get('UNIT', b''); units = [struct.unpack_from('<HB', un, i + 8) for i in range(0, len(un) // 36 * 36, 36)]
    own = S.get('OWNR', b'')
    comps = sum(1 for p in range(min(8, len(own))) if own[p] == 5)
    return {
        'map': os.path.basename(path), 'tileset': tileset, 'map_size': f'{W}x{H}', 'copied_triggers': copies,
        'ground_types_used': gt,
        'doodad_tiles_per_1k': round(1000 * dtiles / tiles, 1),
        'placed_doodads': ndd,
        'distinct_doodad_types': len(types),
        'ramp_groups': level_crossings(h, w),
        'elevation_levels': levels,
        'walkable_share': round(float(w.mean()), 2),
        'triggers': len(T),
        'trigger_actions': sum(acts.values()),
        'transmissions': acts[A_TRANS],
        'briefing_voice_lines': bacts[B_WAV] + bacts[B_TRANS],
        'spawn_actions': acts[A_CREATE],
        'order_actions': acts[A_ORDER],
        'objective_updates': acts[A_OBJ],
        'ai_script_runs': acts[A_AI] + acts[A_AI_LOC],
        'preplaced_units': len(units),
        'computer_players': comps,
    }


def report(path, as_json):
    res = measure(path); low = []
    for k, (mn, typ) in BAND.items():
        v = res[k]
        if v < mn: low.append(k)
        if not as_json: print(f'{"OK  " if v >= mn else "WARN"} {k:24s} {v:>8}   (reference: >= {mn}, typical {typ})')
    if not as_json:
        for k in INFO_ONLY: print(f'INFO {k:24s} {res[k]:>8}')
    res['below_band'] = low
    res['on_floor'] = [k for k, (mn, typ) in BAND.items() if mn <= res[k] <= mn * FLOOR_MARGIN]
    floor_warn = len(res['on_floor']) >= (len(BAND) + 1) // 2
    if as_json: print(json.dumps(res, indent=1)); return res
    if floor_warn:
        print(f'WARN on_floor: {len(res["on_floor"])} of {len(BAND)} rows sit within 10 % of the band minimum ({", ".join(res["on_floor"])}): '
              'a map tuned to the floor of every row is built for the metric, not for the player')
    print(f'RESULT quality_metrics: {len(low)} of {len(BAND)} rows below the reference band'
          + (' - look at the map again; several rows far below the band are not delivery quality' if low else ''))
    return res


def main():
    a = [x for x in sys.argv[1:] if not x.startswith('--')]
    if not a: print(__doc__); sys.exit(2)
    for p in a:
        if len(a) > 1 and '--json' not in sys.argv: print('###', p)
        report(os.path.abspath(p) if not os.path.isabs(p) else p, '--json' in sys.argv)


if __name__ == '__main__':
    main()
