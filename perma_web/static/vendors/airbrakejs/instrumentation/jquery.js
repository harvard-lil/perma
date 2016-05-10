(function(f){if(typeof exports==="object"&&typeof module!=="undefined"){module.exports=f()}else if(typeof define==="function"&&define.amd){define([],f)}else{var g;if(typeof window!=="undefined"){g=window}else if(typeof global!=="undefined"){g=global}else if(typeof self!=="undefined"){g=self}else{g=this}g=(g.airbrakeJs||(g.airbrakeJs = {}));g=(g.instrumentation||(g.instrumentation = {}));g.jquery = f()}})(function(){var define,module,exports;return (function e(t,n,r){function s(o,u){if(!n[o]){if(!t[o]){var a=typeof require=="function"&&require;if(!u&&a)return a(o,!0);if(i)return i(o,!0);var f=new Error("Cannot find module '"+o+"'");throw f.code="MODULE_NOT_FOUND",f}var l=n[o]={exports:{}};t[o][0].call(l.exports,function(e){var n=t[o][1][e];return s(n?n:e)},l,l.exports,e,t,n,r)}return n[o].exports}var i=typeof require=="function"&&require;for(var o=0;o<r.length;o++)s(r[o]);return s})({1:[function(require,module,exports){
(function (global){
var instrumentJQuery;

instrumentJQuery = function(client, jq) {
  var jqCallbacks, jqEventAdd, jqReady, wrapArguments;
  if (jq == null) {
    jq = global.jQuery;
  }
  wrapArguments = function(args) {
    var arg, i, j, len, type;
    for (i = j = 0, len = args.length; j < len; i = ++j) {
      arg = args[i];
      type = typeof arg;
      if (type === 'function') {
        args[i] = client.wrap(arg);
      } else if (arg && arg.length && type !== 'string') {
        args[i] = wrapArguments(arg);
      }
    }
    return args;
  };
  jqEventAdd = jq.event.add;
  jq.event.add = function(elem, types, handler, data, selector) {
    if (handler.handler) {
      if (!handler.handler.guid) {
        handler.handler.guid = jq.guid++;
      }
      handler.handler = client.wrap(handler.handler);
    } else {
      if (!handler.guid) {
        handler.guid = jq.guid++;
      }
      handler = client.wrap(handler);
    }
    return jqEventAdd(elem, types, handler, data, selector);
  };
  jqCallbacks = jq.Callbacks;
  jq.Callbacks = function(options) {
    var cb, cbAdd;
    cb = jqCallbacks(options);
    cbAdd = cb.add;
    cb.add = function() {
      return cbAdd.apply(this, wrapArguments(arguments));
    };
    return cb;
  };
  jqReady = jq.fn.ready;
  jq.fn.ready = function(fn) {
    return jqReady(client.wrap(fn));
  };
  return jq;
};

module.exports = instrumentJQuery;



}).call(this,typeof global !== "undefined" ? global : typeof self !== "undefined" ? self : typeof window !== "undefined" ? window : {})
},{}]},{},[1])(1)
});