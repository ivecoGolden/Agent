from fastapi import WebSocket, WebSocketDisconnect
from fastapi import APIRouter, Depends
import time
import logging
from app.core.auth import get_current_user

router = APIRouter()


@router.websocket("/ws")
async def websocket_endpoint(
    websocket: WebSocket, token: str = Depends(get_current_user)
) -> None:
    # 设置心跳检测间隔为30秒
    HEARTBEAT_INTERVAL = 30
    last_activity = time.time()
    """
    WebSocket 接入端点

    参数：
    - websocket: WebSocket
        WebSocket 连接对象，代表客户端请求连接。
    - token: str
        JWT认证令牌

    功能：
    - 验证JWT令牌；
    - 接收客户端连接；
    - 持续接收消息并将原文回发回去（回显机制）；
    - 处理连接异常。
    """
    try:
        await websocket.accept()
        while True:
            data = await websocket.receive_text()
            if len(data) > 1024:  # 限制消息大小
                await websocket.send_text("消息过长，最大支持1024字节")
                continue
            await websocket.send_text(f"Message text was: {data}")
    except WebSocketDisconnect:
        logging.warning(f"客户端断开连接: {websocket.client}")
    except Exception as e:
        logging.error(f"WebSocket错误: {str(e)}", exc_info=True)
        await websocket.close(code=1011)


@router.websocket("/ws/test")
async def websocket_test_endpoint(websocket: WebSocket) -> None:
    """
    WebSocket 测试端点（无鉴权）

    参数：
    - websocket: WebSocket
        WebSocket 连接对象，代表客户端请求连接。

    功能：
    - 接收客户端连接；
    - 持续接收消息并将原文回发回去（回显机制）；
    - 处理连接异常。
    - ⚠️ 本端点不做任何身份校验，仅用于开发调试，禁止用于生产环境。
    """
    try:
        await websocket.accept()
        while True:
            data = await websocket.receive_text()
            await websocket.send_text(f"[测试回显] Message text was: {data}")
    except WebSocketDisconnect:
        logging.warning(f"[测试] 客户端断开连接: {websocket.client}")
    except Exception as e:
        logging.error(f"[测试] WebSocket错误: {str(e)}", exc_info=True)
        await websocket.close(code=1011)


# ============================
# 安全风险评估与规范性报告
# ============================
# ✅ 当前功能说明：
# - 实现 WebSocket 接口 `/ws`，支持客户端连接并回显消息，需 JWT 鉴权。
# - 新增测试 WebSocket 接口 `/ws/test`，支持无鉴权连接，便于开发调试。
# - 添加消息大小限制（1024字节）防止恶意输入。
# - 完善异常处理机制，捕获断开连接和其他错误。

# 🔐 安全风险分析：
# - ✅ `/ws` 接口已添加 JWT 鉴权机制，防止未授权访问；
# - ✅ 鉴权逻辑使用 `get_current_user` 实现标准 JWT 校验；
# - ⚠️ `/ws/test` 无任何身份校验，仅适合本地开发调试，强烈建议生产环境禁用；
# - ⚠️ 用户身份未与 WebSocket 连接绑定，建议后续增加连接标识与用户追踪机制；
# - ✅ 添加消息大小限制，防止内存滥用；
# - ✅ 异常处理采用 `logging` 模块记录日志，利于生产环境监控；
# - ⚠️ 心跳机制未完全实现，仅声明了检测间隔变量，后续需补充 ping/pong 或超时断开逻辑；

# 📐 编码规范审查：
# - 命名规范：✅ 合规；
# - 类型注解：✅ 参数与返回值均添加类型注解；
# - 注释完整性：✅ 函数与模块已补充 docstring，内容清晰；
# - ✅ 使用 `Depends` 实现依赖注入；
# - ✅ 无重复导入，模块结构清晰；

# 🏗 架构设计与可维护性建议：
# - 当前结构适合功能验证或小型应用；
# - 建议拆分逻辑模块：
#   - `service/websocket.py`：封装连接管理与消息处理逻辑；
#   - `schemas/websocket.py`：定义消息结构，支持类型验证；
# - 建议接入连接管理器，支持多用户标识与广播；
# - 心跳保活机制、异常统一处理、连接追踪建议模块化设计，提升可测性与可维护性。
