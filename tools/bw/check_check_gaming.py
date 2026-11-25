#!/usr/bin/env python3
"""check_gaming (predelivery check 59): the map passes the checks by being good, not by tricking them.
   python3 tools/bw/check_check_gaming.py MAP.scx [...]      (run from the repository root; exit 1 on FAIL)

Review map t1031 ('Canopy Vein', another agent with this repository) passed several checks with tricks instead of
fixes: an 'INCOME_OK' comment in the rescue-quest trigger hid the quest's unit hand-over from the reward check, six
timed camera triggers ordered the player's own Zealots to the front only so that the event-camera check saw a
'scripted effect', and 34 copies of one wave trigger lifted the quality metric to its floor (check 58).

FAIL rules:
1 exception_reason: every '<NAME>_OK:' exception line in the design note (SHORTCUT_OK, PRESSURE_SINGLE_OK, AI_IDLE_OK,
  QUALITY_BAND_OK, ...) and every INCOME_OK / REVEAL_PERMANENT_OK trigger comment gives a concrete reason: at least 4
  words of its own, not a placeholder ('<reason>', 'tbd', 'fixture', 'ok', 'n/a', 'intended', 'by design').
2 income_ok_masks_quest: INCOME_OK marks non-quest income (a timed supply drop). It is refused in a trigger that has an
  objective condition (Bring, Command, Kill, Deaths) or that changes the mission objectives, gives units to the player
  or creates units for the player: that is a quest reward and needs REWARD_WHY.
3 player_army_hijack: timed triggers (Elapsed Time / countdown) must not order the human player's own units around.
  Two or more such triggers FAIL (the mission plays itself and takes control away). Exemption:
  'SCRIPTED_PLAYER_ORDER_OK: <reason>' (e.g. a short opening march inside a cutscene)."""
import sys,os,re,struct
HERE=os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0,HERE); sys.path.insert(0,os.path.join(HERE,'..','lib','bw'))
from check_story_delivery import _sections,_strings,_trigs
from mission_model import notes_text

PLACEHOLDER=re.compile(r'^\s*(<[^>]*>|tbd|todo|fixture|ok|okay|n/?a|none|yes|intended|deliberate|by design|fine|-|\.|\?)\s*$',re.I)
def u32(b,o): return struct.unpack_from('<I',b,o)[0]

def reason_of(line):
    parts=[p.strip() for p in line.split('::')]
    return parts[-1] if parts else ''

def weak(reason):
    r=re.sub(r'\(.*?\)','',reason).strip()
    return bool(PLACEHOLDER.match(r)) or len(re.findall(r'[A-Za-z]{2,}',r))<4

def run(path):
    S=_sections(path)
    return evaluate(_strings(S),_trigs(S.get('TRIG',b'')),S.get('OWNR',b''),notes_text(path))

def evaluate(STR,T,own,notes):
    """STR {id: text}, T [(conditions, actions, owners)] raw 20/32-byte records, own OWNR bytes, notes design-note text"""
    hum={p for p in range(8) if p<len(own) and own[p]==6}
    R=[]
    # 1 exception reasons
    bad=[]
    for m in re.finditer(r'^\s*([A-Z][A-Z0-9_]*_OK)\s*:\s*(.*)$',notes,re.M):
        if weak(reason_of(m.group(2))): bad.append(f'{m.group(1)}: {m.group(2).strip()[:90]!r}')
    for i,(c,a,ow) in enumerate(T):
        for x in a:
            if x[26]==47:
                cm=STR.get(u32(x,4),'')
                mm=re.search(r'\b(INCOME_OK|REVEAL_PERMANENT_OK)\s*:?\s*(.*)',cm)
                if mm and weak(mm.group(2)): bad.append(f'trigger {i} comment {mm.group(1)}: {mm.group(2)[:90]!r}')
    R.append(('FAIL' if bad else 'OK  ')+' exception_reason: every *_OK exception carries a concrete reason (4+ words, no placeholder)'
             +''.join('\n     - '+b for b in bad[:10]))
    # 2 INCOME_OK in quest triggers
    bad=[]
    for i,(c,a,ow) in enumerate(T):
        cms=' '.join(STR.get(u32(x,4),'') for x in a if x[26]==47)
        if 'INCOME_OK' not in cms: continue
        why=[]
        if any(x[15] in (2,3,5,15) for x in c): why.append('objective condition')
        if any(x[26]==12 for x in a): why.append('changes the objectives')
        if any(x[26]==48 and (u32(x,20) in hum or u32(x,20)==13) for x in a): why.append('gives units to the player')
        if any(x[26]==44 and (u32(x,16) in hum or (u32(x,16)==13 and set(ow)&hum)) and struct.unpack_from('<H',x,24)[0] not in (33,101) for x in a): why.append('creates units for the player')
        if why: bad.append(f"trigger {i}: INCOME_OK in a quest trigger ({', '.join(why)})")
    R.append(('FAIL' if bad else 'OK  ')+' income_ok_masks_quest: INCOME_OK only on non-quest income, never on a quest reward (use REWARD_WHY)'
             +''.join('\n     - '+b for b in bad[:10]))
    # 3 timed orders of the player's own units
    hij=[]
    for i,(c,a,ow) in enumerate(T):
        timed=any(x[15]==1 or (x[15]==12 and u32(x,8)>5) for x in c)
        if not timed: continue
        if any(x[26]==46 and (u32(x,16) in hum or (u32(x,16)==13 and set(ow)&hum)) for x in a): hij.append(i)
    ok=[l for l in re.findall(r'SCRIPTED_PLAYER_ORDER_OK\s*:\s*(.+)',notes) if not weak(l)]
    if len(hij)>=2 and not ok:
        R.append(f'FAIL player_army_hijack: {len(hij)} timed triggers order the player\'s own units (triggers {hij[:10]}): the mission moves the player\'s army by itself; order allied or enemy units, or explain SCRIPTED_PLAYER_ORDER_OK')
    else:
        R.append(f'OK   player_army_hijack: timed triggers leave the player\'s units alone'+(f' (SCRIPTED_PLAYER_ORDER_OK: {ok[0][:80]})' if hij and ok else ''))
    return R

if __name__=='__main__':
    rc=0
    for p in sys.argv[1:]:
        print('###',p)
        for l in run(p): print(l); rc|=l.startswith('FAIL')
    sys.exit(rc)
