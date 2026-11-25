#!/usr/bin/env python3
"""opening_review: play the first minutes of a Brood War mission in the trigger simulator and review what the
player meets at second 0. Mandatory before delivery (AGENTS.md); tools/deliver.py runs it and packs the timeline
(OPENING_REVIEW.txt) into the delivery ZIP. Read the timeline yourself: the checks below only catch known failures.
   python3 tools/bw/opening_review.py MAP.scx [--secs 240] [--timeline]     (exit 1 on FAIL)

Review map t1031 ('Canopy Vein', built by another agent with this repository): 13 enemy Marines and Firebats stood
inside the player's base at second 0, the rescue probe stood on an enemy Marine, and the player's own start probe
fulfilled the rescue quest at second 0, 120 s before the quest was announced. No check had looked at second 0.

Checks (predelivery checks 55-57):
55 enemy_near_start (FAIL): no armed enemy unit or tower stands within 8 tiles (acquisition range) of the human
   player's start location or pre-placed buildings at second 0. Exemption: 'ENEMY_NEAR_START_OK: <reason>' in the
   design note (e.g. a scripted opening fight the player is meant to win, with the units named).
56 rescue_under_fire (FAIL): a rescuable unit (Rescuable slot) stands within 7 tiles of armed enemy units that are
   hostile to it at second 0, and the rescuable group nearby is not at least twice as many armed ground units (an
   unarmed Probe or a High Templar beside Marines dies before the player arrives). Exemption:
   'RESCUE_FIGHT_OK: <unit or place> :: <reason>'.
57 quest_idle (FAIL): with nobody moving (idle playthrough of --secs seconds; rescuables standing within 2 tiles of a
   player unit join at second 1, as in the game), no objective trigger fires: a trigger of the human player with a
   'Bring' condition at a location (or a Command/Kill condition) that wins, gives or creates units for the player, or
   adds resources. Such a quest is already done at second 0, usually before it is announced. Victory in the idle
   playthrough is always a FAIL. Exemption: 'QUEST_IDLE_OK: <location or trigger number> :: <reason>'.
Limits: static positions and the trigger simulator (tools/bw/trigsim.py: no combat, no AI, no unit movement); it
does not replace a playtest."""
import sys,os,re,math,struct
HERE=os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0,HERE); sys.path.insert(0,os.path.join(HERE,'..','lib','bw'))
import path_tool as P
import trigsim
from mission_model import notes_text, is_building

AGGRO=8; RESCUE_R=7; JOIN_R=2
NONCOMBAT={7,41,64,214,101,176,177,178,188,33,73,63}     # workers, start location, revealer, resources, scanner, interceptor, ...

def u32(b,o): return struct.unpack_from('<I',b,o)[0]
def u16(b,o): return struct.unpack_from('<H',b,o)[0]
def armed(uid): return uid in P.TOWERS or (uid not in NONCOMBAT and uid<106 and (uid in P.GROUND_ARMED or (P.DB['units'].get(str(uid)) or {}).get('air') is not None))
def exempt(notes,key): return [l.strip() for l in re.findall(key+r'\s*:\s*(.+)',notes) if len(l.split())>=3]

def hostile_rel(v):
    """(player, target group) -> alliance status set by trigger (Set Alliance Status, 0 enemy, 1 ally, 2 allied victory)"""
    rel={}
    for c,a,own in v.trigs:
        for x in a:
            if x[26]==57:
                for q in own:
                    if q<8: rel[(q,u32(x,16))]=u16(x,24)
    return rel

def enemy_near_start(v,notes):
    base=[(u['x']/32,u['y']/32,P.uname(u['id'])) for u in v.U if u['o'] in v.hum and (u['id']==214 or is_building(u['id']))]
    if not base: return ['OK   enemy_near_start: the human player has no start location or pre-placed building']
    bad=[]
    for u in v.U:
        if u['o'] not in v.enemy or not armed(u['id']): continue
        x,y=u['x']/32,u['y']/32
        d,b=min((math.hypot(x-bx,y-by),n) for bx,by,n in base)
        if d<=AGGRO: bad.append((d,f"P{u['o']+1} {P.uname(u['id'])} at ({x:.0f},{y:.0f}) {d:.1f} tiles from the player's {b}"))
    bad.sort()
    ok=exempt(notes,'ENEMY_NEAR_START_OK')
    if bad and ok: return [f'OK   enemy_near_start: {len(bad)} armed enemy unit(s) within {AGGRO} tiles of the start base - ENEMY_NEAR_START_OK ({ok[0][:100]})']
    return [('FAIL' if bad else 'OK  ')+f' enemy_near_start: no armed enemy within {AGGRO} tiles (acquisition range) of the player start base at second 0'
            +(f' - {len(bad)} unit(s): the opening is a fight the player did not choose; move them out or script the scene and explain ENEMY_NEAR_START_OK' if bad else '')
            +''.join('\n     - '+b for _,b in bad[:8])+(f'\n     ... {len(bad)} total' if len(bad)>8 else '')]

