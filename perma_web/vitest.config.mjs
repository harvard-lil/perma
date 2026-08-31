import { defineConfig } from 'vitest/config'
import vue from '@vitejs/plugin-vue'
import path from 'node:path'

export default defineConfig({
  plugins: [vue()],
  resolve: {
    alias: {
      'jstree-css': path.resolve(import.meta.dirname, 'node_modules/jstree/dist/themes'),
    },
  },
  test: {
    environment: 'jsdom',
    include: ['spec/vitest/**/*.spec.js', 'spec/frontend/**/*.spec.js', 'spec/build/**/*.spec.js'],
    setupFiles: ['./spec/vitest.setup.js'],
  },
})
