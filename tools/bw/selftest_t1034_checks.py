#!/usr/bin/env python3
"""Fixtures for the checks added after two map reviews (t1031/t1034): each check must FAIL on a known-bad case and
pass on the repository example.
  python3 tools/bw/selftest_t1034_checks.py        (exit 1 if a fixture misbehaves)
Needs the built Outpost Nine (output/example_mission/Example_Mission.scx) and Thorn Road
(output/examples/ex_thorn_road/Ex_Thorn_Road.scx): python3 tools/bw/example_mission.py --no-checks and
python3 tools/bw/examples/ex_thorn_road.py --no-checks. Known-bad cases are derived from those maps (patched in
memory or in a temp copy of the scenario) or are minimal synthetic data:
  ai_script_valid        the town script id replaced by 'TAIM' (not a Brood War script)
  enemy_near_start       an enemy Marine placed beside the player's start location
  rescue_under_fire      a rescuable Probe placed beside the enemy Hatchery guards, enemy set hostile
  quest_idle             the victory target removed at second 0 (the kill objective is done with nobody moving)
  objective_paths        a rescue target 2 tiles from the start; one threat cluster on the way there and back
  objective_shortcuts    Thorn Road's listening post without anti-air: a Scout raid kills it unopposed
  core_tech              a rescuable High Templar whose spells are disabled for the player
  check_gaming           INCOME_OK in a quest trigger, timed orders of the player's units, a placeholder exception
  wave_variety           ten copies of one wave; ten waves that never grow
  quality_metrics        copied wave triggers counted once
  post_victory (t1036)   waves that only run after a hard victory
  lift off (t1036)       defeat 'Command Center == 0' anywhere, ground waves only
  spawn_source (t1036)   two waves that appear out of nowhere next to the player's base
  objective texts        a '- done' mark in the middle of the objective text
Set ATTACHED_SCX (t1031 review map) and T1036_SCX (t1036 review map) to outside maps that should fail them; the review
maps are not part of the repository."""
import sys,os,shutil,tempfile,struct,collections,copy
H=os.path.dirname(os.path.abspath(__file__)); ROOT=os.path.dirname(os.path.dirname(H))
sys.path.insert(0,H); sys.path.insert(0,os.path.join(ROOT,'tools','lib','bw'))
os.chdir(ROOT)
import path_tool as P, opening_review as O, check_computer_ai as CA, check_objective_paths as OP
import check_objective_shortcuts as SC, check_check_gaming as CG, check_wave_variety as WV, quality_metrics as QM
import core_tech, mission_model as MM
from eudplib.bindings._rust import mpqapi

EX=os.path.join(ROOT,'output','example_mission','Example_Mission.scx')
TR=os.path.join(ROOT,'output','examples','ex_thorn_road','Ex_Thorn_Road.scx')
for f in (EX,TR):
    if not os.path.isfile(f): print('MISSING built example',f,'- build it first (--no-checks)'); sys.exit(1)
ok=True
def fails(out): return [l for l in out if l.startswith('FAIL')]
def expect(name,out,want_fail):
    global ok
    f=fails(out); good=bool(f)==want_fail; ok&=good
    print(('pass ' if good else 'WRONG')+f" {name}: {'FAIL' if f else 'OK'}  {(f or out or ['-'])[0][:170]}")

def chk(path): return bytes(mpqapi.MPQ.open(path).extract_file('staredit\\scenario.chk'))
def sections(d):
    S={};i=0
    while i+8<=len(d):
        k=d[i:i+4].decode('latin1'); n=struct.unpack_from('<i',d,i+4)[0]; S[k]=d[i+8:i+8+n]; i+=8+n
    return S

# ai_script_valid (check_computer_ai.py)
tmp=tempfile.mkdtemp(prefix='t1034_')
raw=chk(EX); good_chk=os.path.join(tmp,'good.chk'); bad_chk=os.path.join(tmp,'bad.chk')
open(good_chk,'wb').write(raw); open(bad_chk,'wb').write(raw.replace(b'ZMEx',b'TAIM'))
expect('ai_script_valid: official example',[l for l in CA.run(good_chk) if 'ai_script_valid' in l],False)
expect("ai_script_valid: town script 'TAIM'",[l for l in CA.run(bad_chk) if 'ai_script_valid' in l],True)

