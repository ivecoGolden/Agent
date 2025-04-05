from fastapi import FastAPI
from fastapi.responses import StreamingResponse, HTMLResponse
from app.agent.MCPAgent import MCPAgent

app = FastAPI()


@app.get("/")
def read_root() -> dict:
    """
    根路径 GET 接口

    功能：
    - 返回简单的欢迎消息，通常用于服务可用性检测。

    返回值：
    - dict: 包含 "message" 字段的欢迎消息
    """
    return {"message": "Hello World"}


@app.get("/mcp-agent/stream")
async def run_mcp_agent_stream(q: str):
    """
    逐步执行 MCPAgent 推理过程，返回 StreamingResponse。
    """
    agent = MCPAgent()

    async def event_stream():
        async for step in agent.run(q):
            yield step + "\n"

    return StreamingResponse(event_stream(), media_type="text/plain")


@app.get("/mcp-agent/ui", response_class=HTMLResponse)
def mcp_agent_ui():
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <title>MCP Agent 流式演示</title>
    </head>
    <body>
        <h1>MCP Agent 推理演示</h1>
        <input type="text" id="query" placeholder="请输入你的请求" size="40"/>
        <button onclick="runAgent()">运行</button>
        <pre id="output" style="background:#f0f0f0;padding:10px;"></pre>

        <script>
        async function runAgent() {
            const query = document.getElementById("query").value;
            const output = document.getElementById("output");
            output.textContent = "正在加载...\\n";
            const response = await fetch(`/mcp-agent/stream?q=${encodeURIComponent(query)}`);
            const reader = response.body.getReader();
            const decoder = new TextDecoder("utf-8");
            let result = "";
            while (true) {
                const { done, value } = await reader.read();
                if (done) break;
                result += decoder.decode(value, { stream: true });
                output.textContent = result;
            }
        }
        </script>
    </body>
    </html>
    """


# ============================
# 安全风险评估与规范性报告
# ============================
# ✅ 当前功能说明：
# - 定义 FastAPI 应用实例，并注册根路径 `/` 的 GET 接口，返回欢迎消息。
#
# 🔐 安全风险分析：
# - ⚠️ 无任何安全控制：接口对所有请求开放，建议后续添加身份校验或访问控制机制。
# - ✅ 当前仅用于开发或健康检查场景下风险较小。
#
# 📐 编码规范审查：
# - 命名规范：✅ 合规
# - 类型注解：✅ `read_root` 已添加返回值类型注解
# - 注释完整性：✅ 已添加函数 docstring
#
# 🏗 架构设计与可维护性建议：
# - 当前结构简单明了，适合项目初始化；
# - 后续可将路由注册、配置加载、异常处理等逻辑拆分至子模块，提高可维护性；
# - 建议接入日志系统与配置化启动逻辑（如加载 `.env` 设置）。