def rescue_under_fire(v,notes):
    rel=hostile_rel(v); fz=v.forces
    def hostile(e,r):
        s=rel.get((e,r),rel.get((e,13)))
        if s is not None: return s==0
        return r in v.comp and fz[e]!=fz[r]
    res=[u for u in v.U if u['o'] in v.rescue and not is_building(u['id']) and u['id'] not in NONCOMBAT-{7,41,64}]
    bad=[]; seen=set()
    for r in res:
        x,y=r['x']/32,r['y']/32
        foes=[e for e in v.U if e['o'] in v.enemy and armed(e['id']) and hostile(e['o'],r['o']) and math.hypot(e['x']/32-x,e['y']/32-y)<=RESCUE_R]
        if not foes: continue
        mates=[q for q in res if q['o']==r['o'] and armed(q['id']) and math.hypot(q['x']/32-x,q['y']/32-y)<=RESCUE_R]
        if len(mates)>=2*len(foes): continue
        k=(r['o'],round(x),round(y))
        if k in seen: continue
        seen.add(k)
        dmin=min(math.hypot(e['x']/32-x,e['y']/32-y) for e in foes)
        bad.append(f"P{r['o']+1} {P.uname(r['id'])} at ({x:.0f},{y:.0f}): {len(foes)} hostile armed enemy unit(s) within {RESCUE_R} tiles (nearest {dmin:.1f}), {len(mates)} armed rescuable(s) beside it")
    ok=exempt(notes,'RESCUE_FIGHT_OK')
    if bad and ok: return [f'OK   rescue_under_fire: {len(bad)} rescuable unit(s) beside hostile enemies - RESCUE_FIGHT_OK ({ok[0][:100]})']
    return [('FAIL' if bad else 'OK  ')+' rescue_under_fire: rescuable units are not beside hostile armed enemies at second 0 (they die before the player arrives)'
            +''.join('\n     - '+b for b in bad[:8])]

class IdleSim(trigsim.Sim):
    def cond(s,c,owner):
        try: return super().cond(c,owner)
        except ValueError: return False
    def act(s,a,owner,ti):
        if a[7]==13 and a[8]==6:                       # Set Switch toggle
            (s.sw.discard if a[4] in s.sw else s.sw.add)(a[4]); return
        super().act(a,owner,ti)

def idle_run(path,secs,patch=None):
    s=IdleSim(path); fired={}
    if patch: patch(s)                                  # fixtures: change the start state
    def join(si):
        hum=[u for u in si.units if u[0]==0]
        for u in si.units:
            if u[0]==7 and any(math.hypot(u[2]-h[2],u[3]-h[3])<=JOIN_R*32 for h in hum): u[0]=0
    s.log=[]
    # record when each trigger fires
    ev=[(1,join,'rescuables beside player units join')]
    t_res=s.run(ev,secs)
    for t,desc in s.log:
        m=re.match(r'trig(\d+) fires',desc)
        if m: fired.setdefault(int(m.group(1)),t)
    return s,fired,t_res

_DEAD={}
def dead_triggers(path,v=None,secs=3600):
    """(victory time or None, set of trigger indices that can only fire after a hard victory). Review t1036: the
    countdown won at 720 s, while waves were scheduled at 745-1230 s and still counted for the wave metrics.
    Dead: an Elapsed Time condition later than the victory, or gated on switches that only dead triggers set."""
    key=os.path.abspath(path)
    if key in _DEAD: return _DEAD[key]
    v=v or P.MapView(path)
    try: s,fired,tres=idle_run(path,secs)
    except Exception: _DEAD[key]=(None,set()); return _DEAD[key]
    if not tres or tres[0]!='VICTORY': _DEAD[key]=(None,set()); return _DEAD[key]
    tv=tres[1]; dead=set()
    for i,(c,a,own) in enumerate(v.trigs):
        if i in fired: continue
        if any(y[15]==12 and y[14] in (0,10) and u32(y,8)>tv for y in c): dead.add(i)
    for _ in range(4):
        setters={}
        for i,(c,a,own) in enumerate(v.trigs):
            for x in a:
                if x[26]==13 and x[27] in (4,6): setters.setdefault(u32(x,20),set()).add(i)
        new=set()
        for i,(c,a,own) in enumerate(v.trigs):
            if i in fired or i in dead: continue
            sw=[y[16] for y in c if y[15]==11 and y[14]==2]
            if sw and any(setters.get(w) and setters[w]<=dead for w in sw): new.add(i)
        if not new: break
        dead|=new
    _DEAD[key]=(tv,dead); return _DEAD[key]

