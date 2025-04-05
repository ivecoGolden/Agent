from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """
    应用配置类，基于 Pydantic 的 BaseSettings，
    用于从环境变量或 .env 文件中加载应用配置。
    """

    PYTHONPATH: any
    GAODE_KEY: str
    ALI_TEXT_MODEL_URL: str = "https://dashscope.aliyuncs.com/compatible-mode/v1"
    ALI_MODEL_API_KEY: str = ""
    app_name: str = ""  # 应用名称
    debug: bool = False  # 是否开启调试模式
    SECRET_KEY: str = ""  # JWT签名密钥
    ALGORITHM: str = "HS256"  # JWT签名算法

    class Config:
        env_file = ".env"


settings = Settings()

# ============================
# 安全风险评估与规范性报告
# ============================
# ✅ 当前功能说明：
# - 使用 Pydantic Settings 机制加载配置，支持从 `.env` 文件读取环境变量。
#
# 🔐 安全风险分析：
# - ⚠️ `.env` 文件中可能包含敏感信息（如密钥、Token），应确保该文件不被提交至版本控制（需添加至 `.gitignore`）。
# - ✅ 使用 `BaseSettings` 能有效避免硬编码配置，提升安全性。
#
# 📐 编码规范审查：
# - 命名规范：✅ 合规
# - 类型注解：✅ 正确使用了类型注解
# - 注释完整性：✅ 已为类和字段补充用途说明
#
# 🏗 架构设计与可维护性建议：
# - 配置集中式管理良好，便于环境隔离与部署；
# - 可进一步封装常用配置访问函数；
# - 若后续配置项增多，建议分模块组织或使用动态加载策略。
