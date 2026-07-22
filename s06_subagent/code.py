#!/usr/bin/env python3
"""
s06: Subagent — spawn sub-agents with fresh messages[] for context isolation.
  Parent Agent                           Subagent
  +------------------+                  +------------------+
  | messages=[...]   |                  | messages=[task]  | <-- fresh
  |                  |   dispatch       |                  |
  | tool: task       | ---------------> | own while loop   |
  |   prompt="..."   |                  |   bash/read/...  |
  |                  |   summary only   |   (max 30 turns) |
  | result = "..."   | <--------------- | return last text |
  +------------------+                  +------------------+
        ^                                      |
        |       intermediate results DISCARDED  |
        +--------------------------------------+
  Subagent tools: bash, read, write, edit, glob (NO task — no recursion)
Changes from s05:
  + task tool + spawn_subagent() with fresh messages[]
  + Safety limit: max 30 turns per subagent
  + extract_text() helper
  Subagent cannot spawn sub-subagents (no task tool in sub_tools).
  Main loop unchanged: task auto-dispatches via TOOL_HANDLERS.
Run: python s06_subagent/code.py
Needs: pip install anthropic python-dotenv + ANTHROPIC_API_KEY in .env
"""

import ast, json, os, subprocess
from pathlib import Path

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
WORKDIR = Path.cwd()
CURRENT_TODOS: list[dict] = []

SYSTEM = (
  f"You are a coding agent at {WORKDIR}. "
  "For complex sub-problems, use the task tool to spawn a subagent."
)

# s06: subagent gets its own system prompt — no task, no recursion
SUB_SYSTEM = (
  f"You are a coding agent at {WORKDIR}. "
  "Complete the task you were given, then return a concise summary. "
  "Do not delegate further."
)

# ═══════════════════════════════════════════════════════════
#  FROM s02-s05 (unchanged): Tool Implementations
# ═══════════════════════════════════════════════════════════

def run_bash(command: str) -> str:
  dangerous = ["rm -rf /", "sudo", "shutdown", "reboot", "> /dev/"]
  if any(d in command for d in dangerous):
    return "Error: Dangerous command detected. Aborting."
  try:
    r = subprocess.run(command, shell=True, cwd=WORKDIR, capture_output=True, text=True, timeout=120, errors="ignore")
    out = (r.stdout + r.stderr).strip()
    return out[:50000] if out else "(no output)"
  except subprocess.TimeoutExpired:
    return "Error: Timeout (120s)"
  except (FileNotFoundError, OSError) as e:
    return f"Error: {e}"

# ═══════════════════════════════════════════════════════════
#  NEW in s02: 4 个新工具
# ═══════════════════════════════════════════════════════════

def safe_path(p: str) -> Path:
  path = (WORKDIR / p).resolve()
  if not path.is_relative_to(WORKDIR):
    raise ValueError(f"Path escapes workspace: {p}")
  return path

def run_read(path: str, limit: int | None = None) -> str:
   try:
      lines = safe_path(path).read_text().splitlines()
      if limit and limit < len(lines):
          lines = lines[:limit] + [f"... ({len(lines) - limit} more lines)"]
      return "\n".join(lines)
   except Exception as e:
      return f"Error: {e}"

def run_write(path: str, content: str) -> str:
   try:
      file_path = safe_path(path)
      file_path.parent.mkdir(parents=True, exist_ok=True)
      file_path.write_text(content)
      return f"Wrote {len(content)} bytes to {path}"
   except Exception as e:
      return f"Error: {e}"

def run_edit(path: str, old_text: str, new_text: str) -> str:
   try:
      file_path = safe_path(path)
      text = file_path.read_text()
      if old_text not in text:
         return f"Error: text not found in {path}"
      file_path.write_text(text.replace(old_text, new_text, 1))
      return f"Edited {path}"
   except Exception as e:
      return f"Error: {e}"
   
def run_glob(pattern: str) -> str:
   import glob as g
   try:
      results = []
      for match in g.glob(pattern, root_dir=WORKDIR):
         if (WORKDIR / match).resolve().is_relative_to(WORKDIR):
            results.append(match)
      return "\n".join(results) if results else "(no matches)"
   except Exception as e:
      return f"Error: {e}"
   