# enemy_near_start / rescue_under_fire (opening_review.py)
v=P.MapView(EX); notes=MM.notes_text(EX)
expect('enemy_near_start: official example',O.enemy_near_start(v,notes),False)
sl=next(u for u in v.U if u['o'] in v.hum and u['id']==214); en=sorted(v.enemy)[0]
v2=copy.copy(v); v2.U=v.U+[dict(o=en,id=0,x=sl['x']+3*32,y=sl['y'])]
expect('enemy_near_start: enemy Marine 3 tiles from the start',O.enemy_near_start(v2,notes),True)
expect('enemy_near_start: accepted with ENEMY_NEAR_START_OK',O.enemy_near_start(v2,notes+'\nENEMY_NEAR_START_OK: the opening ambush is the tutorial fight of this fixture\n'),False)
expect('rescue_under_fire: official example',O.rescue_under_fire(v,notes),False)
guard=next(u for u in v.U if u['o']==en and O.armed(u['id']))
rq=sorted(v.rescue)[0]
v3=copy.copy(v); v3.U=v.U+[dict(o=rq,id=64,x=guard['x']+32,y=guard['y'])]
orig=O.hostile_rel; O.hostile_rel=lambda vv: {(en,13):0}
try: expect('rescue_under_fire: rescuable Probe beside a hostile guard',O.rescue_under_fire(v3,notes),True)
finally: O.hostile_rel=orig

# quest_idle (opening_review.py, trigger simulation)
q,_,_=O.quest_idle(v,EX,notes,240); expect('quest_idle: official example',q,False)
def no_target(s):
    s.units=[u for u in s.units if not (u[0]==en and u[1] in (131,132,133))]
q,_,_=O.quest_idle(v,EX,notes,240,patch=no_target); expect('quest_idle: victory target gone at second 0',q,True)

# objective_paths: distinct clusters and trivially short targets (synthetic objective)
cl=([3,4],['unit Terran Marine at (30,70)','unit Terran Marine at (31,70)'])
o={'type':'rescue','name':'x','paths':[('start_to_target',(26,73),(27,71),64,[],2.4),('return',(27,71),(26,73),64,[],2.4)],'encounters':[[cl],[cl]]}
n=OP.path_encounters(o)
expect('objective_paths: one cluster on the way there and back counts once',[] if n==1 else [f'FAIL counted {n}'],False)
expect('objective_paths: rescue target 2 tiles from the start',['FAIL short'] if OP.short_paths(o) else ['OK'],True)
o2=dict(o,paths=[('start_to_target',(26,73),(80,20),64,[],75.0)])
expect('objective_paths: rescue target 75 tiles away',['FAIL short'] if OP.short_paths(o2) else ['OK'],False)

# objective_shortcuts: destroy target vs air attackers (Thorn Road listening post)
d_ok=[l for l in SC.run(TR) if 'destroy' in l]
expect('objective_shortcuts: Thorn Road listening post with two turrets',d_ok,False)
orig=SC.aa_threats; SC.aa_threats=lambda vv: []
try: expect('objective_shortcuts: listening post without anti-air (Scout raid)',[l for l in SC.run(TR) if 'destroy' in l],True)
finally: SC.aa_threats=orig

# core_tech: units the player gains (rescuable High Templar with spells disabled)
S=sections(raw)
expect('core_tech: official example',['FAIL '+x for x in core_tech.check(S)],False)
S2=dict(S); rec=bytearray(S['UNIT'][:36]); struct.pack_into('<H',rec,8,67); rec[16]=7
S2['UNIT']=S['UNIT']+bytes(rec); ow=bytearray(S['OWNR']); ow[7]=3; S2['OWNR']=bytes(ow)
pt=bytearray(S['PTEx'])
for t in (19,20,23):          # Psionic Storm, Hallucination, Archon Warp: not available to P1, no default
    pt[0*44+t]=0; pt[12*44*2+44*2+0*44+t]=0
