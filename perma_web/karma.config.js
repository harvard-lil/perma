var webpackConfig = require('./webpack.config.js');
var path = require("path");

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
    browsers: ['PhantomJS'],
    singleRun: false,
    autoWatchBatchDelay: 300,

    files: [
      './spec/javascripts/*.js'
    ],

    preprocessors: {'./spec/javascripts/*.js': ['webpack', 'sourcemap']},

    webpack: {
      module: webpackConfig.module,
      resolve: webpackConfig.resolve,
      plugins: [webpackConfig.plugins[1], webpackConfig.plugins[3]],
      devtool: "source-map-inline",
      watchOptions: webpackConfig.watchOptions,
    },

    webpackMiddleware: {
      // noInfo: true
    }
  });
}
