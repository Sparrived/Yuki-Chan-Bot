import os
import shutil
import subprocess
import sys

# uv 环境提示：如果检测到 uv 但未在虚拟环境中运行，给出友好提示
if shutil.which("uv") and sys.prefix == sys.base_prefix:
    venv_python = os.path.join(".venv", "Scripts", "python.exe") if sys.platform == "win32" else os.path.join(".venv", "bin", "python")
    if os.path.exists(venv_python):
        print("💡 检测到 uv 虚拟环境存在，但未激活。")
        print("   请使用以下命令运行 setup.py：")
        print(f"   uv run python setup.py")
        print("   或先激活虚拟环境后再运行。\n")

def ensure_dirs():
    """确保必要的文件夹存在"""
    dirs = ["./models", "./data", "./yuki_memory", "./logs"]
    for d in dirs:
        if not os.path.exists(d):
            os.makedirs(d)
            print(f"已创建文件夹: {d}")

def ensure_files():
    """确保必要的文件存在并有初始内容"""
    # 1. 自动生成初始黑名单
    if not os.path.exists("blacklist.txt"):
        with open("blacklist.txt", "w", encoding="utf-8") as f:
            f.write("yuki\n主人\n哥哥\n池宇健\n人家")
        print("已生成初始 blacklist.txt")
    else:
        print("📝 已存在 blacklist.txt，跳过")

    # 2. 自动生成 .gitignore
    gitignore_content = """.idea/
.env
.vscode/
__pycache__/
yuki_memory/
models/
data/
project_for_ai.txt
models.zip
skills/
core/skills
logs/
core/tasks
configs/config.yaml
.venv/
"""
    if not os.path.exists(".gitignore"):
        with open(".gitignore", "w", encoding="utf-8") as f:
            f.write(gitignore_content)
        print("🛡️ 已生成 .gitignore")
    else:
        with open(".gitignore", "r", encoding="utf-8") as f:
            existing = f.read()
        if "configs/config.yaml" not in existing:
            with open(".gitignore", "a", encoding="utf-8") as f:
                f.write("\nconfigs/config.yaml\n")
            print("🛡️ 已追加 configs/config.yaml 到 .gitignore")
        else:
            print("已存在 .gitignore，跳过")

    # 3. 自动生成初始 configs/config.yaml
    os.makedirs("configs", exist_ok=True)
    if not os.path.exists("configs/config.yaml"):
        default_config = '''# Yuki-Chan Bot 配置文件
# 所有配置均在此文件管理，请勿提交到 Git
# 本文件已在 .gitignore 中

# ================= 机器人身份 =================
robot_name: "yuki"
master_name: "主人"

# ================= 安全配置 =================
max_message_length: 150                # 单条消息最大长度，防止 token 炸弹

# ================= API 配置 =================
api:
  llm_base_url: "https://api.deepseek.com/v1"
  deepseek_base_url: "https://api.deepseek.com/v1"
  image_process_url: "https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions"
  llm_api_key: ""                      # 首选 LLM API Key
  backup_api_key: ""                   # 备选 API Key（留空则使用 llm_api_key）
  image_process_api_key: ""            # 图像处理 API Key

# ================= 模型配置 =================
model:
  llm: "deepseek-chat"                 # 主对话模型
  backup: "deepseek-chat"              # 备用对话模型
  vision: "qwen3-vl-flash"             # 视觉/多模态模型；如不需要可留空 ""

# ================= 连接配置 =================
connection:
  napcat_ws_url: "ws://127.0.0.1:3001"
  max_retries: 3

# ================= 目标配置 =================
target:
  qq: 0                                # 私聊目标 QQ 号
  groups: []                           # 目标群聊 QQ 号列表，如 [123456, 789012]

# ================= 日记触发配置 =================
diary:
  idle_seconds: 120                    # 空闲多久后触发日记（秒）
  min_turns: 15                        # 最小对话轮数阈值
  max_length: 50                       # 历史记录超过此条数强制写日记

# ================= RAG 记忆配置 =================
rag:
  retrieval_top_k: 20                  # 检索返回的最大日记条数
  keep_last_dialogue: 10               # 保留的近期对话条数（短期记忆）

# ================= 本地文件路径配置 =================
# 均为相对项目根目录的路径
paths:
  vector_db: "./yuki_memory"
  embed_model: "./models/text2vec-base-chinese"
  history_file: "./data/chat_history.json"
  log_file: "./data/yuki_log.txt"
  cache_dir: "./data"
  cache_file: "./data/meme_cache.json"

# ================= 时间/超时配置 =================
timing:
  debounce_time: 32                    # 防抖时间（秒）
  request_timeout:
    total: 60
    connect: 10
    sock_read: 30

# ================= 精力值系统配置 =================
energy:
  initial: 100
  max: 100.0
  recovery_per_min: 0.8
  cost_per_reply: 6
  min_active: 25                       # 低于此值进入低活跃状态

# ================= 注意力/响应配置 =================
attention:
  sensitivity: 0.12
  decay_level: 0.65
  sigmoid_centre: 50.0
  sigmoid_alpha: 0.08
  # 以下关键词会在运行时被追加 ROBOT_NAME，无需手动修改
  keywords:
    - "主人"
    - "哥哥"

# ================= 并发与调试配置 =================
max_concurrent_meme: 3
debug: true
'''
        with open("configs/config.yaml", "w", encoding="utf-8") as f:
            f.write(default_config)
        print("📄 已生成初始 configs/config.yaml")
    else:
        print("📄 已存在 configs/config.yaml，跳过")

