var path = require("path");
var webpack = require('webpack');
var autoprefixer = require('autoprefixer');
var BundleTracker = require('webpack-bundle-tracker');
var MiniCssExtractPlugin = require('mini-css-extract-plugin');
const { VueLoaderPlugin } = require('vue-loader')

module.exports = {
  context: __dirname,
  mode: 'none',

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
    'create': './static/js/create',
    'single-link-permissions': './static/js/single-link-permissions.module',
    'link-delete-confirm': './static/js/link-delete-confirm',
    'developer-docs': './static/js/developer-docs',
    'admin-stats': './static/js/admin-stats',

    // for the new Vue frontend
    'dashboard': './frontend/pages/dashboard.js',
  },

  output: {
    path: path.resolve('./static/bundles/'),
    filename: "[name].js",  // "[name]-[hash].js",  // let hashes be handled by django
  },

  plugins: [
    // write out a list of generated files, so Django can find them
    // Allow overriding via env var for tests.
    new BundleTracker({filename: process.env.BUNDLE_TRACKER_PATH || './webpack-stats.json'}),

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
          plugins: [
            [
              "@babel/plugin-transform-runtime",
              {
                "corejs": 3,
              }
            ]
          ],  // add polyfills for <es6 browsers
          presets: ['@babel/preset-env']
        }
      },

      // handlebars template
      {
        test: /\.handlebars$/,
        loader: 'handlebars-loader',
        options: {
          runtime: 'handlebars/dist/handlebars.min.js',
          helperDirs: [
            __dirname + "/static/js/hbs/helpers",
          ]
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
        loader: 'url-loader?limit=10000'
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
                precision: 8
              }
              // include precision=8 for bootstrap -- see https://github.com/twbs/bootstrap-sass/issues/409
            },
          },
        ]
      },

      // bootstrap fonts
      {
        test: /\.woff(2)?(\?v=[0-9]\.[0-9]\.[0-9])?$/,
        loader: 'url-loader',
        options: {
          limit: 10000,
          mimetype: 'application/font-woff',
          esModule: false,
        }
      },
      {
        test: /\.(ttf|otf|eot|svg)(\?v=[0-9]\.[0-9]\.[0-9])?$/,
        loader: 'url-loader',
        options: {
          limit: 10000,
          esModule: false,
        }
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
