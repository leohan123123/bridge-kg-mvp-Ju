#!/bin/bash
# 开发环境快速启动脚本

# 检查 Docker 是否正在运行
if ! docker info > /dev/null 2>&1; then
  echo "错误：Docker Desktop 未运行或 Docker守护进程未启动。"
  echo "请先启动 Docker 再运行此脚本。"
  exit 1
fi

# 检查 Docker Compose 是否可用
if ! command -v docker-compose &> /dev/null; then
    # 如果 docker-compose 命令不存在, 尝试 docker compose (v2)
    if ! docker compose version &> /dev/null; then
        echo "错误：未找到 docker-compose 或 docker compose 命令。"
        echo "请确保已安装 Docker Compose。"
        exit 1
    else
        # 使用 docker compose (v2)
        COMPOSE_CMD="docker compose"
    fi
else
    # 使用 docker-compose (v1)
    COMPOSE_CMD="docker-compose"
fi

echo "正在使用 '$COMPOSE_CMD'..."

# 步骤1: 复制 .env.example 为 .env (如果 .env 文件不存在)
if [ ! -f .env ]; then
  echo "未找到 .env 文件，正在从 .env.example 创建..."
  cp .env.example .env
  echo ".env 文件已创建。请根据需要修改其中的配置，特别是 NEO4J_PASSWORD。"
  echo "按任意键继续启动，或按 Ctrl+C 中断并编辑 .env 文件..."
  read -n 1 -s
fi

# 步骤2: 前端依赖安装 (在宿主机执行，以便 Dockerfile.dev 可以利用缓存或直接映射)
# 这一步是可选的，如果 Dockerfile.dev 内部会执行 npm install，则不需要。
# 但如果希望 node_modules 在宿主机可见并由开发者管理，则需要。
# 当前 frontend/Dockerfile.dev 可能会自己处理 npm install。
# 为了确保 "一键启动"，我们假设开发者可能首次没有运行 npm install。
echo "正在 frontend 目录运行 npm install (如果需要)..."
if [ -d "frontend" ] && [ -f "frontend/package.json" ]; then
  (cd frontend && npm install)
else
  echo "警告: 未找到 frontend/package.json，跳过 npm install。"
fi

# 步骤3: 启动 Docker Compose 服务
echo "正在启动 Docker Compose 服务 (包括构建镜像)..."
$COMPOSE_CMD up --build -d # -d 表示后台运行

echo ""
echo "开发环境已启动！"
echo "-----------------------------------------------------"
echo "您可以访问以下地址:"
echo "  - 前端应用: http://localhost:3000"
echo "  - 后端API (根路径): http://localhost:8000"
echo "  - 后端API文档 (Swagger): http://localhost:8000/docs"
echo "  - Neo4j Browser: http://localhost:7474 (使用 .env 中的凭据登录)"
echo "-----------------------------------------------------"
echo "要停止服务，请运行: $COMPOSE_CMD down"
echo "要查看日志，请运行: $COMPOSE_CMD logs -f"
echo "-----------------------------------------------------"

# 附加：如果需要，可以启动前端开发服务器的日志输出
# echo "按 'f' 查看前端容器日志，按其他任意键退出脚本..."
# read -n 1 key
# if [[ $key == "f" ]]; then
#    $COMPOSE_CMD logs -f frontend
# fi
#
# echo "按 'b' 查看后端容器日志，按其他任意键退出脚本..."
# read -n 1 key
# if [[ $key == "b" ]]; then
#    $COMPOSE_CMD logs -f backend
# fi
