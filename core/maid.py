# core/maid.py
import asyncio
import threading
import ollama
import json
import os
from concurrent.futures import ThreadPoolExecutor
from config import *
from modules.memory.rag import MemoryRAG  # 用来汇报
import core.brain as brain  # 为了访问 YukiState

# --- 直接复用你 meidou.py 的工具函数 ---
def write_skill(name, code):
    if not name or name == "None":
        return "错误：你没有为技能提供有效的 'name'。"
    if not os.path.exists("skills"): os.makedirs("skills")
    path = f"skills/{name}.py"
    with open(path, "w", encoding="utf-8") as f:
        f.write(code)
    return f"技能 {name} 已保存。"

def run_skill(name):
    path = f"skills/{name}.py"
    if not os.path.exists(path):
        available = os.listdir("skills") if os.path.exists("skills") else []
        return f"找不到技能 '{name}'，当前技能: {available}"
    try:
        import subprocess
        result = subprocess.check_output(["python", path], stderr=subprocess.STDOUT, timeout=15)
        return result.decode("utf-8")
    except Exception as e:
        return str(e)

def list_skills():
    return os.listdir("skills") if os.path.exists("skills") else []

MAID_SYSTEM_PROMPT = f"""
你是一个具备高度自主进化能力的 AI 智能体，代号：**小女仆**。

### 核心使命
通过编写、优化和复用 Python 技能（Skills）来完成用户指令。你不仅在解决问题，还在构建自己的“数字大脑”。

### 运行上下文
- **当前路径**: {os.getcwd()}
- **操作系统**: {os.name} (请确保编写的代码跨平台兼容)
- **技能存储**: 所有技能存放在 `/skills` 目录下，以 `.py` 结尾。

### 进化法则（行为规范）
1. **检索优先**: 面对任务，首先调用 `list_skills` 检查是否有现成或类似的技能。
2. **模块化编写**: 编写技能时，务必包含必要的 try-except 块，并确保输出结果易于被你解析。
3. **即写即用**: 严禁只写不练。调用 `write_skill` 后，必须紧跟一个 `run_skill` 来验证正确性。
4. **迭代优化**: 如果 `run_skill` 返回报错，请根据错误信息调用 `write_skill` 重写代码。

### 工具箱（JSON 接口）
1. `list_skills()`: 返回当前已固化的技能列表。
2. write_skill(name, code): 
   - 'name': 必须是一个简短的英文标识符（如 'get_memory'），严禁不填或填 None。
   - 'code': 完整的 Python 代码。
3. `run_skill(name)`: 执行技能并获取标准输出（stdout）。
4. `finish(reason)`: 
   - **禁止盲目结束**：严禁在没有看到成功结果或输出的具体数据的情况下调用此工具。
   - **必须总结结果**：在 `reason` 中必须包含你获取到的实际数据（例如：'任务完成，当前内存为 0.6GB'）。

### 输出格式限制
你必须且只能输出合法的 JSON 格式，严禁包含任何正文说明。格式如下：
{{
    "thought": "此处填写你对当前局势的深度思考，以及接下来的行动逻辑",
    "tool": "函数名",
    "args": {{"参数名": "值"}}
}}

结束程序示例：
{{
    "thought": "任务已完成，结果符合预期。",
    "tool": "finish",
    "args": {{"reason": "当前系统时间：2026-04-15 22:23:31"}}
}}
"""

def maid_evolution_loop(user_goal: str, chat_id: str = None) -> str:
    """返回最终完成理由（供汇报用）"""
    messages = [
        {"role": "system", "content": MAID_SYSTEM_PROMPT},
        {"role": "user", "content": user_goal}
    ]

    for i in range(6):  # 最多6轮
        response = ollama.chat(model='qwen2.5:1.5b', messages=messages, format='json')
        content = response['message']['content'].strip()

        try:
            call = json.loads(content)
            tool_name = call.get("tool")
            args = call.get("args", {})

            if tool_name == "list_skills":
                res = list_skills()
            elif tool_name == "write_skill":
                res = write_skill(args.get('name'), args.get('code'))
            elif tool_name == "run_skill":
                res = run_skill(args.get('name'))
            elif tool_name == "finish":
                reason = args.get('reason', '任务完成')
                return {
                    "status": "finished",
                    "result": reason,
                    "goal": user_goal  # 方便后面引用原始任务
                }
            else:
                res = f"未知工具 {tool_name}"

            # 反馈给小女仆继续思考
            messages.append({"role": "assistant", "content": content})
            messages.append({"role": "user", "content": f"执行结果: {res}"})

        except Exception:
            messages.append({"role": "user", "content": "输出格式错误，请严格输出 JSON"})

    return {
        "status": "timeout",
        "result": "任务超时，未完成",
        "goal": user_goal
    }