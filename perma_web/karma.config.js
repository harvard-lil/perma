// webpack.config.js instantiates BundleTracker when it is required, writing
// the karma build's chunk list to webpack-stats.json -- the file Django reads
// to find the real bundles. Point it elsewhere before the require, so running
// the JS tests cannot clobber the app's stats file (which, in the test image,
// is baked in with no way to regenerate it).
if (!process.env.BUNDLE_TRACKER_PATH) {
  process.env.BUNDLE_TRACKER_PATH = '/tmp/webpack-stats-karma.json';
}
var webpackConfig = require('./webpack.config.js');
var path = require("path");

if (!process.env.CHROMIUM_BIN) {
  process.env.CHROMIUM_BIN = '/usr/local/bin/playwright-chromium';
}

module.exports = function(config) {
  config.set({
    basePath: __dirname,
    frameworks: ['jasmine-ajax', 'jasmine',],

    reporters: ['progress'],
    port: 9876,
    colors: false,
    logLevel: config.LOG_INFO,
    autoWatch: true,
    usePolling: true,
    browsers: ['chromium_with_flags'],
    customLaunchers: {
      chromium_with_flags: {
        base: 'ChromiumHeadless',
        flags: ['--disable-web-security', '--disable-site-isolation-trials', '--no-sandbox']
      }
    },
    singleRun: false,
    autoWatchBatchDelay: 300,

    files: [
      './spec/javascripts/*.js'
    ],

    preprocessors: {'./spec/javascripts/*.js': ['webpack', 'sourcemap']},

    webpack: {
      mode: 'none',
      module: webpackConfig.module,
      resolve: webpackConfig.resolve,
      plugins: webpackConfig.plugins,
      devtool: "source-map-inline",
      watchOptions: webpackConfig.watchOptions,
    },

    webpackMiddleware: {
      // noInfo: true
    }
  });
}

webpackConfig.module.rules[0].options.plugins.push(["@babel/plugin-transform-modules-commonjs"]);
