var webpackConfig = require('./webpack.config.js');
var path = require("path");

process.env.CHROMIUM_BIN = '/root/.cache/ms-playwright/chromium-1012/chrome-linux/chrome'

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