def install_requirements():
    """自动安装依赖（优先使用 uv，回退到 pip）"""
    if input("\n是否现在安装/更新依赖插件? (y/n): ").lower() != 'y':
        return

    has_uv = shutil.which("uv") is not None
    try:
        if has_uv:
            print("🚀 检测到 uv，使用 uv 安装依赖...")
            subprocess.check_call(["uv", "sync"])
            print("✅ 依赖安装完成（via uv）")
        else:
            print("📦 未检测到 uv，使用 pip 安装依赖...")
            subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
            print("✅ 依赖安装完成（via pip）")
    except Exception as e:
        print(f"❌ 依赖安装失败\n错误: {e}")
        print("💡 建议手动执行: uv sync  或  pip install -r requirements.txt")

def migrate_from_env():
    """将 .env 中的配置自动迁移到 configs/config.yaml（仅迁移 yaml 中缺失的值）"""
    env_path = ".env"
    if not os.path.exists(env_path):
        return False

    try:
        import yaml
    except ImportError:
        print("⚠️ PyYAML 未安装，跳过 .env 迁移。建议先安装依赖后再运行 setup.py")
        return False

    # 解析 .env
    env_data = {}
    with open(env_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            env_data[key.strip()] = value.strip().strip('"').strip("'")

    if not env_data:
        return False

    cfg = _load_yaml()
    migrated = []

    # 1. API Keys
    api = cfg.setdefault("api", {})
    key_map = {
        "LLM_API_KEY": "llm_api_key",
        "BACKUP_API_KEY": "backup_api_key",
        "IMAGE_PROCESS_API_KEY": "image_process_api_key",
    }
    for env_key, yaml_key in key_map.items():
        val = env_data.get(env_key)
        if val and not api.get(yaml_key):
            api[yaml_key] = val
            migrated.append(f"api.{yaml_key}")

    # DEEPSEEK_API_KEY 作为 backup_api_key 的兜底迁移
    if not api.get("backup_api_key") and env_data.get("DEEPSEEK_API_KEY"):
        api["backup_api_key"] = env_data["DEEPSEEK_API_KEY"]
        migrated.append("api.backup_api_key (from DEEPSEEK_API_KEY)")

    # 2. 连接配置
    connection = cfg.setdefault("connection", {})
    if env_data.get("NAPCAT_WS_URL") and not connection.get("napcat_ws_url"):
        connection["napcat_ws_url"] = env_data["NAPCAT_WS_URL"]
        migrated.append("connection.napcat_ws_url")

    # 3. 机器人身份（允许覆盖默认值，因为旧版 setup.py 中这些值通常是用户自定义的）
    if env_data.get("ROBOT_NAME"):
        cfg["robot_name"] = env_data["ROBOT_NAME"]
        migrated.append("robot_name")
    if env_data.get("MASTER_NAME"):
        cfg["master_name"] = env_data["MASTER_NAME"]
        migrated.append("master_name")

    # 4. 目标 QQ
    target = cfg.setdefault("target", {})
    if env_data.get("TARGET_QQ") and not target.get("qq"):
        try:
            target["qq"] = int(env_data["TARGET_QQ"])
            migrated.append("target.qq")
        except ValueError:
            pass

    if env_data.get("TARGET_GROUPS") and not target.get("groups"):
        try:
            groups = [int(g.strip()) for g in env_data["TARGET_GROUPS"].split(",") if g.strip()]
            target["groups"] = groups
            migrated.append("target.groups")
        except ValueError:
            pass

    if migrated:
        _save_yaml(cfg)
        print(f"[迁移] 检测到 .env 文件，已自动迁移 {len(migrated)} 项配置到 configs/config.yaml:")
        for item in migrated:
            print(f"   - {item}")
        print("   (.env 文件已保留，可作为备份)")
        return True
    return False

def _load_yaml():
    import yaml
    path = "configs/config.yaml"
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f) or {}
    return {}

