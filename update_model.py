import re

with open('backend/agent.py', 'r', encoding='utf-8') as f:
    code = f.read()

code = re.sub(r'MODEL\s*=\s*"[^"]+"', 'MODEL = "gpt-oss-120b"', code)
code = re.sub(r"MODEL\s*=\s*'[^']+'", 'MODEL = "gpt-oss-120b"', code)

with open('backend/agent.py', 'w', encoding='utf-8') as f:
    f.write(code)

print('Updated model to gpt-oss-120b')