def post_victory(v,path,notes):
    tv,dead=dead_triggers(path,v)
    if tv is None: return ['OK   60 post_victory: no hard victory in the idle simulation (victory needs player action)']
    waves=[i for i in sorted(dead) if any(x[26]==44 and set(v.grp(u32(x,16),v.trigs[i][2]))&v.enemy for x in v.trigs[i][1])]
    late=sorted({u32(y,8) for i in dead for y in v.trigs[i][0] if y[15]==12 and y[14] in (0,10)})
    if not dead: return [f'OK   60 post_victory: hard victory at {tv} s, no trigger scheduled after it']
    msg=(f"60 post_victory: the mission is won at {tv} s (idle simulation), but {len(dead)} trigger(s) can only run later"
         +(f" ({len(waves)} attack wave(s): triggers {waves[:10]})" if waves else '')+(f"; elapsed times {late[:8]}" if late else '')
         +" - dead content: remove it, or move it before the victory (the checks and metrics ignore it)")
    if waves: return ['FAIL '+msg]
    return ['WARN '+msg]

def objective_trigs(v):
    out={}
    for i,(c,a,own) in enumerate(v.trigs):
        if not (own&v.hum or 17 in own): continue
        timed=any(x[15]==1 or (x[15]==12 and u32(x,8)>5) for x in c)
        if timed: continue
        cond=None
        for x in c:
            loc=u32(x,0); pl=set(v.grp(u32(x,4),own))
            if x[15]==3 and x[14] in (0,10) and u32(x,8)>=1 and not v.whole(loc) and pl&v.hum: cond=('bring',loc,u16(x,12))
            elif x[15] in (2,3) and x[14] in (1,10) and u32(x,8)==0 and pl&v.enemy: cond=('kill',loc,u16(x,12))
        if not cond: continue
        def rewards(a,own):
            rw=[]
            for x in a:
                pl=set(v.grp(u32(x,16),own))
                if x[26]==1: rw.append('victory')
                elif x[26]==48 and set(v.grp(u32(x,20),own))&v.hum: rw.append('gives units')
                elif x[26]==44 and pl&v.hum and u16(x,24) not in (101,33): rw.append('creates units')
                elif x[26]==26 and x[27]==8 and pl&v.hum: rw.append('adds resources')
            return rw
        rw=rewards(a,own)
        sws={u32(x,20) for x in a if x[26]==13 and x[27] in (4,6)}
        for c2,a2,o2 in v.trigs:                      # the reward may sit in a trigger gated on a switch this one sets
            if any(y[15]==11 and y[14]==2 and y[16] in sws for y in c2) and len(c2)<=2: rw+=rewards(a2,o2)
        if rw: out[i]=(cond,sorted(set(rw)))
    return out

def announcement(v,s,fired,loc,skip):
    r=v.rect(loc)
    if not r: return None
    best=None
    for i,(c,a,own) in enumerate(v.trigs):
        if i==skip or i not in fired: continue
        for x in a:
            if x[26] in (10,28):
                r2=v.rect(u32(x,0))
                big=r2 and (r2[2]-r2[0])*(r2[3]-r2[1])>2*max(1,(r[2]-r[0])*(r[3]-r[1]))
                if r2 and not big and r2[0]<r[2] and r[0]<r2[2] and r2[1]<r[3] and r[1]<r2[3] and (best is None or fired[i]<best[0]): best=(fired[i],i)
    return best

