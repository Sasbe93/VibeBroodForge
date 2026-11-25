"""Selftest: the agent entry point and the delivery gate stay wired up.

Checks that AGENTS.md is the single entry point and every agent's pointer file points to it, that every repository
path AGENTS.md names exists, that the check-output classifier and the design-note test of tools/deliver.py behave on
fixtures, that every example design note carries the example-only QUALITY_BAND_OK line and the template does not, and
that the quality metric is wired into the gate. Run from the repository root:
  python3 tools/selftest_agent_setup.py
"""
import os, re, sys
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'tools')); sys.path.insert(0, os.path.join(ROOT, 'tools', 'lib'))
from check_summary import classify
import deliver

E = []
def need(cond, msg):
    if not cond: E.append(msg)

def read(p):
    f = os.path.join(ROOT, p)
    return open(f, encoding='utf8').read() if os.path.isfile(f) else None

agents = read('AGENTS.md')
need(agents is not None, 'AGENTS.md missing at the repository root')
for p, rx in [('CLAUDE.md', r'^@\.?/?AGENTS\.md\s*$'), ('GEMINI.md', r'^@\.?/?AGENTS\.md\s*$'),
              ('.github/copilot-instructions.md', r'AGENTS\.md'), ('.cursor/rules/vibebroodforge.mdc', r'AGENTS\.md')]:
    t = read(p)
    need(t is not None, f'{p} missing')
    if t: need(re.search(rx, t, re.M), f'{p} does not point to AGENTS.md')
    if t and p != '.cursor/rules/vibebroodforge.mdc': need(len(t) < 2000, f'{p} is longer than a pointer file: keep rules in AGENTS.md')
mdc = read('.cursor/rules/vibebroodforge.mdc') or ''
need(re.match(r'---\n(.*\n)*?alwaysApply:\s*true\n(.*\n)*?---\n', mdc), '.cursor rule lacks frontmatter with alwaysApply: true')
if agents:
    for path in sorted(set(re.findall(r'`((?:tools|docs|templates|data)/[^`\s]+)`', agents))):
        if any(c in path for c in '<*>'): continue
        need(os.path.exists(os.path.join(ROOT, path)), f'AGENTS.md names {path}, which does not exist')
    for must in ('tools/deliver.py', 'docs/lessons.md', 'docs/quality-bar.md', 'Feedback'):
        need(must in agents, f'AGENTS.md no longer mentions {must}')

# classifier fixtures
for text, want in [('RESULT OK (0 FAIL, 0 WARN)', 'OK'), ('  FAIL x: y', 'FAIL'), ('RESULT FAIL objective_paths (3 FAIL)', 'FAIL'),
                   ('INFO hill (mission; FAIL < 25, WARN < 40)\nRESULT check: PASS (0 fails)', 'OK'), ('  WARN z', 'WARN'),
                   ('RESULT FAIL: 1 FAIL', 'FAIL'), ('RESULT OK m.scx (0 FAIL, 4 WATCH)', 'OK'),
                   ('Traceback (most recent call last):\n  File x', 'CRASH')]:
    got = classify(text)[0]
    need(got == want, f'classify({text[:40]!r}) = {got}, want {want}')

# design-note completeness
need(deliver.note_problems('bw', read('templates/Design_Note_example_bw_mission.md') or '') == [],
     'the example design note no longer has every line the gate requires: ' + '; '.join(deliver.note_problems('bw', read('templates/Design_Note_example_bw_mission.md') or '')))
need(len(deliver.note_problems('bw', '# empty note')) >= 6, 'an empty design note is not refused')
tmp = os.path.join(ROOT, 'output', '_selftest_note.md'); os.makedirs(os.path.dirname(tmp), exist_ok=True)
open(tmp, 'w', encoding='utf8').write('The hero walks north.\nDer Held geht nach Norden und kämpft.\n')
need(len(deliver.english_problems(tmp)) == 1, 'German text in a delivered note is not detected')
os.remove(tmp)