# ═══════════════════════════════════════════════════════════
#  NEW in s05: todo_write tool — plan only, no execution
# ═══════════════════════════════════════════════════════════
def _normalize_todos(todos):
  if isinstance(todos, str):
    try:
      todos = json.loads(todos)
    except json.JSONDecodeError:
      try:
        todos = ast.literal_eval(todos)
      except (SyntaxError, ValueError):
        return None, "Error: todos must be a list or JSON array string"
  if not isinstance(todos, list):
    return None, "Error: todos must be a list"
  for i, t in enumerate(todos):
    if not isinstance(t, dict):
      return None, f"Error: todos[{i}] must be an object"
    if "content" not in t or "status" not in t:
      return None, f"Error: todos[{i}] missing 'content' or 'status'"
    if t["status"] not in ["pending", "in_progress", "completed"]:
      return None, f"Error: todos[{i}] has invalid status '{t['status']}'"
  return todos, None

def run_todo_write(todos: list) -> str:
  global CURRENT_TODOS
  todos, err = _normalize_todos(todos)
  if err:
    return err
  CURRENT_TODOS = todos
  lines = ["\n\033[33m## Current Tasks\033[0m"]
  for t in CURRENT_TODOS:
    icon = {"pending": " ", "in_progress": "\033[36m▸\033[0m", "completed": "\033[32m✓\033[0m"}[t["status"]]
    lines.append(f"  [{icon}] {t['content']}")
  print("\n".join(lines))
  return f"Updated {len(CURRENT_TODOS)} tasks"
# ═══════════════════════════════════════════════════════════
#  NEW in s02: 工具定义（s01 只有一个 bash，现在扩展到 5 个）
# ═══════════════════════════════════════════════════════════
TOOLS = [
    {"name": "bash", "description": "Run a shell command.",
     "input_schema": {"type": "object", "properties": {"command": {"type": "string"}}, "required": ["command"]}},
    {"name": "read_file", "description": "Read file contents.",
     "input_schema": {"type": "object", "properties": {"path": {"type": "string"}, "limit": {"type": "integer"}}, "required": ["path"]}},
    {"name": "write_file", "description": "Write content to a file.",
     "input_schema": {"type": "object", "properties": {"path": {"type": "string"}, "content": {"type": "string"}}, "required": ["path", "content"]}},
    {"name": "edit_file", "description": "Replace exact text in a file once.",
     "input_schema": {"type": "object", "properties": {"path": {"type": "string"}, "old_text": {"type": "string"}, "new_text": {"type": "string"}}, "required": ["path", "old_text", "new_text"]}},
    {"name": "glob", "description": "Find files matching a glob pattern.",
     "input_schema": {"type": "object", "properties": {"pattern": {"type": "string"}}, "required": ["pattern"]}},
    # s05: new tool
    {"name": "todo_write", "description": "Create and manage a task list for your current coding session.",
     "input_schema": {"type": "object", "properties": {"todos": {"type": "array", "items": {"type": "object", "properties": {"content": {"type": "string"}, "status": {"type": "string", "enum": ["pending", "in_progress", "completed"]}}, "required": ["content", "status"]}}}, "required": ["todos"]}},
]

# ═══════════════════════════════════════════════════════════
#  NEW in s02: 工具分发映射（s01 是硬编码 run_bash，现在改为查表）
# ═══════════════════════════════════════════════════════════
TOOL_HANDLERS = {
    "bash": run_bash, "read_file": run_read, "write_file": run_write,
    "edit_file": run_edit, "glob": run_glob, "todo_write": run_todo_write,
}

# ═══════════════════════════════════════════════════════════
#  NEW in s06: Subagent — fresh messages[], summary only
# ═══════════════════════════════════════════════════════════
SUB_TOOLS = [
  {"name": "bash", "description": "Run a shell command.",
    "input_schema": {"type": "object", "properties": {"command": {"type": "string"}}, "required": ["command"]}},
  {"name": "read_file", "description": "Read file contents.",
    "input_schema": {"type": "object", "properties": {"path": {"type": "string"}}, "required": ["path"]}},
  {"name": "write_file", "description": "Write content to a file.",
    "input_schema": {"type": "object", "properties": {"path": {"type": "string"}, "content": {"type": "string"}}, "required": ["path", "content"]}},
  {"name": "edit_file", "description": "Replace exact text in a file once.",
    "input_schema": {"type": "object", "properties": {"path": {"type": "string"}, "old_text": {"type": "string"}, "new_text": {"type": "string"}}, "required": ["path", "old_text", "new_text"]}},
  {"name": "glob", "description": "Find files matching a glob pattern.",
    "input_schema": {"type": "object", "properties": {"pattern": {"type": "string"}}, "required": ["pattern"]}},
]

