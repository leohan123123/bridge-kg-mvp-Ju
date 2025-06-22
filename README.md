# 全栈知识图谱应用开发环境

本项目是一个全栈应用，包含基于 Vite + React + TypeScript 的前端，以及基于 FastAPI + Python 的后端，并使用 Neo4j 图数据库。本文档将指导您如何配置和启动本地开发环境。

## 目录

- [项目结构](#项目结构)
- [先决条件](#先决条件)
- [安装与配置](#安装与配置)
- [一键启动开发环境](#一键启动开发环境)
- [访问应用](#访问应用)
- [开发指南](#开发指南)
  - [前端](#前端)
  - [后端](#后端)
  - [数据库](#数据库)
- [常用命令](#常用命令)
- [故障排除](#故障排除)

## 项目结构

```
.
├── backend/            # 后端 FastAPI 应用
│   ├── app/            # 应用代码
│   ├── Dockerfile      # 后端 Dockerfile
│   ├── requirements.txt# Python 依赖
│   └── .env.example    # 后端环境变量示例 (现已移至根目录)
├── frontend/           # 前端 Vite + React 应用
│   ├── public/
│   ├── src/
│   ├── Dockerfile      # 生产环境 Dockerfile
│   ├── Dockerfile.dev  # 开发环境 Dockerfile
│   ├── package.json    # Node.js 依赖
│   └── vite.config.ts  # Vite 配置文件
├── docker-compose.yml  # Docker Compose 配置文件
├── .env.example        # 项目环境变量示例 (请复制为 .env)
├── start-dev.sh        # 开发环境快速启动脚本
└── README.md           # 本文档
```

## 先决条件

在开始之前，请确保您的系统已安装以下软件：

1.  **Docker**: [获取 Docker](https://www.docker.com/get-started)
    -   确保 Docker 守护进程正在运行。
2.  **Docker Compose**:
    -   Docker Desktop for Windows/Mac 通常已包含 Docker Compose。
    -   对于 Linux 用户，请参考 [Docker Compose 安装指南](https://docs.docker.com/compose/install/)。
    -   脚本 `start-dev.sh` 会尝试使用 `docker compose` (V2) 或 `docker-compose` (V1)。
3.  **Node.js 和 npm**: [获取 Node.js](https://nodejs.org/) (建议使用 LTS 版本)
    -   主要用于前端依赖管理和运行一些脚本。`start-dev.sh` 会尝试在前端目录运行 `npm install`。
4.  **Git**: [获取 Git](https://git-scm.com/)
    -   用于克隆本项目仓库。
5.  **代码编辑器**: 例如 [Visual Studio Code](https://code.visualstudio.com/)

## 安装与配置

1.  **克隆仓库**:
    ```bash
    git clone <仓库URL>
    cd <项目目录名>
    ```

2.  **配置环境变量**:
    -   项目使用 `.env` 文件管理环境变量。该文件由 Docker Compose 加载并传递给后端服务。
    -   复制根目录下的 `.env.example` 文件并重命名为 `.env`:
        ```bash
        cp .env.example .env
        ```
    -   **重要**: 打开 `.env` 文件，检查并根据需要修改配置，特别是 `NEO4J_PASSWORD`。确保此密码与您期望用于 Neo4j 数据库的密码一致。`start-dev.sh` 脚本在首次运行时会自动执行此复制操作（如果`.env`不存在）。

3.  **前端依赖 (可选手动步骤)**:
    -   `start-dev.sh` 脚本会自动在 `frontend` 目录下运行 `npm install`。
    -   如果您想手动安装或更新前端依赖：
        ```bash
        cd frontend
        npm install
        cd ..
        ```

## 一键启动开发环境

我们提供了一个快速启动脚本 `start-dev.sh` 来简化开发环境的搭建。

1.  **确保脚本可执行** (如果通过 Git 克隆，权限通常已保留；如果手动创建，则需要此步骤):
    ```bash
    chmod +x start-dev.sh
    ```

2.  **运行启动脚本**:
    ```bash
    ./start-dev.sh
    ```
    此脚本将执行以下操作：
    *   检查 Docker 和 Docker Compose 是否可用。
    *   如果 `.env` 文件不存在，则从 `.env.example` 创建。
    *   在 `frontend` 目录运行 `npm install`。
    *   使用 `docker-compose up --build -d` 构建并启动所有服务 (前端, 后端, Neo4j数据库)。

    首次启动时，Docker 镜像的构建可能需要一些时间。

## 访问应用

启动成功后，您可以访问以下服务：

*   **前端应用**: [http://localhost:3000](http://localhost:3000)
    *   Vite 开发服务器，支持热模块替换 (HMR)。
*   **后端 API (根路径)**: [http://localhost:8000](http://localhost:8000)
*   **后端 API 文档 (Swagger UI)**: [http://localhost:8000/docs](http://localhost:8000/docs)
*   **Neo4j Browser**: [http://localhost:7474](http://localhost:7474)
    *   用户名: 您在 `.env` 文件中配置的 `NEO4J_USER` (默认为 `neo4j`)。
    *   密码: 您在 `.env` 文件中配置的 `NEO4J_PASSWORD` (默认为 `s3cr3t`，**强烈建议修改**)。
    *   连接 URL: Bolt URL 通常是 `bolt://localhost:7687` (当从浏览器访问 Neo4j Browser 时，它会通过 Docker 映射的端口连接到 Neo4j 实例)。

## 开发指南

### 前端

*   **目录**: `frontend/`
*   **技术栈**: Vite, React, TypeScript, Ant Design
*   **开发服务器**: 运行在 `http://localhost:3000`。
*   **代码更改**: 由于配置了卷挂载 (`./frontend:/app`) 和 Vite 的 HMR，您在 `frontend/src` 目录下的代码更改会实时反映在浏览器中，无需手动刷新。
*   **API 请求**: 前端通过相对路径 `/api/...` 向后端发起请求。Vite 开发服务器已配置代理，会将 `/api` 请求转发到 `http://backend:8000` (即后端 Docker 服务)。
*   **依赖管理**: 使用 `npm` 或 `yarn` 在 `frontend/` 目录下管理依赖。
    ```bash
    # 进入前端目录
    cd frontend
    # 安装新依赖
    npm install <package-name>
    # 或
    yarn add <package-name>
    cd ..
    ```

### 后端

*   **目录**: `backend/`
*   **技术栈**: FastAPI, Python, Uvicorn
*   **开发服务器**: 运行在 `http://localhost:8000`。
*   **代码更改**: 由于配置了卷挂载 (`./backend:/app`) 和 Uvicorn 的 `--reload` 选项，您在 `backend/app` 目录下的代码更改会自动重载后端服务。
*   **环境变量**: 后端配置通过根目录的 `.env` 文件加载。
*   **依赖管理**: Python 依赖在 `backend/requirements.txt` 中定义。如果添加了新的依赖：
    1.  将其添加到 `requirements.txt`。
    2.  您可能需要重新构建后端镜像或在容器内手动安装。最简单的方式是停止并重新运行 `./start-dev.sh` (它会执行 `docker-compose up --build`)。
        或者，您可以运行 `docker-compose build backend` 然后 `docker-compose up -d backend`。

### 数据库

*   **服务**: Neo4j 图数据库
*   **访问**: 通过 Neo4j Browser ([http://localhost:7474](http://localhost:7474)) 或使用 Bolt 驱动程序从后端应用访问 (`bolt://neo4j:7687`)。
*   **数据持久化**: Neo4j 数据存储在 Docker 卷 (`neo4j_data`) 中，这意味着即使容器停止和重启，数据也会保留。要完全清除数据，您需要移除该卷 (例如，使用 `docker volume rm <project_name>_neo4j_data`)。
*   **配置**: Neo4j 用户名和密码在 `.env` 文件中配置 (`NEO4J_USER`, `NEO4J_PASSWORD`)。

## 常用命令

*   **启动所有服务 (后台运行)**:
    ```bash
    ./start-dev.sh
    # 或手动
    # docker-compose up --build -d
    ```
*   **停止所有服务**:
    ```bash
    docker-compose down
    ```
*   **停止并移除卷 (例如，清除Neo4j数据)**:
    ```bash
    docker-compose down -v
    ```
*   **查看所有服务日志**:
    ```bash
    docker-compose logs -f
    ```
*   **查看特定服务日志 (例如前端)**:
    ```bash
    docker-compose logs -f frontend
    # 或后端
    # docker-compose logs -f backend
    ```
*   **重新构建所有镜像**:
    ```bash
    docker-compose build
    ```
*   **重新构建特定服务镜像 (例如后端)**:
    ```bash
    docker-compose build backend
    ```
*   **进入正在运行的容器 (例如后端)**:
    ```bash
    docker-compose exec backend bash
    ```

## 故障排除

*   **端口冲突**:
    *   如果错误消息指示端口 (如 3000, 8000, 7474, 7687) 已被占用，请检查是否有其他应用程序正在使用这些端口。
    *   您可以修改 `docker-compose.yml` (端口映射的左侧) 和相关配置文件 (如 `frontend/vite.config.ts` 的 `server.port`) 来使用不同的端口。
*   **Docker 未运行**:
    *   确保 Docker Desktop 或 Docker 守护进程已启动。`start-dev.sh` 脚本会进行基本检查。
*   **`.env` 文件问题**:
    *   确保 `.env` 文件存在于项目根目录，并且是从 `.env.example` 正确复制和配置的。
    *   特别是检查 `NEO4J_PASSWORD` 是否已按需设置。
*   **前端 `npm install` 失败**:
    *   确保已安装 Node.js 和 npm。
    *   尝试删除 `frontend/node_modules` 目录和 `frontend/package-lock.json` 文件，然后重新运行 `npm install`。
*   **后端依赖问题**:
    *   如果遇到 Python 包相关的错误，尝试重新构建后端镜像：`docker-compose build backend`，然后重启服务。
*   **Neo4j 无法启动或连接**:
    *   检查 `docker-compose logs neo4j` 获取错误信息。
    *   确保 `.env` 文件中的 `NEO4J_USER` 和 `NEO4J_PASSWORD` 与 `docker-compose.yml` 中 `neo4j` 服务的 `NEO4J_AUTH` 环境变量设置兼容。默认脚本和配置应能协同工作。
    *   如果 Neo4j 数据损坏 (罕见)，您可以尝试 `docker-compose down -v` 来移除卷并重新开始。**警告：这将删除所有Neo4j数据。**
*   **热重载不工作**:
    *   确保 `docker-compose.yml` 中的卷挂载配置正确，并且指向您本地的源代码目录。
    *   前端: Vite HMR 通常开箱即用。检查浏览器控制台是否有错误。
    *   后端: Uvicorn `--reload` 依赖于文件系统事件。在某些虚拟化或文件系统设置下可能存在问题，但这在典型 Docker 设置中较少见。

---

祝您开发愉快！