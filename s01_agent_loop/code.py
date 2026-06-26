#!/usr/bin/env python3
"""
s01_agent_loop.py - The Agent Loop
The entire secret of an AI coding agent in one pattern:
    while stop_reason == "tool_use":
        response = LLM(messages, tools)
        execute tools
        append results
    +----------+      +-------+      +---------+
    |   User   | ---> |  LLM  | ---> |  Tool   |
    |  prompt  |      |       |      | execute |
    +----------+      +---+---+      +----+----+
                          ^               |
                          |   tool_result |
                          +---------------+
                          (loop continues)
This is the core loop: feed tool results back to the model
until the model decides to stop. Production agents layer
policy, hooks, and lifecycle controls on top.
Usage:
    pip install anthropic python-dotenv
    ANTHROPIC_API_KEY=... python s01_agent_loop/code.py
"""

import os
import subprocess

try:
  import readline
  # macOS 的 libedit 在处理中文输入时有退格问题，这四行修复它
  readline.parse_and_bind('set bind-tty-special-chars off')
  readline.parse_and_bind('set input-meta on')
  readline.parse_and_bind('set output-meta on')
  readline.parse_and_bind('set convert-meta off')
except ImportError:
  pass

from anthropic import Anthropic
from dotenv import load_dotenv

load_dotenv(override=True)  # Load environment variables from .env file
if os.getenv("ANTHROPIC_BASE_URL"):
  os.environ.pop("ANTHROPIC_AUTH_TOKEN", None)  # Remove ANTHROPIC_AUTH_TOKEN from environment variables

# 检查是否设置了代理环境变量
if os.getenv("HTTP_PROXY") or os.getenv("HTTPS_PROXY"):
    # 如果设置了代理，我们尝试创建客户端时处理可能的导入错误
    try:
        client = Anthropic(
            base_url=os.getenv("ANTHROPIC_BASE_URL"), 
            api_key=os.getenv("ANTHROPIC_API_KEY")  # 修改环境变量名
        )
    except ImportError as e:
        if "socksio" in str(e):
            print("错误：检测到代理设置但缺少 socksio 包。请运行以下命令安装：")
            print("pip install httpx[socks]")
            exit(1)
        else:
            raise e
else:
    # 没有设置代理，直接创建客户端
    client = Anthropic(
        base_url=os.getenv("ANTHROPIC_BASE_URL"), 
        api_key=os.getenv("ANTHROPIC_API_KEY")  # 修改环境变量名
    )

MODEL = os.getenv("MODEL", "deepseek-v4-flash")

SYSTEM = f"You are a coding agent at {os.getcwd()}. Use bash to solve tasks. Act, don't explain."

# ── Tool definition: just bash ────────────────────────────
TOOLS = [
  {
    "name": "bash",
    "description": "Run a shell command.",
    "input_schema": {
      "type": "object",
      "properties": {
        "command": {
          "type": "string",
          "description": "The bash command to run"
        }
      },
      "required": ["command"]
    }
  }
]

# ── Tool execution ────────────────────────────────────────
def run_bash(command: str) -> str:
  dangerous = ["rm -rf /", "sudo", "shutdown", "reboot", "> /dev/"]
  if any(d in command for d in dangerous):
    return "Error: Dangerous command detected. Aborting."
  try:
    r = subprocess.run(command, shell=True, cwd=os.getcwd(), capture_output=True, text=True, timeout=120)
    out = (r.stdout + r.stderr).strip()
    return out[:50000] if out else "(no output)"
  except subprocess.TimeoutExpired:
    return "Error: Timeout (120s)"
  except (FileNotFoundError, OSError) as e:
    return f"Error: {e}"
  
# ── The core pattern: a while loop that calls tools until the model stops ──
def agent_loop(messages: list):
  while True:
    response = client.messages.create(
      model=MODEL,
      system=SYSTEM,
      messages=messages,
      tools=TOOLS,
      max_tokens=8000,
    )
    # Append assistant turn
    messages.append({"role": "assistant", "content": response.content})
    # If the model didn't call a tool, we're done
    if response.stop_reason != "tool_use":
        return
    # Execute each tool call, collect results
    results = []
    for block in response.content:
        if block.type == "tool_use":
            print(f"\033[33m$ {block.input['command']}\033[0m")
            output = run_bash(block.input["command"])
            print(output[:200])
            results.append({
                "type": "tool_result",
                "tool_use_id": block.id,
                "content": output,
            })
    # Feed tool results back, loop continues
    messages.append({"role": "user", "content": results})
# ── Entry point ──────────────────────────────────────────
if __name__ == "__main__":
  print("s01: Agent Loop")
  print("输入问题，回车发送。输入 q 退出。\n")
  history = []
  while True:
      try:
          query = input("\033[36ms01 >> \033[0m")
      except (EOFError, KeyboardInterrupt):
          break
      if query.strip().lower() in ("q", "exit", ""):
          break
      history.append({"role": "user", "content": query})
      agent_loop(history)
      # Print the model's final text response
      response_content = history[-1]["content"]
      if isinstance(response_content, list):
          for block in response_content:
              if getattr(block, "type", None) == "text":
                  print(block.text)
      print()
