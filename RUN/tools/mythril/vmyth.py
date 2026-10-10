import sys, os, tempfile, subprocess, json
sys.path.insert(0, '/app')
from toolwrapper_mythril import parse_file, SOLC_VERSION

records = list(parse_file('/data/dataset.txt'))

print("CHECK 1: parsing")
print("total:", len(records))
l1 = sum(1 for _,lb,_ in records if lb == 1)
l0 = sum(1 for _,lb,_ in records if lb == 0)
ln = sum(1 for _,lb,_ in records if lb is None)
print("label=1:%d label=0:%d None:%d" % (l1, l0, ln))

print("CHECK 2: mythril raw output")
sample = [r for r in records if r[1]==0][:1] + [r for r in records if r[1]==1][:1]
for frag, lb, name in sample:
    print("---", name, "label=", lb, "---")
    tmp = tempfile.NamedTemporaryFile(suffix=".sol", delete=False, mode="w")
    tmp.write("\n".join(frag)); tmp.close()
    cmd = ["myth","analyze",tmp.name,"-o","json","--solv",SOLC_VERSION,"--execution-timeout","60","--no-onchain-data"]
    p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    out, err = p.communicate(timeout=120)
    print("returncode:", p.returncode)
    print("STDOUT:", out.decode("utf-8","ignore")[:800])
    print("STDERR:", err.decode("utf-8","ignore")[:400])
    os.remove(tmp.name)
