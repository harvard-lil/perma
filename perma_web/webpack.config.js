var path = require("path");
var webpack = require('webpack');
var autoprefixer = require('autoprefixer');
var BundleTracker = require('webpack-bundle-tracker');
var ExtractTextPlugin = require("extract-text-webpack-plugin");

module.exports = {
  context: __dirname,

  entry: {
    'single-link': ['./static/js/single-link.module'],
    'single-link-styles':'./static/css/style-responsive-archive.scss',

    'global': './static/js/global',
    'global-styles': [
      './static/css/style-responsive.scss',
      './static/vendors/font-awesome/font-awesome.min.css',
    ],

    // each of these entry points will also include global.js, so should be listed in CommonsChunkPlugin below
    'single-link-permissions': './static/js/single-link-permissions.module',
    'map': './static/js/map',
    'create': './static/js/create',
    'link-delete-confirm': './static/js/link-delete-confirm',
    'developer-docs': './static/js/developer-docs',
    'search': './static/js/search.module',
    'stats': './static/js/stats',
    'admin-stats': './static/js/admin-stats',
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

    /*
     We want to include global.js on just about every page, and then some pages have a second js file included as well.
     We don't want a redundant webpack runtime added to the second js files.
     Using CommonsChunkPlugin with `minChunks: Infinity` does what we want -- the runtime just goes into the first file,
     but nothing gets moved around.
     */
    new webpack.optimize.CommonsChunkPlugin({
      name: "global",
      chunks: ["global", "create", "single-link-permissions", "map", "create", "link-delete-confirm", "developer-docs", "search", "stats", "admin-stats"],
      minChunks: Infinity,
    }),

    new ExtractTextPlugin("[name].css"),

    // make sure sub-dependencies aren't included twice
    new webpack.optimize.DedupePlugin(),

    // uglify
    // new webpack.optimize.UglifyJsPlugin()
  ],

  module: {
    loaders: [
      // javascript
      { test: /\.jsx?$/,
        exclude: /node_modules/,
        loader: 'babel-loader',
        query: {
          plugins: ["transform-runtime"],  // add polyfills for <es6 browsers
          presets: ['es2015']
        }
      },

      // inline css
      {
        test: /\.css$/,
        loader: ExtractTextPlugin.extract("style", "css?sourceMap"),
      },

      // image files (likely included by css)
      {
        test: /\.(jpg|jpeg|png|gif)$/,
        loader: 'url-loader?limit=10000'
      },

      // scss
      {
        test: /\.scss$/,
        // include precision=8 for bootstrap -- see https://github.com/twbs/bootstrap-sass/issues/409
        loader: ExtractTextPlugin.extract("style", ["css", "resolve-url", "postcss", "sass?sourceMap=true&precision=8"]),
      },

      // bootstrap fonts
      {
        test: /\.woff(2)?(\?v=[0-9]\.[0-9]\.[0-9])?$/,
        loader: 'url-loader?limit=10000&mimetype=application/font-woff'
      },
      {
        test: /\.(ttf|otf|eot|svg)(\?v=[0-9]\.[0-9]\.[0-9])?$/,
        loader: 'url-loader?limit=10000'
      }
    ],
  },

  resolve: {
    modulesDirectories: ['node_modules'],
    extensions: ['', '.js', '.jsx'],

    alias: {
      'airbrake-js$': 'airbrake-js/lib/client.js', // Exact match
      'airbrake-js': 'airbrake-js/lib', // and again with a fuzzy match,

      'jstree-css': 'jstree/dist/themes',

      'handlebars': 'handlebars/dist/handlebars.min.js',

      'bootstrap': 'bootstrap-sass/assets/stylesheets/bootstrap',
      'bootstrap-js': 'bootstrap-sass/assets/javascripts/bootstrap',
    }
  },

  // use CPU-intensive polling because VirtualBox shared folder doesn't support inotify
  watchOptions: {
    poll: true
  },

  // tell sass where to find compass includes
  sassLoader: {
    includePaths: [path.resolve(__dirname, './node_modules/compass-mixins/lib')],
  },

  devtool: "source-map",  // dev-only?

  postcss: function () {
    return [
      require('autoprefixer')
    ];
  }
}
