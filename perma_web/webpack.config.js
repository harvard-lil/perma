var path = require("path");
var webpack = require('webpack');
var autoprefixer = require('autoprefixer');
var BundleTracker = require('webpack-bundle-tracker');
var MiniCssExtractPlugin = require('mini-css-extract-plugin');

// Content-hashed bundle names for the container image, where every file under
// static/bundles is published to the static bucket as immutable and kept
// forever, so a page rendered by one version still finds its own bundles
// while another version is serving. The image build sets
// WEBPACK_CONTENT_HASH=1 (Dockerfile, assets stage). Everything else -- local
// development and the bundles committed for the Salt hosts -- keeps plain
// names. Django finds either through webpack-stats.json.
var contentHash = process.env.WEBPACK_CONTENT_HASH === '1';
const { VueLoaderPlugin } = require('vue-loader')

module.exports = {
  context: __dirname,
  mode: 'none',

  optimization: {
    // Vue's esm-bundler build reads process.env.NODE_ENV at runtime. Webpack 4 shimmed
    // Node globals automatically; Webpack 5 does not, so an undefined `process` throws
    // in the browser. 'development' keeps the dev-warning behaviour the Webpack 4
    // bundles already shipped -- switching to 'production' is a product change.
    nodeEnv: 'development',
  },

  entry: {
    'single-link': [
      './static/js/single-link.module.js',
      './static/css/style-responsive-archive.scss'
    ],

    'global': [
      './static/js/global.js',
      './static/css/style-responsive.scss',
      './static/vendors/font-awesome/font-awesome.min.css',
    ],

    // each of these entry points will also include global.js, so should be listed in CommonsChunkPlugin below
    'single-link-permissions': './static/js/single-link-permissions.module',
    'link-delete-confirm': './static/js/link-delete-confirm',
    'developer-docs': './static/js/developer-docs',
    'admin-stats': './static/js/admin-stats',

    // for the new Vue frontend
    'dashboard': './static/frontend/pages/dashboard.js',
  },

  output: {
    path: path.resolve('./static/bundles/'),
    filename: contentHash ? "[name]-[contenthash].js" : "[name].js",
    chunkFilename: contentHash ? "[id]-[contenthash].js" : "[id].js",
    assetModuleFilename: "[contenthash][ext]",

  },

  plugins: [
    // write out a list of generated files, so Django can find them.
    // v3 takes the directory and the basename separately; a path passed as
    // `filename` is ignored. Allow overriding the directory via env var for tests.
    new BundleTracker({
      path: process.env.BUNDLE_TRACKER_DIR || __dirname,
      filename: 'webpack-stats.json',
    }),

    new webpack.ProvidePlugin({
      // Share one jQuery instance between Bootstrap 3, jsTree, and application code.
      jQuery: "jquery", $: "jquery", "window.jQuery": "jquery"
    }),


    // NB: this plugin was removed in webpack v4; this strategy does not
    // avoid a duplicate runtime if using the new SplitChunks optimization.
    /*
     We want to include global.js on just about every page, and then some pages have a second js file included as well.
     We don't want a redundant webpack runtime added to the second js files.
     Using CommonsChunkPlugin with `minChunks: Infinity` does what we want -- the runtime just goes into the first file,
     but nothing gets moved around.
     */
    // new webpack.optimize.CommonsChunkPlugin({
    //   name: "global",
    //   chunks: ["global", "create", "single-link-permissions", "map", "link-delete-confirm", "developer-docs", "stats", "admin-stats"],
    //   minChunks: Infinity,
    // }),

    new MiniCssExtractPlugin({
      filename: contentHash ? "[name]-[contenthash].css" : "[name].css",
      chunkFilename: contentHash ? "[id]-[contenthash].css" : "[id].css",
    }),
    new VueLoaderPlugin()
  ],

  module: {
    rules: [
      // javascript
      { test: /\.jsx?$/,
        exclude: /node_modules/,
        loader: 'babel-loader',
        options: {
          // Babel 8 removed transform-runtime's `corejs` option and preset-env's
          // `useBuiltIns`. `usage-pure` is their replacement and keeps the previous
          // behaviour: polyfills resolve from core-js-pure instead of patching globals.
          plugins: [
            '@babel/plugin-transform-runtime',
            ['babel-plugin-polyfill-corejs3', {method: 'usage-pure', version: '3.50'}]
          ],
          presets: ['@babel/preset-env']  // browser targets come from ./browserslist
        }
      },

      // Vue stuff
      {
        test: /\.vue$/,
        loader: 'vue-loader'
      },

      {
        test: /\.mjs$/,
        include: /node_modules/,
        type: "javascript/auto"
      },

      // inline css
      {
        test: /\.css$/,
        use: [MiniCssExtractPlugin.loader, "css-loader"]
      },

      // image files (likely included by css)
      {
        test: /\.(jpg|jpeg|png|gif)$/,
        type: 'asset',
        parser: { dataUrlCondition: { maxSize: 10000 } }
      },

      // scss
      {
        test: /\.scss$/,
        use: [
          MiniCssExtractPlugin.loader,
          "css-loader",
          // SCSS files share one directory, and Bootstrap's font paths are
          // configured explicitly, so relative URLs do not need resolve-url-loader.
          {
            loader: 'postcss-loader',
            options: {
	      postcssOptions: {
                plugins: [
                  require('autoprefixer'),
                ]
              }
	    }
          },
          {
            loader: 'sass-loader',
            options: {
              sourceMap: true,
              sassOptions: {
                precision: 8,
                // Legacy Bootstrap/Compass partials still use deprecated Sass APIs.
                // Keep application warnings visible while suppressing dependency warnings.
                quietDeps: true
              }
              // include precision=8 for bootstrap -- see https://github.com/twbs/bootstrap-sass/issues/409
            },
          },
        ]
      },

      // bootstrap fonts
      {
        test: /\.woff(2)?(\?v=[0-9]\.[0-9]\.[0-9])?$/,
        type: 'asset',
        parser: { dataUrlCondition: { maxSize: 10000 } },
        generator: { dataUrl: { mimetype: 'application/font-woff' } }
      },
      {
        test: /\.(ttf|otf|eot|svg)(\?v=[0-9]\.[0-9]\.[0-9])?$/,
        type: 'asset',
        parser: { dataUrlCondition: { maxSize: 10000 } }
      }
    ],
  },

  resolve: {
    modules: ['node_modules'],
    extensions: ['.js', '.jsx'],

    alias: {
      'jstree-css': 'jstree/dist/themes',

      'handlebars': 'handlebars/dist/handlebars.min.js',

      'bootstrap': 'bootstrap-sass/assets/stylesheets/bootstrap',
      'bootstrap-js': 'bootstrap-sass/assets/javascripts/bootstrap',

      // Removed with their packages in Phase 5: 'jquery-form' (declared but
      // never imported), plus 'airbrake-js' and 'papaparse', which aliased
      // packages that were not even declared and so resolved to nothing.

      'vue': 'vue/dist/vue.esm-bundler.js'
    }
  },

  watchOptions: {
    poll: false,
    ignored: /node_modules/
  },

  devtool: "source-map",  // dev-only?

}
