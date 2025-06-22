import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],
  css: {
    preprocessorOptions: {
      less: {
        javascriptEnabled: true, // 支持 Less 内联 JavaScript
      },
    },
  },
  server: {
    port: 3000, // 可以自定义端口
    open: true // 自动打开浏览器
  }
});
