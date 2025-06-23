import os
from pydantic import BaseSettings, AnyHttpUrl # AnyHttpUrl 用于验证URL格式
from typing import List, Union
from dotenv import load_dotenv

# 加载 .env 文件中的环境变量 (如果存在)
# 这使得我们可以在开发环境中使用 .env 文件，而在生产环境中通过系统环境变量配置
env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '.env')
if os.path.exists(env_path):
    load_dotenv(dotenv_path=env_path)
    print(f"Loaded .env file from: {env_path}")
else:
    print(f".env file not found at: {env_path}, using system environment variables.")


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

    # Ollama Configuration
    OLLAMA_API_URL: AnyHttpUrl = "http://localhost:11434/api/chat" # Default Ollama API URL
    OLLAMA_DEFAULT_MODEL: str = "qwen2:0.5b" # Default model to use if not specified in request

    class Config:
        case_sensitive = True # 环境变量名大小写敏感
        env_file = ".env" # 指定 .env 文件名 (虽然我们已经手动加载了)
        env_file_encoding = 'utf-8'

        # Pydantic V2 的配置方式
        # @classmethod
        # def parse_env_var(cls, field_name: str, raw_val: str) -> Any:
        #     if field_name == 'ALLOWED_ORIGINS':
        #         if raw_val.startswith('[') and raw_val.endswith(']'):
        #             try:
        #                 return json.loads(raw_val)
        #             except json.JSONDecodeError:
        #                 pass # Fallback to comma-separated string
        #         return [origin.strip() for origin in raw_val.split(',') if origin.strip()]
        #     return cls.json_loads(raw_val) if isinstance(raw_val, str) else raw_val


settings = Settings()

# 打印加载的配置 (用于调试，生产环境可以移除)
if settings.DEBUG:
    print("Loaded application settings:")
    for key, value in settings.dict().items():
        # 避免打印敏感信息如密码
        if "password" in key.lower() or "secret" in key.lower():
            print(f"  {key}: ******")
        else:
            print(f"  {key}: {value}")
