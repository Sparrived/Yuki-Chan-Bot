# config.py
import os
import aiohttp
import yaml

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# ================= 加载持久化配置 =================
_yaml_config = {}
_yaml_path = os.path.join(BASE_DIR, "configs", "config.yaml")
if os.path.exists(_yaml_path):
    with open(_yaml_path, "r", encoding="utf-8") as f:
        _yaml_config = yaml.safe_load(f) or {}


def _cfg(key, default=None, cast=None):
    """从 YAML 顶层读取配置，支持类型转换"""
    val = _yaml_config.get(key, default)
    if val is None:
        val = default
    if cast and val is not None:
        val = cast(val)
    return val


def _nested(*keys, default=None, cast=None):
    """从 YAML 嵌套结构中读取配置"""
    d = _yaml_config
    for k in keys:
        if isinstance(d, dict) and k in d:
            d = d[k]
        else:
            return default
    if d is None:
        return default
    if cast and d is not None:
        d = cast(d)
    return d


def _resolve_path(p):
    """将相对路径解析为基于 BASE_DIR 的绝对路径"""
    if p and isinstance(p, str) and p.startswith("./"):
        return os.path.join(BASE_DIR, p[2:])
    return p


# ================= 机器人身份 =================
ROBOT_NAME = _cfg("robot_name", default="yuki").lower()
MASTER_NAME = _cfg("master_name", default="主人")   # 默认叫主人，也可以改

# ================= 安全配置 =================
MAX_MESSAGE_LENGTH = _cfg("max_message_length", default=150)    # 最大消息长度，防止token炸弹

# ================= 日记触发配置 =================
DIARY_IDLE_SECONDS = _nested("diary", "idle_seconds", default=120)     # 空闲触发时间（秒），2分钟
DIARY_MIN_TURNS = _nested("diary", "min_turns", default=15)      # 最小对话轮数（非系统消息条数）
DIARY_MAX_LENGTH = _nested("diary", "max_length", default=50)     # 保底历史长度阈值（超过则强制写日记）

# ================= RAG 记忆配置 =================
RETRIEVAL_TOP_K = _nested("rag", "retrieval_top_k", default=20)      # 每次检索返回日记条数
KEEP_LAST_DIALOGUE = _nested("rag", "keep_last_dialogue", default=10)     # 保留最近对话条数（短期记忆）

# ================= API 配置 =================
LLM_BASE_URL = _nested("api", "llm_base_url", default="https://api.deepseek.com/v1")
DEEPSEEK_BASE_URL = _nested("api", "deepseek_base_url", default="https://api.deepseek.com/v1")
IMAGE_PROCESS_API_URL = _nested(
    "api", "image_process_url",
    default="https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions"
)
LLM_API_KEY = _nested("api", "llm_api_key", default="")
BACKUP_API_KEY = _nested("api", "backup_api_key", default="") or LLM_API_KEY
IMAGE_PROCESS_API_KEY = _nested("api", "image_process_api_key", default="")

# ================= 模型配置 =================
# 主对话模型 (例如: deepseek-chat, gpt-4o)
LLM_MODEL = _nested("model", "llm", default="deepseek-chat")
BACKUP_MODEL = _nested("model", "backup", default="deepseek-chat")

# 图像分析模型 (如果有专门的视觉模型需求)
# 注意！！如果没有多模态模型，想关闭视觉识别，就将字段留空。如下面所示：
# VISION_MODEL = ""
VISION_MODEL = _nested("model", "vision", default="qwen3-vl-flash")

# ================= 连接配置 =================
NAPCAT_WS_URL = _nested("connection", "napcat_ws_url", default="ws://127.0.0.1:3001")
MAX_RETRIES = _nested("connection", "max_retries", default=3)

# ================= 目标配置 =================
TARGET_QQ = _nested("target", "qq", default=0, cast=int)

# --- 数组（列表）转换 ---
_target_groups = _nested("target", "groups", default=[])
if isinstance(_target_groups, str):
    # 逻辑：分割字符串 -> 去除空格 -> 转换为 int -> 转为 list
    TARGET_GROUPS = [int(g.strip()) for g in _target_groups.split(",") if g.strip()]
else:
    # 如果 yaml 里没写，给一个默认列表
    TARGET_GROUPS = [int(g) for g in _target_groups]

# ================= 文件配置 =================
_paths = _yaml_config.get("paths", {})
VECTOR_DB_PATH = _resolve_path(_paths.get("vector_db", "./yuki_memory")) or os.path.join(BASE_DIR, "yuki_memory")
EMBED_MODEL = _resolve_path(_paths.get("embed_model", "./models/text2vec-base-chinese")) or os.path.join(BASE_DIR, "models", "text2vec-base-chinese")
HISTORY_FILE = _resolve_path(_paths.get("history_file", "./data/chat_history.json")) or os.path.join(BASE_DIR, "data", "chat_history.json")
LOG_FILE = _resolve_path(_paths.get("log_file", "./data/yuki_log.txt")) or os.path.join(BASE_DIR, "data", "yuki_log.txt")
CACHE_DIR = _resolve_path(_paths.get("cache_dir", "./data")) or os.path.join(BASE_DIR, "data")
CACHE_FILE = _resolve_path(_paths.get("cache_file", "./data/meme_cache.json")) or os.path.join(CACHE_DIR, "meme_cache.json")

# ================= 时间配置 =================
DEBOUNCE_TIME = _nested("timing", "debounce_time", default=32)
_timeout_cfg = _yaml_config.get("timing", {}).get("request_timeout", {})
REQUEST_TIMEOUT = aiohttp.ClientTimeout(
    total=_timeout_cfg.get("total", 60),
    connect=_timeout_cfg.get("connect", 10),
    sock_read=_timeout_cfg.get("sock_read", 30)
)

# ================= 精力值配置 =================
INITIAL_ENERGY = _nested("energy", "initial", default=100)
MAX_ENERGY = _nested("energy", "max", default=100.0)
RECOVERY_PER_MIN = _nested("energy", "recovery_per_min", default=0.8)
COST_PER_REPLY = _nested("energy", "cost_per_reply", default=6)
MIN_ACTIVE_ENERGY = _nested("energy", "min_active", default=25)

SENSITIVITY = _nested("attention", "sensitivity", default=0.12)
DECAY_LEVEL = _nested("attention", "decay_level", default=0.65)
SIGMOID_CENTRE = _nested("attention", "sigmoid_centre", default=50.0)
SIGMOID_ALPHA = _nested("attention", "sigmoid_alpha", default=0.08)

_base_keywords = _yaml_config.get("attention", {}).get("keywords", ["主人", "哥哥"])
keywords = list(_base_keywords)
if ROBOT_NAME and ROBOT_NAME not in keywords:
    keywords.append(ROBOT_NAME)

# ================= 并发配置 =================
MAX_CONCURRENT_MEME = _cfg("max_concurrent_meme", default=3)

# ================= 调试配置 =================
DEBUG = _cfg("debug", default=True)
