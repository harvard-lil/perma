import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import inject from '@rollup/plugin-inject'
import path from 'path'
// import { viteCommonjs } from '@originjs/vite-plugin-commonjs'

// https://vitejs.dev/config/
export default defineConfig({
  server: {
    host: '0.0.0.0',  // allow connections from outside the container
  },
  plugins: [
    inject({
        $: 'jquery',
        jQuery: 'jquery',
    }),
    vue(),
  ],
  define: {
  //   'global': {},
    // 'jQuery': 'jquery',
    // '$': 'jquery',
    // 'window.jQuery': 'jquery'
  },
  resolve: {
    alias: {
      'airbrake-js': path.resolve(__dirname, 'node_modules/airbrake-js/lib/client.js'),
      'jstree-css': path.resolve(__dirname, 'node_modules/jstree/dist/themes'),
      'handlebars': path.resolve(__dirname, 'node_modules/handlebars/dist/handlebars.min.js'),
      'bootstrap': path.resolve(__dirname, 'node_modules/bootstrap-sass/assets/stylesheets/bootstrap'),
      'bootstrap-js': path.resolve(__dirname, 'node_modules/bootstrap-sass/assets/javascripts/bootstrap'),
      'papaparse': path.resolve(__dirname, 'node_modules/papaparse/papaparse.min.js'),
      'jquery-form': path.resolve(__dirname, 'node_modules/jquery-form/jquery.form.js'),
      'vue': 'vue/dist/vue.esm-bundler.js',
      '@': path.resolve(__dirname, 'static'),
    }
  },
  base: "",
  build: {
    manifest: "manifest.json",
    outDir: path.resolve("./static_vite/"),
    rollupOptions: {
      input: {
        'single-link': path.resolve(__dirname, 'static/js/single-link.module.js'),
        'global': path.resolve(__dirname, 'static/js/global.js'),
        'single-link-permissions': path.resolve(__dirname, 'static/js/single-link-permissions.module.js'),
        'link-delete-confirm': path.resolve(__dirname, 'static/js/link-delete-confirm.js'),
        'developer-docs': path.resolve(__dirname, 'static/js/developer-docs.js'),
        'admin-stats': path.resolve(__dirname, 'static/js/admin-stats.js'),
        'dashboard': path.resolve(__dirname, 'static/frontend/pages/dashboard.js'),
      },
      output: {
        entryFileNames: (chunkInfo) => {
          const name = chunkInfo.name;
          if (name.startsWith('static/')) {
            return name.replace('static/', '') + '.js';
          }
          return 'js/' + name + '.js';
        }
      },
    },
    sourcemap: true,
    // probably modulepreload polyfill no longer needed? https://caniuse.com/link-rel-modulepreload
    modulePreload: { polyfill: false },
  },
  // assetsInclude: ['**/*.woff', '**/*.woff2', '**/*.ttf', '**/*.otf', '**/*.eot', '**/*.svg'],
})
