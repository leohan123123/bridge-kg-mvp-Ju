# 常见问题排查

## 启动问题
1. **端口占用**：检查3000、8000、7474端口是否已被其他应用占用。
   - `sudo lsof -i :3000` (macOS/Linux)
   - `netstat -ano | findstr :3000` (Windows)
2. **Docker权限**：确保Docker daemon正在运行，并且当前用户有权限访问Docker。
   - 尝试运行 `docker ps`，如果报错，请检查Docker安装和权限。
   - 在Linux上，可能需要将用户添加到 `docker` 组或使用 `sudo docker-compose up -d`。
3. **依赖安装**：
   - 后端依赖由Docker处理。
   - 前端依赖在 `frontend/Dockerfile.dev` 中通过 `npm install` 安装。如果遇到前端相关问题，可以尝试进入前端容器手动安装：
     `docker-compose exec frontend bash`
     `npm install`
     `exit`
4. **.env 文件**：确保项目根目录下有 `.env` 文件。如果不存在，`scripts/setup.sh` 会尝试从 `.env.example` 复制。如果手动操作，请自行复制并按需修改。
5. **Docker Compose版本**：确保安装了兼容的 Docker Compose 版本 (通常 v1.28+ 或 v2.x)。

## 运行时问题
1. **API连接失败** (前端无法访问后端)：
   - 检查后端服务日志：`docker-compose logs backend`。
   - 确认后端服务是否在 `docker-compose.yml` 中正确配置并已启动：`docker-compose ps`。
   - 检查浏览器开发者工具的网络请求，看是否有具体的错误信息。
   - 确认 `VITE_API_BASE_URL` (在 `.env` 或前端配置中) 是否正确指向后端服务 (例如 `http://localhost:8000`)。在本项目中，Vite配置了代理，所以前端应直接请求 `/api/...`。
2. **页面白屏**：
   - 打开浏览器开发者工具 (通常按 F12)，查看控制台 (Console) 是否有JavaScript错误。
   - 检查网络 (Network) 标签页，看是否有资源加载失败 (404等)。
3. **Neo4j连接问题**：
   - 确认Neo4j容器正在运行：`docker-compose ps`。
   - 检查Neo4j日志：`docker-compose logs neo4j`。
   - 确认 `.env` 文件中的 `NEO4J_URI`, `NEO4J_USER`, `NEO4J_PASSWORD` 与 `docker-compose.yml` 中Neo4j服务的环境变量配置一致。
   - 尝试通过浏览器访问 Neo4j Browser (`http://localhost:7474`) 并使用配置的凭据登录。
4. **数据未显示/加载**：
   - 检查相关API请求是否成功以及返回的数据是否符合预期（使用浏览器开发者工具）。
   - 检查后端日志 (`docker-compose logs backend`) 看是否有处理请求时的错误。

## 性能问题
1. **加载缓慢**：
   - 首次启动由于需要构建Docker镜像和下载依赖，可能会比较慢。
   - 清除浏览器缓存和localStorage/sessionStorage。
   - 检查系统资源占用（CPU、内存）。
2. **大数据卡顿**：
   - 对于大数据量表格或列表，确保已实现虚拟滚动或分页。
   - 复杂的图表渲染大量数据点时可能会卡顿，考虑数据聚合或采样。
   - 检查浏览器控制台是否有性能相关的警告。

## 其他
1. **文件权限问题** (尤其在Linux上)：
   - 如果Docker容器内的应用无法写入挂载的卷 (e.g., logs, data)，可能是由于宿主机和容器内用户ID不匹配。尝试修改挂载卷的权限或在Dockerfile中设置用户。
2. **前端热重载不工作**：
   - 确认 `frontend/vite.config.ts` (或 .js) 中HMR配置正确。
   - 确认Docker卷挂载 (`./frontend:/app`) 是否正常工作，使得宿主机文件更改能同步到容器内。

---
如果以上未能解决问题，请尝试提供以下信息进行提问：
- 详细的操作步骤。
- 相关的错误日志（浏览器控制台、后端服务日志、Docker日志等）。
- 您的操作系统和Docker版本。
