#INPUT_PATH = r"F:\LISTTOOL\TL31\ReCheckermaster\train_data\user\user.txt"
#OUTPUT_PATH = r"F:\LISTTOOL\TL31\ReCheckermaster\train_data\user\labels.txt"

#INPUT_PATH = r"F:\LISTTOOL\TL3\CBGRU\train_data\user\user.txt"
#OUTPUT_PATH  = r"F:\LISTTOOL\TL3\CBGRU\train_data\user\labels.txt"

INPUT_PATH = r"F:\LISTTOOL\TL4\WIDENNET\config\train_data\user.txt"
OUTPUT_PATH = r"F:\LISTTOOL\TL4\WIDENNET\config\train_data\labels.txt"


import re
def is_sol_name(line):
    return re.match(r"^\s*\d+\.sol\s*$", line) is not None
def is_separator(line):
    return set(line.strip()) == {"-"} and len(line.strip()) > 0
with open(INPUT_PATH, "r", encoding="utf-8", errors="ignore") as f:
    lines = f.readlines()
results = []
i = 0
n = len(lines)
while i < n:
    if is_sol_name(lines[i]):
        sol_name = lines[i].strip()
        j = i + 1
        while j < n and not is_separator(lines[j]):
            j += 1
        label = ""
        if j - 1 > i and lines[j - 1].strip() in ("0", "1"):
            label = lines[j - 1].strip()
        results.append(f"{sol_name} {label}")
        i = j + 1
    else:
        i += 1
with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
    f.write("\n".join(results) + "\n")

count_1 = sum(1 for r in results if r.endswith(" 1"))
count_0 = sum(1 for r in results if r.endswith(" 0"))
count_blank = len(results) - count_1 - count_0

print(f"Found {len(results)} fragments")
print(f"Output: {OUTPUT_PATH}")
print(f"label 1: {count_1}")
print(f"label 0: {count_0}")
if count_blank:
    print(f"no label found: {count_blank}")
