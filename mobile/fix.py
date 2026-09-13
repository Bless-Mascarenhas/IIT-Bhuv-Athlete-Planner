with open('src/services/health/NativeHealthProvider.ts', 'r') as f:
    content = f.read()

content = content.replace("import('@capawesome-team/capacitor-health')", "import(/* @vite-ignore */ ''.concat('@capawesome-team/capacitor-health'))")

with open('src/services/health/NativeHealthProvider.ts', 'w') as f:
    f.write(content)
