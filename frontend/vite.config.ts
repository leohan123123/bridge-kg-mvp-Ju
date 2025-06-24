import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    host: '0.0.0.0', // 允许外部访问
    port: 3000,      // 更改为要求的3000端口
    proxy: {
      // 字符串简写写法
      // '/foo': 'http://localhost:4567',
      // 选项写法
      '/api': {
        target: 'http://backend:8000', // 代理到后端服务，docker-compose中的服务名
        changeOrigin: true, // 需要虚拟主机站点
      },
    },
    hmr: {
      overlay: true, // 当出现编译错误时，在浏览器中显示一个覆盖层
    },
  },
  // 定义环境变量的前缀，默认为 VITE_
  // envPrefix: 'APP_',
})
