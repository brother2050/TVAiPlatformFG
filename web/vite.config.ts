import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import { resolve } from 'path'

export default defineConfig({
  plugins: [vue()],
  resolve: {
    alias: {
      '@': resolve(__dirname, 'src'),
    },
  },
  build: {
    rollupOptions: {
      output: {
        manualChunks: {
          // Vue 核心
          'vue-vendor': ['vue', 'vue-router', 'pinia'],
          // Element Plus 单独分包
          'element-plus': ['element-plus'],
          // 编辑器相关库
          'editor-vendor': ['monaco-editor', 'fabric'],
          // 音视频处理
          'media-vendor': ['wavesurfer.js'],
        },
      },
    },
    // 启用 gzip 压缩
    gzipSize: true,
  },
  server: {
    port: 3000,
    proxy: {
      '/api': {
        target: 'http://localhost:8100',
        changeOrigin: true,
      },
    },
  },
})
