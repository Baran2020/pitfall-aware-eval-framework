import sys
sys.path.insert(0, '/app')
from toolwrapper_oyente import load_flat_file, KEYWORDS
import subprocess, tempfile, os, hashlib

records = load_flat_file('/data/dataset.txt')

# ---------- CHECK 1: parsing sanity ----------
print("=" * 60)
print("CHECK 1: dataset parsing")
print("=" * 60)
print("total records:", len(records))
n_l1 = sum(1 for r in records if r['label'] == 1)
n_l0 = sum(1 for r in records if r['label'] == 0)
n_ln = sum(1 for r in records if r['label'] is None)
print("label=1: %d, label=0: %d, label=None: %d" % (n_l1, n_l0, n_ln))

bad = 0
for r in records:
    s = r['source']
    # each record must look like a complete contract
    if 'contract' not in s:
        print("  [WARN] %s: no 'contract' keyword!" % r['id'])
        bad += 1
    # label digits must NOT remain inside source (parsing leak check)
    last = s.strip().splitlines()[-1].strip() if s.strip() else ''
    if last in ('0', '1'):
        print("  [WARN] %s: label leaked into source!" % r['id'])
        bad += 1
    # one record must not contain a second file header
    if '.sol' in s and s.count('pragma') > 3:
        print("  [WARN] %s: possibly merged contracts (pragma x%d)" % (r['id'], s.count('pragma')))
        bad += 1
print("parsing issues:", bad)

# duplicate id check (same id = label/source mixup risk)
ids = [r['id'] for r in records]
dups = set(i for i in ids if ids.count(i) > 1)
if dups:
    print("  [WARN] duplicate ids:", list(dups)[:10])

# ---------- CHECK 2 + 3: replay 6 contracts end-to-end ----------
print()
print("=" * 60)
print("CHECK 2+3: end-to-end replay (3 FP-candidates, 3 FN-candidates)")
print("=" * 60)

def run_oyente(source):
    tmp = tempfile.NamedTemporaryFile(suffix='.sol', delete=False, mode='w')
    tmp.write(source); tmp.close()
    # verify file on disk == source we intended (CHECK 2)
    on_disk = open(tmp.name).read()
    same = hashlib.md5(on_disk.encode()).hexdigest() == hashlib.md5(source.encode()).hexdigest()
    p = subprocess.Popen(['python2', '/home/oyente/oyente/oyente.py', tmp.name],
                         stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                         cwd='/home/oyente/oyente')
    out, err = p.communicate(timeout=120)
    os.remove(tmp.name)
    text = (out.decode('utf-8','ignore') + '\n' + err.decode('utf-8','ignore')).lower()
    return text, same

# pick first 3 with label=0 and first 3 with label=1
sample = [r for r in records if r['label'] == 0][:3] + \
         [r for r in records if r['label'] == 1][:3]

for r in sample:
    text, file_ok = run_oyente(r['source'])
    # extract the exact verdict line oyente printed
    verdict = [l.strip() for l in text.splitlines() if 'reentrancy bug exists' in l]
    pred = 1 if any(k in text for k in KEYWORDS) else (0 if verdict else None)
    print("\n--- %s (label=%s) ---" % (r['id'], r['label']))
    print("file integrity ok:", file_ok)
    print("oyente verdict line:", verdict if verdict else "NOT FOUND")
    print("wrapper would predict:", pred)
    print("call.value in source:", 'call.value' in r['source'])
    print("source first line:", r['source'].splitlines()[0][:80])