def quest_idle(v,path,notes,secs,patch=None):
    s,fired,result=idle_run(path,secs,patch)
    obj=objective_trigs(v); bad=[]
    ok=exempt(notes,'QUEST_IDLE_OK')
    for i,(cond,rw) in sorted(obj.items()):
        if i not in fired: continue
        kind,loc,uid=cond; ln=v.lname(loc) if not v.whole(loc) else 'anywhere'
        if any(ln.lower() in l.lower() or re.search(rf'\btrigger\s*{i}\b',l) for l in ok): continue
        ann=announcement(v,s,fired,loc,i)
        when=f'its announcement (trigger {ann[1]}, camera/ping on the place) comes at {ann[0]} s' if ann else 'nothing announces it before'
        early=' - BEFORE the announcement' if ann and fired[i]<ann[0] else ''
        bad.append(f"trigger {i} ({kind} {P.uname(uid)} at '{ln}'; {', '.join(rw)}) fires at {fired[i]} s with nobody moving; {when}{early}")
    if result and result[0]=='VICTORY' and not any('victory' in b for b in bad):
        bad.append(f'victory fires at {result[1]} s with nobody moving (trigger {result[2]})')
    head=f'quest_idle: no objective is fulfilled in an idle playthrough of {secs} s (trigger simulation, nobody moves)'
    out=[('FAIL ' if bad else 'OK   ')+head+''.join('\n     - '+b for b in bad[:8])]
    if result and result[0]=='DEFEAT': out.append(f'WARN quest_idle: defeat fires at {result[1]} s with nobody moving (trigger {result[2]}): is that intended?')
    return out,s,fired

def timeline(v,s,fired,secs):
    """readable opening: what fires when, objective texts, transmissions, spawns, camera"""
    st=v.st; L=[f'Idle playthrough, first {secs} s (trigger simulation, nobody moves; no combat or AI):']
    for i,t in sorted(fired.items(),key=lambda kv:(kv[1],kv[0])):
        c,a,own=v.trigs[i]; bits=[]
        for x in a:
            ty=x[26]
            if ty==12: bits.append('OBJECTIVES: '+P.strip(st(u32(x,4))).replace('\n',' | ')[:160])
            elif ty==7: bits.append('TRANSMISSION: '+P.strip(st(u32(x,4)))[:120])
            elif ty==9: bits.append('TEXT: '+P.strip(st(u32(x,4)))[:120])
            elif ty==10: bits.append(f"camera -> '{v.lname(u32(x,0))}'")
            elif ty==28: bits.append(f"ping '{v.lname(u32(x,0))}'")
            elif ty==44: bits.append(f"create {x[27] or 1}x {P.uname(u16(x,24))} for P{u32(x,16)+1} at '{v.lname(u32(x,0))}'")
            elif ty==48: bits.append(f"give {P.uname(u16(x,24))} P{u32(x,16)+1}->P{u32(x,20)+1}")
            elif ty in (1,2): bits.append('VICTORY' if ty==1 else 'DEFEAT')
            elif ty==46: bits.append(f"order P{u32(x,16)+1} {P.uname(u16(x,24))} -> '{v.lname(u32(x,20))}'")
        bits=list(dict.fromkeys(bits))
        L.append(f'  t={t:>4}s trigger {i} (P{",".join(str(q+1) for q in sorted(own) if q<8) or "all"}): '+('; '.join(bits)[:500] if bits else '(switches, resources or waits only)'))
    return L

def run(path,secs=240,want_timeline=False):
    v=P.MapView(path); notes=notes_text(path)
    R=[]
    for lbl,fn in (('55 enemy near start',lambda: enemy_near_start(v,notes)),('56 rescue under fire',lambda: rescue_under_fire(v,notes))):
        try: R+=fn()
        except Exception as e: R.append(f'FAIL {lbl} check crashed: {type(e).__name__}: {e}'[:300])
    try: R+=post_victory(v,path,notes)
    except Exception as e: R.append(f'FAIL 60 post_victory check crashed: {type(e).__name__}: {e}'[:300])
    try:
        q,s,fired=quest_idle(v,path,notes,secs); R+=q
        if want_timeline: R+=timeline(v,s,fired,secs)
    except Exception as e: R.append(f'FAIL 57 quest idle check crashed: {type(e).__name__}: {e}'[:300])
    return R

if __name__=='__main__':
    a=[x for x in sys.argv[1:] if not x.startswith('--')]
    secs=int(sys.argv[sys.argv.index('--secs')+1]) if '--secs' in sys.argv else 240
    if '--secs' in sys.argv: a=[x for x in a if x!=str(secs)]
    rc=0
    for p in a:
        print('###',p)
        for l in run(p,secs,'--timeline' in sys.argv): print(l); rc|=l.startswith('FAIL')
    sys.exit(rc)
