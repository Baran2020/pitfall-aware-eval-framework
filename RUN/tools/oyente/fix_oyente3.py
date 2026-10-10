import re, os

files = [
    '/home/oyente/oyente3/oyente.py',
    '/home/oyente/oyente3/symExec.py',
    '/home/oyente/oyente3/utils.py',
]

for fpath in files:
    try:
        content = open(fpath).read()
        content = re.sub(
            r'solc_out\[(\d+)\](?!\.decode)',
            r'solc_out[\1].decode("utf-8","ignore")',
            content
        )
        open(fpath, 'w').write(content)
        print('fixed:', fpath)
    except Exception as e:
        print('skip:', fpath, e)