def _save_yaml(data):
    import yaml
    path = "configs/config.yaml"
    with open(path, "w", encoding="utf-8") as f:
        yaml.dump(data, f, allow_unicode=True, default_flow_style=False, sort_keys=False)

def config_yaml(mode):
    """交互式配置 configs/config.yaml"""
    try:
        import yaml
    except ImportError:
        print("⚠️ PyYAML 未安装，无法自动修改 configs/config.yaml")
        print("   请先安装依赖，或手动编辑 configs/config.yaml")
        return

    cfg = _load_yaml()
    changed = False

    # 1. API Keys
    print("\n--- 配置 API 密钥 ---")
    api = cfg.setdefault("api", {})
    keys = [
        ("llm_api_key", "请输入首选 LLM API Key: "),
        ("backup_api_key", "请输入备选 LLM API Key（不需要可留空）: "),
        ("image_process_api_key", "请输入图像处理 API Key: "),
    ]
    for key, prompt in keys:
        if mode == 1 or not api.get(key):
            value = input(prompt).strip()
            if value:
                api[key] = value
                changed = True
                print(f"  ✓ api.{key} 已设置")
            elif mode == 1 and key in api:
                del api[key]
                changed = True
        else:
            print(f"  api.{key} 已存在，跳过")

    # 2. 目标 QQ
    print("\n--- 配置目标 QQ ---")
    target = cfg.setdefault("target", {})
    settings = [
        ("qq", "请输入私聊用 QQ 号: ", int),
        ("groups", "请输入目标群聊 QQ 号 (多个用逗号隔开，不需要可留空): ", None),
    ]
    for key, prompt, cast in settings:
        if mode == 1 or not target.get(key):
            value = input(prompt).strip()
            if value:
                if key == "groups":
                    target[key] = [int(g.strip()) for g in value.split(",") if g.strip()]
                else:
                    target[key] = int(value) if cast == int else value
                changed = True
                print(f"  ✓ target.{key} 已设置")
            elif mode == 1 and key in target:
                del target[key]
                changed = True
        else:
            print(f"  target.{key} 已存在，跳过")

    if changed:
        _save_yaml(cfg)
        print("\n📄 配置已保存到 configs/config.yaml")
    else:
        print("\n配置无变化")

def quick_setup(mode):
    print("\n>>> 步骤 1: 建立文件夹结构")
    ensure_dirs()
    ensure_files()
    # 建立黑名单等必要文件
    if not os.path.exists("blacklist.txt"):
        with open("blacklist.txt", "w", encoding="utf-8") as f:
            f.write("")

    print("\n>>> 步骤 2: 安装依赖文件")
    install_requirements()

    print("\n>>> 步骤 3: 迁移旧版 .env 配置(如有)")
    migrate_from_env()

    print("\n>>> 步骤 4: 配置 API 密钥与 QQ 号")
    config_yaml(mode)

    print("\n>>> 步骤 5: 下载 RAG 嵌入模型")
    try:
        from utils.download_model import download_model
        download_model()
    except ImportError as e:
        print(f"⚠️ 依赖未安装，跳过模型下载: {e}")
        print("   请确保已运行 'uv sync' 或 'pip install -r requirements.txt'")
    except Exception as e:
        print(f"模型下载环节出现问题: {e}")


if __name__ == "__main__":
    print("开始配置必要参数和环境")
    try:
        user_input = input("输入配置方式（刷新（跳过已存在）和写入（全部覆盖））[默认 0]: ").strip()
        current_mode = int(user_input) if user_input else 0
    except ValueError:
        current_mode = 0

    quick_setup(current_mode)

    print("向导结束，如需调整参数，请编辑 configs/config.yaml！")