S2['PTEx']=bytes(pt)
expect('core_tech: rescued High Templar with every spell disabled',['FAIL '+x for x in core_tech.check(S2)],True)

# check_gaming (synthetic triggers)
def cond(ct,player=0,qty=0,unit=0,loc=0,cmp=0,res=0): return struct.pack('<IIIHBBBBH',loc,player,qty,unit,cmp,ct,res,0,0)
def act(ty,loc=0,st=0,player=0,num=0,unit=0,mod=0): return struct.pack('<IIIIIIHBBB3x',loc,st,0,0,player,num,unit,ty,mod,0)
OWN=bytes([6,5,0,0,0,0,0,3,0,0,0,0])
STR={1:'INCOME_OK: seized mineral pallets beside the cache pylon',2:'INCOME_OK: supply drop every five minutes from the fleet'}
quest=[([cond(3,0,1,64,5)],[act(48,5,0,7,0,64),act(26,0,0,0,150,0,8),act(47,0,1)],[0])]
timed=[([cond(12,qty=200)],[act(26,0,0,0,200,0,8),act(47,0,2)],[0])]
expect('check_gaming: INCOME_OK on a timed supply drop',CG.evaluate(STR,timed,OWN,''),False)
expect('check_gaming: INCOME_OK in the rescue-quest trigger',CG.evaluate(STR,quest,OWN,''),True)
hij=[([cond(12,qty=t)],[act(10,3),act(46,3,0,0,4,65,2)],[0]) for t in (50,170,290)]
expect('check_gaming: three timed orders of the player\'s Zealots',CG.evaluate(STR,hij,OWN,''),True)
expect('check_gaming: placeholder exception reason',CG.evaluate(STR,[],OWN,'PRESSURE_SINGLE_OK: <reason>\n'),True)
expect('check_gaming: concrete exception reason',CG.evaluate(STR,[],OWN,'PRESSURE_SINGLE_OK: the warlord base is the climax and the only enemy left\n'),False)

