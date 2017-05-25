webpackJsonp([11],{

/***/ 0:
/***/ function(module, exports, __webpack_require__) {

	/* WEBPACK VAR INJECTION */(function($) {'use strict';
	
	var SingleLinkModule = __webpack_require__(219);
	var DOMHelpers = __webpack_require__(2);
	var APIModule = __webpack_require__(81);
	var Helpers = __webpack_require__(95);
	var LinkHelpers = __webpack_require__(80);
	
	var updateBtnID = '#updateLinky',
	    cancelBtnID = '#cancelUpdateLinky';
	
	function init() {
	  // Hide query parameter from the special Safari redirect
	  if (window.location.href.indexOf('safari=1') > -1) {
	    history.replaceState({}, "", window.location.href.replace(/\??safari=1/, ''));
	  }
	
	  DOMHelpers.toggleBtnDisable(updateBtnID, true);
	  DOMHelpers.toggleBtnDisable(cancelBtnID, true);
	
	  setupEventHandlers();
	}
	
	function setupEventHandlers() {
	  $(".edit-link").click(function () {
	    $(SingleLinkModule.detailsButton).click();
	    return false;
	  });
	
	  $("button.darchive").click(function () {
	    handleDarchiving($(this));
	    return false;
	  });
	
	  $("input:file").change(function () {
	    var fileName = $(this).val();
	    var disableStatus = fileName ? false : true;
	    DOMHelpers.toggleBtnDisable(cancelBtnID, disableStatus);
	    DOMHelpers.toggleBtnDisable(updateBtnID, disableStatus);
	  });
	
	  $("button:reset").click(function () {
	    DOMHelpers.toggleBtnDisable(cancelBtnID, true);
	    DOMHelpers.toggleBtnDisable(updateBtnID, true);
	  });
	
	  $('#archive_upload_form').submit(function (e) {
	    e.preventDefault();
	    submitFile();
	  });
	  var inputValues = {};
	  $('#collapse-details').find('input').on('input propertychange change', function () {
	    var inputarea = $(this);
	    var name = inputarea.attr("name");
	    if (name == "file") return;
	    if (inputarea.val() == inputValues[name]) return;
	    inputValues[name] = inputarea.val();
	    var statusElement = inputarea.parent().find(".save-status");
	
	    LinkHelpers.saveInput(archive.guid, inputarea, statusElement, name, function () {
	      setTimeout(function () {
	        $(statusElement).html('');
	      }, 1000);
	    });
	  });
	}
	
	function submitFile() {
	  DOMHelpers.toggleBtnDisable(updateBtnID, true);
	  DOMHelpers.toggleBtnDisable(cancelBtnID, true);
	  var url = "/archives/" + archive.guid + "/";
	  var data = {};
	  data['file'] = $('#archive_upload_form').find('.file')[0].files[0];
	
	  var requestArgs = {
	    contentType: false,
	    processData: false
	  };
	  if (window.FormData) {
	    Helpers.sendFormData("PATCH", url, data, requestArgs).done(function (data) {
	      location = location;
	    });
	  } else {
	    $('#upload-error').text('Your browser version does not allow for this action. Please use a more modern browser.');
	  }
	}
	
	function handleDarchiving(context) {
	  var $this = context;
	  if (!$this.hasClass('disabled')) {
	    var prev_text = $this.text(),
	        currently_private = prev_text.indexOf('Public') > -1,
	        private_reason = currently_private ? null : $('select[name="private_reason"]').val() || 'user';
	
	    $this.addClass('disabled');
	    $this.text('Updating ...');
	
	    APIModule.request('PATCH', '/archives/' + archive.guid + '/', { is_private: !currently_private, private_reason: private_reason }, {
	      success: function success() {
	        window.location.reload(true);
	      },
	      error: function error(jqXHR) {
	        $this.removeClass('disabled');
	        $this.text(prev_text);
	      }
	    });
	  }
	}
	
	init();
	/* WEBPACK VAR INJECTION */}.call(exports, __webpack_require__(1)))

/***/ },

/***/ 2:
/***/ function(module, exports, __webpack_require__) {

	/* WEBPACK VAR INJECTION */(function($) {'use strict';
	
	Object.defineProperty(exports, "__esModule", {
	  value: true
	});
	exports.setInputValue = setInputValue;
	exports.removeElement = removeElement;
	exports.changeText = changeText;
	exports.toggleBtnDisable = toggleBtnDisable;
	exports.changeHTML = changeHTML;
	exports.emptyElement = emptyElement;
	exports.getValue = getValue;
	exports.removeClass = removeClass;
	exports.showElement = showElement;
	exports.hideElement = hideElement;
	exports.addCSS = addCSS;
	function setInputValue(domSelector, value) {
	  $(domSelector).val(value);
	}
	
	function removeElement(domSelector) {
	  $(domSelector).remove();
	}
	
	function changeText(domSelector, text) {
	  $(domSelector).text(text);
	}
	
	function toggleBtnDisable(domSelector, disableStatus) {
	  // if disableStatus is false, enable.
	  // if disableStatus is true, disable.
	  $(domSelector).prop('disabled', disableStatus);
	}
	
	function changeHTML(domSelector, value) {
	  $(domSelector).html(value);
	}
	
	function emptyElement(domSelector) {
	  $(domSelector).empty();
	}
	
	function getValue(domSelector) {
	  return $(domSelector).val();
	}
	
	function removeClass(domSelector, className) {
	  $(domSelector).removeClass(className);
	}
	
	function showElement(domSelector) {
	  $(domSelector).show();
	}
	
	function hideElement(domSelector) {
	  $(domSelector).hide();
	}
	
	function addCSS(domSelector, propertyName, propertyValue) {
	  $(domSelector).css(propertyName, propertyValue);
	}
	/* WEBPACK VAR INJECTION */}.call(exports, __webpack_require__(1)))

/***/ },

/***/ 12:
/***/ function(module, exports, __webpack_require__) {

	"use strict";
	
	exports.__esModule = true;
	
	var _iterator = __webpack_require__(13);
	
	var _iterator2 = _interopRequireDefault(_iterator);
	
	var _symbol = __webpack_require__(63);
	
	var _symbol2 = _interopRequireDefault(_symbol);
	
	var _typeof = typeof _symbol2.default === "function" && typeof _iterator2.default === "symbol" ? function (obj) { return typeof obj; } : function (obj) { return obj && typeof _symbol2.default === "function" && obj.constructor === _symbol2.default && obj !== _symbol2.default.prototype ? "symbol" : typeof obj; };
	
	function _interopRequireDefault(obj) { return obj && obj.__esModule ? obj : { default: obj }; }
	
	exports.default = typeof _symbol2.default === "function" && _typeof(_iterator2.default) === "symbol" ? function (obj) {
	  return typeof obj === "undefined" ? "undefined" : _typeof(obj);
	} : function (obj) {
	  return obj && typeof _symbol2.default === "function" && obj.constructor === _symbol2.default && obj !== _symbol2.default.prototype ? "symbol" : typeof obj === "undefined" ? "undefined" : _typeof(obj);
	};

/***/ },

/***/ 13:
/***/ function(module, exports, __webpack_require__) {

	module.exports = { "default": __webpack_require__(14), __esModule: true };

/***/ },

/***/ 14:
/***/ function(module, exports, __webpack_require__) {

	__webpack_require__(15);
	__webpack_require__(58);
	module.exports = __webpack_require__(62).f('iterator');

/***/ },

/***/ 62:
/***/ function(module, exports, __webpack_require__) {

	exports.f = __webpack_require__(55);

/***/ },

/***/ 63:
/***/ function(module, exports, __webpack_require__) {

	module.exports = { "default": __webpack_require__(64), __esModule: true };

/***/ },

/***/ 64:
/***/ function(module, exports, __webpack_require__) {

	__webpack_require__(65);
	__webpack_require__(76);
	__webpack_require__(77);
	__webpack_require__(78);
	module.exports = __webpack_require__(11).Symbol;

/***/ },

/***/ 65:
/***/ function(module, exports, __webpack_require__) {

	'use strict';
	// ECMAScript 6 symbols shim
	var global         = __webpack_require__(22)
	  , has            = __webpack_require__(36)
	  , DESCRIPTORS    = __webpack_require__(30)
	  , $export        = __webpack_require__(21)
	  , redefine       = __webpack_require__(35)
	  , META           = __webpack_require__(66).KEY
	  , $fails         = __webpack_require__(31)
	  , shared         = __webpack_require__(50)
	  , setToStringTag = __webpack_require__(54)
	  , uid            = __webpack_require__(51)
	  , wks            = __webpack_require__(55)
	  , wksExt         = __webpack_require__(62)
	  , wksDefine      = __webpack_require__(67)
	  , keyOf          = __webpack_require__(68)
	  , enumKeys       = __webpack_require__(69)
	  , isArray        = __webpack_require__(72)
	  , anObject       = __webpack_require__(27)
	  , toIObject      = __webpack_require__(43)
	  , toPrimitive    = __webpack_require__(33)
	  , createDesc     = __webpack_require__(34)
	  , _create        = __webpack_require__(39)
	  , gOPNExt        = __webpack_require__(73)
	  , $GOPD          = __webpack_require__(75)
	  , $DP            = __webpack_require__(26)
	  , $keys          = __webpack_require__(41)
	  , gOPD           = $GOPD.f
	  , dP             = $DP.f
	  , gOPN           = gOPNExt.f
	  , $Symbol        = global.Symbol
	  , $JSON          = global.JSON
	  , _stringify     = $JSON && $JSON.stringify
	  , PROTOTYPE      = 'prototype'
	  , HIDDEN         = wks('_hidden')
	  , TO_PRIMITIVE   = wks('toPrimitive')
	  , isEnum         = {}.propertyIsEnumerable
	  , SymbolRegistry = shared('symbol-registry')
	  , AllSymbols     = shared('symbols')
	  , OPSymbols      = shared('op-symbols')
	  , ObjectProto    = Object[PROTOTYPE]
	  , USE_NATIVE     = typeof $Symbol == 'function'
	  , QObject        = global.QObject;
	// Don't use setters in Qt Script, https://github.com/zloirock/core-js/issues/173
	var setter = !QObject || !QObject[PROTOTYPE] || !QObject[PROTOTYPE].findChild;
	
	// fallback for old Android, https://code.google.com/p/v8/issues/detail?id=687
	var setSymbolDesc = DESCRIPTORS && $fails(function(){
	  return _create(dP({}, 'a', {
	    get: function(){ return dP(this, 'a', {value: 7}).a; }
	  })).a != 7;
	}) ? function(it, key, D){
	  var protoDesc = gOPD(ObjectProto, key);
	  if(protoDesc)delete ObjectProto[key];
	  dP(it, key, D);
	  if(protoDesc && it !== ObjectProto)dP(ObjectProto, key, protoDesc);
	} : dP;
	
	var wrap = function(tag){
	  var sym = AllSymbols[tag] = _create($Symbol[PROTOTYPE]);
	  sym._k = tag;
	  return sym;
	};
	
	var isSymbol = USE_NATIVE && typeof $Symbol.iterator == 'symbol' ? function(it){
	  return typeof it == 'symbol';
	} : function(it){
	  return it instanceof $Symbol;
	};
	
	var $defineProperty = function defineProperty(it, key, D){
	  if(it === ObjectProto)$defineProperty(OPSymbols, key, D);
	  anObject(it);
	  key = toPrimitive(key, true);
	  anObject(D);
	  if(has(AllSymbols, key)){
	    if(!D.enumerable){
	      if(!has(it, HIDDEN))dP(it, HIDDEN, createDesc(1, {}));
	      it[HIDDEN][key] = true;
	    } else {
	      if(has(it, HIDDEN) && it[HIDDEN][key])it[HIDDEN][key] = false;
	      D = _create(D, {enumerable: createDesc(0, false)});
	    } return setSymbolDesc(it, key, D);
	  } return dP(it, key, D);
	};
	var $defineProperties = function defineProperties(it, P){
	  anObject(it);
	  var keys = enumKeys(P = toIObject(P))
	    , i    = 0
	    , l = keys.length
	    , key;
	  while(l > i)$defineProperty(it, key = keys[i++], P[key]);
	  return it;
	};
	var $create = function create(it, P){
	  return P === undefined ? _create(it) : $defineProperties(_create(it), P);
	};
	var $propertyIsEnumerable = function propertyIsEnumerable(key){
	  var E = isEnum.call(this, key = toPrimitive(key, true));
	  if(this === ObjectProto && has(AllSymbols, key) && !has(OPSymbols, key))return false;
	  return E || !has(this, key) || !has(AllSymbols, key) || has(this, HIDDEN) && this[HIDDEN][key] ? E : true;
	};
	var $getOwnPropertyDescriptor = function getOwnPropertyDescriptor(it, key){
	  it  = toIObject(it);
	  key = toPrimitive(key, true);
	  if(it === ObjectProto && has(AllSymbols, key) && !has(OPSymbols, key))return;
	  var D = gOPD(it, key);
	  if(D && has(AllSymbols, key) && !(has(it, HIDDEN) && it[HIDDEN][key]))D.enumerable = true;
	  return D;
	};
	var $getOwnPropertyNames = function getOwnPropertyNames(it){
	  var names  = gOPN(toIObject(it))
	    , result = []
	    , i      = 0
	    , key;
	  while(names.length > i){
	    if(!has(AllSymbols, key = names[i++]) && key != HIDDEN && key != META)result.push(key);
	  } return result;
	};
	var $getOwnPropertySymbols = function getOwnPropertySymbols(it){
	  var IS_OP  = it === ObjectProto
	    , names  = gOPN(IS_OP ? OPSymbols : toIObject(it))
	    , result = []
	    , i      = 0
	    , key;
	  while(names.length > i){
	    if(has(AllSymbols, key = names[i++]) && (IS_OP ? has(ObjectProto, key) : true))result.push(AllSymbols[key]);
	  } return result;
	};
	
	// 19.4.1.1 Symbol([description])
	if(!USE_NATIVE){
	  $Symbol = function Symbol(){
	    if(this instanceof $Symbol)throw TypeError('Symbol is not a constructor!');
	    var tag = uid(arguments.length > 0 ? arguments[0] : undefined);
	    var $set = function(value){
	      if(this === ObjectProto)$set.call(OPSymbols, value);
	      if(has(this, HIDDEN) && has(this[HIDDEN], tag))this[HIDDEN][tag] = false;
	      setSymbolDesc(this, tag, createDesc(1, value));
	    };
	    if(DESCRIPTORS && setter)setSymbolDesc(ObjectProto, tag, {configurable: true, set: $set});
	    return wrap(tag);
	  };
	  redefine($Symbol[PROTOTYPE], 'toString', function toString(){
	    return this._k;
	  });
	
	  $GOPD.f = $getOwnPropertyDescriptor;
	  $DP.f   = $defineProperty;
	  __webpack_require__(74).f = gOPNExt.f = $getOwnPropertyNames;
	  __webpack_require__(71).f  = $propertyIsEnumerable;
	  __webpack_require__(70).f = $getOwnPropertySymbols;
	
	  if(DESCRIPTORS && !__webpack_require__(20)){
	    redefine(ObjectProto, 'propertyIsEnumerable', $propertyIsEnumerable, true);
	  }
	
	  wksExt.f = function(name){
	    return wrap(wks(name));
	  }
	}
	
	$export($export.G + $export.W + $export.F * !USE_NATIVE, {Symbol: $Symbol});
	
	for(var symbols = (
	  // 19.4.2.2, 19.4.2.3, 19.4.2.4, 19.4.2.6, 19.4.2.8, 19.4.2.9, 19.4.2.10, 19.4.2.11, 19.4.2.12, 19.4.2.13, 19.4.2.14
	  'hasInstance,isConcatSpreadable,iterator,match,replace,search,species,split,toPrimitive,toStringTag,unscopables'
	).split(','), i = 0; symbols.length > i; )wks(symbols[i++]);
	
	for(var symbols = $keys(wks.store), i = 0; symbols.length > i; )wksDefine(symbols[i++]);
	
	$export($export.S + $export.F * !USE_NATIVE, 'Symbol', {
	  // 19.4.2.1 Symbol.for(key)
	  'for': function(key){
	    return has(SymbolRegistry, key += '')
	      ? SymbolRegistry[key]
	      : SymbolRegistry[key] = $Symbol(key);
	  },
	  // 19.4.2.5 Symbol.keyFor(sym)
	  keyFor: function keyFor(key){
	    if(isSymbol(key))return keyOf(SymbolRegistry, key);
	    throw TypeError(key + ' is not a symbol!');
	  },
	  useSetter: function(){ setter = true; },
	  useSimple: function(){ setter = false; }
	});
	
	$export($export.S + $export.F * !USE_NATIVE, 'Object', {
	  // 19.1.2.2 Object.create(O [, Properties])
	  create: $create,
	  // 19.1.2.4 Object.defineProperty(O, P, Attributes)
	  defineProperty: $defineProperty,
	  // 19.1.2.3 Object.defineProperties(O, Properties)
	  defineProperties: $defineProperties,
	  // 19.1.2.6 Object.getOwnPropertyDescriptor(O, P)
	  getOwnPropertyDescriptor: $getOwnPropertyDescriptor,
	  // 19.1.2.7 Object.getOwnPropertyNames(O)
	  getOwnPropertyNames: $getOwnPropertyNames,
	  // 19.1.2.8 Object.getOwnPropertySymbols(O)
	  getOwnPropertySymbols: $getOwnPropertySymbols
	});
	
	// 24.3.2 JSON.stringify(value [, replacer [, space]])
	$JSON && $export($export.S + $export.F * (!USE_NATIVE || $fails(function(){
	  var S = $Symbol();
	  // MS Edge converts symbol values to JSON as {}
	  // WebKit converts symbol values to JSON as null
	  // V8 throws on boxed symbols
	  return _stringify([S]) != '[null]' || _stringify({a: S}) != '{}' || _stringify(Object(S)) != '{}';
	})), 'JSON', {
	  stringify: function stringify(it){
	    if(it === undefined || isSymbol(it))return; // IE8 returns string on undefined
	    var args = [it]
	      , i    = 1
	      , replacer, $replacer;
	    while(arguments.length > i)args.push(arguments[i++]);
	    replacer = args[1];
	    if(typeof replacer == 'function')$replacer = replacer;
	    if($replacer || !isArray(replacer))replacer = function(key, value){
	      if($replacer)value = $replacer.call(this, key, value);
	      if(!isSymbol(value))return value;
	    };
	    args[1] = replacer;
	    return _stringify.apply($JSON, args);
	  }
	});
	
	// 19.4.3.4 Symbol.prototype[@@toPrimitive](hint)
	$Symbol[PROTOTYPE][TO_PRIMITIVE] || __webpack_require__(25)($Symbol[PROTOTYPE], TO_PRIMITIVE, $Symbol[PROTOTYPE].valueOf);
	// 19.4.3.5 Symbol.prototype[@@toStringTag]
	setToStringTag($Symbol, 'Symbol');
	// 20.2.1.9 Math[@@toStringTag]
	setToStringTag(Math, 'Math', true);
	// 24.3.3 JSON[@@toStringTag]
	setToStringTag(global.JSON, 'JSON', true);

/***/ },

/***/ 66:
/***/ function(module, exports, __webpack_require__) {

	var META     = __webpack_require__(51)('meta')
	  , isObject = __webpack_require__(28)
	  , has      = __webpack_require__(36)
	  , setDesc  = __webpack_require__(26).f
	  , id       = 0;
	var isExtensible = Object.isExtensible || function(){
	  return true;
	};
	var FREEZE = !__webpack_require__(31)(function(){
	  return isExtensible(Object.preventExtensions({}));
	});
	var setMeta = function(it){
	  setDesc(it, META, {value: {
	    i: 'O' + ++id, // object ID
	    w: {}          // weak collections IDs
	  }});
	};
	var fastKey = function(it, create){
	  // return primitive with prefix
	  if(!isObject(it))return typeof it == 'symbol' ? it : (typeof it == 'string' ? 'S' : 'P') + it;
	  if(!has(it, META)){
	    // can't set metadata to uncaught frozen object
	    if(!isExtensible(it))return 'F';
	    // not necessary to add metadata
	    if(!create)return 'E';
	    // add missing metadata
	    setMeta(it);
	  // return object ID
	  } return it[META].i;
	};
	var getWeak = function(it, create){
	  if(!has(it, META)){
	    // can't set metadata to uncaught frozen object
	    if(!isExtensible(it))return true;
	    // not necessary to add metadata
	    if(!create)return false;
	    // add missing metadata
	    setMeta(it);
	  // return hash weak collections IDs
	  } return it[META].w;
	};
	// add metadata on freeze-family methods calling
	var onFreeze = function(it){
	  if(FREEZE && meta.NEED && isExtensible(it) && !has(it, META))setMeta(it);
	  return it;
	};
	var meta = module.exports = {
	  KEY:      META,
	  NEED:     false,
	  fastKey:  fastKey,
	  getWeak:  getWeak,
	  onFreeze: onFreeze
	};

/***/ },

/***/ 67:
/***/ function(module, exports, __webpack_require__) {

	var global         = __webpack_require__(22)
	  , core           = __webpack_require__(11)
	  , LIBRARY        = __webpack_require__(20)
	  , wksExt         = __webpack_require__(62)
	  , defineProperty = __webpack_require__(26).f;
	module.exports = function(name){
	  var $Symbol = core.Symbol || (core.Symbol = LIBRARY ? {} : global.Symbol || {});
	  if(name.charAt(0) != '_' && !(name in $Symbol))defineProperty($Symbol, name, {value: wksExt.f(name)});
	};

/***/ },

/***/ 68:
/***/ function(module, exports, __webpack_require__) {

	var getKeys   = __webpack_require__(41)
	  , toIObject = __webpack_require__(43);
	module.exports = function(object, el){
	  var O      = toIObject(object)
	    , keys   = getKeys(O)
	    , length = keys.length
	    , index  = 0
	    , key;
	  while(length > index)if(O[key = keys[index++]] === el)return key;
	};

/***/ },

/***/ 69:
/***/ function(module, exports, __webpack_require__) {

	// all enumerable object keys, includes symbols
	var getKeys = __webpack_require__(41)
	  , gOPS    = __webpack_require__(70)
	  , pIE     = __webpack_require__(71);
	module.exports = function(it){
	  var result     = getKeys(it)
	    , getSymbols = gOPS.f;
	  if(getSymbols){
	    var symbols = getSymbols(it)
	      , isEnum  = pIE.f
	      , i       = 0
	      , key;
	    while(symbols.length > i)if(isEnum.call(it, key = symbols[i++]))result.push(key);
	  } return result;
	};

/***/ },

/***/ 70:
/***/ function(module, exports) {

	exports.f = Object.getOwnPropertySymbols;

/***/ },

/***/ 71:
/***/ function(module, exports) {

	exports.f = {}.propertyIsEnumerable;

/***/ },

/***/ 72:
/***/ function(module, exports, __webpack_require__) {

	// 7.2.2 IsArray(argument)
	var cof = __webpack_require__(45);
	module.exports = Array.isArray || function isArray(arg){
	  return cof(arg) == 'Array';
	};

/***/ },

/***/ 73:
/***/ function(module, exports, __webpack_require__) {

	// fallback for IE11 buggy Object.getOwnPropertyNames with iframe and window
	var toIObject = __webpack_require__(43)
	  , gOPN      = __webpack_require__(74).f
	  , toString  = {}.toString;
	
	var windowNames = typeof window == 'object' && window && Object.getOwnPropertyNames
	  ? Object.getOwnPropertyNames(window) : [];
	
	var getWindowNames = function(it){
	  try {
	    return gOPN(it);
	  } catch(e){
	    return windowNames.slice();
	  }
	};
	
	module.exports.f = function getOwnPropertyNames(it){
	  return windowNames && toString.call(it) == '[object Window]' ? getWindowNames(it) : gOPN(toIObject(it));
	};


/***/ },

/***/ 74:
/***/ function(module, exports, __webpack_require__) {

	// 19.1.2.7 / 15.2.3.4 Object.getOwnPropertyNames(O)
	var $keys      = __webpack_require__(42)
	  , hiddenKeys = __webpack_require__(52).concat('length', 'prototype');
	
	exports.f = Object.getOwnPropertyNames || function getOwnPropertyNames(O){
	  return $keys(O, hiddenKeys);
	};

/***/ },

/***/ 75:
/***/ function(module, exports, __webpack_require__) {

	var pIE            = __webpack_require__(71)
	  , createDesc     = __webpack_require__(34)
	  , toIObject      = __webpack_require__(43)
	  , toPrimitive    = __webpack_require__(33)
	  , has            = __webpack_require__(36)
	  , IE8_DOM_DEFINE = __webpack_require__(29)
	  , gOPD           = Object.getOwnPropertyDescriptor;
	
	exports.f = __webpack_require__(30) ? gOPD : function getOwnPropertyDescriptor(O, P){
	  O = toIObject(O);
	  P = toPrimitive(P, true);
	  if(IE8_DOM_DEFINE)try {
	    return gOPD(O, P);
	  } catch(e){ /* empty */ }
	  if(has(O, P))return createDesc(!pIE.f.call(O, P), O[P]);
	};

/***/ },

/***/ 76:
/***/ function(module, exports) {



/***/ },

/***/ 77:
/***/ function(module, exports, __webpack_require__) {

	__webpack_require__(67)('asyncIterator');

/***/ },

/***/ 78:
/***/ function(module, exports, __webpack_require__) {

	__webpack_require__(67)('observable');

/***/ },

/***/ 80:
/***/ function(module, exports, __webpack_require__) {

	'use strict';
	
	Object.defineProperty(exports, "__esModule", {
	  value: true
	});
	exports.findFaviconURL = findFaviconURL;
	exports.generateLinkFields = generateLinkFields;
	exports.saveInput = saveInput;
	var DOMHelpers = __webpack_require__(2);
	var APIModule = __webpack_require__(81);
	__webpack_require__(105); // add .format() to Date object
	
	
	function findFaviconURL(linkObj) {
	  if (!linkObj.captures) return '';
	
	  var favCapture = linkObj.captures.filter(function (capture) {
	    return capture.role == 'favicon' && capture.status == 'success';
	  });
	
	  return favCapture[0] ? favCapture[0].playback_url : '';
	}
	
	function generateLinkFields(link, query) {
	  link.favicon_url = this.findFaviconURL(link);
	  if (window.host) {
	    link.local_url = window.host + '/' + link.guid;
	  }
	  if (query && link.notes) {
	    link.search_query_in_notes = query && link.notes.indexOf(query) > -1;
	  }
	  link.expiration_date_formatted = new Date(link.expiration_date).format("F j, Y");
	  link.creation_timestamp_formatted = new Date(link.creation_timestamp).format("F j, Y");
	  if (Date.now() < Date.parse(link.archive_timestamp)) {
	    link.delete_available = true;
	  }
	  if (!link.captures.some(function (c) {
	    return c.role == "primary" && c.status == "success" || c.role == "screenshot" && c.role == "success";
	  })) {
	    link.is_failed = true;
	  };
	  return link;
	}
	
	var timeouts = {};
	// save changes in a given text box to the server
	function saveInput(guid, inputElement, statusElement, name, callback) {
	  DOMHelpers.changeHTML(statusElement, 'Saving...');
	
	  var timeoutKey = guid + name;
	  if (timeouts[timeoutKey]) clearTimeout(timeouts[timeoutKey]);
	
	  // use a setTimeout so notes are only saved once every half second
	  timeouts[timeoutKey] = setTimeout(function () {
	    var data = {};
	    data[name] = DOMHelpers.getValue(inputElement);
	    APIModule.request("PATCH", '/archives/' + guid + '/', data).done(function (data) {
	      DOMHelpers.changeHTML(statusElement, 'Saved!');
	      if (callback) callback(data);
	    });
	  }, 500);
	}

/***/ },

/***/ 81:
/***/ function(module, exports, __webpack_require__) {

	/* WEBPACK VAR INJECTION */(function($) {'use strict';
	
	Object.defineProperty(exports, "__esModule", {
	  value: true
	});
	
	var _typeof2 = __webpack_require__(12);
	
	var _typeof3 = _interopRequireDefault(_typeof2);
	
	var _stringify = __webpack_require__(9);
	
	var _stringify2 = _interopRequireDefault(_stringify);
	
	exports.request = request;
	exports.getErrorMessage = getErrorMessage;
	exports.showError = showError;
	
	function _interopRequireDefault(obj) { return obj && obj.__esModule ? obj : { default: obj }; }
	
	var ErrorHandler = __webpack_require__(82);
	var Helpers = __webpack_require__(95);
	
	function request(method, url, data, requestArgs) {
	  // set up arguments for API request
	  requestArgs = typeof requestArgs !== 'undefined' ? requestArgs : {};
	
	  if (data) {
	    if (method == 'GET') {
	      requestArgs.data = data;
	    } else {
	      requestArgs.data = (0, _stringify2.default)(data);
	      requestArgs.contentType = 'application/json';
	    }
	  }
	
	  requestArgs.url = api_path + url;
	  requestArgs.method = method;
	
	  if (!('error' in requestArgs)) requestArgs.error = showError;
	
	  return $.ajax(requestArgs);
	}
	
	// parse error results from API into string for display to user
	function getErrorMessage(jqXHR) {
	  var message;
	
	  if (jqXHR.status == 400 && jqXHR.responseText) {
	    try {
	      var parsedResponse = JSON.parse(jqXHR.responseText);
	      while ((typeof parsedResponse === 'undefined' ? 'undefined' : (0, _typeof3.default)(parsedResponse)) == 'object') {
	        for (var key in parsedResponse) {
	          if (parsedResponse.hasOwnProperty(key)) {
	            parsedResponse = parsedResponse[key];
	            break;
	          }
	        }
	      }
	      message = parsedResponse;
	    } catch (SyntaxError) {
	      ErrorHandler.airbrake.notify(SyntaxError);
	    }
	  } else if (jqXHR.status == 401) {
	    message = "<a href='/login'>You appear to be logged out. Please click here to log back in</a>.";
	  } else {
	    message = 'Error ' + jqXHR.status;
	  }
	
	  return message;
	}
	
	// display error results from API
	function showError(jqXHR) {
	  var message = getErrorMessage(jqXHR);
	  Helpers.informUser(message, 'danger');
	}
	/* WEBPACK VAR INJECTION */}.call(exports, __webpack_require__(1)))

/***/ },

/***/ 105:
/***/ function(module, exports) {

	"use strict";
	
	// JS file used as Django template -- gets included inline in our headers
	
	// given seconds since UTC epoch and a Django date filter/PHP date format string,
	// return formatted date in user's local time.
	function insertLocalDateTime(elementID, epochSeconds, formatString) {
	  var dateString = new Date(epochSeconds * 1000).format(formatString),
	      targetElement = document.getElementById(elementID);
	  targetElement.parentNode.insertBefore(document.createTextNode(dateString), targetElement);
	}
	
	// via http://jacwright.com/projects/javascript/date_format/
	// Simulates PHP's date function, which is similar to Django's date format filter
	Date.prototype.format = function (e) {
	  var t = "";var n = Date.replaceChars;for (var r = 0; r < e.length; r++) {
	    var i = e.charAt(r);if (r - 1 >= 0 && e.charAt(r - 1) == "\\") {
	      t += i;
	    } else if (n[i]) {
	      t += n[i].call(this);
	    } else if (i != "\\") {
	      t += i;
	    }
	  }return t;
	};Date.replaceChars = { shortMonths: ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"], longMonths: ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"], shortDays: ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"], longDays: ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"], d: function d() {
	    return (this.getDate() < 10 ? "0" : "") + this.getDate();
	  }, D: function D() {
	    return Date.replaceChars.shortDays[this.getDay()];
	  }, j: function j() {
	    return this.getDate();
	  }, l: function l() {
	    return Date.replaceChars.longDays[this.getDay()];
	  }, N: function N() {
	    return this.getDay() + 1;
	  }, S: function S() {
	    return this.getDate() % 10 == 1 && this.getDate() != 11 ? "st" : this.getDate() % 10 == 2 && this.getDate() != 12 ? "nd" : this.getDate() % 10 == 3 && this.getDate() != 13 ? "rd" : "th";
	  }, w: function w() {
	    return this.getDay();
	  }, z: function z() {
	    var e = new Date(this.getFullYear(), 0, 1);return Math.ceil((this - e) / 864e5);
	  }, W: function W() {
	    var e = new Date(this.getFullYear(), 0, 1);return Math.ceil(((this - e) / 864e5 + e.getDay() + 1) / 7);
	  }, F: function F() {
	    return Date.replaceChars.longMonths[this.getMonth()];
	  }, m: function m() {
	    return (this.getMonth() < 9 ? "0" : "") + (this.getMonth() + 1);
	  }, M: function M() {
	    return Date.replaceChars.shortMonths[this.getMonth()];
	  }, n: function n() {
	    return this.getMonth() + 1;
	  }, t: function t() {
	    var e = new Date();return new Date(e.getFullYear(), e.getMonth(), 0).getDate();
	  }, L: function L() {
	    var e = this.getFullYear();return e % 400 == 0 || e % 100 != 0 && e % 4 == 0;
	  }, o: function o() {
	    var e = new Date(this.valueOf());e.setDate(e.getDate() - (this.getDay() + 6) % 7 + 3);return e.getFullYear();
	  }, Y: function Y() {
	    return this.getFullYear();
	  }, y: function y() {
	    return ("" + this.getFullYear()).substr(2);
	  }, a: function a() {
	    return this.getHours() < 12 ? "am" : "pm";
	  }, A: function A() {
	    return this.getHours() < 12 ? "AM" : "PM";
	  }, B: function B() {
	    return Math.floor(((this.getUTCHours() + 1) % 24 + this.getUTCMinutes() / 60 + this.getUTCSeconds() / 3600) * 1e3 / 24);
	  }, g: function g() {
	    return this.getHours() % 12 || 12;
	  }, G: function G() {
	    return this.getHours();
	  }, h: function h() {
	    return ((this.getHours() % 12 || 12) < 10 ? "0" : "") + (this.getHours() % 12 || 12);
	  }, H: function H() {
	    return (this.getHours() < 10 ? "0" : "") + this.getHours();
	  }, i: function i() {
	    return (this.getMinutes() < 10 ? "0" : "") + this.getMinutes();
	  }, s: function s() {
	    return (this.getSeconds() < 10 ? "0" : "") + this.getSeconds();
	  }, u: function u() {
	    var e = this.getMilliseconds();return (e < 10 ? "00" : e < 100 ? "0" : "") + e;
	  }, e: function e() {
	    return "Not Yet Supported";
	  }, I: function I() {
	    var e = null;for (var t = 0; t < 12; ++t) {
	      var n = new Date(this.getFullYear(), t, 1);var r = n.getTimezoneOffset();if (e === null) e = r;else if (r < e) {
	        e = r;break;
	      } else if (r > e) break;
	    }return this.getTimezoneOffset() == e | 0;
	  }, O: function O() {
	    return (-this.getTimezoneOffset() < 0 ? "-" : "+") + (Math.abs(this.getTimezoneOffset() / 60) < 10 ? "0" : "") + Math.abs(this.getTimezoneOffset() / 60) + "00";
	  }, P: function P() {
	    return (-this.getTimezoneOffset() < 0 ? "-" : "+") + (Math.abs(this.getTimezoneOffset() / 60) < 10 ? "0" : "") + Math.abs(this.getTimezoneOffset() / 60) + ":00";
	  }, T: function T() {
	    var e = this.getMonth();this.setMonth(0);var t = this.toTimeString().replace(/^.+ \(?([^\)]+)\)?$/, "$1");this.setMonth(e);return t;
	  }, Z: function Z() {
	    return -this.getTimezoneOffset() * 60;
	  }, c: function c() {
	    return this.format("Y-m-d\\TH:i:sP");
	  }, r: function r() {
	    return this.toString();
	  }, U: function U() {
	    return this.getTime() / 1e3;
	  } };

