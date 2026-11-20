import { defineConfig } from 'vite';

// three.js кладётся отдельным файлом: он не меняется от правки к правке и остаётся в кэше браузера
export default defineConfig({
  build: {
    chunkSizeWarningLimit: 900,
    rollupOptions: { output: { manualChunks: { three: ['three'] } } },
  },
});
