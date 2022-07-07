/******/ (function(modules) { // webpackBootstrap
/******/ 	// The module cache
/******/ 	var installedModules = {};
/******/
/******/ 	// The require function
/******/ 	function __webpack_require__(moduleId) {
/******/
/******/ 		// Check if module is in cache
/******/ 		if(installedModules[moduleId]) {
/******/ 			return installedModules[moduleId].exports;
/******/ 		}
/******/ 		// Create a new module (and put it into the cache)
/******/ 		var module = installedModules[moduleId] = {
/******/ 			i: moduleId,
/******/ 			l: false,
/******/ 			exports: {}
/******/ 		};
/******/
/******/ 		// Execute the module function
/******/ 		modules[moduleId].call(module.exports, module, module.exports, __webpack_require__);
/******/
/******/ 		// Flag the module as loaded
/******/ 		module.l = true;
/******/
/******/ 		// Return the exports of the module
/******/ 		return module.exports;
/******/ 	}
/******/
/******/
/******/ 	// expose the modules object (__webpack_modules__)
/******/ 	__webpack_require__.m = modules;
/******/
/******/ 	// expose the module cache
/******/ 	__webpack_require__.c = installedModules;
/******/
/******/ 	// define getter function for harmony exports
/******/ 	__webpack_require__.d = function(exports, name, getter) {
/******/ 		if(!__webpack_require__.o(exports, name)) {
/******/ 			Object.defineProperty(exports, name, { enumerable: true, get: getter });
/******/ 		}
/******/ 	};
/******/
/******/ 	// define __esModule on exports
/******/ 	__webpack_require__.r = function(exports) {
/******/ 		if(typeof Symbol !== 'undefined' && Symbol.toStringTag) {
/******/ 			Object.defineProperty(exports, Symbol.toStringTag, { value: 'Module' });
/******/ 		}
/******/ 		Object.defineProperty(exports, '__esModule', { value: true });
/******/ 	};
/******/
/******/ 	// create a fake namespace object
/******/ 	// mode & 1: value is a module id, require it
/******/ 	// mode & 2: merge all properties of value into the ns
/******/ 	// mode & 4: return value when already ns object
/******/ 	// mode & 8|1: behave like require
/******/ 	__webpack_require__.t = function(value, mode) {
/******/ 		if(mode & 1) value = __webpack_require__(value);
/******/ 		if(mode & 8) return value;
/******/ 		if((mode & 4) && typeof value === 'object' && value && value.__esModule) return value;
/******/ 		var ns = Object.create(null);
/******/ 		__webpack_require__.r(ns);
/******/ 		Object.defineProperty(ns, 'default', { enumerable: true, value: value });
/******/ 		if(mode & 2 && typeof value != 'string') for(var key in value) __webpack_require__.d(ns, key, function(key) { return value[key]; }.bind(null, key));
/******/ 		return ns;
/******/ 	};
/******/
/******/ 	// getDefaultExport function for compatibility with non-harmony modules
/******/ 	__webpack_require__.n = function(module) {
/******/ 		var getter = module && module.__esModule ?
/******/ 			function getDefault() { return module['default']; } :
/******/ 			function getModuleExports() { return module; };
/******/ 		__webpack_require__.d(getter, 'a', getter);
/******/ 		return getter;
/******/ 	};
/******/
/******/ 	// Object.prototype.hasOwnProperty.call
/******/ 	__webpack_require__.o = function(object, property) { return Object.prototype.hasOwnProperty.call(object, property); };
/******/
/******/ 	// __webpack_public_path__
/******/ 	__webpack_require__.p = "";
/******/
/******/
/******/ 	// Load entry module and return exports
/******/ 	return __webpack_require__(__webpack_require__.s = 56);
/******/ })
/************************************************************************/
/******/ ([
/* 0 */,
/* 1 */,
/* 2 */,
/* 3 */,
/* 4 */,
/* 5 */
/***/ (function(module, exports, __webpack_require__) {

"use strict";

var global = __webpack_require__(6);
var apply = __webpack_require__(8);
var uncurryThis = __webpack_require__(11);
var isCallable = __webpack_require__(12);
var getOwnPropertyDescriptor = __webpack_require__(13).f;
var isForced = __webpack_require__(47);
var path = __webpack_require__(27);
var bind = __webpack_require__(48);
var createNonEnumerableProperty = __webpack_require__(49);
var hasOwn = __webpack_require__(42);

var wrapConstructor = function (NativeConstructor) {
  var Wrapper = function (a, b, c) {
    if (this instanceof Wrapper) {
      switch (arguments.length) {
        case 0: return new NativeConstructor();
        case 1: return new NativeConstructor(a);
        case 2: return new NativeConstructor(a, b);
      } return new NativeConstructor(a, b, c);
    } return apply(NativeConstructor, this, arguments);
  };
  Wrapper.prototype = NativeConstructor.prototype;
  return Wrapper;
};

/*
  options.target      - name of the target object
  options.global      - target is the global object
  options.stat        - export as static methods of target
  options.proto       - export as prototype methods of target
  options.real        - real prototype method for the `pure` version
  options.forced      - export even if the native feature is available
  options.bind        - bind methods to the target, required for the `pure` version
  options.wrap        - wrap constructors to preventing global pollution, required for the `pure` version
  options.unsafe      - use the simple assignment of property instead of delete + defineProperty
  options.sham        - add a flag to not completely full polyfills
  options.enumerable  - export as enumerable property
  options.noTargetGet - prevent calling a getter on target
  options.name        - the .name of the function if it does not match the key
*/
module.exports = function (options, source) {
  var TARGET = options.target;
  var GLOBAL = options.global;
  var STATIC = options.stat;
  var PROTO = options.proto;

  var nativeSource = GLOBAL ? global : STATIC ? global[TARGET] : (global[TARGET] || {}).prototype;

  var target = GLOBAL ? path : path[TARGET] || createNonEnumerableProperty(path, TARGET, {})[TARGET];
  var targetPrototype = target.prototype;

  var FORCED, USE_NATIVE, VIRTUAL_PROTOTYPE;
  var key, sourceProperty, targetProperty, nativeProperty, resultProperty, descriptor;

  for (key in source) {
    FORCED = isForced(GLOBAL ? key : TARGET + (STATIC ? '.' : '#') + key, options.forced);
    // contains in native
    USE_NATIVE = !FORCED && nativeSource && hasOwn(nativeSource, key);

    targetProperty = target[key];

    if (USE_NATIVE) if (options.noTargetGet) {
      descriptor = getOwnPropertyDescriptor(nativeSource, key);
      nativeProperty = descriptor && descriptor.value;
    } else nativeProperty = nativeSource[key];

    // export native or implementation
    sourceProperty = (USE_NATIVE && nativeProperty) ? nativeProperty : source[key];

    if (USE_NATIVE && typeof targetProperty == typeof sourceProperty) continue;

    // bind timers to global for call from export context
    if (options.bind && USE_NATIVE) resultProperty = bind(sourceProperty, global);
    // wrap global constructors for prevent changs in this version
    else if (options.wrap && USE_NATIVE) resultProperty = wrapConstructor(sourceProperty);
    // make static versions for prototype methods
    else if (PROTO && isCallable(sourceProperty)) resultProperty = uncurryThis(sourceProperty);
    // default case
    else resultProperty = sourceProperty;

    // add a flag to not completely full polyfills
    if (options.sham || (sourceProperty && sourceProperty.sham) || (targetProperty && targetProperty.sham)) {
      createNonEnumerableProperty(resultProperty, 'sham', true);
    }

    createNonEnumerableProperty(target, key, resultProperty);

    if (PROTO) {
      VIRTUAL_PROTOTYPE = TARGET + 'Prototype';
      if (!hasOwn(path, VIRTUAL_PROTOTYPE)) {
        createNonEnumerableProperty(path, VIRTUAL_PROTOTYPE, {});
      }
      // export virtual prototype methods
      createNonEnumerableProperty(path[VIRTUAL_PROTOTYPE], key, sourceProperty);
      // export real prototype methods
      if (options.real && targetPrototype && !targetPrototype[key]) {
        createNonEnumerableProperty(targetPrototype, key, sourceProperty);
      }
    }
  }
};


/***/ }),
/* 6 */
/***/ (function(module, exports, __webpack_require__) {

/* WEBPACK VAR INJECTION */(function(global) {var check = function (it) {
  return it && it.Math == Math && it;
};

// https://github.com/zloirock/core-js/issues/86#issuecomment-115759028
module.exports =
  // eslint-disable-next-line es/no-global-this -- safe
  check(typeof globalThis == 'object' && globalThis) ||
  check(typeof window == 'object' && window) ||
  // eslint-disable-next-line no-restricted-globals -- safe
  check(typeof self == 'object' && self) ||
  check(typeof global == 'object' && global) ||
  // eslint-disable-next-line no-new-func -- fallback
  (function () { return this; })() || Function('return this')();

/* WEBPACK VAR INJECTION */}.call(this, __webpack_require__(7)))

/***/ }),
/* 7 */
/***/ (function(module, exports) {

var g;

// This works in non-strict mode
g = (function() {
	return this;
})();

try {
	// This works if eval is allowed (see CSP)
	g = g || new Function("return this")();
} catch (e) {
	// This works if the window reference is available
	if (typeof window === "object") g = window;
}

// g can still be undefined, but nothing to do about it...
// We return undefined, instead of nothing here, so it's
// easier to handle this case. if(!global) { ...}

module.exports = g;


/***/ }),
/* 8 */
/***/ (function(module, exports, __webpack_require__) {

var NATIVE_BIND = __webpack_require__(9);

var FunctionPrototype = Function.prototype;
var apply = FunctionPrototype.apply;
var call = FunctionPrototype.call;

// eslint-disable-next-line es/no-reflect -- safe
module.exports = typeof Reflect == 'object' && Reflect.apply || (NATIVE_BIND ? call.bind(apply) : function () {
  return call.apply(apply, arguments);
});


/***/ }),
/* 9 */
/***/ (function(module, exports, __webpack_require__) {

var fails = __webpack_require__(10);

module.exports = !fails(function () {
  var test = (function () { /* empty */ }).bind();
  // eslint-disable-next-line no-prototype-builtins -- safe
  return typeof test != 'function' || test.hasOwnProperty('prototype');
});


/***/ }),
/* 10 */
/***/ (function(module, exports) {

module.exports = function (exec) {
  try {
    return !!exec();
  } catch (error) {
    return true;
  }
};


/***/ }),
/* 11 */
/***/ (function(module, exports, __webpack_require__) {

var NATIVE_BIND = __webpack_require__(9);

var FunctionPrototype = Function.prototype;
var bind = FunctionPrototype.bind;
var call = FunctionPrototype.call;
var uncurryThis = NATIVE_BIND && bind.bind(call, call);

module.exports = NATIVE_BIND ? function (fn) {
  return fn && uncurryThis(fn);
} : function (fn) {
  return fn && function () {
    return call.apply(fn, arguments);
  };
};


/***/ }),
/* 12 */
/***/ (function(module, exports) {

// `IsCallable` abstract operation
// https://tc39.es/ecma262/#sec-iscallable
module.exports = function (argument) {
  return typeof argument == 'function';
};


/***/ }),
/* 13 */
/***/ (function(module, exports, __webpack_require__) {

var DESCRIPTORS = __webpack_require__(14);
var call = __webpack_require__(15);
var propertyIsEnumerableModule = __webpack_require__(16);
var createPropertyDescriptor = __webpack_require__(17);
var toIndexedObject = __webpack_require__(18);
var toPropertyKey = __webpack_require__(22);
var hasOwn = __webpack_require__(42);
var IE8_DOM_DEFINE = __webpack_require__(45);

// eslint-disable-next-line es/no-object-getownpropertydescriptor -- safe
var $getOwnPropertyDescriptor = Object.getOwnPropertyDescriptor;

// `Object.getOwnPropertyDescriptor` method
// https://tc39.es/ecma262/#sec-object.getownpropertydescriptor
exports.f = DESCRIPTORS ? $getOwnPropertyDescriptor : function getOwnPropertyDescriptor(O, P) {
  O = toIndexedObject(O);
  P = toPropertyKey(P);
  if (IE8_DOM_DEFINE) try {
    return $getOwnPropertyDescriptor(O, P);
  } catch (error) { /* empty */ }
  if (hasOwn(O, P)) return createPropertyDescriptor(!call(propertyIsEnumerableModule.f, O, P), O[P]);
};


/***/ }),
/* 14 */
/***/ (function(module, exports, __webpack_require__) {

var fails = __webpack_require__(10);

// Detect IE8's incomplete defineProperty implementation
module.exports = !fails(function () {
  // eslint-disable-next-line es/no-object-defineproperty -- required for testing
  return Object.defineProperty({}, 1, { get: function () { return 7; } })[1] != 7;
});


/***/ }),
/* 15 */
/***/ (function(module, exports, __webpack_require__) {

var NATIVE_BIND = __webpack_require__(9);

var call = Function.prototype.call;

module.exports = NATIVE_BIND ? call.bind(call) : function () {
  return call.apply(call, arguments);
};


/***/ }),
/* 16 */
/***/ (function(module, exports, __webpack_require__) {

"use strict";

var $propertyIsEnumerable = {}.propertyIsEnumerable;
// eslint-disable-next-line es/no-object-getownpropertydescriptor -- safe
var getOwnPropertyDescriptor = Object.getOwnPropertyDescriptor;

// Nashorn ~ JDK8 bug
var NASHORN_BUG = getOwnPropertyDescriptor && !$propertyIsEnumerable.call({ 1: 2 }, 1);

// `Object.prototype.propertyIsEnumerable` method implementation
// https://tc39.es/ecma262/#sec-object.prototype.propertyisenumerable
exports.f = NASHORN_BUG ? function propertyIsEnumerable(V) {
  var descriptor = getOwnPropertyDescriptor(this, V);
  return !!descriptor && descriptor.enumerable;
} : $propertyIsEnumerable;


/***/ }),
/* 17 */
/***/ (function(module, exports) {

module.exports = function (bitmap, value) {
  return {
    enumerable: !(bitmap & 1),
    configurable: !(bitmap & 2),
    writable: !(bitmap & 4),
    value: value
  };
};


/***/ }),
/* 18 */
/***/ (function(module, exports, __webpack_require__) {

// toObject with fallback for non-array-like ES3 strings
var IndexedObject = __webpack_require__(19);
var requireObjectCoercible = __webpack_require__(21);

module.exports = function (it) {
  return IndexedObject(requireObjectCoercible(it));
};


/***/ }),
/* 19 */
/***/ (function(module, exports, __webpack_require__) {

var global = __webpack_require__(6);
var uncurryThis = __webpack_require__(11);
var fails = __webpack_require__(10);
var classof = __webpack_require__(20);

var Object = global.Object;
var split = uncurryThis(''.split);

// fallback for non-array-like ES3 and non-enumerable old V8 strings
module.exports = fails(function () {
  // throws an error in rhino, see https://github.com/mozilla/rhino/issues/346
  // eslint-disable-next-line no-prototype-builtins -- safe
  return !Object('z').propertyIsEnumerable(0);
}) ? function (it) {
  return classof(it) == 'String' ? split(it, '') : Object(it);
} : Object;


/***/ }),
/* 20 */
/***/ (function(module, exports, __webpack_require__) {

var uncurryThis = __webpack_require__(11);

var toString = uncurryThis({}.toString);
var stringSlice = uncurryThis(''.slice);

module.exports = function (it) {
  return stringSlice(toString(it), 8, -1);
};


/***/ }),
/* 21 */
/***/ (function(module, exports, __webpack_require__) {

var global = __webpack_require__(6);

var TypeError = global.TypeError;

// `RequireObjectCoercible` abstract operation
// https://tc39.es/ecma262/#sec-requireobjectcoercible
module.exports = function (it) {
  if (it == undefined) throw TypeError("Can't call method on " + it);
  return it;
};


/***/ }),
/* 22 */
/***/ (function(module, exports, __webpack_require__) {

var toPrimitive = __webpack_require__(23);
var isSymbol = __webpack_require__(25);

// `ToPropertyKey` abstract operation
// https://tc39.es/ecma262/#sec-topropertykey
module.exports = function (argument) {
  var key = toPrimitive(argument, 'string');
  return isSymbol(key) ? key : key + '';
};


/***/ }),
/* 23 */
/***/ (function(module, exports, __webpack_require__) {

var global = __webpack_require__(6);
var call = __webpack_require__(15);
var isObject = __webpack_require__(24);
var isSymbol = __webpack_require__(25);
var getMethod = __webpack_require__(33);
var ordinaryToPrimitive = __webpack_require__(36);
var wellKnownSymbol = __webpack_require__(37);

var TypeError = global.TypeError;
var TO_PRIMITIVE = wellKnownSymbol('toPrimitive');

// `ToPrimitive` abstract operation
// https://tc39.es/ecma262/#sec-toprimitive
module.exports = function (input, pref) {
  if (!isObject(input) || isSymbol(input)) return input;
  var exoticToPrim = getMethod(input, TO_PRIMITIVE);
  var result;
  if (exoticToPrim) {
    if (pref === undefined) pref = 'default';
    result = call(exoticToPrim, input, pref);
    if (!isObject(result) || isSymbol(result)) return result;
    throw TypeError("Can't convert object to primitive value");
  }
  if (pref === undefined) pref = 'number';
  return ordinaryToPrimitive(input, pref);
};


/***/ }),
/* 24 */
/***/ (function(module, exports, __webpack_require__) {

var isCallable = __webpack_require__(12);

module.exports = function (it) {
  return typeof it == 'object' ? it !== null : isCallable(it);
};


/***/ }),
/* 25 */
/***/ (function(module, exports, __webpack_require__) {

var global = __webpack_require__(6);
var getBuiltIn = __webpack_require__(26);
var isCallable = __webpack_require__(12);
var isPrototypeOf = __webpack_require__(28);
var USE_SYMBOL_AS_UID = __webpack_require__(29);

var Object = global.Object;

module.exports = USE_SYMBOL_AS_UID ? function (it) {
  return typeof it == 'symbol';
} : function (it) {
  var $Symbol = getBuiltIn('Symbol');
  return isCallable($Symbol) && isPrototypeOf($Symbol.prototype, Object(it));
};


/***/ }),
/* 26 */
/***/ (function(module, exports, __webpack_require__) {

var path = __webpack_require__(27);
var global = __webpack_require__(6);
var isCallable = __webpack_require__(12);

var aFunction = function (variable) {
  return isCallable(variable) ? variable : undefined;
};

module.exports = function (namespace, method) {
  return arguments.length < 2 ? aFunction(path[namespace]) || aFunction(global[namespace])
    : path[namespace] && path[namespace][method] || global[namespace] && global[namespace][method];
};


/***/ }),
/* 27 */
/***/ (function(module, exports) {

module.exports = {};


/***/ }),
/* 28 */
/***/ (function(module, exports, __webpack_require__) {

var uncurryThis = __webpack_require__(11);

module.exports = uncurryThis({}.isPrototypeOf);


/***/ }),
/* 29 */
/***/ (function(module, exports, __webpack_require__) {

/* eslint-disable es/no-symbol -- required for testing */
var NATIVE_SYMBOL = __webpack_require__(30);

module.exports = NATIVE_SYMBOL
  && !Symbol.sham
  && typeof Symbol.iterator == 'symbol';


/***/ }),
/* 30 */
/***/ (function(module, exports, __webpack_require__) {

/* eslint-disable es/no-symbol -- required for testing */
var V8_VERSION = __webpack_require__(31);
var fails = __webpack_require__(10);

// eslint-disable-next-line es/no-object-getownpropertysymbols -- required for testing
module.exports = !!Object.getOwnPropertySymbols && !fails(function () {
  var symbol = Symbol();
  // Chrome 38 Symbol has incorrect toString conversion
  // `get-own-property-symbols` polyfill symbols converted to object are not Symbol instances
  return !String(symbol) || !(Object(symbol) instanceof Symbol) ||
    // Chrome 38-40 symbols are not inherited from DOM collections prototypes to instances
    !Symbol.sham && V8_VERSION && V8_VERSION < 41;
});


/***/ }),
/* 31 */
/***/ (function(module, exports, __webpack_require__) {

var global = __webpack_require__(6);
var userAgent = __webpack_require__(32);

var process = global.process;
var Deno = global.Deno;
var versions = process && process.versions || Deno && Deno.version;
var v8 = versions && versions.v8;
var match, version;

if (v8) {
  match = v8.split('.');
  // in old Chrome, versions of V8 isn't V8 = Chrome / 10
  // but their correct versions are not interesting for us
  version = match[0] > 0 && match[0] < 4 ? 1 : +(match[0] + match[1]);
}

// BrowserFS NodeJS `process` polyfill incorrectly set `.v8` to `0.0`
// so check `userAgent` even if `.v8` exists, but 0
if (!version && userAgent) {
  match = userAgent.match(/Edge\/(\d+)/);
  if (!match || match[1] >= 74) {
    match = userAgent.match(/Chrome\/(\d+)/);
    if (match) version = +match[1];
  }
}

module.exports = version;


/***/ }),
/* 32 */
/***/ (function(module, exports, __webpack_require__) {

var getBuiltIn = __webpack_require__(26);

module.exports = getBuiltIn('navigator', 'userAgent') || '';


/***/ }),
/* 33 */
/***/ (function(module, exports, __webpack_require__) {

var aCallable = __webpack_require__(34);

// `GetMethod` abstract operation
// https://tc39.es/ecma262/#sec-getmethod
module.exports = function (V, P) {
  var func = V[P];
  return func == null ? undefined : aCallable(func);
};


/***/ }),
/* 34 */
/***/ (function(module, exports, __webpack_require__) {

var global = __webpack_require__(6);
var isCallable = __webpack_require__(12);
var tryToString = __webpack_require__(35);

var TypeError = global.TypeError;

// `Assert: IsCallable(argument) is true`
module.exports = function (argument) {
  if (isCallable(argument)) return argument;
  throw TypeError(tryToString(argument) + ' is not a function');
};


/***/ }),
/* 35 */
/***/ (function(module, exports, __webpack_require__) {

var global = __webpack_require__(6);

var String = global.String;

module.exports = function (argument) {
  try {
    return String(argument);
  } catch (error) {
    return 'Object';
  }
};


/***/ }),
/* 36 */
/***/ (function(module, exports, __webpack_require__) {

var global = __webpack_require__(6);
var call = __webpack_require__(15);
var isCallable = __webpack_require__(12);
var isObject = __webpack_require__(24);

var TypeError = global.TypeError;

// `OrdinaryToPrimitive` abstract operation
// https://tc39.es/ecma262/#sec-ordinarytoprimitive
module.exports = function (input, pref) {
  var fn, val;
  if (pref === 'string' && isCallable(fn = input.toString) && !isObject(val = call(fn, input))) return val;
  if (isCallable(fn = input.valueOf) && !isObject(val = call(fn, input))) return val;
  if (pref !== 'string' && isCallable(fn = input.toString) && !isObject(val = call(fn, input))) return val;
  throw TypeError("Can't convert object to primitive value");
};


/***/ }),
/* 37 */
/***/ (function(module, exports, __webpack_require__) {

var global = __webpack_require__(6);
var shared = __webpack_require__(38);
var hasOwn = __webpack_require__(42);
var uid = __webpack_require__(44);
var NATIVE_SYMBOL = __webpack_require__(30);
var USE_SYMBOL_AS_UID = __webpack_require__(29);

var WellKnownSymbolsStore = shared('wks');
var Symbol = global.Symbol;
var symbolFor = Symbol && Symbol['for'];
var createWellKnownSymbol = USE_SYMBOL_AS_UID ? Symbol : Symbol && Symbol.withoutSetter || uid;

module.exports = function (name) {
  if (!hasOwn(WellKnownSymbolsStore, name) || !(NATIVE_SYMBOL || typeof WellKnownSymbolsStore[name] == 'string')) {
    var description = 'Symbol.' + name;
    if (NATIVE_SYMBOL && hasOwn(Symbol, name)) {
      WellKnownSymbolsStore[name] = Symbol[name];
    } else if (USE_SYMBOL_AS_UID && symbolFor) {
      WellKnownSymbolsStore[name] = symbolFor(description);
    } else {
      WellKnownSymbolsStore[name] = createWellKnownSymbol(description);
    }
  } return WellKnownSymbolsStore[name];
};


/***/ }),
/* 38 */
/***/ (function(module, exports, __webpack_require__) {

var IS_PURE = __webpack_require__(39);
var store = __webpack_require__(40);

(module.exports = function (key, value) {
  return store[key] || (store[key] = value !== undefined ? value : {});
})('versions', []).push({
  version: '3.21.1',
  mode: IS_PURE ? 'pure' : 'global',
  copyright: '© 2014-2022 Denis Pushkarev (zloirock.ru)',
  license: 'https://github.com/zloirock/core-js/blob/v3.21.1/LICENSE',
  source: 'https://github.com/zloirock/core-js'
});


/***/ }),
/* 39 */
/***/ (function(module, exports) {

module.exports = true;


/***/ }),
/* 40 */
/***/ (function(module, exports, __webpack_require__) {

var global = __webpack_require__(6);
var setGlobal = __webpack_require__(41);

var SHARED = '__core-js_shared__';
var store = global[SHARED] || setGlobal(SHARED, {});

module.exports = store;


/***/ }),
/* 41 */
/***/ (function(module, exports, __webpack_require__) {

var global = __webpack_require__(6);

// eslint-disable-next-line es/no-object-defineproperty -- safe
var defineProperty = Object.defineProperty;

module.exports = function (key, value) {
  try {
    defineProperty(global, key, { value: value, configurable: true, writable: true });
  } catch (error) {
    global[key] = value;
  } return value;
};


/***/ }),
/* 42 */
/***/ (function(module, exports, __webpack_require__) {

var uncurryThis = __webpack_require__(11);
var toObject = __webpack_require__(43);

var hasOwnProperty = uncurryThis({}.hasOwnProperty);

// `HasOwnProperty` abstract operation
// https://tc39.es/ecma262/#sec-hasownproperty
module.exports = Object.hasOwn || function hasOwn(it, key) {
  return hasOwnProperty(toObject(it), key);
};


/***/ }),
/* 43 */
/***/ (function(module, exports, __webpack_require__) {

var global = __webpack_require__(6);
var requireObjectCoercible = __webpack_require__(21);

var Object = global.Object;

// `ToObject` abstract operation
// https://tc39.es/ecma262/#sec-toobject
module.exports = function (argument) {
  return Object(requireObjectCoercible(argument));
};


/***/ }),
/* 44 */
/***/ (function(module, exports, __webpack_require__) {

var uncurryThis = __webpack_require__(11);

var id = 0;
var postfix = Math.random();
var toString = uncurryThis(1.0.toString);

module.exports = function (key) {
  return 'Symbol(' + (key === undefined ? '' : key) + ')_' + toString(++id + postfix, 36);
};


/***/ }),
/* 45 */
/***/ (function(module, exports, __webpack_require__) {

var DESCRIPTORS = __webpack_require__(14);
var fails = __webpack_require__(10);
var createElement = __webpack_require__(46);

// Thanks to IE8 for its funny defineProperty
module.exports = !DESCRIPTORS && !fails(function () {
  // eslint-disable-next-line es/no-object-defineproperty -- required for testing
  return Object.defineProperty(createElement('div'), 'a', {
    get: function () { return 7; }
  }).a != 7;
});


/***/ }),
/* 46 */
/***/ (function(module, exports, __webpack_require__) {

var global = __webpack_require__(6);
var isObject = __webpack_require__(24);

var document = global.document;
// typeof document.createElement is 'object' in old IE
var EXISTS = isObject(document) && isObject(document.createElement);

module.exports = function (it) {
  return EXISTS ? document.createElement(it) : {};
};


/***/ }),
/* 47 */
/***/ (function(module, exports, __webpack_require__) {

var fails = __webpack_require__(10);
var isCallable = __webpack_require__(12);

var replacement = /#|\.prototype\./;

var isForced = function (feature, detection) {
  var value = data[normalize(feature)];
  return value == POLYFILL ? true
    : value == NATIVE ? false
    : isCallable(detection) ? fails(detection)
    : !!detection;
};

var normalize = isForced.normalize = function (string) {
  return String(string).replace(replacement, '.').toLowerCase();
};

var data = isForced.data = {};
var NATIVE = isForced.NATIVE = 'N';
var POLYFILL = isForced.POLYFILL = 'P';

module.exports = isForced;


/***/ }),
/* 48 */
/***/ (function(module, exports, __webpack_require__) {

var uncurryThis = __webpack_require__(11);
var aCallable = __webpack_require__(34);
var NATIVE_BIND = __webpack_require__(9);

var bind = uncurryThis(uncurryThis.bind);

// optional / simple context binding
module.exports = function (fn, that) {
  aCallable(fn);
  return that === undefined ? fn : NATIVE_BIND ? bind(fn, that) : function (/* ...args */) {
    return fn.apply(that, arguments);
  };
};


/***/ }),
/* 49 */
/***/ (function(module, exports, __webpack_require__) {

var DESCRIPTORS = __webpack_require__(14);
var definePropertyModule = __webpack_require__(50);
var createPropertyDescriptor = __webpack_require__(17);

module.exports = DESCRIPTORS ? function (object, key, value) {
  return definePropertyModule.f(object, key, createPropertyDescriptor(1, value));
} : function (object, key, value) {
  object[key] = value;
  return object;
};


/***/ }),
/* 50 */
/***/ (function(module, exports, __webpack_require__) {

var global = __webpack_require__(6);
var DESCRIPTORS = __webpack_require__(14);
var IE8_DOM_DEFINE = __webpack_require__(45);
var V8_PROTOTYPE_DEFINE_BUG = __webpack_require__(51);
var anObject = __webpack_require__(52);
var toPropertyKey = __webpack_require__(22);

var TypeError = global.TypeError;
// eslint-disable-next-line es/no-object-defineproperty -- safe
var $defineProperty = Object.defineProperty;
// eslint-disable-next-line es/no-object-getownpropertydescriptor -- safe
var $getOwnPropertyDescriptor = Object.getOwnPropertyDescriptor;
var ENUMERABLE = 'enumerable';
var CONFIGURABLE = 'configurable';
var WRITABLE = 'writable';

// `Object.defineProperty` method
// https://tc39.es/ecma262/#sec-object.defineproperty
exports.f = DESCRIPTORS ? V8_PROTOTYPE_DEFINE_BUG ? function defineProperty(O, P, Attributes) {
  anObject(O);
  P = toPropertyKey(P);
  anObject(Attributes);
  if (typeof O === 'function' && P === 'prototype' && 'value' in Attributes && WRITABLE in Attributes && !Attributes[WRITABLE]) {
    var current = $getOwnPropertyDescriptor(O, P);
    if (current && current[WRITABLE]) {
      O[P] = Attributes.value;
      Attributes = {
        configurable: CONFIGURABLE in Attributes ? Attributes[CONFIGURABLE] : current[CONFIGURABLE],
        enumerable: ENUMERABLE in Attributes ? Attributes[ENUMERABLE] : current[ENUMERABLE],
        writable: false
      };
    }
  } return $defineProperty(O, P, Attributes);
} : $defineProperty : function defineProperty(O, P, Attributes) {
  anObject(O);
  P = toPropertyKey(P);
  anObject(Attributes);
  if (IE8_DOM_DEFINE) try {
    return $defineProperty(O, P, Attributes);
  } catch (error) { /* empty */ }
  if ('get' in Attributes || 'set' in Attributes) throw TypeError('Accessors not supported');
  if ('value' in Attributes) O[P] = Attributes.value;
  return O;
};


/***/ }),
/* 51 */
/***/ (function(module, exports, __webpack_require__) {

var DESCRIPTORS = __webpack_require__(14);
var fails = __webpack_require__(10);

// V8 ~ Chrome 36-
// https://bugs.chromium.org/p/v8/issues/detail?id=3334
module.exports = DESCRIPTORS && fails(function () {
  // eslint-disable-next-line es/no-object-defineproperty -- required for testing
  return Object.defineProperty(function () { /* empty */ }, 'prototype', {
    value: 42,
    writable: false
  }).prototype != 42;
});


/***/ }),
/* 52 */
/***/ (function(module, exports, __webpack_require__) {

var global = __webpack_require__(6);
var isObject = __webpack_require__(24);

var String = global.String;
var TypeError = global.TypeError;

// `Assert: Type(argument) is Object`
module.exports = function (argument) {
  if (isObject(argument)) return argument;
  throw TypeError(String(argument) + ' is not an object');
};


/***/ }),
/* 53 */,
/* 54 */,
/* 55 */,
/* 56 */
/***/ (function(module, exports, __webpack_require__) {

__webpack_require__(57);
__webpack_require__(199);
module.exports = __webpack_require__(200);


/***/ }),
/* 57 */
/***/ (function(module, __webpack_exports__, __webpack_require__) {

"use strict";
__webpack_require__.r(__webpack_exports__);
/* WEBPACK VAR INJECTION */(function($) {/* harmony import */ var _babel_runtime_corejs3_core_js_stable_instance_find__WEBPACK_IMPORTED_MODULE_0__ = __webpack_require__(59);
/* harmony import */ var _babel_runtime_corejs3_core_js_stable_instance_find__WEBPACK_IMPORTED_MODULE_0___default = /*#__PURE__*/__webpack_require__.n(_babel_runtime_corejs3_core_js_stable_instance_find__WEBPACK_IMPORTED_MODULE_0__);
/* harmony import */ var _sentry_browser__WEBPACK_IMPORTED_MODULE_1__ = __webpack_require__(77);



if (settings.USE_SENTRY) {
  _sentry_browser__WEBPACK_IMPORTED_MODULE_1__["init"]({
    dsn: settings.SENTRY_DSN,
    environment: settings.SENTRY_ENVIRONMENT,
    denyUrls: ['^https\:\/\/' + settings.PLAYBACK_HOST + '\/.*$'],
    // Set tracesSampleRate to 1.0 to capture 100%
    // of transactions for performance monitoring.
    // We recommend adjusting this value in production
    tracesSampleRate: settings.SENTRY_TRACES_SAMPLE_RATE
  });
}

var FastClick = __webpack_require__(156);

var ErrorHandler = __webpack_require__(157);

var Helpers = __webpack_require__(170);

__webpack_require__(195); // https://github.com/harvard-lil/accessibility-tools/tree/master/code/fix-links


__webpack_require__(196); // make menus work


__webpack_require__(197); // make menu toggle for small screen work


__webpack_require__(198); // make carousels work
// We used to use modernizr but have currently dropped it.
// If we want to include it again this is where to put it --
//    see https://github.com/Modernizr/Modernizr/issues/878#issuecomment-41448059
// https://www.npmjs.com/package/modernizr-webpack-plugin
// initialize fastclick


FastClick.attach(document.body); // initialize airbrake

ErrorHandler.init(); // set up jquery to properly set CSRF header on AJAX post
// via https://docs.djangoproject.com/en/dev/ref/contrib/csrf/#ajax

$.ajaxSetup({
  crossdomain: false,
  // obviates need for sameOrigin test
  beforeSend: function beforeSend(xhr, settings) {
    if (!Helpers.csrfSafeMethod(settings.type)) {
      xhr.setRequestHeader('X-CSRFToken', Helpers.getCookie('csrftoken'));
    }
  }
});
/*** event handlers ***/
// Add class to active text inputs

$('.text-input').focus(function () {
  $(this).addClass('text-input-active');
}).blur(function () {
  $(this).removeClass('text-input-active');
}); // Select the input text when the user clicks the element

$('.select-on-click').click(function () {
  $(this).select();
}); // clear popup alerts with a click

$(document).on('click', '.popup-alert', function () {
  $(this).remove();
}); // put focus on first form input element when a form is revealed by bootstrap UI

$('.collapse').on('shown.bs.collapse', function () {
  var _context;

  _babel_runtime_corejs3_core_js_stable_instance_find__WEBPACK_IMPORTED_MODULE_0___default()(_context = $(this)).call(_context, 'input[type="text"]').focus();
});
/* WEBPACK VAR INJECTION */}.call(this, __webpack_require__(58)))

/***/ }),
/* 58 */
/***/ (function(module, exports, __webpack_require__) {

var __WEBPACK_AMD_DEFINE_ARRAY__, __WEBPACK_AMD_DEFINE_RESULT__;/*!
 * jQuery JavaScript Library v3.6.0
 * https://jquery.com/
 *
 * Includes Sizzle.js
 * https://sizzlejs.com/
 *
 * Copyright OpenJS Foundation and other contributors
 * Released under the MIT license
 * https://jquery.org/license
 *
 * Date: 2021-03-02T17:08Z
 */
( function( global, factory ) {

	"use strict";

	if (  true && typeof module.exports === "object" ) {

		// For CommonJS and CommonJS-like environments where a proper `window`
		// is present, execute the factory and get jQuery.
		// For environments that do not have a `window` with a `document`
		// (such as Node.js), expose a factory as module.exports.
		// This accentuates the need for the creation of a real `window`.
		// e.g. var jQuery = require("jquery")(window);
		// See ticket #14549 for more info.
		module.exports = global.document ?
			factory( global, true ) :
			function( w ) {
				if ( !w.document ) {
					throw new Error( "jQuery requires a window with a document" );
				}
				return factory( w );
			};
	} else {
		factory( global );
	}

// Pass this if window is not defined yet
} )( typeof window !== "undefined" ? window : this, function( window, noGlobal ) {

// Edge <= 12 - 13+, Firefox <=18 - 45+, IE 10 - 11, Safari 5.1 - 9+, iOS 6 - 9.1
// throw exceptions when non-strict code (e.g., ASP.NET 4.5) accesses strict mode
// arguments.callee.caller (trac-13335). But as of jQuery 3.0 (2016), strict mode should be common
// enough that all such attempts are guarded in a try block.
"use strict";

var arr = [];

var getProto = Object.getPrototypeOf;

var slice = arr.slice;

var flat = arr.flat ? function( array ) {
	return arr.flat.call( array );
} : function( array ) {
	return arr.concat.apply( [], array );
};


var push = arr.push;

var indexOf = arr.indexOf;

var class2type = {};

var toString = class2type.toString;

var hasOwn = class2type.hasOwnProperty;

var fnToString = hasOwn.toString;

var ObjectFunctionString = fnToString.call( Object );

var support = {};

var isFunction = function isFunction( obj ) {

		// Support: Chrome <=57, Firefox <=52
		// In some browsers, typeof returns "function" for HTML <object> elements
		// (i.e., `typeof document.createElement( "object" ) === "function"`).
		// We don't want to classify *any* DOM node as a function.
		// Support: QtWeb <=3.8.5, WebKit <=534.34, wkhtmltopdf tool <=0.12.5
		// Plus for old WebKit, typeof returns "function" for HTML collections
		// (e.g., `typeof document.getElementsByTagName("div") === "function"`). (gh-4756)
		return typeof obj === "function" && typeof obj.nodeType !== "number" &&
			typeof obj.item !== "function";
	};


var isWindow = function isWindow( obj ) {
		return obj != null && obj === obj.window;
	};


var document = window.document;



	var preservedScriptAttributes = {
		type: true,
		src: true,
		nonce: true,
		noModule: true
	};

	function DOMEval( code, node, doc ) {
		doc = doc || document;

		var i, val,
			script = doc.createElement( "script" );

		script.text = code;
		if ( node ) {
			for ( i in preservedScriptAttributes ) {

				// Support: Firefox 64+, Edge 18+
				// Some browsers don't support the "nonce" property on scripts.
				// On the other hand, just using `getAttribute` is not enough as
				// the `nonce` attribute is reset to an empty string whenever it
				// becomes browsing-context connected.
				// See https://github.com/whatwg/html/issues/2369
				// See https://html.spec.whatwg.org/#nonce-attributes
				// The `node.getAttribute` check was added for the sake of
				// `jQuery.globalEval` so that it can fake a nonce-containing node
				// via an object.
				val = node[ i ] || node.getAttribute && node.getAttribute( i );
				if ( val ) {
					script.setAttribute( i, val );
				}
			}
		}
		doc.head.appendChild( script ).parentNode.removeChild( script );
	}


function toType( obj ) {
	if ( obj == null ) {
		return obj + "";
	}

	// Support: Android <=2.3 only (functionish RegExp)
	return typeof obj === "object" || typeof obj === "function" ?
		class2type[ toString.call( obj ) ] || "object" :
		typeof obj;
}
/* global Symbol */
// Defining this global in .eslintrc.json would create a danger of using the global
// unguarded in another place, it seems safer to define global only for this module



var
	version = "3.6.0",

	// Define a local copy of jQuery
	jQuery = function( selector, context ) {

		// The jQuery object is actually just the init constructor 'enhanced'
		// Need init if jQuery is called (just allow error to be thrown if not included)
		return new jQuery.fn.init( selector, context );
	};

jQuery.fn = jQuery.prototype = {

	// The current version of jQuery being used
	jquery: version,

	constructor: jQuery,

	// The default length of a jQuery object is 0
	length: 0,

	toArray: function() {
		return slice.call( this );
	},

	// Get the Nth element in the matched element set OR
	// Get the whole matched element set as a clean array
	get: function( num ) {

		// Return all the elements in a clean array
		if ( num == null ) {
			return slice.call( this );
		}

		// Return just the one element from the set
		return num < 0 ? this[ num + this.length ] : this[ num ];
	},

	// Take an array of elements and push it onto the stack
	// (returning the new matched element set)
	pushStack: function( elems ) {

		// Build a new jQuery matched element set
		var ret = jQuery.merge( this.constructor(), elems );

		// Add the old object onto the stack (as a reference)
		ret.prevObject = this;

		// Return the newly-formed element set
		return ret;
	},

	// Execute a callback for every element in the matched set.
	each: function( callback ) {
		return jQuery.each( this, callback );
	},

	map: function( callback ) {
		return this.pushStack( jQuery.map( this, function( elem, i ) {
			return callback.call( elem, i, elem );
		} ) );
	},

	slice: function() {
		return this.pushStack( slice.apply( this, arguments ) );
	},

	first: function() {
		return this.eq( 0 );
	},

	last: function() {
		return this.eq( -1 );
	},

	even: function() {
		return this.pushStack( jQuery.grep( this, function( _elem, i ) {
			return ( i + 1 ) % 2;
		} ) );
	},

	odd: function() {
		return this.pushStack( jQuery.grep( this, function( _elem, i ) {
			return i % 2;
		} ) );
	},

	eq: function( i ) {
		var len = this.length,
			j = +i + ( i < 0 ? len : 0 );
		return this.pushStack( j >= 0 && j < len ? [ this[ j ] ] : [] );
	},

	end: function() {
		return this.prevObject || this.constructor();
	},

	// For internal use only.
	// Behaves like an Array's method, not like a jQuery method.
	push: push,
	sort: arr.sort,
	splice: arr.splice
};

jQuery.extend = jQuery.fn.extend = function() {
	var options, name, src, copy, copyIsArray, clone,
		target = arguments[ 0 ] || {},
		i = 1,
		length = arguments.length,
		deep = false;

	// Handle a deep copy situation
	if ( typeof target === "boolean" ) {
		deep = target;

		// Skip the boolean and the target
		target = arguments[ i ] || {};
		i++;
	}

	// Handle case when target is a string or something (possible in deep copy)
	if ( typeof target !== "object" && !isFunction( target ) ) {
		target = {};
	}

	// Extend jQuery itself if only one argument is passed
	if ( i === length ) {
		target = this;
		i--;
	}

	for ( ; i < length; i++ ) {

		// Only deal with non-null/undefined values
		if ( ( options = arguments[ i ] ) != null ) {

			// Extend the base object
			for ( name in options ) {
				copy = options[ name ];

				// Prevent Object.prototype pollution
				// Prevent never-ending loop
				if ( name === "__proto__" || target === copy ) {
					continue;
				}

				// Recurse if we're merging plain objects or arrays
				if ( deep && copy && ( jQuery.isPlainObject( copy ) ||
					( copyIsArray = Array.isArray( copy ) ) ) ) {
					src = target[ name ];

					// Ensure proper type for the source value
					if ( copyIsArray && !Array.isArray( src ) ) {
						clone = [];
					} else if ( !copyIsArray && !jQuery.isPlainObject( src ) ) {
						clone = {};
					} else {
						clone = src;
					}
					copyIsArray = false;

					// Never move original objects, clone them
					target[ name ] = jQuery.extend( deep, clone, copy );

				// Don't bring in undefined values
				} else if ( copy !== undefined ) {
					target[ name ] = copy;
				}
			}
		}
	}

	// Return the modified object
	return target;
};

jQuery.extend( {

	// Unique for each copy of jQuery on the page
	expando: "jQuery" + ( version + Math.random() ).replace( /\D/g, "" ),

	// Assume jQuery is ready without the ready module
	isReady: true,

	error: function( msg ) {
		throw new Error( msg );
	},

	noop: function() {},

	isPlainObject: function( obj ) {
		var proto, Ctor;

		// Detect obvious negatives
		// Use toString instead of jQuery.type to catch host objects
		if ( !obj || toString.call( obj ) !== "[object Object]" ) {
			return false;
		}

		proto = getProto( obj );

		// Objects with no prototype (e.g., `Object.create( null )`) are plain
		if ( !proto ) {
			return true;
		}

		// Objects with prototype are plain iff they were constructed by a global Object function
		Ctor = hasOwn.call( proto, "constructor" ) && proto.constructor;
		return typeof Ctor === "function" && fnToString.call( Ctor ) === ObjectFunctionString;
	},

	isEmptyObject: function( obj ) {
		var name;

		for ( name in obj ) {
			return false;
		}
		return true;
	},

	// Evaluates a script in a provided context; falls back to the global one
	// if not specified.
	globalEval: function( code, options, doc ) {
		DOMEval( code, { nonce: options && options.nonce }, doc );
	},

	each: function( obj, callback ) {
		var length, i = 0;

		if ( isArrayLike( obj ) ) {
			length = obj.length;
			for ( ; i < length; i++ ) {
				if ( callback.call( obj[ i ], i, obj[ i ] ) === false ) {
					break;
				}
			}
		} else {
			for ( i in obj ) {
				if ( callback.call( obj[ i ], i, obj[ i ] ) === false ) {
					break;
				}
			}
		}

		return obj;
	},

	// results is for internal usage only
	makeArray: function( arr, results ) {
		var ret = results || [];

		if ( arr != null ) {
			if ( isArrayLike( Object( arr ) ) ) {
				jQuery.merge( ret,
					typeof arr === "string" ?
						[ arr ] : arr
				);
			} else {
				push.call( ret, arr );
			}
		}

		return ret;
	},

	inArray: function( elem, arr, i ) {
		return arr == null ? -1 : indexOf.call( arr, elem, i );
	},

	// Support: Android <=4.0 only, PhantomJS 1 only
	// push.apply(_, arraylike) throws on ancient WebKit
	merge: function( first, second ) {
		var len = +second.length,
			j = 0,
			i = first.length;

		for ( ; j < len; j++ ) {
			first[ i++ ] = second[ j ];
		}

		first.length = i;

		return first;
	},

	grep: function( elems, callback, invert ) {
		var callbackInverse,
			matches = [],
			i = 0,
			length = elems.length,
			callbackExpect = !invert;

		// Go through the array, only saving the items
		// that pass the validator function
		for ( ; i < length; i++ ) {
			callbackInverse = !callback( elems[ i ], i );
			if ( callbackInverse !== callbackExpect ) {
				matches.push( elems[ i ] );
			}
		}

		return matches;
	},

	// arg is for internal usage only
	map: function( elems, callback, arg ) {
		var length, value,
			i = 0,
			ret = [];

		// Go through the array, translating each of the items to their new values
		if ( isArrayLike( elems ) ) {
			length = elems.length;
			for ( ; i < length; i++ ) {
				value = callback( elems[ i ], i, arg );

				if ( value != null ) {
					ret.push( value );
				}
			}

		// Go through every key on the object,
		} else {
			for ( i in elems ) {
				value = callback( elems[ i ], i, arg );

				if ( value != null ) {
					ret.push( value );
				}
			}
		}

		// Flatten any nested arrays
		return flat( ret );
	},

	// A global GUID counter for objects
	guid: 1,

	// jQuery.support is not used in Core but other projects attach their
	// properties to it so it needs to exist.
	support: support
} );

if ( typeof Symbol === "function" ) {
	jQuery.fn[ Symbol.iterator ] = arr[ Symbol.iterator ];
}

// Populate the class2type map
jQuery.each( "Boolean Number String Function Array Date RegExp Object Error Symbol".split( " " ),
	function( _i, name ) {
		class2type[ "[object " + name + "]" ] = name.toLowerCase();
	} );

function isArrayLike( obj ) {

	// Support: real iOS 8.2 only (not reproducible in simulator)
	// `in` check used to prevent JIT error (gh-2145)
	// hasOwn isn't used here due to false negatives
	// regarding Nodelist length in IE
	var length = !!obj && "length" in obj && obj.length,
		type = toType( obj );

	if ( isFunction( obj ) || isWindow( obj ) ) {
		return false;
	}

	return type === "array" || length === 0 ||
		typeof length === "number" && length > 0 && ( length - 1 ) in obj;
}
var Sizzle =
/*!
 * Sizzle CSS Selector Engine v2.3.6
 * https://sizzlejs.com/
 *
 * Copyright JS Foundation and other contributors
 * Released under the MIT license
 * https://js.foundation/
 *
 * Date: 2021-02-16
 */
( function( window ) {
var i,
	support,
	Expr,
	getText,
	isXML,
	tokenize,
	compile,
	select,
	outermostContext,
	sortInput,
	hasDuplicate,

	// Local document vars
	setDocument,
	document,
	docElem,
	documentIsHTML,
	rbuggyQSA,
	rbuggyMatches,
	matches,
	contains,

	// Instance-specific data
	expando = "sizzle" + 1 * new Date(),
	preferredDoc = window.document,
	dirruns = 0,
	done = 0,
	classCache = createCache(),
	tokenCache = createCache(),
	compilerCache = createCache(),
	nonnativeSelectorCache = createCache(),
	sortOrder = function( a, b ) {
		if ( a === b ) {
			hasDuplicate = true;
		}
		return 0;
	},

	// Instance methods
	hasOwn = ( {} ).hasOwnProperty,
	arr = [],
	pop = arr.pop,
	pushNative = arr.push,
	push = arr.push,
	slice = arr.slice,

	// Use a stripped-down indexOf as it's faster than native
	// https://jsperf.com/thor-indexof-vs-for/5
	indexOf = function( list, elem ) {
		var i = 0,
			len = list.length;
		for ( ; i < len; i++ ) {
			if ( list[ i ] === elem ) {
				return i;
			}
		}
		return -1;
	},

	booleans = "checked|selected|async|autofocus|autoplay|controls|defer|disabled|hidden|" +
		"ismap|loop|multiple|open|readonly|required|scoped",

	// Regular expressions

	// http://www.w3.org/TR/css3-selectors/#whitespace
	whitespace = "[\\x20\\t\\r\\n\\f]",

	// https://www.w3.org/TR/css-syntax-3/#ident-token-diagram
	identifier = "(?:\\\\[\\da-fA-F]{1,6}" + whitespace +
		"?|\\\\[^\\r\\n\\f]|[\\w-]|[^\0-\\x7f])+",

	// Attribute selectors: http://www.w3.org/TR/selectors/#attribute-selectors
	attributes = "\\[" + whitespace + "*(" + identifier + ")(?:" + whitespace +

		// Operator (capture 2)
		"*([*^$|!~]?=)" + whitespace +

		// "Attribute values must be CSS identifiers [capture 5]
		// or strings [capture 3 or capture 4]"
		"*(?:'((?:\\\\.|[^\\\\'])*)'|\"((?:\\\\.|[^\\\\\"])*)\"|(" + identifier + "))|)" +
		whitespace + "*\\]",

	pseudos = ":(" + identifier + ")(?:\\((" +

		// To reduce the number of selectors needing tokenize in the preFilter, prefer arguments:
		// 1. quoted (capture 3; capture 4 or capture 5)
		"('((?:\\\\.|[^\\\\'])*)'|\"((?:\\\\.|[^\\\\\"])*)\")|" +

		// 2. simple (capture 6)
		"((?:\\\\.|[^\\\\()[\\]]|" + attributes + ")*)|" +

		// 3. anything else (capture 2)
		".*" +
		")\\)|)",

	// Leading and non-escaped trailing whitespace, capturing some non-whitespace characters preceding the latter
	rwhitespace = new RegExp( whitespace + "+", "g" ),
	rtrim = new RegExp( "^" + whitespace + "+|((?:^|[^\\\\])(?:\\\\.)*)" +
		whitespace + "+$", "g" ),

	rcomma = new RegExp( "^" + whitespace + "*," + whitespace + "*" ),
	rcombinators = new RegExp( "^" + whitespace + "*([>+~]|" + whitespace + ")" + whitespace +
		"*" ),
	rdescend = new RegExp( whitespace + "|>" ),

	rpseudo = new RegExp( pseudos ),
	ridentifier = new RegExp( "^" + identifier + "$" ),

	matchExpr = {
		"ID": new RegExp( "^#(" + identifier + ")" ),
		"CLASS": new RegExp( "^\\.(" + identifier + ")" ),
		"TAG": new RegExp( "^(" + identifier + "|[*])" ),
		"ATTR": new RegExp( "^" + attributes ),
		"PSEUDO": new RegExp( "^" + pseudos ),
		"CHILD": new RegExp( "^:(only|first|last|nth|nth-last)-(child|of-type)(?:\\(" +
			whitespace + "*(even|odd|(([+-]|)(\\d*)n|)" + whitespace + "*(?:([+-]|)" +
			whitespace + "*(\\d+)|))" + whitespace + "*\\)|)", "i" ),
		"bool": new RegExp( "^(?:" + booleans + ")$", "i" ),

		// For use in libraries implementing .is()
		// We use this for POS matching in `select`
		"needsContext": new RegExp( "^" + whitespace +
			"*[>+~]|:(even|odd|eq|gt|lt|nth|first|last)(?:\\(" + whitespace +
			"*((?:-\\d)?\\d*)" + whitespace + "*\\)|)(?=[^-]|$)", "i" )
	},

	rhtml = /HTML$/i,
	rinputs = /^(?:input|select|textarea|button)$/i,
	rheader = /^h\d$/i,

	rnative = /^[^{]+\{\s*\[native \w/,

	// Easily-parseable/retrievable ID or TAG or CLASS selectors
	rquickExpr = /^(?:#([\w-]+)|(\w+)|\.([\w-]+))$/,

	rsibling = /[+~]/,

	// CSS escapes
	// http://www.w3.org/TR/CSS21/syndata.html#escaped-characters
	runescape = new RegExp( "\\\\[\\da-fA-F]{1,6}" + whitespace + "?|\\\\([^\\r\\n\\f])", "g" ),
	funescape = function( escape, nonHex ) {
		var high = "0x" + escape.slice( 1 ) - 0x10000;

		return nonHex ?

			// Strip the backslash prefix from a non-hex escape sequence
			nonHex :

			// Replace a hexadecimal escape sequence with the encoded Unicode code point
			// Support: IE <=11+
			// For values outside the Basic Multilingual Plane (BMP), manually construct a
			// surrogate pair
			high < 0 ?
				String.fromCharCode( high + 0x10000 ) :
				String.fromCharCode( high >> 10 | 0xD800, high & 0x3FF | 0xDC00 );
	},

	// CSS string/identifier serialization
	// https://drafts.csswg.org/cssom/#common-serializing-idioms
	rcssescape = /([\0-\x1f\x7f]|^-?\d)|^-$|[^\0-\x1f\x7f-\uFFFF\w-]/g,
	fcssescape = function( ch, asCodePoint ) {
		if ( asCodePoint ) {

			// U+0000 NULL becomes U+FFFD REPLACEMENT CHARACTER
			if ( ch === "\0" ) {
				return "\uFFFD";
			}

			// Control characters and (dependent upon position) numbers get escaped as code points
			return ch.slice( 0, -1 ) + "\\" +
				ch.charCodeAt( ch.length - 1 ).toString( 16 ) + " ";
		}

		// Other potentially-special ASCII characters get backslash-escaped
		return "\\" + ch;
	},

	// Used for iframes
	// See setDocument()
	// Removing the function wrapper causes a "Permission Denied"
	// error in IE
	unloadHandler = function() {
		setDocument();
	},

	inDisabledFieldset = addCombinator(
		function( elem ) {
			return elem.disabled === true && elem.nodeName.toLowerCase() === "fieldset";
		},
		{ dir: "parentNode", next: "legend" }
	);

// Optimize for push.apply( _, NodeList )
try {
	push.apply(
		( arr = slice.call( preferredDoc.childNodes ) ),
		preferredDoc.childNodes
	);

	// Support: Android<4.0
	// Detect silently failing push.apply
	// eslint-disable-next-line no-unused-expressions
	arr[ preferredDoc.childNodes.length ].nodeType;
} catch ( e ) {
	push = { apply: arr.length ?

		// Leverage slice if possible
		function( target, els ) {
			pushNative.apply( target, slice.call( els ) );
		} :

		// Support: IE<9
		// Otherwise append directly
		function( target, els ) {
			var j = target.length,
				i = 0;

			// Can't trust NodeList.length
			while ( ( target[ j++ ] = els[ i++ ] ) ) {}
			target.length = j - 1;
		}
	};
}

function Sizzle( selector, context, results, seed ) {
	var m, i, elem, nid, match, groups, newSelector,
		newContext = context && context.ownerDocument,

		// nodeType defaults to 9, since context defaults to document
		nodeType = context ? context.nodeType : 9;

	results = results || [];

	// Return early from calls with invalid selector or context
	if ( typeof selector !== "string" || !selector ||
		nodeType !== 1 && nodeType !== 9 && nodeType !== 11 ) {

		return results;
	}

	// Try to shortcut find operations (as opposed to filters) in HTML documents
	if ( !seed ) {
		setDocument( context );
		context = context || document;

		if ( documentIsHTML ) {

			// If the selector is sufficiently simple, try using a "get*By*" DOM method
			// (excepting DocumentFragment context, where the methods don't exist)
			if ( nodeType !== 11 && ( match = rquickExpr.exec( selector ) ) ) {

				// ID selector
				if ( ( m = match[ 1 ] ) ) {

					// Document context
					if ( nodeType === 9 ) {
						if ( ( elem = context.getElementById( m ) ) ) {

							// Support: IE, Opera, Webkit
							// TODO: identify versions
							// getElementById can match elements by name instead of ID
							if ( elem.id === m ) {
								results.push( elem );
								return results;
							}
						} else {
							return results;
						}

					// Element context
					} else {

						// Support: IE, Opera, Webkit
						// TODO: identify versions
						// getElementById can match elements by name instead of ID
						if ( newContext && ( elem = newContext.getElementById( m ) ) &&
							contains( context, elem ) &&
							elem.id === m ) {

							results.push( elem );
							return results;
						}
					}

				// Type selector
				} else if ( match[ 2 ] ) {
					push.apply( results, context.getElementsByTagName( selector ) );
					return results;

				// Class selector
				} else if ( ( m = match[ 3 ] ) && support.getElementsByClassName &&
					context.getElementsByClassName ) {

					push.apply( results, context.getElementsByClassName( m ) );
					return results;
				}
			}

			// Take advantage of querySelectorAll
			if ( support.qsa &&
				!nonnativeSelectorCache[ selector + " " ] &&
				( !rbuggyQSA || !rbuggyQSA.test( selector ) ) &&

				// Support: IE 8 only
				// Exclude object elements
				( nodeType !== 1 || context.nodeName.toLowerCase() !== "object" ) ) {

				newSelector = selector;
				newContext = context;

				// qSA considers elements outside a scoping root when evaluating child or
				// descendant combinators, which is not what we want.
				// In such cases, we work around the behavior by prefixing every selector in the
				// list with an ID selector referencing the scope context.
				// The technique has to be used as well when a leading combinator is used
				// as such selectors are not recognized by querySelectorAll.
				// Thanks to Andrew Dupont for this technique.
				if ( nodeType === 1 &&
					( rdescend.test( selector ) || rcombinators.test( selector ) ) ) {

					// Expand context for sibling selectors
					newContext = rsibling.test( selector ) && testContext( context.parentNode ) ||
						context;

					// We can use :scope instead of the ID hack if the browser
					// supports it & if we're not changing the context.
					if ( newContext !== context || !support.scope ) {

						// Capture the context ID, setting it first if necessary
						if ( ( nid = context.getAttribute( "id" ) ) ) {
							nid = nid.replace( rcssescape, fcssescape );
						} else {
							context.setAttribute( "id", ( nid = expando ) );
						}
					}

					// Prefix every selector in the list
					groups = tokenize( selector );
					i = groups.length;
					while ( i-- ) {
						groups[ i ] = ( nid ? "#" + nid : ":scope" ) + " " +
							toSelector( groups[ i ] );
					}
					newSelector = groups.join( "," );
				}

				try {
					push.apply( results,
						newContext.querySelectorAll( newSelector )
					);
					return results;
				} catch ( qsaError ) {
					nonnativeSelectorCache( selector, true );
				} finally {
					if ( nid === expando ) {
						context.removeAttribute( "id" );
					}
				}
			}
		}
	}

	// All others
	return select( selector.replace( rtrim, "$1" ), context, results, seed );
}

/**
 * Create key-value caches of limited size
 * @returns {function(string, object)} Returns the Object data after storing it on itself with
 *	property name the (space-suffixed) string and (if the cache is larger than Expr.cacheLength)
 *	deleting the oldest entry
 */
function createCache() {
	var keys = [];

	function cache( key, value ) {

		// Use (key + " ") to avoid collision with native prototype properties (see Issue #157)
		if ( keys.push( key + " " ) > Expr.cacheLength ) {

			// Only keep the most recent entries
			delete cache[ keys.shift() ];
		}
		return ( cache[ key + " " ] = value );
	}
	return cache;
}

/**
 * Mark a function for special use by Sizzle
 * @param {Function} fn The function to mark
 */
function markFunction( fn ) {
	fn[ expando ] = true;
	return fn;
}

/**
 * Support testing using an element
 * @param {Function} fn Passed the created element and returns a boolean result
 */
function assert( fn ) {
	var el = document.createElement( "fieldset" );

	try {
		return !!fn( el );
	} catch ( e ) {
		return false;
	} finally {

		// Remove from its parent by default
		if ( el.parentNode ) {
			el.parentNode.removeChild( el );
		}

		// release memory in IE
		el = null;
	}
}

/**
 * Adds the same handler for all of the specified attrs
 * @param {String} attrs Pipe-separated list of attributes
 * @param {Function} handler The method that will be applied
 */
function addHandle( attrs, handler ) {
	var arr = attrs.split( "|" ),
		i = arr.length;

	while ( i-- ) {
		Expr.attrHandle[ arr[ i ] ] = handler;
	}
}

/**
 * Checks document order of two siblings
 * @param {Element} a
 * @param {Element} b
 * @returns {Number} Returns less than 0 if a precedes b, greater than 0 if a follows b
 */
function siblingCheck( a, b ) {
	var cur = b && a,
		diff = cur && a.nodeType === 1 && b.nodeType === 1 &&
			a.sourceIndex - b.sourceIndex;

	// Use IE sourceIndex if available on both nodes
	if ( diff ) {
		return diff;
	}

	// Check if b follows a
	if ( cur ) {
		while ( ( cur = cur.nextSibling ) ) {
			if ( cur === b ) {
				return -1;
			}
		}
	}

	return a ? 1 : -1;
}

/**
 * Returns a function to use in pseudos for input types
 * @param {String} type
 */
function createInputPseudo( type ) {
	return function( elem ) {
		var name = elem.nodeName.toLowerCase();
		return name === "input" && elem.type === type;
	};
}

/**
 * Returns a function to use in pseudos for buttons
 * @param {String} type
 */
function createButtonPseudo( type ) {
	return function( elem ) {
		var name = elem.nodeName.toLowerCase();
		return ( name === "input" || name === "button" ) && elem.type === type;
	};
}

/**
 * Returns a function to use in pseudos for :enabled/:disabled
 * @param {Boolean} disabled true for :disabled; false for :enabled
 */
function createDisabledPseudo( disabled ) {

	// Known :disabled false positives: fieldset[disabled] > legend:nth-of-type(n+2) :can-disable
	return function( elem ) {

		// Only certain elements can match :enabled or :disabled
		// https://html.spec.whatwg.org/multipage/scripting.html#selector-enabled
		// https://html.spec.whatwg.org/multipage/scripting.html#selector-disabled
		if ( "form" in elem ) {

			// Check for inherited disabledness on relevant non-disabled elements:
			// * listed form-associated elements in a disabled fieldset
			//   https://html.spec.whatwg.org/multipage/forms.html#category-listed
			//   https://html.spec.whatwg.org/multipage/forms.html#concept-fe-disabled
			// * option elements in a disabled optgroup
			//   https://html.spec.whatwg.org/multipage/forms.html#concept-option-disabled
			// All such elements have a "form" property.
			if ( elem.parentNode && elem.disabled === false ) {

				// Option elements defer to a parent optgroup if present
				if ( "label" in elem ) {
					if ( "label" in elem.parentNode ) {
						return elem.parentNode.disabled === disabled;
					} else {
						return elem.disabled === disabled;
					}
				}

				// Support: IE 6 - 11
				// Use the isDisabled shortcut property to check for disabled fieldset ancestors
				return elem.isDisabled === disabled ||

					// Where there is no isDisabled, check manually
					/* jshint -W018 */
					elem.isDisabled !== !disabled &&
					inDisabledFieldset( elem ) === disabled;
			}

			return elem.disabled === disabled;

		// Try to winnow out elements that can't be disabled before trusting the disabled property.
		// Some victims get caught in our net (label, legend, menu, track), but it shouldn't
		// even exist on them, let alone have a boolean value.
		} else if ( "label" in elem ) {
			return elem.disabled === disabled;
		}

		// Remaining elements are neither :enabled nor :disabled
		return false;
	};
}

/**
 * Returns a function to use in pseudos for positionals
 * @param {Function} fn
 */
function createPositionalPseudo( fn ) {
	return markFunction( function( argument ) {
		argument = +argument;
		return markFunction( function( seed, matches ) {
			var j,
				matchIndexes = fn( [], seed.length, argument ),
				i = matchIndexes.length;

			// Match elements found at the specified indexes
			while ( i-- ) {
				if ( seed[ ( j = matchIndexes[ i ] ) ] ) {
					seed[ j ] = !( matches[ j ] = seed[ j ] );
				}
			}
		} );
	} );
}

/**
 * Checks a node for validity as a Sizzle context
 * @param {Element|Object=} context
 * @returns {Element|Object|Boolean} The input node if acceptable, otherwise a falsy value
 */
function testContext( context ) {
	return context && typeof context.getElementsByTagName !== "undefined" && context;
}

// Expose support vars for convenience
support = Sizzle.support = {};

/**
 * Detects XML nodes
 * @param {Element|Object} elem An element or a document
 * @returns {Boolean} True iff elem is a non-HTML XML node
 */
isXML = Sizzle.isXML = function( elem ) {
	var namespace = elem && elem.namespaceURI,
		docElem = elem && ( elem.ownerDocument || elem ).documentElement;

	// Support: IE <=8
	// Assume HTML when documentElement doesn't yet exist, such as inside loading iframes
	// https://bugs.jquery.com/ticket/4833
	return !rhtml.test( namespace || docElem && docElem.nodeName || "HTML" );
};

/**
 * Sets document-related variables once based on the current document
 * @param {Element|Object} [doc] An element or document object to use to set the document
 * @returns {Object} Returns the current document
 */
setDocument = Sizzle.setDocument = function( node ) {
	var hasCompare, subWindow,
		doc = node ? node.ownerDocument || node : preferredDoc;

	// Return early if doc is invalid or already selected
	// Support: IE 11+, Edge 17 - 18+
	// IE/Edge sometimes throw a "Permission denied" error when strict-comparing
	// two documents; shallow comparisons work.
	// eslint-disable-next-line eqeqeq
	if ( doc == document || doc.nodeType !== 9 || !doc.documentElement ) {
		return document;
	}

	// Update global variables
	document = doc;
	docElem = document.documentElement;
	documentIsHTML = !isXML( document );

	// Support: IE 9 - 11+, Edge 12 - 18+
	// Accessing iframe documents after unload throws "permission denied" errors (jQuery #13936)
	// Support: IE 11+, Edge 17 - 18+
	// IE/Edge sometimes throw a "Permission denied" error when strict-comparing
	// two documents; shallow comparisons work.
	// eslint-disable-next-line eqeqeq
	if ( preferredDoc != document &&
		( subWindow = document.defaultView ) && subWindow.top !== subWindow ) {

		// Support: IE 11, Edge
		if ( subWindow.addEventListener ) {
			subWindow.addEventListener( "unload", unloadHandler, false );

		// Support: IE 9 - 10 only
		} else if ( subWindow.attachEvent ) {
			subWindow.attachEvent( "onunload", unloadHandler );
		}
	}

	// Support: IE 8 - 11+, Edge 12 - 18+, Chrome <=16 - 25 only, Firefox <=3.6 - 31 only,
	// Safari 4 - 5 only, Opera <=11.6 - 12.x only
	// IE/Edge & older browsers don't support the :scope pseudo-class.
	// Support: Safari 6.0 only
	// Safari 6.0 supports :scope but it's an alias of :root there.
	support.scope = assert( function( el ) {
		docElem.appendChild( el ).appendChild( document.createElement( "div" ) );
		return typeof el.querySelectorAll !== "undefined" &&
			!el.querySelectorAll( ":scope fieldset div" ).length;
	} );

	/* Attributes
	---------------------------------------------------------------------- */

	// Support: IE<8
	// Verify that getAttribute really returns attributes and not properties
	// (excepting IE8 booleans)
	support.attributes = assert( function( el ) {
		el.className = "i";
		return !el.getAttribute( "className" );
	} );

	/* getElement(s)By*
	---------------------------------------------------------------------- */

	// Check if getElementsByTagName("*") returns only elements
	support.getElementsByTagName = assert( function( el ) {
		el.appendChild( document.createComment( "" ) );
		return !el.getElementsByTagName( "*" ).length;
	} );

	// Support: IE<9
	support.getElementsByClassName = rnative.test( document.getElementsByClassName );

	// Support: IE<10
	// Check if getElementById returns elements by name
	// The broken getElementById methods don't pick up programmatically-set names,
	// so use a roundabout getElementsByName test
	support.getById = assert( function( el ) {
		docElem.appendChild( el ).id = expando;
		return !document.getElementsByName || !document.getElementsByName( expando ).length;
	} );

	// ID filter and find
	if ( support.getById ) {
		Expr.filter[ "ID" ] = function( id ) {
			var attrId = id.replace( runescape, funescape );
			return function( elem ) {
				return elem.getAttribute( "id" ) === attrId;
			};
		};
		Expr.find[ "ID" ] = function( id, context ) {
			if ( typeof context.getElementById !== "undefined" && documentIsHTML ) {
				var elem = context.getElementById( id );
				return elem ? [ elem ] : [];
			}
		};
	} else {
		Expr.filter[ "ID" ] =  function( id ) {
			var attrId = id.replace( runescape, funescape );
			return function( elem ) {
				var node = typeof elem.getAttributeNode !== "undefined" &&
					elem.getAttributeNode( "id" );
				return node && node.value === attrId;
			};
		};

		// Support: IE 6 - 7 only
		// getElementById is not reliable as a find shortcut
		Expr.find[ "ID" ] = function( id, context ) {
			if ( typeof context.getElementById !== "undefined" && documentIsHTML ) {
				var node, i, elems,
					elem = context.getElementById( id );

				if ( elem ) {

					// Verify the id attribute
					node = elem.getAttributeNode( "id" );
					if ( node && node.value === id ) {
						return [ elem ];
					}

					// Fall back on getElementsByName
					elems = context.getElementsByName( id );
					i = 0;
					while ( ( elem = elems[ i++ ] ) ) {
						node = elem.getAttributeNode( "id" );
						if ( node && node.value === id ) {
							return [ elem ];
						}
					}
				}

				return [];
			}
		};
	}

	// Tag
	Expr.find[ "TAG" ] = support.getElementsByTagName ?
		function( tag, context ) {
			if ( typeof context.getElementsByTagName !== "undefined" ) {
				return context.getElementsByTagName( tag );

			// DocumentFragment nodes don't have gEBTN
			} else if ( support.qsa ) {
				return context.querySelectorAll( tag );
			}
		} :

		function( tag, context ) {
			var elem,
				tmp = [],
				i = 0,

				// By happy coincidence, a (broken) gEBTN appears on DocumentFragment nodes too
				results = context.getElementsByTagName( tag );

			// Filter out possible comments
			if ( tag === "*" ) {
				while ( ( elem = results[ i++ ] ) ) {
					if ( elem.nodeType === 1 ) {
						tmp.push( elem );
					}
				}

				return tmp;
			}
			return results;
		};

	// Class
	Expr.find[ "CLASS" ] = support.getElementsByClassName && function( className, context ) {
		if ( typeof context.getElementsByClassName !== "undefined" && documentIsHTML ) {
			return context.getElementsByClassName( className );
		}
	};

	/* QSA/matchesSelector
	---------------------------------------------------------------------- */

	// QSA and matchesSelector support

	// matchesSelector(:active) reports false when true (IE9/Opera 11.5)
	rbuggyMatches = [];

	// qSa(:focus) reports false when true (Chrome 21)
	// We allow this because of a bug in IE8/9 that throws an error
	// whenever `document.activeElement` is accessed on an iframe
	// So, we allow :focus to pass through QSA all the time to avoid the IE error
	// See https://bugs.jquery.com/ticket/13378
	rbuggyQSA = [];

	if ( ( support.qsa = rnative.test( document.querySelectorAll ) ) ) {

		// Build QSA regex
		// Regex strategy adopted from Diego Perini
		assert( function( el ) {

			var input;

			// Select is set to empty string on purpose
			// This is to test IE's treatment of not explicitly
			// setting a boolean content attribute,
			// since its presence should be enough
			// https://bugs.jquery.com/ticket/12359
			docElem.appendChild( el ).innerHTML = "<a id='" + expando + "'></a>" +
				"<select id='" + expando + "-\r\\' msallowcapture=''>" +
				"<option selected=''></option></select>";

			// Support: IE8, Opera 11-12.16
			// Nothing should be selected when empty strings follow ^= or $= or *=
			// The test attribute must be unknown in Opera but "safe" for WinRT
			// https://msdn.microsoft.com/en-us/library/ie/hh465388.aspx#attribute_section
			if ( el.querySelectorAll( "[msallowcapture^='']" ).length ) {
				rbuggyQSA.push( "[*^$]=" + whitespace + "*(?:''|\"\")" );
			}

			// Support: IE8
			// Boolean attributes and "value" are not treated correctly
			if ( !el.querySelectorAll( "[selected]" ).length ) {
				rbuggyQSA.push( "\\[" + whitespace + "*(?:value|" + booleans + ")" );
			}

			// Support: Chrome<29, Android<4.4, Safari<7.0+, iOS<7.0+, PhantomJS<1.9.8+
			if ( !el.querySelectorAll( "[id~=" + expando + "-]" ).length ) {
				rbuggyQSA.push( "~=" );
			}

			// Support: IE 11+, Edge 15 - 18+
			// IE 11/Edge don't find elements on a `[name='']` query in some cases.
			// Adding a temporary attribute to the document before the selection works
			// around the issue.
			// Interestingly, IE 10 & older don't seem to have the issue.
			input = document.createElement( "input" );
			input.setAttribute( "name", "" );
			el.appendChild( input );
			if ( !el.querySelectorAll( "[name='']" ).length ) {
				rbuggyQSA.push( "\\[" + whitespace + "*name" + whitespace + "*=" +
					whitespace + "*(?:''|\"\")" );
			}

			// Webkit/Opera - :checked should return selected option elements
			// http://www.w3.org/TR/2011/REC-css3-selectors-20110929/#checked
			// IE8 throws error here and will not see later tests
			if ( !el.querySelectorAll( ":checked" ).length ) {
				rbuggyQSA.push( ":checked" );
			}

			// Support: Safari 8+, iOS 8+
			// https://bugs.webkit.org/show_bug.cgi?id=136851
			// In-page `selector#id sibling-combinator selector` fails
			if ( !el.querySelectorAll( "a#" + expando + "+*" ).length ) {
				rbuggyQSA.push( ".#.+[+~]" );
			}

			// Support: Firefox <=3.6 - 5 only
			// Old Firefox doesn't throw on a badly-escaped identifier.
			el.querySelectorAll( "\\\f" );
			rbuggyQSA.push( "[\\r\\n\\f]" );
		} );

		assert( function( el ) {
			el.innerHTML = "<a href='' disabled='disabled'></a>" +
				"<select disabled='disabled'><option/></select>";

			// Support: Windows 8 Native Apps
			// The type and name attributes are restricted during .innerHTML assignment
			var input = document.createElement( "input" );
			input.setAttribute( "type", "hidden" );
			el.appendChild( input ).setAttribute( "name", "D" );

			// Support: IE8
			// Enforce case-sensitivity of name attribute
			if ( el.querySelectorAll( "[name=d]" ).length ) {
				rbuggyQSA.push( "name" + whitespace + "*[*^$|!~]?=" );
			}

			// FF 3.5 - :enabled/:disabled and hidden elements (hidden elements are still enabled)
			// IE8 throws error here and will not see later tests
			if ( el.querySelectorAll( ":enabled" ).length !== 2 ) {
				rbuggyQSA.push( ":enabled", ":disabled" );
			}

			// Support: IE9-11+
			// IE's :disabled selector does not pick up the children of disabled fieldsets
			docElem.appendChild( el ).disabled = true;
			if ( el.querySelectorAll( ":disabled" ).length !== 2 ) {
				rbuggyQSA.push( ":enabled", ":disabled" );
			}

			// Support: Opera 10 - 11 only
			// Opera 10-11 does not throw on post-comma invalid pseudos
			el.querySelectorAll( "*,:x" );
			rbuggyQSA.push( ",.*:" );
		} );
	}

	if ( ( support.matchesSelector = rnative.test( ( matches = docElem.matches ||
		docElem.webkitMatchesSelector ||
		docElem.mozMatchesSelector ||
		docElem.oMatchesSelector ||
		docElem.msMatchesSelector ) ) ) ) {

		assert( function( el ) {

			// Check to see if it's possible to do matchesSelector
			// on a disconnected node (IE 9)
			support.disconnectedMatch = matches.call( el, "*" );

			// This should fail with an exception
			// Gecko does not error, returns false instead
			matches.call( el, "[s!='']:x" );
			rbuggyMatches.push( "!=", pseudos );
		} );
	}

	rbuggyQSA = rbuggyQSA.length && new RegExp( rbuggyQSA.join( "|" ) );
	rbuggyMatches = rbuggyMatches.length && new RegExp( rbuggyMatches.join( "|" ) );

	/* Contains
	---------------------------------------------------------------------- */
	hasCompare = rnative.test( docElem.compareDocumentPosition );

	// Element contains another
	// Purposefully self-exclusive
	// As in, an element does not contain itself
	contains = hasCompare || rnative.test( docElem.contains ) ?
		function( a, b ) {
			var adown = a.nodeType === 9 ? a.documentElement : a,
				bup = b && b.parentNode;
			return a === bup || !!( bup && bup.nodeType === 1 && (
				adown.contains ?
					adown.contains( bup ) :
					a.compareDocumentPosition && a.compareDocumentPosition( bup ) & 16
			) );
		} :
		function( a, b ) {
			if ( b ) {
				while ( ( b = b.parentNode ) ) {
					if ( b === a ) {
						return true;
					}
				}
			}
			return false;
		};

	/* Sorting
	---------------------------------------------------------------------- */

	// Document order sorting
	sortOrder = hasCompare ?
	function( a, b ) {

		// Flag for duplicate removal
		if ( a === b ) {
			hasDuplicate = true;
			return 0;
		}

		// Sort on method existence if only one input has compareDocumentPosition
		var compare = !a.compareDocumentPosition - !b.compareDocumentPosition;
		if ( compare ) {
			return compare;
		}

		// Calculate position if both inputs belong to the same document
		// Support: IE 11+, Edge 17 - 18+
		// IE/Edge sometimes throw a "Permission denied" error when strict-comparing
		// two documents; shallow comparisons work.
		// eslint-disable-next-line eqeqeq
		compare = ( a.ownerDocument || a ) == ( b.ownerDocument || b ) ?
			a.compareDocumentPosition( b ) :

			// Otherwise we know they are disconnected
			1;

		// Disconnected nodes
		if ( compare & 1 ||
			( !support.sortDetached && b.compareDocumentPosition( a ) === compare ) ) {

			// Choose the first element that is related to our preferred document
			// Support: IE 11+, Edge 17 - 18+
			// IE/Edge sometimes throw a "Permission denied" error when strict-comparing
			// two documents; shallow comparisons work.
			// eslint-disable-next-line eqeqeq
			if ( a == document || a.ownerDocument == preferredDoc &&
				contains( preferredDoc, a ) ) {
				return -1;
			}

			// Support: IE 11+, Edge 17 - 18+
			// IE/Edge sometimes throw a "Permission denied" error when strict-comparing
			// two documents; shallow comparisons work.
			// eslint-disable-next-line eqeqeq
			if ( b == document || b.ownerDocument == preferredDoc &&
				contains( preferredDoc, b ) ) {
				return 1;
			}

			// Maintain original order
			return sortInput ?
				( indexOf( sortInput, a ) - indexOf( sortInput, b ) ) :
				0;
		}

		return compare & 4 ? -1 : 1;
	} :
	function( a, b ) {

		// Exit early if the nodes are identical
		if ( a === b ) {
			hasDuplicate = true;
			return 0;
		}

		var cur,
			i = 0,
			aup = a.parentNode,
			bup = b.parentNode,
			ap = [ a ],
			bp = [ b ];

		// Parentless nodes are either documents or disconnected
		if ( !aup || !bup ) {

			// Support: IE 11+, Edge 17 - 18+
			// IE/Edge sometimes throw a "Permission denied" error when strict-comparing
			// two documents; shallow comparisons work.
			/* eslint-disable eqeqeq */
			return a == document ? -1 :
				b == document ? 1 :
				/* eslint-enable eqeqeq */
				aup ? -1 :
				bup ? 1 :
				sortInput ?
				( indexOf( sortInput, a ) - indexOf( sortInput, b ) ) :
				0;

		// If the nodes are siblings, we can do a quick check
		} else if ( aup === bup ) {
			return siblingCheck( a, b );
		}

		// Otherwise we need full lists of their ancestors for comparison
		cur = a;
		while ( ( cur = cur.parentNode ) ) {
			ap.unshift( cur );
		}
		cur = b;
		while ( ( cur = cur.parentNode ) ) {
			bp.unshift( cur );
		}

		// Walk down the tree looking for a discrepancy
		while ( ap[ i ] === bp[ i ] ) {
			i++;
		}

		return i ?

			// Do a sibling check if the nodes have a common ancestor
			siblingCheck( ap[ i ], bp[ i ] ) :

			// Otherwise nodes in our document sort first
			// Support: IE 11+, Edge 17 - 18+
			// IE/Edge sometimes throw a "Permission denied" error when strict-comparing
			// two documents; shallow comparisons work.
			/* eslint-disable eqeqeq */
			ap[ i ] == preferredDoc ? -1 :
			bp[ i ] == preferredDoc ? 1 :
			/* eslint-enable eqeqeq */
			0;
	};

	return document;
};

Sizzle.matches = function( expr, elements ) {
	return Sizzle( expr, null, null, elements );
};

Sizzle.matchesSelector = function( elem, expr ) {
	setDocument( elem );

	if ( support.matchesSelector && documentIsHTML &&
		!nonnativeSelectorCache[ expr + " " ] &&
		( !rbuggyMatches || !rbuggyMatches.test( expr ) ) &&
		( !rbuggyQSA     || !rbuggyQSA.test( expr ) ) ) {

		try {
			var ret = matches.call( elem, expr );

			// IE 9's matchesSelector returns false on disconnected nodes
			if ( ret || support.disconnectedMatch ||

				// As well, disconnected nodes are said to be in a document
				// fragment in IE 9
				elem.document && elem.document.nodeType !== 11 ) {
				return ret;
			}
		} catch ( e ) {
			nonnativeSelectorCache( expr, true );
		}
	}

	return Sizzle( expr, document, null, [ elem ] ).length > 0;
};

Sizzle.contains = function( context, elem ) {

	// Set document vars if needed
	// Support: IE 11+, Edge 17 - 18+
	// IE/Edge sometimes throw a "Permission denied" error when strict-comparing
	// two documents; shallow comparisons work.
	// eslint-disable-next-line eqeqeq
	if ( ( context.ownerDocument || context ) != document ) {
		setDocument( context );
	}
	return contains( context, elem );
};

Sizzle.attr = function( elem, name ) {

	// Set document vars if needed
	// Support: IE 11+, Edge 17 - 18+
	// IE/Edge sometimes throw a "Permission denied" error when strict-comparing
	// two documents; shallow comparisons work.
	// eslint-disable-next-line eqeqeq
	if ( ( elem.ownerDocument || elem ) != document ) {
		setDocument( elem );
	}

	var fn = Expr.attrHandle[ name.toLowerCase() ],

		// Don't get fooled by Object.prototype properties (jQuery #13807)
		val = fn && hasOwn.call( Expr.attrHandle, name.toLowerCase() ) ?
			fn( elem, name, !documentIsHTML ) :
			undefined;

	return val !== undefined ?
		val :
		support.attributes || !documentIsHTML ?
			elem.getAttribute( name ) :
			( val = elem.getAttributeNode( name ) ) && val.specified ?
				val.value :
				null;
};

Sizzle.escape = function( sel ) {
	return ( sel + "" ).replace( rcssescape, fcssescape );
};

Sizzle.error = function( msg ) {
	throw new Error( "Syntax error, unrecognized expression: " + msg );
};

/**
 * Document sorting and removing duplicates
 * @param {ArrayLike} results
 */
Sizzle.uniqueSort = function( results ) {
	var elem,
		duplicates = [],
		j = 0,
		i = 0;

	// Unless we *know* we can detect duplicates, assume their presence
	hasDuplicate = !support.detectDuplicates;
	sortInput = !support.sortStable && results.slice( 0 );
	results.sort( sortOrder );

	if ( hasDuplicate ) {
		while ( ( elem = results[ i++ ] ) ) {
			if ( elem === results[ i ] ) {
				j = duplicates.push( i );
			}
		}
		while ( j-- ) {
			results.splice( duplicates[ j ], 1 );
		}
	}

	// Clear input after sorting to release objects
	// See https://github.com/jquery/sizzle/pull/225
	sortInput = null;

	return results;
};

/**
 * Utility function for retrieving the text value of an array of DOM nodes
 * @param {Array|Element} elem
 */
getText = Sizzle.getText = function( elem ) {
	var node,
		ret = "",
		i = 0,
		nodeType = elem.nodeType;

	if ( !nodeType ) {

		// If no nodeType, this is expected to be an array
		while ( ( node = elem[ i++ ] ) ) {

			// Do not traverse comment nodes
			ret += getText( node );
		}
	} else if ( nodeType === 1 || nodeType === 9 || nodeType === 11 ) {

		// Use textContent for elements
		// innerText usage removed for consistency of new lines (jQuery #11153)
		if ( typeof elem.textContent === "string" ) {
			return elem.textContent;
		} else {

			// Traverse its children
			for ( elem = elem.firstChild; elem; elem = elem.nextSibling ) {
				ret += getText( elem );
			}
		}
	} else if ( nodeType === 3 || nodeType === 4 ) {
		return elem.nodeValue;
	}

	// Do not include comment or processing instruction nodes

	return ret;
};

Expr = Sizzle.selectors = {

	// Can be adjusted by the user
	cacheLength: 50,

	createPseudo: markFunction,

	match: matchExpr,

	attrHandle: {},

	find: {},

	relative: {
		">": { dir: "parentNode", first: true },
		" ": { dir: "parentNode" },
		"+": { dir: "previousSibling", first: true },
		"~": { dir: "previousSibling" }
	},

	preFilter: {
		"ATTR": function( match ) {
			match[ 1 ] = match[ 1 ].replace( runescape, funescape );

			// Move the given value to match[3] whether quoted or unquoted
			match[ 3 ] = ( match[ 3 ] || match[ 4 ] ||
				match[ 5 ] || "" ).replace( runescape, funescape );

			if ( match[ 2 ] === "~=" ) {
				match[ 3 ] = " " + match[ 3 ] + " ";
			}

			return match.slice( 0, 4 );
		},

		"CHILD": function( match ) {

			/* matches from matchExpr["CHILD"]
				1 type (only|nth|...)
				2 what (child|of-type)
				3 argument (even|odd|\d*|\d*n([+-]\d+)?|...)
				4 xn-component of xn+y argument ([+-]?\d*n|)
				5 sign of xn-component
				6 x of xn-component
				7 sign of y-component
				8 y of y-component
			*/
			match[ 1 ] = match[ 1 ].toLowerCase();

			if ( match[ 1 ].slice( 0, 3 ) === "nth" ) {

				// nth-* requires argument
				if ( !match[ 3 ] ) {
					Sizzle.error( match[ 0 ] );
				}

				// numeric x and y parameters for Expr.filter.CHILD
				// remember that false/true cast respectively to 0/1
				match[ 4 ] = +( match[ 4 ] ?
					match[ 5 ] + ( match[ 6 ] || 1 ) :
					2 * ( match[ 3 ] === "even" || match[ 3 ] === "odd" ) );
				match[ 5 ] = +( ( match[ 7 ] + match[ 8 ] ) || match[ 3 ] === "odd" );

				// other types prohibit arguments
			} else if ( match[ 3 ] ) {
				Sizzle.error( match[ 0 ] );
			}

			return match;
		},

		"PSEUDO": function( match ) {
			var excess,
				unquoted = !match[ 6 ] && match[ 2 ];

			if ( matchExpr[ "CHILD" ].test( match[ 0 ] ) ) {
				return null;
			}

			// Accept quoted arguments as-is
			if ( match[ 3 ] ) {
				match[ 2 ] = match[ 4 ] || match[ 5 ] || "";

			// Strip excess characters from unquoted arguments
			} else if ( unquoted && rpseudo.test( unquoted ) &&

				// Get excess from tokenize (recursively)
				( excess = tokenize( unquoted, true ) ) &&

				// advance to the next closing parenthesis
				( excess = unquoted.indexOf( ")", unquoted.length - excess ) - unquoted.length ) ) {

				// excess is a negative index
				match[ 0 ] = match[ 0 ].slice( 0, excess );
				match[ 2 ] = unquoted.slice( 0, excess );
			}

			// Return only captures needed by the pseudo filter method (type and argument)
			return match.slice( 0, 3 );
		}
	},

	filter: {

		"TAG": function( nodeNameSelector ) {
			var nodeName = nodeNameSelector.replace( runescape, funescape ).toLowerCase();
			return nodeNameSelector === "*" ?
				function() {
					return true;
				} :
				function( elem ) {
					return elem.nodeName && elem.nodeName.toLowerCase() === nodeName;
				};
		},

		"CLASS": function( className ) {
			var pattern = classCache[ className + " " ];

			return pattern ||
				( pattern = new RegExp( "(^|" + whitespace +
					")" + className + "(" + whitespace + "|$)" ) ) && classCache(
						className, function( elem ) {
							return pattern.test(
								typeof elem.className === "string" && elem.className ||
								typeof elem.getAttribute !== "undefined" &&
									elem.getAttribute( "class" ) ||
								""
							);
				} );
		},

		"ATTR": function( name, operator, check ) {
			return function( elem ) {
				var result = Sizzle.attr( elem, name );

				if ( result == null ) {
					return operator === "!=";
				}
				if ( !operator ) {
					return true;
				}

				result += "";

				/* eslint-disable max-len */

				return operator === "=" ? result === check :
					operator === "!=" ? result !== check :
					operator === "^=" ? check && result.indexOf( check ) === 0 :
					operator === "*=" ? check && result.indexOf( check ) > -1 :
					operator === "$=" ? check && result.slice( -check.length ) === check :
					operator === "~=" ? ( " " + result.replace( rwhitespace, " " ) + " " ).indexOf( check ) > -1 :
					operator === "|=" ? result === check || result.slice( 0, check.length + 1 ) === check + "-" :
					false;
				/* eslint-enable max-len */

			};
		},

		"CHILD": function( type, what, _argument, first, last ) {
			var simple = type.slice( 0, 3 ) !== "nth",
				forward = type.slice( -4 ) !== "last",
				ofType = what === "of-type";

			return first === 1 && last === 0 ?

				// Shortcut for :nth-*(n)
				function( elem ) {
					return !!elem.parentNode;
				} :

				function( elem, _context, xml ) {
					var cache, uniqueCache, outerCache, node, nodeIndex, start,
						dir = simple !== forward ? "nextSibling" : "previousSibling",
						parent = elem.parentNode,
						name = ofType && elem.nodeName.toLowerCase(),
						useCache = !xml && !ofType,
						diff = false;

					if ( parent ) {

						// :(first|last|only)-(child|of-type)
						if ( simple ) {
							while ( dir ) {
								node = elem;
								while ( ( node = node[ dir ] ) ) {
									if ( ofType ?
										node.nodeName.toLowerCase() === name :
										node.nodeType === 1 ) {

										return false;
									}
								}

								// Reverse direction for :only-* (if we haven't yet done so)
								start = dir = type === "only" && !start && "nextSibling";
							}
							return true;
						}

						start = [ forward ? parent.firstChild : parent.lastChild ];

						// non-xml :nth-child(...) stores cache data on `parent`
						if ( forward && useCache ) {

							// Seek `elem` from a previously-cached index

							// ...in a gzip-friendly way
							node = parent;
							outerCache = node[ expando ] || ( node[ expando ] = {} );

							// Support: IE <9 only
							// Defend against cloned attroperties (jQuery gh-1709)
							uniqueCache = outerCache[ node.uniqueID ] ||
								( outerCache[ node.uniqueID ] = {} );

							cache = uniqueCache[ type ] || [];
							nodeIndex = cache[ 0 ] === dirruns && cache[ 1 ];
							diff = nodeIndex && cache[ 2 ];
							node = nodeIndex && parent.childNodes[ nodeIndex ];

							while ( ( node = ++nodeIndex && node && node[ dir ] ||

								// Fallback to seeking `elem` from the start
								( diff = nodeIndex = 0 ) || start.pop() ) ) {

								// When found, cache indexes on `parent` and break
								if ( node.nodeType === 1 && ++diff && node === elem ) {
									uniqueCache[ type ] = [ dirruns, nodeIndex, diff ];
									break;
								}
							}

						} else {

							// Use previously-cached element index if available
							if ( useCache ) {

								// ...in a gzip-friendly way
								node = elem;
								outerCache = node[ expando ] || ( node[ expando ] = {} );

								// Support: IE <9 only
								// Defend against cloned attroperties (jQuery gh-1709)
								uniqueCache = outerCache[ node.uniqueID ] ||
									( outerCache[ node.uniqueID ] = {} );

								cache = uniqueCache[ type ] || [];
								nodeIndex = cache[ 0 ] === dirruns && cache[ 1 ];
								diff = nodeIndex;
							}

							// xml :nth-child(...)
							// or :nth-last-child(...) or :nth(-last)?-of-type(...)
							if ( diff === false ) {

								// Use the same loop as above to seek `elem` from the start
								while ( ( node = ++nodeIndex && node && node[ dir ] ||
									( diff = nodeIndex = 0 ) || start.pop() ) ) {

									if ( ( ofType ?
										node.nodeName.toLowerCase() === name :
										node.nodeType === 1 ) &&
										++diff ) {

										// Cache the index of each encountered element
										if ( useCache ) {
											outerCache = node[ expando ] ||
												( node[ expando ] = {} );

											// Support: IE <9 only
											// Defend against cloned attroperties (jQuery gh-1709)
											uniqueCache = outerCache[ node.uniqueID ] ||
												( outerCache[ node.uniqueID ] = {} );

											uniqueCache[ type ] = [ dirruns, diff ];
										}

										if ( node === elem ) {
											break;
										}
									}
								}
							}
						}

						// Incorporate the offset, then check against cycle size
						diff -= last;
						return diff === first || ( diff % first === 0 && diff / first >= 0 );
					}
				};
		},

		"PSEUDO": function( pseudo, argument ) {

			// pseudo-class names are case-insensitive
			// http://www.w3.org/TR/selectors/#pseudo-classes
			// Prioritize by case sensitivity in case custom pseudos are added with uppercase letters
			// Remember that setFilters inherits from pseudos
			var args,
				fn = Expr.pseudos[ pseudo ] || Expr.setFilters[ pseudo.toLowerCase() ] ||
					Sizzle.error( "unsupported pseudo: " + pseudo );

			// The user may use createPseudo to indicate that
			// arguments are needed to create the filter function
			// just as Sizzle does
			if ( fn[ expando ] ) {
				return fn( argument );
			}

			// But maintain support for old signatures
			if ( fn.length > 1 ) {
				args = [ pseudo, pseudo, "", argument ];
				return Expr.setFilters.hasOwnProperty( pseudo.toLowerCase() ) ?
					markFunction( function( seed, matches ) {
						var idx,
							matched = fn( seed, argument ),
							i = matched.length;
						while ( i-- ) {
							idx = indexOf( seed, matched[ i ] );
							seed[ idx ] = !( matches[ idx ] = matched[ i ] );
						}
					} ) :
					function( elem ) {
						return fn( elem, 0, args );
					};
			}

			return fn;
		}
	},

	pseudos: {

		// Potentially complex pseudos
		"not": markFunction( function( selector ) {

			// Trim the selector passed to compile
			// to avoid treating leading and trailing
			// spaces as combinators
			var input = [],
				results = [],
				matcher = compile( selector.replace( rtrim, "$1" ) );

			return matcher[ expando ] ?
				markFunction( function( seed, matches, _context, xml ) {
					var elem,
						unmatched = matcher( seed, null, xml, [] ),
						i = seed.length;

					// Match elements unmatched by `matcher`
					while ( i-- ) {
						if ( ( elem = unmatched[ i ] ) ) {
							seed[ i ] = !( matches[ i ] = elem );
						}
					}
				} ) :
				function( elem, _context, xml ) {
					input[ 0 ] = elem;
					matcher( input, null, xml, results );

					// Don't keep the element (issue #299)
					input[ 0 ] = null;
					return !results.pop();
				};
		} ),

		"has": markFunction( function( selector ) {
			return function( elem ) {
				return Sizzle( selector, elem ).length > 0;
			};
		} ),

		"contains": markFunction( function( text ) {
			text = text.replace( runescape, funescape );
			return function( elem ) {
				return ( elem.textContent || getText( elem ) ).indexOf( text ) > -1;
			};
		} ),

		// "Whether an element is represented by a :lang() selector
		// is based solely on the element's language value
		// being equal to the identifier C,
		// or beginning with the identifier C immediately followed by "-".
		// The matching of C against the element's language value is performed case-insensitively.
		// The identifier C does not have to be a valid language name."
		// http://www.w3.org/TR/selectors/#lang-pseudo
		"lang": markFunction( function( lang ) {

			// lang value must be a valid identifier
			if ( !ridentifier.test( lang || "" ) ) {
				Sizzle.error( "unsupported lang: " + lang );
			}
			lang = lang.replace( runescape, funescape ).toLowerCase();
			return function( elem ) {
				var elemLang;
				do {
					if ( ( elemLang = documentIsHTML ?
						elem.lang :
						elem.getAttribute( "xml:lang" ) || elem.getAttribute( "lang" ) ) ) {

						elemLang = elemLang.toLowerCase();
						return elemLang === lang || elemLang.indexOf( lang + "-" ) === 0;
					}
				} while ( ( elem = elem.parentNode ) && elem.nodeType === 1 );
				return false;
			};
		} ),

		// Miscellaneous
		"target": function( elem ) {
			var hash = window.location && window.location.hash;
			return hash && hash.slice( 1 ) === elem.id;
		},

		"root": function( elem ) {
			return elem === docElem;
		},

		"focus": function( elem ) {
			return elem === document.activeElement &&
				( !document.hasFocus || document.hasFocus() ) &&
				!!( elem.type || elem.href || ~elem.tabIndex );
		},

		// Boolean properties
		"enabled": createDisabledPseudo( false ),
		"disabled": createDisabledPseudo( true ),

		"checked": function( elem ) {

			// In CSS3, :checked should return both checked and selected elements
			// http://www.w3.org/TR/2011/REC-css3-selectors-20110929/#checked
			var nodeName = elem.nodeName.toLowerCase();
			return ( nodeName === "input" && !!elem.checked ) ||
				( nodeName === "option" && !!elem.selected );
		},

		"selected": function( elem ) {

			// Accessing this property makes selected-by-default
			// options in Safari work properly
			if ( elem.parentNode ) {
				// eslint-disable-next-line no-unused-expressions
				elem.parentNode.selectedIndex;
			}

			return elem.selected === true;
		},

		// Contents
		"empty": function( elem ) {

			// http://www.w3.org/TR/selectors/#empty-pseudo
			// :empty is negated by element (1) or content nodes (text: 3; cdata: 4; entity ref: 5),
			//   but not by others (comment: 8; processing instruction: 7; etc.)
			// nodeType < 6 works because attributes (2) do not appear as children
			for ( elem = elem.firstChild; elem; elem = elem.nextSibling ) {
				if ( elem.nodeType < 6 ) {
					return false;
				}
			}
			return true;
		},

		"parent": function( elem ) {
			return !Expr.pseudos[ "empty" ]( elem );
		},

		// Element/input types
		"header": function( elem ) {
			return rheader.test( elem.nodeName );
		},

		"input": function( elem ) {
			return rinputs.test( elem.nodeName );
		},

		"button": function( elem ) {
			var name = elem.nodeName.toLowerCase();
			return name === "input" && elem.type === "button" || name === "button";
		},

		"text": function( elem ) {
			var attr;
			return elem.nodeName.toLowerCase() === "input" &&
				elem.type === "text" &&

				// Support: IE<8
				// New HTML5 attribute values (e.g., "search") appear with elem.type === "text"
				( ( attr = elem.getAttribute( "type" ) ) == null ||
					attr.toLowerCase() === "text" );
		},

		// Position-in-collection
		"first": createPositionalPseudo( function() {
			return [ 0 ];
		} ),

		"last": createPositionalPseudo( function( _matchIndexes, length ) {
			return [ length - 1 ];
		} ),

		"eq": createPositionalPseudo( function( _matchIndexes, length, argument ) {
			return [ argument < 0 ? argument + length : argument ];
		} ),

		"even": createPositionalPseudo( function( matchIndexes, length ) {
			var i = 0;
			for ( ; i < length; i += 2 ) {
				matchIndexes.push( i );
			}
			return matchIndexes;
		} ),

		"odd": createPositionalPseudo( function( matchIndexes, length ) {
			var i = 1;
			for ( ; i < length; i += 2 ) {
				matchIndexes.push( i );
			}
			return matchIndexes;
		} ),

		"lt": createPositionalPseudo( function( matchIndexes, length, argument ) {
			var i = argument < 0 ?
				argument + length :
				argument > length ?
					length :
					argument;
			for ( ; --i >= 0; ) {
				matchIndexes.push( i );
			}
			return matchIndexes;
		} ),

		"gt": createPositionalPseudo( function( matchIndexes, length, argument ) {
			var i = argument < 0 ? argument + length : argument;
			for ( ; ++i < length; ) {
				matchIndexes.push( i );
			}
			return matchIndexes;
		} )
	}
};

Expr.pseudos[ "nth" ] = Expr.pseudos[ "eq" ];

// Add button/input type pseudos
for ( i in { radio: true, checkbox: true, file: true, password: true, image: true } ) {
	Expr.pseudos[ i ] = createInputPseudo( i );
}
for ( i in { submit: true, reset: true } ) {
	Expr.pseudos[ i ] = createButtonPseudo( i );
}

// Easy API for creating new setFilters
function setFilters() {}
setFilters.prototype = Expr.filters = Expr.pseudos;
Expr.setFilters = new setFilters();

tokenize = Sizzle.tokenize = function( selector, parseOnly ) {
	var matched, match, tokens, type,
		soFar, groups, preFilters,
		cached = tokenCache[ selector + " " ];

	if ( cached ) {
		return parseOnly ? 0 : cached.slice( 0 );
	}

	soFar = selector;
	groups = [];
	preFilters = Expr.preFilter;

	while ( soFar ) {

		// Comma and first run
		if ( !matched || ( match = rcomma.exec( soFar ) ) ) {
			if ( match ) {

				// Don't consume trailing commas as valid
				soFar = soFar.slice( match[ 0 ].length ) || soFar;
			}
			groups.push( ( tokens = [] ) );
		}

		matched = false;

		// Combinators
		if ( ( match = rcombinators.exec( soFar ) ) ) {
			matched = match.shift();
			tokens.push( {
				value: matched,

				// Cast descendant combinators to space
				type: match[ 0 ].replace( rtrim, " " )
			} );
			soFar = soFar.slice( matched.length );
		}

		// Filters
		for ( type in Expr.filter ) {
			if ( ( match = matchExpr[ type ].exec( soFar ) ) && ( !preFilters[ type ] ||
				( match = preFilters[ type ]( match ) ) ) ) {
				matched = match.shift();
				tokens.push( {
					value: matched,
					type: type,
					matches: match
				} );
				soFar = soFar.slice( matched.length );
			}
		}

		if ( !matched ) {
			break;
		}
	}

	// Return the length of the invalid excess
	// if we're just parsing
	// Otherwise, throw an error or return tokens
	return parseOnly ?
		soFar.length :
		soFar ?
			Sizzle.error( selector ) :

			// Cache the tokens
			tokenCache( selector, groups ).slice( 0 );
};

function toSelector( tokens ) {
	var i = 0,
		len = tokens.length,
		selector = "";
	for ( ; i < len; i++ ) {
		selector += tokens[ i ].value;
	}
	return selector;
}

function addCombinator( matcher, combinator, base ) {
	var dir = combinator.dir,
		skip = combinator.next,
		key = skip || dir,
		checkNonElements = base && key === "parentNode",
		doneName = done++;

	return combinator.first ?

		// Check against closest ancestor/preceding element
		function( elem, context, xml ) {
			while ( ( elem = elem[ dir ] ) ) {
				if ( elem.nodeType === 1 || checkNonElements ) {
					return matcher( elem, context, xml );
				}
			}
			return false;
		} :

		// Check against all ancestor/preceding elements
		function( elem, context, xml ) {
			var oldCache, uniqueCache, outerCache,
				newCache = [ dirruns, doneName ];

			// We can't set arbitrary data on XML nodes, so they don't benefit from combinator caching
			if ( xml ) {
				while ( ( elem = elem[ dir ] ) ) {
					if ( elem.nodeType === 1 || checkNonElements ) {
						if ( matcher( elem, context, xml ) ) {
							return true;
						}
					}
				}
			} else {
				while ( ( elem = elem[ dir ] ) ) {
					if ( elem.nodeType === 1 || checkNonElements ) {
						outerCache = elem[ expando ] || ( elem[ expando ] = {} );

						// Support: IE <9 only
						// Defend against cloned attroperties (jQuery gh-1709)
						uniqueCache = outerCache[ elem.uniqueID ] ||
							( outerCache[ elem.uniqueID ] = {} );

						if ( skip && skip === elem.nodeName.toLowerCase() ) {
							elem = elem[ dir ] || elem;
						} else if ( ( oldCache = uniqueCache[ key ] ) &&
							oldCache[ 0 ] === dirruns && oldCache[ 1 ] === doneName ) {

							// Assign to newCache so results back-propagate to previous elements
							return ( newCache[ 2 ] = oldCache[ 2 ] );
						} else {

							// Reuse newcache so results back-propagate to previous elements
							uniqueCache[ key ] = newCache;

							// A match means we're done; a fail means we have to keep checking
							if ( ( newCache[ 2 ] = matcher( elem, context, xml ) ) ) {
								return true;
							}
						}
					}
				}
			}
			return false;
		};
}

function elementMatcher( matchers ) {
	return matchers.length > 1 ?
		function( elem, context, xml ) {
			var i = matchers.length;
			while ( i-- ) {
				if ( !matchers[ i ]( elem, context, xml ) ) {
					return false;
				}
			}
			return true;
		} :
		matchers[ 0 ];
}

function multipleContexts( selector, contexts, results ) {
	var i = 0,
		len = contexts.length;
	for ( ; i < len; i++ ) {
		Sizzle( selector, contexts[ i ], results );
	}
	return results;
}

function condense( unmatched, map, filter, context, xml ) {
	var elem,
		newUnmatched = [],
		i = 0,
		len = unmatched.length,
		mapped = map != null;

	for ( ; i < len; i++ ) {
		if ( ( elem = unmatched[ i ] ) ) {
			if ( !filter || filter( elem, context, xml ) ) {
				newUnmatched.push( elem );
				if ( mapped ) {
					map.push( i );
				}
			}
		}
	}

	return newUnmatched;
}

function setMatcher( preFilter, selector, matcher, postFilter, postFinder, postSelector ) {
	if ( postFilter && !postFilter[ expando ] ) {
		postFilter = setMatcher( postFilter );
	}
	if ( postFinder && !postFinder[ expando ] ) {
		postFinder = setMatcher( postFinder, postSelector );
	}
	return markFunction( function( seed, results, context, xml ) {
		var temp, i, elem,
			preMap = [],
			postMap = [],
			preexisting = results.length,

			// Get initial elements from seed or context
			elems = seed || multipleContexts(
				selector || "*",
				context.nodeType ? [ context ] : context,
				[]
			),

			// Prefilter to get matcher input, preserving a map for seed-results synchronization
			matcherIn = preFilter && ( seed || !selector ) ?
				condense( elems, preMap, preFilter, context, xml ) :
				elems,

			matcherOut = matcher ?

				// If we have a postFinder, or filtered seed, or non-seed postFilter or preexisting results,
				postFinder || ( seed ? preFilter : preexisting || postFilter ) ?

					// ...intermediate processing is necessary
					[] :

					// ...otherwise use results directly
					results :
				matcherIn;

		// Find primary matches
		if ( matcher ) {
			matcher( matcherIn, matcherOut, context, xml );
		}

		// Apply postFilter
		if ( postFilter ) {
			temp = condense( matcherOut, postMap );
			postFilter( temp, [], context, xml );

			// Un-match failing elements by moving them back to matcherIn
			i = temp.length;
			while ( i-- ) {
				if ( ( elem = temp[ i ] ) ) {
					matcherOut[ postMap[ i ] ] = !( matcherIn[ postMap[ i ] ] = elem );
				}
			}
		}

		if ( seed ) {
			if ( postFinder || preFilter ) {
				if ( postFinder ) {

					// Get the final matcherOut by condensing this intermediate into postFinder contexts
					temp = [];
					i = matcherOut.length;
					while ( i-- ) {
						if ( ( elem = matcherOut[ i ] ) ) {

							// Restore matcherIn since elem is not yet a final match
							temp.push( ( matcherIn[ i ] = elem ) );
						}
					}
					postFinder( null, ( matcherOut = [] ), temp, xml );
				}

				// Move matched elements from seed to results to keep them synchronized
				i = matcherOut.length;
				while ( i-- ) {
					if ( ( elem = matcherOut[ i ] ) &&
						( temp = postFinder ? indexOf( seed, elem ) : preMap[ i ] ) > -1 ) {

						seed[ temp ] = !( results[ temp ] = elem );
					}
				}
			}

		// Add elements to results, through postFinder if defined
		} else {
			matcherOut = condense(
				matcherOut === results ?
					matcherOut.splice( preexisting, matcherOut.length ) :
					matcherOut
			);
			if ( postFinder ) {
				postFinder( null, results, matcherOut, xml );
			} else {
				push.apply( results, matcherOut );
			}
		}
	} );
}

function matcherFromTokens( tokens ) {
	var checkContext, matcher, j,
		len = tokens.length,
		leadingRelative = Expr.relative[ tokens[ 0 ].type ],
		implicitRelative = leadingRelative || Expr.relative[ " " ],
		i = leadingRelative ? 1 : 0,

		// The foundational matcher ensures that elements are reachable from top-level context(s)
		matchContext = addCombinator( function( elem ) {
			return elem === checkContext;
		}, implicitRelative, true ),
		matchAnyContext = addCombinator( function( elem ) {
			return indexOf( checkContext, elem ) > -1;
		}, implicitRelative, true ),
		matchers = [ function( elem, context, xml ) {
			var ret = ( !leadingRelative && ( xml || context !== outermostContext ) ) || (
				( checkContext = context ).nodeType ?
					matchContext( elem, context, xml ) :
					matchAnyContext( elem, context, xml ) );

			// Avoid hanging onto element (issue #299)
			checkContext = null;
			return ret;
		} ];

	for ( ; i < len; i++ ) {
		if ( ( matcher = Expr.relative[ tokens[ i ].type ] ) ) {
			matchers = [ addCombinator( elementMatcher( matchers ), matcher ) ];
		} else {
			matcher = Expr.filter[ tokens[ i ].type ].apply( null, tokens[ i ].matches );

			// Return special upon seeing a positional matcher
			if ( matcher[ expando ] ) {

				// Find the next relative operator (if any) for proper handling
				j = ++i;
				for ( ; j < len; j++ ) {
					if ( Expr.relative[ tokens[ j ].type ] ) {
						break;
					}
				}
				return setMatcher(
					i > 1 && elementMatcher( matchers ),
					i > 1 && toSelector(

					// If the preceding token was a descendant combinator, insert an implicit any-element `*`
					tokens
						.slice( 0, i - 1 )
						.concat( { value: tokens[ i - 2 ].type === " " ? "*" : "" } )
					).replace( rtrim, "$1" ),
					matcher,
					i < j && matcherFromTokens( tokens.slice( i, j ) ),
					j < len && matcherFromTokens( ( tokens = tokens.slice( j ) ) ),
					j < len && toSelector( tokens )
				);
			}
			matchers.push( matcher );
		}
	}

	return elementMatcher( matchers );
}

function matcherFromGroupMatchers( elementMatchers, setMatchers ) {
	var bySet = setMatchers.length > 0,
		byElement = elementMatchers.length > 0,
		superMatcher = function( seed, context, xml, results, outermost ) {
			var elem, j, matcher,
				matchedCount = 0,
				i = "0",
				unmatched = seed && [],
				setMatched = [],
				contextBackup = outermostContext,

				// We must always have either seed elements or outermost context
				elems = seed || byElement && Expr.find[ "TAG" ]( "*", outermost ),

				// Use integer dirruns iff this is the outermost matcher
				dirrunsUnique = ( dirruns += contextBackup == null ? 1 : Math.random() || 0.1 ),
				len = elems.length;

			if ( outermost ) {

				// Support: IE 11+, Edge 17 - 18+
				// IE/Edge sometimes throw a "Permission denied" error when strict-comparing
				// two documents; shallow comparisons work.
				// eslint-disable-next-line eqeqeq
				outermostContext = context == document || context || outermost;
			}

			// Add elements passing elementMatchers directly to results
			// Support: IE<9, Safari
			// Tolerate NodeList properties (IE: "length"; Safari: <number>) matching elements by id
			for ( ; i !== len && ( elem = elems[ i ] ) != null; i++ ) {
				if ( byElement && elem ) {
					j = 0;

					// Support: IE 11+, Edge 17 - 18+
					// IE/Edge sometimes throw a "Permission denied" error when strict-comparing
					// two documents; shallow comparisons work.
					// eslint-disable-next-line eqeqeq
					if ( !context && elem.ownerDocument != document ) {
						setDocument( elem );
						xml = !documentIsHTML;
					}
					while ( ( matcher = elementMatchers[ j++ ] ) ) {
						if ( matcher( elem, context || document, xml ) ) {
							results.push( elem );
							break;
						}
					}
					if ( outermost ) {
						dirruns = dirrunsUnique;
					}
				}

				// Track unmatched elements for set filters
				if ( bySet ) {

					// They will have gone through all possible matchers
					if ( ( elem = !matcher && elem ) ) {
						matchedCount--;
					}

					// Lengthen the array for every element, matched or not
					if ( seed ) {
						unmatched.push( elem );
					}
				}
			}

			// `i` is now the count of elements visited above, and adding it to `matchedCount`
			// makes the latter nonnegative.
			matchedCount += i;

			// Apply set filters to unmatched elements
			// NOTE: This can be skipped if there are no unmatched elements (i.e., `matchedCount`
			// equals `i`), unless we didn't visit _any_ elements in the above loop because we have
			// no element matchers and no seed.
			// Incrementing an initially-string "0" `i` allows `i` to remain a string only in that
			// case, which will result in a "00" `matchedCount` that differs from `i` but is also
			// numerically zero.
			if ( bySet && i !== matchedCount ) {
				j = 0;
				while ( ( matcher = setMatchers[ j++ ] ) ) {
					matcher( unmatched, setMatched, context, xml );
				}

				if ( seed ) {

					// Reintegrate element matches to eliminate the need for sorting
					if ( matchedCount > 0 ) {
						while ( i-- ) {
							if ( !( unmatched[ i ] || setMatched[ i ] ) ) {
								setMatched[ i ] = pop.call( results );
							}
						}
					}

					// Discard index placeholder values to get only actual matches
					setMatched = condense( setMatched );
				}

				// Add matches to results
				push.apply( results, setMatched );

				// Seedless set matches succeeding multiple successful matchers stipulate sorting
				if ( outermost && !seed && setMatched.length > 0 &&
					( matchedCount + setMatchers.length ) > 1 ) {

					Sizzle.uniqueSort( results );
				}
			}

			// Override manipulation of globals by nested matchers
			if ( outermost ) {
				dirruns = dirrunsUnique;
				outermostContext = contextBackup;
			}

			return unmatched;
		};

	return bySet ?
		markFunction( superMatcher ) :
		superMatcher;
}

compile = Sizzle.compile = function( selector, match /* Internal Use Only */ ) {
	var i,
		setMatchers = [],
		elementMatchers = [],
		cached = compilerCache[ selector + " " ];

	if ( !cached ) {

		// Generate a function of recursive functions that can be used to check each element
		if ( !match ) {
			match = tokenize( selector );
		}
		i = match.length;
		while ( i-- ) {
			cached = matcherFromTokens( match[ i ] );
			if ( cached[ expando ] ) {
				setMatchers.push( cached );
			} else {
				elementMatchers.push( cached );
			}
		}

		// Cache the compiled function
		cached = compilerCache(
			selector,
			matcherFromGroupMatchers( elementMatchers, setMatchers )
		);

		// Save selector and tokenization
		cached.selector = selector;
	}
	return cached;
};

/**
 * A low-level selection function that works with Sizzle's compiled
 *  selector functions
 * @param {String|Function} selector A selector or a pre-compiled
 *  selector function built with Sizzle.compile
 * @param {Element} context
 * @param {Array} [results]
 * @param {Array} [seed] A set of elements to match against
 */
select = Sizzle.select = function( selector, context, results, seed ) {
	var i, tokens, token, type, find,
		compiled = typeof selector === "function" && selector,
		match = !seed && tokenize( ( selector = compiled.selector || selector ) );

	results = results || [];

	// Try to minimize operations if there is only one selector in the list and no seed
	// (the latter of which guarantees us context)
	if ( match.length === 1 ) {

		// Reduce context if the leading compound selector is an ID
		tokens = match[ 0 ] = match[ 0 ].slice( 0 );
		if ( tokens.length > 2 && ( token = tokens[ 0 ] ).type === "ID" &&
			context.nodeType === 9 && documentIsHTML && Expr.relative[ tokens[ 1 ].type ] ) {

			context = ( Expr.find[ "ID" ]( token.matches[ 0 ]
				.replace( runescape, funescape ), context ) || [] )[ 0 ];
			if ( !context ) {
				return results;

			// Precompiled matchers will still verify ancestry, so step up a level
			} else if ( compiled ) {
				context = context.parentNode;
			}

			selector = selector.slice( tokens.shift().value.length );
		}

		// Fetch a seed set for right-to-left matching
		i = matchExpr[ "needsContext" ].test( selector ) ? 0 : tokens.length;
		while ( i-- ) {
			token = tokens[ i ];

			// Abort if we hit a combinator
			if ( Expr.relative[ ( type = token.type ) ] ) {
				break;
			}
			if ( ( find = Expr.find[ type ] ) ) {

				// Search, expanding context for leading sibling combinators
				if ( ( seed = find(
					token.matches[ 0 ].replace( runescape, funescape ),
					rsibling.test( tokens[ 0 ].type ) && testContext( context.parentNode ) ||
						context
				) ) ) {

					// If seed is empty or no tokens remain, we can return early
					tokens.splice( i, 1 );
					selector = seed.length && toSelector( tokens );
					if ( !selector ) {
						push.apply( results, seed );
						return results;
					}

					break;
				}
			}
		}
	}

	// Compile and execute a filtering function if one is not provided
	// Provide `match` to avoid retokenization if we modified the selector above
	( compiled || compile( selector, match ) )(
		seed,
		context,
		!documentIsHTML,
		results,
		!context || rsibling.test( selector ) && testContext( context.parentNode ) || context
	);
	return results;
};

// One-time assignments

// Sort stability
support.sortStable = expando.split( "" ).sort( sortOrder ).join( "" ) === expando;

// Support: Chrome 14-35+
// Always assume duplicates if they aren't passed to the comparison function
support.detectDuplicates = !!hasDuplicate;

// Initialize against the default document
setDocument();

// Support: Webkit<537.32 - Safari 6.0.3/Chrome 25 (fixed in Chrome 27)
// Detached nodes confoundingly follow *each other*
support.sortDetached = assert( function( el ) {

	// Should return 1, but returns 4 (following)
	return el.compareDocumentPosition( document.createElement( "fieldset" ) ) & 1;
} );

// Support: IE<8
// Prevent attribute/property "interpolation"
// https://msdn.microsoft.com/en-us/library/ms536429%28VS.85%29.aspx
if ( !assert( function( el ) {
	el.innerHTML = "<a href='#'></a>";
	return el.firstChild.getAttribute( "href" ) === "#";
} ) ) {
	addHandle( "type|href|height|width", function( elem, name, isXML ) {
		if ( !isXML ) {
			return elem.getAttribute( name, name.toLowerCase() === "type" ? 1 : 2 );
		}
	} );
}

// Support: IE<9
// Use defaultValue in place of getAttribute("value")
if ( !support.attributes || !assert( function( el ) {
	el.innerHTML = "<input/>";
	el.firstChild.setAttribute( "value", "" );
	return el.firstChild.getAttribute( "value" ) === "";
} ) ) {
	addHandle( "value", function( elem, _name, isXML ) {
		if ( !isXML && elem.nodeName.toLowerCase() === "input" ) {
			return elem.defaultValue;
		}
	} );
}

// Support: IE<9
// Use getAttributeNode to fetch booleans when getAttribute lies
if ( !assert( function( el ) {
	return el.getAttribute( "disabled" ) == null;
} ) ) {
	addHandle( booleans, function( elem, name, isXML ) {
		var val;
		if ( !isXML ) {
			return elem[ name ] === true ? name.toLowerCase() :
				( val = elem.getAttributeNode( name ) ) && val.specified ?
					val.value :
					null;
		}
	} );
}

return Sizzle;

} )( window );



jQuery.find = Sizzle;
jQuery.expr = Sizzle.selectors;

// Deprecated
jQuery.expr[ ":" ] = jQuery.expr.pseudos;
jQuery.uniqueSort = jQuery.unique = Sizzle.uniqueSort;
jQuery.text = Sizzle.getText;
jQuery.isXMLDoc = Sizzle.isXML;
jQuery.contains = Sizzle.contains;
jQuery.escapeSelector = Sizzle.escape;




var dir = function( elem, dir, until ) {
	var matched = [],
		truncate = until !== undefined;

	while ( ( elem = elem[ dir ] ) && elem.nodeType !== 9 ) {
		if ( elem.nodeType === 1 ) {
			if ( truncate && jQuery( elem ).is( until ) ) {
				break;
			}
			matched.push( elem );
		}
	}
	return matched;
};


var siblings = function( n, elem ) {
	var matched = [];

	for ( ; n; n = n.nextSibling ) {
		if ( n.nodeType === 1 && n !== elem ) {
			matched.push( n );
		}
	}

	return matched;
};


var rneedsContext = jQuery.expr.match.needsContext;



function nodeName( elem, name ) {

	return elem.nodeName && elem.nodeName.toLowerCase() === name.toLowerCase();

}
var rsingleTag = ( /^<([a-z][^\/\0>:\x20\t\r\n\f]*)[\x20\t\r\n\f]*\/?>(?:<\/\1>|)$/i );



// Implement the identical functionality for filter and not
function winnow( elements, qualifier, not ) {
	if ( isFunction( qualifier ) ) {
		return jQuery.grep( elements, function( elem, i ) {
			return !!qualifier.call( elem, i, elem ) !== not;
		} );
	}

	// Single element
	if ( qualifier.nodeType ) {
		return jQuery.grep( elements, function( elem ) {
			return ( elem === qualifier ) !== not;
		} );
	}

	// Arraylike of elements (jQuery, arguments, Array)
	if ( typeof qualifier !== "string" ) {
		return jQuery.grep( elements, function( elem ) {
			return ( indexOf.call( qualifier, elem ) > -1 ) !== not;
		} );
	}

	// Filtered directly for both simple and complex selectors
	return jQuery.filter( qualifier, elements, not );
}

jQuery.filter = function( expr, elems, not ) {
	var elem = elems[ 0 ];

	if ( not ) {
		expr = ":not(" + expr + ")";
	}

	if ( elems.length === 1 && elem.nodeType === 1 ) {
		return jQuery.find.matchesSelector( elem, expr ) ? [ elem ] : [];
	}

	return jQuery.find.matches( expr, jQuery.grep( elems, function( elem ) {
		return elem.nodeType === 1;
	} ) );
};

jQuery.fn.extend( {
	find: function( selector ) {
		var i, ret,
			len = this.length,
			self = this;

		if ( typeof selector !== "string" ) {
			return this.pushStack( jQuery( selector ).filter( function() {
				for ( i = 0; i < len; i++ ) {
					if ( jQuery.contains( self[ i ], this ) ) {
						return true;
					}
				}
			} ) );
		}

		ret = this.pushStack( [] );

		for ( i = 0; i < len; i++ ) {
			jQuery.find( selector, self[ i ], ret );
		}

		return len > 1 ? jQuery.uniqueSort( ret ) : ret;
	},
	filter: function( selector ) {
		return this.pushStack( winnow( this, selector || [], false ) );
	},
	not: function( selector ) {
		return this.pushStack( winnow( this, selector || [], true ) );
	},
	is: function( selector ) {
		return !!winnow(
			this,

			// If this is a positional/relative selector, check membership in the returned set
			// so $("p:first").is("p:last") won't return true for a doc with two "p".
			typeof selector === "string" && rneedsContext.test( selector ) ?
				jQuery( selector ) :
				selector || [],
			false
		).length;
	}
} );


// Initialize a jQuery object


// A central reference to the root jQuery(document)
var rootjQuery,

	// A simple way to check for HTML strings
	// Prioritize #id over <tag> to avoid XSS via location.hash (#9521)
	// Strict HTML recognition (#11290: must start with <)
	// Shortcut simple #id case for speed
	rquickExpr = /^(?:\s*(<[\w\W]+>)[^>]*|#([\w-]+))$/,

	init = jQuery.fn.init = function( selector, context, root ) {
		var match, elem;

		// HANDLE: $(""), $(null), $(undefined), $(false)
		if ( !selector ) {
			return this;
		}

		// Method init() accepts an alternate rootjQuery
		// so migrate can support jQuery.sub (gh-2101)
		root = root || rootjQuery;

		// Handle HTML strings
		if ( typeof selector === "string" ) {
			if ( selector[ 0 ] === "<" &&
				selector[ selector.length - 1 ] === ">" &&
				selector.length >= 3 ) {

				// Assume that strings that start and end with <> are HTML and skip the regex check
				match = [ null, selector, null ];

			} else {
				match = rquickExpr.exec( selector );
			}

			// Match html or make sure no context is specified for #id
			if ( match && ( match[ 1 ] || !context ) ) {

				// HANDLE: $(html) -> $(array)
				if ( match[ 1 ] ) {
					context = context instanceof jQuery ? context[ 0 ] : context;

					// Option to run scripts is true for back-compat
					// Intentionally let the error be thrown if parseHTML is not present
					jQuery.merge( this, jQuery.parseHTML(
						match[ 1 ],
						context && context.nodeType ? context.ownerDocument || context : document,
						true
					) );

					// HANDLE: $(html, props)
					if ( rsingleTag.test( match[ 1 ] ) && jQuery.isPlainObject( context ) ) {
						for ( match in context ) {

							// Properties of context are called as methods if possible
							if ( isFunction( this[ match ] ) ) {
								this[ match ]( context[ match ] );

							// ...and otherwise set as attributes
							} else {
								this.attr( match, context[ match ] );
							}
						}
					}

					return this;

				// HANDLE: $(#id)
				} else {
					elem = document.getElementById( match[ 2 ] );

					if ( elem ) {

						// Inject the element directly into the jQuery object
						this[ 0 ] = elem;
						this.length = 1;
					}
					return this;
				}

			// HANDLE: $(expr, $(...))
			} else if ( !context || context.jquery ) {
				return ( context || root ).find( selector );

			// HANDLE: $(expr, context)
			// (which is just equivalent to: $(context).find(expr)
			} else {
				return this.constructor( context ).find( selector );
			}

		// HANDLE: $(DOMElement)
		} else if ( selector.nodeType ) {
			this[ 0 ] = selector;
			this.length = 1;
			return this;

		// HANDLE: $(function)
		// Shortcut for document ready
		} else if ( isFunction( selector ) ) {
			return root.ready !== undefined ?
				root.ready( selector ) :

				// Execute immediately if ready is not present
				selector( jQuery );
		}

		return jQuery.makeArray( selector, this );
	};

// Give the init function the jQuery prototype for later instantiation
init.prototype = jQuery.fn;

// Initialize central reference
rootjQuery = jQuery( document );


var rparentsprev = /^(?:parents|prev(?:Until|All))/,

	// Methods guaranteed to produce a unique set when starting from a unique set
	guaranteedUnique = {
		children: true,
		contents: true,
		next: true,
		prev: true
	};

jQuery.fn.extend( {
	has: function( target ) {
		var targets = jQuery( target, this ),
			l = targets.length;

		return this.filter( function() {
			var i = 0;
			for ( ; i < l; i++ ) {
				if ( jQuery.contains( this, targets[ i ] ) ) {
					return true;
				}
			}
		} );
	},

	closest: function( selectors, context ) {
		var cur,
			i = 0,
			l = this.length,
			matched = [],
			targets = typeof selectors !== "string" && jQuery( selectors );

		// Positional selectors never match, since there's no _selection_ context
		if ( !rneedsContext.test( selectors ) ) {
			for ( ; i < l; i++ ) {
				for ( cur = this[ i ]; cur && cur !== context; cur = cur.parentNode ) {

					// Always skip document fragments
					if ( cur.nodeType < 11 && ( targets ?
						targets.index( cur ) > -1 :

						// Don't pass non-elements to Sizzle
						cur.nodeType === 1 &&
							jQuery.find.matchesSelector( cur, selectors ) ) ) {

						matched.push( cur );
						break;
					}
				}
			}
		}

		return this.pushStack( matched.length > 1 ? jQuery.uniqueSort( matched ) : matched );
	},

	// Determine the position of an element within the set
	index: function( elem ) {

		// No argument, return index in parent
		if ( !elem ) {
			return ( this[ 0 ] && this[ 0 ].parentNode ) ? this.first().prevAll().length : -1;
		}

		// Index in selector
		if ( typeof elem === "string" ) {
			return indexOf.call( jQuery( elem ), this[ 0 ] );
		}

		// Locate the position of the desired element
		return indexOf.call( this,

			// If it receives a jQuery object, the first element is used
			elem.jquery ? elem[ 0 ] : elem
		);
	},

	add: function( selector, context ) {
		return this.pushStack(
			jQuery.uniqueSort(
				jQuery.merge( this.get(), jQuery( selector, context ) )
			)
		);
	},

	addBack: function( selector ) {
		return this.add( selector == null ?
			this.prevObject : this.prevObject.filter( selector )
		);
	}
} );

function sibling( cur, dir ) {
	while ( ( cur = cur[ dir ] ) && cur.nodeType !== 1 ) {}
	return cur;
}

jQuery.each( {
	parent: function( elem ) {
		var parent = elem.parentNode;
		return parent && parent.nodeType !== 11 ? parent : null;
	},
	parents: function( elem ) {
		return dir( elem, "parentNode" );
	},
	parentsUntil: function( elem, _i, until ) {
		return dir( elem, "parentNode", until );
	},
	next: function( elem ) {
		return sibling( elem, "nextSibling" );
	},
	prev: function( elem ) {
		return sibling( elem, "previousSibling" );
	},
	nextAll: function( elem ) {
		return dir( elem, "nextSibling" );
	},
	prevAll: function( elem ) {
		return dir( elem, "previousSibling" );
	},
	nextUntil: function( elem, _i, until ) {
		return dir( elem, "nextSibling", until );
	},
	prevUntil: function( elem, _i, until ) {
		return dir( elem, "previousSibling", until );
	},
	siblings: function( elem ) {
		return siblings( ( elem.parentNode || {} ).firstChild, elem );
	},
	children: function( elem ) {
		return siblings( elem.firstChild );
	},
	contents: function( elem ) {
		if ( elem.contentDocument != null &&

			// Support: IE 11+
			// <object> elements with no `data` attribute has an object
			// `contentDocument` with a `null` prototype.
			getProto( elem.contentDocument ) ) {

			return elem.contentDocument;
		}

		// Support: IE 9 - 11 only, iOS 7 only, Android Browser <=4.3 only
		// Treat the template element as a regular one in browsers that
		// don't support it.
		if ( nodeName( elem, "template" ) ) {
			elem = elem.content || elem;
		}

		return jQuery.merge( [], elem.childNodes );
	}
}, function( name, fn ) {
	jQuery.fn[ name ] = function( until, selector ) {
		var matched = jQuery.map( this, fn, until );

		if ( name.slice( -5 ) !== "Until" ) {
			selector = until;
		}

		if ( selector && typeof selector === "string" ) {
			matched = jQuery.filter( selector, matched );
		}

		if ( this.length > 1 ) {

			// Remove duplicates
			if ( !guaranteedUnique[ name ] ) {
				jQuery.uniqueSort( matched );
			}

			// Reverse order for parents* and prev-derivatives
			if ( rparentsprev.test( name ) ) {
				matched.reverse();
			}
		}

		return this.pushStack( matched );
	};
} );
var rnothtmlwhite = ( /[^\x20\t\r\n\f]+/g );



// Convert String-formatted options into Object-formatted ones
function createOptions( options ) {
	var object = {};
	jQuery.each( options.match( rnothtmlwhite ) || [], function( _, flag ) {
		object[ flag ] = true;
	} );
	return object;
}

/*
 * Create a callback list using the following parameters:
 *
 *	options: an optional list of space-separated options that will change how
 *			the callback list behaves or a more traditional option object
 *
 * By default a callback list will act like an event callback list and can be
 * "fired" multiple times.
 *
 * Possible options:
 *
 *	once:			will ensure the callback list can only be fired once (like a Deferred)
 *
 *	memory:			will keep track of previous values and will call any callback added
 *					after the list has been fired right away with the latest "memorized"
 *					values (like a Deferred)
 *
 *	unique:			will ensure a callback can only be added once (no duplicate in the list)
 *
 *	stopOnFalse:	interrupt callings when a callback returns false
 *
 */
jQuery.Callbacks = function( options ) {

	// Convert options from String-formatted to Object-formatted if needed
	// (we check in cache first)
	options = typeof options === "string" ?
		createOptions( options ) :
		jQuery.extend( {}, options );

	var // Flag to know if list is currently firing
		firing,

		// Last fire value for non-forgettable lists
		memory,

		// Flag to know if list was already fired
		fired,

		// Flag to prevent firing
		locked,

		// Actual callback list
		list = [],

		// Queue of execution data for repeatable lists
		queue = [],

		// Index of currently firing callback (modified by add/remove as needed)
		firingIndex = -1,

		// Fire callbacks
		fire = function() {

			// Enforce single-firing
			locked = locked || options.once;

			// Execute callbacks for all pending executions,
			// respecting firingIndex overrides and runtime changes
			fired = firing = true;
			for ( ; queue.length; firingIndex = -1 ) {
				memory = queue.shift();
				while ( ++firingIndex < list.length ) {

					// Run callback and check for early termination
					if ( list[ firingIndex ].apply( memory[ 0 ], memory[ 1 ] ) === false &&
						options.stopOnFalse ) {

						// Jump to end and forget the data so .add doesn't re-fire
						firingIndex = list.length;
						memory = false;
					}
				}
			}

			// Forget the data if we're done with it
			if ( !options.memory ) {
				memory = false;
			}

			firing = false;

			// Clean up if we're done firing for good
			if ( locked ) {

				// Keep an empty list if we have data for future add calls
				if ( memory ) {
					list = [];

				// Otherwise, this object is spent
				} else {
					list = "";
				}
			}
		},

		// Actual Callbacks object
		self = {

			// Add a callback or a collection of callbacks to the list
			add: function() {
				if ( list ) {

					// If we have memory from a past run, we should fire after adding
					if ( memory && !firing ) {
						firingIndex = list.length - 1;
						queue.push( memory );
					}

					( function add( args ) {
						jQuery.each( args, function( _, arg ) {
							if ( isFunction( arg ) ) {
								if ( !options.unique || !self.has( arg ) ) {
									list.push( arg );
								}
							} else if ( arg && arg.length && toType( arg ) !== "string" ) {

								// Inspect recursively
								add( arg );
							}
						} );
					} )( arguments );

					if ( memory && !firing ) {
						fire();
					}
				}
				return this;
			},

			// Remove a callback from the list
			remove: function() {
				jQuery.each( arguments, function( _, arg ) {
					var index;
					while ( ( index = jQuery.inArray( arg, list, index ) ) > -1 ) {
						list.splice( index, 1 );

						// Handle firing indexes
						if ( index <= firingIndex ) {
							firingIndex--;
						}
					}
				} );
				return this;
			},

			// Check if a given callback is in the list.
			// If no argument is given, return whether or not list has callbacks attached.
			has: function( fn ) {
				return fn ?
					jQuery.inArray( fn, list ) > -1 :
					list.length > 0;
			},

			// Remove all callbacks from the list
			empty: function() {
				if ( list ) {
					list = [];
				}
				return this;
			},

			// Disable .fire and .add
			// Abort any current/pending executions
			// Clear all callbacks and values
			disable: function() {
				locked = queue = [];
				list = memory = "";
				return this;
			},
			disabled: function() {
				return !list;
			},

			// Disable .fire
			// Also disable .add unless we have memory (since it would have no effect)
			// Abort any pending executions
			lock: function() {
				locked = queue = [];
				if ( !memory && !firing ) {
					list = memory = "";
				}
				return this;
			},
			locked: function() {
				return !!locked;
			},

			// Call all callbacks with the given context and arguments
			fireWith: function( context, args ) {
				if ( !locked ) {
					args = args || [];
					args = [ context, args.slice ? args.slice() : args ];
					queue.push( args );
					if ( !firing ) {
						fire();
					}
				}
				return this;
			},

			// Call all the callbacks with the given arguments
			fire: function() {
				self.fireWith( this, arguments );
				return this;
			},

			// To know if the callbacks have already been called at least once
			fired: function() {
				return !!fired;
			}
		};

	return self;
};


function Identity( v ) {
	return v;
}
function Thrower( ex ) {
	throw ex;
}

function adoptValue( value, resolve, reject, noValue ) {
	var method;

	try {

		// Check for promise aspect first to privilege synchronous behavior
		if ( value && isFunction( ( method = value.promise ) ) ) {
			method.call( value ).done( resolve ).fail( reject );

		// Other thenables
		} else if ( value && isFunction( ( method = value.then ) ) ) {
			method.call( value, resolve, reject );

		// Other non-thenables
		} else {

			// Control `resolve` arguments by letting Array#slice cast boolean `noValue` to integer:
			// * false: [ value ].slice( 0 ) => resolve( value )
			// * true: [ value ].slice( 1 ) => resolve()
			resolve.apply( undefined, [ value ].slice( noValue ) );
		}

	// For Promises/A+, convert exceptions into rejections
	// Since jQuery.when doesn't unwrap thenables, we can skip the extra checks appearing in
	// Deferred#then to conditionally suppress rejection.
	} catch ( value ) {

		// Support: Android 4.0 only
		// Strict mode functions invoked without .call/.apply get global-object context
		reject.apply( undefined, [ value ] );
	}
}

jQuery.extend( {

	Deferred: function( func ) {
		var tuples = [

				// action, add listener, callbacks,
				// ... .then handlers, argument index, [final state]
				[ "notify", "progress", jQuery.Callbacks( "memory" ),
					jQuery.Callbacks( "memory" ), 2 ],
				[ "resolve", "done", jQuery.Callbacks( "once memory" ),
					jQuery.Callbacks( "once memory" ), 0, "resolved" ],
				[ "reject", "fail", jQuery.Callbacks( "once memory" ),
					jQuery.Callbacks( "once memory" ), 1, "rejected" ]
			],
			state = "pending",
			promise = {
				state: function() {
					return state;
				},
				always: function() {
					deferred.done( arguments ).fail( arguments );
					return this;
				},
				"catch": function( fn ) {
					return promise.then( null, fn );
				},

				// Keep pipe for back-compat
				pipe: function( /* fnDone, fnFail, fnProgress */ ) {
					var fns = arguments;

					return jQuery.Deferred( function( newDefer ) {
						jQuery.each( tuples, function( _i, tuple ) {

							// Map tuples (progress, done, fail) to arguments (done, fail, progress)
							var fn = isFunction( fns[ tuple[ 4 ] ] ) && fns[ tuple[ 4 ] ];

							// deferred.progress(function() { bind to newDefer or newDefer.notify })
							// deferred.done(function() { bind to newDefer or newDefer.resolve })
							// deferred.fail(function() { bind to newDefer or newDefer.reject })
							deferred[ tuple[ 1 ] ]( function() {
								var returned = fn && fn.apply( this, arguments );
								if ( returned && isFunction( returned.promise ) ) {
									returned.promise()
										.progress( newDefer.notify )
										.done( newDefer.resolve )
										.fail( newDefer.reject );
								} else {
									newDefer[ tuple[ 0 ] + "With" ](
										this,
										fn ? [ returned ] : arguments
									);
								}
							} );
						} );
						fns = null;
					} ).promise();
				},
				then: function( onFulfilled, onRejected, onProgress ) {
					var maxDepth = 0;
					function resolve( depth, deferred, handler, special ) {
						return function() {
							var that = this,
								args = arguments,
								mightThrow = function() {
									var returned, then;

									// Support: Promises/A+ section 2.3.3.3.3
									// https://promisesaplus.com/#point-59
									// Ignore double-resolution attempts
									if ( depth < maxDepth ) {
										return;
									}

									returned = handler.apply( that, args );

									// Support: Promises/A+ section 2.3.1
									// https://promisesaplus.com/#point-48
									if ( returned === deferred.promise() ) {
										throw new TypeError( "Thenable self-resolution" );
									}

									// Support: Promises/A+ sections 2.3.3.1, 3.5
									// https://promisesaplus.com/#point-54
									// https://promisesaplus.com/#point-75
									// Retrieve `then` only once
									then = returned &&

										// Support: Promises/A+ section 2.3.4
										// https://promisesaplus.com/#point-64
										// Only check objects and functions for thenability
										( typeof returned === "object" ||
											typeof returned === "function" ) &&
										returned.then;

									// Handle a returned thenable
									if ( isFunction( then ) ) {

										// Special processors (notify) just wait for resolution
										if ( special ) {
											then.call(
												returned,
												resolve( maxDepth, deferred, Identity, special ),
												resolve( maxDepth, deferred, Thrower, special )
											);

										// Normal processors (resolve) also hook into progress
										} else {

											// ...and disregard older resolution values
											maxDepth++;

											then.call(
												returned,
												resolve( maxDepth, deferred, Identity, special ),
												resolve( maxDepth, deferred, Thrower, special ),
												resolve( maxDepth, deferred, Identity,
													deferred.notifyWith )
											);
										}

									// Handle all other returned values
									} else {

										// Only substitute handlers pass on context
										// and multiple values (non-spec behavior)
										if ( handler !== Identity ) {
											that = undefined;
											args = [ returned ];
										}

										// Process the value(s)
										// Default process is resolve
										( special || deferred.resolveWith )( that, args );
									}
								},

								// Only normal processors (resolve) catch and reject exceptions
								process = special ?
									mightThrow :
									function() {
										try {
											mightThrow();
										} catch ( e ) {

											if ( jQuery.Deferred.exceptionHook ) {
												jQuery.Deferred.exceptionHook( e,
													process.stackTrace );
											}

											// Support: Promises/A+ section 2.3.3.3.4.1
											// https://promisesaplus.com/#point-61
											// Ignore post-resolution exceptions
											if ( depth + 1 >= maxDepth ) {

												// Only substitute handlers pass on context
												// and multiple values (non-spec behavior)
												if ( handler !== Thrower ) {
													that = undefined;
													args = [ e ];
												}

												deferred.rejectWith( that, args );
											}
										}
									};

							// Support: Promises/A+ section 2.3.3.3.1
							// https://promisesaplus.com/#point-57
							// Re-resolve promises immediately to dodge false rejection from
							// subsequent errors
							if ( depth ) {
								process();
							} else {

								// Call an optional hook to record the stack, in case of exception
								// since it's otherwise lost when execution goes async
								if ( jQuery.Deferred.getStackHook ) {
									process.stackTrace = jQuery.Deferred.getStackHook();
								}
								window.setTimeout( process );
							}
						};
					}

					return jQuery.Deferred( function( newDefer ) {

						// progress_handlers.add( ... )
						tuples[ 0 ][ 3 ].add(
							resolve(
								0,
								newDefer,
								isFunction( onProgress ) ?
									onProgress :
									Identity,
								newDefer.notifyWith
							)
						);

						// fulfilled_handlers.add( ... )
						tuples[ 1 ][ 3 ].add(
							resolve(
								0,
								newDefer,
								isFunction( onFulfilled ) ?
									onFulfilled :
									Identity
							)
						);

						// rejected_handlers.add( ... )
						tuples[ 2 ][ 3 ].add(
							resolve(
								0,
								newDefer,
								isFunction( onRejected ) ?
									onRejected :
									Thrower
							)
						);
					} ).promise();
				},

				// Get a promise for this deferred
				// If obj is provided, the promise aspect is added to the object
				promise: function( obj ) {
					return obj != null ? jQuery.extend( obj, promise ) : promise;
				}
			},
			deferred = {};

		// Add list-specific methods
		jQuery.each( tuples, function( i, tuple ) {
			var list = tuple[ 2 ],
				stateString = tuple[ 5 ];

			// promise.progress = list.add
			// promise.done = list.add
			// promise.fail = list.add
			promise[ tuple[ 1 ] ] = list.add;

			// Handle state
			if ( stateString ) {
				list.add(
					function() {

						// state = "resolved" (i.e., fulfilled)
						// state = "rejected"
						state = stateString;
					},

					// rejected_callbacks.disable
					// fulfilled_callbacks.disable
					tuples[ 3 - i ][ 2 ].disable,

					// rejected_handlers.disable
					// fulfilled_handlers.disable
					tuples[ 3 - i ][ 3 ].disable,

					// progress_callbacks.lock
					tuples[ 0 ][ 2 ].lock,

					// progress_handlers.lock
					tuples[ 0 ][ 3 ].lock
				);
			}

			// progress_handlers.fire
			// fulfilled_handlers.fire
			// rejected_handlers.fire
			list.add( tuple[ 3 ].fire );

			// deferred.notify = function() { deferred.notifyWith(...) }
			// deferred.resolve = function() { deferred.resolveWith(...) }
			// deferred.reject = function() { deferred.rejectWith(...) }
			deferred[ tuple[ 0 ] ] = function() {
				deferred[ tuple[ 0 ] + "With" ]( this === deferred ? undefined : this, arguments );
				return this;
			};

			// deferred.notifyWith = list.fireWith
			// deferred.resolveWith = list.fireWith
			// deferred.rejectWith = list.fireWith
			deferred[ tuple[ 0 ] + "With" ] = list.fireWith;
		} );

		// Make the deferred a promise
		promise.promise( deferred );

		// Call given func if any
		if ( func ) {
			func.call( deferred, deferred );
		}

		// All done!
		return deferred;
	},

	// Deferred helper
	when: function( singleValue ) {
		var

			// count of uncompleted subordinates
			remaining = arguments.length,

			// count of unprocessed arguments
			i = remaining,

			// subordinate fulfillment data
			resolveContexts = Array( i ),
			resolveValues = slice.call( arguments ),

			// the primary Deferred
			primary = jQuery.Deferred(),

			// subordinate callback factory
			updateFunc = function( i ) {
				return function( value ) {
					resolveContexts[ i ] = this;
					resolveValues[ i ] = arguments.length > 1 ? slice.call( arguments ) : value;
					if ( !( --remaining ) ) {
						primary.resolveWith( resolveContexts, resolveValues );
					}
				};
			};

		// Single- and empty arguments are adopted like Promise.resolve
		if ( remaining <= 1 ) {
			adoptValue( singleValue, primary.done( updateFunc( i ) ).resolve, primary.reject,
				!remaining );

			// Use .then() to unwrap secondary thenables (cf. gh-3000)
			if ( primary.state() === "pending" ||
				isFunction( resolveValues[ i ] && resolveValues[ i ].then ) ) {

				return primary.then();
			}
		}

		// Multiple arguments are aggregated like Promise.all array elements
		while ( i-- ) {
			adoptValue( resolveValues[ i ], updateFunc( i ), primary.reject );
		}

		return primary.promise();
	}
} );


// These usually indicate a programmer mistake during development,
// warn about them ASAP rather than swallowing them by default.
var rerrorNames = /^(Eval|Internal|Range|Reference|Syntax|Type|URI)Error$/;

jQuery.Deferred.exceptionHook = function( error, stack ) {

	// Support: IE 8 - 9 only
	// Console exists when dev tools are open, which can happen at any time
	if ( window.console && window.console.warn && error && rerrorNames.test( error.name ) ) {
		window.console.warn( "jQuery.Deferred exception: " + error.message, error.stack, stack );
	}
};




jQuery.readyException = function( error ) {
	window.setTimeout( function() {
		throw error;
	} );
};




// The deferred used on DOM ready
var readyList = jQuery.Deferred();

jQuery.fn.ready = function( fn ) {

	readyList
		.then( fn )

		// Wrap jQuery.readyException in a function so that the lookup
		// happens at the time of error handling instead of callback
		// registration.
		.catch( function( error ) {
			jQuery.readyException( error );
		} );

	return this;
};

jQuery.extend( {

	// Is the DOM ready to be used? Set to true once it occurs.
	isReady: false,

	// A counter to track how many items to wait for before
	// the ready event fires. See #6781
	readyWait: 1,

	// Handle when the DOM is ready
	ready: function( wait ) {

		// Abort if there are pending holds or we're already ready
		if ( wait === true ? --jQuery.readyWait : jQuery.isReady ) {
			return;
		}

		// Remember that the DOM is ready
		jQuery.isReady = true;

		// If a normal DOM Ready event fired, decrement, and wait if need be
		if ( wait !== true && --jQuery.readyWait > 0 ) {
			return;
		}

		// If there are functions bound, to execute
		readyList.resolveWith( document, [ jQuery ] );
	}
} );

jQuery.ready.then = readyList.then;

// The ready event handler and self cleanup method
function completed() {
	document.removeEventListener( "DOMContentLoaded", completed );
	window.removeEventListener( "load", completed );
	jQuery.ready();
}

// Catch cases where $(document).ready() is called
// after the browser event has already occurred.
// Support: IE <=9 - 10 only
// Older IE sometimes signals "interactive" too soon
if ( document.readyState === "complete" ||
	( document.readyState !== "loading" && !document.documentElement.doScroll ) ) {

	// Handle it asynchronously to allow scripts the opportunity to delay ready
	window.setTimeout( jQuery.ready );

} else {

	// Use the handy event callback
	document.addEventListener( "DOMContentLoaded", completed );

	// A fallback to window.onload, that will always work
	window.addEventListener( "load", completed );
}




// Multifunctional method to get and set values of a collection
// The value/s can optionally be executed if it's a function
var access = function( elems, fn, key, value, chainable, emptyGet, raw ) {
	var i = 0,
		len = elems.length,
		bulk = key == null;

	// Sets many values
	if ( toType( key ) === "object" ) {
		chainable = true;
		for ( i in key ) {
			access( elems, fn, i, key[ i ], true, emptyGet, raw );
		}

	// Sets one value
	} else if ( value !== undefined ) {
		chainable = true;

		if ( !isFunction( value ) ) {
			raw = true;
		}

		if ( bulk ) {

			// Bulk operations run against the entire set
			if ( raw ) {
				fn.call( elems, value );
				fn = null;

			// ...except when executing function values
			} else {
				bulk = fn;
				fn = function( elem, _key, value ) {
					return bulk.call( jQuery( elem ), value );
				};
			}
		}

		if ( fn ) {
			for ( ; i < len; i++ ) {
				fn(
					elems[ i ], key, raw ?
						value :
						value.call( elems[ i ], i, fn( elems[ i ], key ) )
				);
			}
		}
	}

	if ( chainable ) {
		return elems;
	}

	// Gets
	if ( bulk ) {
		return fn.call( elems );
	}

	return len ? fn( elems[ 0 ], key ) : emptyGet;
};


// Matches dashed string for camelizing
var rmsPrefix = /^-ms-/,
	rdashAlpha = /-([a-z])/g;

// Used by camelCase as callback to replace()
function fcamelCase( _all, letter ) {
	return letter.toUpperCase();
}

// Convert dashed to camelCase; used by the css and data modules
// Support: IE <=9 - 11, Edge 12 - 15
// Microsoft forgot to hump their vendor prefix (#9572)
function camelCase( string ) {
	return string.replace( rmsPrefix, "ms-" ).replace( rdashAlpha, fcamelCase );
}
var acceptData = function( owner ) {

	// Accepts only:
	//  - Node
	//    - Node.ELEMENT_NODE
	//    - Node.DOCUMENT_NODE
	//  - Object
	//    - Any
	return owner.nodeType === 1 || owner.nodeType === 9 || !( +owner.nodeType );
};




function Data() {
	this.expando = jQuery.expando + Data.uid++;
}

Data.uid = 1;

Data.prototype = {

	cache: function( owner ) {

		// Check if the owner object already has a cache
		var value = owner[ this.expando ];

		// If not, create one
		if ( !value ) {
			value = {};

			// We can accept data for non-element nodes in modern browsers,
			// but we should not, see #8335.
			// Always return an empty object.
			if ( acceptData( owner ) ) {

				// If it is a node unlikely to be stringify-ed or looped over
				// use plain assignment
				if ( owner.nodeType ) {
					owner[ this.expando ] = value;

				// Otherwise secure it in a non-enumerable property
				// configurable must be true to allow the property to be
				// deleted when data is removed
				} else {
					Object.defineProperty( owner, this.expando, {
						value: value,
						configurable: true
					} );
				}
			}
		}

		return value;
	},
	set: function( owner, data, value ) {
		var prop,
			cache = this.cache( owner );

		// Handle: [ owner, key, value ] args
		// Always use camelCase key (gh-2257)
		if ( typeof data === "string" ) {
			cache[ camelCase( data ) ] = value;

		// Handle: [ owner, { properties } ] args
		} else {

			// Copy the properties one-by-one to the cache object
			for ( prop in data ) {
				cache[ camelCase( prop ) ] = data[ prop ];
			}
		}
		return cache;
	},
	get: function( owner, key ) {
		return key === undefined ?
			this.cache( owner ) :

			// Always use camelCase key (gh-2257)
			owner[ this.expando ] && owner[ this.expando ][ camelCase( key ) ];
	},
	access: function( owner, key, value ) {

		// In cases where either:
		//
		//   1. No key was specified
		//   2. A string key was specified, but no value provided
		//
		// Take the "read" path and allow the get method to determine
		// which value to return, respectively either:
		//
		//   1. The entire cache object
		//   2. The data stored at the key
		//
		if ( key === undefined ||
				( ( key && typeof key === "string" ) && value === undefined ) ) {

			return this.get( owner, key );
		}

		// When the key is not a string, or both a key and value
		// are specified, set or extend (existing objects) with either:
		//
		//   1. An object of properties
		//   2. A key and value
		//
		this.set( owner, key, value );

		// Since the "set" path can have two possible entry points
		// return the expected data based on which path was taken[*]
		return value !== undefined ? value : key;
	},
	remove: function( owner, key ) {
		var i,
			cache = owner[ this.expando ];

		if ( cache === undefined ) {
			return;
		}

		if ( key !== undefined ) {

			// Support array or space separated string of keys
			if ( Array.isArray( key ) ) {

				// If key is an array of keys...
				// We always set camelCase keys, so remove that.
				key = key.map( camelCase );
			} else {
				key = camelCase( key );

				// If a key with the spaces exists, use it.
				// Otherwise, create an array by matching non-whitespace
				key = key in cache ?
					[ key ] :
					( key.match( rnothtmlwhite ) || [] );
			}

			i = key.length;

			while ( i-- ) {
				delete cache[ key[ i ] ];
			}
		}

		// Remove the expando if there's no more data
		if ( key === undefined || jQuery.isEmptyObject( cache ) ) {

			// Support: Chrome <=35 - 45
			// Webkit & Blink performance suffers when deleting properties
			// from DOM nodes, so set to undefined instead
			// https://bugs.chromium.org/p/chromium/issues/detail?id=378607 (bug restricted)
			if ( owner.nodeType ) {
				owner[ this.expando ] = undefined;
			} else {
				delete owner[ this.expando ];
			}
		}
	},
	hasData: function( owner ) {
		var cache = owner[ this.expando ];
		return cache !== undefined && !jQuery.isEmptyObject( cache );
	}
};
var dataPriv = new Data();

var dataUser = new Data();



//	Implementation Summary
//
//	1. Enforce API surface and semantic compatibility with 1.9.x branch
//	2. Improve the module's maintainability by reducing the storage
//		paths to a single mechanism.
//	3. Use the same single mechanism to support "private" and "user" data.
//	4. _Never_ expose "private" data to user code (TODO: Drop _data, _removeData)
//	5. Avoid exposing implementation details on user objects (eg. expando properties)
//	6. Provide a clear path for implementation upgrade to WeakMap in 2014

var rbrace = /^(?:\{[\w\W]*\}|\[[\w\W]*\])$/,
	rmultiDash = /[A-Z]/g;

function getData( data ) {
	if ( data === "true" ) {
		return true;
	}

	if ( data === "false" ) {
		return false;
	}

	if ( data === "null" ) {
		return null;
	}

	// Only convert to a number if it doesn't change the string
	if ( data === +data + "" ) {
		return +data;
	}

	if ( rbrace.test( data ) ) {
		return JSON.parse( data );
	}

	return data;
}

function dataAttr( elem, key, data ) {
	var name;

	// If nothing was found internally, try to fetch any
	// data from the HTML5 data-* attribute
	if ( data === undefined && elem.nodeType === 1 ) {
		name = "data-" + key.replace( rmultiDash, "-$&" ).toLowerCase();
		data = elem.getAttribute( name );

		if ( typeof data === "string" ) {
			try {
				data = getData( data );
			} catch ( e ) {}

			// Make sure we set the data so it isn't changed later
			dataUser.set( elem, key, data );
		} else {
			data = undefined;
		}
	}
	return data;
}

jQuery.extend( {
	hasData: function( elem ) {
		return dataUser.hasData( elem ) || dataPriv.hasData( elem );
	},

	data: function( elem, name, data ) {
		return dataUser.access( elem, name, data );
	},

	removeData: function( elem, name ) {
		dataUser.remove( elem, name );
	},

	// TODO: Now that all calls to _data and _removeData have been replaced
	// with direct calls to dataPriv methods, these can be deprecated.
	_data: function( elem, name, data ) {
		return dataPriv.access( elem, name, data );
	},

	_removeData: function( elem, name ) {
		dataPriv.remove( elem, name );
	}
} );

jQuery.fn.extend( {
	data: function( key, value ) {
		var i, name, data,
			elem = this[ 0 ],
			attrs = elem && elem.attributes;

		// Gets all values
		if ( key === undefined ) {
			if ( this.length ) {
				data = dataUser.get( elem );

				if ( elem.nodeType === 1 && !dataPriv.get( elem, "hasDataAttrs" ) ) {
					i = attrs.length;
					while ( i-- ) {

						// Support: IE 11 only
						// The attrs elements can be null (#14894)
						if ( attrs[ i ] ) {
							name = attrs[ i ].name;
							if ( name.indexOf( "data-" ) === 0 ) {
								name = camelCase( name.slice( 5 ) );
								dataAttr( elem, name, data[ name ] );
							}
						}
					}
					dataPriv.set( elem, "hasDataAttrs", true );
				}
			}

			return data;
		}

		// Sets multiple values
		if ( typeof key === "object" ) {
			return this.each( function() {
				dataUser.set( this, key );
			} );
		}

		return access( this, function( value ) {
			var data;

			// The calling jQuery object (element matches) is not empty
			// (and therefore has an element appears at this[ 0 ]) and the
			// `value` parameter was not undefined. An empty jQuery object
			// will result in `undefined` for elem = this[ 0 ] which will
			// throw an exception if an attempt to read a data cache is made.
			if ( elem && value === undefined ) {

				// Attempt to get data from the cache
				// The key will always be camelCased in Data
				data = dataUser.get( elem, key );
				if ( data !== undefined ) {
					return data;
				}

				// Attempt to "discover" the data in
				// HTML5 custom data-* attrs
				data = dataAttr( elem, key );
				if ( data !== undefined ) {
					return data;
				}

				// We tried really hard, but the data doesn't exist.
				return;
			}

			// Set the data...
			this.each( function() {

				// We always store the camelCased key
				dataUser.set( this, key, value );
			} );
		}, null, value, arguments.length > 1, null, true );
	},

	removeData: function( key ) {
		return this.each( function() {
			dataUser.remove( this, key );
		} );
	}
} );


jQuery.extend( {
	queue: function( elem, type, data ) {
		var queue;

		if ( elem ) {
			type = ( type || "fx" ) + "queue";
			queue = dataPriv.get( elem, type );

			// Speed up dequeue by getting out quickly if this is just a lookup
			if ( data ) {
				if ( !queue || Array.isArray( data ) ) {
					queue = dataPriv.access( elem, type, jQuery.makeArray( data ) );
				} else {
					queue.push( data );
				}
			}
			return queue || [];
		}
	},

	dequeue: function( elem, type ) {
		type = type || "fx";

		var queue = jQuery.queue( elem, type ),
			startLength = queue.length,
			fn = queue.shift(),
			hooks = jQuery._queueHooks( elem, type ),
			next = function() {
				jQuery.dequeue( elem, type );
			};

		// If the fx queue is dequeued, always remove the progress sentinel
		if ( fn === "inprogress" ) {
			fn = queue.shift();
			startLength--;
		}

		if ( fn ) {

			// Add a progress sentinel to prevent the fx queue from being
			// automatically dequeued
			if ( type === "fx" ) {
				queue.unshift( "inprogress" );
			}

			// Clear up the last queue stop function
			delete hooks.stop;
			fn.call( elem, next, hooks );
		}

		if ( !startLength && hooks ) {
			hooks.empty.fire();
		}
	},

	// Not public - generate a queueHooks object, or return the current one
	_queueHooks: function( elem, type ) {
		var key = type + "queueHooks";
		return dataPriv.get( elem, key ) || dataPriv.access( elem, key, {
			empty: jQuery.Callbacks( "once memory" ).add( function() {
				dataPriv.remove( elem, [ type + "queue", key ] );
			} )
		} );
	}
} );

jQuery.fn.extend( {
	queue: function( type, data ) {
		var setter = 2;

		if ( typeof type !== "string" ) {
			data = type;
			type = "fx";
			setter--;
		}

		if ( arguments.length < setter ) {
			return jQuery.queue( this[ 0 ], type );
		}

		return data === undefined ?
			this :
			this.each( function() {
				var queue = jQuery.queue( this, type, data );

				// Ensure a hooks for this queue
				jQuery._queueHooks( this, type );

				if ( type === "fx" && queue[ 0 ] !== "inprogress" ) {
					jQuery.dequeue( this, type );
				}
			} );
	},
	dequeue: function( type ) {
		return this.each( function() {
			jQuery.dequeue( this, type );
		} );
	},
	clearQueue: function( type ) {
		return this.queue( type || "fx", [] );
	},

	// Get a promise resolved when queues of a certain type
	// are emptied (fx is the type by default)
	promise: function( type, obj ) {
		var tmp,
			count = 1,
			defer = jQuery.Deferred(),
			elements = this,
			i = this.length,
			resolve = function() {
				if ( !( --count ) ) {
					defer.resolveWith( elements, [ elements ] );
				}
			};

		if ( typeof type !== "string" ) {
			obj = type;
			type = undefined;
		}
		type = type || "fx";

		while ( i-- ) {
			tmp = dataPriv.get( elements[ i ], type + "queueHooks" );
			if ( tmp && tmp.empty ) {
				count++;
				tmp.empty.add( resolve );
			}
		}
		resolve();
		return defer.promise( obj );
	}
} );
var pnum = ( /[+-]?(?:\d*\.|)\d+(?:[eE][+-]?\d+|)/ ).source;

var rcssNum = new RegExp( "^(?:([+-])=|)(" + pnum + ")([a-z%]*)$", "i" );


var cssExpand = [ "Top", "Right", "Bottom", "Left" ];

var documentElement = document.documentElement;



	var isAttached = function( elem ) {
			return jQuery.contains( elem.ownerDocument, elem );
		},
		composed = { composed: true };

	// Support: IE 9 - 11+, Edge 12 - 18+, iOS 10.0 - 10.2 only
	// Check attachment across shadow DOM boundaries when possible (gh-3504)
	// Support: iOS 10.0-10.2 only
	// Early iOS 10 versions support `attachShadow` but not `getRootNode`,
	// leading to errors. We need to check for `getRootNode`.
	if ( documentElement.getRootNode ) {
		isAttached = function( elem ) {
			return jQuery.contains( elem.ownerDocument, elem ) ||
				elem.getRootNode( composed ) === elem.ownerDocument;
		};
	}
var isHiddenWithinTree = function( elem, el ) {

		// isHiddenWithinTree might be called from jQuery#filter function;
		// in that case, element will be second argument
		elem = el || elem;

		// Inline style trumps all
		return elem.style.display === "none" ||
			elem.style.display === "" &&

			// Otherwise, check computed style
			// Support: Firefox <=43 - 45
			// Disconnected elements can have computed display: none, so first confirm that elem is
			// in the document.
			isAttached( elem ) &&

			jQuery.css( elem, "display" ) === "none";
	};



function adjustCSS( elem, prop, valueParts, tween ) {
	var adjusted, scale,
		maxIterations = 20,
		currentValue = tween ?
			function() {
				return tween.cur();
			} :
			function() {
				return jQuery.css( elem, prop, "" );
			},
		initial = currentValue(),
		unit = valueParts && valueParts[ 3 ] || ( jQuery.cssNumber[ prop ] ? "" : "px" ),

		// Starting value computation is required for potential unit mismatches
		initialInUnit = elem.nodeType &&
			( jQuery.cssNumber[ prop ] || unit !== "px" && +initial ) &&
			rcssNum.exec( jQuery.css( elem, prop ) );

	if ( initialInUnit && initialInUnit[ 3 ] !== unit ) {

		// Support: Firefox <=54
		// Halve the iteration target value to prevent interference from CSS upper bounds (gh-2144)
		initial = initial / 2;

		// Trust units reported by jQuery.css
		unit = unit || initialInUnit[ 3 ];

		// Iteratively approximate from a nonzero starting point
		initialInUnit = +initial || 1;

		while ( maxIterations-- ) {

			// Evaluate and update our best guess (doubling guesses that zero out).
			// Finish if the scale equals or crosses 1 (making the old*new product non-positive).
			jQuery.style( elem, prop, initialInUnit + unit );
			if ( ( 1 - scale ) * ( 1 - ( scale = currentValue() / initial || 0.5 ) ) <= 0 ) {
				maxIterations = 0;
			}
			initialInUnit = initialInUnit / scale;

		}

		initialInUnit = initialInUnit * 2;
		jQuery.style( elem, prop, initialInUnit + unit );

		// Make sure we update the tween properties later on
		valueParts = valueParts || [];
	}

	if ( valueParts ) {
		initialInUnit = +initialInUnit || +initial || 0;

		// Apply relative offset (+=/-=) if specified
		adjusted = valueParts[ 1 ] ?
			initialInUnit + ( valueParts[ 1 ] + 1 ) * valueParts[ 2 ] :
			+valueParts[ 2 ];
		if ( tween ) {
			tween.unit = unit;
			tween.start = initialInUnit;
			tween.end = adjusted;
		}
	}
	return adjusted;
}


var defaultDisplayMap = {};

function getDefaultDisplay( elem ) {
	var temp,
		doc = elem.ownerDocument,
		nodeName = elem.nodeName,
		display = defaultDisplayMap[ nodeName ];

	if ( display ) {
		return display;
	}

	temp = doc.body.appendChild( doc.createElement( nodeName ) );
	display = jQuery.css( temp, "display" );

	temp.parentNode.removeChild( temp );

	if ( display === "none" ) {
		display = "block";
	}
	defaultDisplayMap[ nodeName ] = display;

	return display;
}

function showHide( elements, show ) {
	var display, elem,
		values = [],
		index = 0,
		length = elements.length;

	// Determine new display value for elements that need to change
	for ( ; index < length; index++ ) {
		elem = elements[ index ];
		if ( !elem.style ) {
			continue;
		}

		display = elem.style.display;
		if ( show ) {

			// Since we force visibility upon cascade-hidden elements, an immediate (and slow)
			// check is required in this first loop unless we have a nonempty display value (either
			// inline or about-to-be-restored)
			if ( display === "none" ) {
				values[ index ] = dataPriv.get( elem, "display" ) || null;
				if ( !values[ index ] ) {
					elem.style.display = "";
				}
			}
			if ( elem.style.display === "" && isHiddenWithinTree( elem ) ) {
				values[ index ] = getDefaultDisplay( elem );
			}
		} else {
			if ( display !== "none" ) {
				values[ index ] = "none";

				// Remember what we're overwriting
				dataPriv.set( elem, "display", display );
			}
		}
	}

	// Set the display of the elements in a second loop to avoid constant reflow
	for ( index = 0; index < length; index++ ) {
		if ( values[ index ] != null ) {
			elements[ index ].style.display = values[ index ];
		}
	}

	return elements;
}

jQuery.fn.extend( {
	show: function() {
		return showHide( this, true );
	},
	hide: function() {
		return showHide( this );
	},
	toggle: function( state ) {
		if ( typeof state === "boolean" ) {
			return state ? this.show() : this.hide();
		}

		return this.each( function() {
			if ( isHiddenWithinTree( this ) ) {
				jQuery( this ).show();
			} else {
				jQuery( this ).hide();
			}
		} );
	}
} );
var rcheckableType = ( /^(?:checkbox|radio)$/i );

var rtagName = ( /<([a-z][^\/\0>\x20\t\r\n\f]*)/i );

var rscriptType = ( /^$|^module$|\/(?:java|ecma)script/i );



( function() {
	var fragment = document.createDocumentFragment(),
		div = fragment.appendChild( document.createElement( "div" ) ),
		input = document.createElement( "input" );

	// Support: Android 4.0 - 4.3 only
	// Check state lost if the name is set (#11217)
	// Support: Windows Web Apps (WWA)
	// `name` and `type` must use .setAttribute for WWA (#14901)
	input.setAttribute( "type", "radio" );
	input.setAttribute( "checked", "checked" );
	input.setAttribute( "name", "t" );

	div.appendChild( input );

	// Support: Android <=4.1 only
	// Older WebKit doesn't clone checked state correctly in fragments
	support.checkClone = div.cloneNode( true ).cloneNode( true ).lastChild.checked;

	// Support: IE <=11 only
	// Make sure textarea (and checkbox) defaultValue is properly cloned
	div.innerHTML = "<textarea>x</textarea>";
	support.noCloneChecked = !!div.cloneNode( true ).lastChild.defaultValue;

	// Support: IE <=9 only
	// IE <=9 replaces <option> tags with their contents when inserted outside of
	// the select element.
	div.innerHTML = "<option></option>";
	support.option = !!div.lastChild;
} )();


// We have to close these tags to support XHTML (#13200)
var wrapMap = {

	// XHTML parsers do not magically insert elements in the
	// same way that tag soup parsers do. So we cannot shorten
	// this by omitting <tbody> or other required elements.
	thead: [ 1, "<table>", "</table>" ],
	col: [ 2, "<table><colgroup>", "</colgroup></table>" ],
	tr: [ 2, "<table><tbody>", "</tbody></table>" ],
	td: [ 3, "<table><tbody><tr>", "</tr></tbody></table>" ],

	_default: [ 0, "", "" ]
};

wrapMap.tbody = wrapMap.tfoot = wrapMap.colgroup = wrapMap.caption = wrapMap.thead;
wrapMap.th = wrapMap.td;

// Support: IE <=9 only
if ( !support.option ) {
	wrapMap.optgroup = wrapMap.option = [ 1, "<select multiple='multiple'>", "</select>" ];
}


function getAll( context, tag ) {

	// Support: IE <=9 - 11 only
	// Use typeof to avoid zero-argument method invocation on host objects (#15151)
	var ret;

	if ( typeof context.getElementsByTagName !== "undefined" ) {
		ret = context.getElementsByTagName( tag || "*" );

	} else if ( typeof context.querySelectorAll !== "undefined" ) {
		ret = context.querySelectorAll( tag || "*" );

	} else {
		ret = [];
	}

	if ( tag === undefined || tag && nodeName( context, tag ) ) {
		return jQuery.merge( [ context ], ret );
	}

	return ret;
}


// Mark scripts as having already been evaluated
function setGlobalEval( elems, refElements ) {
	var i = 0,
		l = elems.length;

	for ( ; i < l; i++ ) {
		dataPriv.set(
			elems[ i ],
			"globalEval",
			!refElements || dataPriv.get( refElements[ i ], "globalEval" )
		);
	}
}


var rhtml = /<|&#?\w+;/;

function buildFragment( elems, context, scripts, selection, ignored ) {
	var elem, tmp, tag, wrap, attached, j,
		fragment = context.createDocumentFragment(),
		nodes = [],
		i = 0,
		l = elems.length;

	for ( ; i < l; i++ ) {
		elem = elems[ i ];

		if ( elem || elem === 0 ) {

			// Add nodes directly
			if ( toType( elem ) === "object" ) {

				// Support: Android <=4.0 only, PhantomJS 1 only
				// push.apply(_, arraylike) throws on ancient WebKit
				jQuery.merge( nodes, elem.nodeType ? [ elem ] : elem );

			// Convert non-html into a text node
			} else if ( !rhtml.test( elem ) ) {
				nodes.push( context.createTextNode( elem ) );

			// Convert html into DOM nodes
			} else {
				tmp = tmp || fragment.appendChild( context.createElement( "div" ) );

				// Deserialize a standard representation
				tag = ( rtagName.exec( elem ) || [ "", "" ] )[ 1 ].toLowerCase();
				wrap = wrapMap[ tag ] || wrapMap._default;
				tmp.innerHTML = wrap[ 1 ] + jQuery.htmlPrefilter( elem ) + wrap[ 2 ];

				// Descend through wrappers to the right content
				j = wrap[ 0 ];
				while ( j-- ) {
					tmp = tmp.lastChild;
				}

				// Support: Android <=4.0 only, PhantomJS 1 only
				// push.apply(_, arraylike) throws on ancient WebKit
				jQuery.merge( nodes, tmp.childNodes );

				// Remember the top-level container
				tmp = fragment.firstChild;

				// Ensure the created nodes are orphaned (#12392)
				tmp.textContent = "";
			}
		}
	}

	// Remove wrapper from fragment
	fragment.textContent = "";

	i = 0;
	while ( ( elem = nodes[ i++ ] ) ) {

		// Skip elements already in the context collection (trac-4087)
		if ( selection && jQuery.inArray( elem, selection ) > -1 ) {
			if ( ignored ) {
				ignored.push( elem );
			}
			continue;
		}

		attached = isAttached( elem );

		// Append to fragment
		tmp = getAll( fragment.appendChild( elem ), "script" );

		// Preserve script evaluation history
		if ( attached ) {
			setGlobalEval( tmp );
		}

		// Capture executables
		if ( scripts ) {
			j = 0;
			while ( ( elem = tmp[ j++ ] ) ) {
				if ( rscriptType.test( elem.type || "" ) ) {
					scripts.push( elem );
				}
			}
		}
	}

	return fragment;
}


var rtypenamespace = /^([^.]*)(?:\.(.+)|)/;

function returnTrue() {
	return true;
}

function returnFalse() {
	return false;
}

// Support: IE <=9 - 11+
// focus() and blur() are asynchronous, except when they are no-op.
// So expect focus to be synchronous when the element is already active,
// and blur to be synchronous when the element is not already active.
// (focus and blur are always synchronous in other supported browsers,
// this just defines when we can count on it).
function expectSync( elem, type ) {
	return ( elem === safeActiveElement() ) === ( type === "focus" );
}

// Support: IE <=9 only
// Accessing document.activeElement can throw unexpectedly
// https://bugs.jquery.com/ticket/13393
function safeActiveElement() {
	try {
		return document.activeElement;
	} catch ( err ) { }
}

function on( elem, types, selector, data, fn, one ) {
	var origFn, type;

	// Types can be a map of types/handlers
	if ( typeof types === "object" ) {

		// ( types-Object, selector, data )
		if ( typeof selector !== "string" ) {

			// ( types-Object, data )
			data = data || selector;
			selector = undefined;
		}
		for ( type in types ) {
			on( elem, type, selector, data, types[ type ], one );
		}
		return elem;
	}

	if ( data == null && fn == null ) {

		// ( types, fn )
		fn = selector;
		data = selector = undefined;
	} else if ( fn == null ) {
		if ( typeof selector === "string" ) {

			// ( types, selector, fn )
			fn = data;
			data = undefined;
		} else {

			// ( types, data, fn )
			fn = data;
			data = selector;
			selector = undefined;
		}
	}
	if ( fn === false ) {
		fn = returnFalse;
	} else if ( !fn ) {
		return elem;
	}

	if ( one === 1 ) {
		origFn = fn;
		fn = function( event ) {

			// Can use an empty set, since event contains the info
			jQuery().off( event );
			return origFn.apply( this, arguments );
		};

		// Use same guid so caller can remove using origFn
		fn.guid = origFn.guid || ( origFn.guid = jQuery.guid++ );
	}
	return elem.each( function() {
		jQuery.event.add( this, types, fn, data, selector );
	} );
}

/*
 * Helper functions for managing events -- not part of the public interface.
 * Props to Dean Edwards' addEvent library for many of the ideas.
 */
jQuery.event = {

	global: {},

	add: function( elem, types, handler, data, selector ) {

		var handleObjIn, eventHandle, tmp,
			events, t, handleObj,
			special, handlers, type, namespaces, origType,
			elemData = dataPriv.get( elem );

		// Only attach events to objects that accept data
		if ( !acceptData( elem ) ) {
			return;
		}

		// Caller can pass in an object of custom data in lieu of the handler
		if ( handler.handler ) {
			handleObjIn = handler;
			handler = handleObjIn.handler;
			selector = handleObjIn.selector;
		}

		// Ensure that invalid selectors throw exceptions at attach time
		// Evaluate against documentElement in case elem is a non-element node (e.g., document)
		if ( selector ) {
			jQuery.find.matchesSelector( documentElement, selector );
		}

		// Make sure that the handler has a unique ID, used to find/remove it later
		if ( !handler.guid ) {
			handler.guid = jQuery.guid++;
		}

		// Init the element's event structure and main handler, if this is the first
		if ( !( events = elemData.events ) ) {
			events = elemData.events = Object.create( null );
		}
		if ( !( eventHandle = elemData.handle ) ) {
			eventHandle = elemData.handle = function( e ) {

				// Discard the second event of a jQuery.event.trigger() and
				// when an event is called after a page has unloaded
				return typeof jQuery !== "undefined" && jQuery.event.triggered !== e.type ?
					jQuery.event.dispatch.apply( elem, arguments ) : undefined;
			};
		}

		// Handle multiple events separated by a space
		types = ( types || "" ).match( rnothtmlwhite ) || [ "" ];
		t = types.length;
		while ( t-- ) {
			tmp = rtypenamespace.exec( types[ t ] ) || [];
			type = origType = tmp[ 1 ];
			namespaces = ( tmp[ 2 ] || "" ).split( "." ).sort();

			// There *must* be a type, no attaching namespace-only handlers
			if ( !type ) {
				continue;
			}

			// If event changes its type, use the special event handlers for the changed type
			special = jQuery.event.special[ type ] || {};

			// If selector defined, determine special event api type, otherwise given type
			type = ( selector ? special.delegateType : special.bindType ) || type;

			// Update special based on newly reset type
			special = jQuery.event.special[ type ] || {};

			// handleObj is passed to all event handlers
			handleObj = jQuery.extend( {
				type: type,
				origType: origType,
				data: data,
				handler: handler,
				guid: handler.guid,
				selector: selector,
				needsContext: selector && jQuery.expr.match.needsContext.test( selector ),
				namespace: namespaces.join( "." )
			}, handleObjIn );

			// Init the event handler queue if we're the first
			if ( !( handlers = events[ type ] ) ) {
				handlers = events[ type ] = [];
				handlers.delegateCount = 0;

				// Only use addEventListener if the special events handler returns false
				if ( !special.setup ||
					special.setup.call( elem, data, namespaces, eventHandle ) === false ) {

					if ( elem.addEventListener ) {
						elem.addEventListener( type, eventHandle );
					}
				}
			}

			if ( special.add ) {
				special.add.call( elem, handleObj );

				if ( !handleObj.handler.guid ) {
					handleObj.handler.guid = handler.guid;
				}
			}

			// Add to the element's handler list, delegates in front
			if ( selector ) {
				handlers.splice( handlers.delegateCount++, 0, handleObj );
			} else {
				handlers.push( handleObj );
			}

			// Keep track of which events have ever been used, for event optimization
			jQuery.event.global[ type ] = true;
		}

	},

	// Detach an event or set of events from an element
	remove: function( elem, types, handler, selector, mappedTypes ) {

		var j, origCount, tmp,
			events, t, handleObj,
			special, handlers, type, namespaces, origType,
			elemData = dataPriv.hasData( elem ) && dataPriv.get( elem );

		if ( !elemData || !( events = elemData.events ) ) {
			return;
		}

		// Once for each type.namespace in types; type may be omitted
		types = ( types || "" ).match( rnothtmlwhite ) || [ "" ];
		t = types.length;
		while ( t-- ) {
			tmp = rtypenamespace.exec( types[ t ] ) || [];
			type = origType = tmp[ 1 ];
			namespaces = ( tmp[ 2 ] || "" ).split( "." ).sort();

			// Unbind all events (on this namespace, if provided) for the element
			if ( !type ) {
				for ( type in events ) {
					jQuery.event.remove( elem, type + types[ t ], handler, selector, true );
				}
				continue;
			}

			special = jQuery.event.special[ type ] || {};
			type = ( selector ? special.delegateType : special.bindType ) || type;
			handlers = events[ type ] || [];
			tmp = tmp[ 2 ] &&
				new RegExp( "(^|\\.)" + namespaces.join( "\\.(?:.*\\.|)" ) + "(\\.|$)" );

			// Remove matching events
			origCount = j = handlers.length;
			while ( j-- ) {
				handleObj = handlers[ j ];

				if ( ( mappedTypes || origType === handleObj.origType ) &&
					( !handler || handler.guid === handleObj.guid ) &&
					( !tmp || tmp.test( handleObj.namespace ) ) &&
					( !selector || selector === handleObj.selector ||
						selector === "**" && handleObj.selector ) ) {
					handlers.splice( j, 1 );

					if ( handleObj.selector ) {
						handlers.delegateCount--;
					}
					if ( special.remove ) {
						special.remove.call( elem, handleObj );
					}
				}
			}

			// Remove generic event handler if we removed something and no more handlers exist
			// (avoids potential for endless recursion during removal of special event handlers)
			if ( origCount && !handlers.length ) {
				if ( !special.teardown ||
					special.teardown.call( elem, namespaces, elemData.handle ) === false ) {

					jQuery.removeEvent( elem, type, elemData.handle );
				}

				delete events[ type ];
			}
		}

		// Remove data and the expando if it's no longer used
		if ( jQuery.isEmptyObject( events ) ) {
			dataPriv.remove( elem, "handle events" );
		}
	},

	dispatch: function( nativeEvent ) {

		var i, j, ret, matched, handleObj, handlerQueue,
			args = new Array( arguments.length ),

			// Make a writable jQuery.Event from the native event object
			event = jQuery.event.fix( nativeEvent ),

			handlers = (
				dataPriv.get( this, "events" ) || Object.create( null )
			)[ event.type ] || [],
			special = jQuery.event.special[ event.type ] || {};

		// Use the fix-ed jQuery.Event rather than the (read-only) native event
		args[ 0 ] = event;

		for ( i = 1; i < arguments.length; i++ ) {
			args[ i ] = arguments[ i ];
		}

		event.delegateTarget = this;

		// Call the preDispatch hook for the mapped type, and let it bail if desired
		if ( special.preDispatch && special.preDispatch.call( this, event ) === false ) {
			return;
		}

		// Determine handlers
		handlerQueue = jQuery.event.handlers.call( this, event, handlers );

		// Run delegates first; they may want to stop propagation beneath us
		i = 0;
		while ( ( matched = handlerQueue[ i++ ] ) && !event.isPropagationStopped() ) {
			event.currentTarget = matched.elem;

			j = 0;
			while ( ( handleObj = matched.handlers[ j++ ] ) &&
				!event.isImmediatePropagationStopped() ) {

				// If the event is namespaced, then each handler is only invoked if it is
				// specially universal or its namespaces are a superset of the event's.
				if ( !event.rnamespace || handleObj.namespace === false ||
					event.rnamespace.test( handleObj.namespace ) ) {

					event.handleObj = handleObj;
					event.data = handleObj.data;

					ret = ( ( jQuery.event.special[ handleObj.origType ] || {} ).handle ||
						handleObj.handler ).apply( matched.elem, args );

					if ( ret !== undefined ) {
						if ( ( event.result = ret ) === false ) {
							event.preventDefault();
							event.stopPropagation();
						}
					}
				}
			}
		}

		// Call the postDispatch hook for the mapped type
		if ( special.postDispatch ) {
			special.postDispatch.call( this, event );
		}

		return event.result;
	},

	handlers: function( event, handlers ) {
		var i, handleObj, sel, matchedHandlers, matchedSelectors,
			handlerQueue = [],
			delegateCount = handlers.delegateCount,
			cur = event.target;

		// Find delegate handlers
		if ( delegateCount &&

			// Support: IE <=9
			// Black-hole SVG <use> instance trees (trac-13180)
			cur.nodeType &&

			// Support: Firefox <=42
			// Suppress spec-violating clicks indicating a non-primary pointer button (trac-3861)
			// https://www.w3.org/TR/DOM-Level-3-Events/#event-type-click
			// Support: IE 11 only
			// ...but not arrow key "clicks" of radio inputs, which can have `button` -1 (gh-2343)
			!( event.type === "click" && event.button >= 1 ) ) {

			for ( ; cur !== this; cur = cur.parentNode || this ) {

				// Don't check non-elements (#13208)
				// Don't process clicks on disabled elements (#6911, #8165, #11382, #11764)
				if ( cur.nodeType === 1 && !( event.type === "click" && cur.disabled === true ) ) {
					matchedHandlers = [];
					matchedSelectors = {};
					for ( i = 0; i < delegateCount; i++ ) {
						handleObj = handlers[ i ];

						// Don't conflict with Object.prototype properties (#13203)
						sel = handleObj.selector + " ";

						if ( matchedSelectors[ sel ] === undefined ) {
							matchedSelectors[ sel ] = handleObj.needsContext ?
								jQuery( sel, this ).index( cur ) > -1 :
								jQuery.find( sel, this, null, [ cur ] ).length;
						}
						if ( matchedSelectors[ sel ] ) {
							matchedHandlers.push( handleObj );
						}
					}
					if ( matchedHandlers.length ) {
						handlerQueue.push( { elem: cur, handlers: matchedHandlers } );
					}
				}
			}
		}

		// Add the remaining (directly-bound) handlers
		cur = this;
		if ( delegateCount < handlers.length ) {
			handlerQueue.push( { elem: cur, handlers: handlers.slice( delegateCount ) } );
		}

		return handlerQueue;
	},

	addProp: function( name, hook ) {
		Object.defineProperty( jQuery.Event.prototype, name, {
			enumerable: true,
			configurable: true,

			get: isFunction( hook ) ?
				function() {
					if ( this.originalEvent ) {
						return hook( this.originalEvent );
					}
				} :
				function() {
					if ( this.originalEvent ) {
						return this.originalEvent[ name ];
					}
				},

			set: function( value ) {
				Object.defineProperty( this, name, {
					enumerable: true,
					configurable: true,
					writable: true,
					value: value
				} );
			}
		} );
	},

	fix: function( originalEvent ) {
		return originalEvent[ jQuery.expando ] ?
			originalEvent :
			new jQuery.Event( originalEvent );
	},

	special: {
		load: {

			// Prevent triggered image.load events from bubbling to window.load
			noBubble: true
		},
		click: {

			// Utilize native event to ensure correct state for checkable inputs
			setup: function( data ) {

				// For mutual compressibility with _default, replace `this` access with a local var.
				// `|| data` is dead code meant only to preserve the variable through minification.
				var el = this || data;

				// Claim the first handler
				if ( rcheckableType.test( el.type ) &&
					el.click && nodeName( el, "input" ) ) {

					// dataPriv.set( el, "click", ... )
					leverageNative( el, "click", returnTrue );
				}

				// Return false to allow normal processing in the caller
				return false;
			},
			trigger: function( data ) {

				// For mutual compressibility with _default, replace `this` access with a local var.
				// `|| data` is dead code meant only to preserve the variable through minification.
				var el = this || data;

				// Force setup before triggering a click
				if ( rcheckableType.test( el.type ) &&
					el.click && nodeName( el, "input" ) ) {

					leverageNative( el, "click" );
				}

				// Return non-false to allow normal event-path propagation
				return true;
			},

			// For cross-browser consistency, suppress native .click() on links
			// Also prevent it if we're currently inside a leveraged native-event stack
			_default: function( event ) {
				var target = event.target;
				return rcheckableType.test( target.type ) &&
					target.click && nodeName( target, "input" ) &&
					dataPriv.get( target, "click" ) ||
					nodeName( target, "a" );
			}
		},

		beforeunload: {
			postDispatch: function( event ) {

				// Support: Firefox 20+
				// Firefox doesn't alert if the returnValue field is not set.
				if ( event.result !== undefined && event.originalEvent ) {
					event.originalEvent.returnValue = event.result;
				}
			}
		}
	}
};

// Ensure the presence of an event listener that handles manually-triggered
// synthetic events by interrupting progress until reinvoked in response to
// *native* events that it fires directly, ensuring that state changes have
// already occurred before other listeners are invoked.
function leverageNative( el, type, expectSync ) {

	// Missing expectSync indicates a trigger call, which must force setup through jQuery.event.add
	if ( !expectSync ) {
		if ( dataPriv.get( el, type ) === undefined ) {
			jQuery.event.add( el, type, returnTrue );
		}
		return;
	}

	// Register the controller as a special universal handler for all event namespaces
	dataPriv.set( el, type, false );
	jQuery.event.add( el, type, {
		namespace: false,
		handler: function( event ) {
			var notAsync, result,
				saved = dataPriv.get( this, type );

			if ( ( event.isTrigger & 1 ) && this[ type ] ) {

				// Interrupt processing of the outer synthetic .trigger()ed event
				// Saved data should be false in such cases, but might be a leftover capture object
				// from an async native handler (gh-4350)
				if ( !saved.length ) {

					// Store arguments for use when handling the inner native event
					// There will always be at least one argument (an event object), so this array
					// will not be confused with a leftover capture object.
					saved = slice.call( arguments );
					dataPriv.set( this, type, saved );

					// Trigger the native event and capture its result
					// Support: IE <=9 - 11+
					// focus() and blur() are asynchronous
					notAsync = expectSync( this, type );
					this[ type ]();
					result = dataPriv.get( this, type );
					if ( saved !== result || notAsync ) {
						dataPriv.set( this, type, false );
					} else {
						result = {};
					}
					if ( saved !== result ) {

						// Cancel the outer synthetic event
						event.stopImmediatePropagation();
						event.preventDefault();

						// Support: Chrome 86+
						// In Chrome, if an element having a focusout handler is blurred by
						// clicking outside of it, it invokes the handler synchronously. If
						// that handler calls `.remove()` on the element, the data is cleared,
						// leaving `result` undefined. We need to guard against this.
						return result && result.value;
					}

				// If this is an inner synthetic event for an event with a bubbling surrogate
				// (focus or blur), assume that the surrogate already propagated from triggering the
				// native event and prevent that from happening again here.
				// This technically gets the ordering wrong w.r.t. to `.trigger()` (in which the
				// bubbling surrogate propagates *after* the non-bubbling base), but that seems
				// less bad than duplication.
				} else if ( ( jQuery.event.special[ type ] || {} ).delegateType ) {
					event.stopPropagation();
				}

			// If this is a native event triggered above, everything is now in order
			// Fire an inner synthetic event with the original arguments
			} else if ( saved.length ) {

				// ...and capture the result
				dataPriv.set( this, type, {
					value: jQuery.event.trigger(

						// Support: IE <=9 - 11+
						// Extend with the prototype to reset the above stopImmediatePropagation()
						jQuery.extend( saved[ 0 ], jQuery.Event.prototype ),
						saved.slice( 1 ),
						this
					)
				} );

				// Abort handling of the native event
				event.stopImmediatePropagation();
			}
		}
	} );
}

jQuery.removeEvent = function( elem, type, handle ) {

	// This "if" is needed for plain objects
	if ( elem.removeEventListener ) {
		elem.removeEventListener( type, handle );
	}
};

jQuery.Event = function( src, props ) {

	// Allow instantiation without the 'new' keyword
	if ( !( this instanceof jQuery.Event ) ) {
		return new jQuery.Event( src, props );
	}

	// Event object
	if ( src && src.type ) {
		this.originalEvent = src;
		this.type = src.type;

		// Events bubbling up the document may have been marked as prevented
		// by a handler lower down the tree; reflect the correct value.
		this.isDefaultPrevented = src.defaultPrevented ||
				src.defaultPrevented === undefined &&

				// Support: Android <=2.3 only
				src.returnValue === false ?
			returnTrue :
			returnFalse;

		// Create target properties
		// Support: Safari <=6 - 7 only
		// Target should not be a text node (#504, #13143)
		this.target = ( src.target && src.target.nodeType === 3 ) ?
			src.target.parentNode :
			src.target;

		this.currentTarget = src.currentTarget;
		this.relatedTarget = src.relatedTarget;

	// Event type
	} else {
		this.type = src;
	}

	// Put explicitly provided properties onto the event object
	if ( props ) {
		jQuery.extend( this, props );
	}

	// Create a timestamp if incoming event doesn't have one
	this.timeStamp = src && src.timeStamp || Date.now();

	// Mark it as fixed
	this[ jQuery.expando ] = true;
};

// jQuery.Event is based on DOM3 Events as specified by the ECMAScript Language Binding
// https://www.w3.org/TR/2003/WD-DOM-Level-3-Events-20030331/ecma-script-binding.html
jQuery.Event.prototype = {
	constructor: jQuery.Event,
	isDefaultPrevented: returnFalse,
	isPropagationStopped: returnFalse,
	isImmediatePropagationStopped: returnFalse,
	isSimulated: false,

	preventDefault: function() {
		var e = this.originalEvent;

		this.isDefaultPrevented = returnTrue;

		if ( e && !this.isSimulated ) {
			e.preventDefault();
		}
	},
	stopPropagation: function() {
		var e = this.originalEvent;

		this.isPropagationStopped = returnTrue;

		if ( e && !this.isSimulated ) {
			e.stopPropagation();
		}
	},
	stopImmediatePropagation: function() {
		var e = this.originalEvent;

		this.isImmediatePropagationStopped = returnTrue;

		if ( e && !this.isSimulated ) {
			e.stopImmediatePropagation();
		}

		this.stopPropagation();
	}
};

// Includes all common event props including KeyEvent and MouseEvent specific props
jQuery.each( {
	altKey: true,
	bubbles: true,
	cancelable: true,
	changedTouches: true,
	ctrlKey: true,
	detail: true,
	eventPhase: true,
	metaKey: true,
	pageX: true,
	pageY: true,
	shiftKey: true,
	view: true,
	"char": true,
	code: true,
	charCode: true,
	key: true,
	keyCode: true,
	button: true,
	buttons: true,
	clientX: true,
	clientY: true,
	offsetX: true,
	offsetY: true,
	pointerId: true,
	pointerType: true,
	screenX: true,
	screenY: true,
	targetTouches: true,
	toElement: true,
	touches: true,
	which: true
}, jQuery.event.addProp );

jQuery.each( { focus: "focusin", blur: "focusout" }, function( type, delegateType ) {
	jQuery.event.special[ type ] = {

		// Utilize native event if possible so blur/focus sequence is correct
		setup: function() {

			// Claim the first handler
			// dataPriv.set( this, "focus", ... )
			// dataPriv.set( this, "blur", ... )
			leverageNative( this, type, expectSync );

			// Return false to allow normal processing in the caller
			return false;
		},
		trigger: function() {

			// Force setup before trigger
			leverageNative( this, type );

			// Return non-false to allow normal event-path propagation
			return true;
		},

		// Suppress native focus or blur as it's already being fired
		// in leverageNative.
		_default: function() {
			return true;
		},

		delegateType: delegateType
	};
} );

// Create mouseenter/leave events using mouseover/out and event-time checks
// so that event delegation works in jQuery.
// Do the same for pointerenter/pointerleave and pointerover/pointerout
//
// Support: Safari 7 only
// Safari sends mouseenter too often; see:
// https://bugs.chromium.org/p/chromium/issues/detail?id=470258
// for the description of the bug (it existed in older Chrome versions as well).
jQuery.each( {
	mouseenter: "mouseover",
	mouseleave: "mouseout",
	pointerenter: "pointerover",
	pointerleave: "pointerout"
}, function( orig, fix ) {
	jQuery.event.special[ orig ] = {
		delegateType: fix,
		bindType: fix,

		handle: function( event ) {
			var ret,
				target = this,
				related = event.relatedTarget,
				handleObj = event.handleObj;

			// For mouseenter/leave call the handler if related is outside the target.
			// NB: No relatedTarget if the mouse left/entered the browser window
			if ( !related || ( related !== target && !jQuery.contains( target, related ) ) ) {
				event.type = handleObj.origType;
				ret = handleObj.handler.apply( this, arguments );
				event.type = fix;
			}
			return ret;
		}
	};
} );

jQuery.fn.extend( {

	on: function( types, selector, data, fn ) {
		return on( this, types, selector, data, fn );
	},
	one: function( types, selector, data, fn ) {
		return on( this, types, selector, data, fn, 1 );
	},
	off: function( types, selector, fn ) {
		var handleObj, type;
		if ( types && types.preventDefault && types.handleObj ) {

			// ( event )  dispatched jQuery.Event
			handleObj = types.handleObj;
			jQuery( types.delegateTarget ).off(
				handleObj.namespace ?
					handleObj.origType + "." + handleObj.namespace :
					handleObj.origType,
				handleObj.selector,
				handleObj.handler
			);
			return this;
		}
		if ( typeof types === "object" ) {

			// ( types-object [, selector] )
			for ( type in types ) {
				this.off( type, selector, types[ type ] );
			}
			return this;
		}
		if ( selector === false || typeof selector === "function" ) {

			// ( types [, fn] )
			fn = selector;
			selector = undefined;
		}
		if ( fn === false ) {
			fn = returnFalse;
		}
		return this.each( function() {
			jQuery.event.remove( this, types, fn, selector );
		} );
	}
} );


var

	// Support: IE <=10 - 11, Edge 12 - 13 only
	// In IE/Edge using regex groups here causes severe slowdowns.
	// See https://connect.microsoft.com/IE/feedback/details/1736512/
	rnoInnerhtml = /<script|<style|<link/i,

	// checked="checked" or checked
	rchecked = /checked\s*(?:[^=]|=\s*.checked.)/i,
	rcleanScript = /^\s*<!(?:\[CDATA\[|--)|(?:\]\]|--)>\s*$/g;

// Prefer a tbody over its parent table for containing new rows
function manipulationTarget( elem, content ) {
	if ( nodeName( elem, "table" ) &&
		nodeName( content.nodeType !== 11 ? content : content.firstChild, "tr" ) ) {

		return jQuery( elem ).children( "tbody" )[ 0 ] || elem;
	}

	return elem;
}

// Replace/restore the type attribute of script elements for safe DOM manipulation
function disableScript( elem ) {
	elem.type = ( elem.getAttribute( "type" ) !== null ) + "/" + elem.type;
	return elem;
}
function restoreScript( elem ) {
	if ( ( elem.type || "" ).slice( 0, 5 ) === "true/" ) {
		elem.type = elem.type.slice( 5 );
	} else {
		elem.removeAttribute( "type" );
	}

	return elem;
}

function cloneCopyEvent( src, dest ) {
	var i, l, type, pdataOld, udataOld, udataCur, events;

	if ( dest.nodeType !== 1 ) {
		return;
	}

	// 1. Copy private data: events, handlers, etc.
	if ( dataPriv.hasData( src ) ) {
		pdataOld = dataPriv.get( src );
		events = pdataOld.events;

		if ( events ) {
			dataPriv.remove( dest, "handle events" );

			for ( type in events ) {
				for ( i = 0, l = events[ type ].length; i < l; i++ ) {
					jQuery.event.add( dest, type, events[ type ][ i ] );
				}
			}
		}
	}

	// 2. Copy user data
	if ( dataUser.hasData( src ) ) {
		udataOld = dataUser.access( src );
		udataCur = jQuery.extend( {}, udataOld );

		dataUser.set( dest, udataCur );
	}
}

// Fix IE bugs, see support tests
function fixInput( src, dest ) {
	var nodeName = dest.nodeName.toLowerCase();

	// Fails to persist the checked state of a cloned checkbox or radio button.
	if ( nodeName === "input" && rcheckableType.test( src.type ) ) {
		dest.checked = src.checked;

	// Fails to return the selected option to the default selected state when cloning options
	} else if ( nodeName === "input" || nodeName === "textarea" ) {
		dest.defaultValue = src.defaultValue;
	}
}

function domManip( collection, args, callback, ignored ) {

	// Flatten any nested arrays
	args = flat( args );

	var fragment, first, scripts, hasScripts, node, doc,
		i = 0,
		l = collection.length,
		iNoClone = l - 1,
		value = args[ 0 ],
		valueIsFunction = isFunction( value );

	// We can't cloneNode fragments that contain checked, in WebKit
	if ( valueIsFunction ||
			( l > 1 && typeof value === "string" &&
				!support.checkClone && rchecked.test( value ) ) ) {
		return collection.each( function( index ) {
			var self = collection.eq( index );
			if ( valueIsFunction ) {
				args[ 0 ] = value.call( this, index, self.html() );
			}
			domManip( self, args, callback, ignored );
		} );
	}

	if ( l ) {
		fragment = buildFragment( args, collection[ 0 ].ownerDocument, false, collection, ignored );
		first = fragment.firstChild;

		if ( fragment.childNodes.length === 1 ) {
			fragment = first;
		}

		// Require either new content or an interest in ignored elements to invoke the callback
		if ( first || ignored ) {
			scripts = jQuery.map( getAll( fragment, "script" ), disableScript );
			hasScripts = scripts.length;

			// Use the original fragment for the last item
			// instead of the first because it can end up
			// being emptied incorrectly in certain situations (#8070).
			for ( ; i < l; i++ ) {
				node = fragment;

				if ( i !== iNoClone ) {
					node = jQuery.clone( node, true, true );

					// Keep references to cloned scripts for later restoration
					if ( hasScripts ) {

						// Support: Android <=4.0 only, PhantomJS 1 only
						// push.apply(_, arraylike) throws on ancient WebKit
						jQuery.merge( scripts, getAll( node, "script" ) );
					}
				}

				callback.call( collection[ i ], node, i );
			}

			if ( hasScripts ) {
				doc = scripts[ scripts.length - 1 ].ownerDocument;

				// Reenable scripts
				jQuery.map( scripts, restoreScript );

				// Evaluate executable scripts on first document insertion
				for ( i = 0; i < hasScripts; i++ ) {
					node = scripts[ i ];
					if ( rscriptType.test( node.type || "" ) &&
						!dataPriv.access( node, "globalEval" ) &&
						jQuery.contains( doc, node ) ) {

						if ( node.src && ( node.type || "" ).toLowerCase()  !== "module" ) {

							// Optional AJAX dependency, but won't run scripts if not present
							if ( jQuery._evalUrl && !node.noModule ) {
								jQuery._evalUrl( node.src, {
									nonce: node.nonce || node.getAttribute( "nonce" )
								}, doc );
							}
						} else {
							DOMEval( node.textContent.replace( rcleanScript, "" ), node, doc );
						}
					}
				}
			}
		}
	}

	return collection;
}

function remove( elem, selector, keepData ) {
	var node,
		nodes = selector ? jQuery.filter( selector, elem ) : elem,
		i = 0;

	for ( ; ( node = nodes[ i ] ) != null; i++ ) {
		if ( !keepData && node.nodeType === 1 ) {
			jQuery.cleanData( getAll( node ) );
		}

		if ( node.parentNode ) {
			if ( keepData && isAttached( node ) ) {
				setGlobalEval( getAll( node, "script" ) );
			}
			node.parentNode.removeChild( node );
		}
	}

	return elem;
}

jQuery.extend( {
	htmlPrefilter: function( html ) {
		return html;
	},

	clone: function( elem, dataAndEvents, deepDataAndEvents ) {
		var i, l, srcElements, destElements,
			clone = elem.cloneNode( true ),
			inPage = isAttached( elem );

		// Fix IE cloning issues
		if ( !support.noCloneChecked && ( elem.nodeType === 1 || elem.nodeType === 11 ) &&
				!jQuery.isXMLDoc( elem ) ) {

			// We eschew Sizzle here for performance reasons: https://jsperf.com/getall-vs-sizzle/2
			destElements = getAll( clone );
			srcElements = getAll( elem );

			for ( i = 0, l = srcElements.length; i < l; i++ ) {
				fixInput( srcElements[ i ], destElements[ i ] );
			}
		}

		// Copy the events from the original to the clone
		if ( dataAndEvents ) {
			if ( deepDataAndEvents ) {
				srcElements = srcElements || getAll( elem );
				destElements = destElements || getAll( clone );

				for ( i = 0, l = srcElements.length; i < l; i++ ) {
					cloneCopyEvent( srcElements[ i ], destElements[ i ] );
				}
			} else {
				cloneCopyEvent( elem, clone );
			}
		}

		// Preserve script evaluation history
		destElements = getAll( clone, "script" );
		if ( destElements.length > 0 ) {
			setGlobalEval( destElements, !inPage && getAll( elem, "script" ) );
		}

		// Return the cloned set
		return clone;
	},

	cleanData: function( elems ) {
		var data, elem, type,
			special = jQuery.event.special,
			i = 0;

		for ( ; ( elem = elems[ i ] ) !== undefined; i++ ) {
			if ( acceptData( elem ) ) {
				if ( ( data = elem[ dataPriv.expando ] ) ) {
					if ( data.events ) {
						for ( type in data.events ) {
							if ( special[ type ] ) {
								jQuery.event.remove( elem, type );

							// This is a shortcut to avoid jQuery.event.remove's overhead
							} else {
								jQuery.removeEvent( elem, type, data.handle );
							}
						}
					}

					// Support: Chrome <=35 - 45+
					// Assign undefined instead of using delete, see Data#remove
					elem[ dataPriv.expando ] = undefined;
				}
				if ( elem[ dataUser.expando ] ) {

					// Support: Chrome <=35 - 45+
					// Assign undefined instead of using delete, see Data#remove
					elem[ dataUser.expando ] = undefined;
				}
			}
		}
	}
} );

jQuery.fn.extend( {
	detach: function( selector ) {
		return remove( this, selector, true );
	},

	remove: function( selector ) {
		return remove( this, selector );
	},

	text: function( value ) {
		return access( this, function( value ) {
			return value === undefined ?
				jQuery.text( this ) :
				this.empty().each( function() {
					if ( this.nodeType === 1 || this.nodeType === 11 || this.nodeType === 9 ) {
						this.textContent = value;
					}
				} );
		}, null, value, arguments.length );
	},

	append: function() {
		return domManip( this, arguments, function( elem ) {
			if ( this.nodeType === 1 || this.nodeType === 11 || this.nodeType === 9 ) {
				var target = manipulationTarget( this, elem );
				target.appendChild( elem );
			}
		} );
	},

	prepend: function() {
		return domManip( this, arguments, function( elem ) {
			if ( this.nodeType === 1 || this.nodeType === 11 || this.nodeType === 9 ) {
				var target = manipulationTarget( this, elem );
				target.insertBefore( elem, target.firstChild );
			}
		} );
	},

	before: function() {
		return domManip( this, arguments, function( elem ) {
			if ( this.parentNode ) {
				this.parentNode.insertBefore( elem, this );
			}
		} );
	},

	after: function() {
		return domManip( this, arguments, function( elem ) {
			if ( this.parentNode ) {
				this.parentNode.insertBefore( elem, this.nextSibling );
			}
		} );
	},

	empty: function() {
		var elem,
			i = 0;

		for ( ; ( elem = this[ i ] ) != null; i++ ) {
			if ( elem.nodeType === 1 ) {

				// Prevent memory leaks
				jQuery.cleanData( getAll( elem, false ) );

				// Remove any remaining nodes
				elem.textContent = "";
			}
		}

		return this;
	},

	clone: function( dataAndEvents, deepDataAndEvents ) {
		dataAndEvents = dataAndEvents == null ? false : dataAndEvents;
		deepDataAndEvents = deepDataAndEvents == null ? dataAndEvents : deepDataAndEvents;

		return this.map( function() {
			return jQuery.clone( this, dataAndEvents, deepDataAndEvents );
		} );
	},

	html: function( value ) {
		return access( this, function( value ) {
			var elem = this[ 0 ] || {},
				i = 0,
				l = this.length;

			if ( value === undefined && elem.nodeType === 1 ) {
				return elem.innerHTML;
			}

			// See if we can take a shortcut and just use innerHTML
			if ( typeof value === "string" && !rnoInnerhtml.test( value ) &&
				!wrapMap[ ( rtagName.exec( value ) || [ "", "" ] )[ 1 ].toLowerCase() ] ) {

				value = jQuery.htmlPrefilter( value );

				try {
					for ( ; i < l; i++ ) {
						elem = this[ i ] || {};

						// Remove element nodes and prevent memory leaks
						if ( elem.nodeType === 1 ) {
							jQuery.cleanData( getAll( elem, false ) );
							elem.innerHTML = value;
						}
					}

					elem = 0;

				// If using innerHTML throws an exception, use the fallback method
				} catch ( e ) {}
			}

			if ( elem ) {
				this.empty().append( value );
			}
		}, null, value, arguments.length );
	},

	replaceWith: function() {
		var ignored = [];

		// Make the changes, replacing each non-ignored context element with the new content
		return domManip( this, arguments, function( elem ) {
			var parent = this.parentNode;

			if ( jQuery.inArray( this, ignored ) < 0 ) {
				jQuery.cleanData( getAll( this ) );
				if ( parent ) {
					parent.replaceChild( elem, this );
				}
			}

		// Force callback invocation
		}, ignored );
	}
} );

jQuery.each( {
	appendTo: "append",
	prependTo: "prepend",
	insertBefore: "before",
	insertAfter: "after",
	replaceAll: "replaceWith"
}, function( name, original ) {
	jQuery.fn[ name ] = function( selector ) {
		var elems,
			ret = [],
			insert = jQuery( selector ),
			last = insert.length - 1,
			i = 0;

		for ( ; i <= last; i++ ) {
			elems = i === last ? this : this.clone( true );
			jQuery( insert[ i ] )[ original ]( elems );

			// Support: Android <=4.0 only, PhantomJS 1 only
			// .get() because push.apply(_, arraylike) throws on ancient WebKit
			push.apply( ret, elems.get() );
		}

		return this.pushStack( ret );
	};
} );
var rnumnonpx = new RegExp( "^(" + pnum + ")(?!px)[a-z%]+$", "i" );

var getStyles = function( elem ) {

		// Support: IE <=11 only, Firefox <=30 (#15098, #14150)
		// IE throws on elements created in popups
		// FF meanwhile throws on frame elements through "defaultView.getComputedStyle"
		var view = elem.ownerDocument.defaultView;

		if ( !view || !view.opener ) {
			view = window;
		}

		return view.getComputedStyle( elem );
	};

var swap = function( elem, options, callback ) {
	var ret, name,
		old = {};

	// Remember the old values, and insert the new ones
	for ( name in options ) {
		old[ name ] = elem.style[ name ];
		elem.style[ name ] = options[ name ];
	}

	ret = callback.call( elem );

	// Revert the old values
	for ( name in options ) {
		elem.style[ name ] = old[ name ];
	}

	return ret;
};


var rboxStyle = new RegExp( cssExpand.join( "|" ), "i" );



( function() {

	// Executing both pixelPosition & boxSizingReliable tests require only one layout
	// so they're executed at the same time to save the second computation.
	function computeStyleTests() {

		// This is a singleton, we need to execute it only once
		if ( !div ) {
			return;
		}

		container.style.cssText = "position:absolute;left:-11111px;width:60px;" +
			"margin-top:1px;padding:0;border:0";
		div.style.cssText =
			"position:relative;display:block;box-sizing:border-box;overflow:scroll;" +
			"margin:auto;border:1px;padding:1px;" +
			"width:60%;top:1%";
		documentElement.appendChild( container ).appendChild( div );

		var divStyle = window.getComputedStyle( div );
		pixelPositionVal = divStyle.top !== "1%";

		// Support: Android 4.0 - 4.3 only, Firefox <=3 - 44
		reliableMarginLeftVal = roundPixelMeasures( divStyle.marginLeft ) === 12;

		// Support: Android 4.0 - 4.3 only, Safari <=9.1 - 10.1, iOS <=7.0 - 9.3
		// Some styles come back with percentage values, even though they shouldn't
		div.style.right = "60%";
		pixelBoxStylesVal = roundPixelMeasures( divStyle.right ) === 36;

		// Support: IE 9 - 11 only
		// Detect misreporting of content dimensions for box-sizing:border-box elements
		boxSizingReliableVal = roundPixelMeasures( divStyle.width ) === 36;

		// Support: IE 9 only
		// Detect overflow:scroll screwiness (gh-3699)
		// Support: Chrome <=64
		// Don't get tricked when zoom affects offsetWidth (gh-4029)
		div.style.position = "absolute";
		scrollboxSizeVal = roundPixelMeasures( div.offsetWidth / 3 ) === 12;

		documentElement.removeChild( container );

		// Nullify the div so it wouldn't be stored in the memory and
		// it will also be a sign that checks already performed
		div = null;
	}

	function roundPixelMeasures( measure ) {
		return Math.round( parseFloat( measure ) );
	}

	var pixelPositionVal, boxSizingReliableVal, scrollboxSizeVal, pixelBoxStylesVal,
		reliableTrDimensionsVal, reliableMarginLeftVal,
		container = document.createElement( "div" ),
		div = document.createElement( "div" );

	// Finish early in limited (non-browser) environments
	if ( !div.style ) {
		return;
	}

	// Support: IE <=9 - 11 only
	// Style of cloned element affects source element cloned (#8908)
	div.style.backgroundClip = "content-box";
	div.cloneNode( true ).style.backgroundClip = "";
	support.clearCloneStyle = div.style.backgroundClip === "content-box";

	jQuery.extend( support, {
		boxSizingReliable: function() {
			computeStyleTests();
			return boxSizingReliableVal;
		},
		pixelBoxStyles: function() {
			computeStyleTests();
			return pixelBoxStylesVal;
		},
		pixelPosition: function() {
			computeStyleTests();
			return pixelPositionVal;
		},
		reliableMarginLeft: function() {
			computeStyleTests();
			return reliableMarginLeftVal;
		},
		scrollboxSize: function() {
			computeStyleTests();
			return scrollboxSizeVal;
		},

		// Support: IE 9 - 11+, Edge 15 - 18+
		// IE/Edge misreport `getComputedStyle` of table rows with width/height
		// set in CSS while `offset*` properties report correct values.
		// Behavior in IE 9 is more subtle than in newer versions & it passes
		// some versions of this test; make sure not to make it pass there!
		//
		// Support: Firefox 70+
		// Only Firefox includes border widths
		// in computed dimensions. (gh-4529)
		reliableTrDimensions: function() {
			var table, tr, trChild, trStyle;
			if ( reliableTrDimensionsVal == null ) {
				table = document.createElement( "table" );
				tr = document.createElement( "tr" );
				trChild = document.createElement( "div" );

				table.style.cssText = "position:absolute;left:-11111px;border-collapse:separate";
				tr.style.cssText = "border:1px solid";

				// Support: Chrome 86+
				// Height set through cssText does not get applied.
				// Computed height then comes back as 0.
				tr.style.height = "1px";
				trChild.style.height = "9px";

				// Support: Android 8 Chrome 86+
				// In our bodyBackground.html iframe,
				// display for all div elements is set to "inline",
				// which causes a problem only in Android 8 Chrome 86.
				// Ensuring the div is display: block
				// gets around this issue.
				trChild.style.display = "block";

				documentElement
					.appendChild( table )
					.appendChild( tr )
					.appendChild( trChild );

				trStyle = window.getComputedStyle( tr );
				reliableTrDimensionsVal = ( parseInt( trStyle.height, 10 ) +
					parseInt( trStyle.borderTopWidth, 10 ) +
					parseInt( trStyle.borderBottomWidth, 10 ) ) === tr.offsetHeight;

				documentElement.removeChild( table );
			}
			return reliableTrDimensionsVal;
		}
	} );
} )();


function curCSS( elem, name, computed ) {
	var width, minWidth, maxWidth, ret,

		// Support: Firefox 51+
		// Retrieving style before computed somehow
		// fixes an issue with getting wrong values
		// on detached elements
		style = elem.style;

	computed = computed || getStyles( elem );

	// getPropertyValue is needed for:
	//   .css('filter') (IE 9 only, #12537)
	//   .css('--customProperty) (#3144)
	if ( computed ) {
		ret = computed.getPropertyValue( name ) || computed[ name ];

		if ( ret === "" && !isAttached( elem ) ) {
			ret = jQuery.style( elem, name );
		}

		// A tribute to the "awesome hack by Dean Edwards"
		// Android Browser returns percentage for some values,
		// but width seems to be reliably pixels.
		// This is against the CSSOM draft spec:
		// https://drafts.csswg.org/cssom/#resolved-values
		if ( !support.pixelBoxStyles() && rnumnonpx.test( ret ) && rboxStyle.test( name ) ) {

			// Remember the original values
			width = style.width;
			minWidth = style.minWidth;
			maxWidth = style.maxWidth;

			// Put in the new values to get a computed value out
			style.minWidth = style.maxWidth = style.width = ret;
			ret = computed.width;

			// Revert the changed values
			style.width = width;
			style.minWidth = minWidth;
			style.maxWidth = maxWidth;
		}
	}

	return ret !== undefined ?

		// Support: IE <=9 - 11 only
		// IE returns zIndex value as an integer.
		ret + "" :
		ret;
}


function addGetHookIf( conditionFn, hookFn ) {

	// Define the hook, we'll check on the first run if it's really needed.
	return {
		get: function() {
			if ( conditionFn() ) {

				// Hook not needed (or it's not possible to use it due
				// to missing dependency), remove it.
				delete this.get;
				return;
			}

			// Hook needed; redefine it so that the support test is not executed again.
			return ( this.get = hookFn ).apply( this, arguments );
		}
	};
}


var cssPrefixes = [ "Webkit", "Moz", "ms" ],
	emptyStyle = document.createElement( "div" ).style,
	vendorProps = {};

// Return a vendor-prefixed property or undefined
function vendorPropName( name ) {

	// Check for vendor prefixed names
	var capName = name[ 0 ].toUpperCase() + name.slice( 1 ),
		i = cssPrefixes.length;

	while ( i-- ) {
		name = cssPrefixes[ i ] + capName;
		if ( name in emptyStyle ) {
			return name;
		}
	}
}

// Return a potentially-mapped jQuery.cssProps or vendor prefixed property
function finalPropName( name ) {
	var final = jQuery.cssProps[ name ] || vendorProps[ name ];

	if ( final ) {
		return final;
	}
	if ( name in emptyStyle ) {
		return name;
	}
	return vendorProps[ name ] = vendorPropName( name ) || name;
}


var

	// Swappable if display is none or starts with table
	// except "table", "table-cell", or "table-caption"
	// See here for display values: https://developer.mozilla.org/en-US/docs/CSS/display
	rdisplayswap = /^(none|table(?!-c[ea]).+)/,
	rcustomProp = /^--/,
	cssShow = { position: "absolute", visibility: "hidden", display: "block" },
	cssNormalTransform = {
		letterSpacing: "0",
		fontWeight: "400"
	};

function setPositiveNumber( _elem, value, subtract ) {

	// Any relative (+/-) values have already been
	// normalized at this point
	var matches = rcssNum.exec( value );
	return matches ?

		// Guard against undefined "subtract", e.g., when used as in cssHooks
		Math.max( 0, matches[ 2 ] - ( subtract || 0 ) ) + ( matches[ 3 ] || "px" ) :
		value;
}

function boxModelAdjustment( elem, dimension, box, isBorderBox, styles, computedVal ) {
	var i = dimension === "width" ? 1 : 0,
		extra = 0,
		delta = 0;

	// Adjustment may not be necessary
	if ( box === ( isBorderBox ? "border" : "content" ) ) {
		return 0;
	}

	for ( ; i < 4; i += 2 ) {

		// Both box models exclude margin
		if ( box === "margin" ) {
			delta += jQuery.css( elem, box + cssExpand[ i ], true, styles );
		}

		// If we get here with a content-box, we're seeking "padding" or "border" or "margin"
		if ( !isBorderBox ) {

			// Add padding
			delta += jQuery.css( elem, "padding" + cssExpand[ i ], true, styles );

			// For "border" or "margin", add border
			if ( box !== "padding" ) {
				delta += jQuery.css( elem, "border" + cssExpand[ i ] + "Width", true, styles );

			// But still keep track of it otherwise
			} else {
				extra += jQuery.css( elem, "border" + cssExpand[ i ] + "Width", true, styles );
			}

		// If we get here with a border-box (content + padding + border), we're seeking "content" or
		// "padding" or "margin"
		} else {

			// For "content", subtract padding
			if ( box === "content" ) {
				delta -= jQuery.css( elem, "padding" + cssExpand[ i ], true, styles );
			}

			// For "content" or "padding", subtract border
			if ( box !== "margin" ) {
				delta -= jQuery.css( elem, "border" + cssExpand[ i ] + "Width", true, styles );
			}
		}
	}

	// Account for positive content-box scroll gutter when requested by providing computedVal
	if ( !isBorderBox && computedVal >= 0 ) {

		// offsetWidth/offsetHeight is a rounded sum of content, padding, scroll gutter, and border
		// Assuming integer scroll gutter, subtract the rest and round down
		delta += Math.max( 0, Math.ceil(
			elem[ "offset" + dimension[ 0 ].toUpperCase() + dimension.slice( 1 ) ] -
			computedVal -
			delta -
			extra -
			0.5

		// If offsetWidth/offsetHeight is unknown, then we can't determine content-box scroll gutter
		// Use an explicit zero to avoid NaN (gh-3964)
		) ) || 0;
	}

	return delta;
}

function getWidthOrHeight( elem, dimension, extra ) {

	// Start with computed style
	var styles = getStyles( elem ),

		// To avoid forcing a reflow, only fetch boxSizing if we need it (gh-4322).
		// Fake content-box until we know it's needed to know the true value.
		boxSizingNeeded = !support.boxSizingReliable() || extra,
		isBorderBox = boxSizingNeeded &&
			jQuery.css( elem, "boxSizing", false, styles ) === "border-box",
		valueIsBorderBox = isBorderBox,

		val = curCSS( elem, dimension, styles ),
		offsetProp = "offset" + dimension[ 0 ].toUpperCase() + dimension.slice( 1 );

	// Support: Firefox <=54
	// Return a confounding non-pixel value or feign ignorance, as appropriate.
	if ( rnumnonpx.test( val ) ) {
		if ( !extra ) {
			return val;
		}
		val = "auto";
	}


	// Support: IE 9 - 11 only
	// Use offsetWidth/offsetHeight for when box sizing is unreliable.
	// In those cases, the computed value can be trusted to be border-box.
	if ( ( !support.boxSizingReliable() && isBorderBox ||

		// Support: IE 10 - 11+, Edge 15 - 18+
		// IE/Edge misreport `getComputedStyle` of table rows with width/height
		// set in CSS while `offset*` properties report correct values.
		// Interestingly, in some cases IE 9 doesn't suffer from this issue.
		!support.reliableTrDimensions() && nodeName( elem, "tr" ) ||

		// Fall back to offsetWidth/offsetHeight when value is "auto"
		// This happens for inline elements with no explicit setting (gh-3571)
		val === "auto" ||

		// Support: Android <=4.1 - 4.3 only
		// Also use offsetWidth/offsetHeight for misreported inline dimensions (gh-3602)
		!parseFloat( val ) && jQuery.css( elem, "display", false, styles ) === "inline" ) &&

		// Make sure the element is visible & connected
		elem.getClientRects().length ) {

		isBorderBox = jQuery.css( elem, "boxSizing", false, styles ) === "border-box";

		// Where available, offsetWidth/offsetHeight approximate border box dimensions.
		// Where not available (e.g., SVG), assume unreliable box-sizing and interpret the
		// retrieved value as a content box dimension.
		valueIsBorderBox = offsetProp in elem;
		if ( valueIsBorderBox ) {
			val = elem[ offsetProp ];
		}
	}

	// Normalize "" and auto
	val = parseFloat( val ) || 0;

	// Adjust for the element's box model
	return ( val +
		boxModelAdjustment(
			elem,
			dimension,
			extra || ( isBorderBox ? "border" : "content" ),
			valueIsBorderBox,
			styles,

			// Provide the current computed size to request scroll gutter calculation (gh-3589)
			val
		)
	) + "px";
}

jQuery.extend( {

	// Add in style property hooks for overriding the default
	// behavior of getting and setting a style property
	cssHooks: {
		opacity: {
			get: function( elem, computed ) {
				if ( computed ) {

					// We should always get a number back from opacity
					var ret = curCSS( elem, "opacity" );
					return ret === "" ? "1" : ret;
				}
			}
		}
	},

	// Don't automatically add "px" to these possibly-unitless properties
	cssNumber: {
		"animationIterationCount": true,
		"columnCount": true,
		"fillOpacity": true,
		"flexGrow": true,
		"flexShrink": true,
		"fontWeight": true,
		"gridArea": true,
		"gridColumn": true,
		"gridColumnEnd": true,
		"gridColumnStart": true,
		"gridRow": true,
		"gridRowEnd": true,
		"gridRowStart": true,
		"lineHeight": true,
		"opacity": true,
		"order": true,
		"orphans": true,
		"widows": true,
		"zIndex": true,
		"zoom": true
	},

	// Add in properties whose names you wish to fix before
	// setting or getting the value
	cssProps: {},

	// Get and set the style property on a DOM Node
	style: function( elem, name, value, extra ) {

		// Don't set styles on text and comment nodes
		if ( !elem || elem.nodeType === 3 || elem.nodeType === 8 || !elem.style ) {
			return;
		}

		// Make sure that we're working with the right name
		var ret, type, hooks,
			origName = camelCase( name ),
			isCustomProp = rcustomProp.test( name ),
			style = elem.style;

		// Make sure that we're working with the right name. We don't
		// want to query the value if it is a CSS custom property
		// since they are user-defined.
		if ( !isCustomProp ) {
			name = finalPropName( origName );
		}

		// Gets hook for the prefixed version, then unprefixed version
		hooks = jQuery.cssHooks[ name ] || jQuery.cssHooks[ origName ];

		// Check if we're setting a value
		if ( value !== undefined ) {
			type = typeof value;

			// Convert "+=" or "-=" to relative numbers (#7345)
			if ( type === "string" && ( ret = rcssNum.exec( value ) ) && ret[ 1 ] ) {
				value = adjustCSS( elem, name, ret );

				// Fixes bug #9237
				type = "number";
			}

			// Make sure that null and NaN values aren't set (#7116)
			if ( value == null || value !== value ) {
				return;
			}

			// If a number was passed in, add the unit (except for certain CSS properties)
			// The isCustomProp check can be removed in jQuery 4.0 when we only auto-append
			// "px" to a few hardcoded values.
			if ( type === "number" && !isCustomProp ) {
				value += ret && ret[ 3 ] || ( jQuery.cssNumber[ origName ] ? "" : "px" );
			}

			// background-* props affect original clone's values
			if ( !support.clearCloneStyle && value === "" && name.indexOf( "background" ) === 0 ) {
				style[ name ] = "inherit";
			}

			// If a hook was provided, use that value, otherwise just set the specified value
			if ( !hooks || !( "set" in hooks ) ||
				( value = hooks.set( elem, value, extra ) ) !== undefined ) {

				if ( isCustomProp ) {
					style.setProperty( name, value );
				} else {
					style[ name ] = value;
				}
			}

		} else {

			// If a hook was provided get the non-computed value from there
			if ( hooks && "get" in hooks &&
				( ret = hooks.get( elem, false, extra ) ) !== undefined ) {

				return ret;
			}

			// Otherwise just get the value from the style object
			return style[ name ];
		}
	},

	css: function( elem, name, extra, styles ) {
		var val, num, hooks,
			origName = camelCase( name ),
			isCustomProp = rcustomProp.test( name );

		// Make sure that we're working with the right name. We don't
		// want to modify the value if it is a CSS custom property
		// since they are user-defined.
		if ( !isCustomProp ) {
			name = finalPropName( origName );
		}

		// Try prefixed name followed by the unprefixed name
		hooks = jQuery.cssHooks[ name ] || jQuery.cssHooks[ origName ];

		// If a hook was provided get the computed value from there
		if ( hooks && "get" in hooks ) {
			val = hooks.get( elem, true, extra );
		}

		// Otherwise, if a way to get the computed value exists, use that
		if ( val === undefined ) {
			val = curCSS( elem, name, styles );
		}

		// Convert "normal" to computed value
		if ( val === "normal" && name in cssNormalTransform ) {
			val = cssNormalTransform[ name ];
		}

		// Make numeric if forced or a qualifier was provided and val looks numeric
		if ( extra === "" || extra ) {
			num = parseFloat( val );
			return extra === true || isFinite( num ) ? num || 0 : val;
		}

		return val;
	}
} );

jQuery.each( [ "height", "width" ], function( _i, dimension ) {
	jQuery.cssHooks[ dimension ] = {
		get: function( elem, computed, extra ) {
			if ( computed ) {

				// Certain elements can have dimension info if we invisibly show them
				// but it must have a current display style that would benefit
				return rdisplayswap.test( jQuery.css( elem, "display" ) ) &&

					// Support: Safari 8+
					// Table columns in Safari have non-zero offsetWidth & zero
					// getBoundingClientRect().width unless display is changed.
					// Support: IE <=11 only
					// Running getBoundingClientRect on a disconnected node
					// in IE throws an error.
					( !elem.getClientRects().length || !elem.getBoundingClientRect().width ) ?
					swap( elem, cssShow, function() {
						return getWidthOrHeight( elem, dimension, extra );
					} ) :
					getWidthOrHeight( elem, dimension, extra );
			}
		},

		set: function( elem, value, extra ) {
			var matches,
				styles = getStyles( elem ),

				// Only read styles.position if the test has a chance to fail
				// to avoid forcing a reflow.
				scrollboxSizeBuggy = !support.scrollboxSize() &&
					styles.position === "absolute",

				// To avoid forcing a reflow, only fetch boxSizing if we need it (gh-3991)
				boxSizingNeeded = scrollboxSizeBuggy || extra,
				isBorderBox = boxSizingNeeded &&
					jQuery.css( elem, "boxSizing", false, styles ) === "border-box",
				subtract = extra ?
					boxModelAdjustment(
						elem,
						dimension,
						extra,
						isBorderBox,
						styles
					) :
					0;

			// Account for unreliable border-box dimensions by comparing offset* to computed and
			// faking a content-box to get border and padding (gh-3699)
			if ( isBorderBox && scrollboxSizeBuggy ) {
				subtract -= Math.ceil(
					elem[ "offset" + dimension[ 0 ].toUpperCase() + dimension.slice( 1 ) ] -
					parseFloat( styles[ dimension ] ) -
					boxModelAdjustment( elem, dimension, "border", false, styles ) -
					0.5
				);
			}

			// Convert to pixels if value adjustment is needed
			if ( subtract && ( matches = rcssNum.exec( value ) ) &&
				( matches[ 3 ] || "px" ) !== "px" ) {

				elem.style[ dimension ] = value;
				value = jQuery.css( elem, dimension );
			}

			return setPositiveNumber( elem, value, subtract );
		}
	};
} );

jQuery.cssHooks.marginLeft = addGetHookIf( support.reliableMarginLeft,
	function( elem, computed ) {
		if ( computed ) {
			return ( parseFloat( curCSS( elem, "marginLeft" ) ) ||
				elem.getBoundingClientRect().left -
					swap( elem, { marginLeft: 0 }, function() {
						return elem.getBoundingClientRect().left;
					} )
			) + "px";
		}
	}
);

// These hooks are used by animate to expand properties
jQuery.each( {
	margin: "",
	padding: "",
	border: "Width"
}, function( prefix, suffix ) {
	jQuery.cssHooks[ prefix + suffix ] = {
		expand: function( value ) {
			var i = 0,
				expanded = {},

				// Assumes a single number if not a string
				parts = typeof value === "string" ? value.split( " " ) : [ value ];

			for ( ; i < 4; i++ ) {
				expanded[ prefix + cssExpand[ i ] + suffix ] =
					parts[ i ] || parts[ i - 2 ] || parts[ 0 ];
			}

			return expanded;
		}
	};

	if ( prefix !== "margin" ) {
		jQuery.cssHooks[ prefix + suffix ].set = setPositiveNumber;
	}
} );

jQuery.fn.extend( {
	css: function( name, value ) {
		return access( this, function( elem, name, value ) {
			var styles, len,
				map = {},
				i = 0;

			if ( Array.isArray( name ) ) {
				styles = getStyles( elem );
				len = name.length;

				for ( ; i < len; i++ ) {
					map[ name[ i ] ] = jQuery.css( elem, name[ i ], false, styles );
				}

				return map;
			}

			return value !== undefined ?
				jQuery.style( elem, name, value ) :
				jQuery.css( elem, name );
		}, name, value, arguments.length > 1 );
	}
} );


function Tween( elem, options, prop, end, easing ) {
	return new Tween.prototype.init( elem, options, prop, end, easing );
}
jQuery.Tween = Tween;

Tween.prototype = {
	constructor: Tween,
	init: function( elem, options, prop, end, easing, unit ) {
		this.elem = elem;
		this.prop = prop;
		this.easing = easing || jQuery.easing._default;
		this.options = options;
		this.start = this.now = this.cur();
		this.end = end;
		this.unit = unit || ( jQuery.cssNumber[ prop ] ? "" : "px" );
	},
	cur: function() {
		var hooks = Tween.propHooks[ this.prop ];

		return hooks && hooks.get ?
			hooks.get( this ) :
			Tween.propHooks._default.get( this );
	},
	run: function( percent ) {
		var eased,
			hooks = Tween.propHooks[ this.prop ];

		if ( this.options.duration ) {
			this.pos = eased = jQuery.easing[ this.easing ](
				percent, this.options.duration * percent, 0, 1, this.options.duration
			);
		} else {
			this.pos = eased = percent;
		}
		this.now = ( this.end - this.start ) * eased + this.start;

		if ( this.options.step ) {
			this.options.step.call( this.elem, this.now, this );
		}

		if ( hooks && hooks.set ) {
			hooks.set( this );
		} else {
			Tween.propHooks._default.set( this );
		}
		return this;
	}
};

Tween.prototype.init.prototype = Tween.prototype;

Tween.propHooks = {
	_default: {
		get: function( tween ) {
			var result;

			// Use a property on the element directly when it is not a DOM element,
			// or when there is no matching style property that exists.
			if ( tween.elem.nodeType !== 1 ||
				tween.elem[ tween.prop ] != null && tween.elem.style[ tween.prop ] == null ) {
				return tween.elem[ tween.prop ];
			}

			// Passing an empty string as a 3rd parameter to .css will automatically
			// attempt a parseFloat and fallback to a string if the parse fails.
			// Simple values such as "10px" are parsed to Float;
			// complex values such as "rotate(1rad)" are returned as-is.
			result = jQuery.css( tween.elem, tween.prop, "" );

			// Empty strings, null, undefined and "auto" are converted to 0.
			return !result || result === "auto" ? 0 : result;
		},
		set: function( tween ) {

			// Use step hook for back compat.
			// Use cssHook if its there.
			// Use .style if available and use plain properties where available.
			if ( jQuery.fx.step[ tween.prop ] ) {
				jQuery.fx.step[ tween.prop ]( tween );
			} else if ( tween.elem.nodeType === 1 && (
				jQuery.cssHooks[ tween.prop ] ||
					tween.elem.style[ finalPropName( tween.prop ) ] != null ) ) {
				jQuery.style( tween.elem, tween.prop, tween.now + tween.unit );
			} else {
				tween.elem[ tween.prop ] = tween.now;
			}
		}
	}
};

// Support: IE <=9 only
// Panic based approach to setting things on disconnected nodes
Tween.propHooks.scrollTop = Tween.propHooks.scrollLeft = {
	set: function( tween ) {
		if ( tween.elem.nodeType && tween.elem.parentNode ) {
			tween.elem[ tween.prop ] = tween.now;
		}
	}
};

jQuery.easing = {
	linear: function( p ) {
		return p;
	},
	swing: function( p ) {
		return 0.5 - Math.cos( p * Math.PI ) / 2;
	},
	_default: "swing"
};

jQuery.fx = Tween.prototype.init;

// Back compat <1.8 extension point
jQuery.fx.step = {};




var
	fxNow, inProgress,
	rfxtypes = /^(?:toggle|show|hide)$/,
	rrun = /queueHooks$/;

function schedule() {
	if ( inProgress ) {
		if ( document.hidden === false && window.requestAnimationFrame ) {
			window.requestAnimationFrame( schedule );
		} else {
			window.setTimeout( schedule, jQuery.fx.interval );
		}

		jQuery.fx.tick();
	}
}

// Animations created synchronously will run synchronously
function createFxNow() {
	window.setTimeout( function() {
		fxNow = undefined;
	} );
	return ( fxNow = Date.now() );
}

// Generate parameters to create a standard animation
function genFx( type, includeWidth ) {
	var which,
		i = 0,
		attrs = { height: type };

	// If we include width, step value is 1 to do all cssExpand values,
	// otherwise step value is 2 to skip over Left and Right
	includeWidth = includeWidth ? 1 : 0;
	for ( ; i < 4; i += 2 - includeWidth ) {
		which = cssExpand[ i ];
		attrs[ "margin" + which ] = attrs[ "padding" + which ] = type;
	}

	if ( includeWidth ) {
		attrs.opacity = attrs.width = type;
	}

	return attrs;
}

function createTween( value, prop, animation ) {
	var tween,
		collection = ( Animation.tweeners[ prop ] || [] ).concat( Animation.tweeners[ "*" ] ),
		index = 0,
		length = collection.length;
	for ( ; index < length; index++ ) {
		if ( ( tween = collection[ index ].call( animation, prop, value ) ) ) {

			// We're done with this property
			return tween;
		}
	}
}

function defaultPrefilter( elem, props, opts ) {
	var prop, value, toggle, hooks, oldfire, propTween, restoreDisplay, display,
		isBox = "width" in props || "height" in props,
		anim = this,
		orig = {},
		style = elem.style,
		hidden = elem.nodeType && isHiddenWithinTree( elem ),
		dataShow = dataPriv.get( elem, "fxshow" );

	// Queue-skipping animations hijack the fx hooks
	if ( !opts.queue ) {
		hooks = jQuery._queueHooks( elem, "fx" );
		if ( hooks.unqueued == null ) {
			hooks.unqueued = 0;
			oldfire = hooks.empty.fire;
			hooks.empty.fire = function() {
				if ( !hooks.unqueued ) {
					oldfire();
				}
			};
		}
		hooks.unqueued++;

		anim.always( function() {

			// Ensure the complete handler is called before this completes
			anim.always( function() {
				hooks.unqueued--;
				if ( !jQuery.queue( elem, "fx" ).length ) {
					hooks.empty.fire();
				}
			} );
		} );
	}

	// Detect show/hide animations
	for ( prop in props ) {
		value = props[ prop ];
		if ( rfxtypes.test( value ) ) {
			delete props[ prop ];
			toggle = toggle || value === "toggle";
			if ( value === ( hidden ? "hide" : "show" ) ) {

				// Pretend to be hidden if this is a "show" and
				// there is still data from a stopped show/hide
				if ( value === "show" && dataShow && dataShow[ prop ] !== undefined ) {
					hidden = true;

				// Ignore all other no-op show/hide data
				} else {
					continue;
				}
			}
			orig[ prop ] = dataShow && dataShow[ prop ] || jQuery.style( elem, prop );
		}
	}

	// Bail out if this is a no-op like .hide().hide()
	propTween = !jQuery.isEmptyObject( props );
	if ( !propTween && jQuery.isEmptyObject( orig ) ) {
		return;
	}

	// Restrict "overflow" and "display" styles during box animations
	if ( isBox && elem.nodeType === 1 ) {

		// Support: IE <=9 - 11, Edge 12 - 15
		// Record all 3 overflow attributes because IE does not infer the shorthand
		// from identically-valued overflowX and overflowY and Edge just mirrors
		// the overflowX value there.
		opts.overflow = [ style.overflow, style.overflowX, style.overflowY ];

		// Identify a display type, preferring old show/hide data over the CSS cascade
		restoreDisplay = dataShow && dataShow.display;
		if ( restoreDisplay == null ) {
			restoreDisplay = dataPriv.get( elem, "display" );
		}
		display = jQuery.css( elem, "display" );
		if ( display === "none" ) {
			if ( restoreDisplay ) {
				display = restoreDisplay;
			} else {

				// Get nonempty value(s) by temporarily forcing visibility
				showHide( [ elem ], true );
				restoreDisplay = elem.style.display || restoreDisplay;
				display = jQuery.css( elem, "display" );
				showHide( [ elem ] );
			}
		}

		// Animate inline elements as inline-block
		if ( display === "inline" || display === "inline-block" && restoreDisplay != null ) {
			if ( jQuery.css( elem, "float" ) === "none" ) {

				// Restore the original display value at the end of pure show/hide animations
				if ( !propTween ) {
					anim.done( function() {
						style.display = restoreDisplay;
					} );
					if ( restoreDisplay == null ) {
						display = style.display;
						restoreDisplay = display === "none" ? "" : display;
					}
				}
				style.display = "inline-block";
			}
		}
	}

	if ( opts.overflow ) {
		style.overflow = "hidden";
		anim.always( function() {
			style.overflow = opts.overflow[ 0 ];
			style.overflowX = opts.overflow[ 1 ];
			style.overflowY = opts.overflow[ 2 ];
		} );
	}

	// Implement show/hide animations
	propTween = false;
	for ( prop in orig ) {

		// General show/hide setup for this element animation
		if ( !propTween ) {
			if ( dataShow ) {
				if ( "hidden" in dataShow ) {
					hidden = dataShow.hidden;
				}
			} else {
				dataShow = dataPriv.access( elem, "fxshow", { display: restoreDisplay } );
			}

			// Store hidden/visible for toggle so `.stop().toggle()` "reverses"
			if ( toggle ) {
				dataShow.hidden = !hidden;
			}

			// Show elements before animating them
			if ( hidden ) {
				showHide( [ elem ], true );
			}

			/* eslint-disable no-loop-func */

			anim.done( function() {

				/* eslint-enable no-loop-func */

				// The final step of a "hide" animation is actually hiding the element
				if ( !hidden ) {
					showHide( [ elem ] );
				}
				dataPriv.remove( elem, "fxshow" );
				for ( prop in orig ) {
					jQuery.style( elem, prop, orig[ prop ] );
				}
			} );
		}

		// Per-property setup
		propTween = createTween( hidden ? dataShow[ prop ] : 0, prop, anim );
		if ( !( prop in dataShow ) ) {
			dataShow[ prop ] = propTween.start;
			if ( hidden ) {
				propTween.end = propTween.start;
				propTween.start = 0;
			}
		}
	}
}

function propFilter( props, specialEasing ) {
	var index, name, easing, value, hooks;

	// camelCase, specialEasing and expand cssHook pass
	for ( index in props ) {
		name = camelCase( index );
		easing = specialEasing[ name ];
		value = props[ index ];
		if ( Array.isArray( value ) ) {
			easing = value[ 1 ];
			value = props[ index ] = value[ 0 ];
		}

		if ( index !== name ) {
			props[ name ] = value;
			delete props[ index ];
		}

		hooks = jQuery.cssHooks[ name ];
		if ( hooks && "expand" in hooks ) {
			value = hooks.expand( value );
			delete props[ name ];

			// Not quite $.extend, this won't overwrite existing keys.
			// Reusing 'index' because we have the correct "name"
			for ( index in value ) {
				if ( !( index in props ) ) {
					props[ index ] = value[ index ];
					specialEasing[ index ] = easing;
				}
			}
		} else {
			specialEasing[ name ] = easing;
		}
	}
}

function Animation( elem, properties, options ) {
	var result,
		stopped,
		index = 0,
		length = Animation.prefilters.length,
		deferred = jQuery.Deferred().always( function() {

			// Don't match elem in the :animated selector
			delete tick.elem;
		} ),
		tick = function() {
			if ( stopped ) {
				return false;
			}
			var currentTime = fxNow || createFxNow(),
				remaining = Math.max( 0, animation.startTime + animation.duration - currentTime ),

				// Support: Android 2.3 only
				// Archaic crash bug won't allow us to use `1 - ( 0.5 || 0 )` (#12497)
				temp = remaining / animation.duration || 0,
				percent = 1 - temp,
				index = 0,
				length = animation.tweens.length;

			for ( ; index < length; index++ ) {
				animation.tweens[ index ].run( percent );
			}

			deferred.notifyWith( elem, [ animation, percent, remaining ] );

			// If there's more to do, yield
			if ( percent < 1 && length ) {
				return remaining;
			}

			// If this was an empty animation, synthesize a final progress notification
			if ( !length ) {
				deferred.notifyWith( elem, [ animation, 1, 0 ] );
			}

			// Resolve the animation and report its conclusion
			deferred.resolveWith( elem, [ animation ] );
			return false;
		},
		animation = deferred.promise( {
			elem: elem,
			props: jQuery.extend( {}, properties ),
			opts: jQuery.extend( true, {
				specialEasing: {},
				easing: jQuery.easing._default
			}, options ),
			originalProperties: properties,
			originalOptions: options,
			startTime: fxNow || createFxNow(),
			duration: options.duration,
			tweens: [],
			createTween: function( prop, end ) {
				var tween = jQuery.Tween( elem, animation.opts, prop, end,
					animation.opts.specialEasing[ prop ] || animation.opts.easing );
				animation.tweens.push( tween );
				return tween;
			},
			stop: function( gotoEnd ) {
				var index = 0,

					// If we are going to the end, we want to run all the tweens
					// otherwise we skip this part
					length = gotoEnd ? animation.tweens.length : 0;
				if ( stopped ) {
					return this;
				}
				stopped = true;
				for ( ; index < length; index++ ) {
					animation.tweens[ index ].run( 1 );
				}

				// Resolve when we played the last frame; otherwise, reject
				if ( gotoEnd ) {
					deferred.notifyWith( elem, [ animation, 1, 0 ] );
					deferred.resolveWith( elem, [ animation, gotoEnd ] );
				} else {
					deferred.rejectWith( elem, [ animation, gotoEnd ] );
				}
				return this;
			}
		} ),
		props = animation.props;

	propFilter( props, animation.opts.specialEasing );

	for ( ; index < length; index++ ) {
		result = Animation.prefilters[ index ].call( animation, elem, props, animation.opts );
		if ( result ) {
			if ( isFunction( result.stop ) ) {
				jQuery._queueHooks( animation.elem, animation.opts.queue ).stop =
					result.stop.bind( result );
			}
			return result;
		}
	}

	jQuery.map( props, createTween, animation );

	if ( isFunction( animation.opts.start ) ) {
		animation.opts.start.call( elem, animation );
	}

	// Attach callbacks from options
	animation
		.progress( animation.opts.progress )
		.done( animation.opts.done, animation.opts.complete )
		.fail( animation.opts.fail )
		.always( animation.opts.always );

	jQuery.fx.timer(
		jQuery.extend( tick, {
			elem: elem,
			anim: animation,
			queue: animation.opts.queue
		} )
	);

	return animation;
}

jQuery.Animation = jQuery.extend( Animation, {

	tweeners: {
		"*": [ function( prop, value ) {
			var tween = this.createTween( prop, value );
			adjustCSS( tween.elem, prop, rcssNum.exec( value ), tween );
			return tween;
		} ]
	},

	tweener: function( props, callback ) {
		if ( isFunction( props ) ) {
			callback = props;
			props = [ "*" ];
		} else {
			props = props.match( rnothtmlwhite );
		}

		var prop,
			index = 0,
			length = props.length;

		for ( ; index < length; index++ ) {
			prop = props[ index ];
			Animation.tweeners[ prop ] = Animation.tweeners[ prop ] || [];
			Animation.tweeners[ prop ].unshift( callback );
		}
	},

	prefilters: [ defaultPrefilter ],

	prefilter: function( callback, prepend ) {
		if ( prepend ) {
			Animation.prefilters.unshift( callback );
		} else {
			Animation.prefilters.push( callback );
		}
	}
} );

jQuery.speed = function( speed, easing, fn ) {
	var opt = speed && typeof speed === "object" ? jQuery.extend( {}, speed ) : {
		complete: fn || !fn && easing ||
			isFunction( speed ) && speed,
		duration: speed,
		easing: fn && easing || easing && !isFunction( easing ) && easing
	};

	// Go to the end state if fx are off
	if ( jQuery.fx.off ) {
		opt.duration = 0;

	} else {
		if ( typeof opt.duration !== "number" ) {
			if ( opt.duration in jQuery.fx.speeds ) {
				opt.duration = jQuery.fx.speeds[ opt.duration ];

			} else {
				opt.duration = jQuery.fx.speeds._default;
			}
		}
	}

	// Normalize opt.queue - true/undefined/null -> "fx"
	if ( opt.queue == null || opt.queue === true ) {
		opt.queue = "fx";
	}

	// Queueing
	opt.old = opt.complete;

	opt.complete = function() {
		if ( isFunction( opt.old ) ) {
			opt.old.call( this );
		}

		if ( opt.queue ) {
			jQuery.dequeue( this, opt.queue );
		}
	};

	return opt;
};

jQuery.fn.extend( {
	fadeTo: function( speed, to, easing, callback ) {

		// Show any hidden elements after setting opacity to 0
		return this.filter( isHiddenWithinTree ).css( "opacity", 0 ).show()

			// Animate to the value specified
			.end().animate( { opacity: to }, speed, easing, callback );
	},
	animate: function( prop, speed, easing, callback ) {
		var empty = jQuery.isEmptyObject( prop ),
			optall = jQuery.speed( speed, easing, callback ),
			doAnimation = function() {

				// Operate on a copy of prop so per-property easing won't be lost
				var anim = Animation( this, jQuery.extend( {}, prop ), optall );

				// Empty animations, or finishing resolves immediately
				if ( empty || dataPriv.get( this, "finish" ) ) {
					anim.stop( true );
				}
			};

		doAnimation.finish = doAnimation;

		return empty || optall.queue === false ?
			this.each( doAnimation ) :
			this.queue( optall.queue, doAnimation );
	},
	stop: function( type, clearQueue, gotoEnd ) {
		var stopQueue = function( hooks ) {
			var stop = hooks.stop;
			delete hooks.stop;
			stop( gotoEnd );
		};

		if ( typeof type !== "string" ) {
			gotoEnd = clearQueue;
			clearQueue = type;
			type = undefined;
		}
		if ( clearQueue ) {
			this.queue( type || "fx", [] );
		}

		return this.each( function() {
			var dequeue = true,
				index = type != null && type + "queueHooks",
				timers = jQuery.timers,
				data = dataPriv.get( this );

			if ( index ) {
				if ( data[ index ] && data[ index ].stop ) {
					stopQueue( data[ index ] );
				}
			} else {
				for ( index in data ) {
					if ( data[ index ] && data[ index ].stop && rrun.test( index ) ) {
						stopQueue( data[ index ] );
					}
				}
			}

			for ( index = timers.length; index--; ) {
				if ( timers[ index ].elem === this &&
					( type == null || timers[ index ].queue === type ) ) {

					timers[ index ].anim.stop( gotoEnd );
					dequeue = false;
					timers.splice( index, 1 );
				}
			}

			// Start the next in the queue if the last step wasn't forced.
			// Timers currently will call their complete callbacks, which
			// will dequeue but only if they were gotoEnd.
			if ( dequeue || !gotoEnd ) {
				jQuery.dequeue( this, type );
			}
		} );
	},
	finish: function( type ) {
		if ( type !== false ) {
			type = type || "fx";
		}
		return this.each( function() {
			var index,
				data = dataPriv.get( this ),
				queue = data[ type + "queue" ],
				hooks = data[ type + "queueHooks" ],
				timers = jQuery.timers,
				length = queue ? queue.length : 0;

			// Enable finishing flag on private data
			data.finish = true;

			// Empty the queue first
			jQuery.queue( this, type, [] );

			if ( hooks && hooks.stop ) {
				hooks.stop.call( this, true );
			}

			// Look for any active animations, and finish them
			for ( index = timers.length; index--; ) {
				if ( timers[ index ].elem === this && timers[ index ].queue === type ) {
					timers[ index ].anim.stop( true );
					timers.splice( index, 1 );
				}
			}

			// Look for any animations in the old queue and finish them
			for ( index = 0; index < length; index++ ) {
				if ( queue[ index ] && queue[ index ].finish ) {
					queue[ index ].finish.call( this );
				}
			}

			// Turn off finishing flag
			delete data.finish;
		} );
	}
} );

jQuery.each( [ "toggle", "show", "hide" ], function( _i, name ) {
	var cssFn = jQuery.fn[ name ];
	jQuery.fn[ name ] = function( speed, easing, callback ) {
		return speed == null || typeof speed === "boolean" ?
			cssFn.apply( this, arguments ) :
			this.animate( genFx( name, true ), speed, easing, callback );
	};
} );

// Generate shortcuts for custom animations
jQuery.each( {
	slideDown: genFx( "show" ),
	slideUp: genFx( "hide" ),
	slideToggle: genFx( "toggle" ),
	fadeIn: { opacity: "show" },
	fadeOut: { opacity: "hide" },
	fadeToggle: { opacity: "toggle" }
}, function( name, props ) {
	jQuery.fn[ name ] = function( speed, easing, callback ) {
		return this.animate( props, speed, easing, callback );
	};
} );

jQuery.timers = [];
jQuery.fx.tick = function() {
	var timer,
		i = 0,
		timers = jQuery.timers;

	fxNow = Date.now();

	for ( ; i < timers.length; i++ ) {
		timer = timers[ i ];

		// Run the timer and safely remove it when done (allowing for external removal)
		if ( !timer() && timers[ i ] === timer ) {
			timers.splice( i--, 1 );
		}
	}

	if ( !timers.length ) {
		jQuery.fx.stop();
	}
	fxNow = undefined;
};

jQuery.fx.timer = function( timer ) {
	jQuery.timers.push( timer );
	jQuery.fx.start();
};

jQuery.fx.interval = 13;
jQuery.fx.start = function() {
	if ( inProgress ) {
		return;
	}

	inProgress = true;
	schedule();
};

jQuery.fx.stop = function() {
	inProgress = null;
};

jQuery.fx.speeds = {
	slow: 600,
	fast: 200,

	// Default speed
	_default: 400
};


// Based off of the plugin by Clint Helfers, with permission.
// https://web.archive.org/web/20100324014747/http://blindsignals.com/index.php/2009/07/jquery-delay/
jQuery.fn.delay = function( time, type ) {
	time = jQuery.fx ? jQuery.fx.speeds[ time ] || time : time;
	type = type || "fx";

	return this.queue( type, function( next, hooks ) {
		var timeout = window.setTimeout( next, time );
		hooks.stop = function() {
			window.clearTimeout( timeout );
		};
	} );
};


( function() {
	var input = document.createElement( "input" ),
		select = document.createElement( "select" ),
		opt = select.appendChild( document.createElement( "option" ) );

	input.type = "checkbox";

	// Support: Android <=4.3 only
	// Default value for a checkbox should be "on"
	support.checkOn = input.value !== "";

	// Support: IE <=11 only
	// Must access selectedIndex to make default options select
	support.optSelected = opt.selected;

	// Support: IE <=11 only
	// An input loses its value after becoming a radio
	input = document.createElement( "input" );
	input.value = "t";
	input.type = "radio";
	support.radioValue = input.value === "t";
} )();


var boolHook,
	attrHandle = jQuery.expr.attrHandle;

jQuery.fn.extend( {
	attr: function( name, value ) {
		return access( this, jQuery.attr, name, value, arguments.length > 1 );
	},

	removeAttr: function( name ) {
		return this.each( function() {
			jQuery.removeAttr( this, name );
		} );
	}
} );

jQuery.extend( {
	attr: function( elem, name, value ) {
		var ret, hooks,
			nType = elem.nodeType;

		// Don't get/set attributes on text, comment and attribute nodes
		if ( nType === 3 || nType === 8 || nType === 2 ) {
			return;
		}

		// Fallback to prop when attributes are not supported
		if ( typeof elem.getAttribute === "undefined" ) {
			return jQuery.prop( elem, name, value );
		}

		// Attribute hooks are determined by the lowercase version
		// Grab necessary hook if one is defined
		if ( nType !== 1 || !jQuery.isXMLDoc( elem ) ) {
			hooks = jQuery.attrHooks[ name.toLowerCase() ] ||
				( jQuery.expr.match.bool.test( name ) ? boolHook : undefined );
		}

		if ( value !== undefined ) {
			if ( value === null ) {
				jQuery.removeAttr( elem, name );
				return;
			}

			if ( hooks && "set" in hooks &&
				( ret = hooks.set( elem, value, name ) ) !== undefined ) {
				return ret;
			}

			elem.setAttribute( name, value + "" );
			return value;
		}

		if ( hooks && "get" in hooks && ( ret = hooks.get( elem, name ) ) !== null ) {
			return ret;
		}

		ret = jQuery.find.attr( elem, name );

		// Non-existent attributes return null, we normalize to undefined
		return ret == null ? undefined : ret;
	},

	attrHooks: {
		type: {
			set: function( elem, value ) {
				if ( !support.radioValue && value === "radio" &&
					nodeName( elem, "input" ) ) {
					var val = elem.value;
					elem.setAttribute( "type", value );
					if ( val ) {
						elem.value = val;
					}
					return value;
				}
			}
		}
	},

	removeAttr: function( elem, value ) {
		var name,
			i = 0,

			// Attribute names can contain non-HTML whitespace characters
			// https://html.spec.whatwg.org/multipage/syntax.html#attributes-2
			attrNames = value && value.match( rnothtmlwhite );

		if ( attrNames && elem.nodeType === 1 ) {
			while ( ( name = attrNames[ i++ ] ) ) {
				elem.removeAttribute( name );
			}
		}
	}
} );

// Hooks for boolean attributes
boolHook = {
	set: function( elem, value, name ) {
		if ( value === false ) {

			// Remove boolean attributes when set to false
			jQuery.removeAttr( elem, name );
		} else {
			elem.setAttribute( name, name );
		}
		return name;
	}
};

jQuery.each( jQuery.expr.match.bool.source.match( /\w+/g ), function( _i, name ) {
	var getter = attrHandle[ name ] || jQuery.find.attr;

	attrHandle[ name ] = function( elem, name, isXML ) {
		var ret, handle,
			lowercaseName = name.toLowerCase();

		if ( !isXML ) {

			// Avoid an infinite loop by temporarily removing this function from the getter
			handle = attrHandle[ lowercaseName ];
			attrHandle[ lowercaseName ] = ret;
			ret = getter( elem, name, isXML ) != null ?
				lowercaseName :
				null;
			attrHandle[ lowercaseName ] = handle;
		}
		return ret;
	};
} );




var rfocusable = /^(?:input|select|textarea|button)$/i,
	rclickable = /^(?:a|area)$/i;

jQuery.fn.extend( {
	prop: function( name, value ) {
		return access( this, jQuery.prop, name, value, arguments.length > 1 );
	},

	removeProp: function( name ) {
		return this.each( function() {
			delete this[ jQuery.propFix[ name ] || name ];
		} );
	}
} );

jQuery.extend( {
	prop: function( elem, name, value ) {
		var ret, hooks,
			nType = elem.nodeType;

		// Don't get/set properties on text, comment and attribute nodes
		if ( nType === 3 || nType === 8 || nType === 2 ) {
			return;
		}

		if ( nType !== 1 || !jQuery.isXMLDoc( elem ) ) {

			// Fix name and attach hooks
			name = jQuery.propFix[ name ] || name;
			hooks = jQuery.propHooks[ name ];
		}

		if ( value !== undefined ) {
			if ( hooks && "set" in hooks &&
				( ret = hooks.set( elem, value, name ) ) !== undefined ) {
				return ret;
			}

			return ( elem[ name ] = value );
		}

		if ( hooks && "get" in hooks && ( ret = hooks.get( elem, name ) ) !== null ) {
			return ret;
		}

		return elem[ name ];
	},

	propHooks: {
		tabIndex: {
			get: function( elem ) {

				// Support: IE <=9 - 11 only
				// elem.tabIndex doesn't always return the
				// correct value when it hasn't been explicitly set
				// https://web.archive.org/web/20141116233347/http://fluidproject.org/blog/2008/01/09/getting-setting-and-removing-tabindex-values-with-javascript/
				// Use proper attribute retrieval(#12072)
				var tabindex = jQuery.find.attr( elem, "tabindex" );

				if ( tabindex ) {
					return parseInt( tabindex, 10 );
				}

				if (
					rfocusable.test( elem.nodeName ) ||
					rclickable.test( elem.nodeName ) &&
					elem.href
				) {
					return 0;
				}

				return -1;
			}
		}
	},

	propFix: {
		"for": "htmlFor",
		"class": "className"
	}
} );

// Support: IE <=11 only
// Accessing the selectedIndex property
// forces the browser to respect setting selected
// on the option
// The getter ensures a default option is selected
// when in an optgroup
// eslint rule "no-unused-expressions" is disabled for this code
// since it considers such accessions noop
if ( !support.optSelected ) {
	jQuery.propHooks.selected = {
		get: function( elem ) {

			/* eslint no-unused-expressions: "off" */

			var parent = elem.parentNode;
			if ( parent && parent.parentNode ) {
				parent.parentNode.selectedIndex;
			}
			return null;
		},
		set: function( elem ) {

			/* eslint no-unused-expressions: "off" */

			var parent = elem.parentNode;
			if ( parent ) {
				parent.selectedIndex;

				if ( parent.parentNode ) {
					parent.parentNode.selectedIndex;
				}
			}
		}
	};
}

jQuery.each( [
	"tabIndex",
	"readOnly",
	"maxLength",
	"cellSpacing",
	"cellPadding",
	"rowSpan",
	"colSpan",
	"useMap",
	"frameBorder",
	"contentEditable"
], function() {
	jQuery.propFix[ this.toLowerCase() ] = this;
} );




	// Strip and collapse whitespace according to HTML spec
	// https://infra.spec.whatwg.org/#strip-and-collapse-ascii-whitespace
	function stripAndCollapse( value ) {
		var tokens = value.match( rnothtmlwhite ) || [];
		return tokens.join( " " );
	}


function getClass( elem ) {
	return elem.getAttribute && elem.getAttribute( "class" ) || "";
}

function classesToArray( value ) {
	if ( Array.isArray( value ) ) {
		return value;
	}
	if ( typeof value === "string" ) {
		return value.match( rnothtmlwhite ) || [];
	}
	return [];
}

jQuery.fn.extend( {
	addClass: function( value ) {
		var classes, elem, cur, curValue, clazz, j, finalValue,
			i = 0;

		if ( isFunction( value ) ) {
			return this.each( function( j ) {
				jQuery( this ).addClass( value.call( this, j, getClass( this ) ) );
			} );
		}

		classes = classesToArray( value );

		if ( classes.length ) {
			while ( ( elem = this[ i++ ] ) ) {
				curValue = getClass( elem );
				cur = elem.nodeType === 1 && ( " " + stripAndCollapse( curValue ) + " " );

				if ( cur ) {
					j = 0;
					while ( ( clazz = classes[ j++ ] ) ) {
						if ( cur.indexOf( " " + clazz + " " ) < 0 ) {
							cur += clazz + " ";
						}
					}

					// Only assign if different to avoid unneeded rendering.
					finalValue = stripAndCollapse( cur );
					if ( curValue !== finalValue ) {
						elem.setAttribute( "class", finalValue );
					}
				}
			}
		}

		return this;
	},

	removeClass: function( value ) {
		var classes, elem, cur, curValue, clazz, j, finalValue,
			i = 0;

		if ( isFunction( value ) ) {
			return this.each( function( j ) {
				jQuery( this ).removeClass( value.call( this, j, getClass( this ) ) );
			} );
		}

		if ( !arguments.length ) {
			return this.attr( "class", "" );
		}

		classes = classesToArray( value );

		if ( classes.length ) {
			while ( ( elem = this[ i++ ] ) ) {
				curValue = getClass( elem );

				// This expression is here for better compressibility (see addClass)
				cur = elem.nodeType === 1 && ( " " + stripAndCollapse( curValue ) + " " );

				if ( cur ) {
					j = 0;
					while ( ( clazz = classes[ j++ ] ) ) {

						// Remove *all* instances
						while ( cur.indexOf( " " + clazz + " " ) > -1 ) {
							cur = cur.replace( " " + clazz + " ", " " );
						}
					}

					// Only assign if different to avoid unneeded rendering.
					finalValue = stripAndCollapse( cur );
					if ( curValue !== finalValue ) {
						elem.setAttribute( "class", finalValue );
					}
				}
			}
		}

		return this;
	},

	toggleClass: function( value, stateVal ) {
		var type = typeof value,
			isValidValue = type === "string" || Array.isArray( value );

		if ( typeof stateVal === "boolean" && isValidValue ) {
			return stateVal ? this.addClass( value ) : this.removeClass( value );
		}

		if ( isFunction( value ) ) {
			return this.each( function( i ) {
				jQuery( this ).toggleClass(
					value.call( this, i, getClass( this ), stateVal ),
					stateVal
				);
			} );
		}

		return this.each( function() {
			var className, i, self, classNames;

			if ( isValidValue ) {

				// Toggle individual class names
				i = 0;
				self = jQuery( this );
				classNames = classesToArray( value );

				while ( ( className = classNames[ i++ ] ) ) {

					// Check each className given, space separated list
					if ( self.hasClass( className ) ) {
						self.removeClass( className );
					} else {
						self.addClass( className );
					}
				}

			// Toggle whole class name
			} else if ( value === undefined || type === "boolean" ) {
				className = getClass( this );
				if ( className ) {

					// Store className if set
					dataPriv.set( this, "__className__", className );
				}

				// If the element has a class name or if we're passed `false`,
				// then remove the whole classname (if there was one, the above saved it).
				// Otherwise bring back whatever was previously saved (if anything),
				// falling back to the empty string if nothing was stored.
				if ( this.setAttribute ) {
					this.setAttribute( "class",
						className || value === false ?
							"" :
							dataPriv.get( this, "__className__" ) || ""
					);
				}
			}
		} );
	},

	hasClass: function( selector ) {
		var className, elem,
			i = 0;

		className = " " + selector + " ";
		while ( ( elem = this[ i++ ] ) ) {
			if ( elem.nodeType === 1 &&
				( " " + stripAndCollapse( getClass( elem ) ) + " " ).indexOf( className ) > -1 ) {
				return true;
			}
		}

		return false;
	}
} );




var rreturn = /\r/g;

jQuery.fn.extend( {
	val: function( value ) {
		var hooks, ret, valueIsFunction,
			elem = this[ 0 ];

		if ( !arguments.length ) {
			if ( elem ) {
				hooks = jQuery.valHooks[ elem.type ] ||
					jQuery.valHooks[ elem.nodeName.toLowerCase() ];

				if ( hooks &&
					"get" in hooks &&
					( ret = hooks.get( elem, "value" ) ) !== undefined
				) {
					return ret;
				}

				ret = elem.value;

				// Handle most common string cases
				if ( typeof ret === "string" ) {
					return ret.replace( rreturn, "" );
				}

				// Handle cases where value is null/undef or number
				return ret == null ? "" : ret;
			}

			return;
		}

		valueIsFunction = isFunction( value );

		return this.each( function( i ) {
			var val;

			if ( this.nodeType !== 1 ) {
				return;
			}

			if ( valueIsFunction ) {
				val = value.call( this, i, jQuery( this ).val() );
			} else {
				val = value;
			}

			// Treat null/undefined as ""; convert numbers to string
			if ( val == null ) {
				val = "";

			} else if ( typeof val === "number" ) {
				val += "";

			} else if ( Array.isArray( val ) ) {
				val = jQuery.map( val, function( value ) {
					return value == null ? "" : value + "";
				} );
			}

			hooks = jQuery.valHooks[ this.type ] || jQuery.valHooks[ this.nodeName.toLowerCase() ];

			// If set returns undefined, fall back to normal setting
			if ( !hooks || !( "set" in hooks ) || hooks.set( this, val, "value" ) === undefined ) {
				this.value = val;
			}
		} );
	}
} );

jQuery.extend( {
	valHooks: {
		option: {
			get: function( elem ) {

				var val = jQuery.find.attr( elem, "value" );
				return val != null ?
					val :

					// Support: IE <=10 - 11 only
					// option.text throws exceptions (#14686, #14858)
					// Strip and collapse whitespace
					// https://html.spec.whatwg.org/#strip-and-collapse-whitespace
					stripAndCollapse( jQuery.text( elem ) );
			}
		},
		select: {
			get: function( elem ) {
				var value, option, i,
					options = elem.options,
					index = elem.selectedIndex,
					one = elem.type === "select-one",
					values = one ? null : [],
					max = one ? index + 1 : options.length;

				if ( index < 0 ) {
					i = max;

				} else {
					i = one ? index : 0;
				}

				// Loop through all the selected options
				for ( ; i < max; i++ ) {
					option = options[ i ];

					// Support: IE <=9 only
					// IE8-9 doesn't update selected after form reset (#2551)
					if ( ( option.selected || i === index ) &&

							// Don't return options that are disabled or in a disabled optgroup
							!option.disabled &&
							( !option.parentNode.disabled ||
								!nodeName( option.parentNode, "optgroup" ) ) ) {

						// Get the specific value for the option
						value = jQuery( option ).val();

						// We don't need an array for one selects
						if ( one ) {
							return value;
						}

						// Multi-Selects return an array
						values.push( value );
					}
				}

				return values;
			},

			set: function( elem, value ) {
				var optionSet, option,
					options = elem.options,
					values = jQuery.makeArray( value ),
					i = options.length;

				while ( i-- ) {
					option = options[ i ];

					/* eslint-disable no-cond-assign */

					if ( option.selected =
						jQuery.inArray( jQuery.valHooks.option.get( option ), values ) > -1
					) {
						optionSet = true;
					}

					/* eslint-enable no-cond-assign */
				}

				// Force browsers to behave consistently when non-matching value is set
				if ( !optionSet ) {
					elem.selectedIndex = -1;
				}
				return values;
			}
		}
	}
} );

// Radios and checkboxes getter/setter
jQuery.each( [ "radio", "checkbox" ], function() {
	jQuery.valHooks[ this ] = {
		set: function( elem, value ) {
			if ( Array.isArray( value ) ) {
				return ( elem.checked = jQuery.inArray( jQuery( elem ).val(), value ) > -1 );
			}
		}
	};
	if ( !support.checkOn ) {
		jQuery.valHooks[ this ].get = function( elem ) {
			return elem.getAttribute( "value" ) === null ? "on" : elem.value;
		};
	}
} );




// Return jQuery for attributes-only inclusion


support.focusin = "onfocusin" in window;


var rfocusMorph = /^(?:focusinfocus|focusoutblur)$/,
	stopPropagationCallback = function( e ) {
		e.stopPropagation();
	};

jQuery.extend( jQuery.event, {

	trigger: function( event, data, elem, onlyHandlers ) {

		var i, cur, tmp, bubbleType, ontype, handle, special, lastElement,
			eventPath = [ elem || document ],
			type = hasOwn.call( event, "type" ) ? event.type : event,
			namespaces = hasOwn.call( event, "namespace" ) ? event.namespace.split( "." ) : [];

		cur = lastElement = tmp = elem = elem || document;

		// Don't do events on text and comment nodes
		if ( elem.nodeType === 3 || elem.nodeType === 8 ) {
			return;
		}

		// focus/blur morphs to focusin/out; ensure we're not firing them right now
		if ( rfocusMorph.test( type + jQuery.event.triggered ) ) {
			return;
		}

		if ( type.indexOf( "." ) > -1 ) {

			// Namespaced trigger; create a regexp to match event type in handle()
			namespaces = type.split( "." );
			type = namespaces.shift();
			namespaces.sort();
		}
		ontype = type.indexOf( ":" ) < 0 && "on" + type;

		// Caller can pass in a jQuery.Event object, Object, or just an event type string
		event = event[ jQuery.expando ] ?
			event :
			new jQuery.Event( type, typeof event === "object" && event );

		// Trigger bitmask: & 1 for native handlers; & 2 for jQuery (always true)
		event.isTrigger = onlyHandlers ? 2 : 3;
		event.namespace = namespaces.join( "." );
		event.rnamespace = event.namespace ?
			new RegExp( "(^|\\.)" + namespaces.join( "\\.(?:.*\\.|)" ) + "(\\.|$)" ) :
			null;

		// Clean up the event in case it is being reused
		event.result = undefined;
		if ( !event.target ) {
			event.target = elem;
		}

		// Clone any incoming data and prepend the event, creating the handler arg list
		data = data == null ?
			[ event ] :
			jQuery.makeArray( data, [ event ] );

		// Allow special events to draw outside the lines
		special = jQuery.event.special[ type ] || {};
		if ( !onlyHandlers && special.trigger && special.trigger.apply( elem, data ) === false ) {
			return;
		}

		// Determine event propagation path in advance, per W3C events spec (#9951)
		// Bubble up to document, then to window; watch for a global ownerDocument var (#9724)
		if ( !onlyHandlers && !special.noBubble && !isWindow( elem ) ) {

			bubbleType = special.delegateType || type;
			if ( !rfocusMorph.test( bubbleType + type ) ) {
				cur = cur.parentNode;
			}
			for ( ; cur; cur = cur.parentNode ) {
				eventPath.push( cur );
				tmp = cur;
			}

			// Only add window if we got to document (e.g., not plain obj or detached DOM)
			if ( tmp === ( elem.ownerDocument || document ) ) {
				eventPath.push( tmp.defaultView || tmp.parentWindow || window );
			}
		}

		// Fire handlers on the event path
		i = 0;
		while ( ( cur = eventPath[ i++ ] ) && !event.isPropagationStopped() ) {
			lastElement = cur;
			event.type = i > 1 ?
				bubbleType :
				special.bindType || type;

			// jQuery handler
			handle = ( dataPriv.get( cur, "events" ) || Object.create( null ) )[ event.type ] &&
				dataPriv.get( cur, "handle" );
			if ( handle ) {
				handle.apply( cur, data );
			}

			// Native handler
			handle = ontype && cur[ ontype ];
			if ( handle && handle.apply && acceptData( cur ) ) {
				event.result = handle.apply( cur, data );
				if ( event.result === false ) {
					event.preventDefault();
				}
			}
		}
		event.type = type;

		// If nobody prevented the default action, do it now
		if ( !onlyHandlers && !event.isDefaultPrevented() ) {

			if ( ( !special._default ||
				special._default.apply( eventPath.pop(), data ) === false ) &&
				acceptData( elem ) ) {

				// Call a native DOM method on the target with the same name as the event.
				// Don't do default actions on window, that's where global variables be (#6170)
				if ( ontype && isFunction( elem[ type ] ) && !isWindow( elem ) ) {

					// Don't re-trigger an onFOO event when we call its FOO() method
					tmp = elem[ ontype ];

					if ( tmp ) {
						elem[ ontype ] = null;
					}

					// Prevent re-triggering of the same event, since we already bubbled it above
					jQuery.event.triggered = type;

					if ( event.isPropagationStopped() ) {
						lastElement.addEventListener( type, stopPropagationCallback );
					}

					elem[ type ]();

					if ( event.isPropagationStopped() ) {
						lastElement.removeEventListener( type, stopPropagationCallback );
					}

					jQuery.event.triggered = undefined;

					if ( tmp ) {
						elem[ ontype ] = tmp;
					}
				}
			}
		}

		return event.result;
	},

	// Piggyback on a donor event to simulate a different one
	// Used only for `focus(in | out)` events
	simulate: function( type, elem, event ) {
		var e = jQuery.extend(
			new jQuery.Event(),
			event,
			{
				type: type,
				isSimulated: true
			}
		);

		jQuery.event.trigger( e, null, elem );
	}

} );

jQuery.fn.extend( {

	trigger: function( type, data ) {
		return this.each( function() {
			jQuery.event.trigger( type, data, this );
		} );
	},
	triggerHandler: function( type, data ) {
		var elem = this[ 0 ];
		if ( elem ) {
			return jQuery.event.trigger( type, data, elem, true );
		}
	}
} );


// Support: Firefox <=44
// Firefox doesn't have focus(in | out) events
// Related ticket - https://bugzilla.mozilla.org/show_bug.cgi?id=687787
//
// Support: Chrome <=48 - 49, Safari <=9.0 - 9.1
// focus(in | out) events fire after focus & blur events,
// which is spec violation - http://www.w3.org/TR/DOM-Level-3-Events/#events-focusevent-event-order
// Related ticket - https://bugs.chromium.org/p/chromium/issues/detail?id=449857
if ( !support.focusin ) {
	jQuery.each( { focus: "focusin", blur: "focusout" }, function( orig, fix ) {

		// Attach a single capturing handler on the document while someone wants focusin/focusout
		var handler = function( event ) {
			jQuery.event.simulate( fix, event.target, jQuery.event.fix( event ) );
		};

		jQuery.event.special[ fix ] = {
			setup: function() {

				// Handle: regular nodes (via `this.ownerDocument`), window
				// (via `this.document`) & document (via `this`).
				var doc = this.ownerDocument || this.document || this,
					attaches = dataPriv.access( doc, fix );

				if ( !attaches ) {
					doc.addEventListener( orig, handler, true );
				}
				dataPriv.access( doc, fix, ( attaches || 0 ) + 1 );
			},
			teardown: function() {
				var doc = this.ownerDocument || this.document || this,
					attaches = dataPriv.access( doc, fix ) - 1;

				if ( !attaches ) {
					doc.removeEventListener( orig, handler, true );
					dataPriv.remove( doc, fix );

				} else {
					dataPriv.access( doc, fix, attaches );
				}
			}
		};
	} );
}
var location = window.location;

var nonce = { guid: Date.now() };

var rquery = ( /\?/ );



// Cross-browser xml parsing
jQuery.parseXML = function( data ) {
	var xml, parserErrorElem;
	if ( !data || typeof data !== "string" ) {
		return null;
	}

	// Support: IE 9 - 11 only
	// IE throws on parseFromString with invalid input.
	try {
		xml = ( new window.DOMParser() ).parseFromString( data, "text/xml" );
	} catch ( e ) {}

	parserErrorElem = xml && xml.getElementsByTagName( "parsererror" )[ 0 ];
	if ( !xml || parserErrorElem ) {
		jQuery.error( "Invalid XML: " + (
			parserErrorElem ?
				jQuery.map( parserErrorElem.childNodes, function( el ) {
					return el.textContent;
				} ).join( "\n" ) :
				data
		) );
	}
	return xml;
};


var
	rbracket = /\[\]$/,
	rCRLF = /\r?\n/g,
	rsubmitterTypes = /^(?:submit|button|image|reset|file)$/i,
	rsubmittable = /^(?:input|select|textarea|keygen)/i;

function buildParams( prefix, obj, traditional, add ) {
	var name;

	if ( Array.isArray( obj ) ) {

		// Serialize array item.
		jQuery.each( obj, function( i, v ) {
			if ( traditional || rbracket.test( prefix ) ) {

				// Treat each array item as a scalar.
				add( prefix, v );

			} else {

				// Item is non-scalar (array or object), encode its numeric index.
				buildParams(
					prefix + "[" + ( typeof v === "object" && v != null ? i : "" ) + "]",
					v,
					traditional,
					add
				);
			}
		} );

	} else if ( !traditional && toType( obj ) === "object" ) {

		// Serialize object item.
		for ( name in obj ) {
			buildParams( prefix + "[" + name + "]", obj[ name ], traditional, add );
		}

	} else {

		// Serialize scalar item.
		add( prefix, obj );
	}
}

// Serialize an array of form elements or a set of
// key/values into a query string
jQuery.param = function( a, traditional ) {
	var prefix,
		s = [],
		add = function( key, valueOrFunction ) {

			// If value is a function, invoke it and use its return value
			var value = isFunction( valueOrFunction ) ?
				valueOrFunction() :
				valueOrFunction;

			s[ s.length ] = encodeURIComponent( key ) + "=" +
				encodeURIComponent( value == null ? "" : value );
		};

	if ( a == null ) {
		return "";
	}

	// If an array was passed in, assume that it is an array of form elements.
	if ( Array.isArray( a ) || ( a.jquery && !jQuery.isPlainObject( a ) ) ) {

		// Serialize the form elements
		jQuery.each( a, function() {
			add( this.name, this.value );
		} );

	} else {

		// If traditional, encode the "old" way (the way 1.3.2 or older
		// did it), otherwise encode params recursively.
		for ( prefix in a ) {
			buildParams( prefix, a[ prefix ], traditional, add );
		}
	}

	// Return the resulting serialization
	return s.join( "&" );
};

jQuery.fn.extend( {
	serialize: function() {
		return jQuery.param( this.serializeArray() );
	},
	serializeArray: function() {
		return this.map( function() {

			// Can add propHook for "elements" to filter or add form elements
			var elements = jQuery.prop( this, "elements" );
			return elements ? jQuery.makeArray( elements ) : this;
		} ).filter( function() {
			var type = this.type;

			// Use .is( ":disabled" ) so that fieldset[disabled] works
			return this.name && !jQuery( this ).is( ":disabled" ) &&
				rsubmittable.test( this.nodeName ) && !rsubmitterTypes.test( type ) &&
				( this.checked || !rcheckableType.test( type ) );
		} ).map( function( _i, elem ) {
			var val = jQuery( this ).val();

			if ( val == null ) {
				return null;
			}

			if ( Array.isArray( val ) ) {
				return jQuery.map( val, function( val ) {
					return { name: elem.name, value: val.replace( rCRLF, "\r\n" ) };
				} );
			}

			return { name: elem.name, value: val.replace( rCRLF, "\r\n" ) };
		} ).get();
	}
} );


var
	r20 = /%20/g,
	rhash = /#.*$/,
	rantiCache = /([?&])_=[^&]*/,
	rheaders = /^(.*?):[ \t]*([^\r\n]*)$/mg,

	// #7653, #8125, #8152: local protocol detection
	rlocalProtocol = /^(?:about|app|app-storage|.+-extension|file|res|widget):$/,
	rnoContent = /^(?:GET|HEAD)$/,
	rprotocol = /^\/\//,

	/* Prefilters
	 * 1) They are useful to introduce custom dataTypes (see ajax/jsonp.js for an example)
	 * 2) These are called:
	 *    - BEFORE asking for a transport
	 *    - AFTER param serialization (s.data is a string if s.processData is true)
	 * 3) key is the dataType
	 * 4) the catchall symbol "*" can be used
	 * 5) execution will start with transport dataType and THEN continue down to "*" if needed
	 */
	prefilters = {},

	/* Transports bindings
	 * 1) key is the dataType
	 * 2) the catchall symbol "*" can be used
	 * 3) selection will start with transport dataType and THEN go to "*" if needed
	 */
	transports = {},

	// Avoid comment-prolog char sequence (#10098); must appease lint and evade compression
	allTypes = "*/".concat( "*" ),

	// Anchor tag for parsing the document origin
	originAnchor = document.createElement( "a" );

originAnchor.href = location.href;

// Base "constructor" for jQuery.ajaxPrefilter and jQuery.ajaxTransport
function addToPrefiltersOrTransports( structure ) {

	// dataTypeExpression is optional and defaults to "*"
	return function( dataTypeExpression, func ) {

		if ( typeof dataTypeExpression !== "string" ) {
			func = dataTypeExpression;
			dataTypeExpression = "*";
		}

		var dataType,
			i = 0,
			dataTypes = dataTypeExpression.toLowerCase().match( rnothtmlwhite ) || [];

		if ( isFunction( func ) ) {

			// For each dataType in the dataTypeExpression
			while ( ( dataType = dataTypes[ i++ ] ) ) {

				// Prepend if requested
				if ( dataType[ 0 ] === "+" ) {
					dataType = dataType.slice( 1 ) || "*";
					( structure[ dataType ] = structure[ dataType ] || [] ).unshift( func );

				// Otherwise append
				} else {
					( structure[ dataType ] = structure[ dataType ] || [] ).push( func );
				}
			}
		}
	};
}

// Base inspection function for prefilters and transports
function inspectPrefiltersOrTransports( structure, options, originalOptions, jqXHR ) {

	var inspected = {},
		seekingTransport = ( structure === transports );

	function inspect( dataType ) {
		var selected;
		inspected[ dataType ] = true;
		jQuery.each( structure[ dataType ] || [], function( _, prefilterOrFactory ) {
			var dataTypeOrTransport = prefilterOrFactory( options, originalOptions, jqXHR );
			if ( typeof dataTypeOrTransport === "string" &&
				!seekingTransport && !inspected[ dataTypeOrTransport ] ) {

				options.dataTypes.unshift( dataTypeOrTransport );
				inspect( dataTypeOrTransport );
				return false;
			} else if ( seekingTransport ) {
				return !( selected = dataTypeOrTransport );
			}
		} );
		return selected;
	}

	return inspect( options.dataTypes[ 0 ] ) || !inspected[ "*" ] && inspect( "*" );
}

// A special extend for ajax options
// that takes "flat" options (not to be deep extended)
// Fixes #9887
function ajaxExtend( target, src ) {
	var key, deep,
		flatOptions = jQuery.ajaxSettings.flatOptions || {};

	for ( key in src ) {
		if ( src[ key ] !== undefined ) {
			( flatOptions[ key ] ? target : ( deep || ( deep = {} ) ) )[ key ] = src[ key ];
		}
	}
	if ( deep ) {
		jQuery.extend( true, target, deep );
	}

	return target;
}

/* Handles responses to an ajax request:
 * - finds the right dataType (mediates between content-type and expected dataType)
 * - returns the corresponding response
 */
function ajaxHandleResponses( s, jqXHR, responses ) {

	var ct, type, finalDataType, firstDataType,
		contents = s.contents,
		dataTypes = s.dataTypes;

	// Remove auto dataType and get content-type in the process
	while ( dataTypes[ 0 ] === "*" ) {
		dataTypes.shift();
		if ( ct === undefined ) {
			ct = s.mimeType || jqXHR.getResponseHeader( "Content-Type" );
		}
	}

	// Check if we're dealing with a known content-type
	if ( ct ) {
		for ( type in contents ) {
			if ( contents[ type ] && contents[ type ].test( ct ) ) {
				dataTypes.unshift( type );
				break;
			}
		}
	}

	// Check to see if we have a response for the expected dataType
	if ( dataTypes[ 0 ] in responses ) {
		finalDataType = dataTypes[ 0 ];
	} else {

		// Try convertible dataTypes
		for ( type in responses ) {
			if ( !dataTypes[ 0 ] || s.converters[ type + " " + dataTypes[ 0 ] ] ) {
				finalDataType = type;
				break;
			}
			if ( !firstDataType ) {
				firstDataType = type;
			}
		}

		// Or just use first one
		finalDataType = finalDataType || firstDataType;
	}

	// If we found a dataType
	// We add the dataType to the list if needed
	// and return the corresponding response
	if ( finalDataType ) {
		if ( finalDataType !== dataTypes[ 0 ] ) {
			dataTypes.unshift( finalDataType );
		}
		return responses[ finalDataType ];
	}
}

/* Chain conversions given the request and the original response
 * Also sets the responseXXX fields on the jqXHR instance
 */
function ajaxConvert( s, response, jqXHR, isSuccess ) {
	var conv2, current, conv, tmp, prev,
		converters = {},

		// Work with a copy of dataTypes in case we need to modify it for conversion
		dataTypes = s.dataTypes.slice();

	// Create converters map with lowercased keys
	if ( dataTypes[ 1 ] ) {
		for ( conv in s.converters ) {
			converters[ conv.toLowerCase() ] = s.converters[ conv ];
		}
	}

	current = dataTypes.shift();

	// Convert to each sequential dataType
	while ( current ) {

		if ( s.responseFields[ current ] ) {
			jqXHR[ s.responseFields[ current ] ] = response;
		}

		// Apply the dataFilter if provided
		if ( !prev && isSuccess && s.dataFilter ) {
			response = s.dataFilter( response, s.dataType );
		}

		prev = current;
		current = dataTypes.shift();

		if ( current ) {

			// There's only work to do if current dataType is non-auto
			if ( current === "*" ) {

				current = prev;

			// Convert response if prev dataType is non-auto and differs from current
			} else if ( prev !== "*" && prev !== current ) {

				// Seek a direct converter
				conv = converters[ prev + " " + current ] || converters[ "* " + current ];

				// If none found, seek a pair
				if ( !conv ) {
					for ( conv2 in converters ) {

						// If conv2 outputs current
						tmp = conv2.split( " " );
						if ( tmp[ 1 ] === current ) {

							// If prev can be converted to accepted input
							conv = converters[ prev + " " + tmp[ 0 ] ] ||
								converters[ "* " + tmp[ 0 ] ];
							if ( conv ) {

								// Condense equivalence converters
								if ( conv === true ) {
									conv = converters[ conv2 ];

								// Otherwise, insert the intermediate dataType
								} else if ( converters[ conv2 ] !== true ) {
									current = tmp[ 0 ];
									dataTypes.unshift( tmp[ 1 ] );
								}
								break;
							}
						}
					}
				}

				// Apply converter (if not an equivalence)
				if ( conv !== true ) {

					// Unless errors are allowed to bubble, catch and return them
					if ( conv && s.throws ) {
						response = conv( response );
					} else {
						try {
							response = conv( response );
						} catch ( e ) {
							return {
								state: "parsererror",
								error: conv ? e : "No conversion from " + prev + " to " + current
							};
						}
					}
				}
			}
		}
	}

	return { state: "success", data: response };
}

jQuery.extend( {

	// Counter for holding the number of active queries
	active: 0,

	// Last-Modified header cache for next request
	lastModified: {},
	etag: {},

	ajaxSettings: {
		url: location.href,
		type: "GET",
		isLocal: rlocalProtocol.test( location.protocol ),
		global: true,
		processData: true,
		async: true,
		contentType: "application/x-www-form-urlencoded; charset=UTF-8",

		/*
		timeout: 0,
		data: null,
		dataType: null,
		username: null,
		password: null,
		cache: null,
		throws: false,
		traditional: false,
		headers: {},
		*/

		accepts: {
			"*": allTypes,
			text: "text/plain",
			html: "text/html",
			xml: "application/xml, text/xml",
			json: "application/json, text/javascript"
		},

		contents: {
			xml: /\bxml\b/,
			html: /\bhtml/,
			json: /\bjson\b/
		},

		responseFields: {
			xml: "responseXML",
			text: "responseText",
			json: "responseJSON"
		},

		// Data converters
		// Keys separate source (or catchall "*") and destination types with a single space
		converters: {

			// Convert anything to text
			"* text": String,

			// Text to html (true = no transformation)
			"text html": true,

			// Evaluate text as a json expression
			"text json": JSON.parse,

			// Parse text as xml
			"text xml": jQuery.parseXML
		},

		// For options that shouldn't be deep extended:
		// you can add your own custom options here if
		// and when you create one that shouldn't be
		// deep extended (see ajaxExtend)
		flatOptions: {
			url: true,
			context: true
		}
	},

	// Creates a full fledged settings object into target
	// with both ajaxSettings and settings fields.
	// If target is omitted, writes into ajaxSettings.
	ajaxSetup: function( target, settings ) {
		return settings ?

			// Building a settings object
			ajaxExtend( ajaxExtend( target, jQuery.ajaxSettings ), settings ) :

			// Extending ajaxSettings
			ajaxExtend( jQuery.ajaxSettings, target );
	},

	ajaxPrefilter: addToPrefiltersOrTransports( prefilters ),
	ajaxTransport: addToPrefiltersOrTransports( transports ),

	// Main method
	ajax: function( url, options ) {

		// If url is an object, simulate pre-1.5 signature
		if ( typeof url === "object" ) {
			options = url;
			url = undefined;
		}

		// Force options to be an object
		options = options || {};

		var transport,

			// URL without anti-cache param
			cacheURL,

			// Response headers
			responseHeadersString,
			responseHeaders,

			// timeout handle
			timeoutTimer,

			// Url cleanup var
			urlAnchor,

			// Request state (becomes false upon send and true upon completion)
			completed,

			// To know if global events are to be dispatched
			fireGlobals,

			// Loop variable
			i,

			// uncached part of the url
			uncached,

			// Create the final options object
			s = jQuery.ajaxSetup( {}, options ),

			// Callbacks context
			callbackContext = s.context || s,

			// Context for global events is callbackContext if it is a DOM node or jQuery collection
			globalEventContext = s.context &&
				( callbackContext.nodeType || callbackContext.jquery ) ?
				jQuery( callbackContext ) :
				jQuery.event,

			// Deferreds
			deferred = jQuery.Deferred(),
			completeDeferred = jQuery.Callbacks( "once memory" ),

			// Status-dependent callbacks
			statusCode = s.statusCode || {},

			// Headers (they are sent all at once)
			requestHeaders = {},
			requestHeadersNames = {},

			// Default abort message
			strAbort = "canceled",

			// Fake xhr
			jqXHR = {
				readyState: 0,

				// Builds headers hashtable if needed
				getResponseHeader: function( key ) {
					var match;
					if ( completed ) {
						if ( !responseHeaders ) {
							responseHeaders = {};
							while ( ( match = rheaders.exec( responseHeadersString ) ) ) {
								responseHeaders[ match[ 1 ].toLowerCase() + " " ] =
									( responseHeaders[ match[ 1 ].toLowerCase() + " " ] || [] )
										.concat( match[ 2 ] );
							}
						}
						match = responseHeaders[ key.toLowerCase() + " " ];
					}
					return match == null ? null : match.join( ", " );
				},

				// Raw string
				getAllResponseHeaders: function() {
					return completed ? responseHeadersString : null;
				},

				// Caches the header
				setRequestHeader: function( name, value ) {
					if ( completed == null ) {
						name = requestHeadersNames[ name.toLowerCase() ] =
							requestHeadersNames[ name.toLowerCase() ] || name;
						requestHeaders[ name ] = value;
					}
					return this;
				},

				// Overrides response content-type header
				overrideMimeType: function( type ) {
					if ( completed == null ) {
						s.mimeType = type;
					}
					return this;
				},

				// Status-dependent callbacks
				statusCode: function( map ) {
					var code;
					if ( map ) {
						if ( completed ) {

							// Execute the appropriate callbacks
							jqXHR.always( map[ jqXHR.status ] );
						} else {

							// Lazy-add the new callbacks in a way that preserves old ones
							for ( code in map ) {
								statusCode[ code ] = [ statusCode[ code ], map[ code ] ];
							}
						}
					}
					return this;
				},

				// Cancel the request
				abort: function( statusText ) {
					var finalText = statusText || strAbort;
					if ( transport ) {
						transport.abort( finalText );
					}
					done( 0, finalText );
					return this;
				}
			};

		// Attach deferreds
		deferred.promise( jqXHR );

		// Add protocol if not provided (prefilters might expect it)
		// Handle falsy url in the settings object (#10093: consistency with old signature)
		// We also use the url parameter if available
		s.url = ( ( url || s.url || location.href ) + "" )
			.replace( rprotocol, location.protocol + "//" );

		// Alias method option to type as per ticket #12004
		s.type = options.method || options.type || s.method || s.type;

		// Extract dataTypes list
		s.dataTypes = ( s.dataType || "*" ).toLowerCase().match( rnothtmlwhite ) || [ "" ];

		// A cross-domain request is in order when the origin doesn't match the current origin.
		if ( s.crossDomain == null ) {
			urlAnchor = document.createElement( "a" );

			// Support: IE <=8 - 11, Edge 12 - 15
			// IE throws exception on accessing the href property if url is malformed,
			// e.g. http://example.com:80x/
			try {
				urlAnchor.href = s.url;

				// Support: IE <=8 - 11 only
				// Anchor's host property isn't correctly set when s.url is relative
				urlAnchor.href = urlAnchor.href;
				s.crossDomain = originAnchor.protocol + "//" + originAnchor.host !==
					urlAnchor.protocol + "//" + urlAnchor.host;
			} catch ( e ) {

				// If there is an error parsing the URL, assume it is crossDomain,
				// it can be rejected by the transport if it is invalid
				s.crossDomain = true;
			}
		}

		// Convert data if not already a string
		if ( s.data && s.processData && typeof s.data !== "string" ) {
			s.data = jQuery.param( s.data, s.traditional );
		}

		// Apply prefilters
		inspectPrefiltersOrTransports( prefilters, s, options, jqXHR );

		// If request was aborted inside a prefilter, stop there
		if ( completed ) {
			return jqXHR;
		}

		// We can fire global events as of now if asked to
		// Don't fire events if jQuery.event is undefined in an AMD-usage scenario (#15118)
		fireGlobals = jQuery.event && s.global;

		// Watch for a new set of requests
		if ( fireGlobals && jQuery.active++ === 0 ) {
			jQuery.event.trigger( "ajaxStart" );
		}

		// Uppercase the type
		s.type = s.type.toUpperCase();

		// Determine if request has content
		s.hasContent = !rnoContent.test( s.type );

		// Save the URL in case we're toying with the If-Modified-Since
		// and/or If-None-Match header later on
		// Remove hash to simplify url manipulation
		cacheURL = s.url.replace( rhash, "" );

		// More options handling for requests with no content
		if ( !s.hasContent ) {

			// Remember the hash so we can put it back
			uncached = s.url.slice( cacheURL.length );

			// If data is available and should be processed, append data to url
			if ( s.data && ( s.processData || typeof s.data === "string" ) ) {
				cacheURL += ( rquery.test( cacheURL ) ? "&" : "?" ) + s.data;

				// #9682: remove data so that it's not used in an eventual retry
				delete s.data;
			}

			// Add or update anti-cache param if needed
			if ( s.cache === false ) {
				cacheURL = cacheURL.replace( rantiCache, "$1" );
				uncached = ( rquery.test( cacheURL ) ? "&" : "?" ) + "_=" + ( nonce.guid++ ) +
					uncached;
			}

			// Put hash and anti-cache on the URL that will be requested (gh-1732)
			s.url = cacheURL + uncached;

		// Change '%20' to '+' if this is encoded form body content (gh-2658)
		} else if ( s.data && s.processData &&
			( s.contentType || "" ).indexOf( "application/x-www-form-urlencoded" ) === 0 ) {
			s.data = s.data.replace( r20, "+" );
		}

		// Set the If-Modified-Since and/or If-None-Match header, if in ifModified mode.
		if ( s.ifModified ) {
			if ( jQuery.lastModified[ cacheURL ] ) {
				jqXHR.setRequestHeader( "If-Modified-Since", jQuery.lastModified[ cacheURL ] );
			}
			if ( jQuery.etag[ cacheURL ] ) {
				jqXHR.setRequestHeader( "If-None-Match", jQuery.etag[ cacheURL ] );
			}
		}

		// Set the correct header, if data is being sent
		if ( s.data && s.hasContent && s.contentType !== false || options.contentType ) {
			jqXHR.setRequestHeader( "Content-Type", s.contentType );
		}

		// Set the Accepts header for the server, depending on the dataType
		jqXHR.setRequestHeader(
			"Accept",
			s.dataTypes[ 0 ] && s.accepts[ s.dataTypes[ 0 ] ] ?
				s.accepts[ s.dataTypes[ 0 ] ] +
					( s.dataTypes[ 0 ] !== "*" ? ", " + allTypes + "; q=0.01" : "" ) :
				s.accepts[ "*" ]
		);

		// Check for headers option
		for ( i in s.headers ) {
			jqXHR.setRequestHeader( i, s.headers[ i ] );
		}

		// Allow custom headers/mimetypes and early abort
		if ( s.beforeSend &&
			( s.beforeSend.call( callbackContext, jqXHR, s ) === false || completed ) ) {

			// Abort if not done already and return
			return jqXHR.abort();
		}

		// Aborting is no longer a cancellation
		strAbort = "abort";

		// Install callbacks on deferreds
		completeDeferred.add( s.complete );
		jqXHR.done( s.success );
		jqXHR.fail( s.error );

		// Get transport
		transport = inspectPrefiltersOrTransports( transports, s, options, jqXHR );

		// If no transport, we auto-abort
		if ( !transport ) {
			done( -1, "No Transport" );
		} else {
			jqXHR.readyState = 1;

			// Send global event
			if ( fireGlobals ) {
				globalEventContext.trigger( "ajaxSend", [ jqXHR, s ] );
			}

			// If request was aborted inside ajaxSend, stop there
			if ( completed ) {
				return jqXHR;
			}

			// Timeout
			if ( s.async && s.timeout > 0 ) {
				timeoutTimer = window.setTimeout( function() {
					jqXHR.abort( "timeout" );
				}, s.timeout );
			}

			try {
				completed = false;
				transport.send( requestHeaders, done );
			} catch ( e ) {

				// Rethrow post-completion exceptions
				if ( completed ) {
					throw e;
				}

				// Propagate others as results
				done( -1, e );
			}
		}

		// Callback for when everything is done
		function done( status, nativeStatusText, responses, headers ) {
			var isSuccess, success, error, response, modified,
				statusText = nativeStatusText;

			// Ignore repeat invocations
			if ( completed ) {
				return;
			}

			completed = true;

			// Clear timeout if it exists
			if ( timeoutTimer ) {
				window.clearTimeout( timeoutTimer );
			}

			// Dereference transport for early garbage collection
			// (no matter how long the jqXHR object will be used)
			transport = undefined;

			// Cache response headers
			responseHeadersString = headers || "";

			// Set readyState
			jqXHR.readyState = status > 0 ? 4 : 0;

			// Determine if successful
			isSuccess = status >= 200 && status < 300 || status === 304;

			// Get response data
			if ( responses ) {
				response = ajaxHandleResponses( s, jqXHR, responses );
			}

			// Use a noop converter for missing script but not if jsonp
			if ( !isSuccess &&
				jQuery.inArray( "script", s.dataTypes ) > -1 &&
				jQuery.inArray( "json", s.dataTypes ) < 0 ) {
				s.converters[ "text script" ] = function() {};
			}

			// Convert no matter what (that way responseXXX fields are always set)
			response = ajaxConvert( s, response, jqXHR, isSuccess );

			// If successful, handle type chaining
			if ( isSuccess ) {

				// Set the If-Modified-Since and/or If-None-Match header, if in ifModified mode.
				if ( s.ifModified ) {
					modified = jqXHR.getResponseHeader( "Last-Modified" );
					if ( modified ) {
						jQuery.lastModified[ cacheURL ] = modified;
					}
					modified = jqXHR.getResponseHeader( "etag" );
					if ( modified ) {
						jQuery.etag[ cacheURL ] = modified;
					}
				}

				// if no content
				if ( status === 204 || s.type === "HEAD" ) {
					statusText = "nocontent";

				// if not modified
				} else if ( status === 304 ) {
					statusText = "notmodified";

				// If we have data, let's convert it
				} else {
					statusText = response.state;
					success = response.data;
					error = response.error;
					isSuccess = !error;
				}
			} else {

				// Extract error from statusText and normalize for non-aborts
				error = statusText;
				if ( status || !statusText ) {
					statusText = "error";
					if ( status < 0 ) {
						status = 0;
					}
				}
			}

			// Set data for the fake xhr object
			jqXHR.status = status;
			jqXHR.statusText = ( nativeStatusText || statusText ) + "";

			// Success/Error
			if ( isSuccess ) {
				deferred.resolveWith( callbackContext, [ success, statusText, jqXHR ] );
			} else {
				deferred.rejectWith( callbackContext, [ jqXHR, statusText, error ] );
			}

			// Status-dependent callbacks
			jqXHR.statusCode( statusCode );
			statusCode = undefined;

			if ( fireGlobals ) {
				globalEventContext.trigger( isSuccess ? "ajaxSuccess" : "ajaxError",
					[ jqXHR, s, isSuccess ? success : error ] );
			}

			// Complete
			completeDeferred.fireWith( callbackContext, [ jqXHR, statusText ] );

			if ( fireGlobals ) {
				globalEventContext.trigger( "ajaxComplete", [ jqXHR, s ] );

				// Handle the global AJAX counter
				if ( !( --jQuery.active ) ) {
					jQuery.event.trigger( "ajaxStop" );
				}
			}
		}

		return jqXHR;
	},

	getJSON: function( url, data, callback ) {
		return jQuery.get( url, data, callback, "json" );
	},

	getScript: function( url, callback ) {
		return jQuery.get( url, undefined, callback, "script" );
	}
} );

jQuery.each( [ "get", "post" ], function( _i, method ) {
	jQuery[ method ] = function( url, data, callback, type ) {

		// Shift arguments if data argument was omitted
		if ( isFunction( data ) ) {
			type = type || callback;
			callback = data;
			data = undefined;
		}

		// The url can be an options object (which then must have .url)
		return jQuery.ajax( jQuery.extend( {
			url: url,
			type: method,
			dataType: type,
			data: data,
			success: callback
		}, jQuery.isPlainObject( url ) && url ) );
	};
} );

jQuery.ajaxPrefilter( function( s ) {
	var i;
	for ( i in s.headers ) {
		if ( i.toLowerCase() === "content-type" ) {
			s.contentType = s.headers[ i ] || "";
		}
	}
} );


jQuery._evalUrl = function( url, options, doc ) {
	return jQuery.ajax( {
		url: url,

		// Make this explicit, since user can override this through ajaxSetup (#11264)
		type: "GET",
		dataType: "script",
		cache: true,
		async: false,
		global: false,

		// Only evaluate the response if it is successful (gh-4126)
		// dataFilter is not invoked for failure responses, so using it instead
		// of the default converter is kludgy but it works.
		converters: {
			"text script": function() {}
		},
		dataFilter: function( response ) {
			jQuery.globalEval( response, options, doc );
		}
	} );
};


jQuery.fn.extend( {
	wrapAll: function( html ) {
		var wrap;

		if ( this[ 0 ] ) {
			if ( isFunction( html ) ) {
				html = html.call( this[ 0 ] );
			}

			// The elements to wrap the target around
			wrap = jQuery( html, this[ 0 ].ownerDocument ).eq( 0 ).clone( true );

			if ( this[ 0 ].parentNode ) {
				wrap.insertBefore( this[ 0 ] );
			}

			wrap.map( function() {
				var elem = this;

				while ( elem.firstElementChild ) {
					elem = elem.firstElementChild;
				}

				return elem;
			} ).append( this );
		}

		return this;
	},

	wrapInner: function( html ) {
		if ( isFunction( html ) ) {
			return this.each( function( i ) {
				jQuery( this ).wrapInner( html.call( this, i ) );
			} );
		}

		return this.each( function() {
			var self = jQuery( this ),
				contents = self.contents();

			if ( contents.length ) {
				contents.wrapAll( html );

			} else {
				self.append( html );
			}
		} );
	},

	wrap: function( html ) {
		var htmlIsFunction = isFunction( html );

		return this.each( function( i ) {
			jQuery( this ).wrapAll( htmlIsFunction ? html.call( this, i ) : html );
		} );
	},

	unwrap: function( selector ) {
		this.parent( selector ).not( "body" ).each( function() {
			jQuery( this ).replaceWith( this.childNodes );
		} );
		return this;
	}
} );


jQuery.expr.pseudos.hidden = function( elem ) {
	return !jQuery.expr.pseudos.visible( elem );
};
jQuery.expr.pseudos.visible = function( elem ) {
	return !!( elem.offsetWidth || elem.offsetHeight || elem.getClientRects().length );
};




jQuery.ajaxSettings.xhr = function() {
	try {
		return new window.XMLHttpRequest();
	} catch ( e ) {}
};

var xhrSuccessStatus = {

		// File protocol always yields status code 0, assume 200
		0: 200,

		// Support: IE <=9 only
		// #1450: sometimes IE returns 1223 when it should be 204
		1223: 204
	},
	xhrSupported = jQuery.ajaxSettings.xhr();

support.cors = !!xhrSupported && ( "withCredentials" in xhrSupported );
support.ajax = xhrSupported = !!xhrSupported;

jQuery.ajaxTransport( function( options ) {
	var callback, errorCallback;

	// Cross domain only allowed if supported through XMLHttpRequest
	if ( support.cors || xhrSupported && !options.crossDomain ) {
		return {
			send: function( headers, complete ) {
				var i,
					xhr = options.xhr();

				xhr.open(
					options.type,
					options.url,
					options.async,
					options.username,
					options.password
				);

				// Apply custom fields if provided
				if ( options.xhrFields ) {
					for ( i in options.xhrFields ) {
						xhr[ i ] = options.xhrFields[ i ];
					}
				}

				// Override mime type if needed
				if ( options.mimeType && xhr.overrideMimeType ) {
					xhr.overrideMimeType( options.mimeType );
				}

				// X-Requested-With header
				// For cross-domain requests, seeing as conditions for a preflight are
				// akin to a jigsaw puzzle, we simply never set it to be sure.
				// (it can always be set on a per-request basis or even using ajaxSetup)
				// For same-domain requests, won't change header if already provided.
				if ( !options.crossDomain && !headers[ "X-Requested-With" ] ) {
					headers[ "X-Requested-With" ] = "XMLHttpRequest";
				}

				// Set headers
				for ( i in headers ) {
					xhr.setRequestHeader( i, headers[ i ] );
				}

				// Callback
				callback = function( type ) {
					return function() {
						if ( callback ) {
							callback = errorCallback = xhr.onload =
								xhr.onerror = xhr.onabort = xhr.ontimeout =
									xhr.onreadystatechange = null;

							if ( type === "abort" ) {
								xhr.abort();
							} else if ( type === "error" ) {

								// Support: IE <=9 only
								// On a manual native abort, IE9 throws
								// errors on any property access that is not readyState
								if ( typeof xhr.status !== "number" ) {
									complete( 0, "error" );
								} else {
									complete(

										// File: protocol always yields status 0; see #8605, #14207
										xhr.status,
										xhr.statusText
									);
								}
							} else {
								complete(
									xhrSuccessStatus[ xhr.status ] || xhr.status,
									xhr.statusText,

									// Support: IE <=9 only
									// IE9 has no XHR2 but throws on binary (trac-11426)
									// For XHR2 non-text, let the caller handle it (gh-2498)
									( xhr.responseType || "text" ) !== "text"  ||
									typeof xhr.responseText !== "string" ?
										{ binary: xhr.response } :
										{ text: xhr.responseText },
									xhr.getAllResponseHeaders()
								);
							}
						}
					};
				};

				// Listen to events
				xhr.onload = callback();
				errorCallback = xhr.onerror = xhr.ontimeout = callback( "error" );

				// Support: IE 9 only
				// Use onreadystatechange to replace onabort
				// to handle uncaught aborts
				if ( xhr.onabort !== undefined ) {
					xhr.onabort = errorCallback;
				} else {
					xhr.onreadystatechange = function() {

						// Check readyState before timeout as it changes
						if ( xhr.readyState === 4 ) {

							// Allow onerror to be called first,
							// but that will not handle a native abort
							// Also, save errorCallback to a variable
							// as xhr.onerror cannot be accessed
							window.setTimeout( function() {
								if ( callback ) {
									errorCallback();
								}
							} );
						}
					};
				}

				// Create the abort callback
				callback = callback( "abort" );

				try {

					// Do send the request (this may raise an exception)
					xhr.send( options.hasContent && options.data || null );
				} catch ( e ) {

					// #14683: Only rethrow if this hasn't been notified as an error yet
					if ( callback ) {
						throw e;
					}
				}
			},

			abort: function() {
				if ( callback ) {
					callback();
				}
			}
		};
	}
} );




// Prevent auto-execution of scripts when no explicit dataType was provided (See gh-2432)
jQuery.ajaxPrefilter( function( s ) {
	if ( s.crossDomain ) {
		s.contents.script = false;
	}
} );

// Install script dataType
jQuery.ajaxSetup( {
	accepts: {
		script: "text/javascript, application/javascript, " +
			"application/ecmascript, application/x-ecmascript"
	},
	contents: {
		script: /\b(?:java|ecma)script\b/
	},
	converters: {
		"text script": function( text ) {
			jQuery.globalEval( text );
			return text;
		}
	}
} );

// Handle cache's special case and crossDomain
jQuery.ajaxPrefilter( "script", function( s ) {
	if ( s.cache === undefined ) {
		s.cache = false;
	}
	if ( s.crossDomain ) {
		s.type = "GET";
	}
} );

// Bind script tag hack transport
jQuery.ajaxTransport( "script", function( s ) {

	// This transport only deals with cross domain or forced-by-attrs requests
	if ( s.crossDomain || s.scriptAttrs ) {
		var script, callback;
		return {
			send: function( _, complete ) {
				script = jQuery( "<script>" )
					.attr( s.scriptAttrs || {} )
					.prop( { charset: s.scriptCharset, src: s.url } )
					.on( "load error", callback = function( evt ) {
						script.remove();
						callback = null;
						if ( evt ) {
							complete( evt.type === "error" ? 404 : 200, evt.type );
						}
					} );

				// Use native DOM manipulation to avoid our domManip AJAX trickery
				document.head.appendChild( script[ 0 ] );
			},
			abort: function() {
				if ( callback ) {
					callback();
				}
			}
		};
	}
} );




var oldCallbacks = [],
	rjsonp = /(=)\?(?=&|$)|\?\?/;

// Default jsonp settings
jQuery.ajaxSetup( {
	jsonp: "callback",
	jsonpCallback: function() {
		var callback = oldCallbacks.pop() || ( jQuery.expando + "_" + ( nonce.guid++ ) );
		this[ callback ] = true;
		return callback;
	}
} );

// Detect, normalize options and install callbacks for jsonp requests
jQuery.ajaxPrefilter( "json jsonp", function( s, originalSettings, jqXHR ) {

	var callbackName, overwritten, responseContainer,
		jsonProp = s.jsonp !== false && ( rjsonp.test( s.url ) ?
			"url" :
			typeof s.data === "string" &&
				( s.contentType || "" )
					.indexOf( "application/x-www-form-urlencoded" ) === 0 &&
				rjsonp.test( s.data ) && "data"
		);

	// Handle iff the expected data type is "jsonp" or we have a parameter to set
	if ( jsonProp || s.dataTypes[ 0 ] === "jsonp" ) {

		// Get callback name, remembering preexisting value associated with it
		callbackName = s.jsonpCallback = isFunction( s.jsonpCallback ) ?
			s.jsonpCallback() :
			s.jsonpCallback;

		// Insert callback into url or form data
		if ( jsonProp ) {
			s[ jsonProp ] = s[ jsonProp ].replace( rjsonp, "$1" + callbackName );
		} else if ( s.jsonp !== false ) {
			s.url += ( rquery.test( s.url ) ? "&" : "?" ) + s.jsonp + "=" + callbackName;
		}

		// Use data converter to retrieve json after script execution
		s.converters[ "script json" ] = function() {
			if ( !responseContainer ) {
				jQuery.error( callbackName + " was not called" );
			}
			return responseContainer[ 0 ];
		};

		// Force json dataType
		s.dataTypes[ 0 ] = "json";

		// Install callback
		overwritten = window[ callbackName ];
		window[ callbackName ] = function() {
			responseContainer = arguments;
		};

		// Clean-up function (fires after converters)
		jqXHR.always( function() {

			// If previous value didn't exist - remove it
			if ( overwritten === undefined ) {
				jQuery( window ).removeProp( callbackName );

			// Otherwise restore preexisting value
			} else {
				window[ callbackName ] = overwritten;
			}

			// Save back as free
			if ( s[ callbackName ] ) {

				// Make sure that re-using the options doesn't screw things around
				s.jsonpCallback = originalSettings.jsonpCallback;

				// Save the callback name for future use
				oldCallbacks.push( callbackName );
			}

			// Call if it was a function and we have a response
			if ( responseContainer && isFunction( overwritten ) ) {
				overwritten( responseContainer[ 0 ] );
			}

			responseContainer = overwritten = undefined;
		} );

		// Delegate to script
		return "script";
	}
} );




// Support: Safari 8 only
// In Safari 8 documents created via document.implementation.createHTMLDocument
// collapse sibling forms: the second one becomes a child of the first one.
// Because of that, this security measure has to be disabled in Safari 8.
// https://bugs.webkit.org/show_bug.cgi?id=137337
support.createHTMLDocument = ( function() {
	var body = document.implementation.createHTMLDocument( "" ).body;
	body.innerHTML = "<form></form><form></form>";
	return body.childNodes.length === 2;
} )();


// Argument "data" should be string of html
// context (optional): If specified, the fragment will be created in this context,
// defaults to document
// keepScripts (optional): If true, will include scripts passed in the html string
jQuery.parseHTML = function( data, context, keepScripts ) {
	if ( typeof data !== "string" ) {
		return [];
	}
	if ( typeof context === "boolean" ) {
		keepScripts = context;
		context = false;
	}

	var base, parsed, scripts;

	if ( !context ) {

		// Stop scripts or inline event handlers from being executed immediately
		// by using document.implementation
		if ( support.createHTMLDocument ) {
			context = document.implementation.createHTMLDocument( "" );

			// Set the base href for the created document
			// so any parsed elements with URLs
			// are based on the document's URL (gh-2965)
			base = context.createElement( "base" );
			base.href = document.location.href;
			context.head.appendChild( base );
		} else {
			context = document;
		}
	}

	parsed = rsingleTag.exec( data );
	scripts = !keepScripts && [];

	// Single tag
	if ( parsed ) {
		return [ context.createElement( parsed[ 1 ] ) ];
	}

	parsed = buildFragment( [ data ], context, scripts );

	if ( scripts && scripts.length ) {
		jQuery( scripts ).remove();
	}

	return jQuery.merge( [], parsed.childNodes );
};


/**
 * Load a url into a page
 */
jQuery.fn.load = function( url, params, callback ) {
	var selector, type, response,
		self = this,
		off = url.indexOf( " " );

	if ( off > -1 ) {
		selector = stripAndCollapse( url.slice( off ) );
		url = url.slice( 0, off );
	}

	// If it's a function
	if ( isFunction( params ) ) {

		// We assume that it's the callback
		callback = params;
		params = undefined;

	// Otherwise, build a param string
	} else if ( params && typeof params === "object" ) {
		type = "POST";
	}

	// If we have elements to modify, make the request
	if ( self.length > 0 ) {
		jQuery.ajax( {
			url: url,

			// If "type" variable is undefined, then "GET" method will be used.
			// Make value of this field explicit since
			// user can override it through ajaxSetup method
			type: type || "GET",
			dataType: "html",
			data: params
		} ).done( function( responseText ) {

			// Save response for use in complete callback
			response = arguments;

			self.html( selector ?

				// If a selector was specified, locate the right elements in a dummy div
				// Exclude scripts to avoid IE 'Permission Denied' errors
				jQuery( "<div>" ).append( jQuery.parseHTML( responseText ) ).find( selector ) :

				// Otherwise use the full result
				responseText );

		// If the request succeeds, this function gets "data", "status", "jqXHR"
		// but they are ignored because response was set above.
		// If it fails, this function gets "jqXHR", "status", "error"
		} ).always( callback && function( jqXHR, status ) {
			self.each( function() {
				callback.apply( this, response || [ jqXHR.responseText, status, jqXHR ] );
			} );
		} );
	}

	return this;
};




jQuery.expr.pseudos.animated = function( elem ) {
	return jQuery.grep( jQuery.timers, function( fn ) {
		return elem === fn.elem;
	} ).length;
};




jQuery.offset = {
	setOffset: function( elem, options, i ) {
		var curPosition, curLeft, curCSSTop, curTop, curOffset, curCSSLeft, calculatePosition,
			position = jQuery.css( elem, "position" ),
			curElem = jQuery( elem ),
			props = {};

		// Set position first, in-case top/left are set even on static elem
		if ( position === "static" ) {
			elem.style.position = "relative";
		}

		curOffset = curElem.offset();
		curCSSTop = jQuery.css( elem, "top" );
		curCSSLeft = jQuery.css( elem, "left" );
		calculatePosition = ( position === "absolute" || position === "fixed" ) &&
			( curCSSTop + curCSSLeft ).indexOf( "auto" ) > -1;

		// Need to be able to calculate position if either
		// top or left is auto and position is either absolute or fixed
		if ( calculatePosition ) {
			curPosition = curElem.position();
			curTop = curPosition.top;
			curLeft = curPosition.left;

		} else {
			curTop = parseFloat( curCSSTop ) || 0;
			curLeft = parseFloat( curCSSLeft ) || 0;
		}

		if ( isFunction( options ) ) {

			// Use jQuery.extend here to allow modification of coordinates argument (gh-1848)
			options = options.call( elem, i, jQuery.extend( {}, curOffset ) );
		}

		if ( options.top != null ) {
			props.top = ( options.top - curOffset.top ) + curTop;
		}
		if ( options.left != null ) {
			props.left = ( options.left - curOffset.left ) + curLeft;
		}

		if ( "using" in options ) {
			options.using.call( elem, props );

		} else {
			curElem.css( props );
		}
	}
};

jQuery.fn.extend( {

	// offset() relates an element's border box to the document origin
	offset: function( options ) {

		// Preserve chaining for setter
		if ( arguments.length ) {
			return options === undefined ?
				this :
				this.each( function( i ) {
					jQuery.offset.setOffset( this, options, i );
				} );
		}

		var rect, win,
			elem = this[ 0 ];

		if ( !elem ) {
			return;
		}

		// Return zeros for disconnected and hidden (display: none) elements (gh-2310)
		// Support: IE <=11 only
		// Running getBoundingClientRect on a
		// disconnected node in IE throws an error
		if ( !elem.getClientRects().length ) {
			return { top: 0, left: 0 };
		}

		// Get document-relative position by adding viewport scroll to viewport-relative gBCR
		rect = elem.getBoundingClientRect();
		win = elem.ownerDocument.defaultView;
		return {
			top: rect.top + win.pageYOffset,
			left: rect.left + win.pageXOffset
		};
	},

	// position() relates an element's margin box to its offset parent's padding box
	// This corresponds to the behavior of CSS absolute positioning
	position: function() {
		if ( !this[ 0 ] ) {
			return;
		}

		var offsetParent, offset, doc,
			elem = this[ 0 ],
			parentOffset = { top: 0, left: 0 };

		// position:fixed elements are offset from the viewport, which itself always has zero offset
		if ( jQuery.css( elem, "position" ) === "fixed" ) {

			// Assume position:fixed implies availability of getBoundingClientRect
			offset = elem.getBoundingClientRect();

		} else {
			offset = this.offset();

			// Account for the *real* offset parent, which can be the document or its root element
			// when a statically positioned element is identified
			doc = elem.ownerDocument;
			offsetParent = elem.offsetParent || doc.documentElement;
			while ( offsetParent &&
				( offsetParent === doc.body || offsetParent === doc.documentElement ) &&
				jQuery.css( offsetParent, "position" ) === "static" ) {

				offsetParent = offsetParent.parentNode;
			}
			if ( offsetParent && offsetParent !== elem && offsetParent.nodeType === 1 ) {

				// Incorporate borders into its offset, since they are outside its content origin
				parentOffset = jQuery( offsetParent ).offset();
				parentOffset.top += jQuery.css( offsetParent, "borderTopWidth", true );
				parentOffset.left += jQuery.css( offsetParent, "borderLeftWidth", true );
			}
		}

		// Subtract parent offsets and element margins
		return {
			top: offset.top - parentOffset.top - jQuery.css( elem, "marginTop", true ),
			left: offset.left - parentOffset.left - jQuery.css( elem, "marginLeft", true )
		};
	},

	// This method will return documentElement in the following cases:
	// 1) For the element inside the iframe without offsetParent, this method will return
	//    documentElement of the parent window
	// 2) For the hidden or detached element
	// 3) For body or html element, i.e. in case of the html node - it will return itself
	//
	// but those exceptions were never presented as a real life use-cases
	// and might be considered as more preferable results.
	//
	// This logic, however, is not guaranteed and can change at any point in the future
	offsetParent: function() {
		return this.map( function() {
			var offsetParent = this.offsetParent;

			while ( offsetParent && jQuery.css( offsetParent, "position" ) === "static" ) {
				offsetParent = offsetParent.offsetParent;
			}

			return offsetParent || documentElement;
		} );
	}
} );

// Create scrollLeft and scrollTop methods
jQuery.each( { scrollLeft: "pageXOffset", scrollTop: "pageYOffset" }, function( method, prop ) {
	var top = "pageYOffset" === prop;

	jQuery.fn[ method ] = function( val ) {
		return access( this, function( elem, method, val ) {

			// Coalesce documents and windows
			var win;
			if ( isWindow( elem ) ) {
				win = elem;
			} else if ( elem.nodeType === 9 ) {
				win = elem.defaultView;
			}

			if ( val === undefined ) {
				return win ? win[ prop ] : elem[ method ];
			}

			if ( win ) {
				win.scrollTo(
					!top ? val : win.pageXOffset,
					top ? val : win.pageYOffset
				);

			} else {
				elem[ method ] = val;
			}
		}, method, val, arguments.length );
	};
} );

// Support: Safari <=7 - 9.1, Chrome <=37 - 49
// Add the top/left cssHooks using jQuery.fn.position
// Webkit bug: https://bugs.webkit.org/show_bug.cgi?id=29084
// Blink bug: https://bugs.chromium.org/p/chromium/issues/detail?id=589347
// getComputedStyle returns percent when specified for top/left/bottom/right;
// rather than make the css module depend on the offset module, just check for it here
jQuery.each( [ "top", "left" ], function( _i, prop ) {
	jQuery.cssHooks[ prop ] = addGetHookIf( support.pixelPosition,
		function( elem, computed ) {
			if ( computed ) {
				computed = curCSS( elem, prop );

				// If curCSS returns percentage, fallback to offset
				return rnumnonpx.test( computed ) ?
					jQuery( elem ).position()[ prop ] + "px" :
					computed;
			}
		}
	);
} );


// Create innerHeight, innerWidth, height, width, outerHeight and outerWidth methods
jQuery.each( { Height: "height", Width: "width" }, function( name, type ) {
	jQuery.each( {
		padding: "inner" + name,
		content: type,
		"": "outer" + name
	}, function( defaultExtra, funcName ) {

		// Margin is only for outerHeight, outerWidth
		jQuery.fn[ funcName ] = function( margin, value ) {
			var chainable = arguments.length && ( defaultExtra || typeof margin !== "boolean" ),
				extra = defaultExtra || ( margin === true || value === true ? "margin" : "border" );

			return access( this, function( elem, type, value ) {
				var doc;

				if ( isWindow( elem ) ) {

					// $( window ).outerWidth/Height return w/h including scrollbars (gh-1729)
					return funcName.indexOf( "outer" ) === 0 ?
						elem[ "inner" + name ] :
						elem.document.documentElement[ "client" + name ];
				}

				// Get document width or height
				if ( elem.nodeType === 9 ) {
					doc = elem.documentElement;

					// Either scroll[Width/Height] or offset[Width/Height] or client[Width/Height],
					// whichever is greatest
					return Math.max(
						elem.body[ "scroll" + name ], doc[ "scroll" + name ],
						elem.body[ "offset" + name ], doc[ "offset" + name ],
						doc[ "client" + name ]
					);
				}

				return value === undefined ?

					// Get width or height on the element, requesting but not forcing parseFloat
					jQuery.css( elem, type, extra ) :

					// Set width or height on the element
					jQuery.style( elem, type, value, extra );
			}, type, chainable ? margin : undefined, chainable );
		};
	} );
} );


jQuery.each( [
	"ajaxStart",
	"ajaxStop",
	"ajaxComplete",
	"ajaxError",
	"ajaxSuccess",
	"ajaxSend"
], function( _i, type ) {
	jQuery.fn[ type ] = function( fn ) {
		return this.on( type, fn );
	};
} );




jQuery.fn.extend( {

	bind: function( types, data, fn ) {
		return this.on( types, null, data, fn );
	},
	unbind: function( types, fn ) {
		return this.off( types, null, fn );
	},

	delegate: function( selector, types, data, fn ) {
		return this.on( types, selector, data, fn );
	},
	undelegate: function( selector, types, fn ) {

		// ( namespace ) or ( selector, types [, fn] )
		return arguments.length === 1 ?
			this.off( selector, "**" ) :
			this.off( types, selector || "**", fn );
	},

	hover: function( fnOver, fnOut ) {
		return this.mouseenter( fnOver ).mouseleave( fnOut || fnOver );
	}
} );

jQuery.each(
	( "blur focus focusin focusout resize scroll click dblclick " +
	"mousedown mouseup mousemove mouseover mouseout mouseenter mouseleave " +
	"change select submit keydown keypress keyup contextmenu" ).split( " " ),
	function( _i, name ) {

		// Handle event binding
		jQuery.fn[ name ] = function( data, fn ) {
			return arguments.length > 0 ?
				this.on( name, null, data, fn ) :
				this.trigger( name );
		};
	}
);




// Support: Android <=4.0 only
// Make sure we trim BOM and NBSP
var rtrim = /^[\s\uFEFF\xA0]+|[\s\uFEFF\xA0]+$/g;

// Bind a function to a context, optionally partially applying any
// arguments.
// jQuery.proxy is deprecated to promote standards (specifically Function#bind)
// However, it is not slated for removal any time soon
jQuery.proxy = function( fn, context ) {
	var tmp, args, proxy;

	if ( typeof context === "string" ) {
		tmp = fn[ context ];
		context = fn;
		fn = tmp;
	}

	// Quick check to determine if target is callable, in the spec
	// this throws a TypeError, but we will just return undefined.
	if ( !isFunction( fn ) ) {
		return undefined;
	}

	// Simulated bind
	args = slice.call( arguments, 2 );
	proxy = function() {
		return fn.apply( context || this, args.concat( slice.call( arguments ) ) );
	};

	// Set the guid of unique handler to the same of original handler, so it can be removed
	proxy.guid = fn.guid = fn.guid || jQuery.guid++;

	return proxy;
};

jQuery.holdReady = function( hold ) {
	if ( hold ) {
		jQuery.readyWait++;
	} else {
		jQuery.ready( true );
	}
};
jQuery.isArray = Array.isArray;
jQuery.parseJSON = JSON.parse;
jQuery.nodeName = nodeName;
jQuery.isFunction = isFunction;
jQuery.isWindow = isWindow;
jQuery.camelCase = camelCase;
jQuery.type = toType;

jQuery.now = Date.now;

jQuery.isNumeric = function( obj ) {

	// As of jQuery 3.0, isNumeric is limited to
	// strings and numbers (primitives or objects)
	// that can be coerced to finite numbers (gh-2662)
	var type = jQuery.type( obj );
	return ( type === "number" || type === "string" ) &&

		// parseFloat NaNs numeric-cast false positives ("")
		// ...but misinterprets leading-number strings, particularly hex literals ("0x...")
		// subtraction forces infinities to NaN
		!isNaN( obj - parseFloat( obj ) );
};

jQuery.trim = function( text ) {
	return text == null ?
		"" :
		( text + "" ).replace( rtrim, "" );
};



// Register as a named AMD module, since jQuery can be concatenated with other
// files that may use define, but not via a proper concatenation script that
// understands anonymous AMD modules. A named AMD is safest and most robust
// way to register. Lowercase jquery is used because AMD module names are
// derived from file names, and jQuery is normally delivered in a lowercase
// file name. Do this after creating the global so that if an AMD module wants
// to call noConflict to hide this version of jQuery, it will work.

// Note that for maximum portability, libraries that are not jQuery should
// declare themselves as anonymous modules, and avoid setting a global if an
// AMD loader is present. jQuery is a special case. For more information, see
// https://github.com/jrburke/requirejs/wiki/Updating-existing-libraries#wiki-anon

if ( true ) {
	!(__WEBPACK_AMD_DEFINE_ARRAY__ = [], __WEBPACK_AMD_DEFINE_RESULT__ = (function() {
		return jQuery;
	}).apply(exports, __WEBPACK_AMD_DEFINE_ARRAY__),
				__WEBPACK_AMD_DEFINE_RESULT__ !== undefined && (module.exports = __WEBPACK_AMD_DEFINE_RESULT__));
}




var

	// Map over jQuery in case of overwrite
	_jQuery = window.jQuery,

	// Map over the $ in case of overwrite
	_$ = window.$;

jQuery.noConflict = function( deep ) {
	if ( window.$ === jQuery ) {
		window.$ = _$;
	}

	if ( deep && window.jQuery === jQuery ) {
		window.jQuery = _jQuery;
	}

	return jQuery;
};

// Expose jQuery and $ identifiers, even in AMD
// (#7102#comment:10, https://github.com/jquery/jquery/pull/557)
// and CommonJS for browser emulators (#13566)
if ( typeof noGlobal === "undefined" ) {
	window.jQuery = window.$ = jQuery;
}




return jQuery;
} );


/***/ }),
/* 59 */
/***/ (function(module, exports, __webpack_require__) {

module.exports = __webpack_require__(60);

/***/ }),
/* 60 */
/***/ (function(module, exports, __webpack_require__) {

var parent = __webpack_require__(61);

module.exports = parent;


/***/ }),
/* 61 */
/***/ (function(module, exports, __webpack_require__) {

var isPrototypeOf = __webpack_require__(28);
var method = __webpack_require__(62);

var ArrayPrototype = Array.prototype;

module.exports = function (it) {
  var own = it.find;
  return it === ArrayPrototype || (isPrototypeOf(ArrayPrototype, it) && own === ArrayPrototype.find) ? method : own;
};


/***/ }),
/* 62 */
/***/ (function(module, exports, __webpack_require__) {

__webpack_require__(63);
var entryVirtual = __webpack_require__(76);

module.exports = entryVirtual('Array').find;


/***/ }),
/* 63 */
/***/ (function(module, exports, __webpack_require__) {

"use strict";

var $ = __webpack_require__(5);
var $find = __webpack_require__(64).find;
var addToUnscopables = __webpack_require__(75);

var FIND = 'find';
var SKIPS_HOLES = true;

// Shouldn't skip holes
if (FIND in []) Array(1)[FIND](function () { SKIPS_HOLES = false; });

// `Array.prototype.find` method
// https://tc39.es/ecma262/#sec-array.prototype.find
$({ target: 'Array', proto: true, forced: SKIPS_HOLES }, {
  find: function find(callbackfn /* , that = undefined */) {
    return $find(this, callbackfn, arguments.length > 1 ? arguments[1] : undefined);
  }
});

// https://tc39.es/ecma262/#sec-array.prototype-@@unscopables
addToUnscopables(FIND);


/***/ }),
/* 64 */
/***/ (function(module, exports, __webpack_require__) {

var bind = __webpack_require__(48);
var uncurryThis = __webpack_require__(11);
var IndexedObject = __webpack_require__(19);
var toObject = __webpack_require__(43);
var lengthOfArrayLike = __webpack_require__(65);
var arraySpeciesCreate = __webpack_require__(68);

var push = uncurryThis([].push);

// `Array.prototype.{ forEach, map, filter, some, every, find, findIndex, filterReject }` methods implementation
var createMethod = function (TYPE) {
  var IS_MAP = TYPE == 1;
  var IS_FILTER = TYPE == 2;
  var IS_SOME = TYPE == 3;
  var IS_EVERY = TYPE == 4;
  var IS_FIND_INDEX = TYPE == 6;
  var IS_FILTER_REJECT = TYPE == 7;
  var NO_HOLES = TYPE == 5 || IS_FIND_INDEX;
  return function ($this, callbackfn, that, specificCreate) {
    var O = toObject($this);
    var self = IndexedObject(O);
    var boundFunction = bind(callbackfn, that);
    var length = lengthOfArrayLike(self);
    var index = 0;
    var create = specificCreate || arraySpeciesCreate;
    var target = IS_MAP ? create($this, length) : IS_FILTER || IS_FILTER_REJECT ? create($this, 0) : undefined;
    var value, result;
    for (;length > index; index++) if (NO_HOLES || index in self) {
      value = self[index];
      result = boundFunction(value, index, O);
      if (TYPE) {
        if (IS_MAP) target[index] = result; // map
        else if (result) switch (TYPE) {
          case 3: return true;              // some
          case 5: return value;             // find
          case 6: return index;             // findIndex
          case 2: push(target, value);      // filter
        } else switch (TYPE) {
          case 4: return false;             // every
          case 7: push(target, value);      // filterReject
        }
      }
    }
    return IS_FIND_INDEX ? -1 : IS_SOME || IS_EVERY ? IS_EVERY : target;
  };
};

module.exports = {
  // `Array.prototype.forEach` method
  // https://tc39.es/ecma262/#sec-array.prototype.foreach
  forEach: createMethod(0),
  // `Array.prototype.map` method
  // https://tc39.es/ecma262/#sec-array.prototype.map
  map: createMethod(1),
  // `Array.prototype.filter` method
  // https://tc39.es/ecma262/#sec-array.prototype.filter
  filter: createMethod(2),
  // `Array.prototype.some` method
  // https://tc39.es/ecma262/#sec-array.prototype.some
  some: createMethod(3),
  // `Array.prototype.every` method
  // https://tc39.es/ecma262/#sec-array.prototype.every
  every: createMethod(4),
  // `Array.prototype.find` method
  // https://tc39.es/ecma262/#sec-array.prototype.find
  find: createMethod(5),
  // `Array.prototype.findIndex` method
  // https://tc39.es/ecma262/#sec-array.prototype.findIndex
  findIndex: createMethod(6),
  // `Array.prototype.filterReject` method
  // https://github.com/tc39/proposal-array-filtering
  filterReject: createMethod(7)
};


/***/ }),
/* 65 */
/***/ (function(module, exports, __webpack_require__) {

var toLength = __webpack_require__(66);

// `LengthOfArrayLike` abstract operation
// https://tc39.es/ecma262/#sec-lengthofarraylike
module.exports = function (obj) {
  return toLength(obj.length);
};


/***/ }),
/* 66 */
/***/ (function(module, exports, __webpack_require__) {

var toIntegerOrInfinity = __webpack_require__(67);

var min = Math.min;

// `ToLength` abstract operation
// https://tc39.es/ecma262/#sec-tolength
module.exports = function (argument) {
  return argument > 0 ? min(toIntegerOrInfinity(argument), 0x1FFFFFFFFFFFFF) : 0; // 2 ** 53 - 1 == 9007199254740991
};


/***/ }),
/* 67 */
/***/ (function(module, exports) {

var ceil = Math.ceil;
var floor = Math.floor;

// `ToIntegerOrInfinity` abstract operation
// https://tc39.es/ecma262/#sec-tointegerorinfinity
module.exports = function (argument) {
  var number = +argument;
  // eslint-disable-next-line no-self-compare -- safe
  return number !== number || number === 0 ? 0 : (number > 0 ? floor : ceil)(number);
};


/***/ }),
/* 68 */
/***/ (function(module, exports, __webpack_require__) {

var arraySpeciesConstructor = __webpack_require__(69);

// `ArraySpeciesCreate` abstract operation
// https://tc39.es/ecma262/#sec-arrayspeciescreate
module.exports = function (originalArray, length) {
  return new (arraySpeciesConstructor(originalArray))(length === 0 ? 0 : length);
};


/***/ }),
/* 69 */
/***/ (function(module, exports, __webpack_require__) {

var global = __webpack_require__(6);
var isArray = __webpack_require__(70);
var isConstructor = __webpack_require__(71);
var isObject = __webpack_require__(24);
var wellKnownSymbol = __webpack_require__(37);

var SPECIES = wellKnownSymbol('species');
var Array = global.Array;

// a part of `ArraySpeciesCreate` abstract operation
// https://tc39.es/ecma262/#sec-arrayspeciescreate
module.exports = function (originalArray) {
  var C;
  if (isArray(originalArray)) {
    C = originalArray.constructor;
    // cross-realm fallback
    if (isConstructor(C) && (C === Array || isArray(C.prototype))) C = undefined;
    else if (isObject(C)) {
      C = C[SPECIES];
      if (C === null) C = undefined;
    }
  } return C === undefined ? Array : C;
};


/***/ }),
/* 70 */
/***/ (function(module, exports, __webpack_require__) {

var classof = __webpack_require__(20);

// `IsArray` abstract operation
// https://tc39.es/ecma262/#sec-isarray
// eslint-disable-next-line es/no-array-isarray -- safe
module.exports = Array.isArray || function isArray(argument) {
  return classof(argument) == 'Array';
};


/***/ }),
/* 71 */
/***/ (function(module, exports, __webpack_require__) {

var uncurryThis = __webpack_require__(11);
var fails = __webpack_require__(10);
var isCallable = __webpack_require__(12);
var classof = __webpack_require__(72);
var getBuiltIn = __webpack_require__(26);
var inspectSource = __webpack_require__(74);

var noop = function () { /* empty */ };
var empty = [];
var construct = getBuiltIn('Reflect', 'construct');
var constructorRegExp = /^\s*(?:class|function)\b/;
var exec = uncurryThis(constructorRegExp.exec);
var INCORRECT_TO_STRING = !constructorRegExp.exec(noop);

var isConstructorModern = function isConstructor(argument) {
  if (!isCallable(argument)) return false;
  try {
    construct(noop, empty, argument);
    return true;
  } catch (error) {
    return false;
  }
};

var isConstructorLegacy = function isConstructor(argument) {
  if (!isCallable(argument)) return false;
  switch (classof(argument)) {
    case 'AsyncFunction':
    case 'GeneratorFunction':
    case 'AsyncGeneratorFunction': return false;
  }
  try {
    // we can't check .prototype since constructors produced by .bind haven't it
    // `Function#toString` throws on some built-it function in some legacy engines
    // (for example, `DOMQuad` and similar in FF41-)
    return INCORRECT_TO_STRING || !!exec(constructorRegExp, inspectSource(argument));
  } catch (error) {
    return true;
  }
};

isConstructorLegacy.sham = true;

// `IsConstructor` abstract operation
// https://tc39.es/ecma262/#sec-isconstructor
module.exports = !construct || fails(function () {
  var called;
  return isConstructorModern(isConstructorModern.call)
    || !isConstructorModern(Object)
    || !isConstructorModern(function () { called = true; })
    || called;
}) ? isConstructorLegacy : isConstructorModern;


/***/ }),
/* 72 */
/***/ (function(module, exports, __webpack_require__) {

var global = __webpack_require__(6);
var TO_STRING_TAG_SUPPORT = __webpack_require__(73);
var isCallable = __webpack_require__(12);
var classofRaw = __webpack_require__(20);
var wellKnownSymbol = __webpack_require__(37);

var TO_STRING_TAG = wellKnownSymbol('toStringTag');
var Object = global.Object;

// ES3 wrong here
var CORRECT_ARGUMENTS = classofRaw(function () { return arguments; }()) == 'Arguments';

// fallback for IE11 Script Access Denied error
var tryGet = function (it, key) {
  try {
    return it[key];
  } catch (error) { /* empty */ }
};

// getting tag from ES6+ `Object.prototype.toString`
module.exports = TO_STRING_TAG_SUPPORT ? classofRaw : function (it) {
  var O, tag, result;
  return it === undefined ? 'Undefined' : it === null ? 'Null'
    // @@toStringTag case
    : typeof (tag = tryGet(O = Object(it), TO_STRING_TAG)) == 'string' ? tag
    // builtinTag case
    : CORRECT_ARGUMENTS ? classofRaw(O)
    // ES3 arguments fallback
    : (result = classofRaw(O)) == 'Object' && isCallable(O.callee) ? 'Arguments' : result;
};


/***/ }),
/* 73 */
/***/ (function(module, exports, __webpack_require__) {

var wellKnownSymbol = __webpack_require__(37);

var TO_STRING_TAG = wellKnownSymbol('toStringTag');
var test = {};

test[TO_STRING_TAG] = 'z';

module.exports = String(test) === '[object z]';


/***/ }),
/* 74 */
/***/ (function(module, exports, __webpack_require__) {

var uncurryThis = __webpack_require__(11);
var isCallable = __webpack_require__(12);
var store = __webpack_require__(40);

var functionToString = uncurryThis(Function.toString);

// this helper broken in `core-js@3.4.1-3.4.4`, so we can't use `shared` helper
if (!isCallable(store.inspectSource)) {
  store.inspectSource = function (it) {
    return functionToString(it);
  };
}

module.exports = store.inspectSource;


/***/ }),
/* 75 */
/***/ (function(module, exports) {

module.exports = function () { /* empty */ };


/***/ }),
/* 76 */
/***/ (function(module, exports, __webpack_require__) {

var path = __webpack_require__(27);

module.exports = function (CONSTRUCTOR) {
  return path[CONSTRUCTOR + 'Prototype'];
};


/***/ }),
/* 77 */
/***/ (function(module, __webpack_exports__, __webpack_require__) {

"use strict";
__webpack_require__.r(__webpack_exports__);
/* harmony export (binding) */ __webpack_require__.d(__webpack_exports__, "Integrations", function() { return INTEGRATIONS; });
/* harmony import */ var _exports_js__WEBPACK_IMPORTED_MODULE_0__ = __webpack_require__(78);
/* harmony import */ var _sentry_core__WEBPACK_IMPORTED_MODULE_1__ = __webpack_require__(79);
/* harmony reexport (safe) */ __webpack_require__.d(__webpack_exports__, "FunctionToString", function() { return _sentry_core__WEBPACK_IMPORTED_MODULE_1__["FunctionToString"]; });

/* harmony reexport (safe) */ __webpack_require__.d(__webpack_exports__, "Hub", function() { return _sentry_core__WEBPACK_IMPORTED_MODULE_1__["Hub"]; });

/* harmony reexport (safe) */ __webpack_require__.d(__webpack_exports__, "InboundFilters", function() { return _sentry_core__WEBPACK_IMPORTED_MODULE_1__["InboundFilters"]; });

/* harmony reexport (safe) */ __webpack_require__.d(__webpack_exports__, "SDK_VERSION", function() { return _sentry_core__WEBPACK_IMPORTED_MODULE_1__["SDK_VERSION"]; });

/* harmony reexport (safe) */ __webpack_require__.d(__webpack_exports__, "Scope", function() { return _sentry_core__WEBPACK_IMPORTED_MODULE_1__["Scope"]; });

/* harmony reexport (safe) */ __webpack_require__.d(__webpack_exports__, "addBreadcrumb", function() { return _sentry_core__WEBPACK_IMPORTED_MODULE_1__["addBreadcrumb"]; });

/* harmony reexport (safe) */ __webpack_require__.d(__webpack_exports__, "addGlobalEventProcessor", function() { return _sentry_core__WEBPACK_IMPORTED_MODULE_1__["addGlobalEventProcessor"]; });

/* harmony reexport (safe) */ __webpack_require__.d(__webpack_exports__, "captureEvent", function() { return _sentry_core__WEBPACK_IMPORTED_MODULE_1__["captureEvent"]; });

/* harmony reexport (safe) */ __webpack_require__.d(__webpack_exports__, "captureException", function() { return _sentry_core__WEBPACK_IMPORTED_MODULE_1__["captureException"]; });

/* harmony reexport (safe) */ __webpack_require__.d(__webpack_exports__, "captureMessage", function() { return _sentry_core__WEBPACK_IMPORTED_MODULE_1__["captureMessage"]; });

/* harmony reexport (safe) */ __webpack_require__.d(__webpack_exports__, "configureScope", function() { return _sentry_core__WEBPACK_IMPORTED_MODULE_1__["configureScope"]; });

/* harmony reexport (safe) */ __webpack_require__.d(__webpack_exports__, "createTransport", function() { return _sentry_core__WEBPACK_IMPORTED_MODULE_1__["createTransport"]; });

/* harmony reexport (safe) */ __webpack_require__.d(__webpack_exports__, "getCurrentHub", function() { return _sentry_core__WEBPACK_IMPORTED_MODULE_1__["getCurrentHub"]; });

/* harmony reexport (safe) */ __webpack_require__.d(__webpack_exports__, "getHubFromCarrier", function() { return _sentry_core__WEBPACK_IMPORTED_MODULE_1__["getHubFromCarrier"]; });

/* harmony reexport (safe) */ __webpack_require__.d(__webpack_exports__, "makeMain", function() { return _sentry_core__WEBPACK_IMPORTED_MODULE_1__["makeMain"]; });

/* harmony reexport (safe) */ __webpack_require__.d(__webpack_exports__, "setContext", function() { return _sentry_core__WEBPACK_IMPORTED_MODULE_1__["setContext"]; });

/* harmony reexport (safe) */ __webpack_require__.d(__webpack_exports__, "setExtra", function() { return _sentry_core__WEBPACK_IMPORTED_MODULE_1__["setExtra"]; });

/* harmony reexport (safe) */ __webpack_require__.d(__webpack_exports__, "setExtras", function() { return _sentry_core__WEBPACK_IMPORTED_MODULE_1__["setExtras"]; });

/* harmony reexport (safe) */ __webpack_require__.d(__webpack_exports__, "setTag", function() { return _sentry_core__WEBPACK_IMPORTED_MODULE_1__["setTag"]; });

/* harmony reexport (safe) */ __webpack_require__.d(__webpack_exports__, "setTags", function() { return _sentry_core__WEBPACK_IMPORTED_MODULE_1__["setTags"]; });

/* harmony reexport (safe) */ __webpack_require__.d(__webpack_exports__, "setUser", function() { return _sentry_core__WEBPACK_IMPORTED_MODULE_1__["setUser"]; });

/* harmony reexport (safe) */ __webpack_require__.d(__webpack_exports__, "startTransaction", function() { return _sentry_core__WEBPACK_IMPORTED_MODULE_1__["startTransaction"]; });

/* harmony reexport (safe) */ __webpack_require__.d(__webpack_exports__, "withScope", function() { return _sentry_core__WEBPACK_IMPORTED_MODULE_1__["withScope"]; });

/* harmony import */ var _sentry_utils__WEBPACK_IMPORTED_MODULE_2__ = __webpack_require__(82);
/* harmony import */ var _integrations_index_js__WEBPACK_IMPORTED_MODULE_3__ = __webpack_require__(150);
/* harmony import */ var _client_js__WEBPACK_IMPORTED_MODULE_4__ = __webpack_require__(140);
/* harmony reexport (safe) */ __webpack_require__.d(__webpack_exports__, "BrowserClient", function() { return _client_js__WEBPACK_IMPORTED_MODULE_4__["BrowserClient"]; });

/* harmony import */ var _transports_fetch_js__WEBPACK_IMPORTED_MODULE_5__ = __webpack_require__(145);
/* harmony reexport (safe) */ __webpack_require__.d(__webpack_exports__, "makeFetchTransport", function() { return _transports_fetch_js__WEBPACK_IMPORTED_MODULE_5__["makeFetchTransport"]; });

/* harmony import */ var _transports_xhr_js__WEBPACK_IMPORTED_MODULE_6__ = __webpack_require__(146);
/* harmony reexport (safe) */ __webpack_require__.d(__webpack_exports__, "makeXHRTransport", function() { return _transports_xhr_js__WEBPACK_IMPORTED_MODULE_6__["makeXHRTransport"]; });

/* harmony import */ var _stack_parsers_js__WEBPACK_IMPORTED_MODULE_7__ = __webpack_require__(147);
/* harmony reexport (safe) */ __webpack_require__.d(__webpack_exports__, "chromeStackLineParser", function() { return _stack_parsers_js__WEBPACK_IMPORTED_MODULE_7__["chromeStackLineParser"]; });

/* harmony reexport (safe) */ __webpack_require__.d(__webpack_exports__, "defaultStackLineParsers", function() { return _stack_parsers_js__WEBPACK_IMPORTED_MODULE_7__["defaultStackLineParsers"]; });

/* harmony reexport (safe) */ __webpack_require__.d(__webpack_exports__, "defaultStackParser", function() { return _stack_parsers_js__WEBPACK_IMPORTED_MODULE_7__["defaultStackParser"]; });

/* harmony reexport (safe) */ __webpack_require__.d(__webpack_exports__, "geckoStackLineParser", function() { return _stack_parsers_js__WEBPACK_IMPORTED_MODULE_7__["geckoStackLineParser"]; });

/* harmony reexport (safe) */ __webpack_require__.d(__webpack_exports__, "opera10StackLineParser", function() { return _stack_parsers_js__WEBPACK_IMPORTED_MODULE_7__["opera10StackLineParser"]; });

/* harmony reexport (safe) */ __webpack_require__.d(__webpack_exports__, "opera11StackLineParser", function() { return _stack_parsers_js__WEBPACK_IMPORTED_MODULE_7__["opera11StackLineParser"]; });

/* harmony reexport (safe) */ __webpack_require__.d(__webpack_exports__, "winjsStackLineParser", function() { return _stack_parsers_js__WEBPACK_IMPORTED_MODULE_7__["winjsStackLineParser"]; });

/* harmony import */ var _sdk_js__WEBPACK_IMPORTED_MODULE_8__ = __webpack_require__(148);
/* harmony reexport (safe) */ __webpack_require__.d(__webpack_exports__, "close", function() { return _sdk_js__WEBPACK_IMPORTED_MODULE_8__["close"]; });

/* harmony reexport (safe) */ __webpack_require__.d(__webpack_exports__, "defaultIntegrations", function() { return _sdk_js__WEBPACK_IMPORTED_MODULE_8__["defaultIntegrations"]; });

/* harmony reexport (safe) */ __webpack_require__.d(__webpack_exports__, "flush", function() { return _sdk_js__WEBPACK_IMPORTED_MODULE_8__["flush"]; });

/* harmony reexport (safe) */ __webpack_require__.d(__webpack_exports__, "forceLoad", function() { return _sdk_js__WEBPACK_IMPORTED_MODULE_8__["forceLoad"]; });

/* harmony reexport (safe) */ __webpack_require__.d(__webpack_exports__, "init", function() { return _sdk_js__WEBPACK_IMPORTED_MODULE_8__["init"]; });

/* harmony reexport (safe) */ __webpack_require__.d(__webpack_exports__, "lastEventId", function() { return _sdk_js__WEBPACK_IMPORTED_MODULE_8__["lastEventId"]; });

/* harmony reexport (safe) */ __webpack_require__.d(__webpack_exports__, "onLoad", function() { return _sdk_js__WEBPACK_IMPORTED_MODULE_8__["onLoad"]; });

/* harmony reexport (safe) */ __webpack_require__.d(__webpack_exports__, "showReportDialog", function() { return _sdk_js__WEBPACK_IMPORTED_MODULE_8__["showReportDialog"]; });

/* harmony reexport (safe) */ __webpack_require__.d(__webpack_exports__, "wrap", function() { return _sdk_js__WEBPACK_IMPORTED_MODULE_8__["wrap"]; });

/* harmony import */ var _integrations_globalhandlers_js__WEBPACK_IMPORTED_MODULE_9__ = __webpack_require__(151);
/* harmony reexport (safe) */ __webpack_require__.d(__webpack_exports__, "GlobalHandlers", function() { return _integrations_globalhandlers_js__WEBPACK_IMPORTED_MODULE_9__["GlobalHandlers"]; });

/* harmony import */ var _integrations_trycatch_js__WEBPACK_IMPORTED_MODULE_10__ = __webpack_require__(152);
/* harmony reexport (safe) */ __webpack_require__.d(__webpack_exports__, "TryCatch", function() { return _integrations_trycatch_js__WEBPACK_IMPORTED_MODULE_10__["TryCatch"]; });

/* harmony import */ var _integrations_breadcrumbs_js__WEBPACK_IMPORTED_MODULE_11__ = __webpack_require__(142);
/* harmony reexport (safe) */ __webpack_require__.d(__webpack_exports__, "Breadcrumbs", function() { return _integrations_breadcrumbs_js__WEBPACK_IMPORTED_MODULE_11__["Breadcrumbs"]; });

/* harmony import */ var _integrations_linkederrors_js__WEBPACK_IMPORTED_MODULE_12__ = __webpack_require__(153);
/* harmony reexport (safe) */ __webpack_require__.d(__webpack_exports__, "LinkedErrors", function() { return _integrations_linkederrors_js__WEBPACK_IMPORTED_MODULE_12__["LinkedErrors"]; });

/* harmony import */ var _integrations_httpcontext_js__WEBPACK_IMPORTED_MODULE_13__ = __webpack_require__(154);
/* harmony reexport (safe) */ __webpack_require__.d(__webpack_exports__, "HttpContext", function() { return _integrations_httpcontext_js__WEBPACK_IMPORTED_MODULE_13__["HttpContext"]; });

/* harmony import */ var _integrations_dedupe_js__WEBPACK_IMPORTED_MODULE_14__ = __webpack_require__(155);
/* harmony reexport (safe) */ __webpack_require__.d(__webpack_exports__, "Dedupe", function() { return _integrations_dedupe_js__WEBPACK_IMPORTED_MODULE_14__["Dedupe"]; });


















let windowIntegrations = {};

// This block is needed to add compatibility with the integrations packages when used with a CDN
var _window = Object(_sentry_utils__WEBPACK_IMPORTED_MODULE_2__["getGlobalObject"])();
if (_window.Sentry && _window.Sentry.Integrations) {
  windowIntegrations = _window.Sentry.Integrations;
}

var INTEGRATIONS = {
  ...windowIntegrations,
  ..._sentry_core__WEBPACK_IMPORTED_MODULE_1__["Integrations"],
  ..._integrations_index_js__WEBPACK_IMPORTED_MODULE_3__,
};


//# sourceMappingURL=index.js.map


/***/ }),
/* 78 */
/***/ (function(module, __webpack_exports__, __webpack_require__) {

"use strict";
__webpack_require__.r(__webpack_exports__);
/* harmony import */ var _sentry_core__WEBPACK_IMPORTED_MODULE_0__ = __webpack_require__(79);
/* harmony reexport (safe) */ __webpack_require__.d(__webpack_exports__, "FunctionToString", function() { return _sentry_core__WEBPACK_IMPORTED_MODULE_0__["FunctionToString"]; });

/* harmony reexport (safe) */ __webpack_require__.d(__webpack_exports__, "Hub", function() { return _sentry_core__WEBPACK_IMPORTED_MODULE_0__["Hub"]; });

/* harmony reexport (safe) */ __webpack_require__.d(__webpack_exports__, "InboundFilters", function() { return _sentry_core__WEBPACK_IMPORTED_MODULE_0__["InboundFilters"]; });

/* harmony reexport (safe) */ __webpack_require__.d(__webpack_exports__, "SDK_VERSION", function() { return _sentry_core__WEBPACK_IMPORTED_MODULE_0__["SDK_VERSION"]; });

/* harmony reexport (safe) */ __webpack_require__.d(__webpack_exports__, "Scope", function() { return _sentry_core__WEBPACK_IMPORTED_MODULE_0__["Scope"]; });

/* harmony reexport (safe) */ __webpack_require__.d(__webpack_exports__, "addBreadcrumb", function() { return _sentry_core__WEBPACK_IMPORTED_MODULE_0__["addBreadcrumb"]; });

/* harmony reexport (safe) */ __webpack_require__.d(__webpack_exports__, "addGlobalEventProcessor", function() { return _sentry_core__WEBPACK_IMPORTED_MODULE_0__["addGlobalEventProcessor"]; });

/* harmony reexport (safe) */ __webpack_require__.d(__webpack_exports__, "captureEvent", function() { return _sentry_core__WEBPACK_IMPORTED_MODULE_0__["captureEvent"]; });

/* harmony reexport (safe) */ __webpack_require__.d(__webpack_exports__, "captureException", function() { return _sentry_core__WEBPACK_IMPORTED_MODULE_0__["captureException"]; });

/* harmony reexport (safe) */ __webpack_require__.d(__webpack_exports__, "captureMessage", function() { return _sentry_core__WEBPACK_IMPORTED_MODULE_0__["captureMessage"]; });

/* harmony reexport (safe) */ __webpack_require__.d(__webpack_exports__, "configureScope", function() { return _sentry_core__WEBPACK_IMPORTED_MODULE_0__["configureScope"]; });

/* harmony reexport (safe) */ __webpack_require__.d(__webpack_exports__, "createTransport", function() { return _sentry_core__WEBPACK_IMPORTED_MODULE_0__["createTransport"]; });

/* harmony reexport (safe) */ __webpack_require__.d(__webpack_exports__, "getCurrentHub", function() { return _sentry_core__WEBPACK_IMPORTED_MODULE_0__["getCurrentHub"]; });

/* harmony reexport (safe) */ __webpack_require__.d(__webpack_exports__, "getHubFromCarrier", function() { return _sentry_core__WEBPACK_IMPORTED_MODULE_0__["getHubFromCarrier"]; });

/* harmony reexport (safe) */ __webpack_require__.d(__webpack_exports__, "makeMain", function() { return _sentry_core__WEBPACK_IMPORTED_MODULE_0__["makeMain"]; });

/* harmony reexport (safe) */ __webpack_require__.d(__webpack_exports__, "setContext", function() { return _sentry_core__WEBPACK_IMPORTED_MODULE_0__["setContext"]; });

/* harmony reexport (safe) */ __webpack_require__.d(__webpack_exports__, "setExtra", function() { return _sentry_core__WEBPACK_IMPORTED_MODULE_0__["setExtra"]; });

/* harmony reexport (safe) */ __webpack_require__.d(__webpack_exports__, "setExtras", function() { return _sentry_core__WEBPACK_IMPORTED_MODULE_0__["setExtras"]; });

/* harmony reexport (safe) */ __webpack_require__.d(__webpack_exports__, "setTag", function() { return _sentry_core__WEBPACK_IMPORTED_MODULE_0__["setTag"]; });

/* harmony reexport (safe) */ __webpack_require__.d(__webpack_exports__, "setTags", function() { return _sentry_core__WEBPACK_IMPORTED_MODULE_0__["setTags"]; });

/* harmony reexport (safe) */ __webpack_require__.d(__webpack_exports__, "setUser", function() { return _sentry_core__WEBPACK_IMPORTED_MODULE_0__["setUser"]; });

/* harmony reexport (safe) */ __webpack_require__.d(__webpack_exports__, "startTransaction", function() { return _sentry_core__WEBPACK_IMPORTED_MODULE_0__["startTransaction"]; });

/* harmony reexport (safe) */ __webpack_require__.d(__webpack_exports__, "withScope", function() { return _sentry_core__WEBPACK_IMPORTED_MODULE_0__["withScope"]; });

/* harmony import */ var _client_js__WEBPACK_IMPORTED_MODULE_1__ = __webpack_require__(140);
/* harmony reexport (safe) */ __webpack_require__.d(__webpack_exports__, "BrowserClient", function() { return _client_js__WEBPACK_IMPORTED_MODULE_1__["BrowserClient"]; });

/* harmony import */ var _transports_index_js__WEBPACK_IMPORTED_MODULE_2__ = __webpack_require__(144);
/* harmony import */ var _stack_parsers_js__WEBPACK_IMPORTED_MODULE_3__ = __webpack_require__(147);
/* harmony reexport (safe) */ __webpack_require__.d(__webpack_exports__, "chromeStackLineParser", function() { return _stack_parsers_js__WEBPACK_IMPORTED_MODULE_3__["chromeStackLineParser"]; });

/* harmony reexport (safe) */ __webpack_require__.d(__webpack_exports__, "defaultStackLineParsers", function() { return _stack_parsers_js__WEBPACK_IMPORTED_MODULE_3__["defaultStackLineParsers"]; });

/* harmony reexport (safe) */ __webpack_require__.d(__webpack_exports__, "defaultStackParser", function() { return _stack_parsers_js__WEBPACK_IMPORTED_MODULE_3__["defaultStackParser"]; });

/* harmony reexport (safe) */ __webpack_require__.d(__webpack_exports__, "geckoStackLineParser", function() { return _stack_parsers_js__WEBPACK_IMPORTED_MODULE_3__["geckoStackLineParser"]; });

/* harmony reexport (safe) */ __webpack_require__.d(__webpack_exports__, "opera10StackLineParser", function() { return _stack_parsers_js__WEBPACK_IMPORTED_MODULE_3__["opera10StackLineParser"]; });

/* harmony reexport (safe) */ __webpack_require__.d(__webpack_exports__, "opera11StackLineParser", function() { return _stack_parsers_js__WEBPACK_IMPORTED_MODULE_3__["opera11StackLineParser"]; });

/* harmony reexport (safe) */ __webpack_require__.d(__webpack_exports__, "winjsStackLineParser", function() { return _stack_parsers_js__WEBPACK_IMPORTED_MODULE_3__["winjsStackLineParser"]; });

/* harmony import */ var _sdk_js__WEBPACK_IMPORTED_MODULE_4__ = __webpack_require__(148);
/* harmony reexport (safe) */ __webpack_require__.d(__webpack_exports__, "close", function() { return _sdk_js__WEBPACK_IMPORTED_MODULE_4__["close"]; });

/* harmony reexport (safe) */ __webpack_require__.d(__webpack_exports__, "defaultIntegrations", function() { return _sdk_js__WEBPACK_IMPORTED_MODULE_4__["defaultIntegrations"]; });

/* harmony reexport (safe) */ __webpack_require__.d(__webpack_exports__, "flush", function() { return _sdk_js__WEBPACK_IMPORTED_MODULE_4__["flush"]; });

/* harmony reexport (safe) */ __webpack_require__.d(__webpack_exports__, "forceLoad", function() { return _sdk_js__WEBPACK_IMPORTED_MODULE_4__["forceLoad"]; });

/* harmony reexport (safe) */ __webpack_require__.d(__webpack_exports__, "init", function() { return _sdk_js__WEBPACK_IMPORTED_MODULE_4__["init"]; });

/* harmony reexport (safe) */ __webpack_require__.d(__webpack_exports__, "lastEventId", function() { return _sdk_js__WEBPACK_IMPORTED_MODULE_4__["lastEventId"]; });

/* harmony reexport (safe) */ __webpack_require__.d(__webpack_exports__, "onLoad", function() { return _sdk_js__WEBPACK_IMPORTED_MODULE_4__["onLoad"]; });

/* harmony reexport (safe) */ __webpack_require__.d(__webpack_exports__, "showReportDialog", function() { return _sdk_js__WEBPACK_IMPORTED_MODULE_4__["showReportDialog"]; });

/* harmony reexport (safe) */ __webpack_require__.d(__webpack_exports__, "wrap", function() { return _sdk_js__WEBPACK_IMPORTED_MODULE_4__["wrap"]; });

/* harmony import */ var _integrations_index_js__WEBPACK_IMPORTED_MODULE_5__ = __webpack_require__(150);







;

;
;
//# sourceMappingURL=exports.js.map


/***/ }),
/* 79 */
/***/ (function(module, __webpack_exports__, __webpack_require__) {

"use strict";
__webpack_require__.r(__webpack_exports__);
/* harmony import */ var _sentry_hub__WEBPACK_IMPORTED_MODULE_0__ = __webpack_require__(80);
/* harmony reexport (safe) */ __webpack_require__.d(__webpack_exports__, "Hub", function() { return _sentry_hub__WEBPACK_IMPORTED_MODULE_0__["Hub"]; });

/* harmony reexport (safe) */ __webpack_require__.d(__webpack_exports__, "Scope", function() { return _sentry_hub__WEBPACK_IMPORTED_MODULE_0__["Scope"]; });

/* harmony reexport (safe) */ __webpack_require__.d(__webpack_exports__, "addBreadcrumb", function() { return _sentry_hub__WEBPACK_IMPORTED_MODULE_0__["addBreadcrumb"]; });

/* harmony reexport (safe) */ __webpack_require__.d(__webpack_exports__, "addGlobalEventProcessor", function() { return _sentry_hub__WEBPACK_IMPORTED_MODULE_0__["addGlobalEventProcessor"]; });

/* harmony reexport (safe) */ __webpack_require__.d(__webpack_exports__, "captureEvent", function() { return _sentry_hub__WEBPACK_IMPORTED_MODULE_0__["captureEvent"]; });

/* harmony reexport (safe) */ __webpack_require__.d(__webpack_exports__, "captureException", function() { return _sentry_hub__WEBPACK_IMPORTED_MODULE_0__["captureException"]; });

/* harmony reexport (safe) */ __webpack_require__.d(__webpack_exports__, "captureMessage", function() { return _sentry_hub__WEBPACK_IMPORTED_MODULE_0__["captureMessage"]; });

/* harmony reexport (safe) */ __webpack_require__.d(__webpack_exports__, "configureScope", function() { return _sentry_hub__WEBPACK_IMPORTED_MODULE_0__["configureScope"]; });

/* harmony reexport (safe) */ __webpack_require__.d(__webpack_exports__, "getCurrentHub", function() { return _sentry_hub__WEBPACK_IMPORTED_MODULE_0__["getCurrentHub"]; });

/* harmony reexport (safe) */ __webpack_require__.d(__webpack_exports__, "getHubFromCarrier", function() { return _sentry_hub__WEBPACK_IMPORTED_MODULE_0__["getHubFromCarrier"]; });

/* harmony reexport (safe) */ __webpack_require__.d(__webpack_exports__, "makeMain", function() { return _sentry_hub__WEBPACK_IMPORTED_MODULE_0__["makeMain"]; });

/* harmony reexport (safe) */ __webpack_require__.d(__webpack_exports__, "setContext", function() { return _sentry_hub__WEBPACK_IMPORTED_MODULE_0__["setContext"]; });

/* harmony reexport (safe) */ __webpack_require__.d(__webpack_exports__, "setExtra", function() { return _sentry_hub__WEBPACK_IMPORTED_MODULE_0__["setExtra"]; });

/* harmony reexport (safe) */ __webpack_require__.d(__webpack_exports__, "setExtras", function() { return _sentry_hub__WEBPACK_IMPORTED_MODULE_0__["setExtras"]; });

/* harmony reexport (safe) */ __webpack_require__.d(__webpack_exports__, "setTag", function() { return _sentry_hub__WEBPACK_IMPORTED_MODULE_0__["setTag"]; });

/* harmony reexport (safe) */ __webpack_require__.d(__webpack_exports__, "setTags", function() { return _sentry_hub__WEBPACK_IMPORTED_MODULE_0__["setTags"]; });

/* harmony reexport (safe) */ __webpack_require__.d(__webpack_exports__, "setUser", function() { return _sentry_hub__WEBPACK_IMPORTED_MODULE_0__["setUser"]; });

/* harmony reexport (safe) */ __webpack_require__.d(__webpack_exports__, "startTransaction", function() { return _sentry_hub__WEBPACK_IMPORTED_MODULE_0__["startTransaction"]; });

/* harmony reexport (safe) */ __webpack_require__.d(__webpack_exports__, "withScope", function() { return _sentry_hub__WEBPACK_IMPORTED_MODULE_0__["withScope"]; });

/* harmony import */ var _api_js__WEBPACK_IMPORTED_MODULE_1__ = __webpack_require__(130);
/* harmony reexport (safe) */ __webpack_require__.d(__webpack_exports__, "getEnvelopeEndpointWithUrlEncodedAuth", function() { return _api_js__WEBPACK_IMPORTED_MODULE_1__["getEnvelopeEndpointWithUrlEncodedAuth"]; });

/* harmony reexport (safe) */ __webpack_require__.d(__webpack_exports__, "getReportDialogEndpoint", function() { return _api_js__WEBPACK_IMPORTED_MODULE_1__["getReportDialogEndpoint"]; });

/* harmony import */ var _baseclient_js__WEBPACK_IMPORTED_MODULE_2__ = __webpack_require__(131);
/* harmony reexport (safe) */ __webpack_require__.d(__webpack_exports__, "BaseClient", function() { return _baseclient_js__WEBPACK_IMPORTED_MODULE_2__["BaseClient"]; });

/* harmony import */ var _sdk_js__WEBPACK_IMPORTED_MODULE_3__ = __webpack_require__(134);
/* harmony reexport (safe) */ __webpack_require__.d(__webpack_exports__, "initAndBind", function() { return _sdk_js__WEBPACK_IMPORTED_MODULE_3__["initAndBind"]; });

/* harmony import */ var _transports_base_js__WEBPACK_IMPORTED_MODULE_4__ = __webpack_require__(135);
/* harmony reexport (safe) */ __webpack_require__.d(__webpack_exports__, "createTransport", function() { return _transports_base_js__WEBPACK_IMPORTED_MODULE_4__["createTransport"]; });

/* harmony import */ var _version_js__WEBPACK_IMPORTED_MODULE_5__ = __webpack_require__(136);
/* harmony reexport (safe) */ __webpack_require__.d(__webpack_exports__, "SDK_VERSION", function() { return _version_js__WEBPACK_IMPORTED_MODULE_5__["SDK_VERSION"]; });

/* harmony import */ var _integration_js__WEBPACK_IMPORTED_MODULE_6__ = __webpack_require__(133);
/* harmony reexport (safe) */ __webpack_require__.d(__webpack_exports__, "getIntegrationsToSetup", function() { return _integration_js__WEBPACK_IMPORTED_MODULE_6__["getIntegrationsToSetup"]; });

/* harmony import */ var _integrations_index_js__WEBPACK_IMPORTED_MODULE_7__ = __webpack_require__(137);
/* harmony reexport (module object) */ __webpack_require__.d(__webpack_exports__, "Integrations", function() { return _integrations_index_js__WEBPACK_IMPORTED_MODULE_7__; });
/* harmony import */ var _integrations_functiontostring_js__WEBPACK_IMPORTED_MODULE_8__ = __webpack_require__(138);
/* harmony reexport (safe) */ __webpack_require__.d(__webpack_exports__, "FunctionToString", function() { return _integrations_functiontostring_js__WEBPACK_IMPORTED_MODULE_8__["FunctionToString"]; });

/* harmony import */ var _integrations_inboundfilters_js__WEBPACK_IMPORTED_MODULE_9__ = __webpack_require__(139);
/* harmony reexport (safe) */ __webpack_require__.d(__webpack_exports__, "InboundFilters", function() { return _integrations_inboundfilters_js__WEBPACK_IMPORTED_MODULE_9__["InboundFilters"]; });













;
//# sourceMappingURL=index.js.map


/***/ }),
/* 80 */
/***/ (function(module, __webpack_exports__, __webpack_require__) {

"use strict";
__webpack_require__.r(__webpack_exports__);
/* harmony import */ var _scope_js__WEBPACK_IMPORTED_MODULE_0__ = __webpack_require__(81);
/* harmony reexport (safe) */ __webpack_require__.d(__webpack_exports__, "Scope", function() { return _scope_js__WEBPACK_IMPORTED_MODULE_0__["Scope"]; });

/* harmony reexport (safe) */ __webpack_require__.d(__webpack_exports__, "addGlobalEventProcessor", function() { return _scope_js__WEBPACK_IMPORTED_MODULE_0__["addGlobalEventProcessor"]; });

/* harmony import */ var _session_js__WEBPACK_IMPORTED_MODULE_1__ = __webpack_require__(126);
/* harmony reexport (safe) */ __webpack_require__.d(__webpack_exports__, "closeSession", function() { return _session_js__WEBPACK_IMPORTED_MODULE_1__["closeSession"]; });

/* harmony reexport (safe) */ __webpack_require__.d(__webpack_exports__, "makeSession", function() { return _session_js__WEBPACK_IMPORTED_MODULE_1__["makeSession"]; });

/* harmony reexport (safe) */ __webpack_require__.d(__webpack_exports__, "updateSession", function() { return _session_js__WEBPACK_IMPORTED_MODULE_1__["updateSession"]; });

/* harmony import */ var _sessionflusher_js__WEBPACK_IMPORTED_MODULE_2__ = __webpack_require__(127);
/* harmony reexport (safe) */ __webpack_require__.d(__webpack_exports__, "SessionFlusher", function() { return _sessionflusher_js__WEBPACK_IMPORTED_MODULE_2__["SessionFlusher"]; });

/* harmony import */ var _hub_js__WEBPACK_IMPORTED_MODULE_3__ = __webpack_require__(128);
/* harmony reexport (safe) */ __webpack_require__.d(__webpack_exports__, "Hub", function() { return _hub_js__WEBPACK_IMPORTED_MODULE_3__["Hub"]; });

/* harmony reexport (safe) */ __webpack_require__.d(__webpack_exports__, "getCurrentHub", function() { return _hub_js__WEBPACK_IMPORTED_MODULE_3__["getCurrentHub"]; });

/* harmony reexport (safe) */ __webpack_require__.d(__webpack_exports__, "getHubFromCarrier", function() { return _hub_js__WEBPACK_IMPORTED_MODULE_3__["getHubFromCarrier"]; });

/* harmony reexport (safe) */ __webpack_require__.d(__webpack_exports__, "getMainCarrier", function() { return _hub_js__WEBPACK_IMPORTED_MODULE_3__["getMainCarrier"]; });

/* harmony reexport (safe) */ __webpack_require__.d(__webpack_exports__, "makeMain", function() { return _hub_js__WEBPACK_IMPORTED_MODULE_3__["makeMain"]; });

/* harmony reexport (safe) */ __webpack_require__.d(__webpack_exports__, "setHubOnCarrier", function() { return _hub_js__WEBPACK_IMPORTED_MODULE_3__["setHubOnCarrier"]; });

/* harmony import */ var _exports_js__WEBPACK_IMPORTED_MODULE_4__ = __webpack_require__(129);
/* harmony reexport (safe) */ __webpack_require__.d(__webpack_exports__, "addBreadcrumb", function() { return _exports_js__WEBPACK_IMPORTED_MODULE_4__["addBreadcrumb"]; });

/* harmony reexport (safe) */ __webpack_require__.d(__webpack_exports__, "captureEvent", function() { return _exports_js__WEBPACK_IMPORTED_MODULE_4__["captureEvent"]; });

/* harmony reexport (safe) */ __webpack_require__.d(__webpack_exports__, "captureException", function() { return _exports_js__WEBPACK_IMPORTED_MODULE_4__["captureException"]; });

/* harmony reexport (safe) */ __webpack_require__.d(__webpack_exports__, "captureMessage", function() { return _exports_js__WEBPACK_IMPORTED_MODULE_4__["captureMessage"]; });

/* harmony reexport (safe) */ __webpack_require__.d(__webpack_exports__, "configureScope", function() { return _exports_js__WEBPACK_IMPORTED_MODULE_4__["configureScope"]; });

/* harmony reexport (safe) */ __webpack_require__.d(__webpack_exports__, "setContext", function() { return _exports_js__WEBPACK_IMPORTED_MODULE_4__["setContext"]; });

/* harmony reexport (safe) */ __webpack_require__.d(__webpack_exports__, "setExtra", function() { return _exports_js__WEBPACK_IMPORTED_MODULE_4__["setExtra"]; });

/* harmony reexport (safe) */ __webpack_require__.d(__webpack_exports__, "setExtras", function() { return _exports_js__WEBPACK_IMPORTED_MODULE_4__["setExtras"]; });

/* harmony reexport (safe) */ __webpack_require__.d(__webpack_exports__, "setTag", function() { return _exports_js__WEBPACK_IMPORTED_MODULE_4__["setTag"]; });

/* harmony reexport (safe) */ __webpack_require__.d(__webpack_exports__, "setTags", function() { return _exports_js__WEBPACK_IMPORTED_MODULE_4__["setTags"]; });

/* harmony reexport (safe) */ __webpack_require__.d(__webpack_exports__, "setUser", function() { return _exports_js__WEBPACK_IMPORTED_MODULE_4__["setUser"]; });

/* harmony reexport (safe) */ __webpack_require__.d(__webpack_exports__, "startTransaction", function() { return _exports_js__WEBPACK_IMPORTED_MODULE_4__["startTransaction"]; });

/* harmony reexport (safe) */ __webpack_require__.d(__webpack_exports__, "withScope", function() { return _exports_js__WEBPACK_IMPORTED_MODULE_4__["withScope"]; });







;
//# sourceMappingURL=index.js.map


/***/ }),
/* 81 */
/***/ (function(module, __webpack_exports__, __webpack_require__) {

"use strict";
__webpack_require__.r(__webpack_exports__);
/* harmony export (binding) */ __webpack_require__.d(__webpack_exports__, "Scope", function() { return Scope; });
/* harmony export (binding) */ __webpack_require__.d(__webpack_exports__, "addGlobalEventProcessor", function() { return addGlobalEventProcessor; });
/* harmony import */ var _sentry_utils__WEBPACK_IMPORTED_MODULE_0__ = __webpack_require__(82);
/* harmony import */ var _session_js__WEBPACK_IMPORTED_MODULE_1__ = __webpack_require__(126);



/**
 * Absolute maximum number of breadcrumbs added to an event.
 * The `maxBreadcrumbs` option cannot be higher than this value.
 */
var MAX_BREADCRUMBS = 100;

/**
 * Holds additional event information. {@link Scope.applyToEvent} will be
 * called by the client before an event will be sent.
 */
class Scope  {
  /** Flag if notifying is happening. */
  

  /** Callback for client to receive scope changes. */
  

  /** Callback list that will be called after {@link applyToEvent}. */
  

  /** Array of breadcrumbs. */
  

  /** User */
  

  /** Tags */
  

  /** Extra */
  

  /** Contexts */
  

  /** Attachments */
  

  /**
   * A place to stash data which is needed at some point in the SDK's event processing pipeline but which shouldn't get
   * sent to Sentry
   */
  

  /** Fingerprint */
  

  /** Severity */
    

  /** Transaction Name */
  

  /** Span */
  

  /** Session */
  

  /** Request Mode Session Status */
  

   constructor() {
    this._notifyingListeners = false;
    this._scopeListeners = [];
    this._eventProcessors = [];
    this._breadcrumbs = [];
    this._attachments = [];
    this._user = {};
    this._tags = {};
    this._extra = {};
    this._contexts = {};
    this._sdkProcessingMetadata = {};
  }

  /**
   * Inherit values from the parent scope.
   * @param scope to clone.
   */
   static clone(scope) {
    var newScope = new Scope();
    if (scope) {
      newScope._breadcrumbs = [...scope._breadcrumbs];
      newScope._tags = { ...scope._tags };
      newScope._extra = { ...scope._extra };
      newScope._contexts = { ...scope._contexts };
      newScope._user = scope._user;
      newScope._level = scope._level;
      newScope._span = scope._span;
      newScope._session = scope._session;
      newScope._transactionName = scope._transactionName;
      newScope._fingerprint = scope._fingerprint;
      newScope._eventProcessors = [...scope._eventProcessors];
      newScope._requestSession = scope._requestSession;
      newScope._attachments = [...scope._attachments];
    }
    return newScope;
  }

  /**
   * Add internal on change listener. Used for sub SDKs that need to store the scope.
   * @hidden
   */
   addScopeListener(callback) {
    this._scopeListeners.push(callback);
  }

  /**
   * @inheritDoc
   */
   addEventProcessor(callback) {
    this._eventProcessors.push(callback);
    return this;
  }

  /**
   * @inheritDoc
   */
   setUser(user) {
    this._user = user || {};
    if (this._session) {
      Object(_session_js__WEBPACK_IMPORTED_MODULE_1__["updateSession"])(this._session, { user });
    }
    this._notifyScopeListeners();
    return this;
  }

  /**
   * @inheritDoc
   */
   getUser() {
    return this._user;
  }

  /**
   * @inheritDoc
   */
   getRequestSession() {
    return this._requestSession;
  }

  /**
   * @inheritDoc
   */
   setRequestSession(requestSession) {
    this._requestSession = requestSession;
    return this;
  }

  /**
   * @inheritDoc
   */
   setTags(tags) {
    this._tags = {
      ...this._tags,
      ...tags,
    };
    this._notifyScopeListeners();
    return this;
  }

  /**
   * @inheritDoc
   */
   setTag(key, value) {
    this._tags = { ...this._tags, [key]: value };
    this._notifyScopeListeners();
    return this;
  }

  /**
   * @inheritDoc
   */
   setExtras(extras) {
    this._extra = {
      ...this._extra,
      ...extras,
    };
    this._notifyScopeListeners();
    return this;
  }

  /**
   * @inheritDoc
   */
   setExtra(key, extra) {
    this._extra = { ...this._extra, [key]: extra };
    this._notifyScopeListeners();
    return this;
  }

  /**
   * @inheritDoc
   */
   setFingerprint(fingerprint) {
    this._fingerprint = fingerprint;
    this._notifyScopeListeners();
    return this;
  }

  /**
   * @inheritDoc
   */
   setLevel(
        level,
  ) {
    this._level = level;
    this._notifyScopeListeners();
    return this;
  }

  /**
   * @inheritDoc
   */
   setTransactionName(name) {
    this._transactionName = name;
    this._notifyScopeListeners();
    return this;
  }

  /**
   * @inheritDoc
   */
   setContext(key, context) {
    if (context === null) {
            delete this._contexts[key];
    } else {
      this._contexts = { ...this._contexts, [key]: context };
    }

    this._notifyScopeListeners();
    return this;
  }

  /**
   * @inheritDoc
   */
   setSpan(span) {
    this._span = span;
    this._notifyScopeListeners();
    return this;
  }

  /**
   * @inheritDoc
   */
   getSpan() {
    return this._span;
  }

  /**
   * @inheritDoc
   */
   getTransaction() {
    // Often, this span (if it exists at all) will be a transaction, but it's not guaranteed to be. Regardless, it will
    // have a pointer to the currently-active transaction.
    var span = this.getSpan();
    return span && span.transaction;
  }

  /**
   * @inheritDoc
   */
   setSession(session) {
    if (!session) {
      delete this._session;
    } else {
      this._session = session;
    }
    this._notifyScopeListeners();
    return this;
  }

  /**
   * @inheritDoc
   */
   getSession() {
    return this._session;
  }

  /**
   * @inheritDoc
   */
   update(captureContext) {
    if (!captureContext) {
      return this;
    }

    if (typeof captureContext === 'function') {
      var updatedScope = (captureContext )(this);
      return updatedScope instanceof Scope ? updatedScope : this;
    }

    if (captureContext instanceof Scope) {
      this._tags = { ...this._tags, ...captureContext._tags };
      this._extra = { ...this._extra, ...captureContext._extra };
      this._contexts = { ...this._contexts, ...captureContext._contexts };
      if (captureContext._user && Object.keys(captureContext._user).length) {
        this._user = captureContext._user;
      }
      if (captureContext._level) {
        this._level = captureContext._level;
      }
      if (captureContext._fingerprint) {
        this._fingerprint = captureContext._fingerprint;
      }
      if (captureContext._requestSession) {
        this._requestSession = captureContext._requestSession;
      }
    } else if (Object(_sentry_utils__WEBPACK_IMPORTED_MODULE_0__["isPlainObject"])(captureContext)) {
            captureContext = captureContext ;
      this._tags = { ...this._tags, ...captureContext.tags };
      this._extra = { ...this._extra, ...captureContext.extra };
      this._contexts = { ...this._contexts, ...captureContext.contexts };
      if (captureContext.user) {
        this._user = captureContext.user;
      }
      if (captureContext.level) {
        this._level = captureContext.level;
      }
      if (captureContext.fingerprint) {
        this._fingerprint = captureContext.fingerprint;
      }
      if (captureContext.requestSession) {
        this._requestSession = captureContext.requestSession;
      }
    }

    return this;
  }

  /**
   * @inheritDoc
   */
   clear() {
    this._breadcrumbs = [];
    this._tags = {};
    this._extra = {};
    this._user = {};
    this._contexts = {};
    this._level = undefined;
    this._transactionName = undefined;
    this._fingerprint = undefined;
    this._requestSession = undefined;
    this._span = undefined;
    this._session = undefined;
    this._notifyScopeListeners();
    this._attachments = [];
    return this;
  }

  /**
   * @inheritDoc
   */
   addBreadcrumb(breadcrumb, maxBreadcrumbs) {
    var maxCrumbs = typeof maxBreadcrumbs === 'number' ? Math.min(maxBreadcrumbs, MAX_BREADCRUMBS) : MAX_BREADCRUMBS;

    // No data has been changed, so don't notify scope listeners
    if (maxCrumbs <= 0) {
      return this;
    }

    var mergedBreadcrumb = {
      timestamp: Object(_sentry_utils__WEBPACK_IMPORTED_MODULE_0__["dateTimestampInSeconds"])(),
      ...breadcrumb,
    };
    this._breadcrumbs = [...this._breadcrumbs, mergedBreadcrumb].slice(-maxCrumbs);
    this._notifyScopeListeners();

    return this;
  }

  /**
   * @inheritDoc
   */
   clearBreadcrumbs() {
    this._breadcrumbs = [];
    this._notifyScopeListeners();
    return this;
  }

  /**
   * @inheritDoc
   */
   addAttachment(attachment) {
    this._attachments.push(attachment);
    return this;
  }

  /**
   * @inheritDoc
   */
   getAttachments() {
    return this._attachments;
  }

  /**
   * @inheritDoc
   */
   clearAttachments() {
    this._attachments = [];
    return this;
  }

  /**
   * Applies the current context and fingerprint to the event.
   * Note that breadcrumbs will be added by the client.
   * Also if the event has already breadcrumbs on it, we do not merge them.
   * @param event Event
   * @param hint May contain additional information about the original exception.
   * @hidden
   */
   applyToEvent(event, hint = {}) {
    if (this._extra && Object.keys(this._extra).length) {
      event.extra = { ...this._extra, ...event.extra };
    }
    if (this._tags && Object.keys(this._tags).length) {
      event.tags = { ...this._tags, ...event.tags };
    }
    if (this._user && Object.keys(this._user).length) {
      event.user = { ...this._user, ...event.user };
    }
    if (this._contexts && Object.keys(this._contexts).length) {
      event.contexts = { ...this._contexts, ...event.contexts };
    }
    if (this._level) {
      event.level = this._level;
    }
    if (this._transactionName) {
      event.transaction = this._transactionName;
    }

    // We want to set the trace context for normal events only if there isn't already
    // a trace context on the event. There is a product feature in place where we link
    // errors with transaction and it relies on that.
    if (this._span) {
      event.contexts = { trace: this._span.getTraceContext(), ...event.contexts };
      var transactionName = this._span.transaction && this._span.transaction.name;
      if (transactionName) {
        event.tags = { transaction: transactionName, ...event.tags };
      }
    }

    this._applyFingerprint(event);

    event.breadcrumbs = [...(event.breadcrumbs || []), ...this._breadcrumbs];
    event.breadcrumbs = event.breadcrumbs.length > 0 ? event.breadcrumbs : undefined;

    event.sdkProcessingMetadata = { ...event.sdkProcessingMetadata, ...this._sdkProcessingMetadata };

    return this._notifyEventProcessors([...getGlobalEventProcessors(), ...this._eventProcessors], event, hint);
  }

  /**
   * Add data which will be accessible during event processing but won't get sent to Sentry
   */
   setSDKProcessingMetadata(newData) {
    this._sdkProcessingMetadata = { ...this._sdkProcessingMetadata, ...newData };

    return this;
  }

  /**
   * This will be called after {@link applyToEvent} is finished.
   */
   _notifyEventProcessors(
    processors,
    event,
    hint,
    index = 0,
  ) {
    return new _sentry_utils__WEBPACK_IMPORTED_MODULE_0__["SyncPromise"]((resolve, reject) => {
      var processor = processors[index];
      if (event === null || typeof processor !== 'function') {
        resolve(event);
      } else {
        var result = processor({ ...event }, hint) ;

        (typeof __SENTRY_DEBUG__ === 'undefined' || __SENTRY_DEBUG__) &&
          processor.id &&
          result === null &&
          _sentry_utils__WEBPACK_IMPORTED_MODULE_0__["logger"].log(`Event processor "${processor.id}" dropped event`);

        if (Object(_sentry_utils__WEBPACK_IMPORTED_MODULE_0__["isThenable"])(result)) {
          void result
            .then(final => this._notifyEventProcessors(processors, final, hint, index + 1).then(resolve))
            .then(null, reject);
        } else {
          void this._notifyEventProcessors(processors, result, hint, index + 1)
            .then(resolve)
            .then(null, reject);
        }
      }
    });
  }

  /**
   * This will be called on every set call.
   */
   _notifyScopeListeners() {
    // We need this check for this._notifyingListeners to be able to work on scope during updates
    // If this check is not here we'll produce endless recursion when something is done with the scope
    // during the callback.
    if (!this._notifyingListeners) {
      this._notifyingListeners = true;
      this._scopeListeners.forEach(callback => {
        callback(this);
      });
      this._notifyingListeners = false;
    }
  }

  /**
   * Applies fingerprint from the scope to the event if there's one,
   * uses message if there's one instead or get rid of empty fingerprint
   */
   _applyFingerprint(event) {
    // Make sure it's an array first and we actually have something in place
    event.fingerprint = event.fingerprint
      ? Array.isArray(event.fingerprint)
        ? event.fingerprint
        : [event.fingerprint]
      : [];

    // If we have something on the scope, then merge it with event
    if (this._fingerprint) {
      event.fingerprint = event.fingerprint.concat(this._fingerprint);
    }

    // If we have no data at all, remove empty array default
    if (event.fingerprint && !event.fingerprint.length) {
      delete event.fingerprint;
    }
  }
}

/**
 * Returns the global event processors.
 */
function getGlobalEventProcessors() {
  return Object(_sentry_utils__WEBPACK_IMPORTED_MODULE_0__["getGlobalSingleton"])('globalEventProcessors', () => []);
}

/**
 * Add a EventProcessor to be kept globally.
 * @param callback EventProcessor to add
 */
function addGlobalEventProcessor(callback) {
  getGlobalEventProcessors().push(callback);
}


//# sourceMappingURL=scope.js.map


/***/ }),
/* 82 */
/***/ (function(module, __webpack_exports__, __webpack_require__) {

"use strict";
__webpack_require__.r(__webpack_exports__);
/* harmony import */ var _browser_js__WEBPACK_IMPORTED_MODULE_0__ = __webpack_require__(83);
/* harmony reexport (safe) */ __webpack_require__.d(__webpack_exports__, "getLocationHref", function() { return _browser_js__WEBPACK_IMPORTED_MODULE_0__["getLocationHref"]; });

/* harmony reexport (safe) */ __webpack_require__.d(__webpack_exports__, "htmlTreeAsString", function() { return _browser_js__WEBPACK_IMPORTED_MODULE_0__["htmlTreeAsString"]; });

/* harmony import */ var _dsn_js__WEBPACK_IMPORTED_MODULE_1__ = __webpack_require__(90);
/* harmony reexport (safe) */ __webpack_require__.d(__webpack_exports__, "dsnToString", function() { return _dsn_js__WEBPACK_IMPORTED_MODULE_1__["dsnToString"]; });

/* harmony reexport (safe) */ __webpack_require__.d(__webpack_exports__, "extensionRelayDSN", function() { return _dsn_js__WEBPACK_IMPORTED_MODULE_1__["extensionRelayDSN"]; });

/* harmony reexport (safe) */ __webpack_require__.d(__webpack_exports__, "makeDsn", function() { return _dsn_js__WEBPACK_IMPORTED_MODULE_1__["makeDsn"]; });

/* harmony import */ var _error_js__WEBPACK_IMPORTED_MODULE_2__ = __webpack_require__(91);
/* harmony reexport (safe) */ __webpack_require__.d(__webpack_exports__, "SentryError", function() { return _error_js__WEBPACK_IMPORTED_MODULE_2__["SentryError"]; });

/* harmony import */ var _global_js__WEBPACK_IMPORTED_MODULE_3__ = __webpack_require__(84);
/* harmony reexport (safe) */ __webpack_require__.d(__webpack_exports__, "getGlobalObject", function() { return _global_js__WEBPACK_IMPORTED_MODULE_3__["getGlobalObject"]; });

/* harmony reexport (safe) */ __webpack_require__.d(__webpack_exports__, "getGlobalSingleton", function() { return _global_js__WEBPACK_IMPORTED_MODULE_3__["getGlobalSingleton"]; });

/* harmony import */ var _instrument_js__WEBPACK_IMPORTED_MODULE_4__ = __webpack_require__(92);
/* harmony reexport (safe) */ __webpack_require__.d(__webpack_exports__, "addInstrumentationHandler", function() { return _instrument_js__WEBPACK_IMPORTED_MODULE_4__["addInstrumentationHandler"]; });

/* harmony import */ var _is_js__WEBPACK_IMPORTED_MODULE_5__ = __webpack_require__(89);
/* harmony reexport (safe) */ __webpack_require__.d(__webpack_exports__, "isDOMError", function() { return _is_js__WEBPACK_IMPORTED_MODULE_5__["isDOMError"]; });

/* harmony reexport (safe) */ __webpack_require__.d(__webpack_exports__, "isDOMException", function() { return _is_js__WEBPACK_IMPORTED_MODULE_5__["isDOMException"]; });

/* harmony reexport (safe) */ __webpack_require__.d(__webpack_exports__, "isElement", function() { return _is_js__WEBPACK_IMPORTED_MODULE_5__["isElement"]; });

/* harmony reexport (safe) */ __webpack_require__.d(__webpack_exports__, "isError", function() { return _is_js__WEBPACK_IMPORTED_MODULE_5__["isError"]; });

/* harmony reexport (safe) */ __webpack_require__.d(__webpack_exports__, "isErrorEvent", function() { return _is_js__WEBPACK_IMPORTED_MODULE_5__["isErrorEvent"]; });

/* harmony reexport (safe) */ __webpack_require__.d(__webpack_exports__, "isEvent", function() { return _is_js__WEBPACK_IMPORTED_MODULE_5__["isEvent"]; });

/* harmony reexport (safe) */ __webpack_require__.d(__webpack_exports__, "isInstanceOf", function() { return _is_js__WEBPACK_IMPORTED_MODULE_5__["isInstanceOf"]; });

/* harmony reexport (safe) */ __webpack_require__.d(__webpack_exports__, "isNaN", function() { return _is_js__WEBPACK_IMPORTED_MODULE_5__["isNaN"]; });

/* harmony reexport (safe) */ __webpack_require__.d(__webpack_exports__, "isPlainObject", function() { return _is_js__WEBPACK_IMPORTED_MODULE_5__["isPlainObject"]; });

/* harmony reexport (safe) */ __webpack_require__.d(__webpack_exports__, "isPrimitive", function() { return _is_js__WEBPACK_IMPORTED_MODULE_5__["isPrimitive"]; });

/* harmony reexport (safe) */ __webpack_require__.d(__webpack_exports__, "isRegExp", function() { return _is_js__WEBPACK_IMPORTED_MODULE_5__["isRegExp"]; });

/* harmony reexport (safe) */ __webpack_require__.d(__webpack_exports__, "isString", function() { return _is_js__WEBPACK_IMPORTED_MODULE_5__["isString"]; });

/* harmony reexport (safe) */ __webpack_require__.d(__webpack_exports__, "isSyntheticEvent", function() { return _is_js__WEBPACK_IMPORTED_MODULE_5__["isSyntheticEvent"]; });

/* harmony reexport (safe) */ __webpack_require__.d(__webpack_exports__, "isThenable", function() { return _is_js__WEBPACK_IMPORTED_MODULE_5__["isThenable"]; });

/* harmony import */ var _logger_js__WEBPACK_IMPORTED_MODULE_6__ = __webpack_require__(93);
/* harmony reexport (safe) */ __webpack_require__.d(__webpack_exports__, "CONSOLE_LEVELS", function() { return _logger_js__WEBPACK_IMPORTED_MODULE_6__["CONSOLE_LEVELS"]; });

/* harmony reexport (safe) */ __webpack_require__.d(__webpack_exports__, "consoleSandbox", function() { return _logger_js__WEBPACK_IMPORTED_MODULE_6__["consoleSandbox"]; });

/* harmony reexport (safe) */ __webpack_require__.d(__webpack_exports__, "logger", function() { return _logger_js__WEBPACK_IMPORTED_MODULE_6__["logger"]; });

/* harmony import */ var _memo_js__WEBPACK_IMPORTED_MODULE_7__ = __webpack_require__(112);
/* harmony reexport (safe) */ __webpack_require__.d(__webpack_exports__, "memoBuilder", function() { return _memo_js__WEBPACK_IMPORTED_MODULE_7__["memoBuilder"]; });

/* harmony import */ var _misc_js__WEBPACK_IMPORTED_MODULE_8__ = __webpack_require__(113);
/* harmony reexport (safe) */ __webpack_require__.d(__webpack_exports__, "addContextToFrame", function() { return _misc_js__WEBPACK_IMPORTED_MODULE_8__["addContextToFrame"]; });

/* harmony reexport (safe) */ __webpack_require__.d(__webpack_exports__, "addExceptionMechanism", function() { return _misc_js__WEBPACK_IMPORTED_MODULE_8__["addExceptionMechanism"]; });

/* harmony reexport (safe) */ __webpack_require__.d(__webpack_exports__, "addExceptionTypeValue", function() { return _misc_js__WEBPACK_IMPORTED_MODULE_8__["addExceptionTypeValue"]; });

/* harmony reexport (safe) */ __webpack_require__.d(__webpack_exports__, "checkOrSetAlreadyCaught", function() { return _misc_js__WEBPACK_IMPORTED_MODULE_8__["checkOrSetAlreadyCaught"]; });

/* harmony reexport (safe) */ __webpack_require__.d(__webpack_exports__, "getEventDescription", function() { return _misc_js__WEBPACK_IMPORTED_MODULE_8__["getEventDescription"]; });

/* harmony reexport (safe) */ __webpack_require__.d(__webpack_exports__, "parseSemver", function() { return _misc_js__WEBPACK_IMPORTED_MODULE_8__["parseSemver"]; });

/* harmony reexport (safe) */ __webpack_require__.d(__webpack_exports__, "parseUrl", function() { return _misc_js__WEBPACK_IMPORTED_MODULE_8__["parseUrl"]; });

/* harmony reexport (safe) */ __webpack_require__.d(__webpack_exports__, "stripUrlQueryAndFragment", function() { return _misc_js__WEBPACK_IMPORTED_MODULE_8__["stripUrlQueryAndFragment"]; });

/* harmony reexport (safe) */ __webpack_require__.d(__webpack_exports__, "uuid4", function() { return _misc_js__WEBPACK_IMPORTED_MODULE_8__["uuid4"]; });

/* harmony import */ var _node_js__WEBPACK_IMPORTED_MODULE_9__ = __webpack_require__(85);
/* harmony reexport (safe) */ __webpack_require__.d(__webpack_exports__, "dynamicRequire", function() { return _node_js__WEBPACK_IMPORTED_MODULE_9__["dynamicRequire"]; });

/* harmony reexport (safe) */ __webpack_require__.d(__webpack_exports__, "isNodeEnv", function() { return _node_js__WEBPACK_IMPORTED_MODULE_9__["isNodeEnv"]; });

/* harmony reexport (safe) */ __webpack_require__.d(__webpack_exports__, "loadModule", function() { return _node_js__WEBPACK_IMPORTED_MODULE_9__["loadModule"]; });

/* harmony import */ var _normalize_js__WEBPACK_IMPORTED_MODULE_10__ = __webpack_require__(114);
/* harmony reexport (safe) */ __webpack_require__.d(__webpack_exports__, "normalize", function() { return _normalize_js__WEBPACK_IMPORTED_MODULE_10__["normalize"]; });

/* harmony reexport (safe) */ __webpack_require__.d(__webpack_exports__, "normalizeToSize", function() { return _normalize_js__WEBPACK_IMPORTED_MODULE_10__["normalizeToSize"]; });

/* harmony reexport (safe) */ __webpack_require__.d(__webpack_exports__, "walk", function() { return _normalize_js__WEBPACK_IMPORTED_MODULE_10__["walk"]; });

/* harmony import */ var _object_js__WEBPACK_IMPORTED_MODULE_11__ = __webpack_require__(94);
/* harmony reexport (safe) */ __webpack_require__.d(__webpack_exports__, "addNonEnumerableProperty", function() { return _object_js__WEBPACK_IMPORTED_MODULE_11__["addNonEnumerableProperty"]; });

/* harmony reexport (safe) */ __webpack_require__.d(__webpack_exports__, "convertToPlainObject", function() { return _object_js__WEBPACK_IMPORTED_MODULE_11__["convertToPlainObject"]; });

/* harmony reexport (safe) */ __webpack_require__.d(__webpack_exports__, "dropUndefinedKeys", function() { return _object_js__WEBPACK_IMPORTED_MODULE_11__["dropUndefinedKeys"]; });

/* harmony reexport (safe) */ __webpack_require__.d(__webpack_exports__, "extractExceptionKeysForMessage", function() { return _object_js__WEBPACK_IMPORTED_MODULE_11__["extractExceptionKeysForMessage"]; });

/* harmony reexport (safe) */ __webpack_require__.d(__webpack_exports__, "fill", function() { return _object_js__WEBPACK_IMPORTED_MODULE_11__["fill"]; });

/* harmony reexport (safe) */ __webpack_require__.d(__webpack_exports__, "getOriginalFunction", function() { return _object_js__WEBPACK_IMPORTED_MODULE_11__["getOriginalFunction"]; });

/* harmony reexport (safe) */ __webpack_require__.d(__webpack_exports__, "markFunctionWrapped", function() { return _object_js__WEBPACK_IMPORTED_MODULE_11__["markFunctionWrapped"]; });

/* harmony reexport (safe) */ __webpack_require__.d(__webpack_exports__, "objectify", function() { return _object_js__WEBPACK_IMPORTED_MODULE_11__["objectify"]; });

/* harmony reexport (safe) */ __webpack_require__.d(__webpack_exports__, "urlEncode", function() { return _object_js__WEBPACK_IMPORTED_MODULE_11__["urlEncode"]; });

/* harmony import */ var _path_js__WEBPACK_IMPORTED_MODULE_12__ = __webpack_require__(115);
/* harmony reexport (safe) */ __webpack_require__.d(__webpack_exports__, "basename", function() { return _path_js__WEBPACK_IMPORTED_MODULE_12__["basename"]; });

/* harmony reexport (safe) */ __webpack_require__.d(__webpack_exports__, "dirname", function() { return _path_js__WEBPACK_IMPORTED_MODULE_12__["dirname"]; });

/* harmony reexport (safe) */ __webpack_require__.d(__webpack_exports__, "isAbsolute", function() { return _path_js__WEBPACK_IMPORTED_MODULE_12__["isAbsolute"]; });

/* harmony reexport (safe) */ __webpack_require__.d(__webpack_exports__, "join", function() { return _path_js__WEBPACK_IMPORTED_MODULE_12__["join"]; });

/* harmony reexport (safe) */ __webpack_require__.d(__webpack_exports__, "normalizePath", function() { return _path_js__WEBPACK_IMPORTED_MODULE_12__["normalizePath"]; });

/* harmony reexport (safe) */ __webpack_require__.d(__webpack_exports__, "relative", function() { return _path_js__WEBPACK_IMPORTED_MODULE_12__["relative"]; });

/* harmony reexport (safe) */ __webpack_require__.d(__webpack_exports__, "resolve", function() { return _path_js__WEBPACK_IMPORTED_MODULE_12__["resolve"]; });

/* harmony import */ var _promisebuffer_js__WEBPACK_IMPORTED_MODULE_13__ = __webpack_require__(116);
/* harmony reexport (safe) */ __webpack_require__.d(__webpack_exports__, "makePromiseBuffer", function() { return _promisebuffer_js__WEBPACK_IMPORTED_MODULE_13__["makePromiseBuffer"]; });

/* harmony import */ var _requestdata_js__WEBPACK_IMPORTED_MODULE_14__ = __webpack_require__(118);
/* harmony reexport (safe) */ __webpack_require__.d(__webpack_exports__, "addRequestDataToEvent", function() { return _requestdata_js__WEBPACK_IMPORTED_MODULE_14__["addRequestDataToEvent"]; });

/* harmony reexport (safe) */ __webpack_require__.d(__webpack_exports__, "addRequestDataToTransaction", function() { return _requestdata_js__WEBPACK_IMPORTED_MODULE_14__["addRequestDataToTransaction"]; });

/* harmony reexport (safe) */ __webpack_require__.d(__webpack_exports__, "extractPathForTransaction", function() { return _requestdata_js__WEBPACK_IMPORTED_MODULE_14__["extractPathForTransaction"]; });

/* harmony reexport (safe) */ __webpack_require__.d(__webpack_exports__, "extractRequestData", function() { return _requestdata_js__WEBPACK_IMPORTED_MODULE_14__["extractRequestData"]; });

/* harmony import */ var _severity_js__WEBPACK_IMPORTED_MODULE_15__ = __webpack_require__(119);
/* harmony reexport (safe) */ __webpack_require__.d(__webpack_exports__, "severityFromString", function() { return _severity_js__WEBPACK_IMPORTED_MODULE_15__["severityFromString"]; });

/* harmony reexport (safe) */ __webpack_require__.d(__webpack_exports__, "severityLevelFromString", function() { return _severity_js__WEBPACK_IMPORTED_MODULE_15__["severityLevelFromString"]; });

/* harmony reexport (safe) */ __webpack_require__.d(__webpack_exports__, "validSeverityLevels", function() { return _severity_js__WEBPACK_IMPORTED_MODULE_15__["validSeverityLevels"]; });

/* harmony import */ var _stacktrace_js__WEBPACK_IMPORTED_MODULE_16__ = __webpack_require__(96);
/* harmony reexport (safe) */ __webpack_require__.d(__webpack_exports__, "createStackParser", function() { return _stacktrace_js__WEBPACK_IMPORTED_MODULE_16__["createStackParser"]; });

/* harmony reexport (safe) */ __webpack_require__.d(__webpack_exports__, "getFunctionName", function() { return _stacktrace_js__WEBPACK_IMPORTED_MODULE_16__["getFunctionName"]; });

/* harmony reexport (safe) */ __webpack_require__.d(__webpack_exports__, "nodeStackLineParser", function() { return _stacktrace_js__WEBPACK_IMPORTED_MODULE_16__["nodeStackLineParser"]; });

/* harmony reexport (safe) */ __webpack_require__.d(__webpack_exports__, "stackParserFromStackParserOptions", function() { return _stacktrace_js__WEBPACK_IMPORTED_MODULE_16__["stackParserFromStackParserOptions"]; });

/* harmony reexport (safe) */ __webpack_require__.d(__webpack_exports__, "stripSentryFramesAndReverse", function() { return _stacktrace_js__WEBPACK_IMPORTED_MODULE_16__["stripSentryFramesAndReverse"]; });

/* harmony import */ var _string_js__WEBPACK_IMPORTED_MODULE_17__ = __webpack_require__(95);
/* harmony reexport (safe) */ __webpack_require__.d(__webpack_exports__, "escapeStringForRegex", function() { return _string_js__WEBPACK_IMPORTED_MODULE_17__["escapeStringForRegex"]; });

/* harmony reexport (safe) */ __webpack_require__.d(__webpack_exports__, "isMatchingPattern", function() { return _string_js__WEBPACK_IMPORTED_MODULE_17__["isMatchingPattern"]; });

/* harmony reexport (safe) */ __webpack_require__.d(__webpack_exports__, "safeJoin", function() { return _string_js__WEBPACK_IMPORTED_MODULE_17__["safeJoin"]; });

/* harmony reexport (safe) */ __webpack_require__.d(__webpack_exports__, "snipLine", function() { return _string_js__WEBPACK_IMPORTED_MODULE_17__["snipLine"]; });

/* harmony reexport (safe) */ __webpack_require__.d(__webpack_exports__, "truncate", function() { return _string_js__WEBPACK_IMPORTED_MODULE_17__["truncate"]; });

/* harmony import */ var _supports_js__WEBPACK_IMPORTED_MODULE_18__ = __webpack_require__(111);
/* harmony reexport (safe) */ __webpack_require__.d(__webpack_exports__, "isNativeFetch", function() { return _supports_js__WEBPACK_IMPORTED_MODULE_18__["isNativeFetch"]; });

/* harmony reexport (safe) */ __webpack_require__.d(__webpack_exports__, "supportsDOMError", function() { return _supports_js__WEBPACK_IMPORTED_MODULE_18__["supportsDOMError"]; });

/* harmony reexport (safe) */ __webpack_require__.d(__webpack_exports__, "supportsDOMException", function() { return _supports_js__WEBPACK_IMPORTED_MODULE_18__["supportsDOMException"]; });

/* harmony reexport (safe) */ __webpack_require__.d(__webpack_exports__, "supportsErrorEvent", function() { return _supports_js__WEBPACK_IMPORTED_MODULE_18__["supportsErrorEvent"]; });

/* harmony reexport (safe) */ __webpack_require__.d(__webpack_exports__, "supportsFetch", function() { return _supports_js__WEBPACK_IMPORTED_MODULE_18__["supportsFetch"]; });

/* harmony reexport (safe) */ __webpack_require__.d(__webpack_exports__, "supportsHistory", function() { return _supports_js__WEBPACK_IMPORTED_MODULE_18__["supportsHistory"]; });

/* harmony reexport (safe) */ __webpack_require__.d(__webpack_exports__, "supportsNativeFetch", function() { return _supports_js__WEBPACK_IMPORTED_MODULE_18__["supportsNativeFetch"]; });

/* harmony reexport (safe) */ __webpack_require__.d(__webpack_exports__, "supportsReferrerPolicy", function() { return _supports_js__WEBPACK_IMPORTED_MODULE_18__["supportsReferrerPolicy"]; });

/* harmony reexport (safe) */ __webpack_require__.d(__webpack_exports__, "supportsReportingObserver", function() { return _supports_js__WEBPACK_IMPORTED_MODULE_18__["supportsReportingObserver"]; });

/* harmony import */ var _syncpromise_js__WEBPACK_IMPORTED_MODULE_19__ = __webpack_require__(117);
/* harmony reexport (safe) */ __webpack_require__.d(__webpack_exports__, "SyncPromise", function() { return _syncpromise_js__WEBPACK_IMPORTED_MODULE_19__["SyncPromise"]; });

/* harmony reexport (safe) */ __webpack_require__.d(__webpack_exports__, "rejectedSyncPromise", function() { return _syncpromise_js__WEBPACK_IMPORTED_MODULE_19__["rejectedSyncPromise"]; });

/* harmony reexport (safe) */ __webpack_require__.d(__webpack_exports__, "resolvedSyncPromise", function() { return _syncpromise_js__WEBPACK_IMPORTED_MODULE_19__["resolvedSyncPromise"]; });

/* harmony import */ var _time_js__WEBPACK_IMPORTED_MODULE_20__ = __webpack_require__(120);
/* harmony reexport (safe) */ __webpack_require__.d(__webpack_exports__, "_browserPerformanceTimeOriginMode", function() { return _time_js__WEBPACK_IMPORTED_MODULE_20__["_browserPerformanceTimeOriginMode"]; });

/* harmony reexport (safe) */ __webpack_require__.d(__webpack_exports__, "browserPerformanceTimeOrigin", function() { return _time_js__WEBPACK_IMPORTED_MODULE_20__["browserPerformanceTimeOrigin"]; });

/* harmony reexport (safe) */ __webpack_require__.d(__webpack_exports__, "dateTimestampInSeconds", function() { return _time_js__WEBPACK_IMPORTED_MODULE_20__["dateTimestampInSeconds"]; });

/* harmony reexport (safe) */ __webpack_require__.d(__webpack_exports__, "timestampInSeconds", function() { return _time_js__WEBPACK_IMPORTED_MODULE_20__["timestampInSeconds"]; });

/* harmony reexport (safe) */ __webpack_require__.d(__webpack_exports__, "timestampWithMs", function() { return _time_js__WEBPACK_IMPORTED_MODULE_20__["timestampWithMs"]; });

/* harmony reexport (safe) */ __webpack_require__.d(__webpack_exports__, "usingPerformanceAPI", function() { return _time_js__WEBPACK_IMPORTED_MODULE_20__["usingPerformanceAPI"]; });

/* harmony import */ var _tracing_js__WEBPACK_IMPORTED_MODULE_21__ = __webpack_require__(121);
/* harmony reexport (safe) */ __webpack_require__.d(__webpack_exports__, "TRACEPARENT_REGEXP", function() { return _tracing_js__WEBPACK_IMPORTED_MODULE_21__["TRACEPARENT_REGEXP"]; });

/* harmony reexport (safe) */ __webpack_require__.d(__webpack_exports__, "extractTraceparentData", function() { return _tracing_js__WEBPACK_IMPORTED_MODULE_21__["extractTraceparentData"]; });

/* harmony import */ var _env_js__WEBPACK_IMPORTED_MODULE_22__ = __webpack_require__(88);
/* harmony reexport (safe) */ __webpack_require__.d(__webpack_exports__, "isBrowserBundle", function() { return _env_js__WEBPACK_IMPORTED_MODULE_22__["isBrowserBundle"]; });

/* harmony import */ var _envelope_js__WEBPACK_IMPORTED_MODULE_23__ = __webpack_require__(122);
/* harmony reexport (safe) */ __webpack_require__.d(__webpack_exports__, "addItemToEnvelope", function() { return _envelope_js__WEBPACK_IMPORTED_MODULE_23__["addItemToEnvelope"]; });

/* harmony reexport (safe) */ __webpack_require__.d(__webpack_exports__, "createAttachmentEnvelopeItem", function() { return _envelope_js__WEBPACK_IMPORTED_MODULE_23__["createAttachmentEnvelopeItem"]; });

/* harmony reexport (safe) */ __webpack_require__.d(__webpack_exports__, "createEnvelope", function() { return _envelope_js__WEBPACK_IMPORTED_MODULE_23__["createEnvelope"]; });

/* harmony reexport (safe) */ __webpack_require__.d(__webpack_exports__, "envelopeItemTypeToDataCategory", function() { return _envelope_js__WEBPACK_IMPORTED_MODULE_23__["envelopeItemTypeToDataCategory"]; });

/* harmony reexport (safe) */ __webpack_require__.d(__webpack_exports__, "forEachEnvelopeItem", function() { return _envelope_js__WEBPACK_IMPORTED_MODULE_23__["forEachEnvelopeItem"]; });

/* harmony reexport (safe) */ __webpack_require__.d(__webpack_exports__, "serializeEnvelope", function() { return _envelope_js__WEBPACK_IMPORTED_MODULE_23__["serializeEnvelope"]; });

/* harmony import */ var _clientreport_js__WEBPACK_IMPORTED_MODULE_24__ = __webpack_require__(123);
/* harmony reexport (safe) */ __webpack_require__.d(__webpack_exports__, "createClientReportEnvelope", function() { return _clientreport_js__WEBPACK_IMPORTED_MODULE_24__["createClientReportEnvelope"]; });

/* harmony import */ var _ratelimit_js__WEBPACK_IMPORTED_MODULE_25__ = __webpack_require__(124);
/* harmony reexport (safe) */ __webpack_require__.d(__webpack_exports__, "DEFAULT_RETRY_AFTER", function() { return _ratelimit_js__WEBPACK_IMPORTED_MODULE_25__["DEFAULT_RETRY_AFTER"]; });

/* harmony reexport (safe) */ __webpack_require__.d(__webpack_exports__, "disabledUntil", function() { return _ratelimit_js__WEBPACK_IMPORTED_MODULE_25__["disabledUntil"]; });

/* harmony reexport (safe) */ __webpack_require__.d(__webpack_exports__, "isRateLimited", function() { return _ratelimit_js__WEBPACK_IMPORTED_MODULE_25__["isRateLimited"]; });

/* harmony reexport (safe) */ __webpack_require__.d(__webpack_exports__, "parseRetryAfterHeader", function() { return _ratelimit_js__WEBPACK_IMPORTED_MODULE_25__["parseRetryAfterHeader"]; });

/* harmony reexport (safe) */ __webpack_require__.d(__webpack_exports__, "updateRateLimits", function() { return _ratelimit_js__WEBPACK_IMPORTED_MODULE_25__["updateRateLimits"]; });

/* harmony import */ var _baggage_js__WEBPACK_IMPORTED_MODULE_26__ = __webpack_require__(125);
/* harmony reexport (safe) */ __webpack_require__.d(__webpack_exports__, "BAGGAGE_HEADER_NAME", function() { return _baggage_js__WEBPACK_IMPORTED_MODULE_26__["BAGGAGE_HEADER_NAME"]; });

/* harmony reexport (safe) */ __webpack_require__.d(__webpack_exports__, "MAX_BAGGAGE_STRING_LENGTH", function() { return _baggage_js__WEBPACK_IMPORTED_MODULE_26__["MAX_BAGGAGE_STRING_LENGTH"]; });

/* harmony reexport (safe) */ __webpack_require__.d(__webpack_exports__, "SENTRY_BAGGAGE_KEY_PREFIX", function() { return _baggage_js__WEBPACK_IMPORTED_MODULE_26__["SENTRY_BAGGAGE_KEY_PREFIX"]; });

/* harmony reexport (safe) */ __webpack_require__.d(__webpack_exports__, "SENTRY_BAGGAGE_KEY_PREFIX_REGEX", function() { return _baggage_js__WEBPACK_IMPORTED_MODULE_26__["SENTRY_BAGGAGE_KEY_PREFIX_REGEX"]; });

/* harmony reexport (safe) */ __webpack_require__.d(__webpack_exports__, "createBaggage", function() { return _baggage_js__WEBPACK_IMPORTED_MODULE_26__["createBaggage"]; });

/* harmony reexport (safe) */ __webpack_require__.d(__webpack_exports__, "getBaggageValue", function() { return _baggage_js__WEBPACK_IMPORTED_MODULE_26__["getBaggageValue"]; });

/* harmony reexport (safe) */ __webpack_require__.d(__webpack_exports__, "getSentryBaggageItems", function() { return _baggage_js__WEBPACK_IMPORTED_MODULE_26__["getSentryBaggageItems"]; });

/* harmony reexport (safe) */ __webpack_require__.d(__webpack_exports__, "getThirdPartyBaggage", function() { return _baggage_js__WEBPACK_IMPORTED_MODULE_26__["getThirdPartyBaggage"]; });

/* harmony reexport (safe) */ __webpack_require__.d(__webpack_exports__, "isBaggageMutable", function() { return _baggage_js__WEBPACK_IMPORTED_MODULE_26__["isBaggageMutable"]; });

/* harmony reexport (safe) */ __webpack_require__.d(__webpack_exports__, "isSentryBaggageEmpty", function() { return _baggage_js__WEBPACK_IMPORTED_MODULE_26__["isSentryBaggageEmpty"]; });

/* harmony reexport (safe) */ __webpack_require__.d(__webpack_exports__, "mergeAndSerializeBaggage", function() { return _baggage_js__WEBPACK_IMPORTED_MODULE_26__["mergeAndSerializeBaggage"]; });

/* harmony reexport (safe) */ __webpack_require__.d(__webpack_exports__, "parseBaggageHeader", function() { return _baggage_js__WEBPACK_IMPORTED_MODULE_26__["parseBaggageHeader"]; });

/* harmony reexport (safe) */ __webpack_require__.d(__webpack_exports__, "parseBaggageSetMutability", function() { return _baggage_js__WEBPACK_IMPORTED_MODULE_26__["parseBaggageSetMutability"]; });

/* harmony reexport (safe) */ __webpack_require__.d(__webpack_exports__, "serializeBaggage", function() { return _baggage_js__WEBPACK_IMPORTED_MODULE_26__["serializeBaggage"]; });

/* harmony reexport (safe) */ __webpack_require__.d(__webpack_exports__, "setBaggageImmutable", function() { return _baggage_js__WEBPACK_IMPORTED_MODULE_26__["setBaggageImmutable"]; });

/* harmony reexport (safe) */ __webpack_require__.d(__webpack_exports__, "setBaggageValue", function() { return _baggage_js__WEBPACK_IMPORTED_MODULE_26__["setBaggageValue"]; });




























//# sourceMappingURL=index.js.map


/***/ }),
/* 83 */
/***/ (function(module, __webpack_exports__, __webpack_require__) {

"use strict";
__webpack_require__.r(__webpack_exports__);
/* harmony export (binding) */ __webpack_require__.d(__webpack_exports__, "getLocationHref", function() { return getLocationHref; });
/* harmony export (binding) */ __webpack_require__.d(__webpack_exports__, "htmlTreeAsString", function() { return htmlTreeAsString; });
/* harmony import */ var _global_js__WEBPACK_IMPORTED_MODULE_0__ = __webpack_require__(84);
/* harmony import */ var _is_js__WEBPACK_IMPORTED_MODULE_1__ = __webpack_require__(89);



/**
 * Given a child DOM element, returns a query-selector statement describing that
 * and its ancestors
 * e.g. [HTMLElement] => body > div > input#foo.btn[name=baz]
 * @returns generated DOM path
 */
function htmlTreeAsString(elem, keyAttrs) {
  

  // try/catch both:
  // - accessing event.target (see getsentry/raven-js#838, #768)
  // - `htmlTreeAsString` because it's complex, and just accessing the DOM incorrectly
  // - can throw an exception in some circumstances.
  try {
    let currentElem = elem ;
    var MAX_TRAVERSE_HEIGHT = 5;
    var MAX_OUTPUT_LEN = 80;
    var out = [];
    let height = 0;
    let len = 0;
    var separator = ' > ';
    var sepLength = separator.length;
    let nextStr;

        while (currentElem && height++ < MAX_TRAVERSE_HEIGHT) {
      nextStr = _htmlElementAsString(currentElem, keyAttrs);
      // bail out if
      // - nextStr is the 'html' element
      // - the length of the string that would be created exceeds MAX_OUTPUT_LEN
      //   (ignore this limit if we are on the first iteration)
      if (nextStr === 'html' || (height > 1 && len + out.length * sepLength + nextStr.length >= MAX_OUTPUT_LEN)) {
        break;
      }

      out.push(nextStr);

      len += nextStr.length;
      currentElem = currentElem.parentNode;
    }

    return out.reverse().join(separator);
  } catch (_oO) {
    return '<unknown>';
  }
}

/**
 * Returns a simple, query-selector representation of a DOM element
 * e.g. [HTMLElement] => input#foo.btn[name=baz]
 * @returns generated DOM path
 */
function _htmlElementAsString(el, keyAttrs) {
  var elem = el 

;

  var out = [];
  let className;
  let classes;
  let key;
  let attr;
  let i;

  if (!elem || !elem.tagName) {
    return '';
  }

  out.push(elem.tagName.toLowerCase());

  // Pairs of attribute keys defined in `serializeAttribute` and their values on element.
  var keyAttrPairs =
    keyAttrs && keyAttrs.length
      ? keyAttrs.filter(keyAttr => elem.getAttribute(keyAttr)).map(keyAttr => [keyAttr, elem.getAttribute(keyAttr)])
      : null;

  if (keyAttrPairs && keyAttrPairs.length) {
    keyAttrPairs.forEach(keyAttrPair => {
      out.push(`[${keyAttrPair[0]}="${keyAttrPair[1]}"]`);
    });
  } else {
    if (elem.id) {
      out.push(`#${elem.id}`);
    }

        className = elem.className;
    if (className && Object(_is_js__WEBPACK_IMPORTED_MODULE_1__["isString"])(className)) {
      classes = className.split(/\s+/);
      for (i = 0; i < classes.length; i++) {
        out.push(`.${classes[i]}`);
      }
    }
  }
  var allowedAttrs = ['type', 'name', 'title', 'alt'];
  for (i = 0; i < allowedAttrs.length; i++) {
    key = allowedAttrs[i];
    attr = elem.getAttribute(key);
    if (attr) {
      out.push(`[${key}="${attr}"]`);
    }
  }
  return out.join('');
}

/**
 * A safe form of location.href
 */
function getLocationHref() {
  var global = Object(_global_js__WEBPACK_IMPORTED_MODULE_0__["getGlobalObject"])();
  try {
    return global.document.location.href;
  } catch (oO) {
    return '';
  }
}


//# sourceMappingURL=browser.js.map


/***/ }),
/* 84 */
/***/ (function(module, __webpack_exports__, __webpack_require__) {

"use strict";
__webpack_require__.r(__webpack_exports__);
/* WEBPACK VAR INJECTION */(function(global) {/* harmony export (binding) */ __webpack_require__.d(__webpack_exports__, "getGlobalObject", function() { return getGlobalObject; });
/* harmony export (binding) */ __webpack_require__.d(__webpack_exports__, "getGlobalSingleton", function() { return getGlobalSingleton; });
/* harmony import */ var _node_js__WEBPACK_IMPORTED_MODULE_0__ = __webpack_require__(85);


/** Internal */

var fallbackGlobalObject = {};

/**
 * Safely get global scope object
 *
 * @returns Global scope object
 */
function getGlobalObject() {
  return (
    Object(_node_js__WEBPACK_IMPORTED_MODULE_0__["isNodeEnv"])()
      ? global
      : typeof window !== 'undefined'       ? window       : typeof self !== 'undefined'
      ? self
      : fallbackGlobalObject
  ) ;
}

/**
 * Returns a global singleton contained in the global `__SENTRY__` object.
 *
 * If the singleton doesn't already exist in `__SENTRY__`, it will be created using the given factory
 * function and added to the `__SENTRY__` object.
 *
 * @param name name of the global singleton on __SENTRY__
 * @param creator creator Factory function to create the singleton if it doesn't already exist on `__SENTRY__`
 * @param obj (Optional) The global object on which to look for `__SENTRY__`, if not `getGlobalObject`'s return value
 * @returns the singleton
 */
function getGlobalSingleton(name, creator, obj) {
  var global = (obj || getGlobalObject()) ;
  var __SENTRY__ = (global.__SENTRY__ = global.__SENTRY__ || {});
  var singleton = __SENTRY__[name] || (__SENTRY__[name] = creator());
  return singleton;
}


//# sourceMappingURL=global.js.map

/* WEBPACK VAR INJECTION */}.call(this, __webpack_require__(7)))

/***/ }),
/* 85 */
/***/ (function(module, __webpack_exports__, __webpack_require__) {

"use strict";
__webpack_require__.r(__webpack_exports__);
/* WEBPACK VAR INJECTION */(function(process, module) {/* harmony export (binding) */ __webpack_require__.d(__webpack_exports__, "dynamicRequire", function() { return dynamicRequire; });
/* harmony export (binding) */ __webpack_require__.d(__webpack_exports__, "isNodeEnv", function() { return isNodeEnv; });
/* harmony export (binding) */ __webpack_require__.d(__webpack_exports__, "loadModule", function() { return loadModule; });
/* harmony import */ var _env_js__WEBPACK_IMPORTED_MODULE_0__ = __webpack_require__(88);


/**
 * NOTE: In order to avoid circular dependencies, if you add a function to this module and it needs to print something,
 * you must either a) use `console.log` rather than the logger, or b) put your function elsewhere.
 */

/**
 * Checks whether we're in the Node.js or Browser environment
 *
 * @returns Answer to given question
 */
function isNodeEnv() {
  // explicitly check for browser bundles as those can be optimized statically
  // by terser/rollup.
  return (
    !Object(_env_js__WEBPACK_IMPORTED_MODULE_0__["isBrowserBundle"])() &&
    Object.prototype.toString.call(typeof process !== 'undefined' ? process : 0) === '[object process]'
  );
}

/**
 * Requires a module which is protected against bundler minification.
 *
 * @param request The module path to resolve
 */
function dynamicRequire(mod, request) {
    return mod.require(request);
}

/**
 * Helper for dynamically loading module that should work with linked dependencies.
 * The problem is that we _should_ be using `require(require.resolve(moduleName, { paths: [cwd()] }))`
 * However it's _not possible_ to do that with Webpack, as it has to know all the dependencies during
 * build time. `require.resolve` is also not available in any other way, so we cannot create,
 * a fake helper like we do with `dynamicRequire`.
 *
 * We always prefer to use local package, thus the value is not returned early from each `try/catch` block.
 * That is to mimic the behavior of `require.resolve` exactly.
 *
 * @param moduleName module name to require
 * @returns possibly required module
 */
function loadModule(moduleName) {
  let mod;

  try {
    mod = dynamicRequire(module, moduleName);
  } catch (e) {
    // no-empty
  }

  try {
    const { cwd } = dynamicRequire(module, 'process');
    mod = dynamicRequire(module, `${cwd()}/node_modules/${moduleName}`) ;
  } catch (e) {
    // no-empty
  }

  return mod;
}


//# sourceMappingURL=node.js.map

/* WEBPACK VAR INJECTION */}.call(this, __webpack_require__(86), __webpack_require__(87)(module)))

/***/ }),
/* 86 */
/***/ (function(module, exports) {

// shim for using process in browser
var process = module.exports = {};

// cached from whatever global is present so that test runners that stub it
// don't break things.  But we need to wrap it in a try catch in case it is
// wrapped in strict mode code which doesn't define any globals.  It's inside a
// function because try/catches deoptimize in certain engines.

var cachedSetTimeout;
var cachedClearTimeout;

function defaultSetTimout() {
    throw new Error('setTimeout has not been defined');
}
function defaultClearTimeout () {
    throw new Error('clearTimeout has not been defined');
}
(function () {
    try {
        if (typeof setTimeout === 'function') {
            cachedSetTimeout = setTimeout;
        } else {
            cachedSetTimeout = defaultSetTimout;
        }
    } catch (e) {
        cachedSetTimeout = defaultSetTimout;
    }
    try {
        if (typeof clearTimeout === 'function') {
            cachedClearTimeout = clearTimeout;
        } else {
            cachedClearTimeout = defaultClearTimeout;
        }
    } catch (e) {
        cachedClearTimeout = defaultClearTimeout;
    }
} ())
function runTimeout(fun) {
    if (cachedSetTimeout === setTimeout) {
        //normal enviroments in sane situations
        return setTimeout(fun, 0);
    }
    // if setTimeout wasn't available but was latter defined
    if ((cachedSetTimeout === defaultSetTimout || !cachedSetTimeout) && setTimeout) {
        cachedSetTimeout = setTimeout;
        return setTimeout(fun, 0);
    }
    try {
        // when when somebody has screwed with setTimeout but no I.E. maddness
        return cachedSetTimeout(fun, 0);
    } catch(e){
        try {
            // When we are in I.E. but the script has been evaled so I.E. doesn't trust the global object when called normally
            return cachedSetTimeout.call(null, fun, 0);
        } catch(e){
            // same as above but when it's a version of I.E. that must have the global object for 'this', hopfully our context correct otherwise it will throw a global error
            return cachedSetTimeout.call(this, fun, 0);
        }
    }


}
function runClearTimeout(marker) {
    if (cachedClearTimeout === clearTimeout) {
        //normal enviroments in sane situations
        return clearTimeout(marker);
    }
    // if clearTimeout wasn't available but was latter defined
    if ((cachedClearTimeout === defaultClearTimeout || !cachedClearTimeout) && clearTimeout) {
        cachedClearTimeout = clearTimeout;
        return clearTimeout(marker);
    }
    try {
        // when when somebody has screwed with setTimeout but no I.E. maddness
        return cachedClearTimeout(marker);
    } catch (e){
        try {
            // When we are in I.E. but the script has been evaled so I.E. doesn't  trust the global object when called normally
            return cachedClearTimeout.call(null, marker);
        } catch (e){
            // same as above but when it's a version of I.E. that must have the global object for 'this', hopfully our context correct otherwise it will throw a global error.
            // Some versions of I.E. have different rules for clearTimeout vs setTimeout
            return cachedClearTimeout.call(this, marker);
        }
    }



}
var queue = [];
var draining = false;
var currentQueue;
var queueIndex = -1;

function cleanUpNextTick() {
    if (!draining || !currentQueue) {
        return;
    }
    draining = false;
    if (currentQueue.length) {
        queue = currentQueue.concat(queue);
    } else {
        queueIndex = -1;
    }
    if (queue.length) {
        drainQueue();
    }
}

function drainQueue() {
    if (draining) {
        return;
    }
    var timeout = runTimeout(cleanUpNextTick);
    draining = true;

    var len = queue.length;
    while(len) {
        currentQueue = queue;
        queue = [];
        while (++queueIndex < len) {
            if (currentQueue) {
                currentQueue[queueIndex].run();
            }
        }
        queueIndex = -1;
        len = queue.length;
    }
    currentQueue = null;
    draining = false;
    runClearTimeout(timeout);
}

process.nextTick = function (fun) {
    var args = new Array(arguments.length - 1);
    if (arguments.length > 1) {
        for (var i = 1; i < arguments.length; i++) {
            args[i - 1] = arguments[i];
        }
    }
    queue.push(new Item(fun, args));
    if (queue.length === 1 && !draining) {
        runTimeout(drainQueue);
    }
};

// v8 likes predictible objects
function Item(fun, array) {
    this.fun = fun;
    this.array = array;
}
Item.prototype.run = function () {
    this.fun.apply(null, this.array);
};
process.title = 'browser';
process.browser = true;
process.env = {};
process.argv = [];
process.version = ''; // empty string to avoid regexp issues
process.versions = {};

function noop() {}

process.on = noop;
process.addListener = noop;
process.once = noop;
process.off = noop;
process.removeListener = noop;
process.removeAllListeners = noop;
process.emit = noop;
process.prependListener = noop;
process.prependOnceListener = noop;

process.listeners = function (name) { return [] }

process.binding = function (name) {
    throw new Error('process.binding is not supported');
};

process.cwd = function () { return '/' };
process.chdir = function (dir) {
    throw new Error('process.chdir is not supported');
};
process.umask = function() { return 0; };


/***/ }),
/* 87 */
/***/ (function(module, exports) {

module.exports = function(originalModule) {
	if (!originalModule.webpackPolyfill) {
		var module = Object.create(originalModule);
		// module.parent = undefined by default
		if (!module.children) module.children = [];
		Object.defineProperty(module, "loaded", {
			enumerable: true,
			get: function() {
				return module.l;
			}
		});
		Object.defineProperty(module, "id", {
			enumerable: true,
			get: function() {
				return module.i;
			}
		});
		Object.defineProperty(module, "exports", {
			enumerable: true
		});
		module.webpackPolyfill = 1;
	}
	return module;
};


/***/ }),
/* 88 */
/***/ (function(module, __webpack_exports__, __webpack_require__) {

"use strict";
__webpack_require__.r(__webpack_exports__);
/* harmony export (binding) */ __webpack_require__.d(__webpack_exports__, "isBrowserBundle", function() { return isBrowserBundle; });
/*
 * This module exists for optimizations in the build process through rollup and terser.  We define some global
 * constants, which can be overridden during build. By guarding certain pieces of code with functions that return these
 * constants, we can control whether or not they appear in the final bundle. (Any code guarded by a false condition will
 * never run, and will hence be dropped during treeshaking.) The two primary uses for this are stripping out calls to
 * `logger` and preventing node-related code from appearing in browser bundles.
 *
 * Attention:
 * This file should not be used to define constants/flags that are intended to be used for tree-shaking conducted by
 * users. These fags should live in their respective packages, as we identified user tooling (specifically webpack)
 * having issues tree-shaking these constants across package boundaries.
 * An example for this is the __SENTRY_DEBUG__ constant. It is declared in each package individually because we want
 * users to be able to shake away expressions that it guards.
 */

/**
 * Figures out if we're building a browser bundle.
 *
 * @returns true if this is a browser bundle build.
 */
function isBrowserBundle() {
  return typeof __SENTRY_BROWSER_BUNDLE__ !== 'undefined' && !!__SENTRY_BROWSER_BUNDLE__;
}


//# sourceMappingURL=env.js.map


/***/ }),
/* 89 */
/***/ (function(module, __webpack_exports__, __webpack_require__) {

"use strict";
__webpack_require__.r(__webpack_exports__);
/* harmony export (binding) */ __webpack_require__.d(__webpack_exports__, "isDOMError", function() { return isDOMError; });
/* harmony export (binding) */ __webpack_require__.d(__webpack_exports__, "isDOMException", function() { return isDOMException; });
/* harmony export (binding) */ __webpack_require__.d(__webpack_exports__, "isElement", function() { return isElement; });
/* harmony export (binding) */ __webpack_require__.d(__webpack_exports__, "isError", function() { return isError; });
/* harmony export (binding) */ __webpack_require__.d(__webpack_exports__, "isErrorEvent", function() { return isErrorEvent; });
/* harmony export (binding) */ __webpack_require__.d(__webpack_exports__, "isEvent", function() { return isEvent; });
/* harmony export (binding) */ __webpack_require__.d(__webpack_exports__, "isInstanceOf", function() { return isInstanceOf; });
/* harmony export (binding) */ __webpack_require__.d(__webpack_exports__, "isNaN", function() { return isNaN; });
/* harmony export (binding) */ __webpack_require__.d(__webpack_exports__, "isPlainObject", function() { return isPlainObject; });
/* harmony export (binding) */ __webpack_require__.d(__webpack_exports__, "isPrimitive", function() { return isPrimitive; });
/* harmony export (binding) */ __webpack_require__.d(__webpack_exports__, "isRegExp", function() { return isRegExp; });
/* harmony export (binding) */ __webpack_require__.d(__webpack_exports__, "isString", function() { return isString; });
/* harmony export (binding) */ __webpack_require__.d(__webpack_exports__, "isSyntheticEvent", function() { return isSyntheticEvent; });
/* harmony export (binding) */ __webpack_require__.d(__webpack_exports__, "isThenable", function() { return isThenable; });
var objectToString = Object.prototype.toString;

/**
 * Checks whether given value's type is one of a few Error or Error-like
 * {@link isError}.
 *
 * @param wat A value to be checked.
 * @returns A boolean representing the result.
 */
function isError(wat) {
  switch (objectToString.call(wat)) {
    case '[object Error]':
    case '[object Exception]':
    case '[object DOMException]':
      return true;
    default:
      return isInstanceOf(wat, Error);
  }
}

function isBuiltin(wat, ty) {
  return objectToString.call(wat) === `[object ${ty}]`;
}

/**
 * Checks whether given value's type is ErrorEvent
 * {@link isErrorEvent}.
 *
 * @param wat A value to be checked.
 * @returns A boolean representing the result.
 */
function isErrorEvent(wat) {
  return isBuiltin(wat, 'ErrorEvent');
}

/**
 * Checks whether given value's type is DOMError
 * {@link isDOMError}.
 *
 * @param wat A value to be checked.
 * @returns A boolean representing the result.
 */
function isDOMError(wat) {
  return isBuiltin(wat, 'DOMError');
}

/**
 * Checks whether given value's type is DOMException
 * {@link isDOMException}.
 *
 * @param wat A value to be checked.
 * @returns A boolean representing the result.
 */
function isDOMException(wat) {
  return isBuiltin(wat, 'DOMException');
}

/**
 * Checks whether given value's type is a string
 * {@link isString}.
 *
 * @param wat A value to be checked.
 * @returns A boolean representing the result.
 */
function isString(wat) {
  return isBuiltin(wat, 'String');
}

/**
 * Checks whether given value is a primitive (undefined, null, number, boolean, string, bigint, symbol)
 * {@link isPrimitive}.
 *
 * @param wat A value to be checked.
 * @returns A boolean representing the result.
 */
function isPrimitive(wat) {
  return wat === null || (typeof wat !== 'object' && typeof wat !== 'function');
}

/**
 * Checks whether given value's type is an object literal
 * {@link isPlainObject}.
 *
 * @param wat A value to be checked.
 * @returns A boolean representing the result.
 */
function isPlainObject(wat) {
  return isBuiltin(wat, 'Object');
}

/**
 * Checks whether given value's type is an Event instance
 * {@link isEvent}.
 *
 * @param wat A value to be checked.
 * @returns A boolean representing the result.
 */
function isEvent(wat) {
  return typeof Event !== 'undefined' && isInstanceOf(wat, Event);
}

/**
 * Checks whether given value's type is an Element instance
 * {@link isElement}.
 *
 * @param wat A value to be checked.
 * @returns A boolean representing the result.
 */
function isElement(wat) {
  return typeof Element !== 'undefined' && isInstanceOf(wat, Element);
}

/**
 * Checks whether given value's type is an regexp
 * {@link isRegExp}.
 *
 * @param wat A value to be checked.
 * @returns A boolean representing the result.
 */
function isRegExp(wat) {
  return isBuiltin(wat, 'RegExp');
}

/**
 * Checks whether given value has a then function.
 * @param wat A value to be checked.
 */
function isThenable(wat) {
    return Boolean(wat && wat.then && typeof wat.then === 'function');
}

/**
 * Checks whether given value's type is a SyntheticEvent
 * {@link isSyntheticEvent}.
 *
 * @param wat A value to be checked.
 * @returns A boolean representing the result.
 */
function isSyntheticEvent(wat) {
  return isPlainObject(wat) && 'nativeEvent' in wat && 'preventDefault' in wat && 'stopPropagation' in wat;
}

/**
 * Checks whether given value is NaN
 * {@link isNaN}.
 *
 * @param wat A value to be checked.
 * @returns A boolean representing the result.
 */
function isNaN(wat) {
  return typeof wat === 'number' && wat !== wat;
}

/**
 * Checks whether given value's type is an instance of provided constructor.
 * {@link isInstanceOf}.
 *
 * @param wat A value to be checked.
 * @param base A constructor to be used in a check.
 * @returns A boolean representing the result.
 */
function isInstanceOf(wat, base) {
  try {
    return wat instanceof base;
  } catch (_e) {
    return false;
  }
}


//# sourceMappingURL=is.js.map


/***/ }),
/* 90 */
/***/ (function(module, __webpack_exports__, __webpack_require__) {

"use strict";
__webpack_require__.r(__webpack_exports__);
/* harmony export (binding) */ __webpack_require__.d(__webpack_exports__, "dsnToString", function() { return dsnToString; });
/* harmony export (binding) */ __webpack_require__.d(__webpack_exports__, "extensionRelayDSN", function() { return extensionRelayDSN; });
/* harmony export (binding) */ __webpack_require__.d(__webpack_exports__, "makeDsn", function() { return makeDsn; });
/* harmony import */ var _error_js__WEBPACK_IMPORTED_MODULE_0__ = __webpack_require__(91);


/** Regular expression used to parse a Dsn. */
var DSN_REGEX = /^(?:(\w+):)\/\/(?:(\w+)(?::(\w+))?@)([\w.-]+)(?::(\d+))?\/(.+)/;

function isValidProtocol(protocol) {
  return protocol === 'http' || protocol === 'https';
}

/**
 * Renders the string representation of this Dsn.
 *
 * By default, this will render the public representation without the password
 * component. To get the deprecated private representation, set `withPassword`
 * to true.
 *
 * @param withPassword When set to true, the password will be included.
 */
function dsnToString(dsn, withPassword = false) {
  const { host, path, pass, port, projectId, protocol, publicKey } = dsn;
  return (
    `${protocol}://${publicKey}${withPassword && pass ? `:${pass}` : ''}` +
    `@${host}${port ? `:${port}` : ''}/${path ? `${path}/` : path}${projectId}`
  );
}

/**
 * Parses a Dsn from a given string.
 *
 * @param str A Dsn as string
 * @returns Dsn as DsnComponents
 */
function dsnFromString(str) {
  var match = DSN_REGEX.exec(str);

  if (!match) {
    throw new _error_js__WEBPACK_IMPORTED_MODULE_0__["SentryError"](`Invalid Sentry Dsn: ${str}`);
  }

  const [protocol, publicKey, pass = '', host, port = '', lastPath] = match.slice(1);
  let path = '';
  let projectId = lastPath;

  var split = projectId.split('/');
  if (split.length > 1) {
    path = split.slice(0, -1).join('/');
    projectId = split.pop() ;
  }

  if (projectId) {
    var projectMatch = projectId.match(/^\d+/);
    if (projectMatch) {
      projectId = projectMatch[0];
    }
  }

  return dsnFromComponents({ host, pass, path, projectId, port, protocol: protocol , publicKey });
}

function dsnFromComponents(components) {
  return {
    protocol: components.protocol,
    publicKey: components.publicKey || '',
    pass: components.pass || '',
    host: components.host,
    port: components.port || '',
    path: components.path || '',
    projectId: components.projectId,
  };
}

function validateDsn(dsn) {
  if (!(typeof __SENTRY_DEBUG__ === 'undefined' || __SENTRY_DEBUG__)) {
    return;
  }

  const { port, projectId, protocol } = dsn;

  var requiredComponents = ['protocol', 'publicKey', 'host', 'projectId'];
  requiredComponents.forEach(component => {
    if (!dsn[component]) {
      throw new _error_js__WEBPACK_IMPORTED_MODULE_0__["SentryError"](`Invalid Sentry Dsn: ${component} missing`);
    }
  });

  if (!projectId.match(/^\d+$/)) {
    throw new _error_js__WEBPACK_IMPORTED_MODULE_0__["SentryError"](`Invalid Sentry Dsn: Invalid projectId ${projectId}`);
  }

  if (!isValidProtocol(protocol)) {
    throw new _error_js__WEBPACK_IMPORTED_MODULE_0__["SentryError"](`Invalid Sentry Dsn: Invalid protocol ${protocol}`);
  }

  if (port && isNaN(parseInt(port, 10))) {
    throw new _error_js__WEBPACK_IMPORTED_MODULE_0__["SentryError"](`Invalid Sentry Dsn: Invalid port ${port}`);
  }

  return true;
}

/** The Sentry Dsn, identifying a Sentry instance and project. */
function makeDsn(from) {
  var components = typeof from === 'string' ? dsnFromString(from) : dsnFromComponents(from);
  validateDsn(components);
  return components;
}

/**
 * Changes a Dsn to point to the `relay` server running in the Lambda Extension.
 *
 * This is only used by the serverless integration for AWS Lambda.
 *
 * @param originalDsn The original Dsn of the customer.
 * @returns Dsn pointing to Lambda extension.
 */
function extensionRelayDSN(originalDsn) {
  if (originalDsn === undefined) {
    return undefined;
  }

  var dsn = dsnFromString(originalDsn);
  dsn.host = 'localhost';
  dsn.port = '3000';
  dsn.protocol = 'http';

  return dsnToString(dsn);
}


//# sourceMappingURL=dsn.js.map


/***/ }),
/* 91 */
/***/ (function(module, __webpack_exports__, __webpack_require__) {

"use strict";
__webpack_require__.r(__webpack_exports__);
/* harmony export (binding) */ __webpack_require__.d(__webpack_exports__, "SentryError", function() { return SentryError; });
/** An error emitted by Sentry SDKs and related utilities. */
class SentryError extends Error {
  /** Display name of this error instance. */
  

   constructor( message) {
    super(message);this.message = message;;

    this.name = new.target.prototype.constructor.name;
    Object.setPrototypeOf(this, new.target.prototype);
  }
}


//# sourceMappingURL=error.js.map


/***/ }),
/* 92 */
/***/ (function(module, __webpack_exports__, __webpack_require__) {

"use strict";
__webpack_require__.r(__webpack_exports__);
/* harmony export (binding) */ __webpack_require__.d(__webpack_exports__, "addInstrumentationHandler", function() { return addInstrumentationHandler; });
/* harmony import */ var _global_js__WEBPACK_IMPORTED_MODULE_0__ = __webpack_require__(84);
/* harmony import */ var _is_js__WEBPACK_IMPORTED_MODULE_1__ = __webpack_require__(89);
/* harmony import */ var _logger_js__WEBPACK_IMPORTED_MODULE_2__ = __webpack_require__(93);
/* harmony import */ var _object_js__WEBPACK_IMPORTED_MODULE_3__ = __webpack_require__(94);
/* harmony import */ var _stacktrace_js__WEBPACK_IMPORTED_MODULE_4__ = __webpack_require__(96);
/* harmony import */ var _supports_js__WEBPACK_IMPORTED_MODULE_5__ = __webpack_require__(111);







var global = Object(_global_js__WEBPACK_IMPORTED_MODULE_0__["getGlobalObject"])();

/**
 * Instrument native APIs to call handlers that can be used to create breadcrumbs, APM spans etc.
 *  - Console API
 *  - Fetch API
 *  - XHR API
 *  - History API
 *  - DOM API (click/typing)
 *  - Error API
 *  - UnhandledRejection API
 */

var handlers = {};
var instrumented = {};

/** Instruments given API */
function instrument(type) {
  if (instrumented[type]) {
    return;
  }

  instrumented[type] = true;

  switch (type) {
    case 'console':
      instrumentConsole();
      break;
    case 'dom':
      instrumentDOM();
      break;
    case 'xhr':
      instrumentXHR();
      break;
    case 'fetch':
      instrumentFetch();
      break;
    case 'history':
      instrumentHistory();
      break;
    case 'error':
      instrumentError();
      break;
    case 'unhandledrejection':
      instrumentUnhandledRejection();
      break;
    default:
      (typeof __SENTRY_DEBUG__ === 'undefined' || __SENTRY_DEBUG__) && _logger_js__WEBPACK_IMPORTED_MODULE_2__["logger"].warn('unknown instrumentation type:', type);
      return;
  }
}

/**
 * Add handler that will be called when given type of instrumentation triggers.
 * Use at your own risk, this might break without changelog notice, only used internally.
 * @hidden
 */
function addInstrumentationHandler(type, callback) {
  handlers[type] = handlers[type] || [];
  (handlers[type] ).push(callback);
  instrument(type);
}

/** JSDoc */
function triggerHandlers(type, data) {
  if (!type || !handlers[type]) {
    return;
  }

  for (var handler of handlers[type] || []) {
    try {
      handler(data);
    } catch (e) {
      (typeof __SENTRY_DEBUG__ === 'undefined' || __SENTRY_DEBUG__) &&
        _logger_js__WEBPACK_IMPORTED_MODULE_2__["logger"].error(
          `Error while triggering instrumentation handler.\nType: ${type}\nName: ${Object(_stacktrace_js__WEBPACK_IMPORTED_MODULE_4__["getFunctionName"])(handler)}\nError:`,
          e,
        );
    }
  }
}

/** JSDoc */
function instrumentConsole() {
  if (!('console' in global)) {
    return;
  }

  _logger_js__WEBPACK_IMPORTED_MODULE_2__["CONSOLE_LEVELS"].forEach(function (level) {
    if (!(level in global.console)) {
      return;
    }

    Object(_object_js__WEBPACK_IMPORTED_MODULE_3__["fill"])(global.console, level, function (originalConsoleMethod) {
      return function (...args) {
        triggerHandlers('console', { args, level });

        // this fails for some browsers. :(
        if (originalConsoleMethod) {
          originalConsoleMethod.apply(global.console, args);
        }
      };
    });
  });
}

/** JSDoc */
function instrumentFetch() {
  if (!Object(_supports_js__WEBPACK_IMPORTED_MODULE_5__["supportsNativeFetch"])()) {
    return;
  }

  Object(_object_js__WEBPACK_IMPORTED_MODULE_3__["fill"])(global, 'fetch', function (originalFetch) {
    return function (...args) {
      var handlerData = {
        args,
        fetchData: {
          method: getFetchMethod(args),
          url: getFetchUrl(args),
        },
        startTimestamp: Date.now(),
      };

      triggerHandlers('fetch', {
        ...handlerData,
      });

            return originalFetch.apply(global, args).then(
        (response) => {
          triggerHandlers('fetch', {
            ...handlerData,
            endTimestamp: Date.now(),
            response,
          });
          return response;
        },
        (error) => {
          triggerHandlers('fetch', {
            ...handlerData,
            endTimestamp: Date.now(),
            error,
          });
          // NOTE: If you are a Sentry user, and you are seeing this stack frame,
          //       it means the sentry.javascript SDK caught an error invoking your application code.
          //       This is expected behavior and NOT indicative of a bug with sentry.javascript.
          throw error;
        },
      );
    };
  });
}

/** Extract `method` from fetch call arguments */
function getFetchMethod(fetchArgs = []) {
  if ('Request' in global && Object(_is_js__WEBPACK_IMPORTED_MODULE_1__["isInstanceOf"])(fetchArgs[0], Request) && fetchArgs[0].method) {
    return String(fetchArgs[0].method).toUpperCase();
  }
  if (fetchArgs[1] && fetchArgs[1].method) {
    return String(fetchArgs[1].method).toUpperCase();
  }
  return 'GET';
}

/** Extract `url` from fetch call arguments */
function getFetchUrl(fetchArgs = []) {
  if (typeof fetchArgs[0] === 'string') {
    return fetchArgs[0];
  }
  if ('Request' in global && Object(_is_js__WEBPACK_IMPORTED_MODULE_1__["isInstanceOf"])(fetchArgs[0], Request)) {
    return fetchArgs[0].url;
  }
  return String(fetchArgs[0]);
}

/** JSDoc */
function instrumentXHR() {
  if (!('XMLHttpRequest' in global)) {
    return;
  }

  var xhrproto = XMLHttpRequest.prototype;

  Object(_object_js__WEBPACK_IMPORTED_MODULE_3__["fill"])(xhrproto, 'open', function (originalOpen) {
    return function ( ...args) {
            var xhr = this;
      var url = args[1];
      var xhrInfo = (xhr.__sentry_xhr__ = {
                method: Object(_is_js__WEBPACK_IMPORTED_MODULE_1__["isString"])(args[0]) ? args[0].toUpperCase() : args[0],
        url: args[1],
      });

      // if Sentry key appears in URL, don't capture it as a request
            if (Object(_is_js__WEBPACK_IMPORTED_MODULE_1__["isString"])(url) && xhrInfo.method === 'POST' && url.match(/sentry_key/)) {
        xhr.__sentry_own_request__ = true;
      }

      var onreadystatechangeHandler = function () {
        if (xhr.readyState === 4) {
          try {
            // touching statusCode in some platforms throws
            // an exception
            xhrInfo.status_code = xhr.status;
          } catch (e) {
            /* do nothing */
          }

          triggerHandlers('xhr', {
            args,
            endTimestamp: Date.now(),
            startTimestamp: Date.now(),
            xhr,
          });
        }
      };

      if ('onreadystatechange' in xhr && typeof xhr.onreadystatechange === 'function') {
        Object(_object_js__WEBPACK_IMPORTED_MODULE_3__["fill"])(xhr, 'onreadystatechange', function (original) {
          return function (...readyStateArgs) {
            onreadystatechangeHandler();
            return original.apply(xhr, readyStateArgs);
          };
        });
      } else {
        xhr.addEventListener('readystatechange', onreadystatechangeHandler);
      }

      return originalOpen.apply(xhr, args);
    };
  });

  Object(_object_js__WEBPACK_IMPORTED_MODULE_3__["fill"])(xhrproto, 'send', function (originalSend) {
    return function ( ...args) {
      if (this.__sentry_xhr__ && args[0] !== undefined) {
        this.__sentry_xhr__.body = args[0];
      }

      triggerHandlers('xhr', {
        args,
        startTimestamp: Date.now(),
        xhr: this,
      });

      return originalSend.apply(this, args);
    };
  });
}

let lastHref;

/** JSDoc */
function instrumentHistory() {
  if (!Object(_supports_js__WEBPACK_IMPORTED_MODULE_5__["supportsHistory"])()) {
    return;
  }

  var oldOnPopState = global.onpopstate;
  global.onpopstate = function ( ...args) {
    var to = global.location.href;
    // keep track of the current URL state, as we always receive only the updated state
    var from = lastHref;
    lastHref = to;
    triggerHandlers('history', {
      from,
      to,
    });
    if (oldOnPopState) {
      // Apparently this can throw in Firefox when incorrectly implemented plugin is installed.
      // https://github.com/getsentry/sentry-javascript/issues/3344
      // https://github.com/bugsnag/bugsnag-js/issues/469
      try {
        return oldOnPopState.apply(this, args);
      } catch (_oO) {
        // no-empty
      }
    }
  };

  /** @hidden */
  function historyReplacementFunction(originalHistoryFunction) {
    return function ( ...args) {
      var url = args.length > 2 ? args[2] : undefined;
      if (url) {
        // coerce to string (this is what pushState does)
        var from = lastHref;
        var to = String(url);
        // keep track of the current URL state, as we always receive only the updated state
        lastHref = to;
        triggerHandlers('history', {
          from,
          to,
        });
      }
      return originalHistoryFunction.apply(this, args);
    };
  }

  Object(_object_js__WEBPACK_IMPORTED_MODULE_3__["fill"])(global.history, 'pushState', historyReplacementFunction);
  Object(_object_js__WEBPACK_IMPORTED_MODULE_3__["fill"])(global.history, 'replaceState', historyReplacementFunction);
}

var debounceDuration = 1000;
let debounceTimerID;
let lastCapturedEvent;

/**
 * Decide whether the current event should finish the debounce of previously captured one.
 * @param previous previously captured event
 * @param current event to be captured
 */
function shouldShortcircuitPreviousDebounce(previous, current) {
  // If there was no previous event, it should always be swapped for the new one.
  if (!previous) {
    return true;
  }

  // If both events have different type, then user definitely performed two separate actions. e.g. click + keypress.
  if (previous.type !== current.type) {
    return true;
  }

  try {
    // If both events have the same type, it's still possible that actions were performed on different targets.
    // e.g. 2 clicks on different buttons.
    if (previous.target !== current.target) {
      return true;
    }
  } catch (e) {
    // just accessing `target` property can throw an exception in some rare circumstances
    // see: https://github.com/getsentry/sentry-javascript/issues/838
  }

  // If both events have the same type _and_ same `target` (an element which triggered an event, _not necessarily_
  // to which an event listener was attached), we treat them as the same action, as we want to capture
  // only one breadcrumb. e.g. multiple clicks on the same button, or typing inside a user input box.
  return false;
}

/**
 * Decide whether an event should be captured.
 * @param event event to be captured
 */
function shouldSkipDOMEvent(event) {
  // We are only interested in filtering `keypress` events for now.
  if (event.type !== 'keypress') {
    return false;
  }

  try {
    var target = event.target ;

    if (!target || !target.tagName) {
      return true;
    }

    // Only consider keypress events on actual input elements. This will disregard keypresses targeting body
    // e.g.tabbing through elements, hotkeys, etc.
    if (target.tagName === 'INPUT' || target.tagName === 'TEXTAREA' || target.isContentEditable) {
      return false;
    }
  } catch (e) {
    // just accessing `target` property can throw an exception in some rare circumstances
    // see: https://github.com/getsentry/sentry-javascript/issues/838
  }

  return true;
}

/**
 * Wraps addEventListener to capture UI breadcrumbs
 * @param handler function that will be triggered
 * @param globalListener indicates whether event was captured by the global event listener
 * @returns wrapped breadcrumb events handler
 * @hidden
 */
function makeDOMEventHandler(handler, globalListener = false) {
  return (event) => {
    // It's possible this handler might trigger multiple times for the same
    // event (e.g. event propagation through node ancestors).
    // Ignore if we've already captured that event.
    if (!event || lastCapturedEvent === event) {
      return;
    }

    // We always want to skip _some_ events.
    if (shouldSkipDOMEvent(event)) {
      return;
    }

    var name = event.type === 'keypress' ? 'input' : event.type;

    // If there is no debounce timer, it means that we can safely capture the new event and store it for future comparisons.
    if (debounceTimerID === undefined) {
      handler({
        event: event,
        name,
        global: globalListener,
      });
      lastCapturedEvent = event;
    }
    // If there is a debounce awaiting, see if the new event is different enough to treat it as a unique one.
    // If that's the case, emit the previous event and store locally the newly-captured DOM event.
    else if (shouldShortcircuitPreviousDebounce(lastCapturedEvent, event)) {
      handler({
        event: event,
        name,
        global: globalListener,
      });
      lastCapturedEvent = event;
    }

    // Start a new debounce timer that will prevent us from capturing multiple events that should be grouped together.
    clearTimeout(debounceTimerID);
    debounceTimerID = global.setTimeout(() => {
      debounceTimerID = undefined;
    }, debounceDuration);
  };
}

/** JSDoc */
function instrumentDOM() {
  if (!('document' in global)) {
    return;
  }

  // Make it so that any click or keypress that is unhandled / bubbled up all the way to the document triggers our dom
  // handlers. (Normally we have only one, which captures a breadcrumb for each click or keypress.) Do this before
  // we instrument `addEventListener` so that we don't end up attaching this handler twice.
  var triggerDOMHandler = triggerHandlers.bind(null, 'dom');
  var globalDOMEventHandler = makeDOMEventHandler(triggerDOMHandler, true);
  global.document.addEventListener('click', globalDOMEventHandler, false);
  global.document.addEventListener('keypress', globalDOMEventHandler, false);

  // After hooking into click and keypress events bubbled up to `document`, we also hook into user-handled
  // clicks & keypresses, by adding an event listener of our own to any element to which they add a listener. That
  // way, whenever one of their handlers is triggered, ours will be, too. (This is needed because their handler
  // could potentially prevent the event from bubbling up to our global listeners. This way, our handler are still
  // guaranteed to fire at least once.)
  ['EventTarget', 'Node'].forEach((target) => {
        var proto = (global )[target] && (global )[target].prototype;
        if (!proto || !proto.hasOwnProperty || !proto.hasOwnProperty('addEventListener')) {
      return;
    }

    Object(_object_js__WEBPACK_IMPORTED_MODULE_3__["fill"])(proto, 'addEventListener', function (originalAddEventListener) {
      return function (
        
        type,
        listener,
        options,
      ) {
        if (type === 'click' || type == 'keypress') {
          try {
            var el = this ;
            var handlers = (el.__sentry_instrumentation_handlers__ = el.__sentry_instrumentation_handlers__ || {});
            var handlerForType = (handlers[type] = handlers[type] || { refCount: 0 });

            if (!handlerForType.handler) {
              var handler = makeDOMEventHandler(triggerDOMHandler);
              handlerForType.handler = handler;
              originalAddEventListener.call(this, type, handler, options);
            }

            handlerForType.refCount += 1;
          } catch (e) {
            // Accessing dom properties is always fragile.
            // Also allows us to skip `addEventListenrs` calls with no proper `this` context.
          }
        }

        return originalAddEventListener.call(this, type, listener, options);
      };
    });

    Object(_object_js__WEBPACK_IMPORTED_MODULE_3__["fill"])(
      proto,
      'removeEventListener',
      function (originalRemoveEventListener) {
        return function (
          
          type,
          listener,
          options,
        ) {
          if (type === 'click' || type == 'keypress') {
            try {
              var el = this ;
              var handlers = el.__sentry_instrumentation_handlers__ || {};
              var handlerForType = handlers[type];

              if (handlerForType) {
                handlerForType.refCount -= 1;
                // If there are no longer any custom handlers of the current type on this element, we can remove ours, too.
                if (handlerForType.refCount <= 0) {
                  originalRemoveEventListener.call(this, type, handlerForType.handler, options);
                  handlerForType.handler = undefined;
                  delete handlers[type];                 }

                // If there are no longer any custom handlers of any type on this element, cleanup everything.
                if (Object.keys(handlers).length === 0) {
                  delete el.__sentry_instrumentation_handlers__;
                }
              }
            } catch (e) {
              // Accessing dom properties is always fragile.
              // Also allows us to skip `addEventListenrs` calls with no proper `this` context.
            }
          }

          return originalRemoveEventListener.call(this, type, listener, options);
        };
      },
    );
  });
}

let _oldOnErrorHandler = null;
/** JSDoc */
function instrumentError() {
  _oldOnErrorHandler = global.onerror;

  global.onerror = function (msg, url, line, column, error) {
    triggerHandlers('error', {
      column,
      error,
      line,
      msg,
      url,
    });

    if (_oldOnErrorHandler) {
            return _oldOnErrorHandler.apply(this, arguments);
    }

    return false;
  };
}

let _oldOnUnhandledRejectionHandler = null;
/** JSDoc */
function instrumentUnhandledRejection() {
  _oldOnUnhandledRejectionHandler = global.onunhandledrejection;

  global.onunhandledrejection = function (e) {
    triggerHandlers('unhandledrejection', e);

    if (_oldOnUnhandledRejectionHandler) {
            return _oldOnUnhandledRejectionHandler.apply(this, arguments);
    }

    return true;
  };
}


//# sourceMappingURL=instrument.js.map


/***/ }),
/* 93 */
/***/ (function(module, __webpack_exports__, __webpack_require__) {

"use strict";
__webpack_require__.r(__webpack_exports__);
/* harmony export (binding) */ __webpack_require__.d(__webpack_exports__, "CONSOLE_LEVELS", function() { return CONSOLE_LEVELS; });
/* harmony export (binding) */ __webpack_require__.d(__webpack_exports__, "consoleSandbox", function() { return consoleSandbox; });
/* harmony export (binding) */ __webpack_require__.d(__webpack_exports__, "logger", function() { return logger; });
/* harmony import */ var _global_js__WEBPACK_IMPORTED_MODULE_0__ = __webpack_require__(84);


// TODO: Implement different loggers for different environments
var global = Object(_global_js__WEBPACK_IMPORTED_MODULE_0__["getGlobalObject"])();

/** Prefix for logging strings */
var PREFIX = 'Sentry Logger ';

var CONSOLE_LEVELS = ['debug', 'info', 'warn', 'error', 'log', 'assert', 'trace'] ;

/**
 * Temporarily disable sentry console instrumentations.
 *
 * @param callback The function to run against the original `console` messages
 * @returns The results of the callback
 */
function consoleSandbox(callback) {
  var global = Object(_global_js__WEBPACK_IMPORTED_MODULE_0__["getGlobalObject"])();

  if (!('console' in global)) {
    return callback();
  }

  var originalConsole = global.console ;
  var wrappedLevels = {};

  // Restore all wrapped console methods
  CONSOLE_LEVELS.forEach(level => {
    // TODO(v7): Remove this check as it's only needed for Node 6
    var originalWrappedFunc =
      originalConsole[level] && (originalConsole[level] ).__sentry_original__;
    if (level in global.console && originalWrappedFunc) {
      wrappedLevels[level] = originalConsole[level] ;
      originalConsole[level] = originalWrappedFunc ;
    }
  });

  try {
    return callback();
  } finally {
    // Revert restoration to wrapped state
    Object.keys(wrappedLevels).forEach(level => {
      originalConsole[level] = wrappedLevels[level ];
    });
  }
}

function makeLogger() {
  let enabled = false;
  var logger = {
    enable: () => {
      enabled = true;
    },
    disable: () => {
      enabled = false;
    },
  };

  if ((typeof __SENTRY_DEBUG__ === 'undefined' || __SENTRY_DEBUG__)) {
    CONSOLE_LEVELS.forEach(name => {
            logger[name] = (...args) => {
        if (enabled) {
          consoleSandbox(() => {
            global.console[name](`${PREFIX}[${name}]:`, ...args);
          });
        }
      };
    });
  } else {
    CONSOLE_LEVELS.forEach(name => {
      logger[name] = () => undefined;
    });
  }

  return logger ;
}

// Ensure we only have a single logger instance, even if multiple versions of @sentry/utils are being used
let logger;
if ((typeof __SENTRY_DEBUG__ === 'undefined' || __SENTRY_DEBUG__)) {
  logger = Object(_global_js__WEBPACK_IMPORTED_MODULE_0__["getGlobalSingleton"])('logger', makeLogger);
} else {
  logger = makeLogger();
}


//# sourceMappingURL=logger.js.map


/***/ }),
/* 94 */
/***/ (function(module, __webpack_exports__, __webpack_require__) {

"use strict";
__webpack_require__.r(__webpack_exports__);
/* harmony export (binding) */ __webpack_require__.d(__webpack_exports__, "addNonEnumerableProperty", function() { return addNonEnumerableProperty; });
/* harmony export (binding) */ __webpack_require__.d(__webpack_exports__, "convertToPlainObject", function() { return convertToPlainObject; });
/* harmony export (binding) */ __webpack_require__.d(__webpack_exports__, "dropUndefinedKeys", function() { return dropUndefinedKeys; });
/* harmony export (binding) */ __webpack_require__.d(__webpack_exports__, "extractExceptionKeysForMessage", function() { return extractExceptionKeysForMessage; });
/* harmony export (binding) */ __webpack_require__.d(__webpack_exports__, "fill", function() { return fill; });
/* harmony export (binding) */ __webpack_require__.d(__webpack_exports__, "getOriginalFunction", function() { return getOriginalFunction; });
/* harmony export (binding) */ __webpack_require__.d(__webpack_exports__, "markFunctionWrapped", function() { return markFunctionWrapped; });
/* harmony export (binding) */ __webpack_require__.d(__webpack_exports__, "objectify", function() { return objectify; });
/* harmony export (binding) */ __webpack_require__.d(__webpack_exports__, "urlEncode", function() { return urlEncode; });
/* harmony import */ var _browser_js__WEBPACK_IMPORTED_MODULE_0__ = __webpack_require__(83);
/* harmony import */ var _is_js__WEBPACK_IMPORTED_MODULE_1__ = __webpack_require__(89);
/* harmony import */ var _string_js__WEBPACK_IMPORTED_MODULE_2__ = __webpack_require__(95);




/**
 * Replace a method in an object with a wrapped version of itself.
 *
 * @param source An object that contains a method to be wrapped.
 * @param name The name of the method to be wrapped.
 * @param replacementFactory A higher-order function that takes the original version of the given method and returns a
 * wrapped version. Note: The function returned by `replacementFactory` needs to be a non-arrow function, in order to
 * preserve the correct value of `this`, and the original method must be called using `origMethod.call(this, <other
 * args>)` or `origMethod.apply(this, [<other args>])` (rather than being called directly), again to preserve `this`.
 * @returns void
 */
function fill(source, name, replacementFactory) {
  if (!(name in source)) {
    return;
  }

  var original = source[name] ;
  var wrapped = replacementFactory(original) ;

  // Make sure it's a function first, as we need to attach an empty prototype for `defineProperties` to work
  // otherwise it'll throw "TypeError: Object.defineProperties called on non-object"
  if (typeof wrapped === 'function') {
    try {
      markFunctionWrapped(wrapped, original);
    } catch (_Oo) {
      // This can throw if multiple fill happens on a global object like XMLHttpRequest
      // Fixes https://github.com/getsentry/sentry-javascript/issues/2043
    }
  }

  source[name] = wrapped;
}

/**
 * Defines a non-enumerable property on the given object.
 *
 * @param obj The object on which to set the property
 * @param name The name of the property to be set
 * @param value The value to which to set the property
 */
function addNonEnumerableProperty(obj, name, value) {
  Object.defineProperty(obj, name, {
    // enumerable: false, // the default, so we can save on bundle size by not explicitly setting it
    value: value,
    writable: true,
    configurable: true,
  });
}

/**
 * Remembers the original function on the wrapped function and
 * patches up the prototype.
 *
 * @param wrapped the wrapper function
 * @param original the original function that gets wrapped
 */
function markFunctionWrapped(wrapped, original) {
  var proto = original.prototype || {};
  wrapped.prototype = original.prototype = proto;
  addNonEnumerableProperty(wrapped, '__sentry_original__', original);
}

/**
 * This extracts the original function if available.  See
 * `markFunctionWrapped` for more information.
 *
 * @param func the function to unwrap
 * @returns the unwrapped version of the function if available.
 */
function getOriginalFunction(func) {
  return func.__sentry_original__;
}

/**
 * Encodes given object into url-friendly format
 *
 * @param object An object that contains serializable values
 * @returns string Encoded
 */
function urlEncode(object) {
  return Object.keys(object)
    .map(key => `${encodeURIComponent(key)}=${encodeURIComponent(object[key])}`)
    .join('&');
}

/**
 * Transforms any `Error` or `Event` into a plain object with all of their enumerable properties, and some of their
 * non-enumerable properties attached.
 *
 * @param value Initial source that we have to transform in order for it to be usable by the serializer
 * @returns An Event or Error turned into an object - or the value argurment itself, when value is neither an Event nor
 *  an Error.
 */
function convertToPlainObject(
  value,
)

 {
  if (Object(_is_js__WEBPACK_IMPORTED_MODULE_1__["isError"])(value)) {
    return {
      message: value.message,
      name: value.name,
      stack: value.stack,
      ...getOwnProperties(value),
    };
  } else if (Object(_is_js__WEBPACK_IMPORTED_MODULE_1__["isEvent"])(value)) {
    var newObj

 = {
      type: value.type,
      target: serializeEventTarget(value.target),
      currentTarget: serializeEventTarget(value.currentTarget),
      ...getOwnProperties(value),
    };

    if (typeof CustomEvent !== 'undefined' && Object(_is_js__WEBPACK_IMPORTED_MODULE_1__["isInstanceOf"])(value, CustomEvent)) {
      newObj.detail = value.detail;
    }

    return newObj;
  } else {
    return value;
  }
}

/** Creates a string representation of the target of an `Event` object */
function serializeEventTarget(target) {
  try {
    return Object(_is_js__WEBPACK_IMPORTED_MODULE_1__["isElement"])(target) ? Object(_browser_js__WEBPACK_IMPORTED_MODULE_0__["htmlTreeAsString"])(target) : Object.prototype.toString.call(target);
  } catch (_oO) {
    return '<unknown>';
  }
}

/** Filters out all but an object's own properties */
function getOwnProperties(obj) {
  if (typeof obj === 'object' && obj !== null) {
    var extractedProps = {};
    for (var property in obj) {
      if (Object.prototype.hasOwnProperty.call(obj, property)) {
        extractedProps[property] = (obj )[property];
      }
    }
    return extractedProps;
  } else {
    return {};
  }
}

/**
 * Given any captured exception, extract its keys and create a sorted
 * and truncated list that will be used inside the event message.
 * eg. `Non-error exception captured with keys: foo, bar, baz`
 */
function extractExceptionKeysForMessage(exception, maxLength = 40) {
  var keys = Object.keys(convertToPlainObject(exception));
  keys.sort();

  if (!keys.length) {
    return '[object has no keys]';
  }

  if (keys[0].length >= maxLength) {
    return Object(_string_js__WEBPACK_IMPORTED_MODULE_2__["truncate"])(keys[0], maxLength);
  }

  for (let includedKeys = keys.length; includedKeys > 0; includedKeys--) {
    var serialized = keys.slice(0, includedKeys).join(', ');
    if (serialized.length > maxLength) {
      continue;
    }
    if (includedKeys === keys.length) {
      return serialized;
    }
    return Object(_string_js__WEBPACK_IMPORTED_MODULE_2__["truncate"])(serialized, maxLength);
  }

  return '';
}

/**
 * Given any object, return a new object having removed all fields whose value was `undefined`.
 * Works recursively on objects and arrays.
 *
 * Attention: This function keeps circular references in the returned object.
 */
function dropUndefinedKeys(inputValue) {
  // This map keeps track of what already visited nodes map to.
  // Our Set - based memoBuilder doesn't work here because we want to the output object to have the same circular
  // references as the input object.
  var memoizationMap = new Map();

  // This function just proxies `_dropUndefinedKeys` to keep the `memoBuilder` out of this function's API
  return _dropUndefinedKeys(inputValue, memoizationMap);
}

function _dropUndefinedKeys(inputValue, memoizationMap) {
  if (Object(_is_js__WEBPACK_IMPORTED_MODULE_1__["isPlainObject"])(inputValue)) {
    // If this node has already been visited due to a circular reference, return the object it was mapped to in the new object
    var memoVal = memoizationMap.get(inputValue);
    if (memoVal !== undefined) {
      return memoVal ;
    }

    var returnValue = {};
    // Store the mapping of this value in case we visit it again, in case of circular data
    memoizationMap.set(inputValue, returnValue);

    for (var key of Object.keys(inputValue)) {
      if (typeof inputValue[key] !== 'undefined') {
        returnValue[key] = _dropUndefinedKeys(inputValue[key], memoizationMap);
      }
    }

    return returnValue ;
  }

  if (Array.isArray(inputValue)) {
    // If this node has already been visited due to a circular reference, return the array it was mapped to in the new object
    var memoVal = memoizationMap.get(inputValue);
    if (memoVal !== undefined) {
      return memoVal ;
    }

    var returnValue = [];
    // Store the mapping of this value in case we visit it again, in case of circular data
    memoizationMap.set(inputValue, returnValue);

    inputValue.forEach((item) => {
      returnValue.push(_dropUndefinedKeys(item, memoizationMap));
    });

    return returnValue ;
  }

  return inputValue;
}

/**
 * Ensure that something is an object.
 *
 * Turns `undefined` and `null` into `String`s and all other primitives into instances of their respective wrapper
 * classes (String, Boolean, Number, etc.). Acts as the identity function on non-primitives.
 *
 * @param wat The subject of the objectification
 * @returns A version of `wat` which can safely be used with `Object` class methods
 */
function objectify(wat) {
  let objectified;
  switch (true) {
    case wat === undefined || wat === null:
      objectified = new String(wat);
      break;

    // Though symbols and bigints do have wrapper classes (`Symbol` and `BigInt`, respectively), for whatever reason
    // those classes don't have constructors which can be used with the `new` keyword. We therefore need to cast each as
    // an object in order to wrap it.
    case typeof wat === 'symbol' || typeof wat === 'bigint':
      objectified = Object(wat);
      break;

    // this will catch the remaining primitives: `String`, `Number`, and `Boolean`
    case Object(_is_js__WEBPACK_IMPORTED_MODULE_1__["isPrimitive"])(wat):
            objectified = new (wat ).constructor(wat);
      break;

    // by process of elimination, at this point we know that `wat` must already be an object
    default:
      objectified = wat;
      break;
  }
  return objectified;
}


//# sourceMappingURL=object.js.map


/***/ }),
/* 95 */
/***/ (function(module, __webpack_exports__, __webpack_require__) {

"use strict";
__webpack_require__.r(__webpack_exports__);
/* harmony export (binding) */ __webpack_require__.d(__webpack_exports__, "escapeStringForRegex", function() { return escapeStringForRegex; });
/* harmony export (binding) */ __webpack_require__.d(__webpack_exports__, "isMatchingPattern", function() { return isMatchingPattern; });
/* harmony export (binding) */ __webpack_require__.d(__webpack_exports__, "safeJoin", function() { return safeJoin; });
/* harmony export (binding) */ __webpack_require__.d(__webpack_exports__, "snipLine", function() { return snipLine; });
/* harmony export (binding) */ __webpack_require__.d(__webpack_exports__, "truncate", function() { return truncate; });
/* harmony import */ var _is_js__WEBPACK_IMPORTED_MODULE_0__ = __webpack_require__(89);


/**
 * Truncates given string to the maximum characters count
 *
 * @param str An object that contains serializable values
 * @param max Maximum number of characters in truncated string (0 = unlimited)
 * @returns string Encoded
 */
function truncate(str, max = 0) {
  if (typeof str !== 'string' || max === 0) {
    return str;
  }
  return str.length <= max ? str : `${str.substr(0, max)}...`;
}

/**
 * This is basically just `trim_line` from
 * https://github.com/getsentry/sentry/blob/master/src/sentry/lang/javascript/processor.py#L67
 *
 * @param str An object that contains serializable values
 * @param max Maximum number of characters in truncated string
 * @returns string Encoded
 */
function snipLine(line, colno) {
  let newLine = line;
  var lineLength = newLine.length;
  if (lineLength <= 150) {
    return newLine;
  }
  if (colno > lineLength) {
        colno = lineLength;
  }

  let start = Math.max(colno - 60, 0);
  if (start < 5) {
    start = 0;
  }

  let end = Math.min(start + 140, lineLength);
  if (end > lineLength - 5) {
    end = lineLength;
  }
  if (end === lineLength) {
    start = Math.max(end - 140, 0);
  }

  newLine = newLine.slice(start, end);
  if (start > 0) {
    newLine = `'{snip} ${newLine}`;
  }
  if (end < lineLength) {
    newLine += ' {snip}';
  }

  return newLine;
}

/**
 * Join values in array
 * @param input array of values to be joined together
 * @param delimiter string to be placed in-between values
 * @returns Joined values
 */
function safeJoin(input, delimiter) {
  if (!Array.isArray(input)) {
    return '';
  }

  var output = [];
    for (let i = 0; i < input.length; i++) {
    var value = input[i];
    try {
      output.push(String(value));
    } catch (e) {
      output.push('[value cannot be serialized]');
    }
  }

  return output.join(delimiter);
}

/**
 * Checks if the value matches a regex or includes the string
 * @param value The string value to be checked against
 * @param pattern Either a regex or a string that must be contained in value
 */
function isMatchingPattern(value, pattern) {
  if (!Object(_is_js__WEBPACK_IMPORTED_MODULE_0__["isString"])(value)) {
    return false;
  }

  if (Object(_is_js__WEBPACK_IMPORTED_MODULE_0__["isRegExp"])(pattern)) {
    return pattern.test(value);
  }
  if (typeof pattern === 'string') {
    return value.indexOf(pattern) !== -1;
  }
  return false;
}

/**
 * Given a string, escape characters which have meaning in the regex grammar, such that the result is safe to feed to
 * `new RegExp()`.
 *
 * Based on https://github.com/sindresorhus/escape-string-regexp. Vendored to a) reduce the size by skipping the runtime
 * type-checking, and b) ensure it gets down-compiled for old versions of Node (the published package only supports Node
 * 12+).
 *
 * @param regexString The string to escape
 * @returns An version of the string with all special regex characters escaped
 */
function escapeStringForRegex(regexString) {
  // escape the hyphen separately so we can also replace it with a unicode literal hyphen, to avoid the problems
  // discussed in https://github.com/sindresorhus/escape-string-regexp/issues/20.
  return regexString.replace(/[|\\{}()[\]^$+*?.]/g, '\\$&').replace(/-/g, '\\x2d');
}


//# sourceMappingURL=string.js.map


/***/ }),
/* 96 */
/***/ (function(module, __webpack_exports__, __webpack_require__) {

"use strict";
__webpack_require__.r(__webpack_exports__);
/* harmony export (binding) */ __webpack_require__.d(__webpack_exports__, "createStackParser", function() { return createStackParser; });
/* harmony export (binding) */ __webpack_require__.d(__webpack_exports__, "getFunctionName", function() { return getFunctionName; });
/* harmony export (binding) */ __webpack_require__.d(__webpack_exports__, "nodeStackLineParser", function() { return nodeStackLineParser; });
/* harmony export (binding) */ __webpack_require__.d(__webpack_exports__, "stackParserFromStackParserOptions", function() { return stackParserFromStackParserOptions; });
/* harmony export (binding) */ __webpack_require__.d(__webpack_exports__, "stripSentryFramesAndReverse", function() { return stripSentryFramesAndReverse; });
/* harmony import */ var _buildPolyfills__WEBPACK_IMPORTED_MODULE_0__ = __webpack_require__(97);


var STACKTRACE_LIMIT = 50;

/**
 * Creates a stack parser with the supplied line parsers
 *
 * StackFrames are returned in the correct order for Sentry Exception
 * frames and with Sentry SDK internal frames removed from the top and bottom
 *
 */
function createStackParser(...parsers) {
  var sortedParsers = parsers.sort((a, b) => a[0] - b[0]).map(p => p[1]);

  return (stack, skipFirst = 0) => {
    var frames = [];

    for (var line of stack.split('\n').slice(skipFirst)) {
      for (var parser of sortedParsers) {
        var frame = parser(line);

        if (frame) {
          frames.push(frame);
          break;
        }
      }
    }

    return stripSentryFramesAndReverse(frames);
  };
}

/**
 * Gets a stack parser implementation from Options.stackParser
 * @see Options
 *
 * If options contains an array of line parsers, it is converted into a parser
 */
function stackParserFromStackParserOptions(stackParser) {
  if (Array.isArray(stackParser)) {
    return createStackParser(...stackParser);
  }
  return stackParser;
}

/**
 * @hidden
 */
function stripSentryFramesAndReverse(stack) {
  if (!stack.length) {
    return [];
  }

  let localStack = stack;

  var firstFrameFunction = localStack[0].function || '';
  var lastFrameFunction = localStack[localStack.length - 1].function || '';

  // If stack starts with one of our API calls, remove it (starts, meaning it's the top of the stack - aka last call)
  if (firstFrameFunction.indexOf('captureMessage') !== -1 || firstFrameFunction.indexOf('captureException') !== -1) {
    localStack = localStack.slice(1);
  }

  // If stack ends with one of our internal API calls, remove it (ends, meaning it's the bottom of the stack - aka top-most call)
  if (lastFrameFunction.indexOf('sentryWrapped') !== -1) {
    localStack = localStack.slice(0, -1);
  }

  // The frame where the crash happened, should be the last entry in the array
  return localStack
    .slice(0, STACKTRACE_LIMIT)
    .map(frame => ({
      ...frame,
      filename: frame.filename || localStack[0].filename,
      function: frame.function || '?',
    }))
    .reverse();
}

var defaultFunctionName = '<anonymous>';

/**
 * Safely extract function name from itself
 */
function getFunctionName(fn) {
  try {
    if (!fn || typeof fn !== 'function') {
      return defaultFunctionName;
    }
    return fn.name || defaultFunctionName;
  } catch (e) {
    // Just accessing custom props in some Selenium environments
    // can cause a "Permission denied" exception (see raven-js#495).
    return defaultFunctionName;
  }
}

function node(getModule) {
  var FILENAME_MATCH = /^\s*[-]{4,}$/;
  var FULL_MATCH = /at (?:async )?(?:(.+?)\s+\()?(?:(.+?):(\d+)(?::(\d+))?|([^)]+))\)?/;

    return (line) => {
    if (line.match(FILENAME_MATCH)) {
      return {
        filename: line,
      };
    }

    var lineMatch = line.match(FULL_MATCH);
    if (!lineMatch) {
      return undefined;
    }

    let object;
    let method;
    let functionName;
    let typeName;
    let methodName;

    if (lineMatch[1]) {
      functionName = lineMatch[1];

      let methodStart = functionName.lastIndexOf('.');
      if (functionName[methodStart - 1] === '.') {
                methodStart--;
      }

      if (methodStart > 0) {
        object = functionName.substr(0, methodStart);
        method = functionName.substr(methodStart + 1);
        var objectEnd = object.indexOf('.Module');
        if (objectEnd > 0) {
          functionName = functionName.substr(objectEnd + 1);
          object = object.substr(0, objectEnd);
        }
      }
      typeName = undefined;
    }

    if (method) {
      typeName = object;
      methodName = method;
    }

    if (method === '<anonymous>') {
      methodName = undefined;
      functionName = undefined;
    }

    if (functionName === undefined) {
      methodName = methodName || '<anonymous>';
      functionName = typeName ? `${typeName}.${methodName}` : methodName;
    }

    var filename = Object(_buildPolyfills__WEBPACK_IMPORTED_MODULE_0__["_optionalChain"])([lineMatch, 'access', _ => _[2], 'optionalAccess', _2 => _2.startsWith, 'call', _3 => _3('file://')]) ? lineMatch[2].substr(7) : lineMatch[2];
    var isNative = lineMatch[5] === 'native';
    var isInternal =
      isNative || (filename && !filename.startsWith('/') && !filename.startsWith('.') && filename.indexOf(':\\') !== 1);

    // in_app is all that's not an internal Node function or a module within node_modules
    // note that isNative appears to return true even for node core libraries
    // see https://github.com/getsentry/raven-node/issues/176
    var in_app = !isInternal && filename !== undefined && !filename.includes('node_modules/');

    return {
      filename,
      module: Object(_buildPolyfills__WEBPACK_IMPORTED_MODULE_0__["_optionalChain"])([getModule, 'optionalCall', _4 => _4(filename)]),
      function: functionName,
      lineno: parseInt(lineMatch[3], 10) || undefined,
      colno: parseInt(lineMatch[4], 10) || undefined,
      in_app,
    };
  };
}

/**
 * Node.js stack line parser
 *
 * This is in @sentry/utils so it can be used from the Electron SDK in the browser for when `nodeIntegration == true`.
 * This allows it to be used without referencing or importing any node specific code which causes bundlers to complain
 */
function nodeStackLineParser(getModule) {
  return [90, node(getModule)];
}


//# sourceMappingURL=stacktrace.js.map


/***/ }),
/* 97 */
/***/ (function(module, __webpack_exports__, __webpack_require__) {

"use strict";
__webpack_require__.r(__webpack_exports__);
/* harmony import */ var _asyncNullishCoalesce_js__WEBPACK_IMPORTED_MODULE_0__ = __webpack_require__(98);
/* harmony reexport (safe) */ __webpack_require__.d(__webpack_exports__, "_asyncNullishCoalesce", function() { return _asyncNullishCoalesce_js__WEBPACK_IMPORTED_MODULE_0__["_asyncNullishCoalesce"]; });

/* harmony import */ var _asyncOptionalChain_js__WEBPACK_IMPORTED_MODULE_1__ = __webpack_require__(100);
/* harmony reexport (safe) */ __webpack_require__.d(__webpack_exports__, "_asyncOptionalChain", function() { return _asyncOptionalChain_js__WEBPACK_IMPORTED_MODULE_1__["_asyncOptionalChain"]; });

/* harmony import */ var _asyncOptionalChainDelete_js__WEBPACK_IMPORTED_MODULE_2__ = __webpack_require__(101);
/* harmony reexport (safe) */ __webpack_require__.d(__webpack_exports__, "_asyncOptionalChainDelete", function() { return _asyncOptionalChainDelete_js__WEBPACK_IMPORTED_MODULE_2__["_asyncOptionalChainDelete"]; });

/* harmony import */ var _createNamedExportFrom_js__WEBPACK_IMPORTED_MODULE_3__ = __webpack_require__(102);
/* harmony reexport (safe) */ __webpack_require__.d(__webpack_exports__, "_createNamedExportFrom", function() { return _createNamedExportFrom_js__WEBPACK_IMPORTED_MODULE_3__["_createNamedExportFrom"]; });

/* harmony import */ var _createStarExport_js__WEBPACK_IMPORTED_MODULE_4__ = __webpack_require__(103);
/* harmony reexport (safe) */ __webpack_require__.d(__webpack_exports__, "_createStarExport", function() { return _createStarExport_js__WEBPACK_IMPORTED_MODULE_4__["_createStarExport"]; });

/* harmony import */ var _interopDefault_js__WEBPACK_IMPORTED_MODULE_5__ = __webpack_require__(104);
/* harmony reexport (safe) */ __webpack_require__.d(__webpack_exports__, "_interopDefault", function() { return _interopDefault_js__WEBPACK_IMPORTED_MODULE_5__["_interopDefault"]; });

/* harmony import */ var _interopNamespace_js__WEBPACK_IMPORTED_MODULE_6__ = __webpack_require__(105);
/* harmony reexport (safe) */ __webpack_require__.d(__webpack_exports__, "_interopNamespace", function() { return _interopNamespace_js__WEBPACK_IMPORTED_MODULE_6__["_interopNamespace"]; });

/* harmony import */ var _interopNamespaceDefaultOnly_js__WEBPACK_IMPORTED_MODULE_7__ = __webpack_require__(106);
/* harmony reexport (safe) */ __webpack_require__.d(__webpack_exports__, "_interopNamespaceDefaultOnly", function() { return _interopNamespaceDefaultOnly_js__WEBPACK_IMPORTED_MODULE_7__["_interopNamespaceDefaultOnly"]; });

/* harmony import */ var _interopRequireDefault_js__WEBPACK_IMPORTED_MODULE_8__ = __webpack_require__(107);
/* harmony reexport (safe) */ __webpack_require__.d(__webpack_exports__, "_interopRequireDefault", function() { return _interopRequireDefault_js__WEBPACK_IMPORTED_MODULE_8__["_interopRequireDefault"]; });

/* harmony import */ var _interopRequireWildcard_js__WEBPACK_IMPORTED_MODULE_9__ = __webpack_require__(108);
/* harmony reexport (safe) */ __webpack_require__.d(__webpack_exports__, "_interopRequireWildcard", function() { return _interopRequireWildcard_js__WEBPACK_IMPORTED_MODULE_9__["_interopRequireWildcard"]; });

/* harmony import */ var _nullishCoalesce_js__WEBPACK_IMPORTED_MODULE_10__ = __webpack_require__(99);
/* harmony reexport (safe) */ __webpack_require__.d(__webpack_exports__, "_nullishCoalesce", function() { return _nullishCoalesce_js__WEBPACK_IMPORTED_MODULE_10__["_nullishCoalesce"]; });

/* harmony import */ var _optionalChain_js__WEBPACK_IMPORTED_MODULE_11__ = __webpack_require__(109);
/* harmony reexport (safe) */ __webpack_require__.d(__webpack_exports__, "_optionalChain", function() { return _optionalChain_js__WEBPACK_IMPORTED_MODULE_11__["_optionalChain"]; });

/* harmony import */ var _optionalChainDelete_js__WEBPACK_IMPORTED_MODULE_12__ = __webpack_require__(110);
/* harmony reexport (safe) */ __webpack_require__.d(__webpack_exports__, "_optionalChainDelete", function() { return _optionalChainDelete_js__WEBPACK_IMPORTED_MODULE_12__["_optionalChainDelete"]; });














//# sourceMappingURL=index.js.map


/***/ }),
/* 98 */
/***/ (function(module, __webpack_exports__, __webpack_require__) {

"use strict";
__webpack_require__.r(__webpack_exports__);
/* harmony export (binding) */ __webpack_require__.d(__webpack_exports__, "_asyncNullishCoalesce", function() { return _asyncNullishCoalesce; });
/* harmony import */ var _nullishCoalesce_js__WEBPACK_IMPORTED_MODULE_0__ = __webpack_require__(99);


// adapted from Sucrase (https://github.com/alangpierce/sucrase)

/**
 * Polyfill for the nullish coalescing operator (`??`), when used in situations where at least one of the values is the
 * result of an async operation.
 *
 * Note that the RHS is wrapped in a function so that if it's a computed value, that evaluation won't happen unless the
 * LHS evaluates to a nullish value, to mimic the operator's short-circuiting behavior.
 *
 * Adapted from Sucrase (https://github.com/alangpierce/sucrase)
 *
 * @param lhs The value of the expression to the left of the `??`
 * @param rhsFn A function returning the value of the expression to the right of the `??`
 * @returns The LHS value, unless it's `null` or `undefined`, in which case, the RHS value
 */
async function _asyncNullishCoalesce(lhs, rhsFn) {
  return Object(_nullishCoalesce_js__WEBPACK_IMPORTED_MODULE_0__["_nullishCoalesce"])(lhs, rhsFn);
}

// Sucrase version:
// async function _asyncNullishCoalesce(lhs, rhsFn) {
//   if (lhs != null) {
//     return lhs;
//   } else {
//     return await rhsFn();
//   }
// }


//# sourceMappingURL=_asyncNullishCoalesce.js.map


/***/ }),
/* 99 */
/***/ (function(module, __webpack_exports__, __webpack_require__) {

"use strict";
__webpack_require__.r(__webpack_exports__);
/* harmony export (binding) */ __webpack_require__.d(__webpack_exports__, "_nullishCoalesce", function() { return _nullishCoalesce; });
/**
 * Polyfill for the nullish coalescing operator (`??`).
 *
 * Note that the RHS is wrapped in a function so that if it's a computed value, that evaluation won't happen unless the
 * LHS evaluates to a nullish value, to mimic the operator's short-circuiting behavior.
 *
 * Adapted from Sucrase (https://github.com/alangpierce/sucrase)
 *
 * @param lhs The value of the expression to the left of the `??`
 * @param rhsFn A function returning the value of the expression to the right of the `??`
 * @returns The LHS value, unless it's `null` or `undefined`, in which case, the RHS value
 */
function _nullishCoalesce(lhs, rhsFn) {
  // by checking for loose equality to `null`, we catch both `null` and `undefined`
  return lhs != null ? lhs : rhsFn();
}

// Sucrase version:
// function _nullishCoalesce(lhs, rhsFn) {
//   if (lhs != null) {
//     return lhs;
//   } else {
//     return rhsFn();
//   }
// }


//# sourceMappingURL=_nullishCoalesce.js.map


/***/ }),
/* 100 */
/***/ (function(module, __webpack_exports__, __webpack_require__) {

"use strict";
__webpack_require__.r(__webpack_exports__);
/* harmony export (binding) */ __webpack_require__.d(__webpack_exports__, "_asyncOptionalChain", function() { return _asyncOptionalChain; });
/**
 * Polyfill for the optional chain operator, `?.`, given previous conversion of the expression into an array of values,
 * descriptors, and functions, for situations in which at least one part of the expression is async.
 *
 * Adapted from Sucrase (https://github.com/alangpierce/sucrase) See
 * https://github.com/alangpierce/sucrase/blob/265887868966917f3b924ce38dfad01fbab1329f/src/transformers/OptionalChainingNullishTransformer.ts#L15
 *
 * @param ops Array result of expression conversion
 * @returns The value of the expression
 */
async function _asyncOptionalChain(ops) {
  let lastAccessLHS = undefined;
  let value = ops[0];
  let i = 1;
  while (i < ops.length) {
    var op = ops[i] ;
    var fn = ops[i + 1] ;
    i += 2;
    // by checking for loose equality to `null`, we catch both `null` and `undefined`
    if ((op === 'optionalAccess' || op === 'optionalCall') && value == null) {
      // really we're meaning to return `undefined` as an actual value here, but it saves bytes not to write it
      return;
    }
    if (op === 'access' || op === 'optionalAccess') {
      lastAccessLHS = value;
      value = await fn(value);
    } else if (op === 'call' || op === 'optionalCall') {
      value = await fn((...args) => (value ).call(lastAccessLHS, ...args));
      lastAccessLHS = undefined;
    }
  }
  return value;
}

// Sucrase version:
// async function _asyncOptionalChain(ops) {
//   let lastAccessLHS = undefined;
//   let value = ops[0];
//   let i = 1;
//   while (i < ops.length) {
//     var op = ops[i];
//     var fn = ops[i + 1];
//     i += 2;
//     if ((op === 'optionalAccess' || op === 'optionalCall') && value == null) {
//       return undefined;
//     }
//     if (op === 'access' || op === 'optionalAccess') {
//       lastAccessLHS = value;
//       value = await fn(value);
//     } else if (op === 'call' || op === 'optionalCall') {
//       value = await fn((...args) => value.call(lastAccessLHS, ...args));
//       lastAccessLHS = undefined;
//     }
//   }
//   return value;
// }


//# sourceMappingURL=_asyncOptionalChain.js.map


/***/ }),
/* 101 */
/***/ (function(module, __webpack_exports__, __webpack_require__) {

"use strict";
__webpack_require__.r(__webpack_exports__);
/* harmony export (binding) */ __webpack_require__.d(__webpack_exports__, "_asyncOptionalChainDelete", function() { return _asyncOptionalChainDelete; });
/* harmony import */ var _asyncOptionalChain_js__WEBPACK_IMPORTED_MODULE_0__ = __webpack_require__(100);


/**
 * Polyfill for the optional chain operator, `?.`, given previous conversion of the expression into an array of values,
 * descriptors, and functions, in cases where the value of the expression is to be deleted.
 *
 * Adapted from Sucrase (https://github.com/alangpierce/sucrase) See
 * https://github.com/alangpierce/sucrase/blob/265887868966917f3b924ce38dfad01fbab1329f/src/transformers/OptionalChainingNullishTransformer.ts#L15
 *
 * @param ops Array result of expression conversion
 * @returns The return value of the `delete` operator: `true`, unless the deletion target is an own, non-configurable
 * property (one which can't be deleted or turned into an accessor, and whose enumerability can't be changed), in which
 * case `false`.
 */
async function _asyncOptionalChainDelete(ops) {
  var result = (await Object(_asyncOptionalChain_js__WEBPACK_IMPORTED_MODULE_0__["_asyncOptionalChain"])(ops)) ;
  // If `result` is `null`, it means we didn't get to the end of the chain and so nothing was deleted (in which case,
  // return `true` since that's what `delete` does when it no-ops). If it's non-null, we know the delete happened, in
  // which case we return whatever the `delete` returned, which will be a boolean.
  return result == null ? true : (result );
}

// Sucrase version:
// async function asyncOptionalChainDelete(ops) {
//   var result = await ASYNC_OPTIONAL_CHAIN_NAME(ops);
//   return result == null ? true : result;
// }


//# sourceMappingURL=_asyncOptionalChainDelete.js.map


/***/ }),
/* 102 */
/***/ (function(module, __webpack_exports__, __webpack_require__) {

"use strict";
__webpack_require__.r(__webpack_exports__);
/* harmony export (binding) */ __webpack_require__.d(__webpack_exports__, "_createNamedExportFrom", function() { return _createNamedExportFrom; });
/**
 * Copy a property from the given object into `exports`, under the given name.
 *
 * Adapted from Sucrase (https://github.com/alangpierce/sucrase)
 *
 * @param obj The object containing the property to copy.
 * @param localName The name under which to export the property
 * @param importedName The name under which the property lives in `obj`
 */
function _createNamedExportFrom(obj, localName, importedName) {
  exports[localName] = obj[importedName];
}

// Sucrase version:
// function _createNamedExportFrom(obj, localName, importedName) {
//   Object.defineProperty(exports, localName, {enumerable: true, get: () => obj[importedName]});
// }


//# sourceMappingURL=_createNamedExportFrom.js.map


/***/ }),
/* 103 */
/***/ (function(module, __webpack_exports__, __webpack_require__) {

"use strict";
__webpack_require__.r(__webpack_exports__);
/* harmony export (binding) */ __webpack_require__.d(__webpack_exports__, "_createStarExport", function() { return _createStarExport; });
/**
 * Copy properties from an object into `exports`.
 *
 * Adapted from Sucrase (https://github.com/alangpierce/sucrase)
 *
 * @param obj The object containing the properties to copy.
 */
function _createStarExport(obj) {
  Object.keys(obj)
    .filter(key => key !== 'default' && key !== '__esModule' && !(key in exports))
    .forEach(key => (exports[key] = obj[key]));
}

// Sucrase version:
// function _createStarExport(obj) {
//   Object.keys(obj)
//     .filter(key => key !== 'default' && key !== '__esModule')
//     .forEach(key => {
//       if (exports.hasOwnProperty(key)) {
//         return;
//       }
//       Object.defineProperty(exports, key, { enumerable: true, get: () => obj[key] });
//     });
// }


//# sourceMappingURL=_createStarExport.js.map


/***/ }),
/* 104 */
/***/ (function(module, __webpack_exports__, __webpack_require__) {

"use strict";
__webpack_require__.r(__webpack_exports__);
/* harmony export (binding) */ __webpack_require__.d(__webpack_exports__, "_interopDefault", function() { return _interopDefault; });
/**
 * Unwraps a module if it has been wrapped in an object under the key `default`.
 *
 * Adapted from Rollup (https://github.com/rollup/rollup)
 *
 * @param requireResult The result of calling `require` on a module
 * @returns The full module, unwrapped if necessary.
 */
function _interopDefault(requireResult) {
  return requireResult.__esModule ? (requireResult.default ) : requireResult;
}

// Rollup version:
// function _interopDefault(e) {
//   return e && e.__esModule ? e['default'] : e;
// }


//# sourceMappingURL=_interopDefault.js.map


/***/ }),
/* 105 */
/***/ (function(module, __webpack_exports__, __webpack_require__) {

"use strict";
__webpack_require__.r(__webpack_exports__);
/* harmony export (binding) */ __webpack_require__.d(__webpack_exports__, "_interopNamespace", function() { return _interopNamespace; });
/**
 * Adds a self-referential `default` property to CJS modules which aren't the result of transpilation from ESM modules.
 *
 * Adapted from Rollup (https://github.com/rollup/rollup)
 *
 * @param requireResult The result of calling `require` on a module
 * @returns Either `requireResult` or a copy of `requireResult` with an added self-referential `default` property
 */
function _interopNamespace(requireResult) {
  return requireResult.__esModule ? requireResult : { ...requireResult, default: requireResult };
}

// Rollup version (with `output.externalLiveBindings` and `output.freeze` both set to false)
// function _interopNamespace(e) {
//   if (e && e.__esModule) return e;
//   var n = Object.create(null);
//   if (e) {
//     for (var k in e) {
//       n[k] = e[k];
//     }
//   }
//   n["default"] = e;
//   return n;
// }


//# sourceMappingURL=_interopNamespace.js.map


/***/ }),
/* 106 */
/***/ (function(module, __webpack_exports__, __webpack_require__) {

"use strict";
__webpack_require__.r(__webpack_exports__);
/* harmony export (binding) */ __webpack_require__.d(__webpack_exports__, "_interopNamespaceDefaultOnly", function() { return _interopNamespaceDefaultOnly; });
/**
 * Wrap a module in an object, as the value under the key `default`.
 *
 * Adapted from Rollup (https://github.com/rollup/rollup)
 *
 * @param requireResult The result of calling `require` on a module
 * @returns An object containing the key-value pair (`default`, `requireResult`)
 */
function _interopNamespaceDefaultOnly(requireResult) {
  return {
    __proto__: null,
    default: requireResult,
  };
}

// Rollup version
// function _interopNamespaceDefaultOnly(e) {
//   return {
//     __proto__: null,
//     'default': e
//   };
// }


//# sourceMappingURL=_interopNamespaceDefaultOnly.js.map


/***/ }),
/* 107 */
/***/ (function(module, __webpack_exports__, __webpack_require__) {

"use strict";
__webpack_require__.r(__webpack_exports__);
/* harmony export (binding) */ __webpack_require__.d(__webpack_exports__, "_interopRequireDefault", function() { return _interopRequireDefault; });
/**
 * Wraps modules which aren't the result of transpiling an ESM module in an object under the key `default`
 *
 * Adapted from Sucrase (https://github.com/alangpierce/sucrase)
 *
 * @param requireResult The result of calling `require` on a module
 * @returns `requireResult` or `requireResult` wrapped in an object, keyed as `default`
 */
function _interopRequireDefault(requireResult) {
  return requireResult.__esModule ? requireResult : { default: requireResult };
}

// Sucrase version
// function _interopRequireDefault(obj) {
//   return obj && obj.__esModule ? obj : { default: obj };
// }


//# sourceMappingURL=_interopRequireDefault.js.map


/***/ }),
/* 108 */
/***/ (function(module, __webpack_exports__, __webpack_require__) {

"use strict";
__webpack_require__.r(__webpack_exports__);
/* harmony export (binding) */ __webpack_require__.d(__webpack_exports__, "_interopRequireWildcard", function() { return _interopRequireWildcard; });
/**
 * Adds a `default` property to CJS modules which aren't the result of transpilation from ESM modules.
 *
 * Adapted from Sucrase (https://github.com/alangpierce/sucrase)
 *
 * @param requireResult The result of calling `require` on a module
 * @returns Either `requireResult` or a copy of `requireResult` with an added self-referential `default` property
 */
function _interopRequireWildcard(requireResult) {
  return requireResult.__esModule ? requireResult : { ...requireResult, default: requireResult };
}

// Sucrase version
// function _interopRequireWildcard(obj) {
//   if (obj && obj.__esModule) {
//     return obj;
//   } else {
//     var newObj = {};
//     if (obj != null) {
//       for (var key in obj) {
//         if (Object.prototype.hasOwnProperty.call(obj, key)) {
//           newObj[key] = obj[key];
//         }
//       }
//     }
//     newObj.default = obj;
//     return newObj;
//   }
// }


//# sourceMappingURL=_interopRequireWildcard.js.map


/***/ }),
/* 109 */
/***/ (function(module, __webpack_exports__, __webpack_require__) {

"use strict";
__webpack_require__.r(__webpack_exports__);
/* harmony export (binding) */ __webpack_require__.d(__webpack_exports__, "_optionalChain", function() { return _optionalChain; });
/**
 * Polyfill for the optional chain operator, `?.`, given previous conversion of the expression into an array of values,
 * descriptors, and functions.
 *
 * Adapted from Sucrase (https://github.com/alangpierce/sucrase)
 * See https://github.com/alangpierce/sucrase/blob/265887868966917f3b924ce38dfad01fbab1329f/src/transformers/OptionalChainingNullishTransformer.ts#L15
 *
 * @param ops Array result of expression conversion
 * @returns The value of the expression
 */
function _optionalChain(ops) {
  let lastAccessLHS = undefined;
  let value = ops[0];
  let i = 1;
  while (i < ops.length) {
    var op = ops[i] ;
    var fn = ops[i + 1] ;
    i += 2;
    // by checking for loose equality to `null`, we catch both `null` and `undefined`
    if ((op === 'optionalAccess' || op === 'optionalCall') && value == null) {
      // really we're meaning to return `undefined` as an actual value here, but it saves bytes not to write it
      return;
    }
    if (op === 'access' || op === 'optionalAccess') {
      lastAccessLHS = value;
      value = fn(value);
    } else if (op === 'call' || op === 'optionalCall') {
      value = fn((...args) => (value ).call(lastAccessLHS, ...args));
      lastAccessLHS = undefined;
    }
  }
  return value;
}

// Sucrase version
// function _optionalChain(ops) {
//   let lastAccessLHS = undefined;
//   let value = ops[0];
//   let i = 1;
//   while (i < ops.length) {
//     var op = ops[i];
//     var fn = ops[i + 1];
//     i += 2;
//     if ((op === 'optionalAccess' || op === 'optionalCall') && value == null) {
//       return undefined;
//     }
//     if (op === 'access' || op === 'optionalAccess') {
//       lastAccessLHS = value;
//       value = fn(value);
//     } else if (op === 'call' || op === 'optionalCall') {
//       value = fn((...args) => value.call(lastAccessLHS, ...args));
//       lastAccessLHS = undefined;
//     }
//   }
//   return value;
// }


//# sourceMappingURL=_optionalChain.js.map


/***/ }),
/* 110 */
/***/ (function(module, __webpack_exports__, __webpack_require__) {

"use strict";
__webpack_require__.r(__webpack_exports__);
/* harmony export (binding) */ __webpack_require__.d(__webpack_exports__, "_optionalChainDelete", function() { return _optionalChainDelete; });
/* harmony import */ var _optionalChain_js__WEBPACK_IMPORTED_MODULE_0__ = __webpack_require__(109);


/**
 * Polyfill for the optional chain operator, `?.`, given previous conversion of the expression into an array of values,
 * descriptors, and functions, in cases where the value of the expression is to be deleted.
 *
 * Adapted from Sucrase (https://github.com/alangpierce/sucrase) See
 * https://github.com/alangpierce/sucrase/blob/265887868966917f3b924ce38dfad01fbab1329f/src/transformers/OptionalChainingNullishTransformer.ts#L15
 *
 * @param ops Array result of expression conversion
 * @returns The return value of the `delete` operator: `true`, unless the deletion target is an own, non-configurable
 * property (one which can't be deleted or turned into an accessor, and whose enumerability can't be changed), in which
 * case `false`.
 */
function _optionalChainDelete(ops) {
  var result = Object(_optionalChain_js__WEBPACK_IMPORTED_MODULE_0__["_optionalChain"])(ops) ;
  // If `result` is `null`, it means we didn't get to the end of the chain and so nothing was deleted (in which case,
  // return `true` since that's what `delete` does when it no-ops). If it's non-null, we know the delete happened, in
  // which case we return whatever the `delete` returned, which will be a boolean.
  return result == null ? true : result;
}

// Sucrase version:
// function _optionalChainDelete(ops) {
//   var result = _optionalChain(ops);
//   // by checking for loose equality to `null`, we catch both `null` and `undefined`
//   return result == null ? true : result;
// }


//# sourceMappingURL=_optionalChainDelete.js.map


/***/ }),
/* 111 */
/***/ (function(module, __webpack_exports__, __webpack_require__) {

"use strict";
__webpack_require__.r(__webpack_exports__);
/* harmony export (binding) */ __webpack_require__.d(__webpack_exports__, "isNativeFetch", function() { return isNativeFetch; });
/* harmony export (binding) */ __webpack_require__.d(__webpack_exports__, "supportsDOMError", function() { return supportsDOMError; });
/* harmony export (binding) */ __webpack_require__.d(__webpack_exports__, "supportsDOMException", function() { return supportsDOMException; });
/* harmony export (binding) */ __webpack_require__.d(__webpack_exports__, "supportsErrorEvent", function() { return supportsErrorEvent; });
/* harmony export (binding) */ __webpack_require__.d(__webpack_exports__, "supportsFetch", function() { return supportsFetch; });
/* harmony export (binding) */ __webpack_require__.d(__webpack_exports__, "supportsHistory", function() { return supportsHistory; });
/* harmony export (binding) */ __webpack_require__.d(__webpack_exports__, "supportsNativeFetch", function() { return supportsNativeFetch; });
/* harmony export (binding) */ __webpack_require__.d(__webpack_exports__, "supportsReferrerPolicy", function() { return supportsReferrerPolicy; });
/* harmony export (binding) */ __webpack_require__.d(__webpack_exports__, "supportsReportingObserver", function() { return supportsReportingObserver; });
/* harmony import */ var _global_js__WEBPACK_IMPORTED_MODULE_0__ = __webpack_require__(84);
/* harmony import */ var _logger_js__WEBPACK_IMPORTED_MODULE_1__ = __webpack_require__(93);



/**
 * Tells whether current environment supports ErrorEvent objects
 * {@link supportsErrorEvent}.
 *
 * @returns Answer to the given question.
 */
function supportsErrorEvent() {
  try {
    new ErrorEvent('');
    return true;
  } catch (e) {
    return false;
  }
}

/**
 * Tells whether current environment supports DOMError objects
 * {@link supportsDOMError}.
 *
 * @returns Answer to the given question.
 */
function supportsDOMError() {
  try {
    // Chrome: VM89:1 Uncaught TypeError: Failed to construct 'DOMError':
    // 1 argument required, but only 0 present.
    // @ts-ignore It really needs 1 argument, not 0.
    new DOMError('');
    return true;
  } catch (e) {
    return false;
  }
}

/**
 * Tells whether current environment supports DOMException objects
 * {@link supportsDOMException}.
 *
 * @returns Answer to the given question.
 */
function supportsDOMException() {
  try {
    new DOMException('');
    return true;
  } catch (e) {
    return false;
  }
}

/**
 * Tells whether current environment supports Fetch API
 * {@link supportsFetch}.
 *
 * @returns Answer to the given question.
 */
function supportsFetch() {
  if (!('fetch' in Object(_global_js__WEBPACK_IMPORTED_MODULE_0__["getGlobalObject"])())) {
    return false;
  }

  try {
    new Headers();
    new Request('');
    new Response();
    return true;
  } catch (e) {
    return false;
  }
}
/**
 * isNativeFetch checks if the given function is a native implementation of fetch()
 */
function isNativeFetch(func) {
  return func && /^function fetch\(\)\s+\{\s+\[native code\]\s+\}$/.test(func.toString());
}

/**
 * Tells whether current environment supports Fetch API natively
 * {@link supportsNativeFetch}.
 *
 * @returns true if `window.fetch` is natively implemented, false otherwise
 */
function supportsNativeFetch() {
  if (!supportsFetch()) {
    return false;
  }

  var global = Object(_global_js__WEBPACK_IMPORTED_MODULE_0__["getGlobalObject"])();

  // Fast path to avoid DOM I/O
    if (isNativeFetch(global.fetch)) {
    return true;
  }

  // window.fetch is implemented, but is polyfilled or already wrapped (e.g: by a chrome extension)
  // so create a "pure" iframe to see if that has native fetch
  let result = false;
  var doc = global.document;
    if (doc && typeof (doc.createElement ) === 'function') {
    try {
      var sandbox = doc.createElement('iframe');
      sandbox.hidden = true;
      doc.head.appendChild(sandbox);
      if (sandbox.contentWindow && sandbox.contentWindow.fetch) {
                result = isNativeFetch(sandbox.contentWindow.fetch);
      }
      doc.head.removeChild(sandbox);
    } catch (err) {
      (typeof __SENTRY_DEBUG__ === 'undefined' || __SENTRY_DEBUG__) &&
        _logger_js__WEBPACK_IMPORTED_MODULE_1__["logger"].warn('Could not create sandbox iframe for pure fetch check, bailing to window.fetch: ', err);
    }
  }

  return result;
}

/**
 * Tells whether current environment supports ReportingObserver API
 * {@link supportsReportingObserver}.
 *
 * @returns Answer to the given question.
 */
function supportsReportingObserver() {
  return 'ReportingObserver' in Object(_global_js__WEBPACK_IMPORTED_MODULE_0__["getGlobalObject"])();
}

/**
 * Tells whether current environment supports Referrer Policy API
 * {@link supportsReferrerPolicy}.
 *
 * @returns Answer to the given question.
 */
function supportsReferrerPolicy() {
  // Despite all stars in the sky saying that Edge supports old draft syntax, aka 'never', 'always', 'origin' and 'default'
  // (see https://caniuse.com/#feat=referrer-policy),
  // it doesn't. And it throws an exception instead of ignoring this parameter...
  // REF: https://github.com/getsentry/raven-js/issues/1233

  if (!supportsFetch()) {
    return false;
  }

  try {
    new Request('_', {
      referrerPolicy: 'origin' ,
    });
    return true;
  } catch (e) {
    return false;
  }
}

/**
 * Tells whether current environment supports History API
 * {@link supportsHistory}.
 *
 * @returns Answer to the given question.
 */
function supportsHistory() {
  // NOTE: in Chrome App environment, touching history.pushState, *even inside
  //       a try/catch block*, will cause Chrome to output an error to console.error
  // borrowed from: https://github.com/angular/angular.js/pull/13945/files
  var global = Object(_global_js__WEBPACK_IMPORTED_MODULE_0__["getGlobalObject"])();
      var chrome = (global ).chrome;
  var isChromePackagedApp = chrome && chrome.app && chrome.app.runtime;
    var hasHistoryApi = 'history' in global && !!global.history.pushState && !!global.history.replaceState;

  return !isChromePackagedApp && hasHistoryApi;
}


//# sourceMappingURL=supports.js.map


/***/ }),
/* 112 */
/***/ (function(module, __webpack_exports__, __webpack_require__) {

"use strict";
__webpack_require__.r(__webpack_exports__);
/* harmony export (binding) */ __webpack_require__.d(__webpack_exports__, "memoBuilder", function() { return memoBuilder; });
/**
 * Helper to decycle json objects
 */
function memoBuilder() {
  var hasWeakSet = typeof WeakSet === 'function';
  var inner = hasWeakSet ? new WeakSet() : [];
  function memoize(obj) {
    if (hasWeakSet) {
      if (inner.has(obj)) {
        return true;
      }
      inner.add(obj);
      return false;
    }
        for (let i = 0; i < inner.length; i++) {
      var value = inner[i];
      if (value === obj) {
        return true;
      }
    }
    inner.push(obj);
    return false;
  }

  function unmemoize(obj) {
    if (hasWeakSet) {
      inner.delete(obj);
    } else {
      for (let i = 0; i < inner.length; i++) {
        if (inner[i] === obj) {
          inner.splice(i, 1);
          break;
        }
      }
    }
  }
  return [memoize, unmemoize];
}


//# sourceMappingURL=memo.js.map


/***/ }),
/* 113 */
/***/ (function(module, __webpack_exports__, __webpack_require__) {

"use strict";
__webpack_require__.r(__webpack_exports__);
/* harmony export (binding) */ __webpack_require__.d(__webpack_exports__, "addContextToFrame", function() { return addContextToFrame; });
/* harmony export (binding) */ __webpack_require__.d(__webpack_exports__, "addExceptionMechanism", function() { return addExceptionMechanism; });
/* harmony export (binding) */ __webpack_require__.d(__webpack_exports__, "addExceptionTypeValue", function() { return addExceptionTypeValue; });
/* harmony export (binding) */ __webpack_require__.d(__webpack_exports__, "checkOrSetAlreadyCaught", function() { return checkOrSetAlreadyCaught; });
/* harmony export (binding) */ __webpack_require__.d(__webpack_exports__, "getEventDescription", function() { return getEventDescription; });
/* harmony export (binding) */ __webpack_require__.d(__webpack_exports__, "parseSemver", function() { return parseSemver; });
/* harmony export (binding) */ __webpack_require__.d(__webpack_exports__, "parseUrl", function() { return parseUrl; });
/* harmony export (binding) */ __webpack_require__.d(__webpack_exports__, "stripUrlQueryAndFragment", function() { return stripUrlQueryAndFragment; });
/* harmony export (binding) */ __webpack_require__.d(__webpack_exports__, "uuid4", function() { return uuid4; });
/* harmony import */ var _global_js__WEBPACK_IMPORTED_MODULE_0__ = __webpack_require__(84);
/* harmony import */ var _object_js__WEBPACK_IMPORTED_MODULE_1__ = __webpack_require__(94);
/* harmony import */ var _string_js__WEBPACK_IMPORTED_MODULE_2__ = __webpack_require__(95);




/**
 * Extended Window interface that allows for Crypto API usage in IE browsers
 */

/**
 * UUID4 generator
 *
 * @returns string Generated UUID4.
 */
function uuid4() {
  var global = Object(_global_js__WEBPACK_IMPORTED_MODULE_0__["getGlobalObject"])() ;
  var crypto = global.crypto || global.msCrypto;

  if (!(crypto === void 0) && crypto.getRandomValues) {
    // Use window.crypto API if available
    var arr = new Uint16Array(8);
    crypto.getRandomValues(arr);

    // set 4 in byte 7
        arr[3] = (arr[3] & 0xfff) | 0x4000;
    // set 2 most significant bits of byte 9 to '10'
        arr[4] = (arr[4] & 0x3fff) | 0x8000;

    var pad = (num) => {
      let v = num.toString(16);
      while (v.length < 4) {
        v = `0${v}`;
      }
      return v;
    };

    return (
      pad(arr[0]) + pad(arr[1]) + pad(arr[2]) + pad(arr[3]) + pad(arr[4]) + pad(arr[5]) + pad(arr[6]) + pad(arr[7])
    );
  }
  // http://stackoverflow.com/questions/105034/how-to-create-a-guid-uuid-in-javascript/2117523#2117523
  return 'xxxxxxxxxxxx4xxxyxxxxxxxxxxxxxxx'.replace(/[xy]/g, c => {
        var r = (Math.random() * 16) | 0;
        var v = c === 'x' ? r : (r & 0x3) | 0x8;
    return v.toString(16);
  });
}

/**
 * Parses string form of URL into an object
 * // borrowed from https://tools.ietf.org/html/rfc3986#appendix-B
 * // intentionally using regex and not <a/> href parsing trick because React Native and other
 * // environments where DOM might not be available
 * @returns parsed URL object
 */
function parseUrl(url)

 {
  if (!url) {
    return {};
  }

  var match = url.match(/^(([^:/?#]+):)?(\/\/([^/?#]*))?([^?#]*)(\?([^#]*))?(#(.*))?$/);

  if (!match) {
    return {};
  }

  // coerce to undefined values to empty string so we don't get 'undefined'
  var query = match[6] || '';
  var fragment = match[8] || '';
  return {
    host: match[4],
    path: match[5],
    protocol: match[2],
    relative: match[5] + query + fragment, // everything minus origin
  };
}

function getFirstException(event) {
  return event.exception && event.exception.values ? event.exception.values[0] : undefined;
}

/**
 * Extracts either message or type+value from an event that can be used for user-facing logs
 * @returns event's description
 */
function getEventDescription(event) {
  const { message, event_id: eventId } = event;
  if (message) {
    return message;
  }

  var firstException = getFirstException(event);
  if (firstException) {
    if (firstException.type && firstException.value) {
      return `${firstException.type}: ${firstException.value}`;
    }
    return firstException.type || firstException.value || eventId || '<unknown>';
  }
  return eventId || '<unknown>';
}

/**
 * Adds exception values, type and value to an synthetic Exception.
 * @param event The event to modify.
 * @param value Value of the exception.
 * @param type Type of the exception.
 * @hidden
 */
function addExceptionTypeValue(event, value, type) {
  var exception = (event.exception = event.exception || {});
  var values = (exception.values = exception.values || []);
  var firstException = (values[0] = values[0] || {});
  if (!firstException.value) {
    firstException.value = value || '';
  }
  if (!firstException.type) {
    firstException.type = type || 'Error';
  }
}

/**
 * Adds exception mechanism data to a given event. Uses defaults if the second parameter is not passed.
 *
 * @param event The event to modify.
 * @param newMechanism Mechanism data to add to the event.
 * @hidden
 */
function addExceptionMechanism(event, newMechanism) {
  var firstException = getFirstException(event);
  if (!firstException) {
    return;
  }

  var defaultMechanism = { type: 'generic', handled: true };
  var currentMechanism = firstException.mechanism;
  firstException.mechanism = { ...defaultMechanism, ...currentMechanism, ...newMechanism };

  if (newMechanism && 'data' in newMechanism) {
    var mergedData = { ...(currentMechanism && currentMechanism.data), ...newMechanism.data };
    firstException.mechanism.data = mergedData;
  }
}

// https://semver.org/#is-there-a-suggested-regular-expression-regex-to-check-a-semver-string
var SEMVER_REGEXP =
  /^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)(?:-((?:0|[1-9]\d*|\d*[a-zA-Z-][0-9a-zA-Z-]*)(?:\.(?:0|[1-9]\d*|\d*[a-zA-Z-][0-9a-zA-Z-]*))*))?(?:\+([0-9a-zA-Z-]+(?:\.[0-9a-zA-Z-]+)*))?$/;

/**
 * Represents Semantic Versioning object
 */

/**
 * Parses input into a SemVer interface
 * @param input string representation of a semver version
 */
function parseSemver(input) {
  var match = input.match(SEMVER_REGEXP) || [];
  var major = parseInt(match[1], 10);
  var minor = parseInt(match[2], 10);
  var patch = parseInt(match[3], 10);
  return {
    buildmetadata: match[5],
    major: isNaN(major) ? undefined : major,
    minor: isNaN(minor) ? undefined : minor,
    patch: isNaN(patch) ? undefined : patch,
    prerelease: match[4],
  };
}

/**
 * This function adds context (pre/post/line) lines to the provided frame
 *
 * @param lines string[] containing all lines
 * @param frame StackFrame that will be mutated
 * @param linesOfContext number of context lines we want to add pre/post
 */
function addContextToFrame(lines, frame, linesOfContext = 5) {
  var lineno = frame.lineno || 0;
  var maxLines = lines.length;
  var sourceLine = Math.max(Math.min(maxLines, lineno - 1), 0);

  frame.pre_context = lines
    .slice(Math.max(0, sourceLine - linesOfContext), sourceLine)
    .map((line) => Object(_string_js__WEBPACK_IMPORTED_MODULE_2__["snipLine"])(line, 0));

  frame.context_line = Object(_string_js__WEBPACK_IMPORTED_MODULE_2__["snipLine"])(lines[Math.min(maxLines - 1, sourceLine)], frame.colno || 0);

  frame.post_context = lines
    .slice(Math.min(sourceLine + 1, maxLines), sourceLine + 1 + linesOfContext)
    .map((line) => Object(_string_js__WEBPACK_IMPORTED_MODULE_2__["snipLine"])(line, 0));
}

/**
 * Strip the query string and fragment off of a given URL or path (if present)
 *
 * @param urlPath Full URL or path, including possible query string and/or fragment
 * @returns URL or path without query string or fragment
 */
function stripUrlQueryAndFragment(urlPath) {
    return urlPath.split(/[\?#]/, 1)[0];
}

/**
 * Checks whether or not we've already captured the given exception (note: not an identical exception - the very object
 * in question), and marks it captured if not.
 *
 * This is useful because it's possible for an error to get captured by more than one mechanism. After we intercept and
 * record an error, we rethrow it (assuming we've intercepted it before it's reached the top-level global handlers), so
 * that we don't interfere with whatever effects the error might have had were the SDK not there. At that point, because
 * the error has been rethrown, it's possible for it to bubble up to some other code we've instrumented. If it's not
 * caught after that, it will bubble all the way up to the global handlers (which of course we also instrument). This
 * function helps us ensure that even if we encounter the same error more than once, we only record it the first time we
 * see it.
 *
 * Note: It will ignore primitives (always return `false` and not mark them as seen), as properties can't be set on
 * them. {@link: Object.objectify} can be used on exceptions to convert any that are primitives into their equivalent
 * object wrapper forms so that this check will always work. However, because we need to flag the exact object which
 * will get rethrown, and because that rethrowing happens outside of the event processing pipeline, the objectification
 * must be done before the exception captured.
 *
 * @param A thrown exception to check or flag as having been seen
 * @returns `true` if the exception has already been captured, `false` if not (with the side effect of marking it seen)
 */
function checkOrSetAlreadyCaught(exception) {
    if (exception && (exception ).__sentry_captured__) {
    return true;
  }

  try {
    // set it this way rather than by assignment so that it's not ennumerable and therefore isn't recorded by the
    // `ExtraErrorData` integration
    Object(_object_js__WEBPACK_IMPORTED_MODULE_1__["addNonEnumerableProperty"])(exception , '__sentry_captured__', true);
  } catch (err) {
    // `exception` is a primitive, so we can't mark it seen
  }

  return false;
}


//# sourceMappingURL=misc.js.map


/***/ }),
/* 114 */
/***/ (function(module, __webpack_exports__, __webpack_require__) {

"use strict";
__webpack_require__.r(__webpack_exports__);
/* WEBPACK VAR INJECTION */(function(global) {/* harmony export (binding) */ __webpack_require__.d(__webpack_exports__, "normalize", function() { return normalize; });
/* harmony export (binding) */ __webpack_require__.d(__webpack_exports__, "normalizeToSize", function() { return normalizeToSize; });
/* harmony export (binding) */ __webpack_require__.d(__webpack_exports__, "walk", function() { return visit; });
/* harmony import */ var _is_js__WEBPACK_IMPORTED_MODULE_0__ = __webpack_require__(89);
/* harmony import */ var _memo_js__WEBPACK_IMPORTED_MODULE_1__ = __webpack_require__(112);
/* harmony import */ var _object_js__WEBPACK_IMPORTED_MODULE_2__ = __webpack_require__(94);
/* harmony import */ var _stacktrace_js__WEBPACK_IMPORTED_MODULE_3__ = __webpack_require__(96);





/**
 * Recursively normalizes the given object.
 *
 * - Creates a copy to prevent original input mutation
 * - Skips non-enumerable properties
 * - When stringifying, calls `toJSON` if implemented
 * - Removes circular references
 * - Translates non-serializable values (`undefined`/`NaN`/functions) to serializable format
 * - Translates known global objects/classes to a string representations
 * - Takes care of `Error` object serialization
 * - Optionally limits depth of final output
 * - Optionally limits number of properties/elements included in any single object/array
 *
 * @param input The object to be normalized.
 * @param depth The max depth to which to normalize the object. (Anything deeper stringified whole.)
 * @param maxProperties The max number of elements or properties to be included in any single array or
 * object in the normallized output..
 * @returns A normalized version of the object, or `"**non-serializable**"` if any errors are thrown during normalization.
 */
function normalize(input, depth = +Infinity, maxProperties = +Infinity) {
  try {
    // since we're at the outermost level, we don't provide a key
    return visit('', input, depth, maxProperties);
  } catch (err) {
    return { ERROR: `**non-serializable** (${err})` };
  }
}

/** JSDoc */
function normalizeToSize(
    object,
  // Default Node.js REPL depth
  depth = 3,
  // 100kB, as 200kB is max payload size, so half sounds reasonable
  maxSize = 100 * 1024,
) {
  var normalized = normalize(object, depth);

  if (jsonSize(normalized) > maxSize) {
    return normalizeToSize(object, depth - 1, maxSize);
  }

  return normalized ;
}

/**
 * Visits a node to perform normalization on it
 *
 * @param key The key corresponding to the given node
 * @param value The node to be visited
 * @param depth Optional number indicating the maximum recursion depth
 * @param maxProperties Optional maximum number of properties/elements included in any single object/array
 * @param memo Optional Memo class handling decycling
 */
function visit(
  key,
  value,
  depth = +Infinity,
  maxProperties = +Infinity,
  memo = Object(_memo_js__WEBPACK_IMPORTED_MODULE_1__["memoBuilder"])(),
) {
  const [memoize, unmemoize] = memo;

  // Get the simple cases out of the way first
  if (value === null || (['number', 'boolean', 'string'].includes(typeof value) && !Object(_is_js__WEBPACK_IMPORTED_MODULE_0__["isNaN"])(value))) {
    return value ;
  }

  var stringified = stringifyValue(key, value);

  // Anything we could potentially dig into more (objects or arrays) will have come back as `"[object XXXX]"`.
  // Everything else will have already been serialized, so if we don't see that pattern, we're done.
  if (!stringified.startsWith('[object ')) {
    return stringified;
  }

  // From here on, we can assert that `value` is either an object or an array.

  // Do not normalize objects that we know have already been normalized. As a general rule, the
  // "__sentry_skip_normalization__" property should only be used sparingly and only should only be set on objects that
  // have already been normalized.
  if ((value )['__sentry_skip_normalization__']) {
    return value ;
  }

  // We're also done if we've reached the max depth
  if (depth === 0) {
    // At this point we know `serialized` is a string of the form `"[object XXXX]"`. Clean it up so it's just `"[XXXX]"`.
    return stringified.replace('object ', '');
  }

  // If we've already visited this branch, bail out, as it's circular reference. If not, note that we're seeing it now.
  if (memoize(value)) {
    return '[Circular ~]';
  }

  // If the value has a `toJSON` method, we call it to extract more information
  var valueWithToJSON = value ;
  if (valueWithToJSON && typeof valueWithToJSON.toJSON === 'function') {
    try {
      var jsonValue = valueWithToJSON.toJSON();
      // We need to normalize the return value of `.toJSON()` in case it has circular references
      return visit('', jsonValue, depth - 1, maxProperties, memo);
    } catch (err) {
      // pass (The built-in `toJSON` failed, but we can still try to do it ourselves)
    }
  }

  // At this point we know we either have an object or an array, we haven't seen it before, and we're going to recurse
  // because we haven't yet reached the max depth. Create an accumulator to hold the results of visiting each
  // property/entry, and keep track of the number of items we add to it.
  var normalized = (Array.isArray(value) ? [] : {}) ;
  let numAdded = 0;

  // Before we begin, convert`Error` and`Event` instances into plain objects, since some of each of their relevant
  // properties are non-enumerable and otherwise would get missed.
  var visitable = Object(_object_js__WEBPACK_IMPORTED_MODULE_2__["convertToPlainObject"])(value );

  for (var visitKey in visitable) {
    // Avoid iterating over fields in the prototype if they've somehow been exposed to enumeration.
    if (!Object.prototype.hasOwnProperty.call(visitable, visitKey)) {
      continue;
    }

    if (numAdded >= maxProperties) {
      normalized[visitKey] = '[MaxProperties ~]';
      break;
    }

    // Recursively visit all the child nodes
    var visitValue = visitable[visitKey];
    normalized[visitKey] = visit(visitKey, visitValue, depth - 1, maxProperties, memo);

    numAdded += 1;
  }

  // Once we've visited all the branches, remove the parent from memo storage
  unmemoize(value);

  // Return accumulated values
  return normalized;
}

/**
 * Stringify the given value. Handles various known special values and types.
 *
 * Not meant to be used on simple primitives which already have a string representation, as it will, for example, turn
 * the number 1231 into "[Object Number]", nor on `null`, as it will throw.
 *
 * @param value The value to stringify
 * @returns A stringified representation of the given value
 */
function stringifyValue(
  key,
  // this type is a tiny bit of a cheat, since this function does handle NaN (which is technically a number), but for
  // our internal use, it'll do
  value,
) {
  try {
    if (key === 'domain' && value && typeof value === 'object' && (value )._events) {
      return '[Domain]';
    }

    if (key === 'domainEmitter') {
      return '[DomainEmitter]';
    }

    // It's safe to use `global`, `window`, and `document` here in this manner, as we are asserting using `typeof` first
    // which won't throw if they are not present.

    if (typeof global !== 'undefined' && value === global) {
      return '[Global]';
    }

        if (typeof window !== 'undefined' && value === window) {
      return '[Window]';
    }

        if (typeof document !== 'undefined' && value === document) {
      return '[Document]';
    }

    // React's SyntheticEvent thingy
    if (Object(_is_js__WEBPACK_IMPORTED_MODULE_0__["isSyntheticEvent"])(value)) {
      return '[SyntheticEvent]';
    }

    if (typeof value === 'number' && value !== value) {
      return '[NaN]';
    }

    // this catches `undefined` (but not `null`, which is a primitive and can be serialized on its own)
    if (value === void 0) {
      return '[undefined]';
    }

    if (typeof value === 'function') {
      return `[Function: ${Object(_stacktrace_js__WEBPACK_IMPORTED_MODULE_3__["getFunctionName"])(value)}]`;
    }

    if (typeof value === 'symbol') {
      return `[${String(value)}]`;
    }

    // stringified BigInts are indistinguishable from regular numbers, so we need to label them to avoid confusion
    if (typeof value === 'bigint') {
      return `[BigInt: ${String(value)}]`;
    }

    // Now that we've knocked out all the special cases and the primitives, all we have left are objects. Simply casting
    // them to strings means that instances of classes which haven't defined their `toStringTag` will just come out as
    // `"[object Object]"`. If we instead look at the constructor's name (which is the same as the name of the class),
    // we can make sure that only plain objects come out that way.
    return `[object ${(Object.getPrototypeOf(value) ).constructor.name}]`;
  } catch (err) {
    return `**non-serializable** (${err})`;
  }
}

/** Calculates bytes size of input string */
function utf8Length(value) {
    return ~-encodeURI(value).split(/%..|./).length;
}

/** Calculates bytes size of input object */
function jsonSize(value) {
  return utf8Length(JSON.stringify(value));
}


//# sourceMappingURL=normalize.js.map

/* WEBPACK VAR INJECTION */}.call(this, __webpack_require__(7)))

/***/ }),
/* 115 */
/***/ (function(module, __webpack_exports__, __webpack_require__) {

"use strict";
__webpack_require__.r(__webpack_exports__);
/* harmony export (binding) */ __webpack_require__.d(__webpack_exports__, "basename", function() { return basename; });
/* harmony export (binding) */ __webpack_require__.d(__webpack_exports__, "dirname", function() { return dirname; });
/* harmony export (binding) */ __webpack_require__.d(__webpack_exports__, "isAbsolute", function() { return isAbsolute; });
/* harmony export (binding) */ __webpack_require__.d(__webpack_exports__, "join", function() { return join; });
/* harmony export (binding) */ __webpack_require__.d(__webpack_exports__, "normalizePath", function() { return normalizePath; });
/* harmony export (binding) */ __webpack_require__.d(__webpack_exports__, "relative", function() { return relative; });
/* harmony export (binding) */ __webpack_require__.d(__webpack_exports__, "resolve", function() { return resolve; });
// Slightly modified (no IE8 support, ES6) and transcribed to TypeScript
// https://raw.githubusercontent.com/calvinmetcalf/rollup-plugin-node-builtins/master/src/es6/path.js

/** JSDoc */
function normalizeArray(parts, allowAboveRoot) {
  // if the path tries to go above the root, `up` ends up > 0
  let up = 0;
  for (let i = parts.length - 1; i >= 0; i--) {
    var last = parts[i];
    if (last === '.') {
      parts.splice(i, 1);
    } else if (last === '..') {
      parts.splice(i, 1);
            up++;
    } else if (up) {
      parts.splice(i, 1);
            up--;
    }
  }

  // if the path is allowed to go above the root, restore leading ..s
  if (allowAboveRoot) {
        for (; up--; up) {
      parts.unshift('..');
    }
  }

  return parts;
}

// Split a filename into [root, dir, basename, ext], unix version
// 'root' is just a slash, or nothing.
var splitPathRe = /^(\/?|)([\s\S]*?)((?:\.{1,2}|[^/]+?|)(\.[^./]*|))(?:[/]*)$/;
/** JSDoc */
function splitPath(filename) {
  var parts = splitPathRe.exec(filename);
  return parts ? parts.slice(1) : [];
}

// path.resolve([from ...], to)
// posix version
/** JSDoc */
function resolve(...args) {
  let resolvedPath = '';
  let resolvedAbsolute = false;

  for (let i = args.length - 1; i >= -1 && !resolvedAbsolute; i--) {
    var path = i >= 0 ? args[i] : '/';

    // Skip empty entries
    if (!path) {
      continue;
    }

    resolvedPath = `${path}/${resolvedPath}`;
    resolvedAbsolute = path.charAt(0) === '/';
  }

  // At this point the path should be resolved to a full absolute path, but
  // handle relative paths to be safe (might happen when process.cwd() fails)

  // Normalize the path
  resolvedPath = normalizeArray(
    resolvedPath.split('/').filter(p => !!p),
    !resolvedAbsolute,
  ).join('/');

  return (resolvedAbsolute ? '/' : '') + resolvedPath || '.';
}

/** JSDoc */
function trim(arr) {
  let start = 0;
  for (; start < arr.length; start++) {
    if (arr[start] !== '') {
      break;
    }
  }

  let end = arr.length - 1;
  for (; end >= 0; end--) {
    if (arr[end] !== '') {
      break;
    }
  }

  if (start > end) {
    return [];
  }
  return arr.slice(start, end - start + 1);
}

// path.relative(from, to)
// posix version
/** JSDoc */
function relative(from, to) {
    from = resolve(from).substr(1);
  to = resolve(to).substr(1);
  
  var fromParts = trim(from.split('/'));
  var toParts = trim(to.split('/'));

  var length = Math.min(fromParts.length, toParts.length);
  let samePartsLength = length;
  for (let i = 0; i < length; i++) {
    if (fromParts[i] !== toParts[i]) {
      samePartsLength = i;
      break;
    }
  }

  let outputParts = [];
  for (let i = samePartsLength; i < fromParts.length; i++) {
    outputParts.push('..');
  }

  outputParts = outputParts.concat(toParts.slice(samePartsLength));

  return outputParts.join('/');
}

// path.normalize(path)
// posix version
/** JSDoc */
function normalizePath(path) {
  var isPathAbsolute = isAbsolute(path);
  var trailingSlash = path.substr(-1) === '/';

  // Normalize the path
  let normalizedPath = normalizeArray(
    path.split('/').filter(p => !!p),
    !isPathAbsolute,
  ).join('/');

  if (!normalizedPath && !isPathAbsolute) {
    normalizedPath = '.';
  }
  if (normalizedPath && trailingSlash) {
    normalizedPath += '/';
  }

  return (isPathAbsolute ? '/' : '') + normalizedPath;
}

// posix version
/** JSDoc */
function isAbsolute(path) {
  return path.charAt(0) === '/';
}

// posix version
/** JSDoc */
function join(...args) {
  return normalizePath(args.join('/'));
}

/** JSDoc */
function dirname(path) {
  var result = splitPath(path);
  var root = result[0];
  let dir = result[1];

  if (!root && !dir) {
    // No dirname whatsoever
    return '.';
  }

  if (dir) {
    // It has a dirname, strip trailing slash
    dir = dir.substr(0, dir.length - 1);
  }

  return root + dir;
}

/** JSDoc */
function basename(path, ext) {
  let f = splitPath(path)[2];
  if (ext && f.substr(ext.length * -1) === ext) {
    f = f.substr(0, f.length - ext.length);
  }
  return f;
}


//# sourceMappingURL=path.js.map


/***/ }),
/* 116 */
/***/ (function(module, __webpack_exports__, __webpack_require__) {

"use strict";
__webpack_require__.r(__webpack_exports__);
/* harmony export (binding) */ __webpack_require__.d(__webpack_exports__, "makePromiseBuffer", function() { return makePromiseBuffer; });
/* harmony import */ var _error_js__WEBPACK_IMPORTED_MODULE_0__ = __webpack_require__(91);
/* harmony import */ var _syncpromise_js__WEBPACK_IMPORTED_MODULE_1__ = __webpack_require__(117);



/**
 * Creates an new PromiseBuffer object with the specified limit
 * @param limit max number of promises that can be stored in the buffer
 */
function makePromiseBuffer(limit) {
  var buffer = [];

  function isReady() {
    return limit === undefined || buffer.length < limit;
  }

  /**
   * Remove a promise from the queue.
   *
   * @param task Can be any PromiseLike<T>
   * @returns Removed promise.
   */
  function remove(task) {
    return buffer.splice(buffer.indexOf(task), 1)[0];
  }

  /**
   * Add a promise (representing an in-flight action) to the queue, and set it to remove itself on fulfillment.
   *
   * @param taskProducer A function producing any PromiseLike<T>; In previous versions this used to be `task:
   *        PromiseLike<T>`, but under that model, Promises were instantly created on the call-site and their executor
   *        functions therefore ran immediately. Thus, even if the buffer was full, the action still happened. By
   *        requiring the promise to be wrapped in a function, we can defer promise creation until after the buffer
   *        limit check.
   * @returns The original promise.
   */
  function add(taskProducer) {
    if (!isReady()) {
      return Object(_syncpromise_js__WEBPACK_IMPORTED_MODULE_1__["rejectedSyncPromise"])(new _error_js__WEBPACK_IMPORTED_MODULE_0__["SentryError"]('Not adding Promise due to buffer limit reached.'));
    }

    // start the task and add its promise to the queue
    var task = taskProducer();
    if (buffer.indexOf(task) === -1) {
      buffer.push(task);
    }
    void task
      .then(() => remove(task))
      // Use `then(null, rejectionHandler)` rather than `catch(rejectionHandler)` so that we can use `PromiseLike`
      // rather than `Promise`. `PromiseLike` doesn't have a `.catch` method, making its polyfill smaller. (ES5 didn't
      // have promises, so TS has to polyfill when down-compiling.)
      .then(null, () =>
        remove(task).then(null, () => {
          // We have to add another catch here because `remove()` starts a new promise chain.
        }),
      );
    return task;
  }

  /**
   * Wait for all promises in the queue to resolve or for timeout to expire, whichever comes first.
   *
   * @param timeout The time, in ms, after which to resolve to `false` if the queue is still non-empty. Passing `0` (or
   * not passing anything) will make the promise wait as long as it takes for the queue to drain before resolving to
   * `true`.
   * @returns A promise which will resolve to `true` if the queue is already empty or drains before the timeout, and
   * `false` otherwise
   */
  function drain(timeout) {
    return new _syncpromise_js__WEBPACK_IMPORTED_MODULE_1__["SyncPromise"]((resolve, reject) => {
      let counter = buffer.length;

      if (!counter) {
        return resolve(true);
      }

      // wait for `timeout` ms and then resolve to `false` (if not cancelled first)
      var capturedSetTimeout = setTimeout(() => {
        if (timeout && timeout > 0) {
          resolve(false);
        }
      }, timeout);

      // if all promises resolve in time, cancel the timer and resolve to `true`
      buffer.forEach(item => {
        void Object(_syncpromise_js__WEBPACK_IMPORTED_MODULE_1__["resolvedSyncPromise"])(item).then(() => {
                    if (!--counter) {
            clearTimeout(capturedSetTimeout);
            resolve(true);
          }
        }, reject);
      });
    });
  }

  return {
    $: buffer,
    add,
    drain,
  };
}


//# sourceMappingURL=promisebuffer.js.map


/***/ }),
/* 117 */
/***/ (function(module, __webpack_exports__, __webpack_require__) {

"use strict";
__webpack_require__.r(__webpack_exports__);
/* harmony export (binding) */ __webpack_require__.d(__webpack_exports__, "SyncPromise", function() { return SyncPromise; });
/* harmony export (binding) */ __webpack_require__.d(__webpack_exports__, "rejectedSyncPromise", function() { return rejectedSyncPromise; });
/* harmony export (binding) */ __webpack_require__.d(__webpack_exports__, "resolvedSyncPromise", function() { return resolvedSyncPromise; });
/* harmony import */ var _is_js__WEBPACK_IMPORTED_MODULE_0__ = __webpack_require__(89);


/** SyncPromise internal states */
var States; (function (States) {
  /** Pending */
  var PENDING = 0; States[States["PENDING"] = PENDING] = "PENDING";
  /** Resolved / OK */
  var RESOLVED = 1; States[States["RESOLVED"] = RESOLVED] = "RESOLVED";
  /** Rejected / Error */
  var REJECTED = 2; States[States["REJECTED"] = REJECTED] = "REJECTED";
})(States || (States = {}));

// Overloads so we can call resolvedSyncPromise without arguments and generic argument

/**
 * Creates a resolved sync promise.
 *
 * @param value the value to resolve the promise with
 * @returns the resolved sync promise
 */
function resolvedSyncPromise(value) {
  return new SyncPromise(resolve => {
    resolve(value);
  });
}

/**
 * Creates a rejected sync promise.
 *
 * @param value the value to reject the promise with
 * @returns the rejected sync promise
 */
function rejectedSyncPromise(reason) {
  return new SyncPromise((_, reject) => {
    reject(reason);
  });
}

/**
 * Thenable class that behaves like a Promise and follows it's interface
 * but is not async internally
 */
class SyncPromise {
   __init() {this._state = States.PENDING;}
   __init2() {this._handlers = [];}
  

   constructor(
    executor,
  ) {;SyncPromise.prototype.__init.call(this);SyncPromise.prototype.__init2.call(this);SyncPromise.prototype.__init3.call(this);SyncPromise.prototype.__init4.call(this);SyncPromise.prototype.__init5.call(this);SyncPromise.prototype.__init6.call(this);
    try {
      executor(this._resolve, this._reject);
    } catch (e) {
      this._reject(e);
    }
  }

  /** JSDoc */
   then(
    onfulfilled,
    onrejected,
  ) {
    return new SyncPromise((resolve, reject) => {
      this._handlers.push([
        false,
        result => {
          if (!onfulfilled) {
            // TODO: ¯\_(ツ)_/¯
            // TODO: FIXME
            resolve(result );
          } else {
            try {
              resolve(onfulfilled(result));
            } catch (e) {
              reject(e);
            }
          }
        },
        reason => {
          if (!onrejected) {
            reject(reason);
          } else {
            try {
              resolve(onrejected(reason));
            } catch (e) {
              reject(e);
            }
          }
        },
      ]);
      this._executeHandlers();
    });
  }

  /** JSDoc */
   catch(
    onrejected,
  ) {
    return this.then(val => val, onrejected);
  }

  /** JSDoc */
   finally(onfinally) {
    return new SyncPromise((resolve, reject) => {
      let val;
      let isRejected;

      return this.then(
        value => {
          isRejected = false;
          val = value;
          if (onfinally) {
            onfinally();
          }
        },
        reason => {
          isRejected = true;
          val = reason;
          if (onfinally) {
            onfinally();
          }
        },
      ).then(() => {
        if (isRejected) {
          reject(val);
          return;
        }

        resolve(val );
      });
    });
  }

  /** JSDoc */
    __init3() {this._resolve = (value) => {
    this._setResult(States.RESOLVED, value);
  };}

  /** JSDoc */
    __init4() {this._reject = (reason) => {
    this._setResult(States.REJECTED, reason);
  };}

  /** JSDoc */
    __init5() {this._setResult = (state, value) => {
    if (this._state !== States.PENDING) {
      return;
    }

    if (Object(_is_js__WEBPACK_IMPORTED_MODULE_0__["isThenable"])(value)) {
      void (value ).then(this._resolve, this._reject);
      return;
    }

    this._state = state;
    this._value = value;

    this._executeHandlers();
  };}

  /** JSDoc */
    __init6() {this._executeHandlers = () => {
    if (this._state === States.PENDING) {
      return;
    }

    var cachedHandlers = this._handlers.slice();
    this._handlers = [];

    cachedHandlers.forEach(handler => {
      if (handler[0]) {
        return;
      }

      if (this._state === States.RESOLVED) {
                handler[1](this._value );
      }

      if (this._state === States.REJECTED) {
        handler[2](this._value);
      }

      handler[0] = true;
    });
  };}
}


//# sourceMappingURL=syncpromise.js.map


/***/ }),
/* 118 */
/***/ (function(module, __webpack_exports__, __webpack_require__) {

"use strict";
__webpack_require__.r(__webpack_exports__);
/* harmony export (binding) */ __webpack_require__.d(__webpack_exports__, "addRequestDataToEvent", function() { return addRequestDataToEvent; });
/* harmony export (binding) */ __webpack_require__.d(__webpack_exports__, "addRequestDataToTransaction", function() { return addRequestDataToTransaction; });
/* harmony export (binding) */ __webpack_require__.d(__webpack_exports__, "extractPathForTransaction", function() { return extractPathForTransaction; });
/* harmony export (binding) */ __webpack_require__.d(__webpack_exports__, "extractRequestData", function() { return extractRequestData; });
/* harmony import */ var _buildPolyfills__WEBPACK_IMPORTED_MODULE_0__ = __webpack_require__(97);
/* harmony import */ var _is_js__WEBPACK_IMPORTED_MODULE_1__ = __webpack_require__(89);
/* harmony import */ var _misc_js__WEBPACK_IMPORTED_MODULE_2__ = __webpack_require__(113);
/* harmony import */ var _normalize_js__WEBPACK_IMPORTED_MODULE_3__ = __webpack_require__(114);





var DEFAULT_INCLUDES = {
  ip: false,
  request: true,
  transaction: true,
  user: true,
};
var DEFAULT_REQUEST_INCLUDES = ['cookies', 'data', 'headers', 'method', 'query_string', 'url'];
var DEFAULT_USER_INCLUDES = ['id', 'username', 'email'];

/**
 * Sets parameterized route as transaction name e.g.: `GET /users/:id`
 * Also adds more context data on the transaction from the request
 */
function addRequestDataToTransaction(
  transaction,
  req,
  deps,
) {
  if (!transaction) return;
  transaction.name = extractPathForTransaction(req, { path: true, method: true });
  transaction.setData('url', req.originalUrl || req.url);
  if (req.baseUrl) {
    transaction.setData('baseUrl', req.baseUrl);
  }
  transaction.setData('query', extractQueryParams(req, deps));
}

/**
 * Extracts complete generalized path from the request object and uses it to construct transaction name.
 *
 * eg. GET /mountpoint/user/:id
 *
 * @param req A request object
 * @param options What to include in the transaction name (method, path, or both)
 *
 * @returns The fully constructed transaction name
 */
function extractPathForTransaction(
  req,
  options = {},
) {
  var method = req.method && req.method.toUpperCase();

  let path = '';
  // Check to see if there's a parameterized route we can use (as there is in Express)
  if (req.route) {
    path = `${req.baseUrl || ''}${req.route.path}`;
  }
  // Otherwise, just take the original URL
  else if (req.originalUrl || req.url) {
    path = Object(_misc_js__WEBPACK_IMPORTED_MODULE_2__["stripUrlQueryAndFragment"])(req.originalUrl || req.url || '');
  }

  let info = '';
  if (options.method && method) {
    info += method;
  }
  if (options.method && options.path) {
    info += ' ';
  }
  if (options.path && path) {
    info += path;
  }

  return info;
}

/** JSDoc */
function extractTransaction(req, type) {
  switch (type) {
    case 'path': {
      return extractPathForTransaction(req, { path: true });
    }
    case 'handler': {
      return (req.route && req.route.stack && req.route.stack[0] && req.route.stack[0].name) || '<anonymous>';
    }
    case 'methodPath':
    default: {
      return extractPathForTransaction(req, { path: true, method: true });
    }
  }
}

/** JSDoc */
function extractUserData(
  user

,
  keys,
) {
  var extractedUser = {};
  var attributes = Array.isArray(keys) ? keys : DEFAULT_USER_INCLUDES;

  attributes.forEach(key => {
    if (user && key in user) {
      extractedUser[key] = user[key];
    }
  });

  return extractedUser;
}

/**
 * Normalize data from the request object, accounting for framework differences.
 *
 * @param req The request object from which to extract data
 * @param options.include An optional array of keys to include in the normalized data. Defaults to
 * DEFAULT_REQUEST_INCLUDES if not provided.
 * @param options.deps Injected, platform-specific dependencies
 * @returns An object containing normalized request data
 */
function extractRequestData(
  req,
  options

,
) {
  const { include = DEFAULT_REQUEST_INCLUDES, deps } = options || {};
  var requestData = {};

  // headers:
  //   node, express, koa, nextjs: req.headers
  var headers = (req.headers || {}) 

;
  // method:
  //   node, express, koa, nextjs: req.method
  var method = req.method;
  // host:
  //   express: req.hostname in > 4 and req.host in < 4
  //   koa: req.host
  //   node, nextjs: req.headers.host
  var host = req.hostname || req.host || headers.host || '<no host>';
  // protocol:
  //   node, nextjs: <n/a>
  //   express, koa: req.protocol
  var protocol = req.protocol === 'https' || (req.socket && req.socket.encrypted) ? 'https' : 'http';
  // url (including path and query string):
  //   node, express: req.originalUrl
  //   koa, nextjs: req.url
  var originalUrl = req.originalUrl || req.url || '';
  // absolute url
  var absoluteUrl = `${protocol}://${host}${originalUrl}`;
  include.forEach(key => {
    switch (key) {
      case 'headers': {
        requestData.headers = headers;
        break;
      }
      case 'method': {
        requestData.method = method;
        break;
      }
      case 'url': {
        requestData.url = absoluteUrl;
        break;
      }
      case 'cookies': {
        // cookies:
        //   node, express, koa: req.headers.cookie
        //   vercel, sails.js, express (w/ cookie middleware), nextjs: req.cookies
                requestData.cookies =
          // TODO (v8 / #5257): We're only sending the empty object for backwards compatibility, so the last bit can
          // come off in v8
          req.cookies || (headers.cookie && deps && deps.cookie && deps.cookie.parse(headers.cookie)) || {};
        break;
      }
      case 'query_string': {
        // query string:
        //   node: req.url (raw)
        //   express, koa, nextjs: req.query
                requestData.query_string = extractQueryParams(req, deps);
        break;
      }
      case 'data': {
        if (method === 'GET' || method === 'HEAD') {
          break;
        }
        // body data:
        //   express, koa, nextjs: req.body
        //
        //   when using node by itself, you have to read the incoming stream(see
        //   https://nodejs.dev/learn/get-http-request-body-data-using-nodejs); if a user is doing that, we can't know
        //   where they're going to store the final result, so they'll have to capture this data themselves
        if (req.body !== undefined) {
          requestData.data = Object(_is_js__WEBPACK_IMPORTED_MODULE_1__["isString"])(req.body) ? req.body : JSON.stringify(Object(_normalize_js__WEBPACK_IMPORTED_MODULE_3__["normalize"])(req.body));
        }
        break;
      }
      default: {
        if ({}.hasOwnProperty.call(req, key)) {
          requestData[key] = (req )[key];
        }
      }
    }
  });

  return requestData;
}

/**
 * Options deciding what parts of the request to use when enhancing an event
 */

/**
 * Add data from the given request to the given event
 *
 * @param event The event to which the request data will be added
 * @param req Request object
 * @param options.include Flags to control what data is included
 * @param options.deps Injected platform-specific dependencies
 * @hidden
 */
function addRequestDataToEvent(
  event,
  req,
  options,
) {
  var include = {
    ...DEFAULT_INCLUDES,
    ...Object(_buildPolyfills__WEBPACK_IMPORTED_MODULE_0__["_optionalChain"])([options, 'optionalAccess', _ => _.include]),
  };

  if (include.request) {
    var extractedRequestData = Array.isArray(include.request)
      ? extractRequestData(req, { include: include.request, deps: Object(_buildPolyfills__WEBPACK_IMPORTED_MODULE_0__["_optionalChain"])([options, 'optionalAccess', _2 => _2.deps]) })
      : extractRequestData(req, { deps: Object(_buildPolyfills__WEBPACK_IMPORTED_MODULE_0__["_optionalChain"])([options, 'optionalAccess', _3 => _3.deps]) });

    event.request = {
      ...event.request,
      ...extractedRequestData,
    };
  }

  if (include.user) {
    var extractedUser = req.user && Object(_is_js__WEBPACK_IMPORTED_MODULE_1__["isPlainObject"])(req.user) ? extractUserData(req.user, include.user) : {};

    if (Object.keys(extractedUser).length) {
      event.user = {
        ...event.user,
        ...extractedUser,
      };
    }
  }

  // client ip:
  //   node, nextjs: req.socket.remoteAddress
  //   express, koa: req.ip
  if (include.ip) {
    var ip = req.ip || (req.socket && req.socket.remoteAddress);
    if (ip) {
      event.user = {
        ...event.user,
        ip_address: ip,
      };
    }
  }

  if (include.transaction && !event.transaction) {
    // TODO do we even need this anymore?
    // TODO make this work for nextjs
    event.transaction = extractTransaction(req, include.transaction);
  }

  return event;
}

function extractQueryParams(
  req,
  deps,
) {
  // url (including path and query string):
  //   node, express: req.originalUrl
  //   koa, nextjs: req.url
  let originalUrl = req.originalUrl || req.url || '';

  if (!originalUrl) {
    return;
  }

  // The `URL` constructor can't handle internal URLs of the form `/some/path/here`, so stick a dummy protocol and
  // hostname on the beginning. Since the point here is just to grab the query string, it doesn't matter what we use.
  if (originalUrl.startsWith('/')) {
    originalUrl = `http://dogs.are.great${originalUrl}`;
  }

  return (
    req.query ||
    (typeof URL !== undefined && new URL(originalUrl).search.replace('?', '')) ||
    // In Node 8, `URL` isn't in the global scope, so we have to use the built-in module from Node
    (deps && deps.url && deps.url.parse(originalUrl).query) ||
    undefined
  );
}


//# sourceMappingURL=requestdata.js.map


/***/ }),
/* 119 */
/***/ (function(module, __webpack_exports__, __webpack_require__) {

"use strict";
__webpack_require__.r(__webpack_exports__);
/* harmony export (binding) */ __webpack_require__.d(__webpack_exports__, "severityFromString", function() { return severityFromString; });
/* harmony export (binding) */ __webpack_require__.d(__webpack_exports__, "severityLevelFromString", function() { return severityLevelFromString; });
/* harmony export (binding) */ __webpack_require__.d(__webpack_exports__, "validSeverityLevels", function() { return validSeverityLevels; });
// Note: Ideally the `SeverityLevel` type would be derived from `validSeverityLevels`, but that would mean either
//
// a) moving `validSeverityLevels` to `@sentry/types`,
// b) moving the`SeverityLevel` type here, or
// c) importing `validSeverityLevels` from here into `@sentry/types`.
//
// Option A would make `@sentry/types` a runtime dependency of `@sentry/utils` (not good), and options B and C would
// create a circular dependency between `@sentry/types` and `@sentry/utils` (also not good). So a TODO accompanying the
// type, reminding anyone who changes it to change this list also, will have to do.

var validSeverityLevels = ['fatal', 'error', 'warning', 'log', 'info', 'debug'];

/**
 * Converts a string-based level into a member of the deprecated {@link Severity} enum.
 *
 * @deprecated `severityFromString` is deprecated. Please use `severityLevelFromString` instead.
 *
 * @param level String representation of Severity
 * @returns Severity
 */
function severityFromString(level) {
  return severityLevelFromString(level) ;
}

/**
 * Converts a string-based level into a `SeverityLevel`, normalizing it along the way.
 *
 * @param level String representation of desired `SeverityLevel`.
 * @returns The `SeverityLevel` corresponding to the given string, or 'log' if the string isn't a valid level.
 */
function severityLevelFromString(level) {
  return (level === 'warn' ? 'warning' : validSeverityLevels.includes(level) ? level : 'log') ;
}


//# sourceMappingURL=severity.js.map


/***/ }),
/* 120 */
/***/ (function(module, __webpack_exports__, __webpack_require__) {

"use strict";
__webpack_require__.r(__webpack_exports__);
/* WEBPACK VAR INJECTION */(function(module) {/* harmony export (binding) */ __webpack_require__.d(__webpack_exports__, "_browserPerformanceTimeOriginMode", function() { return _browserPerformanceTimeOriginMode; });
/* harmony export (binding) */ __webpack_require__.d(__webpack_exports__, "browserPerformanceTimeOrigin", function() { return browserPerformanceTimeOrigin; });
/* harmony export (binding) */ __webpack_require__.d(__webpack_exports__, "dateTimestampInSeconds", function() { return dateTimestampInSeconds; });
/* harmony export (binding) */ __webpack_require__.d(__webpack_exports__, "timestampInSeconds", function() { return timestampInSeconds; });
/* harmony export (binding) */ __webpack_require__.d(__webpack_exports__, "timestampWithMs", function() { return timestampWithMs; });
/* harmony export (binding) */ __webpack_require__.d(__webpack_exports__, "usingPerformanceAPI", function() { return usingPerformanceAPI; });
/* harmony import */ var _global_js__WEBPACK_IMPORTED_MODULE_0__ = __webpack_require__(84);
/* harmony import */ var _node_js__WEBPACK_IMPORTED_MODULE_1__ = __webpack_require__(85);



/**
 * An object that can return the current timestamp in seconds since the UNIX epoch.
 */

/**
 * A TimestampSource implementation for environments that do not support the Performance Web API natively.
 *
 * Note that this TimestampSource does not use a monotonic clock. A call to `nowSeconds` may return a timestamp earlier
 * than a previously returned value. We do not try to emulate a monotonic behavior in order to facilitate debugging. It
 * is more obvious to explain "why does my span have negative duration" than "why my spans have zero duration".
 */
var dateTimestampSource = {
  nowSeconds: () => Date.now() / 1000,
};

/**
 * A partial definition of the [Performance Web API]{@link https://developer.mozilla.org/en-US/docs/Web/API/Performance}
 * for accessing a high-resolution monotonic clock.
 */

/**
 * Returns a wrapper around the native Performance API browser implementation, or undefined for browsers that do not
 * support the API.
 *
 * Wrapping the native API works around differences in behavior from different browsers.
 */
function getBrowserPerformance() {
  const { performance } = Object(_global_js__WEBPACK_IMPORTED_MODULE_0__["getGlobalObject"])();
  if (!performance || !performance.now) {
    return undefined;
  }

  // Replace performance.timeOrigin with our own timeOrigin based on Date.now().
  //
  // This is a partial workaround for browsers reporting performance.timeOrigin such that performance.timeOrigin +
  // performance.now() gives a date arbitrarily in the past.
  //
  // Additionally, computing timeOrigin in this way fills the gap for browsers where performance.timeOrigin is
  // undefined.
  //
  // The assumption that performance.timeOrigin + performance.now() ~= Date.now() is flawed, but we depend on it to
  // interact with data coming out of performance entries.
  //
  // Note that despite recommendations against it in the spec, browsers implement the Performance API with a clock that
  // might stop when the computer is asleep (and perhaps under other circumstances). Such behavior causes
  // performance.timeOrigin + performance.now() to have an arbitrary skew over Date.now(). In laptop computers, we have
  // observed skews that can be as long as days, weeks or months.
  //
  // See https://github.com/getsentry/sentry-javascript/issues/2590.
  //
  // BUG: despite our best intentions, this workaround has its limitations. It mostly addresses timings of pageload
  // transactions, but ignores the skew built up over time that can aversely affect timestamps of navigation
  // transactions of long-lived web pages.
  var timeOrigin = Date.now() - performance.now();

  return {
    now: () => performance.now(),
    timeOrigin,
  };
}

/**
 * Returns the native Performance API implementation from Node.js. Returns undefined in old Node.js versions that don't
 * implement the API.
 */
function getNodePerformance() {
  try {
    var perfHooks = Object(_node_js__WEBPACK_IMPORTED_MODULE_1__["dynamicRequire"])(module, 'perf_hooks') ;
    return perfHooks.performance;
  } catch (_) {
    return undefined;
  }
}

/**
 * The Performance API implementation for the current platform, if available.
 */
var platformPerformance = Object(_node_js__WEBPACK_IMPORTED_MODULE_1__["isNodeEnv"])() ? getNodePerformance() : getBrowserPerformance();

var timestampSource =
  platformPerformance === undefined
    ? dateTimestampSource
    : {
        nowSeconds: () => (platformPerformance.timeOrigin + platformPerformance.now()) / 1000,
      };

/**
 * Returns a timestamp in seconds since the UNIX epoch using the Date API.
 */
var dateTimestampInSeconds = dateTimestampSource.nowSeconds.bind(dateTimestampSource);

/**
 * Returns a timestamp in seconds since the UNIX epoch using either the Performance or Date APIs, depending on the
 * availability of the Performance API.
 *
 * See `usingPerformanceAPI` to test whether the Performance API is used.
 *
 * BUG: Note that because of how browsers implement the Performance API, the clock might stop when the computer is
 * asleep. This creates a skew between `dateTimestampInSeconds` and `timestampInSeconds`. The
 * skew can grow to arbitrary amounts like days, weeks or months.
 * See https://github.com/getsentry/sentry-javascript/issues/2590.
 */
var timestampInSeconds = timestampSource.nowSeconds.bind(timestampSource);

// Re-exported with an old name for backwards-compatibility.
var timestampWithMs = timestampInSeconds;

/**
 * A boolean that is true when timestampInSeconds uses the Performance API to produce monotonic timestamps.
 */
var usingPerformanceAPI = platformPerformance !== undefined;

/**
 * Internal helper to store what is the source of browserPerformanceTimeOrigin below. For debugging only.
 */
let _browserPerformanceTimeOriginMode;

/**
 * The number of milliseconds since the UNIX epoch. This value is only usable in a browser, and only when the
 * performance API is available.
 */
var browserPerformanceTimeOrigin = (() => {
  // Unfortunately browsers may report an inaccurate time origin data, through either performance.timeOrigin or
  // performance.timing.navigationStart, which results in poor results in performance data. We only treat time origin
  // data as reliable if they are within a reasonable threshold of the current time.

  const { performance } = Object(_global_js__WEBPACK_IMPORTED_MODULE_0__["getGlobalObject"])();
  if (!performance || !performance.now) {
    _browserPerformanceTimeOriginMode = 'none';
    return undefined;
  }

  var threshold = 3600 * 1000;
  var performanceNow = performance.now();
  var dateNow = Date.now();

  // if timeOrigin isn't available set delta to threshold so it isn't used
  var timeOriginDelta = performance.timeOrigin
    ? Math.abs(performance.timeOrigin + performanceNow - dateNow)
    : threshold;
  var timeOriginIsReliable = timeOriginDelta < threshold;

  // While performance.timing.navigationStart is deprecated in favor of performance.timeOrigin, performance.timeOrigin
  // is not as widely supported. Namely, performance.timeOrigin is undefined in Safari as of writing.
  // Also as of writing, performance.timing is not available in Web Workers in mainstream browsers, so it is not always
  // a valid fallback. In the absence of an initial time provided by the browser, fallback to the current time from the
  // Date API.
    var navigationStart = performance.timing && performance.timing.navigationStart;
  var hasNavigationStart = typeof navigationStart === 'number';
  // if navigationStart isn't available set delta to threshold so it isn't used
  var navigationStartDelta = hasNavigationStart ? Math.abs(navigationStart + performanceNow - dateNow) : threshold;
  var navigationStartIsReliable = navigationStartDelta < threshold;

  if (timeOriginIsReliable || navigationStartIsReliable) {
    // Use the more reliable time origin
    if (timeOriginDelta <= navigationStartDelta) {
      _browserPerformanceTimeOriginMode = 'timeOrigin';
      return performance.timeOrigin;
    } else {
      _browserPerformanceTimeOriginMode = 'navigationStart';
      return navigationStart;
    }
  }

  // Either both timeOrigin and navigationStart are skewed or neither is available, fallback to Date.
  _browserPerformanceTimeOriginMode = 'dateNow';
  return dateNow;
})();


//# sourceMappingURL=time.js.map

/* WEBPACK VAR INJECTION */}.call(this, __webpack_require__(87)(module)))

/***/ }),
/* 121 */
/***/ (function(module, __webpack_exports__, __webpack_require__) {

"use strict";
__webpack_require__.r(__webpack_exports__);
/* harmony export (binding) */ __webpack_require__.d(__webpack_exports__, "TRACEPARENT_REGEXP", function() { return TRACEPARENT_REGEXP; });
/* harmony export (binding) */ __webpack_require__.d(__webpack_exports__, "extractTraceparentData", function() { return extractTraceparentData; });
var TRACEPARENT_REGEXP = new RegExp(
  '^[ \\t]*' + // whitespace
    '([0-9a-f]{32})?' + // trace_id
    '-?([0-9a-f]{16})?' + // span_id
    '-?([01])?' + // sampled
    '[ \\t]*$', // whitespace
);

/**
 * Extract transaction context data from a `sentry-trace` header.
 *
 * @param traceparent Traceparent string
 *
 * @returns Object containing data from the header, or undefined if traceparent string is malformed
 */
function extractTraceparentData(traceparent) {
  var matches = traceparent.match(TRACEPARENT_REGEXP);
  if (matches) {
    let parentSampled;
    if (matches[3] === '1') {
      parentSampled = true;
    } else if (matches[3] === '0') {
      parentSampled = false;
    }
    return {
      traceId: matches[1],
      parentSampled,
      parentSpanId: matches[2],
    };
  }
  return undefined;
}


//# sourceMappingURL=tracing.js.map


/***/ }),
/* 122 */
/***/ (function(module, __webpack_exports__, __webpack_require__) {

"use strict";
__webpack_require__.r(__webpack_exports__);
/* harmony export (binding) */ __webpack_require__.d(__webpack_exports__, "addItemToEnvelope", function() { return addItemToEnvelope; });
/* harmony export (binding) */ __webpack_require__.d(__webpack_exports__, "createAttachmentEnvelopeItem", function() { return createAttachmentEnvelopeItem; });
/* harmony export (binding) */ __webpack_require__.d(__webpack_exports__, "createEnvelope", function() { return createEnvelope; });
/* harmony export (binding) */ __webpack_require__.d(__webpack_exports__, "envelopeItemTypeToDataCategory", function() { return envelopeItemTypeToDataCategory; });
/* harmony export (binding) */ __webpack_require__.d(__webpack_exports__, "forEachEnvelopeItem", function() { return forEachEnvelopeItem; });
/* harmony export (binding) */ __webpack_require__.d(__webpack_exports__, "serializeEnvelope", function() { return serializeEnvelope; });
/* harmony import */ var _object_js__WEBPACK_IMPORTED_MODULE_0__ = __webpack_require__(94);


/**
 * Creates an envelope.
 * Make sure to always explicitly provide the generic to this function
 * so that the envelope types resolve correctly.
 */
function createEnvelope(headers, items = []) {
  return [headers, items] ;
}

/**
 * Add an item to an envelope.
 * Make sure to always explicitly provide the generic to this function
 * so that the envelope types resolve correctly.
 */
function addItemToEnvelope(envelope, newItem) {
  const [headers, items] = envelope;
  return [headers, [...items, newItem]] ;
}

/**
 * Convenience function to loop through the items and item types of an envelope.
 * (This function was mostly created because working with envelope types is painful at the moment)
 */
function forEachEnvelopeItem(
  envelope,
  callback,
) {
  var envelopeItems = envelope[1];
  envelopeItems.forEach((envelopeItem) => {
    var envelopeItemType = envelopeItem[0].type;
    callback(envelopeItem, envelopeItemType);
  });
}

function encodeUTF8(input, textEncoder) {
  var utf8 = textEncoder || new TextEncoder();
  return utf8.encode(input);
}

/**
 * Serializes an envelope.
 */
function serializeEnvelope(envelope, textEncoder) {
  const [envHeaders, items] = envelope;

  // Initially we construct our envelope as a string and only convert to binary chunks if we encounter binary data
  let parts = JSON.stringify(envHeaders);

  function append(next) {
    if (typeof parts === 'string') {
      parts = typeof next === 'string' ? parts + next : [encodeUTF8(parts, textEncoder), next];
    } else {
      parts.push(typeof next === 'string' ? encodeUTF8(next, textEncoder) : next);
    }
  }

  for (var item of items) {
    const [itemHeaders, payload] = item ;
    append(`\n${JSON.stringify(itemHeaders)}\n`);
    append(typeof payload === 'string' || payload instanceof Uint8Array ? payload : JSON.stringify(payload));
  }

  return typeof parts === 'string' ? parts : concatBuffers(parts);
}

function concatBuffers(buffers) {
  var totalLength = buffers.reduce((acc, buf) => acc + buf.length, 0);

  var merged = new Uint8Array(totalLength);
  let offset = 0;
  for (var buffer of buffers) {
    merged.set(buffer, offset);
    offset += buffer.length;
  }

  return merged;
}

/**
 * Creates attachment envelope items
 */
function createAttachmentEnvelopeItem(
  attachment,
  textEncoder,
) {
  var buffer = typeof attachment.data === 'string' ? encodeUTF8(attachment.data, textEncoder) : attachment.data;

  return [
    Object(_object_js__WEBPACK_IMPORTED_MODULE_0__["dropUndefinedKeys"])({
      type: 'attachment',
      length: buffer.length,
      filename: attachment.filename,
      content_type: attachment.contentType,
      attachment_type: attachment.attachmentType,
    }),
    buffer,
  ];
}

var ITEM_TYPE_TO_DATA_CATEGORY_MAP = {
  session: 'session',
  sessions: 'session',
  attachment: 'attachment',
  transaction: 'transaction',
  event: 'error',
  client_report: 'internal',
  user_report: 'default',
};

/**
 * Maps the type of an envelope item to a data category.
 */
function envelopeItemTypeToDataCategory(type) {
  return ITEM_TYPE_TO_DATA_CATEGORY_MAP[type];
}


//# sourceMappingURL=envelope.js.map


/***/ }),
/* 123 */
/***/ (function(module, __webpack_exports__, __webpack_require__) {

"use strict";
__webpack_require__.r(__webpack_exports__);
/* harmony export (binding) */ __webpack_require__.d(__webpack_exports__, "createClientReportEnvelope", function() { return createClientReportEnvelope; });
/* harmony import */ var _envelope_js__WEBPACK_IMPORTED_MODULE_0__ = __webpack_require__(122);
/* harmony import */ var _time_js__WEBPACK_IMPORTED_MODULE_1__ = __webpack_require__(120);



/**
 * Creates client report envelope
 * @param discarded_events An array of discard events
 * @param dsn A DSN that can be set on the header. Optional.
 */
function createClientReportEnvelope(
  discarded_events,
  dsn,
  timestamp,
) {
  var clientReportItem = [
    { type: 'client_report' },
    {
      timestamp: timestamp || Object(_time_js__WEBPACK_IMPORTED_MODULE_1__["dateTimestampInSeconds"])(),
      discarded_events,
    },
  ];
  return Object(_envelope_js__WEBPACK_IMPORTED_MODULE_0__["createEnvelope"])(dsn ? { dsn } : {}, [clientReportItem]);
}


//# sourceMappingURL=clientreport.js.map


/***/ }),
/* 124 */
/***/ (function(module, __webpack_exports__, __webpack_require__) {

"use strict";
__webpack_require__.r(__webpack_exports__);
/* harmony export (binding) */ __webpack_require__.d(__webpack_exports__, "DEFAULT_RETRY_AFTER", function() { return DEFAULT_RETRY_AFTER; });
/* harmony export (binding) */ __webpack_require__.d(__webpack_exports__, "disabledUntil", function() { return disabledUntil; });
/* harmony export (binding) */ __webpack_require__.d(__webpack_exports__, "isRateLimited", function() { return isRateLimited; });
/* harmony export (binding) */ __webpack_require__.d(__webpack_exports__, "parseRetryAfterHeader", function() { return parseRetryAfterHeader; });
/* harmony export (binding) */ __webpack_require__.d(__webpack_exports__, "updateRateLimits", function() { return updateRateLimits; });
// Intentionally keeping the key broad, as we don't know for sure what rate limit headers get returned from backend

var DEFAULT_RETRY_AFTER = 60 * 1000; // 60 seconds

/**
 * Extracts Retry-After value from the request header or returns default value
 * @param header string representation of 'Retry-After' header
 * @param now current unix timestamp
 *
 */
function parseRetryAfterHeader(header, now = Date.now()) {
  var headerDelay = parseInt(`${header}`, 10);
  if (!isNaN(headerDelay)) {
    return headerDelay * 1000;
  }

  var headerDate = Date.parse(`${header}`);
  if (!isNaN(headerDate)) {
    return headerDate - now;
  }

  return DEFAULT_RETRY_AFTER;
}

/**
 * Gets the time that given category is disabled until for rate limiting
 */
function disabledUntil(limits, category) {
  return limits[category] || limits.all || 0;
}

/**
 * Checks if a category is rate limited
 */
function isRateLimited(limits, category, now = Date.now()) {
  return disabledUntil(limits, category) > now;
}

/**
 * Update ratelimits from incoming headers.
 * Returns true if headers contains a non-empty rate limiting header.
 */
function updateRateLimits(
  limits,
  { statusCode, headers },
  now = Date.now(),
) {
  var updatedRateLimits = {
    ...limits,
  };

  // "The name is case-insensitive."
  // https://developer.mozilla.org/en-US/docs/Web/API/Headers/get
  var rateLimitHeader = headers && headers['x-sentry-rate-limits'];
  var retryAfterHeader = headers && headers['retry-after'];

  if (rateLimitHeader) {
    /**
     * rate limit headers are of the form
     *     <header>,<header>,..
     * where each <header> is of the form
     *     <retry_after>: <categories>: <scope>: <reason_code>
     * where
     *     <retry_after> is a delay in seconds
     *     <categories> is the event type(s) (error, transaction, etc) being rate limited and is of the form
     *         <category>;<category>;...
     *     <scope> is what's being limited (org, project, or key) - ignored by SDK
     *     <reason_code> is an arbitrary string like "org_quota" - ignored by SDK
     */
    for (var limit of rateLimitHeader.trim().split(',')) {
      const [retryAfter, categories] = limit.split(':', 2);
      var headerDelay = parseInt(retryAfter, 10);
      var delay = (!isNaN(headerDelay) ? headerDelay : 60) * 1000; // 60sec default
      if (!categories) {
        updatedRateLimits.all = now + delay;
      } else {
        for (var category of categories.split(';')) {
          updatedRateLimits[category] = now + delay;
        }
      }
    }
  } else if (retryAfterHeader) {
    updatedRateLimits.all = now + parseRetryAfterHeader(retryAfterHeader, now);
  } else if (statusCode === 429) {
    updatedRateLimits.all = now + 60 * 1000;
  }

  return updatedRateLimits;
}


//# sourceMappingURL=ratelimit.js.map


/***/ }),
/* 125 */
/***/ (function(module, __webpack_exports__, __webpack_require__) {

"use strict";
__webpack_require__.r(__webpack_exports__);
/* harmony export (binding) */ __webpack_require__.d(__webpack_exports__, "BAGGAGE_HEADER_NAME", function() { return BAGGAGE_HEADER_NAME; });
/* harmony export (binding) */ __webpack_require__.d(__webpack_exports__, "MAX_BAGGAGE_STRING_LENGTH", function() { return MAX_BAGGAGE_STRING_LENGTH; });
/* harmony export (binding) */ __webpack_require__.d(__webpack_exports__, "SENTRY_BAGGAGE_KEY_PREFIX", function() { return SENTRY_BAGGAGE_KEY_PREFIX; });
/* harmony export (binding) */ __webpack_require__.d(__webpack_exports__, "SENTRY_BAGGAGE_KEY_PREFIX_REGEX", function() { return SENTRY_BAGGAGE_KEY_PREFIX_REGEX; });
/* harmony export (binding) */ __webpack_require__.d(__webpack_exports__, "createBaggage", function() { return createBaggage; });
/* harmony export (binding) */ __webpack_require__.d(__webpack_exports__, "getBaggageValue", function() { return getBaggageValue; });
/* harmony export (binding) */ __webpack_require__.d(__webpack_exports__, "getSentryBaggageItems", function() { return getSentryBaggageItems; });
/* harmony export (binding) */ __webpack_require__.d(__webpack_exports__, "getThirdPartyBaggage", function() { return getThirdPartyBaggage; });
/* harmony export (binding) */ __webpack_require__.d(__webpack_exports__, "isBaggageMutable", function() { return isBaggageMutable; });
/* harmony export (binding) */ __webpack_require__.d(__webpack_exports__, "isSentryBaggageEmpty", function() { return isSentryBaggageEmpty; });
/* harmony export (binding) */ __webpack_require__.d(__webpack_exports__, "mergeAndSerializeBaggage", function() { return mergeAndSerializeBaggage; });
/* harmony export (binding) */ __webpack_require__.d(__webpack_exports__, "parseBaggageHeader", function() { return parseBaggageHeader; });
/* harmony export (binding) */ __webpack_require__.d(__webpack_exports__, "parseBaggageSetMutability", function() { return parseBaggageSetMutability; });
/* harmony export (binding) */ __webpack_require__.d(__webpack_exports__, "serializeBaggage", function() { return serializeBaggage; });
/* harmony export (binding) */ __webpack_require__.d(__webpack_exports__, "setBaggageImmutable", function() { return setBaggageImmutable; });
/* harmony export (binding) */ __webpack_require__.d(__webpack_exports__, "setBaggageValue", function() { return setBaggageValue; });
/* harmony import */ var _is_js__WEBPACK_IMPORTED_MODULE_0__ = __webpack_require__(89);
/* harmony import */ var _logger_js__WEBPACK_IMPORTED_MODULE_1__ = __webpack_require__(93);



var BAGGAGE_HEADER_NAME = 'baggage';

var SENTRY_BAGGAGE_KEY_PREFIX = 'sentry-';

var SENTRY_BAGGAGE_KEY_PREFIX_REGEX = /^sentry-/;

/**
 * Max length of a serialized baggage string
 *
 * https://www.w3.org/TR/baggage/#limits
 */
var MAX_BAGGAGE_STRING_LENGTH = 8192;

/** Create an instance of Baggage */
function createBaggage(initItems, baggageString = '', mutable = true) {
  return [{ ...initItems }, baggageString, mutable];
}

/** Get a value from baggage */
function getBaggageValue(baggage, key) {
  return baggage[0][key];
}

/** Add a value to baggage */
function setBaggageValue(baggage, key, value) {
  if (isBaggageMutable(baggage)) {
    baggage[0][key] = value;
  }
}

/** Check if the Sentry part of the passed baggage (i.e. the first element in the tuple) is empty */
function isSentryBaggageEmpty(baggage) {
  return Object.keys(baggage[0]).length === 0;
}

/** Returns Sentry specific baggage values */
function getSentryBaggageItems(baggage) {
  return baggage[0];
}

/**
 * Returns 3rd party baggage string of @param baggage
 * @param baggage
 */
function getThirdPartyBaggage(baggage) {
  return baggage[1];
}

/**
 * Checks if baggage is mutable
 * @param baggage
 * @returns true if baggage is mutable, else false
 */
function isBaggageMutable(baggage) {
  return baggage[2];
}

/**
 * Sets the passed baggage immutable
 * @param baggage
 */
function setBaggageImmutable(baggage) {
  baggage[2] = false;
}

/** Serialize a baggage object */
function serializeBaggage(baggage) {
  return Object.keys(baggage[0]).reduce((prev, key) => {
    var val = baggage[0][key] ;
    var baggageEntry = `${SENTRY_BAGGAGE_KEY_PREFIX}${encodeURIComponent(key)}=${encodeURIComponent(val)}`;
    var newVal = prev === '' ? baggageEntry : `${prev},${baggageEntry}`;
    if (newVal.length > MAX_BAGGAGE_STRING_LENGTH) {
      (typeof __SENTRY_DEBUG__ === 'undefined' || __SENTRY_DEBUG__) &&
        _logger_js__WEBPACK_IMPORTED_MODULE_1__["logger"].warn(`Not adding key: ${key} with val: ${val} to baggage due to exceeding baggage size limits.`);
      return prev;
    } else {
      return newVal;
    }
  }, baggage[1]);
}

/**
 * Parse a baggage header from a string or a string array and return a Baggage object
 *
 * If @param includeThirdPartyEntries is set to true, third party baggage entries are added to the Baggage object
 * (This is necessary for merging potentially pre-existing baggage headers in outgoing requests with
 * our `sentry-` values)
 */
function parseBaggageHeader(
  inputBaggageValue,
  includeThirdPartyEntries = false,
) {
  // Adding this check here because we got reports of this function failing due to the input value
  // not being a string. This debug log might help us determine what's going on here.
  if ((!Array.isArray(inputBaggageValue) && !Object(_is_js__WEBPACK_IMPORTED_MODULE_0__["isString"])(inputBaggageValue)) || typeof inputBaggageValue === 'number') {
    (typeof __SENTRY_DEBUG__ === 'undefined' || __SENTRY_DEBUG__) &&
      _logger_js__WEBPACK_IMPORTED_MODULE_1__["logger"].warn(
        '[parseBaggageHeader] Received input value of incompatible type: ',
        typeof inputBaggageValue,
        inputBaggageValue,
      );

    // Gonna early-return an empty baggage object so that we don't fail later on
    return createBaggage({}, '');
  }

  var baggageEntries = (Object(_is_js__WEBPACK_IMPORTED_MODULE_0__["isString"])(inputBaggageValue) ? inputBaggageValue : inputBaggageValue.join(','))
    .split(',')
    .map(entry => entry.trim())
    .filter(entry => entry !== '' && (includeThirdPartyEntries || SENTRY_BAGGAGE_KEY_PREFIX_REGEX.test(entry)));

  return baggageEntries.reduce(
    ([baggageObj, baggageString], curr) => {
      const [key, val] = curr.split('=');
      if (SENTRY_BAGGAGE_KEY_PREFIX_REGEX.test(key)) {
        var baggageKey = decodeURIComponent(key.split('-')[1]);
        return [
          {
            ...baggageObj,
            [baggageKey]: decodeURIComponent(val),
          },
          baggageString,
          true,
        ];
      } else {
        return [baggageObj, baggageString === '' ? curr : `${baggageString},${curr}`, true];
      }
    },
    [{}, '', true],
  );
}

/**
 * Merges the baggage header we saved from the incoming request (or meta tag) with
 * a possibly created or modified baggage header by a third party that's been added
 * to the outgoing request header.
 *
 * In case @param headerBaggageString exists, we can safely add the the 3rd party part of @param headerBaggage
 * with our @param incomingBaggage. This is possible because if we modified anything beforehand,
 * it would only affect parts of the sentry baggage (@see Baggage interface).
 *
 * @param incomingBaggage the baggage header of the incoming request that might contain sentry entries
 * @param thirdPartyBaggageHeader possibly existing baggage header string or string[] added from a third
 *        party to the request headers
 *
 * @return a merged and serialized baggage string to be propagated with the outgoing request
 */
function mergeAndSerializeBaggage(incomingBaggage, thirdPartyBaggageHeader) {
  if (!incomingBaggage && !thirdPartyBaggageHeader) {
    return '';
  }

  var headerBaggage = (thirdPartyBaggageHeader && parseBaggageHeader(thirdPartyBaggageHeader, true)) || undefined;
  var thirdPartyHeaderBaggage = headerBaggage && getThirdPartyBaggage(headerBaggage);

  var finalBaggage = createBaggage((incomingBaggage && incomingBaggage[0]) || {}, thirdPartyHeaderBaggage || '');
  return serializeBaggage(finalBaggage);
}

/**
 * Helper function that takes a raw baggage string (if available) and the processed sentry-trace header
 * data (if available), parses the baggage string and creates a Baggage object
 * If there is no baggage string, it will create an empty Baggage object.
 * In a second step, this functions determines if the created Baggage object should be set immutable
 * to prevent mutation of the Sentry data.
 *
 * Extracted this logic to a function because it's duplicated in a lot of places.
 *
 * @param rawBaggageValue
 * @param sentryTraceHeader
 */
function parseBaggageSetMutability(
  rawBaggageValue,
  sentryTraceHeader,
) {
  var baggage = parseBaggageHeader(rawBaggageValue || '');

  // Because we are always creating a Baggage object by calling `parseBaggageHeader` above
  // (either a filled one or an empty one, even if we didn't get a `baggage` header),
  // we only need to check if we have a sentry-trace header or not. As soon as we have it,
  // we set baggage immutable. In case we don't get a sentry-trace header, we can assume that
  // this SDK is the head of the trace and thus we still permit mutation at this time.
  // There is one exception though, which is that we get a baggage-header with `sentry-`
  // items but NO sentry-trace header. In this case we also set the baggage immutable for now
  // but if smoething like this would ever happen, we should revisit this and determine
  // what this would actually mean for the trace (i.e. is this SDK the head?, what happened
  // before that we don't have a sentry-trace header?, etc)
  (sentryTraceHeader || !isSentryBaggageEmpty(baggage)) && setBaggageImmutable(baggage);

  return baggage;
}


//# sourceMappingURL=baggage.js.map


/***/ }),
/* 126 */
/***/ (function(module, __webpack_exports__, __webpack_require__) {

"use strict";
__webpack_require__.r(__webpack_exports__);
/* harmony export (binding) */ __webpack_require__.d(__webpack_exports__, "closeSession", function() { return closeSession; });
/* harmony export (binding) */ __webpack_require__.d(__webpack_exports__, "makeSession", function() { return makeSession; });
/* harmony export (binding) */ __webpack_require__.d(__webpack_exports__, "updateSession", function() { return updateSession; });
/* harmony import */ var _sentry_utils__WEBPACK_IMPORTED_MODULE_0__ = __webpack_require__(82);


/**
 * Creates a new `Session` object by setting certain default parameters. If optional @param context
 * is passed, the passed properties are applied to the session object.
 *
 * @param context (optional) additional properties to be applied to the returned session object
 *
 * @returns a new `Session` object
 */
function makeSession(context) {
  // Both timestamp and started are in seconds since the UNIX epoch.
  var startingTime = Object(_sentry_utils__WEBPACK_IMPORTED_MODULE_0__["timestampInSeconds"])();

  var session = {
    sid: Object(_sentry_utils__WEBPACK_IMPORTED_MODULE_0__["uuid4"])(),
    init: true,
    timestamp: startingTime,
    started: startingTime,
    duration: 0,
    status: 'ok',
    errors: 0,
    ignoreDuration: false,
    toJSON: () => sessionToJSON(session),
  };

  if (context) {
    updateSession(session, context);
  }

  return session;
}

/**
 * Updates a session object with the properties passed in the context.
 *
 * Note that this function mutates the passed object and returns void.
 * (Had to do this instead of returning a new and updated session because closing and sending a session
 * makes an update to the session after it was passed to the sending logic.
 * @see BaseClient.captureSession )
 *
 * @param session the `Session` to update
 * @param context the `SessionContext` holding the properties that should be updated in @param session
 */
function updateSession(session, context = {}) {
  if (context.user) {
    if (!session.ipAddress && context.user.ip_address) {
      session.ipAddress = context.user.ip_address;
    }

    if (!session.did && !context.did) {
      session.did = context.user.id || context.user.email || context.user.username;
    }
  }

  session.timestamp = context.timestamp || Object(_sentry_utils__WEBPACK_IMPORTED_MODULE_0__["timestampInSeconds"])();

  if (context.ignoreDuration) {
    session.ignoreDuration = context.ignoreDuration;
  }
  if (context.sid) {
    // Good enough uuid validation. — Kamil
    session.sid = context.sid.length === 32 ? context.sid : Object(_sentry_utils__WEBPACK_IMPORTED_MODULE_0__["uuid4"])();
  }
  if (context.init !== undefined) {
    session.init = context.init;
  }
  if (!session.did && context.did) {
    session.did = `${context.did}`;
  }
  if (typeof context.started === 'number') {
    session.started = context.started;
  }
  if (session.ignoreDuration) {
    session.duration = undefined;
  } else if (typeof context.duration === 'number') {
    session.duration = context.duration;
  } else {
    var duration = session.timestamp - session.started;
    session.duration = duration >= 0 ? duration : 0;
  }
  if (context.release) {
    session.release = context.release;
  }
  if (context.environment) {
    session.environment = context.environment;
  }
  if (!session.ipAddress && context.ipAddress) {
    session.ipAddress = context.ipAddress;
  }
  if (!session.userAgent && context.userAgent) {
    session.userAgent = context.userAgent;
  }
  if (typeof context.errors === 'number') {
    session.errors = context.errors;
  }
  if (context.status) {
    session.status = context.status;
  }
}

/**
 * Closes a session by setting its status and updating the session object with it.
 * Internally calls `updateSession` to update the passed session object.
 *
 * Note that this function mutates the passed session (@see updateSession for explanation).
 *
 * @param session the `Session` object to be closed
 * @param status the `SessionStatus` with which the session was closed. If you don't pass a status,
 *               this function will keep the previously set status, unless it was `'ok'` in which case
 *               it is changed to `'exited'`.
 */
function closeSession(session, status) {
  let context = {};
  if (status) {
    context = { status };
  } else if (session.status === 'ok') {
    context = { status: 'exited' };
  }

  updateSession(session, context);
}

/**
 * Serializes a passed session object to a JSON object with a slightly different structure.
 * This is necessary because the Sentry backend requires a slightly different schema of a session
 * than the one the JS SDKs use internally.
 *
 * @param session the session to be converted
 *
 * @returns a JSON object of the passed session
 */
function sessionToJSON(session) {
  return Object(_sentry_utils__WEBPACK_IMPORTED_MODULE_0__["dropUndefinedKeys"])({
    sid: `${session.sid}`,
    init: session.init,
    // Make sure that sec is converted to ms for date constructor
    started: new Date(session.started * 1000).toISOString(),
    timestamp: new Date(session.timestamp * 1000).toISOString(),
    status: session.status,
    errors: session.errors,
    did: typeof session.did === 'number' || typeof session.did === 'string' ? `${session.did}` : undefined,
    duration: session.duration,
    attrs: {
      release: session.release,
      environment: session.environment,
      ip_address: session.ipAddress,
      user_agent: session.userAgent,
    },
  });
}


//# sourceMappingURL=session.js.map


/***/ }),
/* 127 */
/***/ (function(module, __webpack_exports__, __webpack_require__) {

"use strict";
__webpack_require__.r(__webpack_exports__);
/* harmony export (binding) */ __webpack_require__.d(__webpack_exports__, "SessionFlusher", function() { return SessionFlusher; });
/* harmony import */ var _sentry_utils__WEBPACK_IMPORTED_MODULE_0__ = __webpack_require__(82);
/* harmony import */ var _hub_js__WEBPACK_IMPORTED_MODULE_1__ = __webpack_require__(128);



/**
 * @inheritdoc
 */
class SessionFlusher  {
    __init() {this.flushTimeout = 60;}
   __init2() {this._pendingAggregates = {};}
  
  
   __init3() {this._isEnabled = true;}
  

   constructor(client, attrs) {;SessionFlusher.prototype.__init.call(this);SessionFlusher.prototype.__init2.call(this);SessionFlusher.prototype.__init3.call(this);
    this._client = client;
    // Call to setInterval, so that flush is called every 60 seconds
    this._intervalId = setInterval(() => this.flush(), this.flushTimeout * 1000);
    this._sessionAttrs = attrs;
  }

  /** Checks if `pendingAggregates` has entries, and if it does flushes them by calling `sendSession` */
   flush() {
    var sessionAggregates = this.getSessionAggregates();
    if (sessionAggregates.aggregates.length === 0) {
      return;
    }
    this._pendingAggregates = {};
    this._client.sendSession(sessionAggregates);
  }

  /** Massages the entries in `pendingAggregates` and returns aggregated sessions */
   getSessionAggregates() {
    var aggregates = Object.keys(this._pendingAggregates).map((key) => {
      return this._pendingAggregates[parseInt(key)];
    });

    var sessionAggregates = {
      attrs: this._sessionAttrs,
      aggregates,
    };
    return Object(_sentry_utils__WEBPACK_IMPORTED_MODULE_0__["dropUndefinedKeys"])(sessionAggregates);
  }

  /** JSDoc */
   close() {
    clearInterval(this._intervalId);
    this._isEnabled = false;
    this.flush();
  }

  /**
   * Wrapper function for _incrementSessionStatusCount that checks if the instance of SessionFlusher is enabled then
   * fetches the session status of the request from `Scope.getRequestSession().status` on the scope and passes them to
   * `_incrementSessionStatusCount` along with the start date
   */
   incrementSessionStatusCount() {
    if (!this._isEnabled) {
      return;
    }
    var scope = Object(_hub_js__WEBPACK_IMPORTED_MODULE_1__["getCurrentHub"])().getScope();
    var requestSession = scope && scope.getRequestSession();

    if (requestSession && requestSession.status) {
      this._incrementSessionStatusCount(requestSession.status, new Date());
      // This is not entirely necessarily but is added as a safe guard to indicate the bounds of a request and so in
      // case captureRequestSession is called more than once to prevent double count
      if (scope) {
        scope.setRequestSession(undefined);
      }
          }
  }

  /**
   * Increments status bucket in pendingAggregates buffer (internal state) corresponding to status of
   * the session received
   */
   _incrementSessionStatusCount(status, date) {
    // Truncate minutes and seconds on Session Started attribute to have one minute bucket keys
    var sessionStartedTrunc = new Date(date).setSeconds(0, 0);
    this._pendingAggregates[sessionStartedTrunc] = this._pendingAggregates[sessionStartedTrunc] || {};

    // corresponds to aggregated sessions in one specific minute bucket
    // for example, {"started":"2021-03-16T08:00:00.000Z","exited":4, "errored": 1}
    var aggregationCounts = this._pendingAggregates[sessionStartedTrunc];
    if (!aggregationCounts.started) {
      aggregationCounts.started = new Date(sessionStartedTrunc).toISOString();
    }

    switch (status) {
      case 'errored':
        aggregationCounts.errored = (aggregationCounts.errored || 0) + 1;
        return aggregationCounts.errored;
      case 'ok':
        aggregationCounts.exited = (aggregationCounts.exited || 0) + 1;
        return aggregationCounts.exited;
      default:
        aggregationCounts.crashed = (aggregationCounts.crashed || 0) + 1;
        return aggregationCounts.crashed;
    }
  }
}


//# sourceMappingURL=sessionflusher.js.map


/***/ }),
/* 128 */
/***/ (function(module, __webpack_exports__, __webpack_require__) {

"use strict";
__webpack_require__.r(__webpack_exports__);
/* harmony export (binding) */ __webpack_require__.d(__webpack_exports__, "API_VERSION", function() { return API_VERSION; });
/* harmony export (binding) */ __webpack_require__.d(__webpack_exports__, "Hub", function() { return Hub; });
/* harmony export (binding) */ __webpack_require__.d(__webpack_exports__, "getCurrentHub", function() { return getCurrentHub; });
/* harmony export (binding) */ __webpack_require__.d(__webpack_exports__, "getHubFromCarrier", function() { return getHubFromCarrier; });
/* harmony export (binding) */ __webpack_require__.d(__webpack_exports__, "getMainCarrier", function() { return getMainCarrier; });
/* harmony export (binding) */ __webpack_require__.d(__webpack_exports__, "makeMain", function() { return makeMain; });
/* harmony export (binding) */ __webpack_require__.d(__webpack_exports__, "setHubOnCarrier", function() { return setHubOnCarrier; });
/* harmony import */ var _sentry_utils__WEBPACK_IMPORTED_MODULE_0__ = __webpack_require__(82);
/* harmony import */ var _scope_js__WEBPACK_IMPORTED_MODULE_1__ = __webpack_require__(81);
/* harmony import */ var _session_js__WEBPACK_IMPORTED_MODULE_2__ = __webpack_require__(126);




/**
 * API compatibility version of this hub.
 *
 * WARNING: This number should only be increased when the global interface
 * changes and new methods are introduced.
 *
 * @hidden
 */
var API_VERSION = 4;

/**
 * Default maximum number of breadcrumbs added to an event. Can be overwritten
 * with {@link Options.maxBreadcrumbs}.
 */
var DEFAULT_BREADCRUMBS = 100;

/**
 * A layer in the process stack.
 * @hidden
 */

/**
 * @inheritDoc
 */
class Hub  {
  /** Is a {@link Layer}[] containing the client and scope */
    __init() {this._stack = [{}];}

  /** Contains the last event id of a captured event.  */
  

  /**
   * Creates a new instance of the hub, will push one {@link Layer} into the
   * internal stack on creation.
   *
   * @param client bound to the hub.
   * @param scope bound to the hub.
   * @param version number, higher number means higher priority.
   */
   constructor(client, scope = new _scope_js__WEBPACK_IMPORTED_MODULE_1__["Scope"](),   _version = API_VERSION) {;this._version = _version;Hub.prototype.__init.call(this);
    this.getStackTop().scope = scope;
    if (client) {
      this.bindClient(client);
    }
  }

  /**
   * @inheritDoc
   */
   isOlderThan(version) {
    return this._version < version;
  }

  /**
   * @inheritDoc
   */
   bindClient(client) {
    var top = this.getStackTop();
    top.client = client;
    if (client && client.setupIntegrations) {
      client.setupIntegrations();
    }
  }

  /**
   * @inheritDoc
   */
   pushScope() {
    // We want to clone the content of prev scope
    var scope = _scope_js__WEBPACK_IMPORTED_MODULE_1__["Scope"].clone(this.getScope());
    this.getStack().push({
      client: this.getClient(),
      scope,
    });
    return scope;
  }

  /**
   * @inheritDoc
   */
   popScope() {
    if (this.getStack().length <= 1) return false;
    return !!this.getStack().pop();
  }

  /**
   * @inheritDoc
   */
   withScope(callback) {
    var scope = this.pushScope();
    try {
      callback(scope);
    } finally {
      this.popScope();
    }
  }

  /**
   * @inheritDoc
   */
   getClient() {
    return this.getStackTop().client ;
  }

  /** Returns the scope of the top stack. */
   getScope() {
    return this.getStackTop().scope;
  }

  /** Returns the scope stack for domains or the process. */
   getStack() {
    return this._stack;
  }

  /** Returns the topmost scope layer in the order domain > local > process. */
   getStackTop() {
    return this._stack[this._stack.length - 1];
  }

  /**
   * @inheritDoc
   */
     captureException(exception, hint) {
    var eventId = (this._lastEventId = hint && hint.event_id ? hint.event_id : Object(_sentry_utils__WEBPACK_IMPORTED_MODULE_0__["uuid4"])());
    var syntheticException = new Error('Sentry syntheticException');
    this._withClient((client, scope) => {
      client.captureException(
        exception,
        {
          originalException: exception,
          syntheticException,
          ...hint,
          event_id: eventId,
        },
        scope,
      );
    });
    return eventId;
  }

  /**
   * @inheritDoc
   */
   captureMessage(
    message,
        level,
    hint,
  ) {
    var eventId = (this._lastEventId = hint && hint.event_id ? hint.event_id : Object(_sentry_utils__WEBPACK_IMPORTED_MODULE_0__["uuid4"])());
    var syntheticException = new Error(message);
    this._withClient((client, scope) => {
      client.captureMessage(
        message,
        level,
        {
          originalException: message,
          syntheticException,
          ...hint,
          event_id: eventId,
        },
        scope,
      );
    });
    return eventId;
  }

  /**
   * @inheritDoc
   */
   captureEvent(event, hint) {
    var eventId = hint && hint.event_id ? hint.event_id : Object(_sentry_utils__WEBPACK_IMPORTED_MODULE_0__["uuid4"])();
    if (event.type !== 'transaction') {
      this._lastEventId = eventId;
    }

    this._withClient((client, scope) => {
      client.captureEvent(event, { ...hint, event_id: eventId }, scope);
    });
    return eventId;
  }

  /**
   * @inheritDoc
   */
   lastEventId() {
    return this._lastEventId;
  }

  /**
   * @inheritDoc
   */
   addBreadcrumb(breadcrumb, hint) {
    const { scope, client } = this.getStackTop();

    if (!scope || !client) return;

        const { beforeBreadcrumb = null, maxBreadcrumbs = DEFAULT_BREADCRUMBS } =
      (client.getOptions && client.getOptions()) || {};

    if (maxBreadcrumbs <= 0) return;

    var timestamp = Object(_sentry_utils__WEBPACK_IMPORTED_MODULE_0__["dateTimestampInSeconds"])();
    var mergedBreadcrumb = { timestamp, ...breadcrumb };
    var finalBreadcrumb = beforeBreadcrumb
      ? (Object(_sentry_utils__WEBPACK_IMPORTED_MODULE_0__["consoleSandbox"])(() => beforeBreadcrumb(mergedBreadcrumb, hint)) )
      : mergedBreadcrumb;

    if (finalBreadcrumb === null) return;

    scope.addBreadcrumb(finalBreadcrumb, maxBreadcrumbs);
  }

  /**
   * @inheritDoc
   */
   setUser(user) {
    var scope = this.getScope();
    if (scope) scope.setUser(user);
  }

  /**
   * @inheritDoc
   */
   setTags(tags) {
    var scope = this.getScope();
    if (scope) scope.setTags(tags);
  }

  /**
   * @inheritDoc
   */
   setExtras(extras) {
    var scope = this.getScope();
    if (scope) scope.setExtras(extras);
  }

  /**
   * @inheritDoc
   */
   setTag(key, value) {
    var scope = this.getScope();
    if (scope) scope.setTag(key, value);
  }

  /**
   * @inheritDoc
   */
   setExtra(key, extra) {
    var scope = this.getScope();
    if (scope) scope.setExtra(key, extra);
  }

  /**
   * @inheritDoc
   */
     setContext(name, context) {
    var scope = this.getScope();
    if (scope) scope.setContext(name, context);
  }

  /**
   * @inheritDoc
   */
   configureScope(callback) {
    const { scope, client } = this.getStackTop();
    if (scope && client) {
      callback(scope);
    }
  }

  /**
   * @inheritDoc
   */
   run(callback) {
    var oldHub = makeMain(this);
    try {
      callback(this);
    } finally {
      makeMain(oldHub);
    }
  }

  /**
   * @inheritDoc
   */
   getIntegration(integration) {
    var client = this.getClient();
    if (!client) return null;
    try {
      return client.getIntegration(integration);
    } catch (_oO) {
      (typeof __SENTRY_DEBUG__ === 'undefined' || __SENTRY_DEBUG__) && _sentry_utils__WEBPACK_IMPORTED_MODULE_0__["logger"].warn(`Cannot retrieve integration ${integration.id} from the current Hub`);
      return null;
    }
  }

  /**
   * @inheritDoc
   */
   startTransaction(context, customSamplingContext) {
    return this._callExtensionMethod('startTransaction', context, customSamplingContext);
  }

  /**
   * @inheritDoc
   */
   traceHeaders() {
    return this._callExtensionMethod('traceHeaders');
  }

  /**
   * @inheritDoc
   */
   captureSession(endSession = false) {
    // both send the update and pull the session from the scope
    if (endSession) {
      return this.endSession();
    }

    // only send the update
    this._sendSessionUpdate();
  }

  /**
   * @inheritDoc
   */
   endSession() {
    var layer = this.getStackTop();
    var scope = layer && layer.scope;
    var session = scope && scope.getSession();
    if (session) {
      Object(_session_js__WEBPACK_IMPORTED_MODULE_2__["closeSession"])(session);
    }
    this._sendSessionUpdate();

    // the session is over; take it off of the scope
    if (scope) {
      scope.setSession();
    }
  }

  /**
   * @inheritDoc
   */
   startSession(context) {
    const { scope, client } = this.getStackTop();
    const { release, environment } = (client && client.getOptions()) || {};

    // Will fetch userAgent if called from browser sdk
    var global = Object(_sentry_utils__WEBPACK_IMPORTED_MODULE_0__["getGlobalObject"])();
    const { userAgent } = global.navigator || {};

    var session = Object(_session_js__WEBPACK_IMPORTED_MODULE_2__["makeSession"])({
      release,
      environment,
      ...(scope && { user: scope.getUser() }),
      ...(userAgent && { userAgent }),
      ...context,
    });

    if (scope) {
      // End existing session if there's one
      var currentSession = scope.getSession && scope.getSession();
      if (currentSession && currentSession.status === 'ok') {
        Object(_session_js__WEBPACK_IMPORTED_MODULE_2__["updateSession"])(currentSession, { status: 'exited' });
      }
      this.endSession();

      // Afterwards we set the new session on the scope
      scope.setSession(session);
    }

    return session;
  }

  /**
   * Returns if default PII should be sent to Sentry and propagated in ourgoing requests
   * when Tracing is used.
   */
   shouldSendDefaultPii() {
    var client = this.getClient();
    var options = client && client.getOptions();
    return Boolean(options && options.sendDefaultPii);
  }

  /**
   * Sends the current Session on the scope
   */
   _sendSessionUpdate() {
    const { scope, client } = this.getStackTop();
    if (!scope) return;

    var session = scope.getSession();
    if (session) {
      if (client && client.captureSession) {
        client.captureSession(session);
      }
    }
  }

  /**
   * Internal helper function to call a method on the top client if it exists.
   *
   * @param method The method to call on the client.
   * @param args Arguments to pass to the client function.
   */
   _withClient(callback) {
    const { scope, client } = this.getStackTop();
    if (client) {
      callback(client, scope);
    }
  }

  /**
   * Calls global extension method and binding current instance to the function call
   */
  // @ts-ignore Function lacks ending return statement and return type does not include 'undefined'. ts(2366)
     _callExtensionMethod(method, ...args) {
    var carrier = getMainCarrier();
    var sentry = carrier.__SENTRY__;
    if (sentry && sentry.extensions && typeof sentry.extensions[method] === 'function') {
      return sentry.extensions[method].apply(this, args);
    }
    (typeof __SENTRY_DEBUG__ === 'undefined' || __SENTRY_DEBUG__) && _sentry_utils__WEBPACK_IMPORTED_MODULE_0__["logger"].warn(`Extension method ${method} couldn't be found, doing nothing.`);
  }
}

/**
 * Returns the global shim registry.
 *
 * FIXME: This function is problematic, because despite always returning a valid Carrier,
 * it has an optional `__SENTRY__` property, which then in turn requires us to always perform an unnecessary check
 * at the call-site. We always access the carrier through this function, so we can guarantee that `__SENTRY__` is there.
 **/
function getMainCarrier() {
  var carrier = Object(_sentry_utils__WEBPACK_IMPORTED_MODULE_0__["getGlobalObject"])();
  carrier.__SENTRY__ = carrier.__SENTRY__ || {
    extensions: {},
    hub: undefined,
  };
  return carrier;
}

/**
 * Replaces the current main hub with the passed one on the global object
 *
 * @returns The old replaced hub
 */
function makeMain(hub) {
  var registry = getMainCarrier();
  var oldHub = getHubFromCarrier(registry);
  setHubOnCarrier(registry, hub);
  return oldHub;
}

/**
 * Returns the default hub instance.
 *
 * If a hub is already registered in the global carrier but this module
 * contains a more recent version, it replaces the registered version.
 * Otherwise, the currently registered hub will be returned.
 */
function getCurrentHub() {
  // Get main carrier (global for every environment)
  var registry = getMainCarrier();

  // If there's no hub, or its an old API, assign a new one
  if (!hasHubOnCarrier(registry) || getHubFromCarrier(registry).isOlderThan(API_VERSION)) {
    setHubOnCarrier(registry, new Hub());
  }

  // Prefer domains over global if they are there (applicable only to Node environment)
  if (Object(_sentry_utils__WEBPACK_IMPORTED_MODULE_0__["isNodeEnv"])()) {
    return getHubFromActiveDomain(registry);
  }
  // Return hub that lives on a global object
  return getHubFromCarrier(registry);
}

/**
 * Try to read the hub from an active domain, and fallback to the registry if one doesn't exist
 * @returns discovered hub
 */
function getHubFromActiveDomain(registry) {
  try {
    var sentry = getMainCarrier().__SENTRY__;
    var activeDomain = sentry && sentry.extensions && sentry.extensions.domain && sentry.extensions.domain.active;

    // If there's no active domain, just return global hub
    if (!activeDomain) {
      return getHubFromCarrier(registry);
    }

    // If there's no hub on current domain, or it's an old API, assign a new one
    if (!hasHubOnCarrier(activeDomain) || getHubFromCarrier(activeDomain).isOlderThan(API_VERSION)) {
      var registryHubTopStack = getHubFromCarrier(registry).getStackTop();
      setHubOnCarrier(activeDomain, new Hub(registryHubTopStack.client, _scope_js__WEBPACK_IMPORTED_MODULE_1__["Scope"].clone(registryHubTopStack.scope)));
    }

    // Return hub that lives on a domain
    return getHubFromCarrier(activeDomain);
  } catch (_Oo) {
    // Return hub that lives on a global object
    return getHubFromCarrier(registry);
  }
}

/**
 * This will tell whether a carrier has a hub on it or not
 * @param carrier object
 */
function hasHubOnCarrier(carrier) {
  return !!(carrier && carrier.__SENTRY__ && carrier.__SENTRY__.hub);
}

/**
 * This will create a new {@link Hub} and add to the passed object on
 * __SENTRY__.hub.
 * @param carrier object
 * @hidden
 */
function getHubFromCarrier(carrier) {
  return Object(_sentry_utils__WEBPACK_IMPORTED_MODULE_0__["getGlobalSingleton"])('hub', () => new Hub(), carrier);
}

/**
 * This will set passed {@link Hub} on the passed object's __SENTRY__.hub attribute
 * @param carrier object
 * @param hub Hub
 * @returns A boolean indicating success or failure
 */
function setHubOnCarrier(carrier, hub) {
  if (!carrier) return false;
  var __SENTRY__ = (carrier.__SENTRY__ = carrier.__SENTRY__ || {});
  __SENTRY__.hub = hub;
  return true;
}


//# sourceMappingURL=hub.js.map


/***/ }),
/* 129 */
/***/ (function(module, __webpack_exports__, __webpack_require__) {

"use strict";
__webpack_require__.r(__webpack_exports__);
/* harmony export (binding) */ __webpack_require__.d(__webpack_exports__, "addBreadcrumb", function() { return addBreadcrumb; });
/* harmony export (binding) */ __webpack_require__.d(__webpack_exports__, "captureEvent", function() { return captureEvent; });
/* harmony export (binding) */ __webpack_require__.d(__webpack_exports__, "captureException", function() { return captureException; });
/* harmony export (binding) */ __webpack_require__.d(__webpack_exports__, "captureMessage", function() { return captureMessage; });
/* harmony export (binding) */ __webpack_require__.d(__webpack_exports__, "configureScope", function() { return configureScope; });
/* harmony export (binding) */ __webpack_require__.d(__webpack_exports__, "setContext", function() { return setContext; });
/* harmony export (binding) */ __webpack_require__.d(__webpack_exports__, "setExtra", function() { return setExtra; });
/* harmony export (binding) */ __webpack_require__.d(__webpack_exports__, "setExtras", function() { return setExtras; });
/* harmony export (binding) */ __webpack_require__.d(__webpack_exports__, "setTag", function() { return setTag; });
/* harmony export (binding) */ __webpack_require__.d(__webpack_exports__, "setTags", function() { return setTags; });
/* harmony export (binding) */ __webpack_require__.d(__webpack_exports__, "setUser", function() { return setUser; });
/* harmony export (binding) */ __webpack_require__.d(__webpack_exports__, "startTransaction", function() { return startTransaction; });
/* harmony export (binding) */ __webpack_require__.d(__webpack_exports__, "withScope", function() { return withScope; });
/* harmony import */ var _hub_js__WEBPACK_IMPORTED_MODULE_0__ = __webpack_require__(128);


// Note: All functions in this file are typed with a return value of `ReturnType<Hub[HUB_FUNCTION]>`,
// where HUB_FUNCTION is some method on the Hub class.
//
// This is done to make sure the top level SDK methods stay in sync with the hub methods.
// Although every method here has an explicit return type, some of them (that map to void returns) do not
// contain `return` keywords. This is done to save on bundle size, as `return` is not minifiable.

/**
 * Captures an exception event and sends it to Sentry.
 *
 * @param exception An exception-like object.
 * @param captureContext Additional scope data to apply to exception event.
 * @returns The generated eventId.
 */
function captureException(exception, captureContext) {
  return Object(_hub_js__WEBPACK_IMPORTED_MODULE_0__["getCurrentHub"])().captureException(exception, { captureContext });
}

/**
 * Captures a message event and sends it to Sentry.
 *
 * @param message The message to send to Sentry.
 * @param Severity Define the level of the message.
 * @returns The generated eventId.
 */
function captureMessage(
  message,
    captureContext,
) {
  // This is necessary to provide explicit scopes upgrade, without changing the original
  // arity of the `captureMessage(message, level)` method.
  var level = typeof captureContext === 'string' ? captureContext : undefined;
  var context = typeof captureContext !== 'string' ? { captureContext } : undefined;
  return Object(_hub_js__WEBPACK_IMPORTED_MODULE_0__["getCurrentHub"])().captureMessage(message, level, context);
}

/**
 * Captures a manually created event and sends it to Sentry.
 *
 * @param event The event to send to Sentry.
 * @returns The generated eventId.
 */
function captureEvent(event, hint) {
  return Object(_hub_js__WEBPACK_IMPORTED_MODULE_0__["getCurrentHub"])().captureEvent(event, hint);
}

/**
 * Callback to set context information onto the scope.
 * @param callback Callback function that receives Scope.
 */
function configureScope(callback) {
  Object(_hub_js__WEBPACK_IMPORTED_MODULE_0__["getCurrentHub"])().configureScope(callback);
}

/**
 * Records a new breadcrumb which will be attached to future events.
 *
 * Breadcrumbs will be added to subsequent events to provide more context on
 * user's actions prior to an error or crash.
 *
 * @param breadcrumb The breadcrumb to record.
 */
function addBreadcrumb(breadcrumb) {
  Object(_hub_js__WEBPACK_IMPORTED_MODULE_0__["getCurrentHub"])().addBreadcrumb(breadcrumb);
}

/**
 * Sets context data with the given name.
 * @param name of the context
 * @param context Any kind of data. This data will be normalized.
 */
function setContext(name, context) {
  Object(_hub_js__WEBPACK_IMPORTED_MODULE_0__["getCurrentHub"])().setContext(name, context);
}

/**
 * Set an object that will be merged sent as extra data with the event.
 * @param extras Extras object to merge into current context.
 */
function setExtras(extras) {
  Object(_hub_js__WEBPACK_IMPORTED_MODULE_0__["getCurrentHub"])().setExtras(extras);
}

/**
 * Set key:value that will be sent as extra data with the event.
 * @param key String of extra
 * @param extra Any kind of data. This data will be normalized.
 */
function setExtra(key, extra) {
  Object(_hub_js__WEBPACK_IMPORTED_MODULE_0__["getCurrentHub"])().setExtra(key, extra);
}

/**
 * Set an object that will be merged sent as tags data with the event.
 * @param tags Tags context object to merge into current context.
 */
function setTags(tags) {
  Object(_hub_js__WEBPACK_IMPORTED_MODULE_0__["getCurrentHub"])().setTags(tags);
}

/**
 * Set key:value that will be sent as tags data with the event.
 *
 * Can also be used to unset a tag, by passing `undefined`.
 *
 * @param key String key of tag
 * @param value Value of tag
 */
function setTag(key, value) {
  Object(_hub_js__WEBPACK_IMPORTED_MODULE_0__["getCurrentHub"])().setTag(key, value);
}

/**
 * Updates user context information for future events.
 *
 * @param user User context object to be set in the current context. Pass `null` to unset the user.
 */
function setUser(user) {
  Object(_hub_js__WEBPACK_IMPORTED_MODULE_0__["getCurrentHub"])().setUser(user);
}

/**
 * Creates a new scope with and executes the given operation within.
 * The scope is automatically removed once the operation
 * finishes or throws.
 *
 * This is essentially a convenience function for:
 *
 *     pushScope();
 *     callback();
 *     popScope();
 *
 * @param callback that will be enclosed into push/popScope.
 */
function withScope(callback) {
  Object(_hub_js__WEBPACK_IMPORTED_MODULE_0__["getCurrentHub"])().withScope(callback);
}

/**
 * Starts a new `Transaction` and returns it. This is the entry point to manual tracing instrumentation.
 *
 * A tree structure can be built by adding child spans to the transaction, and child spans to other spans. To start a
 * new child span within the transaction or any span, call the respective `.startChild()` method.
 *
 * Every child span must be finished before the transaction is finished, otherwise the unfinished spans are discarded.
 *
 * The transaction must be finished with a call to its `.finish()` method, at which point the transaction with all its
 * finished child spans will be sent to Sentry.
 *
 * @param context Properties of the new `Transaction`.
 * @param customSamplingContext Information given to the transaction sampling function (along with context-dependent
 * default values). See {@link Options.tracesSampler}.
 *
 * @returns The transaction which was just started
 */
function startTransaction(
  context,
  customSamplingContext,
) {
  return Object(_hub_js__WEBPACK_IMPORTED_MODULE_0__["getCurrentHub"])().startTransaction({ ...context }, customSamplingContext);
}


//# sourceMappingURL=exports.js.map


/***/ }),
/* 130 */
/***/ (function(module, __webpack_exports__, __webpack_require__) {

"use strict";
__webpack_require__.r(__webpack_exports__);
/* harmony export (binding) */ __webpack_require__.d(__webpack_exports__, "getEnvelopeEndpointWithUrlEncodedAuth", function() { return getEnvelopeEndpointWithUrlEncodedAuth; });
/* harmony export (binding) */ __webpack_require__.d(__webpack_exports__, "getReportDialogEndpoint", function() { return getReportDialogEndpoint; });
/* harmony import */ var _sentry_utils__WEBPACK_IMPORTED_MODULE_0__ = __webpack_require__(82);


var SENTRY_API_VERSION = '7';

/** Returns the prefix to construct Sentry ingestion API endpoints. */
function getBaseApiEndpoint(dsn) {
  var protocol = dsn.protocol ? `${dsn.protocol}:` : '';
  var port = dsn.port ? `:${dsn.port}` : '';
  return `${protocol}//${dsn.host}${port}${dsn.path ? `/${dsn.path}` : ''}/api/`;
}

/** Returns the ingest API endpoint for target. */
function _getIngestEndpoint(dsn) {
  return `${getBaseApiEndpoint(dsn)}${dsn.projectId}/envelope/`;
}

/** Returns a URL-encoded string with auth config suitable for a query string. */
function _encodedAuth(dsn) {
  return Object(_sentry_utils__WEBPACK_IMPORTED_MODULE_0__["urlEncode"])({
    // We send only the minimum set of required information. See
    // https://github.com/getsentry/sentry-javascript/issues/2572.
    sentry_key: dsn.publicKey,
    sentry_version: SENTRY_API_VERSION,
  });
}

/**
 * Returns the envelope endpoint URL with auth in the query string.
 *
 * Sending auth as part of the query string and not as custom HTTP headers avoids CORS preflight requests.
 */
function getEnvelopeEndpointWithUrlEncodedAuth(dsn, tunnel) {
  return tunnel ? tunnel : `${_getIngestEndpoint(dsn)}?${_encodedAuth(dsn)}`;
}

/** Returns the url to the report dialog endpoint. */
function getReportDialogEndpoint(
  dsnLike,
  dialogOptions

,
) {
  var dsn = Object(_sentry_utils__WEBPACK_IMPORTED_MODULE_0__["makeDsn"])(dsnLike);
  var endpoint = `${getBaseApiEndpoint(dsn)}embed/error-page/`;

  let encodedOptions = `dsn=${Object(_sentry_utils__WEBPACK_IMPORTED_MODULE_0__["dsnToString"])(dsn)}`;
  for (var key in dialogOptions) {
    if (key === 'dsn') {
      continue;
    }

    if (key === 'user') {
      var user = dialogOptions.user;
      if (!user) {
        continue;
      }
      if (user.name) {
        encodedOptions += `&name=${encodeURIComponent(user.name)}`;
      }
      if (user.email) {
        encodedOptions += `&email=${encodeURIComponent(user.email)}`;
      }
    } else {
      encodedOptions += `&${encodeURIComponent(key)}=${encodeURIComponent(dialogOptions[key] )}`;
    }
  }

  return `${endpoint}?${encodedOptions}`;
}


//# sourceMappingURL=api.js.map


/***/ }),
/* 131 */
/***/ (function(module, __webpack_exports__, __webpack_require__) {

"use strict";
__webpack_require__.r(__webpack_exports__);
/* harmony export (binding) */ __webpack_require__.d(__webpack_exports__, "BaseClient", function() { return BaseClient; });
/* harmony import */ var _sentry_hub__WEBPACK_IMPORTED_MODULE_0__ = __webpack_require__(80);
/* harmony import */ var _sentry_utils__WEBPACK_IMPORTED_MODULE_1__ = __webpack_require__(82);
/* harmony import */ var _api_js__WEBPACK_IMPORTED_MODULE_2__ = __webpack_require__(130);
/* harmony import */ var _envelope_js__WEBPACK_IMPORTED_MODULE_3__ = __webpack_require__(132);
/* harmony import */ var _integration_js__WEBPACK_IMPORTED_MODULE_4__ = __webpack_require__(133);






var ALREADY_SEEN_ERROR = "Not capturing exception because it's already been captured.";

/**
 * Base implementation for all JavaScript SDK clients.
 *
 * Call the constructor with the corresponding options
 * specific to the client subclass. To access these options later, use
 * {@link Client.getOptions}.
 *
 * If a Dsn is specified in the options, it will be parsed and stored. Use
 * {@link Client.getDsn} to retrieve the Dsn at any moment. In case the Dsn is
 * invalid, the constructor will throw a {@link SentryException}. Note that
 * without a valid Dsn, the SDK will not send any events to Sentry.
 *
 * Before sending an event, it is passed through
 * {@link BaseClient._prepareEvent} to add SDK information and scope data
 * (breadcrumbs and context). To add more custom information, override this
 * method and extend the resulting prepared event.
 *
 * To issue automatically created events (e.g. via instrumentation), use
 * {@link Client.captureEvent}. It will prepare the event and pass it through
 * the callback lifecycle. To issue auto-breadcrumbs, use
 * {@link Client.addBreadcrumb}.
 *
 * @example
 * class NodeClient extends BaseClient<NodeOptions> {
 *   public constructor(options: NodeOptions) {
 *     super(options);
 *   }
 *
 *   // ...
 * }
 */
class BaseClient {
  /** Options passed to the SDK. */
  

  /** The client Dsn, if specified in options. Without this Dsn, the SDK will be disabled. */
  

  /** Array of set up integrations. */
   __init() {this._integrations = {};}

  /** Indicates whether this client's integrations have been set up. */
   __init2() {this._integrationsInitialized = false;}

  /** Number of calls being processed */
   __init3() {this._numProcessing = 0;}

  /** Holds flushable  */
   __init4() {this._outcomes = {};}

  /**
   * Initializes this client instance.
   *
   * @param options Options for the client.
   */
   constructor(options) {;BaseClient.prototype.__init.call(this);BaseClient.prototype.__init2.call(this);BaseClient.prototype.__init3.call(this);BaseClient.prototype.__init4.call(this);
    this._options = options;
    if (options.dsn) {
      this._dsn = Object(_sentry_utils__WEBPACK_IMPORTED_MODULE_1__["makeDsn"])(options.dsn);
      var url = Object(_api_js__WEBPACK_IMPORTED_MODULE_2__["getEnvelopeEndpointWithUrlEncodedAuth"])(this._dsn, options.tunnel);
      this._transport = options.transport({
        recordDroppedEvent: this.recordDroppedEvent.bind(this),
        ...options.transportOptions,
        url,
      });
    } else {
      (typeof __SENTRY_DEBUG__ === 'undefined' || __SENTRY_DEBUG__) && _sentry_utils__WEBPACK_IMPORTED_MODULE_1__["logger"].warn('No DSN provided, client will not do anything.');
    }
  }

  /**
   * @inheritDoc
   */
     captureException(exception, hint, scope) {
    // ensure we haven't captured this very object before
    if (Object(_sentry_utils__WEBPACK_IMPORTED_MODULE_1__["checkOrSetAlreadyCaught"])(exception)) {
      (typeof __SENTRY_DEBUG__ === 'undefined' || __SENTRY_DEBUG__) && _sentry_utils__WEBPACK_IMPORTED_MODULE_1__["logger"].log(ALREADY_SEEN_ERROR);
      return;
    }

    let eventId = hint && hint.event_id;

    this._process(
      this.eventFromException(exception, hint)
        .then(event => this._captureEvent(event, hint, scope))
        .then(result => {
          eventId = result;
        }),
    );

    return eventId;
  }

  /**
   * @inheritDoc
   */
   captureMessage(
    message,
        level,
    hint,
    scope,
  ) {
    let eventId = hint && hint.event_id;

    var promisedEvent = Object(_sentry_utils__WEBPACK_IMPORTED_MODULE_1__["isPrimitive"])(message)
      ? this.eventFromMessage(String(message), level, hint)
      : this.eventFromException(message, hint);

    this._process(
      promisedEvent
        .then(event => this._captureEvent(event, hint, scope))
        .then(result => {
          eventId = result;
        }),
    );

    return eventId;
  }

  /**
   * @inheritDoc
   */
   captureEvent(event, hint, scope) {
    // ensure we haven't captured this very object before
    if (hint && hint.originalException && Object(_sentry_utils__WEBPACK_IMPORTED_MODULE_1__["checkOrSetAlreadyCaught"])(hint.originalException)) {
      (typeof __SENTRY_DEBUG__ === 'undefined' || __SENTRY_DEBUG__) && _sentry_utils__WEBPACK_IMPORTED_MODULE_1__["logger"].log(ALREADY_SEEN_ERROR);
      return;
    }

    let eventId = hint && hint.event_id;

    this._process(
      this._captureEvent(event, hint, scope).then(result => {
        eventId = result;
      }),
    );

    return eventId;
  }

  /**
   * @inheritDoc
   */
   captureSession(session) {
    if (!this._isEnabled()) {
      (typeof __SENTRY_DEBUG__ === 'undefined' || __SENTRY_DEBUG__) && _sentry_utils__WEBPACK_IMPORTED_MODULE_1__["logger"].warn('SDK not enabled, will not capture session.');
      return;
    }

    if (!(typeof session.release === 'string')) {
      (typeof __SENTRY_DEBUG__ === 'undefined' || __SENTRY_DEBUG__) && _sentry_utils__WEBPACK_IMPORTED_MODULE_1__["logger"].warn('Discarded session because of missing or non-string release');
    } else {
      this.sendSession(session);
      // After sending, we set init false to indicate it's not the first occurrence
      Object(_sentry_hub__WEBPACK_IMPORTED_MODULE_0__["updateSession"])(session, { init: false });
    }
  }

  /**
   * @inheritDoc
   */
   getDsn() {
    return this._dsn;
  }

  /**
   * @inheritDoc
   */
   getOptions() {
    return this._options;
  }

  /**
   * @inheritDoc
   */
   getTransport() {
    return this._transport;
  }

  /**
   * @inheritDoc
   */
   flush(timeout) {
    var transport = this._transport;
    if (transport) {
      return this._isClientDoneProcessing(timeout).then(clientFinished => {
        return transport.flush(timeout).then(transportFlushed => clientFinished && transportFlushed);
      });
    } else {
      return Object(_sentry_utils__WEBPACK_IMPORTED_MODULE_1__["resolvedSyncPromise"])(true);
    }
  }

  /**
   * @inheritDoc
   */
   close(timeout) {
    return this.flush(timeout).then(result => {
      this.getOptions().enabled = false;
      return result;
    });
  }

  /**
   * Sets up the integrations
   */
   setupIntegrations() {
    if (this._isEnabled() && !this._integrationsInitialized) {
      this._integrations = Object(_integration_js__WEBPACK_IMPORTED_MODULE_4__["setupIntegrations"])(this._options.integrations);
      this._integrationsInitialized = true;
    }
  }

  /**
   * Gets an installed integration by its `id`.
   *
   * @returns The installed integration or `undefined` if no integration with that `id` was installed.
   */
   getIntegrationById(integrationId) {
    return this._integrations[integrationId];
  }

  /**
   * @inheritDoc
   */
   getIntegration(integration) {
    try {
      return (this._integrations[integration.id] ) || null;
    } catch (_oO) {
      (typeof __SENTRY_DEBUG__ === 'undefined' || __SENTRY_DEBUG__) && _sentry_utils__WEBPACK_IMPORTED_MODULE_1__["logger"].warn(`Cannot retrieve integration ${integration.id} from the current Client`);
      return null;
    }
  }

  /**
   * @inheritDoc
   */
   sendEvent(event, hint = {}) {
    if (this._dsn) {
      let env = Object(_envelope_js__WEBPACK_IMPORTED_MODULE_3__["createEventEnvelope"])(event, this._dsn, this._options._metadata, this._options.tunnel);

      for (var attachment of hint.attachments || []) {
        env = Object(_sentry_utils__WEBPACK_IMPORTED_MODULE_1__["addItemToEnvelope"])(
          env,
          Object(_sentry_utils__WEBPACK_IMPORTED_MODULE_1__["createAttachmentEnvelopeItem"])(
            attachment,
            this._options.transportOptions && this._options.transportOptions.textEncoder,
          ),
        );
      }

      this._sendEnvelope(env);
    }
  }

  /**
   * @inheritDoc
   */
   sendSession(session) {
    if (this._dsn) {
      var env = Object(_envelope_js__WEBPACK_IMPORTED_MODULE_3__["createSessionEnvelope"])(session, this._dsn, this._options._metadata, this._options.tunnel);
      this._sendEnvelope(env);
    }
  }

  /**
   * @inheritDoc
   */
   recordDroppedEvent(reason, category) {
    if (this._options.sendClientReports) {
      // We want to track each category (error, transaction, session) separately
      // but still keep the distinction between different type of outcomes.
      // We could use nested maps, but it's much easier to read and type this way.
      // A correct type for map-based implementation if we want to go that route
      // would be `Partial<Record<SentryRequestType, Partial<Record<Outcome, number>>>>`
      // With typescript 4.1 we could even use template literal types
      var key = `${reason}:${category}`;
      (typeof __SENTRY_DEBUG__ === 'undefined' || __SENTRY_DEBUG__) && _sentry_utils__WEBPACK_IMPORTED_MODULE_1__["logger"].log(`Adding outcome: "${key}"`);

      // The following works because undefined + 1 === NaN and NaN is falsy
      this._outcomes[key] = this._outcomes[key] + 1 || 1;
    }
  }

  /** Updates existing session based on the provided event */
   _updateSessionFromEvent(session, event) {
    let crashed = false;
    let errored = false;
    var exceptions = event.exception && event.exception.values;

    if (exceptions) {
      errored = true;

      for (var ex of exceptions) {
        var mechanism = ex.mechanism;
        if (mechanism && mechanism.handled === false) {
          crashed = true;
          break;
        }
      }
    }

    // A session is updated and that session update is sent in only one of the two following scenarios:
    // 1. Session with non terminal status and 0 errors + an error occurred -> Will set error count to 1 and send update
    // 2. Session with non terminal status and 1 error + a crash occurred -> Will set status crashed and send update
    var sessionNonTerminal = session.status === 'ok';
    var shouldUpdateAndSend = (sessionNonTerminal && session.errors === 0) || (sessionNonTerminal && crashed);

    if (shouldUpdateAndSend) {
      Object(_sentry_hub__WEBPACK_IMPORTED_MODULE_0__["updateSession"])(session, {
        ...(crashed && { status: 'crashed' }),
        errors: session.errors || Number(errored || crashed),
      });
      this.captureSession(session);
    }
  }

  /**
   * Determine if the client is finished processing. Returns a promise because it will wait `timeout` ms before saying
   * "no" (resolving to `false`) in order to give the client a chance to potentially finish first.
   *
   * @param timeout The time, in ms, after which to resolve to `false` if the client is still busy. Passing `0` (or not
   * passing anything) will make the promise wait as long as it takes for processing to finish before resolving to
   * `true`.
   * @returns A promise which will resolve to `true` if processing is already done or finishes before the timeout, and
   * `false` otherwise
   */
   _isClientDoneProcessing(timeout) {
    return new _sentry_utils__WEBPACK_IMPORTED_MODULE_1__["SyncPromise"](resolve => {
      let ticked = 0;
      var tick = 1;

      var interval = setInterval(() => {
        if (this._numProcessing == 0) {
          clearInterval(interval);
          resolve(true);
        } else {
          ticked += tick;
          if (timeout && ticked >= timeout) {
            clearInterval(interval);
            resolve(false);
          }
        }
      }, tick);
    });
  }

  /** Determines whether this SDK is enabled and a valid Dsn is present. */
   _isEnabled() {
    return this.getOptions().enabled !== false && this._dsn !== undefined;
  }

  /**
   * Adds common information to events.
   *
   * The information includes release and environment from `options`,
   * breadcrumbs and context (extra, tags and user) from the scope.
   *
   * Information that is already present in the event is never overwritten. For
   * nested objects, such as the context, keys are merged.
   *
   * @param event The original event.
   * @param hint May contain additional information about the original exception.
   * @param scope A scope containing event metadata.
   * @returns A new event with more information.
   */
   _prepareEvent(event, hint, scope) {
    const { normalizeDepth = 3, normalizeMaxBreadth = 1000 } = this.getOptions();
    var prepared = {
      ...event,
      event_id: event.event_id || hint.event_id || Object(_sentry_utils__WEBPACK_IMPORTED_MODULE_1__["uuid4"])(),
      timestamp: event.timestamp || Object(_sentry_utils__WEBPACK_IMPORTED_MODULE_1__["dateTimestampInSeconds"])(),
    };

    this._applyClientOptions(prepared);
    this._applyIntegrationsMetadata(prepared);

    // If we have scope given to us, use it as the base for further modifications.
    // This allows us to prevent unnecessary copying of data if `captureContext` is not provided.
    let finalScope = scope;
    if (hint.captureContext) {
      finalScope = _sentry_hub__WEBPACK_IMPORTED_MODULE_0__["Scope"].clone(finalScope).update(hint.captureContext);
    }

    // We prepare the result here with a resolved Event.
    let result = Object(_sentry_utils__WEBPACK_IMPORTED_MODULE_1__["resolvedSyncPromise"])(prepared);

    // This should be the last thing called, since we want that
    // {@link Hub.addEventProcessor} gets the finished prepared event.
    if (finalScope) {
      // Collect attachments from the hint and scope
      var attachments = [...(hint.attachments || []), ...finalScope.getAttachments()];

      if (attachments.length) {
        hint.attachments = attachments;
      }

      // In case we have a hub we reassign it.
      result = finalScope.applyToEvent(prepared, hint);
    }

    return result.then(evt => {
      if (typeof normalizeDepth === 'number' && normalizeDepth > 0) {
        return this._normalizeEvent(evt, normalizeDepth, normalizeMaxBreadth);
      }
      return evt;
    });
  }

  /**
   * Applies `normalize` function on necessary `Event` attributes to make them safe for serialization.
   * Normalized keys:
   * - `breadcrumbs.data`
   * - `user`
   * - `contexts`
   * - `extra`
   * @param event Event
   * @returns Normalized event
   */
   _normalizeEvent(event, depth, maxBreadth) {
    if (!event) {
      return null;
    }

    var normalized = {
      ...event,
      ...(event.breadcrumbs && {
        breadcrumbs: event.breadcrumbs.map(b => ({
          ...b,
          ...(b.data && {
            data: Object(_sentry_utils__WEBPACK_IMPORTED_MODULE_1__["normalize"])(b.data, depth, maxBreadth),
          }),
        })),
      }),
      ...(event.user && {
        user: Object(_sentry_utils__WEBPACK_IMPORTED_MODULE_1__["normalize"])(event.user, depth, maxBreadth),
      }),
      ...(event.contexts && {
        contexts: Object(_sentry_utils__WEBPACK_IMPORTED_MODULE_1__["normalize"])(event.contexts, depth, maxBreadth),
      }),
      ...(event.extra && {
        extra: Object(_sentry_utils__WEBPACK_IMPORTED_MODULE_1__["normalize"])(event.extra, depth, maxBreadth),
      }),
    };

    // event.contexts.trace stores information about a Transaction. Similarly,
    // event.spans[] stores information about child Spans. Given that a
    // Transaction is conceptually a Span, normalization should apply to both
    // Transactions and Spans consistently.
    // For now the decision is to skip normalization of Transactions and Spans,
    // so this block overwrites the normalized event to add back the original
    // Transaction information prior to normalization.
    if (event.contexts && event.contexts.trace && normalized.contexts) {
      normalized.contexts.trace = event.contexts.trace;

      // event.contexts.trace.data may contain circular/dangerous data so we need to normalize it
      if (event.contexts.trace.data) {
        normalized.contexts.trace.data = Object(_sentry_utils__WEBPACK_IMPORTED_MODULE_1__["normalize"])(event.contexts.trace.data, depth, maxBreadth);
      }
    }

    // event.spans[].data may contain circular/dangerous data so we need to normalize it
    if (event.spans) {
      normalized.spans = event.spans.map(span => {
        // We cannot use the spread operator here because `toJSON` on `span` is non-enumerable
        if (span.data) {
          span.data = Object(_sentry_utils__WEBPACK_IMPORTED_MODULE_1__["normalize"])(span.data, depth, maxBreadth);
        }
        return span;
      });
    }

    return normalized;
  }

  /**
   *  Enhances event using the client configuration.
   *  It takes care of all "static" values like environment, release and `dist`,
   *  as well as truncating overly long values.
   * @param event event instance to be enhanced
   */
   _applyClientOptions(event) {
    var options = this.getOptions();
    const { environment, release, dist, maxValueLength = 250 } = options;

    if (!('environment' in event)) {
      event.environment = 'environment' in options ? environment : 'production';
    }

    if (event.release === undefined && release !== undefined) {
      event.release = release;
    }

    if (event.dist === undefined && dist !== undefined) {
      event.dist = dist;
    }

    if (event.message) {
      event.message = Object(_sentry_utils__WEBPACK_IMPORTED_MODULE_1__["truncate"])(event.message, maxValueLength);
    }

    var exception = event.exception && event.exception.values && event.exception.values[0];
    if (exception && exception.value) {
      exception.value = Object(_sentry_utils__WEBPACK_IMPORTED_MODULE_1__["truncate"])(exception.value, maxValueLength);
    }

    var request = event.request;
    if (request && request.url) {
      request.url = Object(_sentry_utils__WEBPACK_IMPORTED_MODULE_1__["truncate"])(request.url, maxValueLength);
    }
  }

  /**
   * This function adds all used integrations to the SDK info in the event.
   * @param event The event that will be filled with all integrations.
   */
   _applyIntegrationsMetadata(event) {
    var integrationsArray = Object.keys(this._integrations);
    if (integrationsArray.length > 0) {
      event.sdk = event.sdk || {};
      event.sdk.integrations = [...(event.sdk.integrations || []), ...integrationsArray];
    }
  }

  /**
   * Processes the event and logs an error in case of rejection
   * @param event
   * @param hint
   * @param scope
   */
   _captureEvent(event, hint = {}, scope) {
    return this._processEvent(event, hint, scope).then(
      finalEvent => {
        return finalEvent.event_id;
      },
      reason => {
        (typeof __SENTRY_DEBUG__ === 'undefined' || __SENTRY_DEBUG__) && _sentry_utils__WEBPACK_IMPORTED_MODULE_1__["logger"].warn(reason);
        return undefined;
      },
    );
  }

  /**
   * Processes an event (either error or message) and sends it to Sentry.
   *
   * This also adds breadcrumbs and context information to the event. However,
   * platform specific meta data (such as the User's IP address) must be added
   * by the SDK implementor.
   *
   *
   * @param event The event to send to Sentry.
   * @param hint May contain additional information about the original exception.
   * @param scope A scope containing event metadata.
   * @returns A SyncPromise that resolves with the event or rejects in case event was/will not be send.
   */
   _processEvent(event, hint, scope) {
    const { beforeSend, sampleRate } = this.getOptions();

    if (!this._isEnabled()) {
      return Object(_sentry_utils__WEBPACK_IMPORTED_MODULE_1__["rejectedSyncPromise"])(new _sentry_utils__WEBPACK_IMPORTED_MODULE_1__["SentryError"]('SDK not enabled, will not capture event.'));
    }

    var isTransaction = event.type === 'transaction';
    // 1.0 === 100% events are sent
    // 0.0 === 0% events are sent
    // Sampling for transaction happens somewhere else
    if (!isTransaction && typeof sampleRate === 'number' && Math.random() > sampleRate) {
      this.recordDroppedEvent('sample_rate', 'error');
      return Object(_sentry_utils__WEBPACK_IMPORTED_MODULE_1__["rejectedSyncPromise"])(
        new _sentry_utils__WEBPACK_IMPORTED_MODULE_1__["SentryError"](
          `Discarding event because it's not included in the random sample (sampling rate = ${sampleRate})`,
        ),
      );
    }

    return this._prepareEvent(event, hint, scope)
      .then(prepared => {
        if (prepared === null) {
          this.recordDroppedEvent('event_processor', event.type || 'error');
          throw new _sentry_utils__WEBPACK_IMPORTED_MODULE_1__["SentryError"]('An event processor returned null, will not send event.');
        }

        var isInternalException = hint.data && (hint.data ).__sentry__ === true;
        if (isInternalException || isTransaction || !beforeSend) {
          return prepared;
        }

        var beforeSendResult = beforeSend(prepared, hint);
        return _ensureBeforeSendRv(beforeSendResult);
      })
      .then(processedEvent => {
        if (processedEvent === null) {
          this.recordDroppedEvent('before_send', event.type || 'error');
          throw new _sentry_utils__WEBPACK_IMPORTED_MODULE_1__["SentryError"]('`beforeSend` returned `null`, will not send event.');
        }

        var session = scope && scope.getSession();
        if (!isTransaction && session) {
          this._updateSessionFromEvent(session, processedEvent);
        }

        this.sendEvent(processedEvent, hint);
        return processedEvent;
      })
      .then(null, reason => {
        if (reason instanceof _sentry_utils__WEBPACK_IMPORTED_MODULE_1__["SentryError"]) {
          throw reason;
        }

        this.captureException(reason, {
          data: {
            __sentry__: true,
          },
          originalException: reason ,
        });
        throw new _sentry_utils__WEBPACK_IMPORTED_MODULE_1__["SentryError"](
          `Event processing pipeline threw an error, original event will not be sent. Details have been sent as a new event.\nReason: ${reason}`,
        );
      });
  }

  /**
   * Occupies the client with processing and event
   */
   _process(promise) {
    this._numProcessing += 1;
    void promise.then(
      value => {
        this._numProcessing -= 1;
        return value;
      },
      reason => {
        this._numProcessing -= 1;
        return reason;
      },
    );
  }

  /**
   * @inheritdoc
   */
   _sendEnvelope(envelope) {
    if (this._transport && this._dsn) {
      this._transport.send(envelope).then(null, reason => {
        (typeof __SENTRY_DEBUG__ === 'undefined' || __SENTRY_DEBUG__) && _sentry_utils__WEBPACK_IMPORTED_MODULE_1__["logger"].error('Error while sending event:', reason);
      });
    } else {
      (typeof __SENTRY_DEBUG__ === 'undefined' || __SENTRY_DEBUG__) && _sentry_utils__WEBPACK_IMPORTED_MODULE_1__["logger"].error('Transport disabled');
    }
  }

  /**
   * Clears outcomes on this client and returns them.
   */
   _clearOutcomes() {
    var outcomes = this._outcomes;
    this._outcomes = {};
    return Object.keys(outcomes).map(key => {
      const [reason, category] = key.split(':') ;
      return {
        reason,
        category,
        quantity: outcomes[key],
      };
    });
  }

  /**
   * @inheritDoc
   */
    

}

/**
 * Verifies that return value of configured `beforeSend` is of expected type.
 */
function _ensureBeforeSendRv(rv) {
  var nullErr = '`beforeSend` method has to return `null` or a valid event.';
  if (Object(_sentry_utils__WEBPACK_IMPORTED_MODULE_1__["isThenable"])(rv)) {
    return rv.then(
      event => {
        if (!(Object(_sentry_utils__WEBPACK_IMPORTED_MODULE_1__["isPlainObject"])(event) || event === null)) {
          throw new _sentry_utils__WEBPACK_IMPORTED_MODULE_1__["SentryError"](nullErr);
        }
        return event;
      },
      e => {
        throw new _sentry_utils__WEBPACK_IMPORTED_MODULE_1__["SentryError"](`beforeSend rejected with ${e}`);
      },
    );
  } else if (!(Object(_sentry_utils__WEBPACK_IMPORTED_MODULE_1__["isPlainObject"])(rv) || rv === null)) {
    throw new _sentry_utils__WEBPACK_IMPORTED_MODULE_1__["SentryError"](nullErr);
  }
  return rv;
}


//# sourceMappingURL=baseclient.js.map


/***/ }),
/* 132 */
/***/ (function(module, __webpack_exports__, __webpack_require__) {

"use strict";
__webpack_require__.r(__webpack_exports__);
/* harmony export (binding) */ __webpack_require__.d(__webpack_exports__, "createEventEnvelope", function() { return createEventEnvelope; });
/* harmony export (binding) */ __webpack_require__.d(__webpack_exports__, "createSessionEnvelope", function() { return createSessionEnvelope; });
/* harmony import */ var _sentry_utils__WEBPACK_IMPORTED_MODULE_0__ = __webpack_require__(82);


/** Extract sdk info from from the API metadata */
function getSdkMetadataForEnvelopeHeader(metadata) {
  if (!metadata || !metadata.sdk) {
    return;
  }
  const { name, version } = metadata.sdk;
  return { name, version };
}

/**
 * Apply SdkInfo (name, version, packages, integrations) to the corresponding event key.
 * Merge with existing data if any.
 **/
function enhanceEventWithSdkInfo(event, sdkInfo) {
  if (!sdkInfo) {
    return event;
  }
  event.sdk = event.sdk || {};
  event.sdk.name = event.sdk.name || sdkInfo.name;
  event.sdk.version = event.sdk.version || sdkInfo.version;
  event.sdk.integrations = [...(event.sdk.integrations || []), ...(sdkInfo.integrations || [])];
  event.sdk.packages = [...(event.sdk.packages || []), ...(sdkInfo.packages || [])];
  return event;
}

/** Creates an envelope from a Session */
function createSessionEnvelope(
  session,
  dsn,
  metadata,
  tunnel,
) {
  var sdkInfo = getSdkMetadataForEnvelopeHeader(metadata);
  var envelopeHeaders = {
    sent_at: new Date().toISOString(),
    ...(sdkInfo && { sdk: sdkInfo }),
    ...(!!tunnel && { dsn: Object(_sentry_utils__WEBPACK_IMPORTED_MODULE_0__["dsnToString"])(dsn) }),
  };

  var envelopeItem =
    'aggregates' in session ? [{ type: 'sessions' }, session] : [{ type: 'session' }, session];

  return Object(_sentry_utils__WEBPACK_IMPORTED_MODULE_0__["createEnvelope"])(envelopeHeaders, [envelopeItem]);
}

/**
 * Create an Envelope from an event.
 */
function createEventEnvelope(
  event,
  dsn,
  metadata,
  tunnel,
) {
  var sdkInfo = getSdkMetadataForEnvelopeHeader(metadata);
  var eventType = event.type || 'event';

  const { transactionSampling } = event.sdkProcessingMetadata || {};
  const { method: samplingMethod, rate: sampleRate } = transactionSampling || {};

  enhanceEventWithSdkInfo(event, metadata && metadata.sdk);

  var envelopeHeaders = createEventEnvelopeHeaders(event, sdkInfo, tunnel, dsn);

  // Prevent this data (which, if it exists, was used in earlier steps in the processing pipeline) from being sent to
  // sentry. (Note: Our use of this property comes and goes with whatever we might be debugging, whatever hacks we may
  // have temporarily added, etc. Even if we don't happen to be using it at some point in the future, let's not get rid
  // of this `delete`, lest we miss putting it back in the next time the property is in use.)
  delete event.sdkProcessingMetadata;

  var eventItem = [
    {
      type: eventType,
      sample_rates: [{ id: samplingMethod, rate: sampleRate }],
    },
    event,
  ];
  return Object(_sentry_utils__WEBPACK_IMPORTED_MODULE_0__["createEnvelope"])(envelopeHeaders, [eventItem]);
}

function createEventEnvelopeHeaders(
  event,
  sdkInfo,
  tunnel,
  dsn,
) {
  var baggage = event.sdkProcessingMetadata && event.sdkProcessingMetadata.baggage;
  var dynamicSamplingContext = baggage && Object(_sentry_utils__WEBPACK_IMPORTED_MODULE_0__["getSentryBaggageItems"])(baggage);

  return {
    event_id: event.event_id ,
    sent_at: new Date().toISOString(),
    ...(sdkInfo && { sdk: sdkInfo }),
    ...(!!tunnel && { dsn: Object(_sentry_utils__WEBPACK_IMPORTED_MODULE_0__["dsnToString"])(dsn) }),
    ...(event.type === 'transaction' &&
      dynamicSamplingContext && {
        trace: Object(_sentry_utils__WEBPACK_IMPORTED_MODULE_0__["dropUndefinedKeys"])({ ...dynamicSamplingContext }) ,
      }),
  };
}


//# sourceMappingURL=envelope.js.map


/***/ }),
/* 133 */
/***/ (function(module, __webpack_exports__, __webpack_require__) {

"use strict";
__webpack_require__.r(__webpack_exports__);
/* harmony export (binding) */ __webpack_require__.d(__webpack_exports__, "getIntegrationsToSetup", function() { return getIntegrationsToSetup; });
/* harmony export (binding) */ __webpack_require__.d(__webpack_exports__, "installedIntegrations", function() { return installedIntegrations; });
/* harmony export (binding) */ __webpack_require__.d(__webpack_exports__, "setupIntegrations", function() { return setupIntegrations; });
/* harmony import */ var _sentry_hub__WEBPACK_IMPORTED_MODULE_0__ = __webpack_require__(80);
/* harmony import */ var _sentry_utils__WEBPACK_IMPORTED_MODULE_1__ = __webpack_require__(82);



var installedIntegrations = [];

/** Map of integrations assigned to a client */

/**
 * @private
 */
function filterDuplicates(integrations) {
  return integrations.reduce((acc, integrations) => {
    if (acc.every(accIntegration => integrations.name !== accIntegration.name)) {
      acc.push(integrations);
    }
    return acc;
  }, [] );
}

/** Gets integration to install */
function getIntegrationsToSetup(options) {
  var defaultIntegrations = (options.defaultIntegrations && [...options.defaultIntegrations]) || [];
  var userIntegrations = options.integrations;

  let integrations = [...filterDuplicates(defaultIntegrations)];

  if (Array.isArray(userIntegrations)) {
    // Filter out integrations that are also included in user options
    integrations = [
      ...integrations.filter(integrations =>
        userIntegrations.every(userIntegration => userIntegration.name !== integrations.name),
      ),
      // And filter out duplicated user options integrations
      ...filterDuplicates(userIntegrations),
    ];
  } else if (typeof userIntegrations === 'function') {
    integrations = userIntegrations(integrations);
    integrations = Array.isArray(integrations) ? integrations : [integrations];
  }

  // Make sure that if present, `Debug` integration will always run last
  var integrationsNames = integrations.map(i => i.name);
  var alwaysLastToRun = 'Debug';
  if (integrationsNames.indexOf(alwaysLastToRun) !== -1) {
    integrations.push(...integrations.splice(integrationsNames.indexOf(alwaysLastToRun), 1));
  }

  return integrations;
}

/**
 * Given a list of integration instances this installs them all. When `withDefaults` is set to `true` then all default
 * integrations are added unless they were already provided before.
 * @param integrations array of integration instances
 * @param withDefault should enable default integrations
 */
function setupIntegrations(integrations) {
  var integrationIndex = {};

  integrations.forEach(integration => {
    integrationIndex[integration.name] = integration;

    if (installedIntegrations.indexOf(integration.name) === -1) {
      integration.setupOnce(_sentry_hub__WEBPACK_IMPORTED_MODULE_0__["addGlobalEventProcessor"], _sentry_hub__WEBPACK_IMPORTED_MODULE_0__["getCurrentHub"]);
      installedIntegrations.push(integration.name);
      (typeof __SENTRY_DEBUG__ === 'undefined' || __SENTRY_DEBUG__) && _sentry_utils__WEBPACK_IMPORTED_MODULE_1__["logger"].log(`Integration installed: ${integration.name}`);
    }
  });

  return integrationIndex;
}


//# sourceMappingURL=integration.js.map


/***/ }),
/* 134 */
/***/ (function(module, __webpack_exports__, __webpack_require__) {

"use strict";
__webpack_require__.r(__webpack_exports__);
/* harmony export (binding) */ __webpack_require__.d(__webpack_exports__, "initAndBind", function() { return initAndBind; });
/* harmony import */ var _sentry_hub__WEBPACK_IMPORTED_MODULE_0__ = __webpack_require__(80);
/* harmony import */ var _sentry_utils__WEBPACK_IMPORTED_MODULE_1__ = __webpack_require__(82);



/** A class object that can instantiate Client objects. */

/**
 * Internal function to create a new SDK client instance. The client is
 * installed and then bound to the current scope.
 *
 * @param clientClass The client class to instantiate.
 * @param options Options to pass to the client.
 */
function initAndBind(
  clientClass,
  options,
) {
  if (options.debug === true) {
    if ((typeof __SENTRY_DEBUG__ === 'undefined' || __SENTRY_DEBUG__)) {
      _sentry_utils__WEBPACK_IMPORTED_MODULE_1__["logger"].enable();
    } else {
      // use `console.warn` rather than `logger.warn` since by non-debug bundles have all `logger.x` statements stripped
            console.warn('[Sentry] Cannot initialize SDK with `debug` option using a non-debug bundle.');
    }
  }
  var hub = Object(_sentry_hub__WEBPACK_IMPORTED_MODULE_0__["getCurrentHub"])();
  var scope = hub.getScope();
  if (scope) {
    scope.update(options.initialScope);
  }

  var client = new clientClass(options);
  hub.bindClient(client);
}


//# sourceMappingURL=sdk.js.map


/***/ }),
/* 135 */
/***/ (function(module, __webpack_exports__, __webpack_require__) {

"use strict";
__webpack_require__.r(__webpack_exports__);
/* harmony export (binding) */ __webpack_require__.d(__webpack_exports__, "DEFAULT_TRANSPORT_BUFFER_SIZE", function() { return DEFAULT_TRANSPORT_BUFFER_SIZE; });
/* harmony export (binding) */ __webpack_require__.d(__webpack_exports__, "createTransport", function() { return createTransport; });
/* harmony import */ var _sentry_utils__WEBPACK_IMPORTED_MODULE_0__ = __webpack_require__(82);


var DEFAULT_TRANSPORT_BUFFER_SIZE = 30;

/**
 * Creates an instance of a Sentry `Transport`
 *
 * @param options
 * @param makeRequest
 */
function createTransport(
  options,
  makeRequest,
  buffer = Object(_sentry_utils__WEBPACK_IMPORTED_MODULE_0__["makePromiseBuffer"])(options.bufferSize || DEFAULT_TRANSPORT_BUFFER_SIZE),
) {
  let rateLimits = {};

  var flush = (timeout) => buffer.drain(timeout);

  function send(envelope) {
    var filteredEnvelopeItems = [];

    // Drop rate limited items from envelope
    Object(_sentry_utils__WEBPACK_IMPORTED_MODULE_0__["forEachEnvelopeItem"])(envelope, (item, type) => {
      var envelopeItemDataCategory = Object(_sentry_utils__WEBPACK_IMPORTED_MODULE_0__["envelopeItemTypeToDataCategory"])(type);
      if (Object(_sentry_utils__WEBPACK_IMPORTED_MODULE_0__["isRateLimited"])(rateLimits, envelopeItemDataCategory)) {
        options.recordDroppedEvent('ratelimit_backoff', envelopeItemDataCategory);
      } else {
        filteredEnvelopeItems.push(item);
      }
    });

    // Skip sending if envelope is empty after filtering out rate limited events
    if (filteredEnvelopeItems.length === 0) {
      return Object(_sentry_utils__WEBPACK_IMPORTED_MODULE_0__["resolvedSyncPromise"])();
    }

        var filteredEnvelope = Object(_sentry_utils__WEBPACK_IMPORTED_MODULE_0__["createEnvelope"])(envelope[0], filteredEnvelopeItems );

    // Creates client report for each item in an envelope
    var recordEnvelopeLoss = (reason) => {
      Object(_sentry_utils__WEBPACK_IMPORTED_MODULE_0__["forEachEnvelopeItem"])(filteredEnvelope, (_, type) => {
        options.recordDroppedEvent(reason, Object(_sentry_utils__WEBPACK_IMPORTED_MODULE_0__["envelopeItemTypeToDataCategory"])(type));
      });
    };

    var requestTask = () =>
      makeRequest({ body: Object(_sentry_utils__WEBPACK_IMPORTED_MODULE_0__["serializeEnvelope"])(filteredEnvelope, options.textEncoder) }).then(
        response => {
          // We don't want to throw on NOK responses, but we want to at least log them
          if (response.statusCode !== undefined && (response.statusCode < 200 || response.statusCode >= 300)) {
            (typeof __SENTRY_DEBUG__ === 'undefined' || __SENTRY_DEBUG__) && _sentry_utils__WEBPACK_IMPORTED_MODULE_0__["logger"].warn(`Sentry responded with status code ${response.statusCode} to sent event.`);
          }

          rateLimits = Object(_sentry_utils__WEBPACK_IMPORTED_MODULE_0__["updateRateLimits"])(rateLimits, response);
        },
        error => {
          (typeof __SENTRY_DEBUG__ === 'undefined' || __SENTRY_DEBUG__) && _sentry_utils__WEBPACK_IMPORTED_MODULE_0__["logger"].error('Failed while sending event:', error);
          recordEnvelopeLoss('network_error');
        },
      );

    return buffer.add(requestTask).then(
      result => result,
      error => {
        if (error instanceof _sentry_utils__WEBPACK_IMPORTED_MODULE_0__["SentryError"]) {
          (typeof __SENTRY_DEBUG__ === 'undefined' || __SENTRY_DEBUG__) && _sentry_utils__WEBPACK_IMPORTED_MODULE_0__["logger"].error('Skipped sending event due to full buffer');
          recordEnvelopeLoss('queue_overflow');
          return Object(_sentry_utils__WEBPACK_IMPORTED_MODULE_0__["resolvedSyncPromise"])();
        } else {
          throw error;
        }
      },
    );
  }

  return {
    send,
    flush,
  };
}


//# sourceMappingURL=base.js.map


/***/ }),
/* 136 */
/***/ (function(module, __webpack_exports__, __webpack_require__) {

"use strict";
__webpack_require__.r(__webpack_exports__);
/* harmony export (binding) */ __webpack_require__.d(__webpack_exports__, "SDK_VERSION", function() { return SDK_VERSION; });
var SDK_VERSION = '7.5.1';


//# sourceMappingURL=version.js.map


/***/ }),
/* 137 */
/***/ (function(module, __webpack_exports__, __webpack_require__) {

"use strict";
__webpack_require__.r(__webpack_exports__);
/* harmony import */ var _functiontostring_js__WEBPACK_IMPORTED_MODULE_0__ = __webpack_require__(138);
/* harmony reexport (safe) */ __webpack_require__.d(__webpack_exports__, "FunctionToString", function() { return _functiontostring_js__WEBPACK_IMPORTED_MODULE_0__["FunctionToString"]; });

/* harmony import */ var _inboundfilters_js__WEBPACK_IMPORTED_MODULE_1__ = __webpack_require__(139);
/* harmony reexport (safe) */ __webpack_require__.d(__webpack_exports__, "InboundFilters", function() { return _inboundfilters_js__WEBPACK_IMPORTED_MODULE_1__["InboundFilters"]; });



//# sourceMappingURL=index.js.map


/***/ }),
/* 138 */
/***/ (function(module, __webpack_exports__, __webpack_require__) {

"use strict";
__webpack_require__.r(__webpack_exports__);
/* harmony export (binding) */ __webpack_require__.d(__webpack_exports__, "FunctionToString", function() { return FunctionToString; });
/* harmony import */ var _sentry_utils__WEBPACK_IMPORTED_MODULE_0__ = __webpack_require__(82);


let originalFunctionToString;

/** Patch toString calls to return proper name for wrapped functions */
class FunctionToString  {constructor() { FunctionToString.prototype.__init.call(this); }
  /**
   * @inheritDoc
   */
   static __initStatic() {this.id = 'FunctionToString';}

  /**
   * @inheritDoc
   */
   __init() {this.name = FunctionToString.id;}

  /**
   * @inheritDoc
   */
   setupOnce() {
        originalFunctionToString = Function.prototype.toString;

        Function.prototype.toString = function ( ...args) {
      var context = Object(_sentry_utils__WEBPACK_IMPORTED_MODULE_0__["getOriginalFunction"])(this) || this;
      return originalFunctionToString.apply(context, args);
    };
  }
} FunctionToString.__initStatic();


//# sourceMappingURL=functiontostring.js.map


/***/ }),
/* 139 */
/***/ (function(module, __webpack_exports__, __webpack_require__) {

"use strict";
__webpack_require__.r(__webpack_exports__);
/* harmony export (binding) */ __webpack_require__.d(__webpack_exports__, "InboundFilters", function() { return InboundFilters; });
/* harmony export (binding) */ __webpack_require__.d(__webpack_exports__, "_mergeOptions", function() { return _mergeOptions; });
/* harmony export (binding) */ __webpack_require__.d(__webpack_exports__, "_shouldDropEvent", function() { return _shouldDropEvent; });
/* harmony import */ var _sentry_utils__WEBPACK_IMPORTED_MODULE_0__ = __webpack_require__(82);


// "Script error." is hard coded into browsers for errors that it can't read.
// this is the result of a script being pulled in from an external domain and CORS.
var DEFAULT_IGNORE_ERRORS = [/^Script error\.?$/, /^Javascript error: Script error\.? on line 0$/];

/** Options for the InboundFilters integration */

/** Inbound filters configurable by the user */
class InboundFilters  {
  /**
   * @inheritDoc
   */
   static __initStatic() {this.id = 'InboundFilters';}

  /**
   * @inheritDoc
   */
   __init() {this.name = InboundFilters.id;}

   constructor(  _options = {}) {;this._options = _options;InboundFilters.prototype.__init.call(this);}

  /**
   * @inheritDoc
   */
   setupOnce(addGlobalEventProcessor, getCurrentHub) {
    var eventProcess = (event) => {
      var hub = getCurrentHub();
      if (hub) {
        var self = hub.getIntegration(InboundFilters);
        if (self) {
          var client = hub.getClient();
          var clientOptions = client ? client.getOptions() : {};
          var options = _mergeOptions(self._options, clientOptions);
          return _shouldDropEvent(event, options) ? null : event;
        }
      }
      return event;
    };

    eventProcess.id = this.name;
    addGlobalEventProcessor(eventProcess);
  }
} InboundFilters.__initStatic();

/** JSDoc */
function _mergeOptions(
  internalOptions = {},
  clientOptions = {},
) {
  return {
    allowUrls: [...(internalOptions.allowUrls || []), ...(clientOptions.allowUrls || [])],
    denyUrls: [...(internalOptions.denyUrls || []), ...(clientOptions.denyUrls || [])],
    ignoreErrors: [
      ...(internalOptions.ignoreErrors || []),
      ...(clientOptions.ignoreErrors || []),
      ...DEFAULT_IGNORE_ERRORS,
    ],
    ignoreInternal: internalOptions.ignoreInternal !== undefined ? internalOptions.ignoreInternal : true,
  };
}

/** JSDoc */
function _shouldDropEvent(event, options) {
  if (options.ignoreInternal && _isSentryError(event)) {
    (typeof __SENTRY_DEBUG__ === 'undefined' || __SENTRY_DEBUG__) &&
      _sentry_utils__WEBPACK_IMPORTED_MODULE_0__["logger"].warn(`Event dropped due to being internal Sentry Error.\nEvent: ${Object(_sentry_utils__WEBPACK_IMPORTED_MODULE_0__["getEventDescription"])(event)}`);
    return true;
  }
  if (_isIgnoredError(event, options.ignoreErrors)) {
    (typeof __SENTRY_DEBUG__ === 'undefined' || __SENTRY_DEBUG__) &&
      _sentry_utils__WEBPACK_IMPORTED_MODULE_0__["logger"].warn(
        `Event dropped due to being matched by \`ignoreErrors\` option.\nEvent: ${Object(_sentry_utils__WEBPACK_IMPORTED_MODULE_0__["getEventDescription"])(event)}`,
      );
    return true;
  }
  if (_isDeniedUrl(event, options.denyUrls)) {
    (typeof __SENTRY_DEBUG__ === 'undefined' || __SENTRY_DEBUG__) &&
      _sentry_utils__WEBPACK_IMPORTED_MODULE_0__["logger"].warn(
        `Event dropped due to being matched by \`denyUrls\` option.\nEvent: ${Object(_sentry_utils__WEBPACK_IMPORTED_MODULE_0__["getEventDescription"])(
          event,
        )}.\nUrl: ${_getEventFilterUrl(event)}`,
      );
    return true;
  }
  if (!_isAllowedUrl(event, options.allowUrls)) {
    (typeof __SENTRY_DEBUG__ === 'undefined' || __SENTRY_DEBUG__) &&
      _sentry_utils__WEBPACK_IMPORTED_MODULE_0__["logger"].warn(
        `Event dropped due to not being matched by \`allowUrls\` option.\nEvent: ${Object(_sentry_utils__WEBPACK_IMPORTED_MODULE_0__["getEventDescription"])(
          event,
        )}.\nUrl: ${_getEventFilterUrl(event)}`,
      );
    return true;
  }
  return false;
}

function _isIgnoredError(event, ignoreErrors) {
  if (!ignoreErrors || !ignoreErrors.length) {
    return false;
  }

  return _getPossibleEventMessages(event).some(message =>
    ignoreErrors.some(pattern => Object(_sentry_utils__WEBPACK_IMPORTED_MODULE_0__["isMatchingPattern"])(message, pattern)),
  );
}

function _isDeniedUrl(event, denyUrls) {
  // TODO: Use Glob instead?
  if (!denyUrls || !denyUrls.length) {
    return false;
  }
  var url = _getEventFilterUrl(event);
  return !url ? false : denyUrls.some(pattern => Object(_sentry_utils__WEBPACK_IMPORTED_MODULE_0__["isMatchingPattern"])(url, pattern));
}

function _isAllowedUrl(event, allowUrls) {
  // TODO: Use Glob instead?
  if (!allowUrls || !allowUrls.length) {
    return true;
  }
  var url = _getEventFilterUrl(event);
  return !url ? true : allowUrls.some(pattern => Object(_sentry_utils__WEBPACK_IMPORTED_MODULE_0__["isMatchingPattern"])(url, pattern));
}

function _getPossibleEventMessages(event) {
  if (event.message) {
    return [event.message];
  }
  if (event.exception) {
    try {
      const { type = '', value = '' } = (event.exception.values && event.exception.values[0]) || {};
      return [`${value}`, `${type}: ${value}`];
    } catch (oO) {
      (typeof __SENTRY_DEBUG__ === 'undefined' || __SENTRY_DEBUG__) && _sentry_utils__WEBPACK_IMPORTED_MODULE_0__["logger"].error(`Cannot extract message for event ${Object(_sentry_utils__WEBPACK_IMPORTED_MODULE_0__["getEventDescription"])(event)}`);
      return [];
    }
  }
  return [];
}

function _isSentryError(event) {
  try {
    // @ts-ignore can't be a sentry error if undefined
        return event.exception.values[0].type === 'SentryError';
  } catch (e) {
    // ignore
  }
  return false;
}

function _getLastValidUrl(frames = []) {
  for (let i = frames.length - 1; i >= 0; i--) {
    var frame = frames[i];

    if (frame && frame.filename !== '<anonymous>' && frame.filename !== '[native code]') {
      return frame.filename || null;
    }
  }

  return null;
}

function _getEventFilterUrl(event) {
  try {
    let frames;
    try {
      // @ts-ignore we only care about frames if the whole thing here is defined
      frames = event.exception.values[0].stacktrace.frames;
    } catch (e) {
      // ignore
    }
    return frames ? _getLastValidUrl(frames) : null;
  } catch (oO) {
    (typeof __SENTRY_DEBUG__ === 'undefined' || __SENTRY_DEBUG__) && _sentry_utils__WEBPACK_IMPORTED_MODULE_0__["logger"].error(`Cannot extract url for event ${Object(_sentry_utils__WEBPACK_IMPORTED_MODULE_0__["getEventDescription"])(event)}`);
    return null;
  }
}


//# sourceMappingURL=inboundfilters.js.map


/***/ }),
/* 140 */
/***/ (function(module, __webpack_exports__, __webpack_require__) {

"use strict";
__webpack_require__.r(__webpack_exports__);
/* harmony export (binding) */ __webpack_require__.d(__webpack_exports__, "BrowserClient", function() { return BrowserClient; });
/* harmony import */ var _sentry_core__WEBPACK_IMPORTED_MODULE_0__ = __webpack_require__(79);
/* harmony import */ var _sentry_utils__WEBPACK_IMPORTED_MODULE_1__ = __webpack_require__(82);
/* harmony import */ var _eventbuilder_js__WEBPACK_IMPORTED_MODULE_2__ = __webpack_require__(141);
/* harmony import */ var _integrations_breadcrumbs_js__WEBPACK_IMPORTED_MODULE_3__ = __webpack_require__(142);
/* harmony import */ var _transports_utils_js__WEBPACK_IMPORTED_MODULE_4__ = __webpack_require__(143);






var globalObject = Object(_sentry_utils__WEBPACK_IMPORTED_MODULE_1__["getGlobalObject"])();

/**
 * The Sentry Browser SDK Client.
 *
 * @see BrowserOptions for documentation on configuration options.
 * @see SentryClient for usage documentation.
 */
class BrowserClient extends _sentry_core__WEBPACK_IMPORTED_MODULE_0__["BaseClient"] {
  /**
   * Creates a new Browser SDK instance.
   *
   * @param options Configuration options for this SDK.
   */
   constructor(options) {
    options._metadata = options._metadata || {};
    options._metadata.sdk = options._metadata.sdk || {
      name: 'sentry.javascript.browser',
      packages: [
        {
          name: 'npm:@sentry/browser',
          version: _sentry_core__WEBPACK_IMPORTED_MODULE_0__["SDK_VERSION"],
        },
      ],
      version: _sentry_core__WEBPACK_IMPORTED_MODULE_0__["SDK_VERSION"],
    };

    super(options);

    if (options.sendClientReports && globalObject.document) {
      globalObject.document.addEventListener('visibilitychange', () => {
        if (globalObject.document.visibilityState === 'hidden') {
          this._flushOutcomes();
        }
      });
    }
  }

  /**
   * @inheritDoc
   */
   eventFromException(exception, hint) {
    return Object(_eventbuilder_js__WEBPACK_IMPORTED_MODULE_2__["eventFromException"])(this._options.stackParser, exception, hint, this._options.attachStacktrace);
  }

  /**
   * @inheritDoc
   */
   eventFromMessage(
    message,
        level = 'info',
    hint,
  ) {
    return Object(_eventbuilder_js__WEBPACK_IMPORTED_MODULE_2__["eventFromMessage"])(this._options.stackParser, message, level, hint, this._options.attachStacktrace);
  }

  /**
   * @inheritDoc
   */
   sendEvent(event, hint) {
    // We only want to add the sentry event breadcrumb when the user has the breadcrumb integration installed and
    // activated its `sentry` option.
    // We also do not want to use the `Breadcrumbs` class here directly, because we do not want it to be included in
    // bundles, if it is not used by the SDK.
    // This all sadly is a bit ugly, but we currently don't have a "pre-send" hook on the integrations so we do it this
    // way for now.
    var breadcrumbIntegration = this.getIntegrationById(_integrations_breadcrumbs_js__WEBPACK_IMPORTED_MODULE_3__["BREADCRUMB_INTEGRATION_ID"]) ;
    if (
      breadcrumbIntegration &&
      // We check for definedness of `options`, even though it is not strictly necessary, because that access to
      // `.sentry` below does not throw, in case users provided their own integration with id "Breadcrumbs" that does
      // not have an`options` field
      breadcrumbIntegration.options &&
      breadcrumbIntegration.options.sentry
    ) {
      Object(_sentry_core__WEBPACK_IMPORTED_MODULE_0__["getCurrentHub"])().addBreadcrumb(
        {
          category: `sentry.${event.type === 'transaction' ? 'transaction' : 'event'}`,
          event_id: event.event_id,
          level: event.level,
          message: Object(_sentry_utils__WEBPACK_IMPORTED_MODULE_1__["getEventDescription"])(event),
        },
        {
          event,
        },
      );
    }

    super.sendEvent(event, hint);
  }

  /**
   * @inheritDoc
   */
   _prepareEvent(event, hint, scope) {
    event.platform = event.platform || 'javascript';
    return super._prepareEvent(event, hint, scope);
  }

  /**
   * Sends client reports as an envelope.
   */
   _flushOutcomes() {
    var outcomes = this._clearOutcomes();

    if (outcomes.length === 0) {
      (typeof __SENTRY_DEBUG__ === 'undefined' || __SENTRY_DEBUG__) && _sentry_utils__WEBPACK_IMPORTED_MODULE_1__["logger"].log('No outcomes to send');
      return;
    }

    if (!this._dsn) {
      (typeof __SENTRY_DEBUG__ === 'undefined' || __SENTRY_DEBUG__) && _sentry_utils__WEBPACK_IMPORTED_MODULE_1__["logger"].log('No dsn provided, will not send outcomes');
      return;
    }

    (typeof __SENTRY_DEBUG__ === 'undefined' || __SENTRY_DEBUG__) && _sentry_utils__WEBPACK_IMPORTED_MODULE_1__["logger"].log('Sending outcomes:', outcomes);

    var url = Object(_sentry_core__WEBPACK_IMPORTED_MODULE_0__["getEnvelopeEndpointWithUrlEncodedAuth"])(this._dsn, this._options.tunnel);
    var envelope = Object(_sentry_utils__WEBPACK_IMPORTED_MODULE_1__["createClientReportEnvelope"])(outcomes, this._options.tunnel && Object(_sentry_utils__WEBPACK_IMPORTED_MODULE_1__["dsnToString"])(this._dsn));

    try {
      Object(_transports_utils_js__WEBPACK_IMPORTED_MODULE_4__["sendReport"])(url, Object(_sentry_utils__WEBPACK_IMPORTED_MODULE_1__["serializeEnvelope"])(envelope));
    } catch (e) {
      (typeof __SENTRY_DEBUG__ === 'undefined' || __SENTRY_DEBUG__) && _sentry_utils__WEBPACK_IMPORTED_MODULE_1__["logger"].error(e);
    }
  }
}


//# sourceMappingURL=client.js.map


/***/ }),
/* 141 */
/***/ (function(module, __webpack_exports__, __webpack_require__) {

"use strict";
__webpack_require__.r(__webpack_exports__);
/* harmony export (binding) */ __webpack_require__.d(__webpack_exports__, "eventFromError", function() { return eventFromError; });
/* harmony export (binding) */ __webpack_require__.d(__webpack_exports__, "eventFromException", function() { return eventFromException; });
/* harmony export (binding) */ __webpack_require__.d(__webpack_exports__, "eventFromMessage", function() { return eventFromMessage; });
/* harmony export (binding) */ __webpack_require__.d(__webpack_exports__, "eventFromPlainObject", function() { return eventFromPlainObject; });
/* harmony export (binding) */ __webpack_require__.d(__webpack_exports__, "eventFromString", function() { return eventFromString; });
/* harmony export (binding) */ __webpack_require__.d(__webpack_exports__, "eventFromUnknownInput", function() { return eventFromUnknownInput; });
/* harmony export (binding) */ __webpack_require__.d(__webpack_exports__, "exceptionFromError", function() { return exceptionFromError; });
/* harmony export (binding) */ __webpack_require__.d(__webpack_exports__, "parseStackFrames", function() { return parseStackFrames; });
/* harmony import */ var _sentry_utils__WEBPACK_IMPORTED_MODULE_0__ = __webpack_require__(82);


/**
 * This function creates an exception from a JavaScript Error
 */
function exceptionFromError(stackParser, ex) {
  // Get the frames first since Opera can lose the stack if we touch anything else first
  var frames = parseStackFrames(stackParser, ex);

  var exception = {
    type: ex && ex.name,
    value: extractMessage(ex),
  };

  if (frames.length) {
    exception.stacktrace = { frames };
  }

  if (exception.type === undefined && exception.value === '') {
    exception.value = 'Unrecoverable error caught';
  }

  return exception;
}

/**
 * @hidden
 */
function eventFromPlainObject(
  stackParser,
  exception,
  syntheticException,
  isUnhandledRejection,
) {
  var event = {
    exception: {
      values: [
        {
          type: Object(_sentry_utils__WEBPACK_IMPORTED_MODULE_0__["isEvent"])(exception) ? exception.constructor.name : isUnhandledRejection ? 'UnhandledRejection' : 'Error',
          value: `Non-Error ${
            isUnhandledRejection ? 'promise rejection' : 'exception'
          } captured with keys: ${Object(_sentry_utils__WEBPACK_IMPORTED_MODULE_0__["extractExceptionKeysForMessage"])(exception)}`,
        },
      ],
    },
    extra: {
      __serialized__: Object(_sentry_utils__WEBPACK_IMPORTED_MODULE_0__["normalizeToSize"])(exception),
    },
  };

  if (syntheticException) {
    var frames = parseStackFrames(stackParser, syntheticException);
    if (frames.length) {
      // event.exception.values[0] has been set above
      (event.exception ).values[0].stacktrace = { frames };
    }
  }

  return event;
}

/**
 * @hidden
 */
function eventFromError(stackParser, ex) {
  return {
    exception: {
      values: [exceptionFromError(stackParser, ex)],
    },
  };
}

/** Parses stack frames from an error */
function parseStackFrames(
  stackParser,
  ex,
) {
  // Access and store the stacktrace property before doing ANYTHING
  // else to it because Opera is not very good at providing it
  // reliably in other circumstances.
  var stacktrace = ex.stacktrace || ex.stack || '';

  var popSize = getPopSize(ex);

  try {
    return stackParser(stacktrace, popSize);
  } catch (e) {
    // no-empty
  }

  return [];
}

// Based on our own mapping pattern - https://github.com/getsentry/sentry/blob/9f08305e09866c8bd6d0c24f5b0aabdd7dd6c59c/src/sentry/lang/javascript/errormapping.py#L83-L108
var reactMinifiedRegexp = /Minified React error #\d+;/i;

function getPopSize(ex) {
  if (ex) {
    if (typeof ex.framesToPop === 'number') {
      return ex.framesToPop;
    }

    if (reactMinifiedRegexp.test(ex.message)) {
      return 1;
    }
  }

  return 0;
}

/**
 * There are cases where stacktrace.message is an Event object
 * https://github.com/getsentry/sentry-javascript/issues/1949
 * In this specific case we try to extract stacktrace.message.error.message
 */
function extractMessage(ex) {
  var message = ex && ex.message;
  if (!message) {
    return 'No error message';
  }
  if (message.error && typeof message.error.message === 'string') {
    return message.error.message;
  }
  return message;
}

/**
 * Creates an {@link Event} from all inputs to `captureException` and non-primitive inputs to `captureMessage`.
 * @hidden
 */
function eventFromException(
  stackParser,
  exception,
  hint,
  attachStacktrace,
) {
  var syntheticException = (hint && hint.syntheticException) || undefined;
  var event = eventFromUnknownInput(stackParser, exception, syntheticException, attachStacktrace);
  Object(_sentry_utils__WEBPACK_IMPORTED_MODULE_0__["addExceptionMechanism"])(event); // defaults to { type: 'generic', handled: true }
  event.level = 'error';
  if (hint && hint.event_id) {
    event.event_id = hint.event_id;
  }
  return Object(_sentry_utils__WEBPACK_IMPORTED_MODULE_0__["resolvedSyncPromise"])(event);
}

/**
 * Builds and Event from a Message
 * @hidden
 */
function eventFromMessage(
  stackParser,
  message,
    level = 'info',
  hint,
  attachStacktrace,
) {
  var syntheticException = (hint && hint.syntheticException) || undefined;
  var event = eventFromString(stackParser, message, syntheticException, attachStacktrace);
  event.level = level;
  if (hint && hint.event_id) {
    event.event_id = hint.event_id;
  }
  return Object(_sentry_utils__WEBPACK_IMPORTED_MODULE_0__["resolvedSyncPromise"])(event);
}

/**
 * @hidden
 */
function eventFromUnknownInput(
  stackParser,
  exception,
  syntheticException,
  attachStacktrace,
  isUnhandledRejection,
) {
  let event;

  if (Object(_sentry_utils__WEBPACK_IMPORTED_MODULE_0__["isErrorEvent"])(exception ) && (exception ).error) {
    // If it is an ErrorEvent with `error` property, extract it to get actual Error
    var errorEvent = exception ;
    return eventFromError(stackParser, errorEvent.error );
  }

  // If it is a `DOMError` (which is a legacy API, but still supported in some browsers) then we just extract the name
  // and message, as it doesn't provide anything else. According to the spec, all `DOMExceptions` should also be
  // `Error`s, but that's not the case in IE11, so in that case we treat it the same as we do a `DOMError`.
  //
  // https://developer.mozilla.org/en-US/docs/Web/API/DOMError
  // https://developer.mozilla.org/en-US/docs/Web/API/DOMException
  // https://webidl.spec.whatwg.org/#es-DOMException-specialness
  if (Object(_sentry_utils__WEBPACK_IMPORTED_MODULE_0__["isDOMError"])(exception ) || Object(_sentry_utils__WEBPACK_IMPORTED_MODULE_0__["isDOMException"])(exception )) {
    var domException = exception ;

    if ('stack' in (exception )) {
      event = eventFromError(stackParser, exception );
    } else {
      var name = domException.name || (Object(_sentry_utils__WEBPACK_IMPORTED_MODULE_0__["isDOMError"])(domException) ? 'DOMError' : 'DOMException');
      var message = domException.message ? `${name}: ${domException.message}` : name;
      event = eventFromString(stackParser, message, syntheticException, attachStacktrace);
      Object(_sentry_utils__WEBPACK_IMPORTED_MODULE_0__["addExceptionTypeValue"])(event, message);
    }
    if ('code' in domException) {
      event.tags = { ...event.tags, 'DOMException.code': `${domException.code}` };
    }

    return event;
  }
  if (Object(_sentry_utils__WEBPACK_IMPORTED_MODULE_0__["isError"])(exception)) {
    // we have a real Error object, do nothing
    return eventFromError(stackParser, exception);
  }
  if (Object(_sentry_utils__WEBPACK_IMPORTED_MODULE_0__["isPlainObject"])(exception) || Object(_sentry_utils__WEBPACK_IMPORTED_MODULE_0__["isEvent"])(exception)) {
    // If it's a plain object or an instance of `Event` (the built-in JS kind, not this SDK's `Event` type), serialize
    // it manually. This will allow us to group events based on top-level keys which is much better than creating a new
    // group on any key/value change.
    var objectException = exception ;
    event = eventFromPlainObject(stackParser, objectException, syntheticException, isUnhandledRejection);
    Object(_sentry_utils__WEBPACK_IMPORTED_MODULE_0__["addExceptionMechanism"])(event, {
      synthetic: true,
    });
    return event;
  }

  // If none of previous checks were valid, then it means that it's not:
  // - an instance of DOMError
  // - an instance of DOMException
  // - an instance of Event
  // - an instance of Error
  // - a valid ErrorEvent (one with an error property)
  // - a plain Object
  //
  // So bail out and capture it as a simple message:
  event = eventFromString(stackParser, exception , syntheticException, attachStacktrace);
  Object(_sentry_utils__WEBPACK_IMPORTED_MODULE_0__["addExceptionTypeValue"])(event, `${exception}`, undefined);
  Object(_sentry_utils__WEBPACK_IMPORTED_MODULE_0__["addExceptionMechanism"])(event, {
    synthetic: true,
  });

  return event;
}

/**
 * @hidden
 */
function eventFromString(
  stackParser,
  input,
  syntheticException,
  attachStacktrace,
) {
  var event = {
    message: input,
  };

  if (attachStacktrace && syntheticException) {
    var frames = parseStackFrames(stackParser, syntheticException);
    if (frames.length) {
      event.exception = {
        values: [{ value: input, stacktrace: { frames } }],
      };
    }
  }

  return event;
}


//# sourceMappingURL=eventbuilder.js.map


/***/ }),
/* 142 */
/***/ (function(module, __webpack_exports__, __webpack_require__) {

"use strict";
__webpack_require__.r(__webpack_exports__);
/* harmony export (binding) */ __webpack_require__.d(__webpack_exports__, "BREADCRUMB_INTEGRATION_ID", function() { return BREADCRUMB_INTEGRATION_ID; });
/* harmony export (binding) */ __webpack_require__.d(__webpack_exports__, "Breadcrumbs", function() { return Breadcrumbs; });
/* harmony import */ var _sentry_core__WEBPACK_IMPORTED_MODULE_0__ = __webpack_require__(79);
/* harmony import */ var _sentry_utils__WEBPACK_IMPORTED_MODULE_1__ = __webpack_require__(82);



/** JSDoc */

var BREADCRUMB_INTEGRATION_ID = 'Breadcrumbs';

/**
 * Default Breadcrumbs instrumentations
 * TODO: Deprecated - with v6, this will be renamed to `Instrument`
 */
class Breadcrumbs  {
  /**
   * @inheritDoc
   */
   static __initStatic() {this.id = BREADCRUMB_INTEGRATION_ID;}

  /**
   * @inheritDoc
   */
   __init() {this.name = Breadcrumbs.id;}

  /**
   * Options of the breadcrumbs integration.
   */
  // This field is public, because we use it in the browser client to check if the `sentry` option is enabled.
  

  /**
   * @inheritDoc
   */
   constructor(options) {;Breadcrumbs.prototype.__init.call(this);
    this.options = {
      console: true,
      dom: true,
      fetch: true,
      history: true,
      sentry: true,
      xhr: true,
      ...options,
    };
  }

  /**
   * Instrument browser built-ins w/ breadcrumb capturing
   *  - Console API
   *  - DOM API (click/typing)
   *  - XMLHttpRequest API
   *  - Fetch API
   *  - History API
   */
   setupOnce() {
    if (this.options.console) {
      Object(_sentry_utils__WEBPACK_IMPORTED_MODULE_1__["addInstrumentationHandler"])('console', _consoleBreadcrumb);
    }
    if (this.options.dom) {
      Object(_sentry_utils__WEBPACK_IMPORTED_MODULE_1__["addInstrumentationHandler"])('dom', _domBreadcrumb(this.options.dom));
    }
    if (this.options.xhr) {
      Object(_sentry_utils__WEBPACK_IMPORTED_MODULE_1__["addInstrumentationHandler"])('xhr', _xhrBreadcrumb);
    }
    if (this.options.fetch) {
      Object(_sentry_utils__WEBPACK_IMPORTED_MODULE_1__["addInstrumentationHandler"])('fetch', _fetchBreadcrumb);
    }
    if (this.options.history) {
      Object(_sentry_utils__WEBPACK_IMPORTED_MODULE_1__["addInstrumentationHandler"])('history', _historyBreadcrumb);
    }
  }
} Breadcrumbs.__initStatic();

/**
 * A HOC that creaes a function that creates breadcrumbs from DOM API calls.
 * This is a HOC so that we get access to dom options in the closure.
 */
function _domBreadcrumb(dom) {
    function _innerDomBreadcrumb(handlerData) {
    let target;
    let keyAttrs = typeof dom === 'object' ? dom.serializeAttribute : undefined;

    if (typeof keyAttrs === 'string') {
      keyAttrs = [keyAttrs];
    }

    // Accessing event.target can throw (see getsentry/raven-js#838, #768)
    try {
      target = handlerData.event.target
        ? Object(_sentry_utils__WEBPACK_IMPORTED_MODULE_1__["htmlTreeAsString"])(handlerData.event.target , keyAttrs)
        : Object(_sentry_utils__WEBPACK_IMPORTED_MODULE_1__["htmlTreeAsString"])(handlerData.event , keyAttrs);
    } catch (e) {
      target = '<unknown>';
    }

    if (target.length === 0) {
      return;
    }

    Object(_sentry_core__WEBPACK_IMPORTED_MODULE_0__["getCurrentHub"])().addBreadcrumb(
      {
        category: `ui.${handlerData.name}`,
        message: target,
      },
      {
        event: handlerData.event,
        name: handlerData.name,
        global: handlerData.global,
      },
    );
  }

  return _innerDomBreadcrumb;
}

/**
 * Creates breadcrumbs from console API calls
 */
function _consoleBreadcrumb(handlerData) {
  var breadcrumb = {
    category: 'console',
    data: {
      arguments: handlerData.args,
      logger: 'console',
    },
    level: Object(_sentry_utils__WEBPACK_IMPORTED_MODULE_1__["severityLevelFromString"])(handlerData.level),
    message: Object(_sentry_utils__WEBPACK_IMPORTED_MODULE_1__["safeJoin"])(handlerData.args, ' '),
  };

  if (handlerData.level === 'assert') {
    if (handlerData.args[0] === false) {
      breadcrumb.message = `Assertion failed: ${Object(_sentry_utils__WEBPACK_IMPORTED_MODULE_1__["safeJoin"])(handlerData.args.slice(1), ' ') || 'console.assert'}`;
      breadcrumb.data.arguments = handlerData.args.slice(1);
    } else {
      // Don't capture a breadcrumb for passed assertions
      return;
    }
  }

  Object(_sentry_core__WEBPACK_IMPORTED_MODULE_0__["getCurrentHub"])().addBreadcrumb(breadcrumb, {
    input: handlerData.args,
    level: handlerData.level,
  });
}

/**
 * Creates breadcrumbs from XHR API calls
 */
function _xhrBreadcrumb(handlerData) {
  if (handlerData.endTimestamp) {
    // We only capture complete, non-sentry requests
    if (handlerData.xhr.__sentry_own_request__) {
      return;
    }

    const { method, url, status_code, body } = handlerData.xhr.__sentry_xhr__ || {};

    Object(_sentry_core__WEBPACK_IMPORTED_MODULE_0__["getCurrentHub"])().addBreadcrumb(
      {
        category: 'xhr',
        data: {
          method,
          url,
          status_code,
        },
        type: 'http',
      },
      {
        xhr: handlerData.xhr,
        input: body,
      },
    );

    return;
  }
}

/**
 * Creates breadcrumbs from fetch API calls
 */
function _fetchBreadcrumb(handlerData) {
  // We only capture complete fetch requests
  if (!handlerData.endTimestamp) {
    return;
  }

  if (handlerData.fetchData.url.match(/sentry_key/) && handlerData.fetchData.method === 'POST') {
    // We will not create breadcrumbs for fetch requests that contain `sentry_key` (internal sentry requests)
    return;
  }

  if (handlerData.error) {
    Object(_sentry_core__WEBPACK_IMPORTED_MODULE_0__["getCurrentHub"])().addBreadcrumb(
      {
        category: 'fetch',
        data: handlerData.fetchData,
        level: 'error',
        type: 'http',
      },
      {
        data: handlerData.error,
        input: handlerData.args,
      },
    );
  } else {
    Object(_sentry_core__WEBPACK_IMPORTED_MODULE_0__["getCurrentHub"])().addBreadcrumb(
      {
        category: 'fetch',
        data: {
          ...handlerData.fetchData,
          status_code: handlerData.response.status,
        },
        type: 'http',
      },
      {
        input: handlerData.args,
        response: handlerData.response,
      },
    );
  }
}

/**
 * Creates breadcrumbs from history API calls
 */
function _historyBreadcrumb(handlerData) {
  var global = Object(_sentry_utils__WEBPACK_IMPORTED_MODULE_1__["getGlobalObject"])();
  let from = handlerData.from;
  let to = handlerData.to;
  var parsedLoc = Object(_sentry_utils__WEBPACK_IMPORTED_MODULE_1__["parseUrl"])(global.location.href);
  let parsedFrom = Object(_sentry_utils__WEBPACK_IMPORTED_MODULE_1__["parseUrl"])(from);
  var parsedTo = Object(_sentry_utils__WEBPACK_IMPORTED_MODULE_1__["parseUrl"])(to);

  // Initial pushState doesn't provide `from` information
  if (!parsedFrom.path) {
    parsedFrom = parsedLoc;
  }

  // Use only the path component of the URL if the URL matches the current
  // document (almost all the time when using pushState)
  if (parsedLoc.protocol === parsedTo.protocol && parsedLoc.host === parsedTo.host) {
    to = parsedTo.relative;
  }
  if (parsedLoc.protocol === parsedFrom.protocol && parsedLoc.host === parsedFrom.host) {
    from = parsedFrom.relative;
  }

  Object(_sentry_core__WEBPACK_IMPORTED_MODULE_0__["getCurrentHub"])().addBreadcrumb({
    category: 'navigation',
    data: {
      from,
      to,
    },
  });
}


//# sourceMappingURL=breadcrumbs.js.map


/***/ }),
/* 143 */
/***/ (function(module, __webpack_exports__, __webpack_require__) {

"use strict";
__webpack_require__.r(__webpack_exports__);
/* harmony export (binding) */ __webpack_require__.d(__webpack_exports__, "getNativeFetchImplementation", function() { return getNativeFetchImplementation; });
/* harmony export (binding) */ __webpack_require__.d(__webpack_exports__, "sendReport", function() { return sendReport; });
/* harmony import */ var _sentry_utils__WEBPACK_IMPORTED_MODULE_0__ = __webpack_require__(82);


var global = Object(_sentry_utils__WEBPACK_IMPORTED_MODULE_0__["getGlobalObject"])();
let cachedFetchImpl;

/**
 * A special usecase for incorrectly wrapped Fetch APIs in conjunction with ad-blockers.
 * Whenever someone wraps the Fetch API and returns the wrong promise chain,
 * this chain becomes orphaned and there is no possible way to capture it's rejections
 * other than allowing it bubble up to this very handler. eg.
 *
 * var f = window.fetch;
 * window.fetch = function () {
 *   var p = f.apply(this, arguments);
 *
 *   p.then(function() {
 *     console.log('hi.');
 *   });
 *
 *   return p;
 * }
 *
 * `p.then(function () { ... })` is producing a completely separate promise chain,
 * however, what's returned is `p` - the result of original `fetch` call.
 *
 * This mean, that whenever we use the Fetch API to send our own requests, _and_
 * some ad-blocker blocks it, this orphaned chain will _always_ reject,
 * effectively causing another event to be captured.
 * This makes a whole process become an infinite loop, which we need to somehow
 * deal with, and break it in one way or another.
 *
 * To deal with this issue, we are making sure that we _always_ use the real
 * browser Fetch API, instead of relying on what `window.fetch` exposes.
 * The only downside to this would be missing our own requests as breadcrumbs,
 * but because we are already not doing this, it should be just fine.
 *
 * Possible failed fetch error messages per-browser:
 *
 * Chrome:  Failed to fetch
 * Edge:    Failed to Fetch
 * Firefox: NetworkError when attempting to fetch resource
 * Safari:  resource blocked by content blocker
 */
function getNativeFetchImplementation() {
  if (cachedFetchImpl) {
    return cachedFetchImpl;
  }

  // Fast path to avoid DOM I/O
  if (Object(_sentry_utils__WEBPACK_IMPORTED_MODULE_0__["isNativeFetch"])(global.fetch)) {
    return (cachedFetchImpl = global.fetch.bind(global));
  }

  var document = global.document;
  let fetchImpl = global.fetch;
    if (document && typeof document.createElement === 'function') {
    try {
      var sandbox = document.createElement('iframe');
      sandbox.hidden = true;
      document.head.appendChild(sandbox);
      var contentWindow = sandbox.contentWindow;
      if (contentWindow && contentWindow.fetch) {
        fetchImpl = contentWindow.fetch;
      }
      document.head.removeChild(sandbox);
    } catch (e) {
      (typeof __SENTRY_DEBUG__ === 'undefined' || __SENTRY_DEBUG__) &&
        _sentry_utils__WEBPACK_IMPORTED_MODULE_0__["logger"].warn('Could not create sandbox iframe for pure fetch check, bailing to window.fetch: ', e);
    }
  }

  return (cachedFetchImpl = fetchImpl.bind(global));
  }

/**
 * Sends sdk client report using sendBeacon or fetch as a fallback if available
 *
 * @param url report endpoint
 * @param body report payload
 */
function sendReport(url, body) {
  var isRealNavigator = Object.prototype.toString.call(global && global.navigator) === '[object Navigator]';
  var hasSendBeacon = isRealNavigator && typeof global.navigator.sendBeacon === 'function';

  if (hasSendBeacon) {
    // Prevent illegal invocations - https://xgwang.me/posts/you-may-not-know-beacon/#it-may-throw-error%2C-be-sure-to-catch
    var sendBeacon = global.navigator.sendBeacon.bind(global.navigator);
    sendBeacon(url, body);
  } else if (Object(_sentry_utils__WEBPACK_IMPORTED_MODULE_0__["supportsFetch"])()) {
    var fetch = getNativeFetchImplementation();
    fetch(url, {
      body,
      method: 'POST',
      credentials: 'omit',
      keepalive: true,
    }).then(null, error => {
      (typeof __SENTRY_DEBUG__ === 'undefined' || __SENTRY_DEBUG__) && _sentry_utils__WEBPACK_IMPORTED_MODULE_0__["logger"].error(error);
    });
  }
}


//# sourceMappingURL=utils.js.map


/***/ }),
/* 144 */
/***/ (function(module, __webpack_exports__, __webpack_require__) {

"use strict";
__webpack_require__.r(__webpack_exports__);
/* harmony import */ var _fetch_js__WEBPACK_IMPORTED_MODULE_0__ = __webpack_require__(145);
/* harmony reexport (safe) */ __webpack_require__.d(__webpack_exports__, "makeFetchTransport", function() { return _fetch_js__WEBPACK_IMPORTED_MODULE_0__["makeFetchTransport"]; });

/* harmony import */ var _xhr_js__WEBPACK_IMPORTED_MODULE_1__ = __webpack_require__(146);
/* harmony reexport (safe) */ __webpack_require__.d(__webpack_exports__, "makeXHRTransport", function() { return _xhr_js__WEBPACK_IMPORTED_MODULE_1__["makeXHRTransport"]; });



//# sourceMappingURL=index.js.map


/***/ }),
/* 145 */
/***/ (function(module, __webpack_exports__, __webpack_require__) {

"use strict";
__webpack_require__.r(__webpack_exports__);
/* harmony export (binding) */ __webpack_require__.d(__webpack_exports__, "makeFetchTransport", function() { return makeFetchTransport; });
/* harmony import */ var _sentry_core__WEBPACK_IMPORTED_MODULE_0__ = __webpack_require__(79);
/* harmony import */ var _utils_js__WEBPACK_IMPORTED_MODULE_1__ = __webpack_require__(143);



/**
 * Creates a Transport that uses the Fetch API to send events to Sentry.
 */
function makeFetchTransport(
  options,
  nativeFetch = Object(_utils_js__WEBPACK_IMPORTED_MODULE_1__["getNativeFetchImplementation"])(),
) {
  function makeRequest(request) {
    var requestOptions = {
      body: request.body,
      method: 'POST',
      referrerPolicy: 'origin',
      headers: options.headers,
      ...options.fetchOptions,
    };

    return nativeFetch(options.url, requestOptions).then(response => ({
      statusCode: response.status,
      headers: {
        'x-sentry-rate-limits': response.headers.get('X-Sentry-Rate-Limits'),
        'retry-after': response.headers.get('Retry-After'),
      },
    }));
  }

  return Object(_sentry_core__WEBPACK_IMPORTED_MODULE_0__["createTransport"])(options, makeRequest);
}


//# sourceMappingURL=fetch.js.map


/***/ }),
/* 146 */
/***/ (function(module, __webpack_exports__, __webpack_require__) {

"use strict";
__webpack_require__.r(__webpack_exports__);
/* harmony export (binding) */ __webpack_require__.d(__webpack_exports__, "makeXHRTransport", function() { return makeXHRTransport; });
/* harmony import */ var _sentry_core__WEBPACK_IMPORTED_MODULE_0__ = __webpack_require__(79);
/* harmony import */ var _sentry_utils__WEBPACK_IMPORTED_MODULE_1__ = __webpack_require__(82);



/**
 * The DONE ready state for XmlHttpRequest
 *
 * Defining it here as a constant b/c XMLHttpRequest.DONE is not always defined
 * (e.g. during testing, it is `undefined`)
 *
 * @see {@link https://developer.mozilla.org/en-US/docs/Web/API/XMLHttpRequest/readyState}
 */
var XHR_READYSTATE_DONE = 4;

/**
 * Creates a Transport that uses the XMLHttpRequest API to send events to Sentry.
 */
function makeXHRTransport(options) {
  function makeRequest(request) {
    return new _sentry_utils__WEBPACK_IMPORTED_MODULE_1__["SyncPromise"]((resolve, reject) => {
      var xhr = new XMLHttpRequest();

      xhr.onerror = reject;

      xhr.onreadystatechange = () => {
        if (xhr.readyState === XHR_READYSTATE_DONE) {
          resolve({
            statusCode: xhr.status,
            headers: {
              'x-sentry-rate-limits': xhr.getResponseHeader('X-Sentry-Rate-Limits'),
              'retry-after': xhr.getResponseHeader('Retry-After'),
            },
          });
        }
      };

      xhr.open('POST', options.url);

      for (var header in options.headers) {
        if (Object.prototype.hasOwnProperty.call(options.headers, header)) {
          xhr.setRequestHeader(header, options.headers[header]);
        }
      }

      xhr.send(request.body);
    });
  }

  return Object(_sentry_core__WEBPACK_IMPORTED_MODULE_0__["createTransport"])(options, makeRequest);
}


//# sourceMappingURL=xhr.js.map


/***/ }),
/* 147 */
/***/ (function(module, __webpack_exports__, __webpack_require__) {

"use strict";
__webpack_require__.r(__webpack_exports__);
/* harmony export (binding) */ __webpack_require__.d(__webpack_exports__, "chromeStackLineParser", function() { return chromeStackLineParser; });
/* harmony export (binding) */ __webpack_require__.d(__webpack_exports__, "defaultStackLineParsers", function() { return defaultStackLineParsers; });
/* harmony export (binding) */ __webpack_require__.d(__webpack_exports__, "defaultStackParser", function() { return defaultStackParser; });
/* harmony export (binding) */ __webpack_require__.d(__webpack_exports__, "geckoStackLineParser", function() { return geckoStackLineParser; });
/* harmony export (binding) */ __webpack_require__.d(__webpack_exports__, "opera10StackLineParser", function() { return opera10StackLineParser; });
/* harmony export (binding) */ __webpack_require__.d(__webpack_exports__, "opera11StackLineParser", function() { return opera11StackLineParser; });
/* harmony export (binding) */ __webpack_require__.d(__webpack_exports__, "winjsStackLineParser", function() { return winjsStackLineParser; });
/* harmony import */ var _sentry_utils__WEBPACK_IMPORTED_MODULE_0__ = __webpack_require__(82);


// global reference to slice
var UNKNOWN_FUNCTION = '?';

var OPERA10_PRIORITY = 10;
var OPERA11_PRIORITY = 20;
var CHROME_PRIORITY = 30;
var WINJS_PRIORITY = 40;
var GECKO_PRIORITY = 50;

function createFrame(filename, func, lineno, colno) {
  var frame = {
    filename,
    function: func,
    // All browser frames are considered in_app
    in_app: true,
  };

  if (lineno !== undefined) {
    frame.lineno = lineno;
  }

  if (colno !== undefined) {
    frame.colno = colno;
  }

  return frame;
}

// Chromium based browsers: Chrome, Brave, new Opera, new Edge
var chromeRegex =
  /^\s*at (?:(.*?) ?\((?:address at )?)?((?:file|https?|blob|chrome-extension|address|native|eval|webpack|<anonymous>|[-a-z]+:|.*bundle|\/).*?)(?::(\d+))?(?::(\d+))?\)?\s*$/i;
var chromeEvalRegex = /\((\S*)(?::(\d+))(?::(\d+))\)/;

var chrome = line => {
  var parts = chromeRegex.exec(line);

  if (parts) {
    var isEval = parts[2] && parts[2].indexOf('eval') === 0; // start of line

    if (isEval) {
      var subMatch = chromeEvalRegex.exec(parts[2]);

      if (subMatch) {
        // throw out eval line/column and use top-most line/column number
        parts[2] = subMatch[1]; // url
        parts[3] = subMatch[2]; // line
        parts[4] = subMatch[3]; // column
      }
    }

    // Kamil: One more hack won't hurt us right? Understanding and adding more rules on top of these regexps right now
    // would be way too time consuming. (TODO: Rewrite whole RegExp to be more readable)
    const [func, filename] = extractSafariExtensionDetails(parts[1] || UNKNOWN_FUNCTION, parts[2]);

    return createFrame(filename, func, parts[3] ? +parts[3] : undefined, parts[4] ? +parts[4] : undefined);
  }

  return;
};

var chromeStackLineParser = [CHROME_PRIORITY, chrome];

// gecko regex: `(?:bundle|\d+\.js)`: `bundle` is for react native, `\d+\.js` also but specifically for ram bundles because it
// generates filenames without a prefix like `file://` the filenames in the stacktrace are just 42.js
// We need this specific case for now because we want no other regex to match.
var geckoREgex =
  /^\s*(.*?)(?:\((.*?)\))?(?:^|@)?((?:file|https?|blob|chrome|webpack|resource|moz-extension|capacitor).*?:\/.*?|\[native code\]|[^@]*(?:bundle|\d+\.js)|\/[\w\-. /=]+)(?::(\d+))?(?::(\d+))?\s*$/i;
var geckoEvalRegex = /(\S+) line (\d+)(?: > eval line \d+)* > eval/i;

var gecko = line => {
  var parts = geckoREgex.exec(line);

  if (parts) {
    var isEval = parts[3] && parts[3].indexOf(' > eval') > -1;
    if (isEval) {
      var subMatch = geckoEvalRegex.exec(parts[3]);

      if (subMatch) {
        // throw out eval line/column and use top-most line number
        parts[1] = parts[1] || 'eval';
        parts[3] = subMatch[1];
        parts[4] = subMatch[2];
        parts[5] = ''; // no column when eval
      }
    }

    let filename = parts[3];
    let func = parts[1] || UNKNOWN_FUNCTION;
    [func, filename] = extractSafariExtensionDetails(func, filename);

    return createFrame(filename, func, parts[4] ? +parts[4] : undefined, parts[5] ? +parts[5] : undefined);
  }

  return;
};

var geckoStackLineParser = [GECKO_PRIORITY, gecko];

var winjsRegex =
  /^\s*at (?:((?:\[object object\])?.+) )?\(?((?:file|ms-appx|https?|webpack|blob):.*?):(\d+)(?::(\d+))?\)?\s*$/i;

var winjs = line => {
  var parts = winjsRegex.exec(line);

  return parts
    ? createFrame(parts[2], parts[1] || UNKNOWN_FUNCTION, +parts[3], parts[4] ? +parts[4] : undefined)
    : undefined;
};

var winjsStackLineParser = [WINJS_PRIORITY, winjs];

var opera10Regex = / line (\d+).*script (?:in )?(\S+)(?:: in function (\S+))?$/i;

var opera10 = line => {
  var parts = opera10Regex.exec(line);
  return parts ? createFrame(parts[2], parts[3] || UNKNOWN_FUNCTION, +parts[1]) : undefined;
};

var opera10StackLineParser = [OPERA10_PRIORITY, opera10];

var opera11Regex =
  / line (\d+), column (\d+)\s*(?:in (?:<anonymous function: ([^>]+)>|([^)]+))\(.*\))? in (.*):\s*$/i;

var opera11 = line => {
  var parts = opera11Regex.exec(line);
  return parts ? createFrame(parts[5], parts[3] || parts[4] || UNKNOWN_FUNCTION, +parts[1], +parts[2]) : undefined;
};

var opera11StackLineParser = [OPERA11_PRIORITY, opera11];

var defaultStackLineParsers = [chromeStackLineParser, geckoStackLineParser, winjsStackLineParser];

var defaultStackParser = Object(_sentry_utils__WEBPACK_IMPORTED_MODULE_0__["createStackParser"])(...defaultStackLineParsers);

/**
 * Safari web extensions, starting version unknown, can produce "frames-only" stacktraces.
 * What it means, is that instead of format like:
 *
 * Error: wat
 *   at function@url:row:col
 *   at function@url:row:col
 *   at function@url:row:col
 *
 * it produces something like:
 *
 *   function@url:row:col
 *   function@url:row:col
 *   function@url:row:col
 *
 * Because of that, it won't be captured by `chrome` RegExp and will fall into `Gecko` branch.
 * This function is extracted so that we can use it in both places without duplicating the logic.
 * Unfortunately "just" changing RegExp is too complicated now and making it pass all tests
 * and fix this case seems like an impossible, or at least way too time-consuming task.
 */
var extractSafariExtensionDetails = (func, filename) => {
  var isSafariExtension = func.indexOf('safari-extension') !== -1;
  var isSafariWebExtension = func.indexOf('safari-web-extension') !== -1;

  return isSafariExtension || isSafariWebExtension
    ? [
        func.indexOf('@') !== -1 ? func.split('@')[0] : UNKNOWN_FUNCTION,
        isSafariExtension ? `safari-extension:${filename}` : `safari-web-extension:${filename}`,
      ]
    : [func, filename];
};


//# sourceMappingURL=stack-parsers.js.map


/***/ }),
/* 148 */
/***/ (function(module, __webpack_exports__, __webpack_require__) {

"use strict";
__webpack_require__.r(__webpack_exports__);
/* harmony export (binding) */ __webpack_require__.d(__webpack_exports__, "close", function() { return close; });
/* harmony export (binding) */ __webpack_require__.d(__webpack_exports__, "defaultIntegrations", function() { return defaultIntegrations; });
/* harmony export (binding) */ __webpack_require__.d(__webpack_exports__, "flush", function() { return flush; });
/* harmony export (binding) */ __webpack_require__.d(__webpack_exports__, "forceLoad", function() { return forceLoad; });
/* harmony export (binding) */ __webpack_require__.d(__webpack_exports__, "init", function() { return init; });
/* harmony export (binding) */ __webpack_require__.d(__webpack_exports__, "lastEventId", function() { return lastEventId; });
/* harmony export (binding) */ __webpack_require__.d(__webpack_exports__, "onLoad", function() { return onLoad; });
/* harmony export (binding) */ __webpack_require__.d(__webpack_exports__, "showReportDialog", function() { return showReportDialog; });
/* harmony export (binding) */ __webpack_require__.d(__webpack_exports__, "wrap", function() { return wrap; });
/* harmony import */ var _sentry_core__WEBPACK_IMPORTED_MODULE_0__ = __webpack_require__(79);
/* harmony import */ var _sentry_utils__WEBPACK_IMPORTED_MODULE_1__ = __webpack_require__(82);
/* harmony import */ var _client_js__WEBPACK_IMPORTED_MODULE_2__ = __webpack_require__(140);
/* harmony import */ var _helpers_js__WEBPACK_IMPORTED_MODULE_3__ = __webpack_require__(149);
/* harmony import */ var _integrations_index_js__WEBPACK_IMPORTED_MODULE_4__ = __webpack_require__(150);
/* harmony import */ var _stack_parsers_js__WEBPACK_IMPORTED_MODULE_5__ = __webpack_require__(147);
/* harmony import */ var _transports_index_js__WEBPACK_IMPORTED_MODULE_6__ = __webpack_require__(144);
/* harmony import */ var _integrations_trycatch_js__WEBPACK_IMPORTED_MODULE_7__ = __webpack_require__(152);
/* harmony import */ var _integrations_breadcrumbs_js__WEBPACK_IMPORTED_MODULE_8__ = __webpack_require__(142);
/* harmony import */ var _integrations_globalhandlers_js__WEBPACK_IMPORTED_MODULE_9__ = __webpack_require__(151);
/* harmony import */ var _integrations_linkederrors_js__WEBPACK_IMPORTED_MODULE_10__ = __webpack_require__(153);
/* harmony import */ var _integrations_dedupe_js__WEBPACK_IMPORTED_MODULE_11__ = __webpack_require__(155);
/* harmony import */ var _integrations_httpcontext_js__WEBPACK_IMPORTED_MODULE_12__ = __webpack_require__(154);
/* harmony import */ var _transports_fetch_js__WEBPACK_IMPORTED_MODULE_13__ = __webpack_require__(145);
/* harmony import */ var _transports_xhr_js__WEBPACK_IMPORTED_MODULE_14__ = __webpack_require__(146);
















var defaultIntegrations = [
  new _sentry_core__WEBPACK_IMPORTED_MODULE_0__["Integrations"].InboundFilters(),
  new _sentry_core__WEBPACK_IMPORTED_MODULE_0__["Integrations"].FunctionToString(),
  new _integrations_trycatch_js__WEBPACK_IMPORTED_MODULE_7__["TryCatch"](),
  new _integrations_breadcrumbs_js__WEBPACK_IMPORTED_MODULE_8__["Breadcrumbs"](),
  new _integrations_globalhandlers_js__WEBPACK_IMPORTED_MODULE_9__["GlobalHandlers"](),
  new _integrations_linkederrors_js__WEBPACK_IMPORTED_MODULE_10__["LinkedErrors"](),
  new _integrations_dedupe_js__WEBPACK_IMPORTED_MODULE_11__["Dedupe"](),
  new _integrations_httpcontext_js__WEBPACK_IMPORTED_MODULE_12__["HttpContext"](),
];

/**
 * The Sentry Browser SDK Client.
 *
 * To use this SDK, call the {@link init} function as early as possible when
 * loading the web page. To set context information or send manual events, use
 * the provided methods.
 *
 * @example
 *
 * ```
 *
 * import { init } from '@sentry/browser';
 *
 * init({
 *   dsn: '__DSN__',
 *   // ...
 * });
 * ```
 *
 * @example
 * ```
 *
 * import { configureScope } from '@sentry/browser';
 * configureScope((scope: Scope) => {
 *   scope.setExtra({ battery: 0.7 });
 *   scope.setTag({ user_mode: 'admin' });
 *   scope.setUser({ id: '4711' });
 * });
 * ```
 *
 * @example
 * ```
 *
 * import { addBreadcrumb } from '@sentry/browser';
 * addBreadcrumb({
 *   message: 'My Breadcrumb',
 *   // ...
 * });
 * ```
 *
 * @example
 *
 * ```
 *
 * import * as Sentry from '@sentry/browser';
 * Sentry.captureMessage('Hello, world!');
 * Sentry.captureException(new Error('Good bye'));
 * Sentry.captureEvent({
 *   message: 'Manual',
 *   stacktrace: [
 *     // ...
 *   ],
 * });
 * ```
 *
 * @see {@link BrowserOptions} for documentation on configuration options.
 */
function init(options = {}) {
  if (options.defaultIntegrations === undefined) {
    options.defaultIntegrations = defaultIntegrations;
  }
  if (options.release === undefined) {
    var window = Object(_sentry_utils__WEBPACK_IMPORTED_MODULE_1__["getGlobalObject"])();
    // This supports the variable that sentry-webpack-plugin injects
    if (window.SENTRY_RELEASE && window.SENTRY_RELEASE.id) {
      options.release = window.SENTRY_RELEASE.id;
    }
  }
  if (options.autoSessionTracking === undefined) {
    options.autoSessionTracking = true;
  }
  if (options.sendClientReports === undefined) {
    options.sendClientReports = true;
  }

  var clientOptions = {
    ...options,
    stackParser: Object(_sentry_utils__WEBPACK_IMPORTED_MODULE_1__["stackParserFromStackParserOptions"])(options.stackParser || _stack_parsers_js__WEBPACK_IMPORTED_MODULE_5__["defaultStackParser"]),
    integrations: Object(_sentry_core__WEBPACK_IMPORTED_MODULE_0__["getIntegrationsToSetup"])(options),
    transport: options.transport || (Object(_sentry_utils__WEBPACK_IMPORTED_MODULE_1__["supportsFetch"])() ? _transports_fetch_js__WEBPACK_IMPORTED_MODULE_13__["makeFetchTransport"] : _transports_xhr_js__WEBPACK_IMPORTED_MODULE_14__["makeXHRTransport"]),
  };

  Object(_sentry_core__WEBPACK_IMPORTED_MODULE_0__["initAndBind"])(_client_js__WEBPACK_IMPORTED_MODULE_2__["BrowserClient"], clientOptions);

  if (options.autoSessionTracking) {
    startSessionTracking();
  }
}

/**
 * Present the user with a report dialog.
 *
 * @param options Everything is optional, we try to fetch all info need from the global scope.
 */
function showReportDialog(options = {}, hub = Object(_sentry_core__WEBPACK_IMPORTED_MODULE_0__["getCurrentHub"])()) {
  // doesn't work without a document (React Native)
  var global = Object(_sentry_utils__WEBPACK_IMPORTED_MODULE_1__["getGlobalObject"])();
  if (!global.document) {
    (typeof __SENTRY_DEBUG__ === 'undefined' || __SENTRY_DEBUG__) && _sentry_utils__WEBPACK_IMPORTED_MODULE_1__["logger"].error('Global document not defined in showReportDialog call');
    return;
  }

  const { client, scope } = hub.getStackTop();
  var dsn = options.dsn || (client && client.getDsn());
  if (!dsn) {
    (typeof __SENTRY_DEBUG__ === 'undefined' || __SENTRY_DEBUG__) && _sentry_utils__WEBPACK_IMPORTED_MODULE_1__["logger"].error('DSN not configured for showReportDialog call');
    return;
  }

  if (scope) {
    options.user = {
      ...scope.getUser(),
      ...options.user,
    };
  }

  if (!options.eventId) {
    options.eventId = hub.lastEventId();
  }

  var script = global.document.createElement('script');
  script.async = true;
  script.src = Object(_sentry_core__WEBPACK_IMPORTED_MODULE_0__["getReportDialogEndpoint"])(dsn, options);

  if (options.onLoad) {
        script.onload = options.onLoad;
  }

  var injectionPoint = global.document.head || global.document.body;
  if (injectionPoint) {
    injectionPoint.appendChild(script);
  } else {
    (typeof __SENTRY_DEBUG__ === 'undefined' || __SENTRY_DEBUG__) && _sentry_utils__WEBPACK_IMPORTED_MODULE_1__["logger"].error('Not injecting report dialog. No injection point found in HTML');
  }
}

/**
 * This is the getter for lastEventId.
 *
 * @returns The last event id of a captured event.
 */
function lastEventId() {
  return Object(_sentry_core__WEBPACK_IMPORTED_MODULE_0__["getCurrentHub"])().lastEventId();
}

/**
 * This function is here to be API compatible with the loader.
 * @hidden
 */
function forceLoad() {
  // Noop
}

/**
 * This function is here to be API compatible with the loader.
 * @hidden
 */
function onLoad(callback) {
  callback();
}

/**
 * Call `flush()` on the current client, if there is one. See {@link Client.flush}.
 *
 * @param timeout Maximum time in ms the client should wait to flush its event queue. Omitting this parameter will cause
 * the client to wait until all events are sent before resolving the promise.
 * @returns A promise which resolves to `true` if the queue successfully drains before the timeout, or `false` if it
 * doesn't (or if there's no client defined).
 */
function flush(timeout) {
  var client = Object(_sentry_core__WEBPACK_IMPORTED_MODULE_0__["getCurrentHub"])().getClient();
  if (client) {
    return client.flush(timeout);
  }
  (typeof __SENTRY_DEBUG__ === 'undefined' || __SENTRY_DEBUG__) && _sentry_utils__WEBPACK_IMPORTED_MODULE_1__["logger"].warn('Cannot flush events. No client defined.');
  return Object(_sentry_utils__WEBPACK_IMPORTED_MODULE_1__["resolvedSyncPromise"])(false);
}

/**
 * Call `close()` on the current client, if there is one. See {@link Client.close}.
 *
 * @param timeout Maximum time in ms the client should wait to flush its event queue before shutting down. Omitting this
 * parameter will cause the client to wait until all events are sent before disabling itself.
 * @returns A promise which resolves to `true` if the queue successfully drains before the timeout, or `false` if it
 * doesn't (or if there's no client defined).
 */
function close(timeout) {
  var client = Object(_sentry_core__WEBPACK_IMPORTED_MODULE_0__["getCurrentHub"])().getClient();
  if (client) {
    return client.close(timeout);
  }
  (typeof __SENTRY_DEBUG__ === 'undefined' || __SENTRY_DEBUG__) && _sentry_utils__WEBPACK_IMPORTED_MODULE_1__["logger"].warn('Cannot flush events and disable SDK. No client defined.');
  return Object(_sentry_utils__WEBPACK_IMPORTED_MODULE_1__["resolvedSyncPromise"])(false);
}

/**
 * Wrap code within a try/catch block so the SDK is able to capture errors.
 *
 * @param fn A function to wrap.
 *
 * @returns The result of wrapped function call.
 */
function wrap(fn) {
  return Object(_helpers_js__WEBPACK_IMPORTED_MODULE_3__["wrap"])(fn)();
}

function startSessionOnHub(hub) {
  hub.startSession({ ignoreDuration: true });
  hub.captureSession();
}

/**
 * Enable automatic Session Tracking for the initial page load.
 */
function startSessionTracking() {
  var window = Object(_sentry_utils__WEBPACK_IMPORTED_MODULE_1__["getGlobalObject"])();
  var document = window.document;

  if (typeof document === 'undefined') {
    (typeof __SENTRY_DEBUG__ === 'undefined' || __SENTRY_DEBUG__) &&
      _sentry_utils__WEBPACK_IMPORTED_MODULE_1__["logger"].warn('Session tracking in non-browser environment with @sentry/browser is not supported.');
    return;
  }

  var hub = Object(_sentry_core__WEBPACK_IMPORTED_MODULE_0__["getCurrentHub"])();

  // The only way for this to be false is for there to be a version mismatch between @sentry/browser (>= 6.0.0) and
  // @sentry/hub (< 5.27.0). In the simple case, there won't ever be such a mismatch, because the two packages are
  // pinned at the same version in package.json, but there are edge cases where it's possible. See
  // https://github.com/getsentry/sentry-javascript/issues/3207 and
  // https://github.com/getsentry/sentry-javascript/issues/3234 and
  // https://github.com/getsentry/sentry-javascript/issues/3278.
  if (!hub.captureSession) {
    return;
  }

  // The session duration for browser sessions does not track a meaningful
  // concept that can be used as a metric.
  // Automatically captured sessions are akin to page views, and thus we
  // discard their duration.
  startSessionOnHub(hub);

  // We want to create a session for every navigation as well
  Object(_sentry_utils__WEBPACK_IMPORTED_MODULE_1__["addInstrumentationHandler"])('history', ({ from, to }) => {
    // Don't create an additional session for the initial route or if the location did not change
    if (!(from === undefined || from === to)) {
      startSessionOnHub(Object(_sentry_core__WEBPACK_IMPORTED_MODULE_0__["getCurrentHub"])());
    }
  });
}


//# sourceMappingURL=sdk.js.map


/***/ }),
/* 149 */
/***/ (function(module, __webpack_exports__, __webpack_require__) {

"use strict";
__webpack_require__.r(__webpack_exports__);
/* harmony export (binding) */ __webpack_require__.d(__webpack_exports__, "ignoreNextOnError", function() { return ignoreNextOnError; });
/* harmony export (binding) */ __webpack_require__.d(__webpack_exports__, "shouldIgnoreOnError", function() { return shouldIgnoreOnError; });
/* harmony export (binding) */ __webpack_require__.d(__webpack_exports__, "wrap", function() { return wrap; });
/* harmony import */ var _sentry_core__WEBPACK_IMPORTED_MODULE_0__ = __webpack_require__(79);
/* harmony import */ var _sentry_utils__WEBPACK_IMPORTED_MODULE_1__ = __webpack_require__(82);



let ignoreOnError = 0;

/**
 * @hidden
 */
function shouldIgnoreOnError() {
  return ignoreOnError > 0;
}

/**
 * @hidden
 */
function ignoreNextOnError() {
  // onerror should trigger before setTimeout
  ignoreOnError += 1;
  setTimeout(() => {
    ignoreOnError -= 1;
  });
}

/**
 * Instruments the given function and sends an event to Sentry every time the
 * function throws an exception.
 *
 * @param fn A function to wrap. It is generally safe to pass an unbound function, because the returned wrapper always
 * has a correct `this` context.
 * @returns The wrapped function.
 * @hidden
 */
function wrap(
  fn,
  options

 = {},
  before,
  ) {
  // for future readers what this does is wrap a function and then create
  // a bi-directional wrapping between them.
  //
  // example: wrapped = wrap(original);
  //  original.__sentry_wrapped__ -> wrapped
  //  wrapped.__sentry_original__ -> original

  if (typeof fn !== 'function') {
    return fn;
  }

  try {
    // if we're dealing with a function that was previously wrapped, return
    // the original wrapper.
    var wrapper = fn.__sentry_wrapped__;
    if (wrapper) {
      return wrapper;
    }

    // We don't wanna wrap it twice
    if (Object(_sentry_utils__WEBPACK_IMPORTED_MODULE_1__["getOriginalFunction"])(fn)) {
      return fn;
    }
  } catch (e) {
    // Just accessing custom props in some Selenium environments
    // can cause a "Permission denied" exception (see raven-js#495).
    // Bail on wrapping and return the function as-is (defers to window.onerror).
    return fn;
  }

    // It is important that `sentryWrapped` is not an arrow function to preserve the context of `this`
  var sentryWrapped = function () {
    var args = Array.prototype.slice.call(arguments);

    try {
      if (before && typeof before === 'function') {
        before.apply(this, arguments);
      }

            var wrappedArguments = args.map((arg) => wrap(arg, options));

      // Attempt to invoke user-land function
      // NOTE: If you are a Sentry user, and you are seeing this stack frame, it
      //       means the sentry.javascript SDK caught an error invoking your application code. This
      //       is expected behavior and NOT indicative of a bug with sentry.javascript.
      return fn.apply(this, wrappedArguments);
    } catch (ex) {
      ignoreNextOnError();

      Object(_sentry_core__WEBPACK_IMPORTED_MODULE_0__["withScope"])((scope) => {
        scope.addEventProcessor((event) => {
          if (options.mechanism) {
            Object(_sentry_utils__WEBPACK_IMPORTED_MODULE_1__["addExceptionTypeValue"])(event, undefined, undefined);
            Object(_sentry_utils__WEBPACK_IMPORTED_MODULE_1__["addExceptionMechanism"])(event, options.mechanism);
          }

          event.extra = {
            ...event.extra,
            arguments: args,
          };

          return event;
        });

        Object(_sentry_core__WEBPACK_IMPORTED_MODULE_0__["captureException"])(ex);
      });

      throw ex;
    }
  };
  
  // Accessing some objects may throw
  // ref: https://github.com/getsentry/sentry-javascript/issues/1168
  try {
    for (var property in fn) {
      if (Object.prototype.hasOwnProperty.call(fn, property)) {
        sentryWrapped[property] = fn[property];
      }
    }
  } catch (_oO) {} 
  // Signal that this function has been wrapped/filled already
  // for both debugging and to prevent it to being wrapped/filled twice
  Object(_sentry_utils__WEBPACK_IMPORTED_MODULE_1__["markFunctionWrapped"])(sentryWrapped, fn);

  Object(_sentry_utils__WEBPACK_IMPORTED_MODULE_1__["addNonEnumerableProperty"])(fn, '__sentry_wrapped__', sentryWrapped);

  // Restore original function name (not all browsers allow that)
  try {
    var descriptor = Object.getOwnPropertyDescriptor(sentryWrapped, 'name') ;
    if (descriptor.configurable) {
      Object.defineProperty(sentryWrapped, 'name', {
        get() {
          return fn.name;
        },
      });
    }
      } catch (_oO) {}

  return sentryWrapped;
}

/**
 * All properties the report dialog supports
 */


//# sourceMappingURL=helpers.js.map


/***/ }),
/* 150 */
/***/ (function(module, __webpack_exports__, __webpack_require__) {

"use strict";
__webpack_require__.r(__webpack_exports__);
/* harmony import */ var _globalhandlers_js__WEBPACK_IMPORTED_MODULE_0__ = __webpack_require__(151);
/* harmony reexport (safe) */ __webpack_require__.d(__webpack_exports__, "GlobalHandlers", function() { return _globalhandlers_js__WEBPACK_IMPORTED_MODULE_0__["GlobalHandlers"]; });

/* harmony import */ var _trycatch_js__WEBPACK_IMPORTED_MODULE_1__ = __webpack_require__(152);
/* harmony reexport (safe) */ __webpack_require__.d(__webpack_exports__, "TryCatch", function() { return _trycatch_js__WEBPACK_IMPORTED_MODULE_1__["TryCatch"]; });

/* harmony import */ var _breadcrumbs_js__WEBPACK_IMPORTED_MODULE_2__ = __webpack_require__(142);
/* harmony reexport (safe) */ __webpack_require__.d(__webpack_exports__, "Breadcrumbs", function() { return _breadcrumbs_js__WEBPACK_IMPORTED_MODULE_2__["Breadcrumbs"]; });

/* harmony import */ var _linkederrors_js__WEBPACK_IMPORTED_MODULE_3__ = __webpack_require__(153);
/* harmony reexport (safe) */ __webpack_require__.d(__webpack_exports__, "LinkedErrors", function() { return _linkederrors_js__WEBPACK_IMPORTED_MODULE_3__["LinkedErrors"]; });

/* harmony import */ var _httpcontext_js__WEBPACK_IMPORTED_MODULE_4__ = __webpack_require__(154);
/* harmony reexport (safe) */ __webpack_require__.d(__webpack_exports__, "HttpContext", function() { return _httpcontext_js__WEBPACK_IMPORTED_MODULE_4__["HttpContext"]; });

/* harmony import */ var _dedupe_js__WEBPACK_IMPORTED_MODULE_5__ = __webpack_require__(155);
/* harmony reexport (safe) */ __webpack_require__.d(__webpack_exports__, "Dedupe", function() { return _dedupe_js__WEBPACK_IMPORTED_MODULE_5__["Dedupe"]; });







//# sourceMappingURL=index.js.map


/***/ }),
/* 151 */
/***/ (function(module, __webpack_exports__, __webpack_require__) {

"use strict";
__webpack_require__.r(__webpack_exports__);
/* harmony export (binding) */ __webpack_require__.d(__webpack_exports__, "GlobalHandlers", function() { return GlobalHandlers; });
/* harmony import */ var _sentry_core__WEBPACK_IMPORTED_MODULE_0__ = __webpack_require__(79);
/* harmony import */ var _sentry_utils__WEBPACK_IMPORTED_MODULE_1__ = __webpack_require__(82);
/* harmony import */ var _eventbuilder_js__WEBPACK_IMPORTED_MODULE_2__ = __webpack_require__(141);
/* harmony import */ var _helpers_js__WEBPACK_IMPORTED_MODULE_3__ = __webpack_require__(149);





/** Global handlers */
class GlobalHandlers  {
  /**
   * @inheritDoc
   */
   static __initStatic() {this.id = 'GlobalHandlers';}

  /**
   * @inheritDoc
   */
   __init() {this.name = GlobalHandlers.id;}

  /** JSDoc */
  

  /**
   * Stores references functions to installing handlers. Will set to undefined
   * after they have been run so that they are not used twice.
   */
   __init2() {this._installFunc = {
    onerror: _installGlobalOnErrorHandler,
    onunhandledrejection: _installGlobalOnUnhandledRejectionHandler,
  };}

  /** JSDoc */
   constructor(options) {;GlobalHandlers.prototype.__init.call(this);GlobalHandlers.prototype.__init2.call(this);
    this._options = {
      onerror: true,
      onunhandledrejection: true,
      ...options,
    };
  }
  /**
   * @inheritDoc
   */
   setupOnce() {
    Error.stackTraceLimit = 50;
    var options = this._options;

    // We can disable guard-for-in as we construct the options object above + do checks against
    // `this._installFunc` for the property.
        for (var key in options) {
      var installFunc = this._installFunc[key ];
      if (installFunc && options[key ]) {
        globalHandlerLog(key);
        installFunc();
        this._installFunc[key ] = undefined;
      }
    }
  }
} GlobalHandlers.__initStatic();

/** JSDoc */
function _installGlobalOnErrorHandler() {
  Object(_sentry_utils__WEBPACK_IMPORTED_MODULE_1__["addInstrumentationHandler"])(
    'error',
        (data) => {
      const [hub, stackParser, attachStacktrace] = getHubAndOptions();
      if (!hub.getIntegration(GlobalHandlers)) {
        return;
      }
      const { msg, url, line, column, error } = data;
      if (Object(_helpers_js__WEBPACK_IMPORTED_MODULE_3__["shouldIgnoreOnError"])() || (error && error.__sentry_own_request__)) {
        return;
      }

      var event =
        error === undefined && Object(_sentry_utils__WEBPACK_IMPORTED_MODULE_1__["isString"])(msg)
          ? _eventFromIncompleteOnError(msg, url, line, column)
          : _enhanceEventWithInitialFrame(
              Object(_eventbuilder_js__WEBPACK_IMPORTED_MODULE_2__["eventFromUnknownInput"])(stackParser, error || msg, undefined, attachStacktrace, false),
              url,
              line,
              column,
            );

      event.level = 'error';

      addMechanismAndCapture(hub, error, event, 'onerror');
    },
  );
}

/** JSDoc */
function _installGlobalOnUnhandledRejectionHandler() {
  Object(_sentry_utils__WEBPACK_IMPORTED_MODULE_1__["addInstrumentationHandler"])(
    'unhandledrejection',
        (e) => {
      const [hub, stackParser, attachStacktrace] = getHubAndOptions();
      if (!hub.getIntegration(GlobalHandlers)) {
        return;
      }
      let error = e;

      // dig the object of the rejection out of known event types
      try {
        // PromiseRejectionEvents store the object of the rejection under 'reason'
        // see https://developer.mozilla.org/en-US/docs/Web/API/PromiseRejectionEvent
        if ('reason' in e) {
          error = e.reason;
        }
        // something, somewhere, (likely a browser extension) effectively casts PromiseRejectionEvents
        // to CustomEvents, moving the `promise` and `reason` attributes of the PRE into
        // the CustomEvent's `detail` attribute, since they're not part of CustomEvent's spec
        // see https://developer.mozilla.org/en-US/docs/Web/API/CustomEvent and
        // https://github.com/getsentry/sentry-javascript/issues/2380
        else if ('detail' in e && 'reason' in e.detail) {
          error = e.detail.reason;
        }
      } catch (_oO) {
        // no-empty
      }

      if (Object(_helpers_js__WEBPACK_IMPORTED_MODULE_3__["shouldIgnoreOnError"])() || (error && error.__sentry_own_request__)) {
        return true;
      }

      var event = Object(_sentry_utils__WEBPACK_IMPORTED_MODULE_1__["isPrimitive"])(error)
        ? _eventFromRejectionWithPrimitive(error)
        : Object(_eventbuilder_js__WEBPACK_IMPORTED_MODULE_2__["eventFromUnknownInput"])(stackParser, error, undefined, attachStacktrace, true);

      event.level = 'error';

      addMechanismAndCapture(hub, error, event, 'onunhandledrejection');
      return;
    },
  );
}

/**
 * Create an event from a promise rejection where the `reason` is a primitive.
 *
 * @param reason: The `reason` property of the promise rejection
 * @returns An Event object with an appropriate `exception` value
 */
function _eventFromRejectionWithPrimitive(reason) {
  return {
    exception: {
      values: [
        {
          type: 'UnhandledRejection',
          // String() is needed because the Primitive type includes symbols (which can't be automatically stringified)
          value: `Non-Error promise rejection captured with value: ${String(reason)}`,
        },
      ],
    },
  };
}

/**
 * This function creates a stack from an old, error-less onerror handler.
 */
function _eventFromIncompleteOnError(msg, url, line, column) {
  var ERROR_TYPES_RE =
    /^(?:[Uu]ncaught (?:exception: )?)?(?:((?:Eval|Internal|Range|Reference|Syntax|Type|URI|)Error): )?(.*)$/i;

  // If 'message' is ErrorEvent, get real message from inside
  let message = Object(_sentry_utils__WEBPACK_IMPORTED_MODULE_1__["isErrorEvent"])(msg) ? msg.message : msg;
  let name = 'Error';

  var groups = message.match(ERROR_TYPES_RE);
  if (groups) {
    name = groups[1];
    message = groups[2];
  }

  var event = {
    exception: {
      values: [
        {
          type: name,
          value: message,
        },
      ],
    },
  };

  return _enhanceEventWithInitialFrame(event, url, line, column);
}

/** JSDoc */
function _enhanceEventWithInitialFrame(event, url, line, column) {
  // event.exception
  var e = (event.exception = event.exception || {});
  // event.exception.values
  var ev = (e.values = e.values || []);
  // event.exception.values[0]
  var ev0 = (ev[0] = ev[0] || {});
  // event.exception.values[0].stacktrace
  var ev0s = (ev0.stacktrace = ev0.stacktrace || {});
  // event.exception.values[0].stacktrace.frames
  var ev0sf = (ev0s.frames = ev0s.frames || []);

  var colno = isNaN(parseInt(column, 10)) ? undefined : column;
  var lineno = isNaN(parseInt(line, 10)) ? undefined : line;
  var filename = Object(_sentry_utils__WEBPACK_IMPORTED_MODULE_1__["isString"])(url) && url.length > 0 ? url : Object(_sentry_utils__WEBPACK_IMPORTED_MODULE_1__["getLocationHref"])();

  // event.exception.values[0].stacktrace.frames
  if (ev0sf.length === 0) {
    ev0sf.push({
      colno,
      filename,
      function: '?',
      in_app: true,
      lineno,
    });
  }

  return event;
}

function globalHandlerLog(type) {
  (typeof __SENTRY_DEBUG__ === 'undefined' || __SENTRY_DEBUG__) && _sentry_utils__WEBPACK_IMPORTED_MODULE_1__["logger"].log(`Global Handler attached: ${type}`);
}

function addMechanismAndCapture(hub, error, event, type) {
  Object(_sentry_utils__WEBPACK_IMPORTED_MODULE_1__["addExceptionMechanism"])(event, {
    handled: false,
    type,
  });
  hub.captureEvent(event, {
    originalException: error,
  });
}

function getHubAndOptions() {
  var hub = Object(_sentry_core__WEBPACK_IMPORTED_MODULE_0__["getCurrentHub"])();
  var client = hub.getClient();
  var options = (client && client.getOptions()) || {
    stackParser: () => [],
    attachStacktrace: false,
  };
  return [hub, options.stackParser, options.attachStacktrace];
}


//# sourceMappingURL=globalhandlers.js.map


/***/ }),
/* 152 */
/***/ (function(module, __webpack_exports__, __webpack_require__) {

"use strict";
__webpack_require__.r(__webpack_exports__);
/* harmony export (binding) */ __webpack_require__.d(__webpack_exports__, "TryCatch", function() { return TryCatch; });
/* harmony import */ var _sentry_utils__WEBPACK_IMPORTED_MODULE_0__ = __webpack_require__(82);
/* harmony import */ var _helpers_js__WEBPACK_IMPORTED_MODULE_1__ = __webpack_require__(149);



var DEFAULT_EVENT_TARGET = [
  'EventTarget',
  'Window',
  'Node',
  'ApplicationCache',
  'AudioTrackList',
  'ChannelMergerNode',
  'CryptoOperation',
  'EventSource',
  'FileReader',
  'HTMLUnknownElement',
  'IDBDatabase',
  'IDBRequest',
  'IDBTransaction',
  'KeyOperation',
  'MediaController',
  'MessagePort',
  'ModalWindow',
  'Notification',
  'SVGElementInstance',
  'Screen',
  'TextTrack',
  'TextTrackCue',
  'TextTrackList',
  'WebSocket',
  'WebSocketWorker',
  'Worker',
  'XMLHttpRequest',
  'XMLHttpRequestEventTarget',
  'XMLHttpRequestUpload',
];

/** Wrap timer functions and event targets to catch errors and provide better meta data */
class TryCatch  {
  /**
   * @inheritDoc
   */
   static __initStatic() {this.id = 'TryCatch';}

  /**
   * @inheritDoc
   */
   __init() {this.name = TryCatch.id;}

  /** JSDoc */
  

  /**
   * @inheritDoc
   */
   constructor(options) {;TryCatch.prototype.__init.call(this);
    this._options = {
      XMLHttpRequest: true,
      eventTarget: true,
      requestAnimationFrame: true,
      setInterval: true,
      setTimeout: true,
      ...options,
    };
  }

  /**
   * Wrap timer functions and event targets to catch errors
   * and provide better metadata.
   */
   setupOnce() {
    var global = Object(_sentry_utils__WEBPACK_IMPORTED_MODULE_0__["getGlobalObject"])();

    if (this._options.setTimeout) {
      Object(_sentry_utils__WEBPACK_IMPORTED_MODULE_0__["fill"])(global, 'setTimeout', _wrapTimeFunction);
    }

    if (this._options.setInterval) {
      Object(_sentry_utils__WEBPACK_IMPORTED_MODULE_0__["fill"])(global, 'setInterval', _wrapTimeFunction);
    }

    if (this._options.requestAnimationFrame) {
      Object(_sentry_utils__WEBPACK_IMPORTED_MODULE_0__["fill"])(global, 'requestAnimationFrame', _wrapRAF);
    }

    if (this._options.XMLHttpRequest && 'XMLHttpRequest' in global) {
      Object(_sentry_utils__WEBPACK_IMPORTED_MODULE_0__["fill"])(XMLHttpRequest.prototype, 'send', _wrapXHR);
    }

    var eventTargetOption = this._options.eventTarget;
    if (eventTargetOption) {
      var eventTarget = Array.isArray(eventTargetOption) ? eventTargetOption : DEFAULT_EVENT_TARGET;
      eventTarget.forEach(_wrapEventTarget);
    }
  }
} TryCatch.__initStatic();

/** JSDoc */
function _wrapTimeFunction(original) {
    return function ( ...args) {
    var originalCallback = args[0];
    args[0] = Object(_helpers_js__WEBPACK_IMPORTED_MODULE_1__["wrap"])(originalCallback, {
      mechanism: {
        data: { function: Object(_sentry_utils__WEBPACK_IMPORTED_MODULE_0__["getFunctionName"])(original) },
        handled: true,
        type: 'instrument',
      },
    });
    return original.apply(this, args);
  };
}

/** JSDoc */
function _wrapRAF(original) {
    return function ( callback) {
        return original.apply(this, [
      Object(_helpers_js__WEBPACK_IMPORTED_MODULE_1__["wrap"])(callback, {
        mechanism: {
          data: {
            function: 'requestAnimationFrame',
            handler: Object(_sentry_utils__WEBPACK_IMPORTED_MODULE_0__["getFunctionName"])(original),
          },
          handled: true,
          type: 'instrument',
        },
      }),
    ]);
  };
}

/** JSDoc */
function _wrapXHR(originalSend) {
    return function ( ...args) {
        var xhr = this;
    var xmlHttpRequestProps = ['onload', 'onerror', 'onprogress', 'onreadystatechange'];

    xmlHttpRequestProps.forEach(prop => {
      if (prop in xhr && typeof xhr[prop] === 'function') {
                Object(_sentry_utils__WEBPACK_IMPORTED_MODULE_0__["fill"])(xhr, prop, function (original) {
          var wrapOptions = {
            mechanism: {
              data: {
                function: prop,
                handler: Object(_sentry_utils__WEBPACK_IMPORTED_MODULE_0__["getFunctionName"])(original),
              },
              handled: true,
              type: 'instrument',
            },
          };

          // If Instrument integration has been called before TryCatch, get the name of original function
          var originalFunction = Object(_sentry_utils__WEBPACK_IMPORTED_MODULE_0__["getOriginalFunction"])(original);
          if (originalFunction) {
            wrapOptions.mechanism.data.handler = Object(_sentry_utils__WEBPACK_IMPORTED_MODULE_0__["getFunctionName"])(originalFunction);
          }

          // Otherwise wrap directly
          return Object(_helpers_js__WEBPACK_IMPORTED_MODULE_1__["wrap"])(original, wrapOptions);
        });
      }
    });

    return originalSend.apply(this, args);
  };
}

/** JSDoc */
function _wrapEventTarget(target) {
    var global = Object(_sentry_utils__WEBPACK_IMPORTED_MODULE_0__["getGlobalObject"])() ;
    var proto = global[target] && global[target].prototype;

    if (!proto || !proto.hasOwnProperty || !proto.hasOwnProperty('addEventListener')) {
    return;
  }

  Object(_sentry_utils__WEBPACK_IMPORTED_MODULE_0__["fill"])(proto, 'addEventListener', function (original)

 {
    return function (
            
      eventName,
      fn,
      options,
    ) {
      try {
        if (typeof fn.handleEvent === 'function') {
          // ESlint disable explanation:
          //  First, it is generally safe to call `wrap` with an unbound function. Furthermore, using `.bind()` would
          //  introduce a bug here, because bind returns a new function that doesn't have our
          //  flags(like __sentry_original__) attached. `wrap` checks for those flags to avoid unnecessary wrapping.
          //  Without those flags, every call to addEventListener wraps the function again, causing a memory leak.
                    fn.handleEvent = Object(_helpers_js__WEBPACK_IMPORTED_MODULE_1__["wrap"])(fn.handleEvent, {
            mechanism: {
              data: {
                function: 'handleEvent',
                handler: Object(_sentry_utils__WEBPACK_IMPORTED_MODULE_0__["getFunctionName"])(fn),
                target,
              },
              handled: true,
              type: 'instrument',
            },
          });
        }
      } catch (err) {
        // can sometimes get 'Permission denied to access property "handle Event'
      }

      return original.apply(this, [
        eventName,
                Object(_helpers_js__WEBPACK_IMPORTED_MODULE_1__["wrap"])(fn , {
          mechanism: {
            data: {
              function: 'addEventListener',
              handler: Object(_sentry_utils__WEBPACK_IMPORTED_MODULE_0__["getFunctionName"])(fn),
              target,
            },
            handled: true,
            type: 'instrument',
          },
        }),
        options,
      ]);
    };
  });

  Object(_sentry_utils__WEBPACK_IMPORTED_MODULE_0__["fill"])(
    proto,
    'removeEventListener',
    function (
      originalRemoveEventListener,
          ) {
      return function (
                
        eventName,
        fn,
        options,
      ) {
        /**
         * There are 2 possible scenarios here:
         *
         * 1. Someone passes a callback, which was attached prior to Sentry initialization, or by using unmodified
         * method, eg. `document.addEventListener.call(el, name, handler). In this case, we treat this function
         * as a pass-through, and call original `removeEventListener` with it.
         *
         * 2. Someone passes a callback, which was attached after Sentry was initialized, which means that it was using
         * our wrapped version of `addEventListener`, which internally calls `wrap` helper.
         * This helper "wraps" whole callback inside a try/catch statement, and attached appropriate metadata to it,
         * in order for us to make a distinction between wrapped/non-wrapped functions possible.
         * If a function was wrapped, it has additional property of `__sentry_wrapped__`, holding the handler.
         *
         * When someone adds a handler prior to initialization, and then do it again, but after,
         * then we have to detach both of them. Otherwise, if we'd detach only wrapped one, it'd be impossible
         * to get rid of the initial handler and it'd stick there forever.
         */
        var wrappedEventHandler = fn ;
        try {
          var originalEventHandler = wrappedEventHandler && wrappedEventHandler.__sentry_wrapped__;
          if (originalEventHandler) {
            originalRemoveEventListener.call(this, eventName, originalEventHandler, options);
          }
        } catch (e) {
          // ignore, accessing __sentry_wrapped__ will throw in some Selenium environments
        }
        return originalRemoveEventListener.call(this, eventName, wrappedEventHandler, options);
      };
    },
  );
}


//# sourceMappingURL=trycatch.js.map


/***/ }),
/* 153 */
/***/ (function(module, __webpack_exports__, __webpack_require__) {

"use strict";
__webpack_require__.r(__webpack_exports__);
/* harmony export (binding) */ __webpack_require__.d(__webpack_exports__, "LinkedErrors", function() { return LinkedErrors; });
/* harmony export (binding) */ __webpack_require__.d(__webpack_exports__, "_handler", function() { return _handler; });
/* harmony export (binding) */ __webpack_require__.d(__webpack_exports__, "_walkErrorTree", function() { return _walkErrorTree; });
/* harmony import */ var _sentry_core__WEBPACK_IMPORTED_MODULE_0__ = __webpack_require__(79);
/* harmony import */ var _sentry_utils__WEBPACK_IMPORTED_MODULE_1__ = __webpack_require__(82);
/* harmony import */ var _eventbuilder_js__WEBPACK_IMPORTED_MODULE_2__ = __webpack_require__(141);




var DEFAULT_KEY = 'cause';
var DEFAULT_LIMIT = 5;

/** Adds SDK info to an event. */
class LinkedErrors  {
  /**
   * @inheritDoc
   */
   static __initStatic() {this.id = 'LinkedErrors';}

  /**
   * @inheritDoc
   */
    __init() {this.name = LinkedErrors.id;}

  /**
   * @inheritDoc
   */
  

  /**
   * @inheritDoc
   */
  

  /**
   * @inheritDoc
   */
   constructor(options = {}) {;LinkedErrors.prototype.__init.call(this);
    this._key = options.key || DEFAULT_KEY;
    this._limit = options.limit || DEFAULT_LIMIT;
  }

  /**
   * @inheritDoc
   */
   setupOnce() {
    var client = Object(_sentry_core__WEBPACK_IMPORTED_MODULE_0__["getCurrentHub"])().getClient();
    if (!client) {
      return;
    }
    Object(_sentry_core__WEBPACK_IMPORTED_MODULE_0__["addGlobalEventProcessor"])((event, hint) => {
      var self = Object(_sentry_core__WEBPACK_IMPORTED_MODULE_0__["getCurrentHub"])().getIntegration(LinkedErrors);
      return self ? _handler(client.getOptions().stackParser, self._key, self._limit, event, hint) : event;
    });
  }
} LinkedErrors.__initStatic();

/**
 * @inheritDoc
 */
function _handler(
  parser,
  key,
  limit,
  event,
  hint,
) {
  if (!event.exception || !event.exception.values || !hint || !Object(_sentry_utils__WEBPACK_IMPORTED_MODULE_1__["isInstanceOf"])(hint.originalException, Error)) {
    return event;
  }
  var linkedErrors = _walkErrorTree(parser, limit, hint.originalException , key);
  event.exception.values = [...linkedErrors, ...event.exception.values];
  return event;
}

/**
 * JSDOC
 */
function _walkErrorTree(
  parser,
  limit,
  error,
  key,
  stack = [],
) {
  if (!Object(_sentry_utils__WEBPACK_IMPORTED_MODULE_1__["isInstanceOf"])(error[key], Error) || stack.length + 1 >= limit) {
    return stack;
  }
  var exception = Object(_eventbuilder_js__WEBPACK_IMPORTED_MODULE_2__["exceptionFromError"])(parser, error[key]);
  return _walkErrorTree(parser, limit, error[key], key, [exception, ...stack]);
}


//# sourceMappingURL=linkederrors.js.map


/***/ }),
/* 154 */
/***/ (function(module, __webpack_exports__, __webpack_require__) {

"use strict";
__webpack_require__.r(__webpack_exports__);
/* harmony export (binding) */ __webpack_require__.d(__webpack_exports__, "HttpContext", function() { return HttpContext; });
/* harmony import */ var _sentry_core__WEBPACK_IMPORTED_MODULE_0__ = __webpack_require__(79);
/* harmony import */ var _sentry_utils__WEBPACK_IMPORTED_MODULE_1__ = __webpack_require__(82);



var global = Object(_sentry_utils__WEBPACK_IMPORTED_MODULE_1__["getGlobalObject"])();

/** HttpContext integration collects information about HTTP request headers */
class HttpContext  {constructor() { HttpContext.prototype.__init.call(this); }
  /**
   * @inheritDoc
   */
   static __initStatic() {this.id = 'HttpContext';}

  /**
   * @inheritDoc
   */
   __init() {this.name = HttpContext.id;}

  /**
   * @inheritDoc
   */
   setupOnce() {
    Object(_sentry_core__WEBPACK_IMPORTED_MODULE_0__["addGlobalEventProcessor"])((event) => {
      if (Object(_sentry_core__WEBPACK_IMPORTED_MODULE_0__["getCurrentHub"])().getIntegration(HttpContext)) {
        // if none of the information we want exists, don't bother
        if (!global.navigator && !global.location && !global.document) {
          return event;
        }

        // grab as much info as exists and add it to the event
        var url = (event.request && event.request.url) || (global.location && global.location.href);
        const { referrer } = global.document || {};
        const { userAgent } = global.navigator || {};

        var headers = {
          ...(event.request && event.request.headers),
          ...(referrer && { Referer: referrer }),
          ...(userAgent && { 'User-Agent': userAgent }),
        };
        var request = { ...(url && { url }), headers };

        return { ...event, request };
      }
      return event;
    });
  }
} HttpContext.__initStatic();


//# sourceMappingURL=httpcontext.js.map


/***/ }),
/* 155 */
/***/ (function(module, __webpack_exports__, __webpack_require__) {

"use strict";
__webpack_require__.r(__webpack_exports__);
/* harmony export (binding) */ __webpack_require__.d(__webpack_exports__, "Dedupe", function() { return Dedupe; });
/* harmony import */ var _sentry_utils__WEBPACK_IMPORTED_MODULE_0__ = __webpack_require__(82);


/** Deduplication filter */
class Dedupe  {constructor() { Dedupe.prototype.__init.call(this); }
  /**
   * @inheritDoc
   */
   static __initStatic() {this.id = 'Dedupe';}

  /**
   * @inheritDoc
   */
   __init() {this.name = Dedupe.id;}

  /**
   * @inheritDoc
   */
  

  /**
   * @inheritDoc
   */
   setupOnce(addGlobalEventProcessor, getCurrentHub) {
    var eventProcessor = currentEvent => {
      var self = getCurrentHub().getIntegration(Dedupe);
      if (self) {
        // Juuust in case something goes wrong
        try {
          if (_shouldDropEvent(currentEvent, self._previousEvent)) {
            (typeof __SENTRY_DEBUG__ === 'undefined' || __SENTRY_DEBUG__) && _sentry_utils__WEBPACK_IMPORTED_MODULE_0__["logger"].warn('Event dropped due to being a duplicate of previously captured event.');
            return null;
          }
        } catch (_oO) {
          return (self._previousEvent = currentEvent);
        }

        return (self._previousEvent = currentEvent);
      }
      return currentEvent;
    };

    eventProcessor.id = this.name;
    addGlobalEventProcessor(eventProcessor);
  }
} Dedupe.__initStatic();

/** JSDoc */
function _shouldDropEvent(currentEvent, previousEvent) {
  if (!previousEvent) {
    return false;
  }

  if (_isSameMessageEvent(currentEvent, previousEvent)) {
    return true;
  }

  if (_isSameExceptionEvent(currentEvent, previousEvent)) {
    return true;
  }

  return false;
}

/** JSDoc */
function _isSameMessageEvent(currentEvent, previousEvent) {
  var currentMessage = currentEvent.message;
  var previousMessage = previousEvent.message;

  // If neither event has a message property, they were both exceptions, so bail out
  if (!currentMessage && !previousMessage) {
    return false;
  }

  // If only one event has a stacktrace, but not the other one, they are not the same
  if ((currentMessage && !previousMessage) || (!currentMessage && previousMessage)) {
    return false;
  }

  if (currentMessage !== previousMessage) {
    return false;
  }

  if (!_isSameFingerprint(currentEvent, previousEvent)) {
    return false;
  }

  if (!_isSameStacktrace(currentEvent, previousEvent)) {
    return false;
  }

  return true;
}

/** JSDoc */
function _isSameExceptionEvent(currentEvent, previousEvent) {
  var previousException = _getExceptionFromEvent(previousEvent);
  var currentException = _getExceptionFromEvent(currentEvent);

  if (!previousException || !currentException) {
    return false;
  }

  if (previousException.type !== currentException.type || previousException.value !== currentException.value) {
    return false;
  }

  if (!_isSameFingerprint(currentEvent, previousEvent)) {
    return false;
  }

  if (!_isSameStacktrace(currentEvent, previousEvent)) {
    return false;
  }

  return true;
}

/** JSDoc */
function _isSameStacktrace(currentEvent, previousEvent) {
  let currentFrames = _getFramesFromEvent(currentEvent);
  let previousFrames = _getFramesFromEvent(previousEvent);

  // If neither event has a stacktrace, they are assumed to be the same
  if (!currentFrames && !previousFrames) {
    return true;
  }

  // If only one event has a stacktrace, but not the other one, they are not the same
  if ((currentFrames && !previousFrames) || (!currentFrames && previousFrames)) {
    return false;
  }

  currentFrames = currentFrames ;
  previousFrames = previousFrames ;

  // If number of frames differ, they are not the same
  if (previousFrames.length !== currentFrames.length) {
    return false;
  }

  // Otherwise, compare the two
  for (let i = 0; i < previousFrames.length; i++) {
    var frameA = previousFrames[i];
    var frameB = currentFrames[i];

    if (
      frameA.filename !== frameB.filename ||
      frameA.lineno !== frameB.lineno ||
      frameA.colno !== frameB.colno ||
      frameA.function !== frameB.function
    ) {
      return false;
    }
  }

  return true;
}

/** JSDoc */
function _isSameFingerprint(currentEvent, previousEvent) {
  let currentFingerprint = currentEvent.fingerprint;
  let previousFingerprint = previousEvent.fingerprint;

  // If neither event has a fingerprint, they are assumed to be the same
  if (!currentFingerprint && !previousFingerprint) {
    return true;
  }

  // If only one event has a fingerprint, but not the other one, they are not the same
  if ((currentFingerprint && !previousFingerprint) || (!currentFingerprint && previousFingerprint)) {
    return false;
  }

  currentFingerprint = currentFingerprint ;
  previousFingerprint = previousFingerprint ;

  // Otherwise, compare the two
  try {
    return !!(currentFingerprint.join('') === previousFingerprint.join(''));
  } catch (_oO) {
    return false;
  }
}

/** JSDoc */
function _getExceptionFromEvent(event) {
  return event.exception && event.exception.values && event.exception.values[0];
}

/** JSDoc */
function _getFramesFromEvent(event) {
  var exception = event.exception;

  if (exception) {
    try {
      // @ts-ignore Object could be undefined
      return exception.values[0].stacktrace.frames;
    } catch (_oO) {
      return undefined;
    }
  }
  return undefined;
}


//# sourceMappingURL=dedupe.js.map


/***/ }),
/* 156 */
/***/ (function(module, exports, __webpack_require__) {

var __WEBPACK_AMD_DEFINE_RESULT__;;(function () {
	'use strict';

	/**
	 * @preserve FastClick: polyfill to remove click delays on browsers with touch UIs.
	 *
	 * @codingstandard ftlabs-jsv2
	 * @copyright The Financial Times Limited [All Rights Reserved]
	 * @license MIT License (see LICENSE.txt)
	 */

	/*jslint browser:true, node:true*/
	/*global define, Event, Node*/


	/**
	 * Instantiate fast-clicking listeners on the specified layer.
	 *
	 * @constructor
	 * @param {Element} layer The layer to listen on
	 * @param {Object} [options={}] The options to override the defaults
	 */
	function FastClick(layer, options) {
		var oldOnClick;

		options = options || {};

		/**
		 * Whether a click is currently being tracked.
		 *
		 * @type boolean
		 */
		this.trackingClick = false;


		/**
		 * Timestamp for when click tracking started.
		 *
		 * @type number
		 */
		this.trackingClickStart = 0;


		/**
		 * The element being tracked for a click.
		 *
		 * @type EventTarget
		 */
		this.targetElement = null;


		/**
		 * X-coordinate of touch start event.
		 *
		 * @type number
		 */
		this.touchStartX = 0;


		/**
		 * Y-coordinate of touch start event.
		 *
		 * @type number
		 */
		this.touchStartY = 0;


		/**
		 * ID of the last touch, retrieved from Touch.identifier.
		 *
		 * @type number
		 */
		this.lastTouchIdentifier = 0;


		/**
		 * Touchmove boundary, beyond which a click will be cancelled.
		 *
		 * @type number
		 */
		this.touchBoundary = options.touchBoundary || 10;


		/**
		 * The FastClick layer.
		 *
		 * @type Element
		 */
		this.layer = layer;

		/**
		 * The minimum time between tap(touchstart and touchend) events
		 *
		 * @type number
		 */
		this.tapDelay = options.tapDelay || 200;

		/**
		 * The maximum time for a tap
		 *
		 * @type number
		 */
		this.tapTimeout = options.tapTimeout || 700;

		if (FastClick.notNeeded(layer)) {
			return;
		}

		// Some old versions of Android don't have Function.prototype.bind
		function bind(method, context) {
			return function() { return method.apply(context, arguments); };
		}


		var methods = ['onMouse', 'onClick', 'onTouchStart', 'onTouchMove', 'onTouchEnd', 'onTouchCancel'];
		var context = this;
		for (var i = 0, l = methods.length; i < l; i++) {
			context[methods[i]] = bind(context[methods[i]], context);
		}

		// Set up event handlers as required
		if (deviceIsAndroid) {
			layer.addEventListener('mouseover', this.onMouse, true);
			layer.addEventListener('mousedown', this.onMouse, true);
			layer.addEventListener('mouseup', this.onMouse, true);
		}

		layer.addEventListener('click', this.onClick, true);
		layer.addEventListener('touchstart', this.onTouchStart, false);
		layer.addEventListener('touchmove', this.onTouchMove, false);
		layer.addEventListener('touchend', this.onTouchEnd, false);
		layer.addEventListener('touchcancel', this.onTouchCancel, false);

		// Hack is required for browsers that don't support Event#stopImmediatePropagation (e.g. Android 2)
		// which is how FastClick normally stops click events bubbling to callbacks registered on the FastClick
		// layer when they are cancelled.
		if (!Event.prototype.stopImmediatePropagation) {
			layer.removeEventListener = function(type, callback, capture) {
				var rmv = Node.prototype.removeEventListener;
				if (type === 'click') {
					rmv.call(layer, type, callback.hijacked || callback, capture);
				} else {
					rmv.call(layer, type, callback, capture);
				}
			};

			layer.addEventListener = function(type, callback, capture) {
				var adv = Node.prototype.addEventListener;
				if (type === 'click') {
					adv.call(layer, type, callback.hijacked || (callback.hijacked = function(event) {
						if (!event.propagationStopped) {
							callback(event);
						}
					}), capture);
				} else {
					adv.call(layer, type, callback, capture);
				}
			};
		}

		// If a handler is already declared in the element's onclick attribute, it will be fired before
		// FastClick's onClick handler. Fix this by pulling out the user-defined handler function and
		// adding it as listener.
		if (typeof layer.onclick === 'function') {

			// Android browser on at least 3.2 requires a new reference to the function in layer.onclick
			// - the old one won't work if passed to addEventListener directly.
			oldOnClick = layer.onclick;
			layer.addEventListener('click', function(event) {
				oldOnClick(event);
			}, false);
			layer.onclick = null;
		}
	}

	/**
	* Windows Phone 8.1 fakes user agent string to look like Android and iPhone.
	*
	* @type boolean
	*/
	var deviceIsWindowsPhone = navigator.userAgent.indexOf("Windows Phone") >= 0;

	/**
	 * Android requires exceptions.
	 *
	 * @type boolean
	 */
	var deviceIsAndroid = navigator.userAgent.indexOf('Android') > 0 && !deviceIsWindowsPhone;


	/**
	 * iOS requires exceptions.
	 *
	 * @type boolean
	 */
	var deviceIsIOS = /iP(ad|hone|od)/.test(navigator.userAgent) && !deviceIsWindowsPhone;


	/**
	 * iOS 4 requires an exception for select elements.
	 *
	 * @type boolean
	 */
	var deviceIsIOS4 = deviceIsIOS && (/OS 4_\d(_\d)?/).test(navigator.userAgent);


	/**
	 * iOS 6.0-7.* requires the target element to be manually derived
	 *
	 * @type boolean
	 */
	var deviceIsIOSWithBadTarget = deviceIsIOS && (/OS [6-7]_\d/).test(navigator.userAgent);

	/**
	 * BlackBerry requires exceptions.
	 *
	 * @type boolean
	 */
	var deviceIsBlackBerry10 = navigator.userAgent.indexOf('BB10') > 0;

	/**
	 * Determine whether a given element requires a native click.
	 *
	 * @param {EventTarget|Element} target Target DOM element
	 * @returns {boolean} Returns true if the element needs a native click
	 */
	FastClick.prototype.needsClick = function(target) {
		switch (target.nodeName.toLowerCase()) {

		// Don't send a synthetic click to disabled inputs (issue #62)
		case 'button':
		case 'select':
		case 'textarea':
			if (target.disabled) {
				return true;
			}

			break;
		case 'input':

			// File inputs need real clicks on iOS 6 due to a browser bug (issue #68)
			if ((deviceIsIOS && target.type === 'file') || target.disabled) {
				return true;
			}

			break;
		case 'label':
		case 'iframe': // iOS8 homescreen apps can prevent events bubbling into frames
		case 'video':
			return true;
		}

		return (/\bneedsclick\b/).test(target.className);
	};


	/**
	 * Determine whether a given element requires a call to focus to simulate click into element.
	 *
	 * @param {EventTarget|Element} target Target DOM element
	 * @returns {boolean} Returns true if the element requires a call to focus to simulate native click.
	 */
	FastClick.prototype.needsFocus = function(target) {
		switch (target.nodeName.toLowerCase()) {
		case 'textarea':
			return true;
		case 'select':
			return !deviceIsAndroid;
		case 'input':
			switch (target.type) {
			case 'button':
			case 'checkbox':
			case 'file':
			case 'image':
			case 'radio':
			case 'submit':
				return false;
			}

			// No point in attempting to focus disabled inputs
			return !target.disabled && !target.readOnly;
		default:
			return (/\bneedsfocus\b/).test(target.className);
		}
	};


	/**
	 * Send a click event to the specified element.
	 *
	 * @param {EventTarget|Element} targetElement
	 * @param {Event} event
	 */
	FastClick.prototype.sendClick = function(targetElement, event) {
		var clickEvent, touch;

		// On some Android devices activeElement needs to be blurred otherwise the synthetic click will have no effect (#24)
		if (document.activeElement && document.activeElement !== targetElement) {
			document.activeElement.blur();
		}

		touch = event.changedTouches[0];

		// Synthesise a click event, with an extra attribute so it can be tracked
		clickEvent = document.createEvent('MouseEvents');
		clickEvent.initMouseEvent(this.determineEventType(targetElement), true, true, window, 1, touch.screenX, touch.screenY, touch.clientX, touch.clientY, false, false, false, false, 0, null);
		clickEvent.forwardedTouchEvent = true;
		targetElement.dispatchEvent(clickEvent);
	};

	FastClick.prototype.determineEventType = function(targetElement) {

		//Issue #159: Android Chrome Select Box does not open with a synthetic click event
		if (deviceIsAndroid && targetElement.tagName.toLowerCase() === 'select') {
			return 'mousedown';
		}

		return 'click';
	};


	/**
	 * @param {EventTarget|Element} targetElement
	 */
	FastClick.prototype.focus = function(targetElement) {
		var length;

		// Issue #160: on iOS 7, some input elements (e.g. date datetime month) throw a vague TypeError on setSelectionRange. These elements don't have an integer value for the selectionStart and selectionEnd properties, but unfortunately that can't be used for detection because accessing the properties also throws a TypeError. Just check the type instead. Filed as Apple bug #15122724.
		if (deviceIsIOS && targetElement.setSelectionRange && targetElement.type.indexOf('date') !== 0 && targetElement.type !== 'time' && targetElement.type !== 'month') {
			length = targetElement.value.length;
			targetElement.setSelectionRange(length, length);
		} else {
			targetElement.focus();
		}
	};


	/**
	 * Check whether the given target element is a child of a scrollable layer and if so, set a flag on it.
	 *
	 * @param {EventTarget|Element} targetElement
	 */
	FastClick.prototype.updateScrollParent = function(targetElement) {
		var scrollParent, parentElement;

		scrollParent = targetElement.fastClickScrollParent;

		// Attempt to discover whether the target element is contained within a scrollable layer. Re-check if the
		// target element was moved to another parent.
		if (!scrollParent || !scrollParent.contains(targetElement)) {
			parentElement = targetElement;
			do {
				if (parentElement.scrollHeight > parentElement.offsetHeight) {
					scrollParent = parentElement;
					targetElement.fastClickScrollParent = parentElement;
					break;
				}

				parentElement = parentElement.parentElement;
			} while (parentElement);
		}

		// Always update the scroll top tracker if possible.
		if (scrollParent) {
			scrollParent.fastClickLastScrollTop = scrollParent.scrollTop;
		}
	};


	/**
	 * @param {EventTarget} targetElement
	 * @returns {Element|EventTarget}
	 */
	FastClick.prototype.getTargetElementFromEventTarget = function(eventTarget) {

		// On some older browsers (notably Safari on iOS 4.1 - see issue #56) the event target may be a text node.
		if (eventTarget.nodeType === Node.TEXT_NODE) {
			return eventTarget.parentNode;
		}

		return eventTarget;
	};


	/**
	 * On touch start, record the position and scroll offset.
	 *
	 * @param {Event} event
	 * @returns {boolean}
	 */
	FastClick.prototype.onTouchStart = function(event) {
		var targetElement, touch, selection;

		// Ignore multiple touches, otherwise pinch-to-zoom is prevented if both fingers are on the FastClick element (issue #111).
		if (event.targetTouches.length > 1) {
			return true;
		}

		targetElement = this.getTargetElementFromEventTarget(event.target);
		touch = event.targetTouches[0];

		if (deviceIsIOS) {

			// Only trusted events will deselect text on iOS (issue #49)
			selection = window.getSelection();
			if (selection.rangeCount && !selection.isCollapsed) {
				return true;
			}

			if (!deviceIsIOS4) {

				// Weird things happen on iOS when an alert or confirm dialog is opened from a click event callback (issue #23):
				// when the user next taps anywhere else on the page, new touchstart and touchend events are dispatched
				// with the same identifier as the touch event that previously triggered the click that triggered the alert.
				// Sadly, there is an issue on iOS 4 that causes some normal touch events to have the same identifier as an
				// immediately preceeding touch event (issue #52), so this fix is unavailable on that platform.
				// Issue 120: touch.identifier is 0 when Chrome dev tools 'Emulate touch events' is set with an iOS device UA string,
				// which causes all touch events to be ignored. As this block only applies to iOS, and iOS identifiers are always long,
				// random integers, it's safe to to continue if the identifier is 0 here.
				if (touch.identifier && touch.identifier === this.lastTouchIdentifier) {
					event.preventDefault();
					return false;
				}

				this.lastTouchIdentifier = touch.identifier;

				// If the target element is a child of a scrollable layer (using -webkit-overflow-scrolling: touch) and:
				// 1) the user does a fling scroll on the scrollable layer
				// 2) the user stops the fling scroll with another tap
				// then the event.target of the last 'touchend' event will be the element that was under the user's finger
				// when the fling scroll was started, causing FastClick to send a click event to that layer - unless a check
				// is made to ensure that a parent layer was not scrolled before sending a synthetic click (issue #42).
				this.updateScrollParent(targetElement);
			}
		}

		this.trackingClick = true;
		this.trackingClickStart = event.timeStamp;
		this.targetElement = targetElement;

		this.touchStartX = touch.pageX;
		this.touchStartY = touch.pageY;

		// Prevent phantom clicks on fast double-tap (issue #36)
		if ((event.timeStamp - this.lastClickTime) < this.tapDelay) {
			event.preventDefault();
		}

		return true;
	};


	/**
	 * Based on a touchmove event object, check whether the touch has moved past a boundary since it started.
	 *
	 * @param {Event} event
	 * @returns {boolean}
	 */
	FastClick.prototype.touchHasMoved = function(event) {
		var touch = event.changedTouches[0], boundary = this.touchBoundary;

		if (Math.abs(touch.pageX - this.touchStartX) > boundary || Math.abs(touch.pageY - this.touchStartY) > boundary) {
			return true;
		}

		return false;
	};


	/**
	 * Update the last position.
	 *
	 * @param {Event} event
	 * @returns {boolean}
	 */
	FastClick.prototype.onTouchMove = function(event) {
		if (!this.trackingClick) {
			return true;
		}

		// If the touch has moved, cancel the click tracking
		if (this.targetElement !== this.getTargetElementFromEventTarget(event.target) || this.touchHasMoved(event)) {
			this.trackingClick = false;
			this.targetElement = null;
		}

		return true;
	};


	/**
	 * Attempt to find the labelled control for the given label element.
	 *
	 * @param {EventTarget|HTMLLabelElement} labelElement
	 * @returns {Element|null}
	 */
	FastClick.prototype.findControl = function(labelElement) {

		// Fast path for newer browsers supporting the HTML5 control attribute
		if (labelElement.control !== undefined) {
			return labelElement.control;
		}

		// All browsers under test that support touch events also support the HTML5 htmlFor attribute
		if (labelElement.htmlFor) {
			return document.getElementById(labelElement.htmlFor);
		}

		// If no for attribute exists, attempt to retrieve the first labellable descendant element
		// the list of which is defined here: http://www.w3.org/TR/html5/forms.html#category-label
		return labelElement.querySelector('button, input:not([type=hidden]), keygen, meter, output, progress, select, textarea');
	};


	/**
	 * On touch end, determine whether to send a click event at once.
	 *
	 * @param {Event} event
	 * @returns {boolean}
	 */
	FastClick.prototype.onTouchEnd = function(event) {
		var forElement, trackingClickStart, targetTagName, scrollParent, touch, targetElement = this.targetElement;

		if (!this.trackingClick) {
			return true;
		}

		// Prevent phantom clicks on fast double-tap (issue #36)
		if ((event.timeStamp - this.lastClickTime) < this.tapDelay) {
			this.cancelNextClick = true;
			return true;
		}

		if ((event.timeStamp - this.trackingClickStart) > this.tapTimeout) {
			return true;
		}

		// Reset to prevent wrong click cancel on input (issue #156).
		this.cancelNextClick = false;

		this.lastClickTime = event.timeStamp;

		trackingClickStart = this.trackingClickStart;
		this.trackingClick = false;
		this.trackingClickStart = 0;

		// On some iOS devices, the targetElement supplied with the event is invalid if the layer
		// is performing a transition or scroll, and has to be re-detected manually. Note that
		// for this to function correctly, it must be called *after* the event target is checked!
		// See issue #57; also filed as rdar://13048589 .
		if (deviceIsIOSWithBadTarget) {
			touch = event.changedTouches[0];

			// In certain cases arguments of elementFromPoint can be negative, so prevent setting targetElement to null
			targetElement = document.elementFromPoint(touch.pageX - window.pageXOffset, touch.pageY - window.pageYOffset) || targetElement;
			targetElement.fastClickScrollParent = this.targetElement.fastClickScrollParent;
		}

		targetTagName = targetElement.tagName.toLowerCase();
		if (targetTagName === 'label') {
			forElement = this.findControl(targetElement);
			if (forElement) {
				this.focus(targetElement);
				if (deviceIsAndroid) {
					return false;
				}

				targetElement = forElement;
			}
		} else if (this.needsFocus(targetElement)) {

			// Case 1: If the touch started a while ago (best guess is 100ms based on tests for issue #36) then focus will be triggered anyway. Return early and unset the target element reference so that the subsequent click will be allowed through.
			// Case 2: Without this exception for input elements tapped when the document is contained in an iframe, then any inputted text won't be visible even though the value attribute is updated as the user types (issue #37).
			if ((event.timeStamp - trackingClickStart) > 100 || (deviceIsIOS && window.top !== window && targetTagName === 'input')) {
				this.targetElement = null;
				return false;
			}

			this.focus(targetElement);
			this.sendClick(targetElement, event);

			// Select elements need the event to go through on iOS 4, otherwise the selector menu won't open.
			// Also this breaks opening selects when VoiceOver is active on iOS6, iOS7 (and possibly others)
			if (!deviceIsIOS || targetTagName !== 'select') {
				this.targetElement = null;
				event.preventDefault();
			}

			return false;
		}

		if (deviceIsIOS && !deviceIsIOS4) {

			// Don't send a synthetic click event if the target element is contained within a parent layer that was scrolled
			// and this tap is being used to stop the scrolling (usually initiated by a fling - issue #42).
			scrollParent = targetElement.fastClickScrollParent;
			if (scrollParent && scrollParent.fastClickLastScrollTop !== scrollParent.scrollTop) {
				return true;
			}
		}

		// Prevent the actual click from going though - unless the target node is marked as requiring
		// real clicks or if it is in the whitelist in which case only non-programmatic clicks are permitted.
		if (!this.needsClick(targetElement)) {
			event.preventDefault();
			this.sendClick(targetElement, event);
		}

		return false;
	};


	/**
	 * On touch cancel, stop tracking the click.
	 *
	 * @returns {void}
	 */
	FastClick.prototype.onTouchCancel = function() {
		this.trackingClick = false;
		this.targetElement = null;
	};


	/**
	 * Determine mouse events which should be permitted.
	 *
	 * @param {Event} event
	 * @returns {boolean}
	 */
	FastClick.prototype.onMouse = function(event) {

		// If a target element was never set (because a touch event was never fired) allow the event
		if (!this.targetElement) {
			return true;
		}

		if (event.forwardedTouchEvent) {
			return true;
		}

		// Programmatically generated events targeting a specific element should be permitted
		if (!event.cancelable) {
			return true;
		}

		// Derive and check the target element to see whether the mouse event needs to be permitted;
		// unless explicitly enabled, prevent non-touch click events from triggering actions,
		// to prevent ghost/doubleclicks.
		if (!this.needsClick(this.targetElement) || this.cancelNextClick) {

			// Prevent any user-added listeners declared on FastClick element from being fired.
			if (event.stopImmediatePropagation) {
				event.stopImmediatePropagation();
			} else {

				// Part of the hack for browsers that don't support Event#stopImmediatePropagation (e.g. Android 2)
				event.propagationStopped = true;
			}

			// Cancel the event
			event.stopPropagation();
			event.preventDefault();

			return false;
		}

		// If the mouse event is permitted, return true for the action to go through.
		return true;
	};


	/**
	 * On actual clicks, determine whether this is a touch-generated click, a click action occurring
	 * naturally after a delay after a touch (which needs to be cancelled to avoid duplication), or
	 * an actual click which should be permitted.
	 *
	 * @param {Event} event
	 * @returns {boolean}
	 */
	FastClick.prototype.onClick = function(event) {
		var permitted;

		// It's possible for another FastClick-like library delivered with third-party code to fire a click event before FastClick does (issue #44). In that case, set the click-tracking flag back to false and return early. This will cause onTouchEnd to return early.
		if (this.trackingClick) {
			this.targetElement = null;
			this.trackingClick = false;
			return true;
		}

		// Very odd behaviour on iOS (issue #18): if a submit element is present inside a form and the user hits enter in the iOS simulator or clicks the Go button on the pop-up OS keyboard the a kind of 'fake' click event will be triggered with the submit-type input element as the target.
		if (event.target.type === 'submit' && event.detail === 0) {
			return true;
		}

		permitted = this.onMouse(event);

		// Only unset targetElement if the click is not permitted. This will ensure that the check for !targetElement in onMouse fails and the browser's click doesn't go through.
		if (!permitted) {
			this.targetElement = null;
		}

		// If clicks are permitted, return true for the action to go through.
		return permitted;
	};


	/**
	 * Remove all FastClick's event listeners.
	 *
	 * @returns {void}
	 */
	FastClick.prototype.destroy = function() {
		var layer = this.layer;

		if (deviceIsAndroid) {
			layer.removeEventListener('mouseover', this.onMouse, true);
			layer.removeEventListener('mousedown', this.onMouse, true);
			layer.removeEventListener('mouseup', this.onMouse, true);
		}

		layer.removeEventListener('click', this.onClick, true);
		layer.removeEventListener('touchstart', this.onTouchStart, false);
		layer.removeEventListener('touchmove', this.onTouchMove, false);
		layer.removeEventListener('touchend', this.onTouchEnd, false);
		layer.removeEventListener('touchcancel', this.onTouchCancel, false);
	};


	/**
	 * Check whether FastClick is needed.
	 *
	 * @param {Element} layer The layer to listen on
	 */
	FastClick.notNeeded = function(layer) {
		var metaViewport;
		var chromeVersion;
		var blackberryVersion;
		var firefoxVersion;

		// Devices that don't support touch don't need FastClick
		if (typeof window.ontouchstart === 'undefined') {
			return true;
		}

		// Chrome version - zero for other browsers
		chromeVersion = +(/Chrome\/([0-9]+)/.exec(navigator.userAgent) || [,0])[1];

		if (chromeVersion) {

			if (deviceIsAndroid) {
				metaViewport = document.querySelector('meta[name=viewport]');

				if (metaViewport) {
					// Chrome on Android with user-scalable="no" doesn't need FastClick (issue #89)
					if (metaViewport.content.indexOf('user-scalable=no') !== -1) {
						return true;
					}
					// Chrome 32 and above with width=device-width or less don't need FastClick
					if (chromeVersion > 31 && document.documentElement.scrollWidth <= window.outerWidth) {
						return true;
					}
				}

			// Chrome desktop doesn't need FastClick (issue #15)
			} else {
				return true;
			}
		}

		if (deviceIsBlackBerry10) {
			blackberryVersion = navigator.userAgent.match(/Version\/([0-9]*)\.([0-9]*)/);

			// BlackBerry 10.3+ does not require Fastclick library.
			// https://github.com/ftlabs/fastclick/issues/251
			if (blackberryVersion[1] >= 10 && blackberryVersion[2] >= 3) {
				metaViewport = document.querySelector('meta[name=viewport]');

				if (metaViewport) {
					// user-scalable=no eliminates click delay.
					if (metaViewport.content.indexOf('user-scalable=no') !== -1) {
						return true;
					}
					// width=device-width (or less than device-width) eliminates click delay.
					if (document.documentElement.scrollWidth <= window.outerWidth) {
						return true;
					}
				}
			}
		}

		// IE10 with -ms-touch-action: none or manipulation, which disables double-tap-to-zoom (issue #97)
		if (layer.style.msTouchAction === 'none' || layer.style.touchAction === 'manipulation') {
			return true;
		}

		// Firefox version - zero for other browsers
		firefoxVersion = +(/Firefox\/([0-9]+)/.exec(navigator.userAgent) || [,0])[1];

		if (firefoxVersion >= 27) {
			// Firefox 27+ does not have tap delay if the content is not zoomable - https://bugzilla.mozilla.org/show_bug.cgi?id=922896

			metaViewport = document.querySelector('meta[name=viewport]');
			if (metaViewport && (metaViewport.content.indexOf('user-scalable=no') !== -1 || document.documentElement.scrollWidth <= window.outerWidth)) {
				return true;
			}
		}

		// IE11: prefixed -ms-touch-action is no longer supported and it's recomended to use non-prefixed version
		// http://msdn.microsoft.com/en-us/library/windows/apps/Hh767313.aspx
		if (layer.style.touchAction === 'none' || layer.style.touchAction === 'manipulation') {
			return true;
		}

		return false;
	};


	/**
	 * Factory method for creating a FastClick object
	 *
	 * @param {Element} layer The layer to listen on
	 * @param {Object} [options={}] The options to override the defaults
	 */
	FastClick.attach = function(layer, options) {
		return new FastClick(layer, options);
	};


	if (true) {

		// AMD. Register as an anonymous module.
		!(__WEBPACK_AMD_DEFINE_RESULT__ = (function() {
			return FastClick;
		}).call(exports, __webpack_require__, exports, module),
				__WEBPACK_AMD_DEFINE_RESULT__ !== undefined && (module.exports = __WEBPACK_AMD_DEFINE_RESULT__));
	} else {}
}());


/***/ }),
/* 157 */
/***/ (function(module, __webpack_exports__, __webpack_require__) {

"use strict";
__webpack_require__.r(__webpack_exports__);
/* WEBPACK VAR INJECTION */(function($, __webpack_provided_window_dot_jQuery, jQuery) {/* harmony export (binding) */ __webpack_require__.d(__webpack_exports__, "resolve", function() { return resolve; });
/* harmony export (binding) */ __webpack_require__.d(__webpack_exports__, "airbrake", function() { return airbrake; });
/* harmony export (binding) */ __webpack_require__.d(__webpack_exports__, "init", function() { return init; });
var airbrakeJs = __webpack_require__(158);

var airbrakeJs_instrumentation_jquery = __webpack_require__(169);

function resolve(error_id) {
  $.ajax({
    type: 'POST',
    url: '/manage/errors/resolve',
    data: {
      'error_id': error_id
    }
  });
}
var airbrake = undefined;
function init() {
  airbrake = new airbrakeJs({
    reporter: 'xhr',
    host: '/errors/new?'
  });
  window.onerror = airbrake.onerror; // in debug mode, monkey-patch airbrake.notify() to log the error to the console

  if (typeof settings !== 'undefined' && settings.DEBUG) {
    airbrake.notify = function (err) {
      console.error(err.error ? err.error.stack : err);
      return this.__proto__.notify.apply(this, arguments); // call real notify() method
    };
  } // add listener for jquery errors


  if (__webpack_provided_window_dot_jQuery) {
    airbrakeJs_instrumentation_jquery(airbrake, jQuery);
  }
}
/* WEBPACK VAR INJECTION */}.call(this, __webpack_require__(58), __webpack_require__(58), __webpack_require__(58)))

/***/ }),
/* 158 */
/***/ (function(module, exports, __webpack_require__) {

/* WEBPACK VAR INJECTION */(function(global) {(function() {
  var Client, Promise, makeOnErrorHandler, merge;

  __webpack_require__(159);

  merge = __webpack_require__(160);

  Promise = __webpack_require__(161);

  makeOnErrorHandler = function(notifier) {
    return function(message, file, line, column, error) {
      if (error) {
        return notifier.notify(error);
      } else {
        return notifier.notify({
          error: {
            message: message,
            fileName: file,
            lineNumber: line,
            columnNumber: column || 0
          }
        });
      }
    };
  };

  Client = (function() {
    function Client(opts) {
      var reporter;
      if (opts == null) {
        opts = {};
      }
      this._projectId = opts.projectId || 0;
      this._projectKey = opts.projectKey || '';
      this._host = opts.host || 'https://api.airbrake.io';
      this._processor = null;
      this._reporters = [];
      this._filters = [];
      if (opts.processor !== void 0) {
        this._processor = opts.processor;
      } else {
        this._processor = __webpack_require__(162);
      }
      if (opts.reporter !== void 0) {
        this.addReporter(opts.reporter);
      } else {
        if ('withCredentials' in new global.XMLHttpRequest()) {
          reporter = 'compat';
        } else {
          reporter = 'jsonp';
        }
        this.addReporter(reporter);
      }
      this.addFilter(__webpack_require__(163));
      this.onerror = makeOnErrorHandler(this);
      if ((global.onerror == null) && opts.onerror !== false) {
        global.onerror = this.onerror;
      }
    }

    Client.prototype.setProject = function(id, key) {
      this._projectId = id;
      return this._projectKey = key;
    };

    Client.prototype.setHost = function(host) {
      return this._host = host;
    };

    Client.prototype.addContext = function(context) {
      if (typeof console !== "undefined" && console !== null) {
        if (typeof console.warn === "function") {
          console.warn('airbrake: addContext is deprecated, please use addFilter');
        }
      }
      return this.addFilter(function(notice) {
        notice.context = merge({}, context, notice.context);
        return notice;
      });
    };

    Client.prototype.setEnvironmentName = function(envName) {
      if (typeof console !== "undefined" && console !== null) {
        if (typeof console.warn === "function") {
          console.warn('airbrake: setEnvironmentName is deprecated, please use addFilter');
        }
      }
      return this.addFilter(function(notice) {
        if (notice.context.environment == null) {
          notice.context.environment = envName;
        }
        return notice;
      });
    };

    Client.prototype.addParams = function(params) {
      if (typeof console !== "undefined" && console !== null) {
        if (typeof console.warn === "function") {
          console.warn('airbrake: addParams is deprecated, please use addFilter');
        }
      }
      return this.addFilter(function(notice) {
        notice.params = merge({}, params, notice.params);
        return notice;
      });
    };

    Client.prototype.addEnvironment = function(env) {
      if (typeof console !== "undefined" && console !== null) {
        if (typeof console.warn === "function") {
          console.warn('airbrake: addEnvironment is deprecated, please use addFilter');
        }
      }
      return this.addFilter(function(notice) {
        notice.environment = merge({}, env, notice.environment);
        return notice;
      });
    };

    Client.prototype.addSession = function(session) {
      if (typeof console !== "undefined" && console !== null) {
        if (typeof console.warn === "function") {
          console.warn('airbrake: addSession is deprecated, please use addFilter');
        }
      }
      return this.addFilter(function(notice) {
        notice.session = merge({}, session, notice.session);
        return notice;
      });
    };

    Client.prototype.addReporter = function(reporter) {
      switch (reporter) {
        case 'compat':
          reporter = __webpack_require__(164);
          break;
        case 'xhr':
          reporter = __webpack_require__(167);
          break;
        case 'jsonp':
          reporter = __webpack_require__(168);
      }
      return this._reporters.push(reporter);
    };

    Client.prototype.addFilter = function(filter) {
      return this._filters.push(filter);
    };

    Client.prototype.notify = function(err) {
      var defContext, promise, ref;
      defContext = {
        language: 'JavaScript',
        sourceMapEnabled: true
      };
      if ((ref = global.navigator) != null ? ref.userAgent : void 0) {
        defContext.userAgent = global.navigator.userAgent;
      }
      if (global.location) {
        defContext.url = String(global.location);
        defContext.rootDirectory = global.location.protocol + '//' + global.location.host;
      }
      promise = new Promise();
      this._processor(err.error || err, (function(_this) {
        return function(processorName, errInfo) {
          var filterFn, j, k, len, len1, n, notice, opts, ref1, ref2, reporterFn;
          notice = {
            errors: [errInfo],
            context: merge(defContext, err.context),
            params: err.params || {},
            environment: err.environment || {},
            session: err.session || {}
          };
          notice.context.notifier = {
            name: 'airbrake-js-' + processorName,
            version: '0.5.9',
            url: 'https://github.com/airbrake/airbrake-js'
          };
          ref1 = _this._filters;
          for (j = 0, len = ref1.length; j < len; j++) {
            filterFn = ref1[j];
            n = filterFn(notice);
            if (n === null || n === false) {
              return;
            }
            if (n.errors != null) {
              notice = n;
            } else {
              if (typeof console !== "undefined" && console !== null) {
                if (typeof console.warn === "function") {
                  console.warn('airbrake: filter must return notice or null to ignore the notice');
                }
              }
            }
          }
          opts = {
            projectId: _this._projectId,
            projectKey: _this._projectKey,
            host: _this._host
          };
          ref2 = _this._reporters;
          for (k = 0, len1 = ref2.length; k < len1; k++) {
            reporterFn = ref2[k];
            reporterFn(notice, opts, promise);
          }
        };
      })(this));
      return promise;
    };

    Client.prototype.push = function(err) {
      if (typeof console !== "undefined" && console !== null) {
        if (typeof console.warn === "function") {
          console.warn('airbrake: push is deprecated, please use notify');
        }
      }
      return this.notify(err);
    };

    Client.prototype._wrapArguments = function(args) {
      var arg, i, j, len;
      for (i = j = 0, len = args.length; j < len; i = ++j) {
        arg = args[i];
        if (typeof arg === 'function') {
          args[i] = this.wrap(arg);
        }
      }
      return args;
    };

    Client.prototype.wrap = function(fn) {
      var airbrakeWrapper, prop, self;
      if (fn.__airbrake__) {
        return fn;
      }
      self = this;
      airbrakeWrapper = function() {
        var args, exc;
        args = self._wrapArguments(arguments);
        try {
          return fn.apply(this, args);
        } catch (_error) {
          exc = _error;
          args = Array.prototype.slice.call(arguments);
          self.notify({
            error: exc,
            params: {
              "arguments": args
            }
          });
        }
      };
      for (prop in fn) {
        if (fn.hasOwnProperty(prop)) {
          airbrakeWrapper[prop] = fn[prop];
        }
      }
      airbrakeWrapper.__airbrake__ = true;
      airbrakeWrapper.__inner__ = fn;
      return airbrakeWrapper;
    };

    return Client;

  })();

  module.exports = Client;

}).call(this);

/* WEBPACK VAR INJECTION */}.call(this, __webpack_require__(7)))

/***/ }),
/* 159 */
/***/ (function(module, exports) {

(function() {
  var base;

  if ((base = Array.prototype).indexOf == null) {
    base.indexOf = function(obj, start) {
      var i, j, ref, ref1;
      start = start || 0;
      for (i = j = ref = start, ref1 = this.length; ref <= ref1 ? j < ref1 : j > ref1; i = ref <= ref1 ? ++j : --j) {
        if (this[i] === obj) {
          return i;
        }
      }
      return -1;
    };
  }

}).call(this);


/***/ }),
/* 160 */
/***/ (function(module, exports) {

(function() {
  var merge;

  merge = function() {
    var dst, i, key, len, obj, objs;
    objs = Array.prototype.slice.call(arguments);
    dst = objs.shift() || {};
    for (i = 0, len = objs.length; i < len; i++) {
      obj = objs[i];
      for (key in obj) {
        if (Object.prototype.hasOwnProperty.call(obj, key)) {
          dst[key] = obj[key];
        }
      }
    }
    return dst;
  };

  module.exports = merge;

}).call(this);


/***/ }),
/* 161 */
/***/ (function(module, exports) {

(function() {
  var Promise;

  Promise = (function() {
    function Promise(executor) {
      var reject, resolve;
      this._onResolved = [];
      this._onRejected = [];
      resolve = (function(_this) {
        return function() {
          return _this.resolve.apply(_this, arguments);
        };
      })(this);
      reject = (function(_this) {
        return function() {
          return _this.reject.apply(_this, arguments);
        };
      })(this);
      if (executor != null) {
        executor(resolve, reject);
      }
    }

    Promise.prototype.then = function(onResolved, onRejected) {
      if (onResolved) {
        if (this._resolvedWith != null) {
          onResolved(this._resolvedWith);
        }
        this._onResolved.push(onResolved);
      }
      if (onRejected) {
        if (this._rejectedWith != null) {
          onRejected(this._resolvedWith);
        }
        this._onRejected.push(onRejected);
      }
      return this;
    };

    Promise.prototype["catch"] = function(onRejected) {
      if (this._rejectedWith != null) {
        onRejected(this._rejectedWith);
      }
      this._onRejected.push(onRejected);
      return this;
    };

    Promise.prototype.resolve = function() {
      var fn, i, len, ref;
      this._resolvedWith = arguments;
      ref = this._onResolved;
      for (i = 0, len = ref.length; i < len; i++) {
        fn = ref[i];
        fn.apply(this, this._resolvedWith);
      }
      return this;
    };

    Promise.prototype.reject = function() {
      var fn, i, len, ref;
      this._rejectedWith = arguments;
      ref = this._onRejected;
      for (i = 0, len = ref.length; i < len; i++) {
        fn = ref[i];
        fn.apply(this, this._rejectedWith);
      }
      return this;
    };

    return Promise;

  })();

  module.exports = Promise;

}).call(this);


/***/ }),
/* 162 */
/***/ (function(module, exports) {

(function() {
  var processor, rules, typeMessageRe;

  rules = [
    {
      name: 'v8',
      re: /^\s*at\s(.+?)\s\((?:(?:(.+):(\d+):(\d+))|(.+))\)$/,
      fn: function(m) {
        return {
          "function": m[1],
          file: m[2] || m[5],
          line: m[3] && parseInt(m[3], 10) || 0,
          column: m[4] && parseInt(m[4], 10) || 0
        };
      }
    }, {
      name: 'firefox30',
      re: /^(.*)@(.+):(\d+):(\d+)$/,
      fn: function(m) {
        var evaledRe, file, func, mm;
        func = m[1];
        file = m[2];
        evaledRe = /^(\S+)\s(line\s\d+\s>\seval.*)$/;
        if (mm = file.match(evaledRe)) {
          if (func.length > 0) {
            func = func + ' ' + mm[2];
          } else {
            func = mm[2];
          }
          file = mm[1];
        }
        return {
          "function": func,
          file: file,
          line: parseInt(m[3], 10),
          column: parseInt(m[4], 10)
        };
      }
    }, {
      name: 'firefox14',
      re: /^(.*)@(.+):(\d+)$/,
      fn: function(m, i, e) {
        var column;
        if (i === 0) {
          column = e.columnNumber || 0;
        } else {
          column = 0;
        }
        return {
          "function": m[1],
          file: m[2],
          line: parseInt(m[3], 10),
          column: column
        };
      }
    }, {
      name: 'v8-short',
      re: /^\s*at\s(.+):(\d+):(\d+)$/,
      fn: function(m) {
        return {
          "function": '',
          file: m[1],
          line: parseInt(m[2], 10),
          column: parseInt(m[3], 10)
        };
      }
    }, {
      name: 'phantomjs',
      re: /^\s*at\s(.+):(\d+)$/,
      fn: function(m) {
        return {
          "function": '',
          file: m[1],
          line: parseInt(m[2], 10),
          column: 0
        };
      }
    }, {
      name: 'default',
      re: /.+/,
      fn: function(m) {
        return {
          "function": m[0],
          file: '',
          line: 0,
          column: 0
        };
      }
    }
  ];

  typeMessageRe = /^\S+:\s.+$/;

  processor = function(e, cb) {
    var backtrace, i, j, k, len, len1, line, lines, m, msg, processorName, rule, stack, type, uncaughtExcRe;
    processorName = 'nostack';
    stack = e.stack || '';
    lines = stack.split('\n');
    backtrace = [];
    for (i = j = 0, len = lines.length; j < len; i = ++j) {
      line = lines[i];
      if (line === '') {
        continue;
      }
      for (k = 0, len1 = rules.length; k < len1; k++) {
        rule = rules[k];
        m = line.match(rule.re);
        if (!m) {
          continue;
        }
        processorName = rule.name;
        backtrace.push(rule.fn(m, i, e));
        break;
      }
    }
    if ((processorName === 'v8' || processorName === 'v8-short') && backtrace.length > 0 && backtrace[0]["function"].match(typeMessageRe)) {
      backtrace = backtrace.slice(1);
    }
    if (backtrace.length === 0 && ((e.fileName != null) || (e.lineNumber != null) || (e.columnNumber != null))) {
      backtrace.push({
        "function": '',
        file: e.fileName || '',
        line: parseInt(e.lineNumber, 10) || 0,
        column: parseInt(e.columnNumber, 10) || 0
      });
    }
    if (backtrace.length === 0 && ((e.filename != null) || (e.lineno != null) || (e.column != null) || (e.colno != null))) {
      backtrace.push({
        "function": '',
        file: e.filename || '',
        line: parseInt(e.lineno, 10) || 0,
        column: parseInt(e.column || e.colno, 10) || 0
      });
    }
    if (e.message != null) {
      msg = e.message;
    } else {
      msg = String(e);
    }
    if ((e.name != null) && e.name !== '') {
      type = e.name;
    } else {
      uncaughtExcRe = /^Uncaught\s(.+?):\s(.+)$/;
      m = msg.match(uncaughtExcRe);
      if (m) {
        type = m[1];
        msg = m[2];
      } else {
        type = '';
      }
    }
    if (type === '' && msg === '' && backtrace.length === 0) {
      if (typeof console !== "undefined" && console !== null) {
        if (typeof console.warn === "function") {
          console.warn("airbrake: can't process error", e);
        }
      }
      return;
    }
    return cb(processorName, {
      'type': type,
      'message': msg,
      'backtrace': backtrace
    });
  };

  module.exports = processor;

}).call(this);


/***/ }),
/* 163 */
/***/ (function(module, exports) {

(function() {
  var IGNORED_MESSAGES, filter,
    indexOf = [].indexOf || function(item) { for (var i = 0, l = this.length; i < l; i++) { if (i in this && this[i] === item) return i; } return -1; };

  IGNORED_MESSAGES = ['Script error', 'Script error.'];

  filter = function(notice) {
    var msg;
    msg = notice.errors[0].message;
    if (indexOf.call(IGNORED_MESSAGES, msg) >= 0) {
      return null;
    }
    return notice;
  };

  module.exports = filter;

}).call(this);


/***/ }),
/* 164 */
/***/ (function(module, exports, __webpack_require__) {

/* WEBPACK VAR INJECTION */(function(global) {(function() {
  var jsonifyNotice, report;

  jsonifyNotice = __webpack_require__(165);

  report = function(notice, opts, promise) {
    var payload, req, url;
    url = opts.host + "/api/v3/projects/" + opts.projectId + "/create-notice?key=" + opts.projectKey;
    payload = jsonifyNotice(notice);
    req = new global.XMLHttpRequest();
    req.open('POST', url, true);
    req.send(payload);
    return req.onreadystatechange = function() {
      var resp;
      if (req.readyState === 4 && req.status === 200) {
        resp = JSON.parse(req.responseText);
        notice.id = resp.id;
        return promise.resolve(notice);
      }
    };
  };

  module.exports = report;

}).call(this);

/* WEBPACK VAR INJECTION */}.call(this, __webpack_require__(7)))

/***/ }),
/* 165 */
/***/ (function(module, exports, __webpack_require__) {

(function() {
  var jsonifyNotice, truncate, truncateObj;

  truncate = __webpack_require__(166);

  truncateObj = function(obj, n) {
    var dst, key;
    if (n == null) {
      n = 1000;
    }
    dst = {};
    for (key in obj) {
      dst[key] = truncate(obj[key], n = n);
    }
    return dst;
  };

  jsonifyNotice = function(notice, n, maxLength) {
    var err, s;
    if (n == null) {
      n = 1000;
    }
    if (maxLength == null) {
      maxLength = 64000;
    }
    while (true) {
      notice.params = truncateObj(notice.params, n = n);
      notice.environment = truncateObj(notice.environment, n = n);
      notice.session = truncateObj(notice.session, n = n);
      s = JSON.stringify(notice);
      if (s.length < maxLength) {
        return s;
      }
      if (n === 0) {
        break;
      }
      n = Math.floor(n / 2);
    }
    err = new Error("airbrake-js: cannot jsonify notice (length=" + s.length + " maxLength=" + maxLength + ")");
    err.params = {
      json: s.slice(0, +Math.floor(n / 2) + 1 || 9e9) + '...'
    };
    throw err;
  };

  module.exports = jsonifyNotice;

}).call(this);


/***/ }),
/* 166 */
/***/ (function(module, exports) {

(function() {
  var getAttr, truncate;

  getAttr = function(obj, attr) {
    var exc;
    try {
      return obj[attr];
    } catch (_error) {
      exc = _error;
      return void 0;
    }
  };

  truncate = function(value, n, depth) {
    var fn, getPath, keys, nn, seen;
    if (n == null) {
      n = 1000;
    }
    if (depth == null) {
      depth = 5;
    }
    nn = 0;
    keys = [];
    seen = [];
    getPath = function(value) {
      var i, index, j, path, ref;
      index = seen.indexOf(value);
      path = [keys[index]];
      for (i = j = ref = index; ref <= 0 ? j <= 0 : j >= 0; i = ref <= 0 ? ++j : --j) {
        if (seen[i] && getAttr(seen[i], path[0]) === value) {
          value = seen[i];
          path.unshift(keys[i]);
        }
      }
      return '~' + path.join('.');
    };
    fn = function(value, key, dd) {
      var dst, el, i, j, len, val;
      if (key == null) {
        key = '';
      }
      if (dd == null) {
        dd = 0;
      }
      nn++;
      if (nn > n) {
        return '[Truncated]';
      }
      if (value === null || value === void 0) {
        return value;
      }
      switch (typeof value) {
        case 'boolean':
        case 'number':
        case 'string':
        case 'function':
          return value;
        case 'object':
          break;
        default:
          return String(value);
      }
      if (value instanceof Boolean || value instanceof Number || value instanceof String || value instanceof Date || value instanceof RegExp) {
        return value;
      }
      if (seen.indexOf(value) >= 0) {
        return "[Circular " + (getPath(value)) + "]";
      }
      dd++;
      if (dd > depth) {
        return '[Truncated]';
      }
      keys.push(key);
      seen.push(value);
      nn--;
      if (Object.prototype.toString.apply(value) === '[object Array]') {
        dst = [];
        for (i = j = 0, len = value.length; j < len; i = ++j) {
          el = value[i];
          nn++;
          if (nn >= n) {
            break;
          }
          dst.push(fn(el, key = i, dd));
        }
        return dst;
      }
      dst = {};
      for (key in value) {
        if (!Object.prototype.hasOwnProperty.call(value, key)) {
          continue;
        }
        nn++;
        if (nn >= n) {
          break;
        }
        val = getAttr(value, key);
        if (val !== void 0) {
          dst[key] = fn(val, key = key, dd);
        }
      }
      return dst;
    };
    return fn(value);
  };

  module.exports = truncate;

}).call(this);


/***/ }),
/* 167 */
/***/ (function(module, exports, __webpack_require__) {

/* WEBPACK VAR INJECTION */(function(global) {(function() {
  var jsonifyNotice, report;

  jsonifyNotice = __webpack_require__(165);

  report = function(notice, opts, promise) {
    var payload, req, url;
    url = opts.host + "/api/v3/projects/" + opts.projectId + "/notices?key=" + opts.projectKey;
    payload = jsonifyNotice(notice);
    req = new global.XMLHttpRequest();
    req.open('POST', url, true);
    req.setRequestHeader('Content-Type', 'application/json');
    req.send(payload);
    return req.onreadystatechange = function() {
      var resp;
      if (req.readyState === 4 && req.status === 201) {
        resp = JSON.parse(req.responseText);
        notice.id = resp.id;
        return promise.resolve(notice);
      }
    };
  };

  module.exports = report;

}).call(this);

/* WEBPACK VAR INJECTION */}.call(this, __webpack_require__(7)))

/***/ }),
/* 168 */
/***/ (function(module, exports, __webpack_require__) {

/* WEBPACK VAR INJECTION */(function(global) {(function() {
  var cbCount, jsonifyNotice, report;

  jsonifyNotice = __webpack_require__(165);

  cbCount = 0;

  report = function(notice, opts, promise) {
    var cbName, document, head, payload, removeScript, script, url;
    cbCount++;
    cbName = 'airbrakeCb' + String(cbCount);
    global[cbName] = function(resp) {
      var _;
      notice.id = resp.id;
      promise.resolve(notice);
      try {
        return delete global[cbName];
      } catch (_error) {
        _ = _error;
        return global[cbName] = void 0;
      }
    };
    payload = encodeURIComponent(jsonifyNotice(notice));
    url = opts.host + "/api/v3/projects/" + opts.projectId + "/create-notice?key=" + opts.projectKey + "&callback=" + cbName + "&body=" + payload;
    document = global.document;
    head = document.getElementsByTagName('head')[0];
    script = document.createElement('script');
    script.src = url;
    removeScript = function() {
      return head.removeChild(script);
    };
    script.onload = removeScript;
    script.onerror = removeScript;
    return head.appendChild(script);
  };

  module.exports = report;

}).call(this);

/* WEBPACK VAR INJECTION */}.call(this, __webpack_require__(7)))

/***/ }),
/* 169 */
/***/ (function(module, exports, __webpack_require__) {

/* WEBPACK VAR INJECTION */(function(global) {(function() {
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

}).call(this);

/* WEBPACK VAR INJECTION */}.call(this, __webpack_require__(7)))

/***/ }),
/* 170 */
/***/ (function(module, __webpack_exports__, __webpack_require__) {

"use strict";
__webpack_require__.r(__webpack_exports__);
/* WEBPACK VAR INJECTION */(function($) {/* harmony export (binding) */ __webpack_require__.d(__webpack_exports__, "sendFormData", function() { return sendFormData; });
/* harmony export (binding) */ __webpack_require__.d(__webpack_exports__, "informUser", function() { return informUser; });
/* harmony export (binding) */ __webpack_require__.d(__webpack_exports__, "setCookie", function() { return setCookie; });
/* harmony export (binding) */ __webpack_require__.d(__webpack_exports__, "getCookie", function() { return getCookie; });
/* harmony export (binding) */ __webpack_require__.d(__webpack_exports__, "csrfSafeMethod", function() { return csrfSafeMethod; });
/* harmony export (binding) */ __webpack_require__.d(__webpack_exports__, "isHighDensity", function() { return isHighDensity; });
/* harmony export (binding) */ __webpack_require__.d(__webpack_exports__, "getQueryStringDict", function() { return getQueryStringDict; });
/* harmony export (binding) */ __webpack_require__.d(__webpack_exports__, "getWindowLocationSearch", function() { return getWindowLocationSearch; });
/* harmony export (binding) */ __webpack_require__.d(__webpack_exports__, "variables", function() { return variables; });
/* harmony export (binding) */ __webpack_require__.d(__webpack_exports__, "jsonLocalStorage", function() { return jsonLocalStorage; });
/* harmony export (binding) */ __webpack_require__.d(__webpack_exports__, "triggerOnWindow", function() { return triggerOnWindow; });
/* harmony import */ var _babel_runtime_corejs3_core_js_stable_object_keys__WEBPACK_IMPORTED_MODULE_0__ = __webpack_require__(171);
/* harmony import */ var _babel_runtime_corejs3_core_js_stable_object_keys__WEBPACK_IMPORTED_MODULE_0___default = /*#__PURE__*/__webpack_require__.n(_babel_runtime_corejs3_core_js_stable_object_keys__WEBPACK_IMPORTED_MODULE_0__);
/* harmony import */ var _babel_runtime_corejs3_core_js_stable_instance_trim__WEBPACK_IMPORTED_MODULE_1__ = __webpack_require__(181);
/* harmony import */ var _babel_runtime_corejs3_core_js_stable_instance_trim__WEBPACK_IMPORTED_MODULE_1___default = /*#__PURE__*/__webpack_require__.n(_babel_runtime_corejs3_core_js_stable_instance_trim__WEBPACK_IMPORTED_MODULE_1__);
/* harmony import */ var _babel_runtime_corejs3_core_js_stable_json_stringify__WEBPACK_IMPORTED_MODULE_2__ = __webpack_require__(191);
/* harmony import */ var _babel_runtime_corejs3_core_js_stable_json_stringify__WEBPACK_IMPORTED_MODULE_2___default = /*#__PURE__*/__webpack_require__.n(_babel_runtime_corejs3_core_js_stable_json_stringify__WEBPACK_IMPORTED_MODULE_2__);



function sendFormData(method, url, data, requestArgs) {
  requestArgs = requestArgs || {};
  var formData = new FormData();

  for (var _i = 0, _Object$keys = _babel_runtime_corejs3_core_js_stable_object_keys__WEBPACK_IMPORTED_MODULE_0___default()(data); _i < _Object$keys.length; _i++) {
    var key = _Object$keys[_i];
    formData.append(key, data[key]);
  }

  requestArgs.data = formData;
  requestArgs.url = api_path + url;
  requestArgs.method = method;
  return $.ajax(requestArgs);
}
function informUser(message, alertClass) {
  /*
      Show user some information at top of screen.
      alertClass options are 'success', 'info', 'warning', 'danger'
   */
  $('.popup-alert button.close').click();
  alertClass = alertClass || "info";
  $('<div class="alert alert-' + alertClass + ' alert-dismissible popup-alert" role="alert" style="display: none">' + '<button type="button" class="close" data-dismiss="alert"><span aria-hidden="true">&times;</span><span class="sr-only">Close</span></button>' + message + '</div>').prependTo('body').fadeIn('fast');
} // via http://www.w3schools.com/js/js_cookies.asp

function setCookie(cname, cvalue, exdays) {
  var d = new Date();
  d.setTime(d.getTime() + exdays * 24 * 60 * 60 * 1000);
  var expires = "expires=" + d.toUTCString();
  document.cookie = cname + "=" + cvalue + "; " + expires;
}
function getCookie(name) {
  var cookieValue;

  if (document.cookie) {
    var cookies = document.cookie.split(';');

    for (var i = 0; i < cookies.length; i++) {
      var cookie = _babel_runtime_corejs3_core_js_stable_instance_trim__WEBPACK_IMPORTED_MODULE_1___default()($).call($, cookies[i]); // Does this cookie string begin with the name we want?


      if (cookie.substring(0, name.length + 1) == name + '=') {
        cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
        break;
      }
    }
  }

  return cookieValue;
}
function csrfSafeMethod(method) {
  // these HTTP methods do not require CSRF protection
  return /^(GET|HEAD|OPTIONS|TRACE)$/.test(method);
} // check if this is a retina-style display
// via http://stackoverflow.com/a/20413768

function isHighDensity() {
  return window.matchMedia && (window.matchMedia('only screen and (min-resolution: 124dpi), only screen and (min-resolution: 1.3dppx), only screen and (min-resolution: 48.8dpcm)').matches || window.matchMedia('only screen and (-webkit-min-device-pixel-ratio: 1.3), only screen and (-o-min-device-pixel-ratio: 2.6/2), only screen and (min--moz-device-pixel-ratio: 1.3), only screen and (min-device-pixel-ratio: 1.3)').matches) || window.devicePixelRatio && window.devicePixelRatio > 1.3;
}
function getQueryStringDict() {
  var queryString = window.location.search.substring(1);

  if (queryString) {
    var queries = queryString.split("&");
    var queryDict = {};

    for (var i = 0; i < queries.length; i++) {
      var split = queries[i].split('=');
      queryDict[split[0]] = split[1];
    }

    return queryDict;
  } else {
    return {};
  }
}
function getWindowLocationSearch() {
  return window.location.search;
}
var variables = {
  localStorageKey: "perma_selection"
};
var jsonLocalStorage = {
  getItem: function getItem(key) {
    var result = localStorage.getItem(key);

    try {
      result = JSON.parse(result);
    } catch (e) {
      result;
    }

    return result;
  },
  setItem: function setItem(key, value) {
    if (typeof value !== "string") {
      value = _babel_runtime_corejs3_core_js_stable_json_stringify__WEBPACK_IMPORTED_MODULE_2___default()(value);
    }

    localStorage.setItem(key, value);
  }
};
function triggerOnWindow(message, data) {
  $(window).trigger(message, data);
}
/* WEBPACK VAR INJECTION */}.call(this, __webpack_require__(58)))

/***/ }),
/* 171 */
/***/ (function(module, exports, __webpack_require__) {

module.exports = __webpack_require__(172);

/***/ }),
/* 172 */
/***/ (function(module, exports, __webpack_require__) {

var parent = __webpack_require__(173);

module.exports = parent;


/***/ }),
/* 173 */
/***/ (function(module, exports, __webpack_require__) {

__webpack_require__(174);
var path = __webpack_require__(27);

module.exports = path.Object.keys;


/***/ }),
/* 174 */
/***/ (function(module, exports, __webpack_require__) {

var $ = __webpack_require__(5);
var toObject = __webpack_require__(43);
var nativeKeys = __webpack_require__(175);
var fails = __webpack_require__(10);

var FAILS_ON_PRIMITIVES = fails(function () { nativeKeys(1); });

// `Object.keys` method
// https://tc39.es/ecma262/#sec-object.keys
$({ target: 'Object', stat: true, forced: FAILS_ON_PRIMITIVES }, {
  keys: function keys(it) {
    return nativeKeys(toObject(it));
  }
});


/***/ }),
/* 175 */
/***/ (function(module, exports, __webpack_require__) {

var internalObjectKeys = __webpack_require__(176);
var enumBugKeys = __webpack_require__(180);

// `Object.keys` method
// https://tc39.es/ecma262/#sec-object.keys
// eslint-disable-next-line es/no-object-keys -- safe
module.exports = Object.keys || function keys(O) {
  return internalObjectKeys(O, enumBugKeys);
};


/***/ }),
/* 176 */
/***/ (function(module, exports, __webpack_require__) {

var uncurryThis = __webpack_require__(11);
var hasOwn = __webpack_require__(42);
var toIndexedObject = __webpack_require__(18);
var indexOf = __webpack_require__(177).indexOf;
var hiddenKeys = __webpack_require__(179);

var push = uncurryThis([].push);

module.exports = function (object, names) {
  var O = toIndexedObject(object);
  var i = 0;
  var result = [];
  var key;
  for (key in O) !hasOwn(hiddenKeys, key) && hasOwn(O, key) && push(result, key);
  // Don't enum bug & hidden keys
  while (names.length > i) if (hasOwn(O, key = names[i++])) {
    ~indexOf(result, key) || push(result, key);
  }
  return result;
};


/***/ }),
/* 177 */
/***/ (function(module, exports, __webpack_require__) {

var toIndexedObject = __webpack_require__(18);
var toAbsoluteIndex = __webpack_require__(178);
var lengthOfArrayLike = __webpack_require__(65);

// `Array.prototype.{ indexOf, includes }` methods implementation
var createMethod = function (IS_INCLUDES) {
  return function ($this, el, fromIndex) {
    var O = toIndexedObject($this);
    var length = lengthOfArrayLike(O);
    var index = toAbsoluteIndex(fromIndex, length);
    var value;
    // Array#includes uses SameValueZero equality algorithm
    // eslint-disable-next-line no-self-compare -- NaN check
    if (IS_INCLUDES && el != el) while (length > index) {
      value = O[index++];
      // eslint-disable-next-line no-self-compare -- NaN check
      if (value != value) return true;
    // Array#indexOf ignores holes, Array#includes - not
    } else for (;length > index; index++) {
      if ((IS_INCLUDES || index in O) && O[index] === el) return IS_INCLUDES || index || 0;
    } return !IS_INCLUDES && -1;
  };
};

module.exports = {
  // `Array.prototype.includes` method
  // https://tc39.es/ecma262/#sec-array.prototype.includes
  includes: createMethod(true),
  // `Array.prototype.indexOf` method
  // https://tc39.es/ecma262/#sec-array.prototype.indexof
  indexOf: createMethod(false)
};


/***/ }),
/* 178 */
/***/ (function(module, exports, __webpack_require__) {

var toIntegerOrInfinity = __webpack_require__(67);

var max = Math.max;
var min = Math.min;

// Helper for a popular repeating case of the spec:
// Let integer be ? ToInteger(index).
// If integer < 0, let result be max((length + integer), 0); else let result be min(integer, length).
module.exports = function (index, length) {
  var integer = toIntegerOrInfinity(index);
  return integer < 0 ? max(integer + length, 0) : min(integer, length);
};


/***/ }),
/* 179 */
/***/ (function(module, exports) {

module.exports = {};


/***/ }),
/* 180 */
/***/ (function(module, exports) {

// IE8- don't enum bug keys
module.exports = [
  'constructor',
  'hasOwnProperty',
  'isPrototypeOf',
  'propertyIsEnumerable',
  'toLocaleString',
  'toString',
  'valueOf'
];


/***/ }),
/* 181 */
/***/ (function(module, exports, __webpack_require__) {

module.exports = __webpack_require__(182);

/***/ }),
/* 182 */
/***/ (function(module, exports, __webpack_require__) {

var parent = __webpack_require__(183);

module.exports = parent;


/***/ }),
/* 183 */
/***/ (function(module, exports, __webpack_require__) {

var isPrototypeOf = __webpack_require__(28);
var method = __webpack_require__(184);

var StringPrototype = String.prototype;

module.exports = function (it) {
  var own = it.trim;
  return typeof it == 'string' || it === StringPrototype
    || (isPrototypeOf(StringPrototype, it) && own === StringPrototype.trim) ? method : own;
};


/***/ }),
/* 184 */
/***/ (function(module, exports, __webpack_require__) {

__webpack_require__(185);
var entryVirtual = __webpack_require__(76);

module.exports = entryVirtual('String').trim;


/***/ }),
/* 185 */
/***/ (function(module, exports, __webpack_require__) {

"use strict";

var $ = __webpack_require__(5);
var $trim = __webpack_require__(186).trim;
var forcedStringTrimMethod = __webpack_require__(189);

// `String.prototype.trim` method
// https://tc39.es/ecma262/#sec-string.prototype.trim
$({ target: 'String', proto: true, forced: forcedStringTrimMethod('trim') }, {
  trim: function trim() {
    return $trim(this);
  }
});


/***/ }),
/* 186 */
/***/ (function(module, exports, __webpack_require__) {

var uncurryThis = __webpack_require__(11);
var requireObjectCoercible = __webpack_require__(21);
var toString = __webpack_require__(187);
var whitespaces = __webpack_require__(188);

var replace = uncurryThis(''.replace);
var whitespace = '[' + whitespaces + ']';
var ltrim = RegExp('^' + whitespace + whitespace + '*');
var rtrim = RegExp(whitespace + whitespace + '*$');

// `String.prototype.{ trim, trimStart, trimEnd, trimLeft, trimRight }` methods implementation
var createMethod = function (TYPE) {
  return function ($this) {
    var string = toString(requireObjectCoercible($this));
    if (TYPE & 1) string = replace(string, ltrim, '');
    if (TYPE & 2) string = replace(string, rtrim, '');
    return string;
  };
};

module.exports = {
  // `String.prototype.{ trimLeft, trimStart }` methods
  // https://tc39.es/ecma262/#sec-string.prototype.trimstart
  start: createMethod(1),
  // `String.prototype.{ trimRight, trimEnd }` methods
  // https://tc39.es/ecma262/#sec-string.prototype.trimend
  end: createMethod(2),
  // `String.prototype.trim` method
  // https://tc39.es/ecma262/#sec-string.prototype.trim
  trim: createMethod(3)
};


/***/ }),
/* 187 */
/***/ (function(module, exports, __webpack_require__) {

var global = __webpack_require__(6);
var classof = __webpack_require__(72);

var String = global.String;

module.exports = function (argument) {
  if (classof(argument) === 'Symbol') throw TypeError('Cannot convert a Symbol value to a string');
  return String(argument);
};


/***/ }),
/* 188 */
/***/ (function(module, exports) {

// a string of all valid unicode whitespaces
module.exports = '\u0009\u000A\u000B\u000C\u000D\u0020\u00A0\u1680\u2000\u2001\u2002' +
  '\u2003\u2004\u2005\u2006\u2007\u2008\u2009\u200A\u202F\u205F\u3000\u2028\u2029\uFEFF';


/***/ }),
/* 189 */
/***/ (function(module, exports, __webpack_require__) {

var PROPER_FUNCTION_NAME = __webpack_require__(190).PROPER;
var fails = __webpack_require__(10);
var whitespaces = __webpack_require__(188);

var non = '\u200B\u0085\u180E';

// check that a method works with the correct list
// of whitespaces and has a correct name
module.exports = function (METHOD_NAME) {
  return fails(function () {
    return !!whitespaces[METHOD_NAME]()
      || non[METHOD_NAME]() !== non
      || (PROPER_FUNCTION_NAME && whitespaces[METHOD_NAME].name !== METHOD_NAME);
  });
};


/***/ }),
/* 190 */
/***/ (function(module, exports, __webpack_require__) {

var DESCRIPTORS = __webpack_require__(14);
var hasOwn = __webpack_require__(42);

var FunctionPrototype = Function.prototype;
// eslint-disable-next-line es/no-object-getownpropertydescriptor -- safe
var getDescriptor = DESCRIPTORS && Object.getOwnPropertyDescriptor;

var EXISTS = hasOwn(FunctionPrototype, 'name');
// additional protection from minified / mangled / dropped function names
var PROPER = EXISTS && (function something() { /* empty */ }).name === 'something';
var CONFIGURABLE = EXISTS && (!DESCRIPTORS || (DESCRIPTORS && getDescriptor(FunctionPrototype, 'name').configurable));

module.exports = {
  EXISTS: EXISTS,
  PROPER: PROPER,
  CONFIGURABLE: CONFIGURABLE
};


/***/ }),
/* 191 */
/***/ (function(module, exports, __webpack_require__) {

module.exports = __webpack_require__(192);

/***/ }),
/* 192 */
/***/ (function(module, exports, __webpack_require__) {

var parent = __webpack_require__(193);

module.exports = parent;


/***/ }),
/* 193 */
/***/ (function(module, exports, __webpack_require__) {

__webpack_require__(194);
var path = __webpack_require__(27);
var apply = __webpack_require__(8);

// eslint-disable-next-line es/no-json -- safe
if (!path.JSON) path.JSON = { stringify: JSON.stringify };

// eslint-disable-next-line no-unused-vars -- required for `.length`
module.exports = function stringify(it, replacer, space) {
  return apply(path.JSON.stringify, null, arguments);
};


/***/ }),
/* 194 */
/***/ (function(module, exports, __webpack_require__) {

var $ = __webpack_require__(5);
var global = __webpack_require__(6);
var getBuiltIn = __webpack_require__(26);
var apply = __webpack_require__(8);
var uncurryThis = __webpack_require__(11);
var fails = __webpack_require__(10);

var Array = global.Array;
var $stringify = getBuiltIn('JSON', 'stringify');
var exec = uncurryThis(/./.exec);
var charAt = uncurryThis(''.charAt);
var charCodeAt = uncurryThis(''.charCodeAt);
var replace = uncurryThis(''.replace);
var numberToString = uncurryThis(1.0.toString);

var tester = /[\uD800-\uDFFF]/g;
var low = /^[\uD800-\uDBFF]$/;
var hi = /^[\uDC00-\uDFFF]$/;

var fix = function (match, offset, string) {
  var prev = charAt(string, offset - 1);
  var next = charAt(string, offset + 1);
  if ((exec(low, match) && !exec(hi, next)) || (exec(hi, match) && !exec(low, prev))) {
    return '\\u' + numberToString(charCodeAt(match, 0), 16);
  } return match;
};

var FORCED = fails(function () {
  return $stringify('\uDF06\uD834') !== '"\\udf06\\ud834"'
    || $stringify('\uDEAD') !== '"\\udead"';
});

if ($stringify) {
  // `JSON.stringify` method
  // https://tc39.es/ecma262/#sec-json.stringify
  // https://github.com/tc39/proposal-well-formed-stringify
  $({ target: 'JSON', stat: true, forced: FORCED }, {
    // eslint-disable-next-line no-unused-vars -- required for `.length`
    stringify: function stringify(it, replacer, space) {
      for (var i = 0, l = arguments.length, args = Array(l); i < l; i++) args[i] = arguments[i];
      var result = apply($stringify, null, args);
      return typeof result == 'string' ? replace(result, tester, fix) : result;
    }
  });
}


/***/ }),
/* 195 */
/***/ (function(module, exports) {

/**
 * from https://github.com/Automattic/_s/blob/master/js/skip-link-focus-fix.js
 *
 * File skip-link-focus-fix.js.
 *
 * Helps with accessibility for keyboard only users.
 *
 * Learn more: https://git.io/vWdr2
 */
(function () {
  var isIe = /(trident|msie)/i.test(navigator.userAgent);

  if (isIe && document.getElementById && window.addEventListener) {
    window.addEventListener('hashchange', function () {
      var id = location.hash.substring(1),
          element;

      if (!/^[A-z0-9_-]+$/.test(id)) {
        return;
      }

      element = document.getElementById(id);

      if (element) {
        if (!/^(?:a|select|input|button|textarea)$/i.test(element.tagName)) {
          element.tabIndex = -1;
        }

        element.focus();
      }
    }, false);
  }
})();

/***/ }),
/* 196 */
/***/ (function(module, exports, __webpack_require__) {

/* WEBPACK VAR INJECTION */(function(jQuery) {/* ========================================================================
 * Bootstrap: dropdown.js v3.4.1
 * https://getbootstrap.com/docs/3.4/javascript/#dropdowns
 * ========================================================================
 * Copyright 2011-2019 Twitter, Inc.
 * Licensed under MIT (https://github.com/twbs/bootstrap/blob/master/LICENSE)
 * ======================================================================== */


+function ($) {
  'use strict';

  // DROPDOWN CLASS DEFINITION
  // =========================

  var backdrop = '.dropdown-backdrop'
  var toggle   = '[data-toggle="dropdown"]'
  var Dropdown = function (element) {
    $(element).on('click.bs.dropdown', this.toggle)
  }

  Dropdown.VERSION = '3.4.1'

  function getParent($this) {
    var selector = $this.attr('data-target')

    if (!selector) {
      selector = $this.attr('href')
      selector = selector && /#[A-Za-z]/.test(selector) && selector.replace(/.*(?=#[^\s]*$)/, '') // strip for ie7
    }

    var $parent = selector !== '#' ? $(document).find(selector) : null

    return $parent && $parent.length ? $parent : $this.parent()
  }

  function clearMenus(e) {
    if (e && e.which === 3) return
    $(backdrop).remove()
    $(toggle).each(function () {
      var $this         = $(this)
      var $parent       = getParent($this)
      var relatedTarget = { relatedTarget: this }

      if (!$parent.hasClass('open')) return

      if (e && e.type == 'click' && /input|textarea/i.test(e.target.tagName) && $.contains($parent[0], e.target)) return

      $parent.trigger(e = $.Event('hide.bs.dropdown', relatedTarget))

      if (e.isDefaultPrevented()) return

      $this.attr('aria-expanded', 'false')
      $parent.removeClass('open').trigger($.Event('hidden.bs.dropdown', relatedTarget))
    })
  }

  Dropdown.prototype.toggle = function (e) {
    var $this = $(this)

    if ($this.is('.disabled, :disabled')) return

    var $parent  = getParent($this)
    var isActive = $parent.hasClass('open')

    clearMenus()

    if (!isActive) {
      if ('ontouchstart' in document.documentElement && !$parent.closest('.navbar-nav').length) {
        // if mobile we use a backdrop because click events don't delegate
        $(document.createElement('div'))
          .addClass('dropdown-backdrop')
          .insertAfter($(this))
          .on('click', clearMenus)
      }

      var relatedTarget = { relatedTarget: this }
      $parent.trigger(e = $.Event('show.bs.dropdown', relatedTarget))

      if (e.isDefaultPrevented()) return

      $this
        .trigger('focus')
        .attr('aria-expanded', 'true')

      $parent
        .toggleClass('open')
        .trigger($.Event('shown.bs.dropdown', relatedTarget))
    }

    return false
  }

  Dropdown.prototype.keydown = function (e) {
    if (!/(38|40|27|32)/.test(e.which) || /input|textarea/i.test(e.target.tagName)) return

    var $this = $(this)

    e.preventDefault()
    e.stopPropagation()

    if ($this.is('.disabled, :disabled')) return

    var $parent  = getParent($this)
    var isActive = $parent.hasClass('open')

    if (!isActive && e.which != 27 || isActive && e.which == 27) {
      if (e.which == 27) $parent.find(toggle).trigger('focus')
      return $this.trigger('click')
    }

    var desc = ' li:not(.disabled):visible a'
    var $items = $parent.find('.dropdown-menu' + desc)

    if (!$items.length) return

    var index = $items.index(e.target)

    if (e.which == 38 && index > 0)                 index--         // up
    if (e.which == 40 && index < $items.length - 1) index++         // down
    if (!~index)                                    index = 0

    $items.eq(index).trigger('focus')
  }


  // DROPDOWN PLUGIN DEFINITION
  // ==========================

  function Plugin(option) {
    return this.each(function () {
      var $this = $(this)
      var data  = $this.data('bs.dropdown')

      if (!data) $this.data('bs.dropdown', (data = new Dropdown(this)))
      if (typeof option == 'string') data[option].call($this)
    })
  }

  var old = $.fn.dropdown

  $.fn.dropdown             = Plugin
  $.fn.dropdown.Constructor = Dropdown


  // DROPDOWN NO CONFLICT
  // ====================

  $.fn.dropdown.noConflict = function () {
    $.fn.dropdown = old
    return this
  }


  // APPLY TO STANDARD DROPDOWN ELEMENTS
  // ===================================

  $(document)
    .on('click.bs.dropdown.data-api', clearMenus)
    .on('click.bs.dropdown.data-api', '.dropdown form', function (e) { e.stopPropagation() })
    .on('click.bs.dropdown.data-api', toggle, Dropdown.prototype.toggle)
    .on('keydown.bs.dropdown.data-api', toggle, Dropdown.prototype.keydown)
    .on('keydown.bs.dropdown.data-api', '.dropdown-menu', Dropdown.prototype.keydown)

}(jQuery);

/* WEBPACK VAR INJECTION */}.call(this, __webpack_require__(58)))

/***/ }),
/* 197 */
/***/ (function(module, exports, __webpack_require__) {

/* WEBPACK VAR INJECTION */(function(jQuery) {/* ========================================================================
 * Bootstrap: collapse.js v3.4.1
 * https://getbootstrap.com/docs/3.4/javascript/#collapse
 * ========================================================================
 * Copyright 2011-2019 Twitter, Inc.
 * Licensed under MIT (https://github.com/twbs/bootstrap/blob/master/LICENSE)
 * ======================================================================== */

/* jshint latedef: false */

+function ($) {
  'use strict';

  // COLLAPSE PUBLIC CLASS DEFINITION
  // ================================

  var Collapse = function (element, options) {
    this.$element      = $(element)
    this.options       = $.extend({}, Collapse.DEFAULTS, options)
    this.$trigger      = $('[data-toggle="collapse"][href="#' + element.id + '"],' +
                           '[data-toggle="collapse"][data-target="#' + element.id + '"]')
    this.transitioning = null

    if (this.options.parent) {
      this.$parent = this.getParent()
    } else {
      this.addAriaAndCollapsedClass(this.$element, this.$trigger)
    }

    if (this.options.toggle) this.toggle()
  }

  Collapse.VERSION  = '3.4.1'

  Collapse.TRANSITION_DURATION = 350

  Collapse.DEFAULTS = {
    toggle: true
  }

  Collapse.prototype.dimension = function () {
    var hasWidth = this.$element.hasClass('width')
    return hasWidth ? 'width' : 'height'
  }

  Collapse.prototype.show = function () {
    if (this.transitioning || this.$element.hasClass('in')) return

    var activesData
    var actives = this.$parent && this.$parent.children('.panel').children('.in, .collapsing')

    if (actives && actives.length) {
      activesData = actives.data('bs.collapse')
      if (activesData && activesData.transitioning) return
    }

    var startEvent = $.Event('show.bs.collapse')
    this.$element.trigger(startEvent)
    if (startEvent.isDefaultPrevented()) return

    if (actives && actives.length) {
      Plugin.call(actives, 'hide')
      activesData || actives.data('bs.collapse', null)
    }

    var dimension = this.dimension()

    this.$element
      .removeClass('collapse')
      .addClass('collapsing')[dimension](0)
      .attr('aria-expanded', true)

    this.$trigger
      .removeClass('collapsed')
      .attr('aria-expanded', true)

    this.transitioning = 1

    var complete = function () {
      this.$element
        .removeClass('collapsing')
        .addClass('collapse in')[dimension]('')
      this.transitioning = 0
      this.$element
        .trigger('shown.bs.collapse')
    }

    if (!$.support.transition) return complete.call(this)

    var scrollSize = $.camelCase(['scroll', dimension].join('-'))

    this.$element
      .one('bsTransitionEnd', $.proxy(complete, this))
      .emulateTransitionEnd(Collapse.TRANSITION_DURATION)[dimension](this.$element[0][scrollSize])
  }

  Collapse.prototype.hide = function () {
    if (this.transitioning || !this.$element.hasClass('in')) return

    var startEvent = $.Event('hide.bs.collapse')
    this.$element.trigger(startEvent)
    if (startEvent.isDefaultPrevented()) return

    var dimension = this.dimension()

    this.$element[dimension](this.$element[dimension]())[0].offsetHeight

    this.$element
      .addClass('collapsing')
      .removeClass('collapse in')
      .attr('aria-expanded', false)

    this.$trigger
      .addClass('collapsed')
      .attr('aria-expanded', false)

    this.transitioning = 1

    var complete = function () {
      this.transitioning = 0
      this.$element
        .removeClass('collapsing')
        .addClass('collapse')
        .trigger('hidden.bs.collapse')
    }

    if (!$.support.transition) return complete.call(this)

    this.$element
      [dimension](0)
      .one('bsTransitionEnd', $.proxy(complete, this))
      .emulateTransitionEnd(Collapse.TRANSITION_DURATION)
  }

  Collapse.prototype.toggle = function () {
    this[this.$element.hasClass('in') ? 'hide' : 'show']()
  }

  Collapse.prototype.getParent = function () {
    return $(document).find(this.options.parent)
      .find('[data-toggle="collapse"][data-parent="' + this.options.parent + '"]')
      .each($.proxy(function (i, element) {
        var $element = $(element)
        this.addAriaAndCollapsedClass(getTargetFromTrigger($element), $element)
      }, this))
      .end()
  }

  Collapse.prototype.addAriaAndCollapsedClass = function ($element, $trigger) {
    var isOpen = $element.hasClass('in')

    $element.attr('aria-expanded', isOpen)
    $trigger
      .toggleClass('collapsed', !isOpen)
      .attr('aria-expanded', isOpen)
  }

  function getTargetFromTrigger($trigger) {
    var href
    var target = $trigger.attr('data-target')
      || (href = $trigger.attr('href')) && href.replace(/.*(?=#[^\s]+$)/, '') // strip for ie7

    return $(document).find(target)
  }


  // COLLAPSE PLUGIN DEFINITION
  // ==========================

  function Plugin(option) {
    return this.each(function () {
      var $this   = $(this)
      var data    = $this.data('bs.collapse')
      var options = $.extend({}, Collapse.DEFAULTS, $this.data(), typeof option == 'object' && option)

      if (!data && options.toggle && /show|hide/.test(option)) options.toggle = false
      if (!data) $this.data('bs.collapse', (data = new Collapse(this, options)))
      if (typeof option == 'string') data[option]()
    })
  }

  var old = $.fn.collapse

  $.fn.collapse             = Plugin
  $.fn.collapse.Constructor = Collapse


  // COLLAPSE NO CONFLICT
  // ====================

  $.fn.collapse.noConflict = function () {
    $.fn.collapse = old
    return this
  }


  // COLLAPSE DATA-API
  // =================

  $(document).on('click.bs.collapse.data-api', '[data-toggle="collapse"]', function (e) {
    var $this   = $(this)

    if (!$this.attr('data-target')) e.preventDefault()

    var $target = getTargetFromTrigger($this)
    var data    = $target.data('bs.collapse')
    var option  = data ? 'toggle' : $this.data()

    Plugin.call($target, option)
  })

}(jQuery);

/* WEBPACK VAR INJECTION */}.call(this, __webpack_require__(58)))

/***/ }),
/* 198 */
/***/ (function(module, exports, __webpack_require__) {

/* WEBPACK VAR INJECTION */(function(jQuery) {/* ========================================================================
 * Bootstrap: carousel.js v3.4.1
 * https://getbootstrap.com/docs/3.4/javascript/#carousel
 * ========================================================================
 * Copyright 2011-2019 Twitter, Inc.
 * Licensed under MIT (https://github.com/twbs/bootstrap/blob/master/LICENSE)
 * ======================================================================== */


+function ($) {
  'use strict';

  // CAROUSEL CLASS DEFINITION
  // =========================

  var Carousel = function (element, options) {
    this.$element    = $(element)
    this.$indicators = this.$element.find('.carousel-indicators')
    this.options     = options
    this.paused      = null
    this.sliding     = null
    this.interval    = null
    this.$active     = null
    this.$items      = null

    this.options.keyboard && this.$element.on('keydown.bs.carousel', $.proxy(this.keydown, this))

    this.options.pause == 'hover' && !('ontouchstart' in document.documentElement) && this.$element
      .on('mouseenter.bs.carousel', $.proxy(this.pause, this))
      .on('mouseleave.bs.carousel', $.proxy(this.cycle, this))
  }

  Carousel.VERSION  = '3.4.1'

  Carousel.TRANSITION_DURATION = 600

  Carousel.DEFAULTS = {
    interval: 5000,
    pause: 'hover',
    wrap: true,
    keyboard: true
  }

  Carousel.prototype.keydown = function (e) {
    if (/input|textarea/i.test(e.target.tagName)) return
    switch (e.which) {
      case 37: this.prev(); break
      case 39: this.next(); break
      default: return
    }

    e.preventDefault()
  }

  Carousel.prototype.cycle = function (e) {
    e || (this.paused = false)

    this.interval && clearInterval(this.interval)

    this.options.interval
      && !this.paused
      && (this.interval = setInterval($.proxy(this.next, this), this.options.interval))

    return this
  }

  Carousel.prototype.getItemIndex = function (item) {
    this.$items = item.parent().children('.item')
    return this.$items.index(item || this.$active)
  }

  Carousel.prototype.getItemForDirection = function (direction, active) {
    var activeIndex = this.getItemIndex(active)
    var willWrap = (direction == 'prev' && activeIndex === 0)
                || (direction == 'next' && activeIndex == (this.$items.length - 1))
    if (willWrap && !this.options.wrap) return active
    var delta = direction == 'prev' ? -1 : 1
    var itemIndex = (activeIndex + delta) % this.$items.length
    return this.$items.eq(itemIndex)
  }

  Carousel.prototype.to = function (pos) {
    var that        = this
    var activeIndex = this.getItemIndex(this.$active = this.$element.find('.item.active'))

    if (pos > (this.$items.length - 1) || pos < 0) return

    if (this.sliding)       return this.$element.one('slid.bs.carousel', function () { that.to(pos) }) // yes, "slid"
    if (activeIndex == pos) return this.pause().cycle()

    return this.slide(pos > activeIndex ? 'next' : 'prev', this.$items.eq(pos))
  }

  Carousel.prototype.pause = function (e) {
    e || (this.paused = true)

    if (this.$element.find('.next, .prev').length && $.support.transition) {
      this.$element.trigger($.support.transition.end)
      this.cycle(true)
    }

    this.interval = clearInterval(this.interval)

    return this
  }

  Carousel.prototype.next = function () {
    if (this.sliding) return
    return this.slide('next')
  }

  Carousel.prototype.prev = function () {
    if (this.sliding) return
    return this.slide('prev')
  }

  Carousel.prototype.slide = function (type, next) {
    var $active   = this.$element.find('.item.active')
    var $next     = next || this.getItemForDirection(type, $active)
    var isCycling = this.interval
    var direction = type == 'next' ? 'left' : 'right'
    var that      = this

    if ($next.hasClass('active')) return (this.sliding = false)

    var relatedTarget = $next[0]
    var slideEvent = $.Event('slide.bs.carousel', {
      relatedTarget: relatedTarget,
      direction: direction
    })
    this.$element.trigger(slideEvent)
    if (slideEvent.isDefaultPrevented()) return

    this.sliding = true

    isCycling && this.pause()

    if (this.$indicators.length) {
      this.$indicators.find('.active').removeClass('active')
      var $nextIndicator = $(this.$indicators.children()[this.getItemIndex($next)])
      $nextIndicator && $nextIndicator.addClass('active')
    }

    var slidEvent = $.Event('slid.bs.carousel', { relatedTarget: relatedTarget, direction: direction }) // yes, "slid"
    if ($.support.transition && this.$element.hasClass('slide')) {
      $next.addClass(type)
      if (typeof $next === 'object' && $next.length) {
        $next[0].offsetWidth // force reflow
      }
      $active.addClass(direction)
      $next.addClass(direction)
      $active
        .one('bsTransitionEnd', function () {
          $next.removeClass([type, direction].join(' ')).addClass('active')
          $active.removeClass(['active', direction].join(' '))
          that.sliding = false
          setTimeout(function () {
            that.$element.trigger(slidEvent)
          }, 0)
        })
        .emulateTransitionEnd(Carousel.TRANSITION_DURATION)
    } else {
      $active.removeClass('active')
      $next.addClass('active')
      this.sliding = false
      this.$element.trigger(slidEvent)
    }

    isCycling && this.cycle()

    return this
  }


  // CAROUSEL PLUGIN DEFINITION
  // ==========================

  function Plugin(option) {
    return this.each(function () {
      var $this   = $(this)
      var data    = $this.data('bs.carousel')
      var options = $.extend({}, Carousel.DEFAULTS, $this.data(), typeof option == 'object' && option)
      var action  = typeof option == 'string' ? option : options.slide

      if (!data) $this.data('bs.carousel', (data = new Carousel(this, options)))
      if (typeof option == 'number') data.to(option)
      else if (action) data[action]()
      else if (options.interval) data.pause().cycle()
    })
  }

  var old = $.fn.carousel

  $.fn.carousel             = Plugin
  $.fn.carousel.Constructor = Carousel


  // CAROUSEL NO CONFLICT
  // ====================

  $.fn.carousel.noConflict = function () {
    $.fn.carousel = old
    return this
  }


  // CAROUSEL DATA-API
  // =================

  var clickHandler = function (e) {
    var $this   = $(this)
    var href    = $this.attr('href')
    if (href) {
      href = href.replace(/.*(?=#[^\s]+$)/, '') // strip for ie7
    }

    var target  = $this.attr('data-target') || href
    var $target = $(document).find(target)

    if (!$target.hasClass('carousel')) return

    var options = $.extend({}, $target.data(), $this.data())
    var slideIndex = $this.attr('data-slide-to')
    if (slideIndex) options.interval = false

    Plugin.call($target, options)

    if (slideIndex) {
      $target.data('bs.carousel').to(slideIndex)
    }

    e.preventDefault()
  }

  $(document)
    .on('click.bs.carousel.data-api', '[data-slide]', clickHandler)
    .on('click.bs.carousel.data-api', '[data-slide-to]', clickHandler)

  $(window).on('load', function () {
    $('[data-ride="carousel"]').each(function () {
      var $carousel = $(this)
      Plugin.call($carousel, $carousel.data())
    })
  })

}(jQuery);

/* WEBPACK VAR INJECTION */}.call(this, __webpack_require__(58)))

/***/ }),
/* 199 */
/***/ (function(module, exports, __webpack_require__) {

// extracted by mini-css-extract-plugin

/***/ }),
/* 200 */
/***/ (function(module, exports, __webpack_require__) {

// extracted by mini-css-extract-plugin

/***/ })
/******/ ]);
//# sourceMappingURL=global.js.map