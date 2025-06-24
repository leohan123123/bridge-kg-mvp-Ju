import os
from pydantic import AnyHttpUrl # AnyHttpUrl 用于验证URL格式
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List, Union
# python-dotenv is usually automatically handled by pydantic-settings if installed
# from dotenv import load_dotenv

# pydantic-settings will automatically load from .env files by default.
# The manual loading below is generally not needed with pydantic-settings.
# However, explicit loading can be kept if specific paths or behaviors are desired
# beyond pydantic-settings' defaults. For now, we can rely on pydantic-settings'
# built-in .env file handling.

# env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '.env')
# if os.path.exists(env_path):
#     load_dotenv(dotenv_path=env_path)
#     print(f"Loaded .env file from: {env_path}")
# else:
#     print(f".env file not found at: {env_path}, using system environment variables.")


class Settings(BaseSettings):
    PROJECT_NAME: str = "Bridge KG MVP Backend"
    API_PREFIX: str = "/api"
    DEBUG: bool = True # 开发模式开关

    # Neo4j 配置
    NEO4J_URI: str = "bolt://localhost:7687" # 默认值，会被 .env 或环境变量覆盖
    NEO4J_USER: str = "neo4j"
    NEO4J_PASSWORD: str = "password" # 默认密码，强烈建议修改
    NEO4J_DATABASE: str = "neo4j" # 默认数据库名

    # CORS 配置
    # ALLOWED_ORIGINS 可以是一个逗号分隔的字符串，例如 "http://localhost:5173,http://127.0.0.1:5173"
    # 或者在 .env 文件中定义为 ALLOWED_ORIGINS='["http://localhost:5173", "http://127.0.0.1:5173"]' (JSON string)
    # Pydantic 会尝试解析它
    ALLOWED_ORIGINS: Union[str, List[AnyHttpUrl]] = [] # 默认为空列表，表示不特别限制或由CORSMiddleware处理

    # 日志级别
    LOG_LEVEL: str = "INFO"

    # DeepSeek AI服务配置
    DEEPSEEK_API_KEY: str = "" # DeepSeek API密钥
    DEEPSEEK_DEFAULT_MODEL: str = "deepseek-chat" # 默认使用的DeepSeek模型

    # Ollama Configuration
    OLLAMA_API_URL: AnyHttpUrl = "http://localhost:11434/api/chat" # Default Ollama API URL
    OLLAMA_DEFAULT_MODEL: str = "qwen2:0.5b" # Default model to use if not specified in request

    # Pydantic-Settings configuration
    model_config = SettingsConfigDict(
        case_sensitive=True,
        env_file=".env", # Specifies the .env file name for pydantic-settings to load
        env_file_encoding='utf-8',
        extra='ignore' # Ignores extra fields from .env rather than raising an error
    )

    # The commented-out Pydantic V2 configuration for parse_env_var is generally
    # not needed for simple cases as Pydantic V2 and pydantic-settings have improved
    # parsing for list types from environment variables.
    # If complex parsing is needed, @field_validator can be used.


settings = Settings()

# 打印加载的配置 (用于调试，生产环境可以移除)
if settings.DEBUG:
    print("Loaded application settings:")
    # Use model_dump() in Pydantic V2
    for key, value in settings.model_dump().items():
        # 避免打印敏感信息如密码
        if "password" in key.lower() or "secret" in key.lower() or "api_key" in key.lower():
            print(f"  {key}: ******")
        else:
            print(f"  {key}: {value}")