# ws_connection.py
import json
import asyncio
import websockets
from typing import Optional, Dict
from config import NAPCAT_WS_URL


class BotConnector:
    def __init__(self, ws_url: str = NAPCAT_WS_URL):
        self.ws_url = ws_url
        self.websocket = None
        self._lock = asyncio.Lock()

    async def ensure_connection(self):
        """最兼容的版本判断：确保返回一个真正 OPEN 的连接"""
        async with self._lock:
            # 使用 hasattr 进行安全检查，或者直接判断对象是否存在
            # 核心逻辑：如果对象不存在，或者对象的状态不是 OPEN (1)
            is_alive = False
            if self.websocket is not None:
                try:
                    # websockets 库最通用的检查方式是查看其 protocol 状态机
                    # 或者直接检查 connection 状态
                    from websockets.protocol import State
                    is_alive = self.websocket.state == State.OPEN
                except Exception:
                    # 如果找不到 State 枚举，回退到最原始的尝试
                    try:
                        is_alive = not self.websocket.closed
                    except AttributeError:
                        try:
                            is_alive = self.websocket.open
                        except AttributeError:
                            is_alive = False  # 属性全无，视为失效

            if not is_alive:
                if self.websocket is not None:
                    print("[Network] 检测到连接状态异常，正在重建...")

                self.websocket = await websockets.connect(
                    self.ws_url,
                    ping_interval=20,
                    ping_timeout=60,
                    close_timeout=10
                )
                print(f"[Network] 全局连接已建立: {self.ws_url}")

            return self.websocket

    async def listen(self):
        """闭环监听：自动重连"""
        while True:
            try:
                # 始终获取当前最新的可用连接
                ws = await self.ensure_connection()
                async for message in ws:
                    yield json.loads(message)
            except Exception as e:
                # 发生任何网络异常，标记连接失效，等待下一次循环重连
                print(f"[Network] 监听异常: {e}")
                self.websocket = None
                await asyncio.sleep(3)

    async def close(self):
        """优雅关闭"""
        async with self._lock:
            if self.websocket:
                await self.websocket.close()
                self.websocket = None
    async def send_request(self, action: str, params: dict, echo: str) -> Optional[Dict]:
        try:
            ws = await self.ensure_connection()
            request = {"action": action, "params": params, "echo": echo}
            await ws.send(json.dumps(request))
            try:
                while True:
                    response = await asyncio.wait_for(ws.recv(), timeout=5.0)
                    data = json.loads(response)
                    if data.get("echo") == echo:
                        return data
            except asyncio.TimeoutError:
                print(f"请求 {action} 超时")

        except Exception as e:
            print(f"网络异常: {e}")
            await self.close()
        return None

