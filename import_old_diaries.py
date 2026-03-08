# import_old_diaries.py
import json
import re
from memory_rag import memory_rag


def import_old_diaries_from_history(history_file):
    print(f"📂 正在加载历史文件: {history_file}")
    with open(history_file, 'r', encoding='utf-8') as f:
        data = json.load(f)

    diary_pattern = r'【日记\(.*?\)】：\n(.*)'
    total_count = 0
    chat_count = 0

    for chat_id, messages in data.items():
        chat_count += 1
        chat_diary_count = 0
        for msg in messages:
            if msg.get("role") == "system":
                content = msg.get("content", "")
                match = re.search(diary_pattern, content, re.DOTALL)
                if match:
                    diary_text = match.group(1).strip()
                    # 传入 chat_id
                    memory_rag.save_diary(diary_text, chat_id=chat_id)
                    chat_diary_count += 1
                    total_count += 1
        print(f"  聊天 {chat_id}: 找到 {chat_diary_count} 条日记")

    print(f"✅ 导入完成！总共处理 {chat_count} 个聊天，导入 {total_count} 条日记。")


if __name__ == "__main__":
    import_old_diaries_from_history("chat_history.json")