# NO "task" tool — prevent recursive spawning
SUB_HANDLERS = {
  "bash": run_bash, "read_file": run_read, "write_file": run_write,
  "edit_file": run_edit, "glob": run_glob,
}

def extract_text(content) -> str:
  """Extract text from message content blocks."""
  if not isinstance(content, list):
    return str(content)
  return "\n".join(getattr(b, "text", "") for b in content if getattr(b, "type", None) == "text")

def spawn_subagent(description: str) -> str:
  """Spawn a subagent with fresh messages[], return summary only."""
  print(f"\n\033[35m[Subagent spawned]\033[0m")
  messages = [{"role": "user", "content": description}]  # fresh context
  for _ in range(30): # safety limit
    response = client.messages.create(model=MODEL, system=SUB_SYSTEM, messages=messages, tools=SUB_TOOLS, max_tokens=8000)
    messages.append({"role": "assistant", "content": response.content})
    if response.stop_reason != "tool_use":
      break
    results = []
    for block in response.content:
      if block.type == "tool_use":
        # Issue 1: subagent also runs hooks (permissions apply)
        blocked = trigger_hooks("PreToolUse", block)
        if blocked:
          results.append({"type": "tool_result", "tool_use_id": block.id, "content": str(blocked)})
          continue
        handler = SUB_HANDLERS.get(block.name)
        output = handler(**block.input) if handler else f"Unknown: {block.name}"
        trigger_hooks("PostToolUse", block, output)
        print(f"  \033[90m[sub] {block.name}: {str(output)[:100]}\033[0m")
        results.append({"type": "tool_result", "tool_use_id": block.id, "content": output})
    messages.append({"role": "user", "content": results})
  
  # Issue 5: fallback if safety limit hit during tool_use
  result = extract_text(messages[-1]["content"])
  if not result:
    # last message is tool_result, look backwards for assistant text
    for msg in reversed(messages):
      if msg.get("role") == "assistant":
        result = extract_text(msg.content)
        if result:
          break
    if not result:
      result = "Subagent stopped after 30 turns without final answer."
  print(f"\033[35m[Subagent done]\033[0m")
  return result  # only summary, entire message history discarded


# Add task tool to parent's tools
TOOLS.append({
    "name": "task",
    "description": "Launch a subagent to handle a complex subtask. Returns only the final conclusion.",
    "input_schema": {"type": "object", "properties": {"description": {"type": "string"}}, "required": ["description"]},
})
TOOL_HANDLERS["task"] = spawn_subagent

# ═══════════════════════════════════════════════════════════
#  NEW in s04: Hook System (s03 permission logic now via hooks)
# ═══════════════════════════════════════════════════════════
HOOKS = {"UserPromptSubmit": [], "PreToolUse": [], "PostToolUse": [], "Stop": []}

def register_hook(event: str, callback):
  HOOKS[event].append(callback)

def trigger_hooks(event: str, *args):
  for callback in HOOKS.get(event, []):
    result = callback(*args)
    if result is not None:
      return result
  return None

# ═══════════════════════════════════════════════════════════
#  NEW in s03: Three-Gate Permission Pipeline
# ═══════════════════════════════════════════════════════════

# Gate 1: Hard deny list — always forbidden
DENY_LIST = ["rm -rf /", "sudo", "shutdown", "reboot", "mkfs", "dd if=", "> /dev/sda"]
DESTRUCTIVE = ["rm ", "> /etc/", "chmod 777"]

