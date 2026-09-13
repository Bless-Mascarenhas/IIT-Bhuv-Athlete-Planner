import re

with open('backend/agent.py', 'r', encoding='utf-8') as f:
    code = f.read()

code = code.replace('MODEL = "llama3-70b-versatile"', 'MODEL = "llama-3.1-70b-versatile"')
code = code.replace('MODEL = "llama-3-70b-versatile"', 'MODEL = "llama-3.1-70b-versatile"')
code = code.replace('MODEL="llama3-70b-versatile"', 'MODEL="llama-3.1-70b-versatile"')

with open('backend/agent.py', 'w', encoding='utf-8') as f:
    f.write(code)

print('Agent updated.')