# wave_variety (synthetic waves)
C=collections.Counter
same=[{'t':80+40*k,'comp':C({0:4,32:3,34:2})} for k in range(10)]
grow=[{'t':80+40*k,'comp':C({0:3+k//3,32:1+k//4}|({5:1} if k>6 else {}))} for k in range(10)]
flat=[{'t':80+40*k,'comp':C({0:4,32:3}) if k%3==0 else C({0:3,32:4}) if k%3==1 else C({0:5,32:2})} for k in range(10)]
expect('wave_variety: ten copies of one wave',WV.judge(same,''),True)
expect('wave_variety: three compositions that never grow',WV.judge(flat,''),True)
expect('wave_variety: growing waves with a new unit type',WV.judge(grow,''),False)

# quality_metrics: copies count once
wave=([cond(12,qty=80)],[act(44,4,0,1,0,0,3),act(44,4,0,1,0,32,2),act(46,4,0,1,8,229,2),act(13,num=150,mod=4)],[1])
T=[wave]+[(wave[0],wave[1][:3]+[act(13,num=150+k,mod=4)],wave[2]) for k in range(1,34)]
D,cp=QM.dedupe(T)
expect('quality_metrics: 34 copies of one wave count once',[] if len(D)==1 and cp==33 else [f'FAIL kept {len(D)}, copies {cp}'],False)

# post_victory (opening_review.py): waves scheduled after a hard victory
v=P.MapView(EX)
expect('post_victory: official example',O.post_victory(v,EX,notes),False)
wav=[i for i,(c,a,own) in enumerate(v.trigs) if any(x[26]==44 and set(v.grp(struct.unpack_from('<I',x,16)[0],own))&v.enemy for x in a)]
O._DEAD[os.path.abspath('fixture_post_victory.scx')]=(720,set(wav[:3]))
expect('post_victory: three wave triggers after the victory at 720 s',O.post_victory(v,'fixture_post_victory.scx',notes),True)

# lift off (check_objective_shortcuts.py): defended Command Center anywhere, ground-only waves
M0=MM.Model(EX)
expect('lift off: official example',[l for l in SC.liftoff_defend(M0) if 'lift off' in l],False)
def nodefeat(M): return [t for t in M.v.trigs if not (t[2]&M.v.hum and any(x[26]==2 for x in t[1]))]
M1=MM.Model(EX); M1.v.trigs=list(M1.v.trigs)+[([cond(2,0,0,106,0,10)],[act(2)],{0})]
expect("lift off: Command Center defeat beside the 'Buildings' defeat (not the only way to lose)",[l for l in SC.liftoff_defend(M1) if 'lift off' in l],False)
M1.v.trigs=nodefeat(M1)+[([cond(2,0,0,106,0,10)],[act(2)],{0})]
expect("lift off: only defeat 'Command(P1, Command Center) == 0', ground waves",[l for l in SC.liftoff_defend(M1) if 'lift off' in l],True)
far=next(l for l in range(1,256) if M1.v.rect(l) and not M1.v.whole(l))
M2=MM.Model(EX); M2.v.trigs=nodefeat(M2)+[([cond(3,0,0,106,far,10)],[act(2)],{0})]
expect('lift off: defeat is a Bring of the Command Center at a location',[l for l in SC.liftoff_defend(M2) if 'lift off' in l],False)

# spawn_source (check_wave_variety.py): waves out of nowhere beside the player
expect('spawn_source: official example',WV.spawn_source(v,EX,notes),False)
hum=[(u['x']/32,u['y']/32) for u in v.U if u['o'] in v.hum]
blds=[(u['x']/32,u['y']/32) for u in v.U if u['o'] in v.enemy and MM.is_building(u['id'])]
import math
near=next(l for l in range(1,256) if v.lcenter(l) and not v.whole(l) and min(math.hypot(v.lcenter(l)[0]-h[0],v.lcenter(l)[1]-h[1]) for h in hum)<20
          and all(math.hypot(v.lcenter(l)[0]-b[0],v.lcenter(l)[1]-b[1])>8 for b in blds))
v4=copy.copy(v); v4.trigs=list(v.trigs)+[([cond(12,qty=t)],[act(44,near,0,en,6,37)],{en}) for t in (300,420)]
O._DEAD[os.path.abspath('fixture_spawn.scx')]=(None,set())
expect('spawn_source: two waves appear 20 tiles from the player with no source',WV.spawn_source(v4,'fixture_spawn.scx',notes),True)

# objective texts: a '- done' mark in the middle (path_tool.objective_texts)
class _V: pass
vs=_V(); txt={1:'Survive until the beacon burns out (12 minutes). The Command Center must stand.',2:'Survive until the beacon burns out (12 minutes). - done The Command Center must stand.'}
vs.st=lambda i: txt[i]; vs.trigs=[([],[act(12,0,1)],{0}),([],[act(12,0,2)],{0})]
ot=P.objective_texts(vs)
expect("objective texts: '- done' in the middle is no second objective",[] if len(ot)==1 else [f'FAIL {ot}'],False)

att=os.environ.get('ATTACHED_SCX','')
if att and os.path.isfile(att):
    import predelivery_check as PC
    out=PC.run_safe(att)
    for key in ('ai_script_valid','enemy_near_start','rescue_under_fire','quest_idle','wave_variety','income_ok_masks_quest','player_army_hijack','event cameras','core abilities'):
        expect(f'attached map: {key}',[l for l in out if key in l],True)
else:
    print('skip attached-map fixture (set ATTACHED_SCX=<map.scx>)')
t36=os.environ.get('T1036_SCX','')
if t36 and os.path.isfile(t36):
    import predelivery_check as PC
    out=PC.run_safe(t36)
    for key in ('post_victory','lift off','spawn_source','player_army_hijack','event cameras'):
        expect(f'T1036 map: {key}',[l for l in out if key in l],True)
    expect('T1036 map: wave_variety after dead triggers',[l for l in out if 'wave_variety' in l],False)
    vt=P.MapView(t36); expect("T1036 map: one objective despite '- done'",[] if len(P.objective_texts(vt))==1 else ['FAIL'],False)
else:
    print('skip T1036 fixture (set T1036_SCX=<map.scx>)')
shutil.rmtree(tmp,ignore_errors=True)
print('SELFTEST','PASS' if ok else 'FAIL'); sys.exit(0 if ok else 1)