def permission_hook(block) -> bool:
  """PreToolUse: s03 check_permission() logic moved here."""
  if block.name == "bash":
    for pattern in DENY_LIST:
      if pattern in block.input.get("command", ""):
        print(f"\n\033[31m⛔ Blocked: '{pattern}'\033[0m")
        return "Permission denied by deny list"
    for kw in DESTRUCTIVE:
      if kw in block.input.get("command", ""):
        print(f"\n\033[33m⚠  Potentially destructive command\033[0m")
        print(f"   Tool: {block.name}({block.input})")
        choice = input("   Allow? [y/N] ").strip().lower()
        if choice not in ["y", "yes"]:
          return "Permission denied by user"
  if block.name in ["write_file", "edit_file"]:
    path = block.input.get("path", "")
    if not (WORKDIR / path).resolve().is_relative_to(WORKDIR):
      print(f"\n\033[33m⚠  Writing outside workspace\033[0m")
      print(f"   Tool: {block.name}({block.input})")
      choice = input("   Allow? [y/N] ").strip().lower()
      if choice not in ["y", "yes"]:
        return "Permission denied by user"
  return None

def log_hook(block):
  """PreToolUse: log every tool call."""
  args_preview = str(list(block.input.values())[:2])[:60000]
  print(f"\033[90m[HOOK] {block.name}({args_preview})\033[0m")
  return None

def large_output_hook(block, output):
  """PostToolUse: warn on large output."""
  if len(str(output)) > 100000:
    print(f"\033[33m[HOOK] ⚠ Large output from {block.name}: {len(str(output))} chars\033[0m")
  return None

# UserPromptSubmit hook: log user input before it reaches the LLM
def context_inject_hook(query: str):
  print(f"\033[90m[HOOK] UserPromptSubmit: working in {WORKDIR}\033[0m")
  return None

# Stop hook: print summary when loop is about to exit
def summary_hook(messages: list):
  tool_count = sum(1 for m in messages
              for b in (m.get("content") if isinstance(m.get("content"), list) else [])
              if isinstance(b, dict) and b.get("type") == "tool_result")
  print(f"\033[90m[HOOK] Stop: session used {tool_count} tool calls\033[0m")
  return None

register_hook("UserPromptSubmit", context_inject_hook)
register_hook("PreToolUse", permission_hook)
register_hook("PreToolUse", log_hook)
register_hook("PostToolUse", large_output_hook)
register_hook("Stop", summary_hook)

# ═══════════════════════════════════════════════════════════
#  agent_loop — same as s05 + nag reminder, task auto-dispatches
# ═══════════════════════════════════════════════════════════

rounds_since_todo = 0

def agent_loop(messages: list):
  global rounds_since_todo
  while True:
    # s05: nag reminder — inject if model hasn't updated todos for 3 rounds
    if rounds_since_todo > 3 and messages:
      messages.append({"role": "user", "content": "<reminder>Update your todos.</reminder>"})
      rounds_since_todo = 0
      
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
        force = trigger_hooks("Stop", messages)
        if force:
          messages.append({"role": "user", "content": force})
          continue
        return
    # Execute each tool call, collect results
    rounds_since_todo += 1
    results = []
    for block in response.content:
        if block.type != "tool_use":
          continue
        # s04 change: hook replaces hard-coded check_permission()
        blocked = trigger_hooks("PreToolUse", block)
        if blocked:
          results.append({"type": "tool_result", "tool_use_id": block.id, "content": str(blocked)})
          continue
        handler = TOOL_HANDLERS.get(block.name)
        output = handler(**block.input) if handler else f"Error: No handler for tool {block.name}"
        trigger_hooks("PostToolUse", block, output)
        # s05: reset nag counter when todo_write is called
        if block.name == "todo_write":
          rounds_since_todo = 0
        results.append({"type": "tool_result", "tool_use_id": block.id, "content": output})
    messages.append({"role": "user", "content": results})


# ── Entry point ──────────────────────────────────────────
if __name__ == "__main__":
    print("s06: Subagent — spawn sub-agents with fresh context, summary only")
    print("Type a question, press Enter. Type q to quit.\n")
    
    history = []
    while True:
        try:
            query = input("\033[36ms04 >> \033[0m")
        except (EOFError, KeyboardInterrupt):
            break
        if query.strip().lower() in ("q", "exit", ""):
            break
        trigger_hooks("UserPromptSubmit", query)
        history.append({"role": "user", "content": query})
        agent_loop(history)
        for block in history[-1]["content"]:
            if getattr(block, "type", None) == "text":
                print(block.text)
        print()