# example-only quality exception
import glob
notes = sorted(glob.glob(os.path.join(ROOT, 'tools', 'bw', 'examples', 'ex_*_Design_Note.md'))) + [os.path.join(ROOT, 'templates', 'Design_Note_example_bw_mission.md')]
need(len(notes) == 8, f'expected 7 example design notes plus the template example, found {len(notes)}')
for n in notes:
    need(re.search(r'^QUALITY_BAND_OK: repository example', open(n, encoding='utf8').read(), re.M), f'{os.path.relpath(n, ROOT)} lacks the example QUALITY_BAND_OK line')
need(not re.search(r'^QUALITY_BAND_OK: repository example', read('templates/Design_Note_template.md') or '', re.M), 'the design note template carries the example-only QUALITY_BAND_OK line')
ex = deliver.example_maps()
need(len(ex) == 8 and 'Example_Mission' in ex and 'Ex_Relay_Watch' in ex, f'deliver.example_maps() = {sorted(ex)}')
dsrc = read('tools/deliver.py') or ''
need('tools/bw/quality_metrics.py' in dsrc and os.path.isfile(os.path.join(ROOT, 'tools', 'bw', 'quality_metrics.py')), 'the gate no longer runs tools/bw/quality_metrics.py')
qb = read('docs/quality-bar.md') or ''
sys.path.insert(0, os.path.join(ROOT, 'tools', 'bw'))
try:
    import quality_metrics as QM
    for row in QM.BAND: need(row in qb, f'docs/quality-bar.md does not list the band row {row}')
except Exception as e:
    need(False, f'tools/bw/quality_metrics.py does not import: {e}')
for p in ('README.md', 'AGENTS.md', 'tools/README.md'):
    t = read(p) or ''
    need(not re.search(r'tools/wc3/|docs/wc3-|data/wc3/|\.w3x\b', t), f'{p} names a Warcraft III path (this repository is Brood War only)')

# t1034: opening review, foreign maps, anti-gaming wired up
need('tools/bw/opening_review.py' in dsrc, 'the gate no longer runs tools/bw/opening_review.py')
pre = read('tools/bw/predelivery_check.py') or ''
for mod in ('opening_review', 'check_wave_variety', 'check_check_gaming'):
    need(f'import {mod}' in pre and os.path.isfile(os.path.join(ROOT, 'tools', 'bw', mod + '.py')), f'predelivery_check.py does not run {mod}')
if agents:
    for must in ('opening_review.py', 'Never deliver an existing map', 'Never game a check'):
        need(must in agents, f'AGENTS.md no longer says {must!r}')
for t, want in [('Old Campaign - Chapter Test (Main Run)', True), ('Trigger Test: Outpost', True), ('VibeModForge test', True),
                ('Canopy Vein', False), ('The Testament of Ash', False)]:
    need(bool(deliver.TEST_TITLE.search(t)) == want, f'deliver.TEST_TITLE on {t!r} should be {want}')
need(os.path.isfile(os.path.join(ROOT, 'data', 'bw', 'aiscripts.json')), 'data/bw/aiscripts.json (valid AI script ids) missing')


# self-review, exceptions, review prompt, rules index (t1034 follow-up)
for f in ('templates/Self_Review_template.md', 'tools/lib/self_review.py', 'docs/review-prompt.md', 'docs/bw-mission-rules.md', 'tools/selftest_self_review.py'):
    need(os.path.isfile(os.path.join(ROOT, f)), f + ' is missing')
_dv = read('tools/deliver.py') or ''
need('self_review(mp, rep' in _dv and 'exceptions(text, rep)' in _dv, 'tools/deliver.py no longer runs the self-review and the exception list')
_r = {'problems': []}; deliver.exceptions('SHORTCUT_OK: North Relay :: lift-off :: <reason>\nWAVE_VARIETY_OK: the siege waves are identical on purpose because the story says so\n', _r)
need(len(_r['problems']) == 1 and len(_r['exceptions']) == 2, 'deliver.exceptions does not list both lines and refuse only the placeholder')
_ag = read('AGENTS.md') or ''
for must in ('Self-review', 'docs/review-prompt.md', 'docs/bw-mission-rules.md'):
    need(must in _ag, f'AGENTS.md lost {must!r}')

for e in E: print('FAIL', e)
print('SELFTEST PASS' if not E else f'SELFTEST FAIL ({len(E)})')
sys.exit(1 if E else 0)