/***/ },

/***/ 219:
/***/ function(module, exports) {

	"use strict";
	
	Object.defineProperty(exports, "__esModule", {
	  value: true
	});
	exports.handleShowDetails = handleShowDetails;
	var resizeTimeout, wrapper;
	
	var detailsButton = exports.detailsButton = document.getElementById("details-button");
	var detailsTray = document.getElementById("collapse-details");
	
	function init() {
	  adjustTopMargin();
	  var clicked = false;
	  if (detailsButton) {
	    detailsButton.onclick = function () {
	      clicked = !clicked;
	      handleShowDetails(clicked);
	    };
	  }
	
	  window.onresize = function () {
	    if (resizeTimeout != null) clearTimeout(resizeTimeout);
	    resizeTimeout = setTimeout(adjustTopMargin, 200);
	  };
	}
	
	function handleShowDetails(open) {
	  detailsButton.textContent = open ? "Hide record details" : "Show record details";
	  detailsTray.style.display = open ? "block" : "none";
	}
	
	function adjustTopMargin() {
	  wrapper = document.getElementsByClassName("capture-wrapper")[0];
	  var header = document.getElementsByTagName('header')[0];
	  if (!wrapper) return;
	  wrapper.style.marginTop = header.offsetHeight + "px";
	}
	
	init();

/***/ }

});
//# sourceMappingURL=single-link-permissions.js.map