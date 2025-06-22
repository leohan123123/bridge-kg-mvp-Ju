import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    host: '0.0.0.0', // 允许外部访问
    port: 5173,      // 明确指定端口，与docker-compose.yml一致
    hmr: {
      overlay: true, // 当出现编译错误时，在浏览器中显示一个覆盖层
    },
  },
  // 定义环境变量的前缀，默认为 VITE_
  // envPrefix: 'APP_',
})
