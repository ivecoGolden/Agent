from typing import Dict
from fastapi import WebSocket


class ConnectionManager:
    """
    WebSocket 连接管理器，用于维护客户端连接信息，
    支持用户私聊和全体广播功能。
    """

    def __init__(self):
        """
        初始化连接管理器，创建存储客户端连接的字典。
        """
        self.active_connections: Dict[str, WebSocket] = {}

    async def connect(self, websocket: WebSocket, client_id: str):
        """
        接受客户端连接并存储 WebSocket 实例。

        参数：
        - websocket: WebSocket 客户端连接对象
        - client_id: str 客户端唯一标识符
        """
        await websocket.accept()
        self.active_connections[client_id] = websocket

    def disconnect(self, client_id: str):
        """
        移除指定客户端的连接。

        参数：
        - client_id: str 客户端唯一标识符
        """
        if client_id in self.active_connections:
            del self.active_connections[client_id]

    async def send_personal_message(self, message: str, client_id: str):
        """
        向指定客户端发送私有消息。

        参数：
        - message: str 要发送的消息内容
        - client_id: str 目标客户端标识符
        """
        if client_id in self.active_connections:
            await self.active_connections[client_id].send_text(message)

    async def broadcast(self, message: str):
        """
        向所有已连接客户端广播消息。

        参数：
        - message: str 要广播的消息内容
        """
        for connection in self.active_connections.values():
            await connection.send_text(message)


# ============================
# 安全风险评估与规范性报告
# ============================
# ✅ 当前功能说明：
# - `ConnectionManager` 管理 WebSocket 客户端连接，支持私聊与广播功能。
#
# 🔐 安全风险分析：
# - ❗ `client_id` 可被伪造：若 client_id 来自用户输入，恶意客户端可冒充他人。
#   建议：结合身份验证机制（如 JWT）确保 client_id 的真实性。
# - ❗ 未处理 send_text 异常：当连接已断开时发送消息将抛出异常，建议添加 try-except。
# - ⚠️ 内存泄漏风险：连接未主动断开或 client_id 重复可能导致连接未释放。
#
# 📐 编码规范审查：
# - 命名规范：✅ 合规
# - 类型注解：✅ 正确使用了类型注解
# - 注释完整性：✅ 已为类和方法添加用途说明 docstring
#
# 🏗 架构设计与可维护性建议：
# - 构造清晰，适合支持单房间通信模型；
# - 后续可扩展为支持多房间、连接生命周期事件钩子（如 on_connect/on_disconnect）；
# - 建议增加连接状态日志、消息发送失败重试机制、心跳保活等增强功能。
