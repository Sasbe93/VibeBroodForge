#!/usr/bin/env python3
"""wave_variety (predelivery check 58): scripted enemy waves vary and escalate; copies do not count as content.
   python3 tools/bw/check_wave_variety.py MAP.scx [...]      (run from the repository root; exit 1 on FAIL)

Review map t1031 ('Canopy Vein'): 34 identical wave triggers (the same 4 Marines, 3 Firebats and 2 Medics, alternating
two spawn points for the whole mission) lifted the trigger, spawn and order counts of the quality metric to the band
floor. A player meets the same wave for twenty minutes.

Waves are the Create Unit actions for enemy computer players outside the opening (second > 5), grouped by their Elapsed Time
condition or the second they fire in an idle trigger simulation (tools/bw/trigsim.py; triggers that need an event
are one wave each; the same wave gated on another state of its building counts once). With 5
or more waves the check FAILs when
  - fewer than 3 distinct compositions exist (unit types and counts; the spawn point does not make a wave new), or
  - the waves do not escalate: the last third is neither larger on average than the first third nor brings unit
    types the first third did not have.
Exemption: 'WAVE_VARIETY_OK: <reason>' in the design note (e.g. a fixed garrison relief that is the story).
Waves after a hard victory (opening_review.dead_triggers) do not count.
spawn_source (t1036): a wave that spawns closer than 30 tiles to the player's start units with no enemy building
within 8 tiles and no transport created with it WARNs, two or more FAIL ('SPAWN_SOURCE_OK: <location> :: <reason>')."""
import sys,os,re,math,struct,collections
HERE=os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0,HERE); sys.path.insert(0,os.path.join(HERE,'..','lib','bw'))
import path_tool as P
from mission_model import notes_text
import opening_review as O

def u32(b,o): return struct.unpack_from('<I',b,o)[0]
def u16(b,o): return struct.unpack_from('<H',b,o)[0]

def waves(path,v=None,secs=3600):
    v=v or P.MapView(path)
    _,fired,_=O.idle_run(path,secs)
    _tv,dead=O.dead_triggers(path,v)          # waves after a hard victory never come (review t1036)
    per=[]
    for i,(c,a,own) in enumerate(v.trigs):
        if i in dead: continue
        comp=collections.Counter(); srcs=set()
        for x in a:
            if x[26]!=44: continue
            uid=u16(x,24)
            if uid in (101,33) or uid>=228: continue
            if set(v.grp(u32(x,16),own))&v.enemy: comp[uid]+=x[27] or 1; srcs.add(u32(x,0))
        if not comp: continue
        et=[u32(y,8) for y in c if y[15]==12 and y[14] in (0,10)]
        t=max(et) if et else fired.get(i)        # alternatives gated on a morph chain (T_each) share the Elapsed Time
        start=all(y[15]==22 or (y[15]==12 and u32(y,8)<=5) for y in c)
        if (t is not None and t<=5) or (t is None and start): continue
        per.append((t,i,comp,frozenset(srcs)))
    timed=sorted([p for p in per if p[0] is not None],key=lambda p:(p[0],p[1])); untimed=[p for p in per if p[0] is None]
    out=[]
    for t,i,comp,srcs in timed:
        key=(srcs,tuple(sorted(comp.items())))
        if out and t-out[-1]['t']<=5:
            if key in out[-1]['keys']: continue           # the same wave for another state of its building (alternative)
            out[-1]['comp']+=comp; out[-1]['trigs'].append(i); out[-1]['keys'].add(key)
        else: out.append({'t':t,'comp':collections.Counter(comp),'trigs':[i],'keys':{key}})
    known=set().union(*[w['keys'] for w in out]) if out else set()
    for t,i,comp,srcs in sorted(untimed,key=lambda p:p[1]):
        key=(srcs,tuple(sorted(comp.items())))
        if key in known: continue                         # an alternative of a timed wave (switch-gated, never idle-fired)
        known.add(key); out.append({'t':None,'comp':collections.Counter(comp),'trigs':[i],'keys':{key}})
    return out

def run(path):
    v=P.MapView(path)
    notes=notes_text(path)
    return judge(waves(path,v),notes)+spawn_source(v,path,notes)

SPAWN_MIN=30          # tiles from the player's start units/buildings
SOURCE_R=8            # tiles: an enemy building (hatchery, gate, nydus, ...) near the spawn explains it
DROPS={11,69,42}      # Dropship, Shuttle, Overlord created with the wave: a drop

