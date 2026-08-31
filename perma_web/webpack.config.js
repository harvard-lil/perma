var path = require("path");
var webpack = require('webpack');
var autoprefixer = require('autoprefixer');
var BundleTracker = require('webpack-bundle-tracker');
var MiniCssExtractPlugin = require('mini-css-extract-plugin');
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
    filename: "[name].js",  // "[name]-[hash].js",  // let hashes be handled by django
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
      // Automatically detect jQuery and $ as free var in modules and inject the jquery library
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

    new MiniCssExtractPlugin(),
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
          "resolve-url-loader",
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
                // Suppressed, not fixed. Every Sass deprecation here (@import,
                // color-functions, if-function) originates in bootstrap-sass or
                // compass-mixins, which Phase 4 removes; quietDeps silences only
                // dependency SCSS, so our own deprecations still surface.
                // Phase 4 must delete this line.
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
      'airbrake-js$': 'airbrake-js/lib/client.js', // Exact match
      'airbrake-js': 'airbrake-js/lib', // and again with a fuzzy match,

      'jstree-css': 'jstree/dist/themes',

      'handlebars': 'handlebars/dist/handlebars.min.js',

      'bootstrap': 'bootstrap-sass/assets/stylesheets/bootstrap',
      'bootstrap-js': 'bootstrap-sass/assets/javascripts/bootstrap',

      'papaparse': 'papaparse/papaparse.min.js',

      'jquery-form': 'jquery-form/jquery.form.js',

      'vue': 'vue/dist/vue.esm-bundler.js'
    }
  },

  watchOptions: {
    poll: false,
    ignored: /node_modules/
  },

  devtool: "source-map",  // dev-only?

}
