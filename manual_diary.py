#!/usr/bin/env python
# manual_diary.py - 手动触发Yuki写日记
import asyncio
import json
import datetime
import sys
import argparse

# 导入所需模块
from yuki_core import YukiState, HistoryManager, BASE_SETTING
from config import (
    DEEPSEEK_API_KEY, DEEPSEEK_BASE_URL,
    KEEP_LAST_DIALOGUE
)
from memory_rag import memory_rag

# 初始化必要组件（与bot_main中一致）
yuki = YukiState(DEEPSEEK_API_KEY, DEEPSEEK_BASE_URL)
history_manager = HistoryManager()

async def summarize_memory(chat_id, history):
    """复制自 bot_main.py 的 summarize_memory，但依赖全局的 yuki 和 memory_rag"""
    print(f"[{chat_id}] 手动触发：正在写日记回顾...")
    dialogue_msgs = [msg for msg in history if msg["role"] != "system"]
    content_to_summarize = json.dumps(dialogue_msgs, ensure_ascii=False)
    time_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    summary_prompt = f"你现在是 Yuki。请以 Yuki 的口吻写一篇 150 字以内的日记，总结这段对话。要求真实记录，尤其是叙述和性格概述。当前时间：{time_str}"
    try:
        response = yuki.client.chat.completions.create(
            model="deepseek-chat",
            messages=[
                {"role": "system", "content": f"{BASE_SETTING}"},
                {"role": "user", "content": f"{summary_prompt}\n\n内容如下：\n{content_to_summarize}"}
            ]
        )
        diary_entry = response.choices[0].message.content
        # 存入向量记忆库
        memory_rag.save_diary(diary_entry, chat_id=chat_id)
        print(f"✅ 日记已生成并存入记忆库：\n{diary_entry}\n")

        # 构建新历史（用于更新文件）
        system_messages = [msg for msg in history if msg["role"] == "system"]
        new_diary_node = {"role": "system", "content": f"【日记({time_str})】：\n{diary_entry}"}
        recent_dialogue = dialogue_msgs[-KEEP_LAST_DIALOGUE:]  # 保留最近对话
        new_history = system_messages + [new_diary_node] + recent_dialogue
        return new_history, diary_entry
    except Exception as e:
        print(f"❌ 写日记失败: {e}")
        return history, None

async def main():
    parser = argparse.ArgumentParser(description="手动触发Yuki写日记")
    parser.add_argument("chat_id", help="要处理的聊天ID（群号或QQ号）")
    parser.add_argument("--update", action="store_true", help="是否更新历史文件（压缩历史）")
    args = parser.parse_args()

    chat_id = args.chat_id
    cid = str(chat_id)

    # 加载历史
    history_dict = history_manager.load()
    if cid not in history_dict:
        print(f"❌ 聊天 {chat_id} 不存在于历史文件中。")
        return

    history = history_dict[cid]
    print(f"📖 加载聊天 {chat_id}，当前历史长度：{len(history)} 条")

    # 执行写日记
    new_history, diary = await summarize_memory(chat_id, history)

    if diary is None:
        print("❌ 写日记失败，终止。")
        return

    # 如果要求更新历史文件
    if args.update:
        history_dict[cid] = new_history
        history_manager.save(history_dict)
        print(f"✅ 历史文件已更新，新历史长度：{len(new_history)} 条")
    else:
        print("ℹ️ 历史文件未修改（未使用 --update）")

if __name__ == "__main__":
    asyncio.run(main())