def spawn_source(v,path,notes):
    """review t1036: waves appeared out of thin air a few screens from the player's front. A wave that spawns
    closer than SPAWN_MIN tiles to the player's start units, with no enemy building within SOURCE_R tiles of the spawn
    and no transport created with it, WARNs; two or more such waves FAIL. 'SPAWN_SOURCE_OK: <location> :: <reason>'."""
    import mission_model as MM
    _tv,dead=O.dead_triggers(path,v)
    front=[(u['x']/32,u['y']/32) for u in v.U if u['o'] in v.hum and u['id'] not in (214,)]
    if not front: return []
    blds=[(u['x']/32,u['y']/32) for u in v.U if u['o'] in v.enemy and MM.is_building(u['id'])]
    bad={}
    for i,(c,a,own) in enumerate(v.trigs):
        if i in dead: continue
        if all(y[15]==22 or (y[15]==12 and u32(y,8)<=5) for y in c): continue     # opening placement
        ids=[u16(x,24) for x in a if x[26]==44 and set(v.grp(u32(x,16),own))&v.enemy]
        if not ids or set(ids)&DROPS: continue
        for x in a:
            if x[26]!=44 or not set(v.grp(u32(x,16),own))&v.enemy: continue
            c0=v.lcenter(u32(x,0))
            if not c0: continue
            d=min(math.hypot(c0[0]-f[0],c0[1]-f[1]) for f in front)
            if d>=SPAWN_MIN or any(math.hypot(c0[0]-b[0],c0[1]-b[1])<=SOURCE_R for b in blds): continue
            bad.setdefault(v.lname(u32(x,0)),[d,0]); bad[v.lname(u32(x,0))][1]+=1
    ok=[l for l in re.findall(r'SPAWN_SOURCE_OK\s*:\s*(.+)',notes) if len(l.split('::')[-1].split())>=4]
    bad={k:x for k,x in bad.items() if not any(k.lower() in l.lower() for l in ok)}
    if not bad: return [f'OK   spawn_source: no wave appears out of nowhere within {SPAWN_MIN} tiles of the player']
    n=sum(x[1] for x in bad.values())
    msg=(f"spawn_source: {n} wave spawn(s) appear out of nowhere within {SPAWN_MIN} tiles of the player's start units with no enemy "
         f"building (hatchery, gate, nydus) within {SOURCE_R} tiles and no transport: "+', '.join(f"'{k}' ({x[0]:.0f} tiles, {x[1]}x)" for k,x in bad.items())
         +" - spawn at an enemy base, a nydus or the map edge, or drop them; or explain 'SPAWN_SOURCE_OK: <location> :: <reason>'")
    return [('FAIL ' if n>=2 else 'WARN ')+msg]

def judge(W,notes):
    """W: [{'t': seconds or None, 'comp': Counter(unit id -> count)}] in time order"""
    if len(W)<5: return [f'OK   wave_variety: {len(W)} scripted wave(s) (the rule starts at 5)']
    sig=lambda w: tuple(sorted(w['comp'].items()))
    distinct=len({sig(w) for w in W})
    k=max(1,len(W)//3); first,last=W[:k],W[-k:]
    size=lambda ws: sum(sum(w['comp'].values()) for w in ws)/len(ws)
    t_first={u for w in first for u in w['comp']}; t_last={u for w in last for u in w['comp']}
    grows=size(last)>size(first) or bool(t_last-t_first)
    F=[]
    if distinct<3: F.append(f'only {distinct} distinct wave composition(s) in {len(W)} waves (need 3): the same wave again and again, e.g. '+', '.join(f'{n}x {P.uname(u)}' for u,n in sorted(W[0]['comp'].items())))
    if not grows: F.append(f'no escalation: the last {k} wave(s) average {size(last):.1f} units vs {size(first):.1f} in the first {k}, and bring no new unit type')
    ok=[l for l in re.findall(r'WAVE_VARIETY_OK\s*:\s*(.+)',notes) if len(l.split())>=4]
    head=f'wave_variety: {len(W)} waves, {distinct} distinct compositions, first-third {size(first):.1f} / last-third {size(last):.1f} units'
    if F and ok: return [f'OK   {head} - WAVE_VARIETY_OK ({ok[0][:80]})']
    return [('FAIL ' if F else 'OK   ')+head+''.join('\n     - '+f for f in F)]

if __name__=='__main__':
    rc=0
    for p in sys.argv[1:]:
        print('###',p)
        for l in run(p): print(l); rc|=l.startswith('FAIL')
    sys.exit(rc)
