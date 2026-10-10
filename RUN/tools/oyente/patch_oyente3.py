import re, glob

for path in glob.glob('/home/oyente/oyente3/*.py'):
    with open(path) as f:
        code = f.read()
    orig = code

    # Bug 1: os.system('python ...') must call python3
    code = code.replace("os.system('python ", "os.system('python3 ")
    code = code.replace('os.system("python ', 'os.system("python3 ')

    # Bug 2: subprocess pipes must use text mode in py3
    code = re.sub(
        r'(subprocess\.Popen\([^)]*stdin=subprocess\.PIPE)\)',
        r'\1, universal_newlines=True)',
        code,
    )
    code = re.sub(
        r'(subprocess\.Popen\([^)]*stdout=subprocess\.PIPE)\)',
        r'\1, universal_newlines=True)',
        code,
    )

    if code != orig:
        with open(path, 'w') as f:
            f.write(code)
        print('patched:', path)
