#!/bin/bash
echo "🚀 Bridge KG MVP - 快速启动"
echo "检查环境..."

# 检查Docker
if ! command -v docker &> /dev/null; then
    echo "❌ Docker未安装"
    exit 1
fi

# 检查Node.js
if ! command -v node &> /dev/null; then
    echo "❌ Node.js未安装"
    exit 1
fi

echo "✅ 环境检查通过"
echo "🔧 启动服务..."

# 复制环境变量
if [ ! -f .env ]; then
    cp .env.example .env
    echo "✅ 已创建.env文件"
fi

# 启动服务
docker-compose up -d
echo "🎉 服务启动完成"
echo "📊 前端：http://localhost:3000"
echo "🔧 后端：http://localhost:8000"
echo "🗄️ Neo4j：http://localhost:7474"
