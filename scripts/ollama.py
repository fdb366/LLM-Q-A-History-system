import subprocess

# 定义curl命令
cmd = [
    'curl',
    'http://localhost:11434/api/generate',
    '-d',
    '{"model": "deepseek-r1:7b", "prompt": "你好，你能帮我写一段代码吗？", "stream": true}'
]

# 执行命令并实时输出结果
print("正在调用 Ollama API (stream: true)...")
print("=" * 60)

process = subprocess.Popen(
    cmd,
    stdout=subprocess.PIPE,
    stderr=subprocess.STDOUT,
    text=True,
    shell=True  # 在Windows上使用shell=True
)

for line in process.stdout:
    print(line, end='')

process.wait()
print("=" * 60)
print(f"命令执行完成，返回码: {process.returncode}")
