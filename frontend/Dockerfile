# Dockerfile for Frontend Production Build

# ---- Build Stage ----
FROM node:18-alpine as builder

WORKDIR /app

# 复制 package.json 和 package-lock.json (或 yarn.lock)
COPY package*.json ./
# COPY yarn.lock ./ # 如果使用Yarn

# 安装依赖
RUN npm install --frozen-lockfile
# RUN yarn install --frozen-lockfile # 如果使用Yarn

# 复制所有源代码
COPY . .

# 构建生产版本
# 环境变量 VITE_API_BASE_URL 可以在构建时传入，或在运行时由Nginx配置
# ARG VITE_API_BASE_URL=/api # 示例：如果API通过Nginx反向代理到同一域名下
# RUN npm run build -- --base=$VITE_API_BASE_URL # 如果需要动态base
RUN npm run build

# ---- Serve Stage ----
# 使用 Nginx 提供静态文件服务
FROM nginx:1.25-alpine

# 移除默认的 Nginx 欢迎页面
RUN rm -rf /usr/share/nginx/html/*

# 从构建阶段复制构建好的静态文件到 Nginx 的 www 目录
COPY --from=builder /app/dist /usr/share/nginx/html

# （可选）复制自定义的 Nginx 配置文件
# COPY nginx.conf /etc/nginx/conf.d/default.conf
# 如果不提供自定义配置，Nginx 会使用默认配置来服务 /usr/share/nginx/html 下的文件

# Nginx 默认监听 80 端口
EXPOSE 80

# 启动 Nginx
CMD ["nginx", "-g", "daemon off;"]
