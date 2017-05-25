webpackJsonp([3],{

/***/ 0:
/***/ function(module, exports, __webpack_require__) {

	'use strict';
	
	var LinkListModule = __webpack_require__(8);
	var FolderTreeModule = __webpack_require__(106);
	var CreateLinkModule = __webpack_require__(146);
	
	FolderTreeModule.init();
	LinkListModule.init();
	CreateLinkModule.init();

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

/***/ 3:
/***/ function(module, exports, __webpack_require__) {

	/* WEBPACK VAR INJECTION */(function($) {'use strict';
	
	Object.defineProperty(exports, "__esModule", {
	    value: true
	});
	exports.renderTemplate = renderTemplate;
	var Handlebars = __webpack_require__(4);
	
	Handlebars.registerHelper('truncatechars', function (str, len) {
	    if (str.length > len) {
	        var new_str = str.substr(0, len + 1);
	
	        while (new_str.length) {
	            var ch = new_str.substr(-1);
	            new_str = new_str.substr(0, -1);
	            if (ch == ' ') break;
	        }
	
	        if (new_str == '') new_str = str.substr(0, len);
	
	        return new Handlebars.SafeString(new_str + '...');
	    }
	    return str;
	});
	
	/*
	Using handlebar's compile method to generate templates on the fly
	*/
	
	var templateCache = {};
	function renderTemplate(templateId, args) {
	    var args = args || {};
	    var $this = $(templateId);
	    if (!templateCache[templateId]) {
	        templateCache[templateId] = Handlebars.compile($this.html());
	    }
	    return templateCache[templateId](args);
	}
	/* WEBPACK VAR INJECTION */}.call(exports, __webpack_require__(1)))

/***/ },

/***/ 4:
/***/ function(module, exports, __webpack_require__) {

	/*!
	
	 handlebars v4.0.5
	
	Copyright (C) 2011-2015 by Yehuda Katz
	
	Permission is hereby granted, free of charge, to any person obtaining a copy
	of this software and associated documentation files (the "Software"), to deal
	in the Software without restriction, including without limitation the rights
	to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
	copies of the Software, and to permit persons to whom the Software is
	furnished to do so, subject to the following conditions:
	
	The above copyright notice and this permission notice shall be included in
	all copies or substantial portions of the Software.
	
	THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
	IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
	FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
	AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
	LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
	OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
	THE SOFTWARE.
	
	@license
	*/
	!function(a,b){ true?module.exports=b():"function"==typeof define&&define.amd?define([],b):"object"==typeof exports?exports.Handlebars=b():a.Handlebars=b()}(this,function(){return function(a){function b(d){if(c[d])return c[d].exports;var e=c[d]={exports:{},id:d,loaded:!1};return a[d].call(e.exports,e,e.exports,b),e.loaded=!0,e.exports}var c={};return b.m=a,b.c=c,b.p="",b(0)}([function(a,b,c){"use strict";function d(){var a=r();return a.compile=function(b,c){return k.compile(b,c,a)},a.precompile=function(b,c){return k.precompile(b,c,a)},a.AST=i["default"],a.Compiler=k.Compiler,a.JavaScriptCompiler=m["default"],a.Parser=j.parser,a.parse=j.parse,a}var e=c(1)["default"];b.__esModule=!0;var f=c(2),g=e(f),h=c(21),i=e(h),j=c(22),k=c(27),l=c(28),m=e(l),n=c(25),o=e(n),p=c(20),q=e(p),r=g["default"].create,s=d();s.create=d,q["default"](s),s.Visitor=o["default"],s["default"]=s,b["default"]=s,a.exports=b["default"]},function(a,b){"use strict";b["default"]=function(a){return a&&a.__esModule?a:{"default":a}},b.__esModule=!0},function(a,b,c){"use strict";function d(){var a=new h.HandlebarsEnvironment;return n.extend(a,h),a.SafeString=j["default"],a.Exception=l["default"],a.Utils=n,a.escapeExpression=n.escapeExpression,a.VM=p,a.template=function(b){return p.template(b,a)},a}var e=c(3)["default"],f=c(1)["default"];b.__esModule=!0;var g=c(4),h=e(g),i=c(18),j=f(i),k=c(6),l=f(k),m=c(5),n=e(m),o=c(19),p=e(o),q=c(20),r=f(q),s=d();s.create=d,r["default"](s),s["default"]=s,b["default"]=s,a.exports=b["default"]},function(a,b){"use strict";b["default"]=function(a){if(a&&a.__esModule)return a;var b={};if(null!=a)for(var c in a)Object.prototype.hasOwnProperty.call(a,c)&&(b[c]=a[c]);return b["default"]=a,b},b.__esModule=!0},function(a,b,c){"use strict";function d(a,b,c){this.helpers=a||{},this.partials=b||{},this.decorators=c||{},i.registerDefaultHelpers(this),j.registerDefaultDecorators(this)}var e=c(1)["default"];b.__esModule=!0,b.HandlebarsEnvironment=d;var f=c(5),g=c(6),h=e(g),i=c(7),j=c(15),k=c(17),l=e(k),m="4.0.5";b.VERSION=m;var n=7;b.COMPILER_REVISION=n;var o={1:"<= 1.0.rc.2",2:"== 1.0.0-rc.3",3:"== 1.0.0-rc.4",4:"== 1.x.x",5:"== 2.0.0-alpha.x",6:">= 2.0.0-beta.1",7:">= 4.0.0"};b.REVISION_CHANGES=o;var p="[object Object]";d.prototype={constructor:d,logger:l["default"],log:l["default"].log,registerHelper:function(a,b){if(f.toString.call(a)===p){if(b)throw new h["default"]("Arg not supported with multiple helpers");f.extend(this.helpers,a)}else this.helpers[a]=b},unregisterHelper:function(a){delete this.helpers[a]},registerPartial:function(a,b){if(f.toString.call(a)===p)f.extend(this.partials,a);else{if("undefined"==typeof b)throw new h["default"]('Attempting to register a partial called "'+a+'" as undefined');this.partials[a]=b}},unregisterPartial:function(a){delete this.partials[a]},registerDecorator:function(a,b){if(f.toString.call(a)===p){if(b)throw new h["default"]("Arg not supported with multiple decorators");f.extend(this.decorators,a)}else this.decorators[a]=b},unregisterDecorator:function(a){delete this.decorators[a]}};var q=l["default"].log;b.log=q,b.createFrame=f.createFrame,b.logger=l["default"]},function(a,b){"use strict";function c(a){return k[a]}function d(a){for(var b=1;b<arguments.length;b++)for(var c in arguments[b])Object.prototype.hasOwnProperty.call(arguments[b],c)&&(a[c]=arguments[b][c]);return a}function e(a,b){for(var c=0,d=a.length;d>c;c++)if(a[c]===b)return c;return-1}function f(a){if("string"!=typeof a){if(a&&a.toHTML)return a.toHTML();if(null==a)return"";if(!a)return a+"";a=""+a}return m.test(a)?a.replace(l,c):a}function g(a){return a||0===a?p(a)&&0===a.length?!0:!1:!0}function h(a){var b=d({},a);return b._parent=a,b}function i(a,b){return a.path=b,a}function j(a,b){return(a?a+".":"")+b}b.__esModule=!0,b.extend=d,b.indexOf=e,b.escapeExpression=f,b.isEmpty=g,b.createFrame=h,b.blockParams=i,b.appendContextPath=j;var k={"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#x27;","`":"&#x60;","=":"&#x3D;"},l=/[&<>"'`=]/g,m=/[&<>"'`=]/,n=Object.prototype.toString;b.toString=n;var o=function(a){return"function"==typeof a};o(/x/)&&(b.isFunction=o=function(a){return"function"==typeof a&&"[object Function]"===n.call(a)}),b.isFunction=o;var p=Array.isArray||function(a){return a&&"object"==typeof a?"[object Array]"===n.call(a):!1};b.isArray=p},function(a,b){"use strict";function c(a,b){var e=b&&b.loc,f=void 0,g=void 0;e&&(f=e.start.line,g=e.start.column,a+=" - "+f+":"+g);for(var h=Error.prototype.constructor.call(this,a),i=0;i<d.length;i++)this[d[i]]=h[d[i]];Error.captureStackTrace&&Error.captureStackTrace(this,c),e&&(this.lineNumber=f,this.column=g)}b.__esModule=!0;var d=["description","fileName","lineNumber","message","name","number","stack"];c.prototype=new Error,b["default"]=c,a.exports=b["default"]},function(a,b,c){"use strict";function d(a){g["default"](a),i["default"](a),k["default"](a),m["default"](a),o["default"](a),q["default"](a),s["default"](a)}var e=c(1)["default"];b.__esModule=!0,b.registerDefaultHelpers=d;var f=c(8),g=e(f),h=c(9),i=e(h),j=c(10),k=e(j),l=c(11),m=e(l),n=c(12),o=e(n),p=c(13),q=e(p),r=c(14),s=e(r)},function(a,b,c){"use strict";b.__esModule=!0;var d=c(5);b["default"]=function(a){a.registerHelper("blockHelperMissing",function(b,c){var e=c.inverse,f=c.fn;if(b===!0)return f(this);if(b===!1||null==b)return e(this);if(d.isArray(b))return b.length>0?(c.ids&&(c.ids=[c.name]),a.helpers.each(b,c)):e(this);if(c.data&&c.ids){var g=d.createFrame(c.data);g.contextPath=d.appendContextPath(c.data.contextPath,c.name),c={data:g}}return f(b,c)})},a.exports=b["default"]},function(a,b,c){"use strict";var d=c(1)["default"];b.__esModule=!0;var e=c(5),f=c(6),g=d(f);b["default"]=function(a){a.registerHelper("each",function(a,b){function c(b,c,f){j&&(j.key=b,j.index=c,j.first=0===c,j.last=!!f,k&&(j.contextPath=k+b)),i+=d(a[b],{data:j,blockParams:e.blockParams([a[b],b],[k+b,null])})}if(!b)throw new g["default"]("Must pass iterator to #each");var d=b.fn,f=b.inverse,h=0,i="",j=void 0,k=void 0;if(b.data&&b.ids&&(k=e.appendContextPath(b.data.contextPath,b.ids[0])+"."),e.isFunction(a)&&(a=a.call(this)),b.data&&(j=e.createFrame(b.data)),a&&"object"==typeof a)if(e.isArray(a))for(var l=a.length;l>h;h++)h in a&&c(h,h,h===a.length-1);else{var m=void 0;for(var n in a)a.hasOwnProperty(n)&&(void 0!==m&&c(m,h-1),m=n,h++);void 0!==m&&c(m,h-1,!0)}return 0===h&&(i=f(this)),i})},a.exports=b["default"]},function(a,b,c){"use strict";var d=c(1)["default"];b.__esModule=!0;var e=c(6),f=d(e);b["default"]=function(a){a.registerHelper("helperMissing",function(){if(1!==arguments.length)throw new f["default"]('Missing helper: "'+arguments[arguments.length-1].name+'"')})},a.exports=b["default"]},function(a,b,c){"use strict";b.__esModule=!0;var d=c(5);b["default"]=function(a){a.registerHelper("if",function(a,b){return d.isFunction(a)&&(a=a.call(this)),!b.hash.includeZero&&!a||d.isEmpty(a)?b.inverse(this):b.fn(this)}),a.registerHelper("unless",function(b,c){return a.helpers["if"].call(this,b,{fn:c.inverse,inverse:c.fn,hash:c.hash})})},a.exports=b["default"]},function(a,b){"use strict";b.__esModule=!0,b["default"]=function(a){a.registerHelper("log",function(){for(var b=[void 0],c=arguments[arguments.length-1],d=0;d<arguments.length-1;d++)b.push(arguments[d]);var e=1;null!=c.hash.level?e=c.hash.level:c.data&&null!=c.data.level&&(e=c.data.level),b[0]=e,a.log.apply(a,b)})},a.exports=b["default"]},function(a,b){"use strict";b.__esModule=!0,b["default"]=function(a){a.registerHelper("lookup",function(a,b){return a&&a[b]})},a.exports=b["default"]},function(a,b,c){"use strict";b.__esModule=!0;var d=c(5);b["default"]=function(a){a.registerHelper("with",function(a,b){d.isFunction(a)&&(a=a.call(this));var c=b.fn;if(d.isEmpty(a))return b.inverse(this);var e=b.data;return b.data&&b.ids&&(e=d.createFrame(b.data),e.contextPath=d.appendContextPath(b.data.contextPath,b.ids[0])),c(a,{data:e,blockParams:d.blockParams([a],[e&&e.contextPath])})})},a.exports=b["default"]},function(a,b,c){"use strict";function d(a){g["default"](a)}var e=c(1)["default"];b.__esModule=!0,b.registerDefaultDecorators=d;var f=c(16),g=e(f)},function(a,b,c){"use strict";b.__esModule=!0;var d=c(5);b["default"]=function(a){a.registerDecorator("inline",function(a,b,c,e){var f=a;return b.partials||(b.partials={},f=function(e,f){var g=c.partials;c.partials=d.extend({},g,b.partials);var h=a(e,f);return c.partials=g,h}),b.partials[e.args[0]]=e.fn,f})},a.exports=b["default"]},function(a,b,c){"use strict";b.__esModule=!0;var d=c(5),e={methodMap:["debug","info","warn","error"],level:"info",lookupLevel:function(a){if("string"==typeof a){var b=d.indexOf(e.methodMap,a.toLowerCase());a=b>=0?b:parseInt(a,10)}return a},log:function(a){if(a=e.lookupLevel(a),"undefined"!=typeof console&&e.lookupLevel(e.level)<=a){var b=e.methodMap[a];console[b]||(b="log");for(var c=arguments.length,d=Array(c>1?c-1:0),f=1;c>f;f++)d[f-1]=arguments[f];console[b].apply(console,d)}}};b["default"]=e,a.exports=b["default"]},function(a,b){"use strict";function c(a){this.string=a}b.__esModule=!0,c.prototype.toString=c.prototype.toHTML=function(){return""+this.string},b["default"]=c,a.exports=b["default"]},function(a,b,c){"use strict";function d(a){var b=a&&a[0]||1,c=r.COMPILER_REVISION;if(b!==c){if(c>b){var d=r.REVISION_CHANGES[c],e=r.REVISION_CHANGES[b];throw new q["default"]("Template was precompiled with an older version of Handlebars than the current runtime. Please update your precompiler to a newer version ("+d+") or downgrade your runtime to an older version ("+e+").")}throw new q["default"]("Template was precompiled with a newer version of Handlebars than the current runtime. Please update your runtime to a newer version ("+a[1]+").")}}function e(a,b){function c(c,d,e){e.hash&&(d=o.extend({},d,e.hash),e.ids&&(e.ids[0]=!0)),c=b.VM.resolvePartial.call(this,c,d,e);var f=b.VM.invokePartial.call(this,c,d,e);if(null==f&&b.compile&&(e.partials[e.name]=b.compile(c,a.compilerOptions,b),f=e.partials[e.name](d,e)),null!=f){if(e.indent){for(var g=f.split("\n"),h=0,i=g.length;i>h&&(g[h]||h+1!==i);h++)g[h]=e.indent+g[h];f=g.join("\n")}return f}throw new q["default"]("The partial "+e.name+" could not be compiled when running in runtime-only mode")}function d(b){function c(b){return""+a.main(e,b,e.helpers,e.partials,g,i,h)}var f=arguments.length<=1||void 0===arguments[1]?{}:arguments[1],g=f.data;d._setup(f),!f.partial&&a.useData&&(g=j(b,g));var h=void 0,i=a.useBlockParams?[]:void 0;return a.useDepths&&(h=f.depths?b!==f.depths[0]?[b].concat(f.depths):f.depths:[b]),(c=k(a.main,c,e,f.depths||[],g,i))(b,f)}if(!b)throw new q["default"]("No environment passed to template");if(!a||!a.main)throw new q["default"]("Unknown template object: "+typeof a);a.main.decorator=a.main_d,b.VM.checkRevision(a.compiler);var e={strict:function(a,b){if(!(b in a))throw new q["default"]('"'+b+'" not defined in '+a);return a[b]},lookup:function(a,b){for(var c=a.length,d=0;c>d;d++)if(a[d]&&null!=a[d][b])return a[d][b]},lambda:function(a,b){return"function"==typeof a?a.call(b):a},escapeExpression:o.escapeExpression,invokePartial:c,fn:function(b){var c=a[b];return c.decorator=a[b+"_d"],c},programs:[],program:function(a,b,c,d,e){var g=this.programs[a],h=this.fn(a);return b||e||d||c?g=f(this,a,h,b,c,d,e):g||(g=this.programs[a]=f(this,a,h)),g},data:function(a,b){for(;a&&b--;)a=a._parent;return a},merge:function(a,b){var c=a||b;return a&&b&&a!==b&&(c=o.extend({},b,a)),c},noop:b.VM.noop,compilerInfo:a.compiler};return d.isTop=!0,d._setup=function(c){c.partial?(e.helpers=c.helpers,e.partials=c.partials,e.decorators=c.decorators):(e.helpers=e.merge(c.helpers,b.helpers),a.usePartial&&(e.partials=e.merge(c.partials,b.partials)),(a.usePartial||a.useDecorators)&&(e.decorators=e.merge(c.decorators,b.decorators)))},d._child=function(b,c,d,g){if(a.useBlockParams&&!d)throw new q["default"]("must pass block params");if(a.useDepths&&!g)throw new q["default"]("must pass parent depths");return f(e,b,a[b],c,0,d,g)},d}function f(a,b,c,d,e,f,g){function h(b){var e=arguments.length<=1||void 0===arguments[1]?{}:arguments[1],h=g;return g&&b!==g[0]&&(h=[b].concat(g)),c(a,b,a.helpers,a.partials,e.data||d,f&&[e.blockParams].concat(f),h)}return h=k(c,h,a,g,d,f),h.program=b,h.depth=g?g.length:0,h.blockParams=e||0,h}function g(a,b,c){return a?a.call||c.name||(c.name=a,a=c.partials[a]):a="@partial-block"===c.name?c.data["partial-block"]:c.partials[c.name],a}function h(a,b,c){c.partial=!0,c.ids&&(c.data.contextPath=c.ids[0]||c.data.contextPath);var d=void 0;if(c.fn&&c.fn!==i&&(c.data=r.createFrame(c.data),d=c.data["partial-block"]=c.fn,d.partials&&(c.partials=o.extend({},c.partials,d.partials))),void 0===a&&d&&(a=d),void 0===a)throw new q["default"]("The partial "+c.name+" could not be found");return a instanceof Function?a(b,c):void 0}function i(){return""}function j(a,b){return b&&"root"in b||(b=b?r.createFrame(b):{},b.root=a),b}function k(a,b,c,d,e,f){if(a.decorator){var g={};b=a.decorator(b,g,c,d&&d[0],e,f,d),o.extend(b,g)}return b}var l=c(3)["default"],m=c(1)["default"];b.__esModule=!0,b.checkRevision=d,b.template=e,b.wrapProgram=f,b.resolvePartial=g,b.invokePartial=h,b.noop=i;var n=c(5),o=l(n),p=c(6),q=m(p),r=c(4)},function(a,b){(function(c){"use strict";b.__esModule=!0,b["default"]=function(a){var b="undefined"!=typeof c?c:window,d=b.Handlebars;a.noConflict=function(){return b.Handlebars===a&&(b.Handlebars=d),a}},a.exports=b["default"]}).call(b,function(){return this}())},function(a,b){"use strict";b.__esModule=!0;var c={helpers:{helperExpression:function(a){return"SubExpression"===a.type||("MustacheStatement"===a.type||"BlockStatement"===a.type)&&!!(a.params&&a.params.length||a.hash)},scopedId:function(a){return/^\.|this\b/.test(a.original)},simpleId:function(a){return 1===a.parts.length&&!c.helpers.scopedId(a)&&!a.depth}}};b["default"]=c,a.exports=b["default"]},function(a,b,c){"use strict";function d(a,b){if("Program"===a.type)return a;h["default"].yy=n,n.locInfo=function(a){return new n.SourceLocation(b&&b.srcName,a)};var c=new j["default"](b);return c.accept(h["default"].parse(a))}var e=c(1)["default"],f=c(3)["default"];b.__esModule=!0,b.parse=d;var g=c(23),h=e(g),i=c(24),j=e(i),k=c(26),l=f(k),m=c(5);b.parser=h["default"];var n={};m.extend(n,l)},function(a,b){"use strict";var c=function(){function a(){this.yy={}}var b={trace:function(){},yy:{},symbols_:{error:2,root:3,program:4,EOF:5,program_repetition0:6,statement:7,mustache:8,block:9,rawBlock:10,partial:11,partialBlock:12,content:13,COMMENT:14,CONTENT:15,openRawBlock:16,rawBlock_repetition_plus0:17,END_RAW_BLOCK:18,OPEN_RAW_BLOCK:19,helperName:20,openRawBlock_repetition0:21,openRawBlock_option0:22,CLOSE_RAW_BLOCK:23,openBlock:24,block_option0:25,closeBlock:26,openInverse:27,block_option1:28,OPEN_BLOCK:29,openBlock_repetition0:30,openBlock_option0:31,openBlock_option1:32,CLOSE:33,OPEN_INVERSE:34,openInverse_repetition0:35,openInverse_option0:36,openInverse_option1:37,openInverseChain:38,OPEN_INVERSE_CHAIN:39,openInverseChain_repetition0:40,openInverseChain_option0:41,openInverseChain_option1:42,inverseAndProgram:43,INVERSE:44,inverseChain:45,inverseChain_option0:46,OPEN_ENDBLOCK:47,OPEN:48,mustache_repetition0:49,mustache_option0:50,OPEN_UNESCAPED:51,mustache_repetition1:52,mustache_option1:53,CLOSE_UNESCAPED:54,OPEN_PARTIAL:55,partialName:56,partial_repetition0:57,partial_option0:58,openPartialBlock:59,OPEN_PARTIAL_BLOCK:60,openPartialBlock_repetition0:61,openPartialBlock_option0:62,param:63,sexpr:64,OPEN_SEXPR:65,sexpr_repetition0:66,sexpr_option0:67,CLOSE_SEXPR:68,hash:69,hash_repetition_plus0:70,hashSegment:71,ID:72,EQUALS:73,blockParams:74,OPEN_BLOCK_PARAMS:75,blockParams_repetition_plus0:76,CLOSE_BLOCK_PARAMS:77,path:78,dataName:79,STRING:80,NUMBER:81,BOOLEAN:82,UNDEFINED:83,NULL:84,DATA:85,pathSegments:86,SEP:87,$accept:0,$end:1},terminals_:{2:"error",5:"EOF",14:"COMMENT",15:"CONTENT",18:"END_RAW_BLOCK",19:"OPEN_RAW_BLOCK",23:"CLOSE_RAW_BLOCK",29:"OPEN_BLOCK",33:"CLOSE",34:"OPEN_INVERSE",39:"OPEN_INVERSE_CHAIN",44:"INVERSE",47:"OPEN_ENDBLOCK",48:"OPEN",51:"OPEN_UNESCAPED",54:"CLOSE_UNESCAPED",55:"OPEN_PARTIAL",60:"OPEN_PARTIAL_BLOCK",65:"OPEN_SEXPR",68:"CLOSE_SEXPR",72:"ID",73:"EQUALS",75:"OPEN_BLOCK_PARAMS",77:"CLOSE_BLOCK_PARAMS",80:"STRING",81:"NUMBER",82:"BOOLEAN",83:"UNDEFINED",84:"NULL",85:"DATA",87:"SEP"},productions_:[0,[3,2],[4,1],[7,1],[7,1],[7,1],[7,1],[7,1],[7,1],[7,1],[13,1],[10,3],[16,5],[9,4],[9,4],[24,6],[27,6],[38,6],[43,2],[45,3],[45,1],[26,3],[8,5],[8,5],[11,5],[12,3],[59,5],[63,1],[63,1],[64,5],[69,1],[71,3],[74,3],[20,1],[20,1],[20,1],[20,1],[20,1],[20,1],[20,1],[56,1],[56,1],[79,2],[78,1],[86,3],[86,1],[6,0],[6,2],[17,1],[17,2],[21,0],[21,2],[22,0],[22,1],[25,0],[25,1],[28,0],[28,1],[30,0],[30,2],[31,0],[31,1],[32,0],[32,1],[35,0],[35,2],[36,0],[36,1],[37,0],[37,1],[40,0],[40,2],[41,0],[41,1],[42,0],[42,1],[46,0],[46,1],[49,0],[49,2],[50,0],[50,1],[52,0],[52,2],[53,0],[53,1],[57,0],[57,2],[58,0],[58,1],[61,0],[61,2],[62,0],[62,1],[66,0],[66,2],[67,0],[67,1],[70,1],[70,2],[76,1],[76,2]],performAction:function(a,b,c,d,e,f,g){var h=f.length-1;switch(e){case 1:return f[h-1];case 2:this.$=d.prepareProgram(f[h]);break;case 3:this.$=f[h];break;case 4:this.$=f[h];break;case 5:this.$=f[h];break;case 6:this.$=f[h];break;case 7:this.$=f[h];break;case 8:this.$=f[h];break;case 9:this.$={type:"CommentStatement",value:d.stripComment(f[h]),strip:d.stripFlags(f[h],f[h]),loc:d.locInfo(this._$)};break;case 10:this.$={type:"ContentStatement",original:f[h],value:f[h],loc:d.locInfo(this._$)};break;case 11:this.$=d.prepareRawBlock(f[h-2],f[h-1],f[h],this._$);break;case 12:this.$={path:f[h-3],params:f[h-2],hash:f[h-1]};break;case 13:this.$=d.prepareBlock(f[h-3],f[h-2],f[h-1],f[h],!1,this._$);break;case 14:this.$=d.prepareBlock(f[h-3],f[h-2],f[h-1],f[h],!0,this._$);break;case 15:this.$={open:f[h-5],path:f[h-4],params:f[h-3],hash:f[h-2],blockParams:f[h-1],strip:d.stripFlags(f[h-5],f[h])};break;case 16:this.$={path:f[h-4],params:f[h-3],hash:f[h-2],blockParams:f[h-1],strip:d.stripFlags(f[h-5],f[h])};break;case 17:this.$={path:f[h-4],params:f[h-3],hash:f[h-2],blockParams:f[h-1],strip:d.stripFlags(f[h-5],f[h])};break;case 18:this.$={strip:d.stripFlags(f[h-1],f[h-1]),program:f[h]};break;case 19:var i=d.prepareBlock(f[h-2],f[h-1],f[h],f[h],!1,this._$),j=d.prepareProgram([i],f[h-1].loc);j.chained=!0,this.$={strip:f[h-2].strip,program:j,chain:!0};break;case 20:this.$=f[h];break;case 21:this.$={path:f[h-1],strip:d.stripFlags(f[h-2],f[h])};break;case 22:this.$=d.prepareMustache(f[h-3],f[h-2],f[h-1],f[h-4],d.stripFlags(f[h-4],f[h]),this._$);break;case 23:this.$=d.prepareMustache(f[h-3],f[h-2],f[h-1],f[h-4],d.stripFlags(f[h-4],f[h]),this._$);break;case 24:this.$={type:"PartialStatement",name:f[h-3],params:f[h-2],hash:f[h-1],indent:"",strip:d.stripFlags(f[h-4],f[h]),loc:d.locInfo(this._$)};break;case 25:this.$=d.preparePartialBlock(f[h-2],f[h-1],f[h],this._$);break;case 26:this.$={path:f[h-3],params:f[h-2],hash:f[h-1],strip:d.stripFlags(f[h-4],f[h])};break;case 27:this.$=f[h];break;case 28:this.$=f[h];break;case 29:this.$={type:"SubExpression",path:f[h-3],params:f[h-2],hash:f[h-1],loc:d.locInfo(this._$)};break;case 30:this.$={type:"Hash",pairs:f[h],loc:d.locInfo(this._$)};break;case 31:this.$={type:"HashPair",key:d.id(f[h-2]),value:f[h],loc:d.locInfo(this._$)};break;case 32:this.$=d.id(f[h-1]);break;case 33:this.$=f[h];break;case 34:this.$=f[h];break;case 35:this.$={type:"StringLiteral",value:f[h],original:f[h],loc:d.locInfo(this._$)};break;case 36:this.$={type:"NumberLiteral",value:Number(f[h]),original:Number(f[h]),loc:d.locInfo(this._$)};break;case 37:this.$={type:"BooleanLiteral",value:"true"===f[h],original:"true"===f[h],loc:d.locInfo(this._$)};break;case 38:this.$={type:"UndefinedLiteral",original:void 0,value:void 0,loc:d.locInfo(this._$)};break;case 39:this.$={type:"NullLiteral",original:null,value:null,loc:d.locInfo(this._$)};break;case 40:this.$=f[h];break;case 41:this.$=f[h];break;case 42:this.$=d.preparePath(!0,f[h],this._$);break;case 43:this.$=d.preparePath(!1,f[h],this._$);break;case 44:f[h-2].push({part:d.id(f[h]),original:f[h],separator:f[h-1]}),this.$=f[h-2];break;case 45:this.$=[{part:d.id(f[h]),original:f[h]}];break;case 46:this.$=[];break;case 47:f[h-1].push(f[h]);break;case 48:this.$=[f[h]];break;case 49:f[h-1].push(f[h]);break;case 50:this.$=[];break;case 51:f[h-1].push(f[h]);break;case 58:this.$=[];break;case 59:f[h-1].push(f[h]);break;case 64:this.$=[];break;case 65:f[h-1].push(f[h]);break;case 70:this.$=[];break;case 71:f[h-1].push(f[h]);break;case 78:this.$=[];break;case 79:f[h-1].push(f[h]);break;case 82:this.$=[];break;case 83:f[h-1].push(f[h]);break;case 86:this.$=[];break;case 87:f[h-1].push(f[h]);break;case 90:this.$=[];break;case 91:f[h-1].push(f[h]);break;case 94:this.$=[];break;case 95:f[h-1].push(f[h]);break;case 98:this.$=[f[h]];break;case 99:f[h-1].push(f[h]);break;case 100:this.$=[f[h]];break;case 101:f[h-1].push(f[h])}},table:[{3:1,4:2,5:[2,46],6:3,14:[2,46],15:[2,46],19:[2,46],29:[2,46],34:[2,46],48:[2,46],51:[2,46],55:[2,46],60:[2,46]},{1:[3]},{5:[1,4]},{5:[2,2],7:5,8:6,9:7,10:8,11:9,12:10,13:11,14:[1,12],15:[1,20],16:17,19:[1,23],24:15,27:16,29:[1,21],34:[1,22],39:[2,2],44:[2,2],47:[2,2],48:[1,13],51:[1,14],55:[1,18],59:19,60:[1,24]},{1:[2,1]},{5:[2,47],14:[2,47],15:[2,47],19:[2,47],29:[2,47],34:[2,47],39:[2,47],44:[2,47],47:[2,47],48:[2,47],51:[2,47],55:[2,47],60:[2,47]},{5:[2,3],14:[2,3],15:[2,3],19:[2,3],29:[2,3],34:[2,3],39:[2,3],44:[2,3],47:[2,3],48:[2,3],51:[2,3],55:[2,3],60:[2,3]},{5:[2,4],14:[2,4],15:[2,4],19:[2,4],29:[2,4],34:[2,4],39:[2,4],44:[2,4],47:[2,4],48:[2,4],51:[2,4],55:[2,4],60:[2,4]},{5:[2,5],14:[2,5],15:[2,5],19:[2,5],29:[2,5],34:[2,5],39:[2,5],44:[2,5],47:[2,5],48:[2,5],51:[2,5],55:[2,5],60:[2,5]},{5:[2,6],14:[2,6],15:[2,6],19:[2,6],29:[2,6],34:[2,6],39:[2,6],44:[2,6],47:[2,6],48:[2,6],51:[2,6],55:[2,6],60:[2,6]},{5:[2,7],14:[2,7],15:[2,7],19:[2,7],29:[2,7],34:[2,7],39:[2,7],44:[2,7],47:[2,7],48:[2,7],51:[2,7],55:[2,7],60:[2,7]},{5:[2,8],14:[2,8],15:[2,8],19:[2,8],29:[2,8],34:[2,8],39:[2,8],44:[2,8],47:[2,8],48:[2,8],51:[2,8],55:[2,8],60:[2,8]},{5:[2,9],14:[2,9],15:[2,9],19:[2,9],29:[2,9],34:[2,9],39:[2,9],44:[2,9],47:[2,9],48:[2,9],51:[2,9],55:[2,9],60:[2,9]},{20:25,72:[1,35],78:26,79:27,80:[1,28],81:[1,29],82:[1,30],83:[1,31],84:[1,32],85:[1,34],86:33},{20:36,72:[1,35],78:26,79:27,80:[1,28],81:[1,29],82:[1,30],83:[1,31],84:[1,32],85:[1,34],86:33},{4:37,6:3,14:[2,46],15:[2,46],19:[2,46],29:[2,46],34:[2,46],39:[2,46],44:[2,46],47:[2,46],48:[2,46],51:[2,46],55:[2,46],60:[2,46]},{4:38,6:3,14:[2,46],15:[2,46],19:[2,46],29:[2,46],34:[2,46],44:[2,46],47:[2,46],48:[2,46],51:[2,46],55:[2,46],60:[2,46]},{13:40,15:[1,20],17:39},{20:42,56:41,64:43,65:[1,44],72:[1,35],78:26,79:27,80:[1,28],81:[1,29],82:[1,30],83:[1,31],84:[1,32],85:[1,34],86:33},{4:45,6:3,14:[2,46],15:[2,46],19:[2,46],29:[2,46],34:[2,46],47:[2,46],48:[2,46],51:[2,46],55:[2,46],60:[2,46]},{5:[2,10],14:[2,10],15:[2,10],18:[2,10],19:[2,10],29:[2,10],34:[2,10],39:[2,10],44:[2,10],47:[2,10],48:[2,10],51:[2,10],55:[2,10],60:[2,10]},{20:46,72:[1,35],78:26,79:27,80:[1,28],81:[1,29],82:[1,30],83:[1,31],84:[1,32],85:[1,34],86:33},{20:47,72:[1,35],78:26,79:27,80:[1,28],81:[1,29],82:[1,30],83:[1,31],84:[1,32],85:[1,34],86:33},{20:48,72:[1,35],78:26,79:27,80:[1,28],81:[1,29],82:[1,30],83:[1,31],84:[1,32],85:[1,34],86:33},{20:42,56:49,64:43,65:[1,44],72:[1,35],78:26,79:27,80:[1,28],81:[1,29],82:[1,30],83:[1,31],84:[1,32],85:[1,34],86:33},{33:[2,78],49:50,65:[2,78],72:[2,78],80:[2,78],81:[2,78],82:[2,78],83:[2,78],84:[2,78],85:[2,78]},{23:[2,33],33:[2,33],54:[2,33],65:[2,33],68:[2,33],72:[2,33],75:[2,33],80:[2,33],81:[2,33],82:[2,33],83:[2,33],84:[2,33],85:[2,33]},{23:[2,34],33:[2,34],54:[2,34],65:[2,34],68:[2,34],72:[2,34],75:[2,34],80:[2,34],81:[2,34],82:[2,34],83:[2,34],84:[2,34],85:[2,34]},{23:[2,35],33:[2,35],54:[2,35],65:[2,35],68:[2,35],72:[2,35],75:[2,35],80:[2,35],81:[2,35],82:[2,35],83:[2,35],84:[2,35],85:[2,35]},{23:[2,36],33:[2,36],54:[2,36],65:[2,36],68:[2,36],72:[2,36],75:[2,36],80:[2,36],81:[2,36],82:[2,36],83:[2,36],84:[2,36],85:[2,36]},{23:[2,37],33:[2,37],54:[2,37],65:[2,37],68:[2,37],72:[2,37],75:[2,37],80:[2,37],81:[2,37],82:[2,37],83:[2,37],84:[2,37],85:[2,37]},{23:[2,38],33:[2,38],54:[2,38],65:[2,38],68:[2,38],72:[2,38],75:[2,38],80:[2,38],81:[2,38],82:[2,38],83:[2,38],84:[2,38],85:[2,38]},{23:[2,39],33:[2,39],54:[2,39],65:[2,39],68:[2,39],72:[2,39],75:[2,39],80:[2,39],81:[2,39],82:[2,39],83:[2,39],84:[2,39],85:[2,39]},{23:[2,43],33:[2,43],54:[2,43],65:[2,43],68:[2,43],72:[2,43],75:[2,43],80:[2,43],81:[2,43],82:[2,43],83:[2,43],84:[2,43],85:[2,43],87:[1,51]},{72:[1,35],86:52},{23:[2,45],33:[2,45],54:[2,45],65:[2,45],68:[2,45],72:[2,45],75:[2,45],80:[2,45],81:[2,45],82:[2,45],83:[2,45],84:[2,45],85:[2,45],87:[2,45]},{52:53,54:[2,82],65:[2,82],72:[2,82],80:[2,82],81:[2,82],82:[2,82],83:[2,82],84:[2,82],85:[2,82]},{25:54,38:56,39:[1,58],43:57,44:[1,59],45:55,47:[2,54]},{28:60,43:61,44:[1,59],47:[2,56]},{13:63,15:[1,20],18:[1,62]},{15:[2,48],18:[2,48]},{33:[2,86],57:64,65:[2,86],72:[2,86],80:[2,86],81:[2,86],82:[2,86],83:[2,86],84:[2,86],85:[2,86]},{33:[2,40],65:[2,40],72:[2,40],80:[2,40],81:[2,40],82:[2,40],83:[2,40],84:[2,40],85:[2,40]},{33:[2,41],65:[2,41],72:[2,41],80:[2,41],81:[2,41],82:[2,41],83:[2,41],84:[2,41],85:[2,41]},{20:65,72:[1,35],78:26,79:27,80:[1,28],81:[1,29],82:[1,30],83:[1,31],84:[1,32],85:[1,34],86:33},{26:66,47:[1,67]},{30:68,33:[2,58],65:[2,58],72:[2,58],75:[2,58],80:[2,58],81:[2,58],82:[2,58],83:[2,58],84:[2,58],85:[2,58]},{33:[2,64],35:69,65:[2,64],72:[2,64],75:[2,64],80:[2,64],81:[2,64],82:[2,64],83:[2,64],84:[2,64],85:[2,64]},{21:70,23:[2,50],65:[2,50],72:[2,50],80:[2,50],81:[2,50],82:[2,50],83:[2,50],84:[2,50],85:[2,50]},{33:[2,90],61:71,65:[2,90],72:[2,90],80:[2,90],81:[2,90],82:[2,90],83:[2,90],84:[2,90],85:[2,90]},{20:75,33:[2,80],50:72,63:73,64:76,65:[1,44],69:74,70:77,71:78,72:[1,79],78:26,79:27,80:[1,28],81:[1,29],82:[1,30],83:[1,31],84:[1,32],85:[1,34],86:33},{72:[1,80]},{23:[2,42],33:[2,42],54:[2,42],65:[2,42],68:[2,42],72:[2,42],75:[2,42],80:[2,42],81:[2,42],82:[2,42],83:[2,42],84:[2,42],85:[2,42],87:[1,51]},{20:75,53:81,54:[2,84],63:82,64:76,65:[1,44],69:83,70:77,71:78,72:[1,79],78:26,79:27,80:[1,28],81:[1,29],82:[1,30],83:[1,31],84:[1,32],85:[1,34],86:33},{26:84,47:[1,67]},{47:[2,55]},{4:85,6:3,14:[2,46],15:[2,46],19:[2,46],29:[2,46],34:[2,46],39:[2,46],44:[2,46],47:[2,46],48:[2,46],51:[2,46],55:[2,46],60:[2,46]},{47:[2,20]},{20:86,72:[1,35],78:26,79:27,80:[1,28],81:[1,29],82:[1,30],83:[1,31],84:[1,32],85:[1,34],86:33},{4:87,6:3,14:[2,46],15:[2,46],19:[2,46],29:[2,46],34:[2,46],47:[2,46],48:[2,46],51:[2,46],55:[2,46],60:[2,46]},{26:88,47:[1,67]},{47:[2,57]},{5:[2,11],14:[2,11],15:[2,11],19:[2,11],29:[2,11],34:[2,11],39:[2,11],44:[2,11],47:[2,11],48:[2,11],51:[2,11],55:[2,11],60:[2,11]},{15:[2,49],18:[2,49]},{20:75,33:[2,88],58:89,63:90,64:76,65:[1,44],69:91,70:77,71:78,72:[1,79],78:26,79:27,80:[1,28],81:[1,29],82:[1,30],83:[1,31],84:[1,32],85:[1,34],86:33},{65:[2,94],66:92,68:[2,94],72:[2,94],80:[2,94],81:[2,94],82:[2,94],83:[2,94],84:[2,94],85:[2,94]},{5:[2,25],14:[2,25],15:[2,25],19:[2,25],29:[2,25],34:[2,25],39:[2,25],44:[2,25],47:[2,25],48:[2,25],51:[2,25],55:[2,25],60:[2,25]},{20:93,72:[1,35],78:26,79:27,80:[1,28],81:[1,29],82:[1,30],83:[1,31],84:[1,32],85:[1,34],86:33},{20:75,31:94,33:[2,60],63:95,64:76,65:[1,44],69:96,70:77,71:78,72:[1,79],75:[2,60],78:26,79:27,80:[1,28],81:[1,29],82:[1,30],83:[1,31],84:[1,32],85:[1,34],86:33},{20:75,33:[2,66],36:97,63:98,64:76,65:[1,44],69:99,70:77,71:78,72:[1,79],75:[2,66],78:26,79:27,80:[1,28],81:[1,29],82:[1,30],83:[1,31],84:[1,32],85:[1,34],86:33},{20:75,22:100,23:[2,52],63:101,64:76,65:[1,44],69:102,70:77,71:78,72:[1,79],78:26,79:27,80:[1,28],81:[1,29],82:[1,30],83:[1,31],84:[1,32],85:[1,34],86:33},{20:75,33:[2,92],62:103,63:104,64:76,65:[1,44],69:105,70:77,71:78,72:[1,79],78:26,79:27,80:[1,28],81:[1,29],82:[1,30],83:[1,31],84:[1,32],85:[1,34],86:33},{33:[1,106]},{33:[2,79],65:[2,79],72:[2,79],80:[2,79],81:[2,79],82:[2,79],83:[2,79],84:[2,79],85:[2,79]},{33:[2,81]},{23:[2,27],33:[2,27],54:[2,27],65:[2,27],68:[2,27],72:[2,27],75:[2,27],80:[2,27],81:[2,27],82:[2,27],83:[2,27],84:[2,27],85:[2,27]},{23:[2,28],33:[2,28],54:[2,28],65:[2,28],68:[2,28],72:[2,28],75:[2,28],80:[2,28],81:[2,28],82:[2,28],83:[2,28],84:[2,28],85:[2,28]},{23:[2,30],33:[2,30],54:[2,30],68:[2,30],71:107,72:[1,108],75:[2,30]},{23:[2,98],33:[2,98],54:[2,98],68:[2,98],72:[2,98],75:[2,98]},{23:[2,45],33:[2,45],54:[2,45],65:[2,45],68:[2,45],72:[2,45],73:[1,109],75:[2,45],80:[2,45],81:[2,45],82:[2,45],83:[2,45],84:[2,45],85:[2,45],87:[2,45]},{23:[2,44],33:[2,44],54:[2,44],65:[2,44],68:[2,44],72:[2,44],75:[2,44],80:[2,44],81:[2,44],82:[2,44],83:[2,44],84:[2,44],85:[2,44],87:[2,44]},{54:[1,110]},{54:[2,83],65:[2,83],72:[2,83],80:[2,83],81:[2,83],82:[2,83],83:[2,83],84:[2,83],85:[2,83]},{54:[2,85]},{5:[2,13],14:[2,13],15:[2,13],19:[2,13],29:[2,13],34:[2,13],39:[2,13],44:[2,13],47:[2,13],48:[2,13],51:[2,13],55:[2,13],60:[2,13]},{38:56,39:[1,58],43:57,44:[1,59],45:112,46:111,47:[2,76]},{33:[2,70],40:113,65:[2,70],72:[2,70],75:[2,70],80:[2,70],81:[2,70],82:[2,70],83:[2,70],84:[2,70],85:[2,70]},{47:[2,18]},{5:[2,14],14:[2,14],15:[2,14],19:[2,14],29:[2,14],34:[2,14],39:[2,14],44:[2,14],47:[2,14],48:[2,14],51:[2,14],55:[2,14],60:[2,14]},{33:[1,114]},{33:[2,87],65:[2,87],72:[2,87],80:[2,87],81:[2,87],82:[2,87],83:[2,87],84:[2,87],85:[2,87]},{33:[2,89]},{20:75,63:116,64:76,65:[1,44],67:115,68:[2,96],69:117,70:77,71:78,72:[1,79],78:26,79:27,80:[1,28],81:[1,29],82:[1,30],83:[1,31],84:[1,32],85:[1,34],86:33},{33:[1,118]},{32:119,33:[2,62],74:120,75:[1,121]},{33:[2,59],65:[2,59],72:[2,59],75:[2,59],80:[2,59],81:[2,59],82:[2,59],83:[2,59],84:[2,59],85:[2,59]},{33:[2,61],75:[2,61]},{33:[2,68],37:122,74:123,75:[1,121]},{33:[2,65],65:[2,65],72:[2,65],75:[2,65],80:[2,65],81:[2,65],82:[2,65],83:[2,65],84:[2,65],85:[2,65]},{33:[2,67],75:[2,67]},{23:[1,124]},{23:[2,51],65:[2,51],72:[2,51],80:[2,51],81:[2,51],82:[2,51],83:[2,51],84:[2,51],85:[2,51]},{23:[2,53]},{33:[1,125]},{33:[2,91],65:[2,91],72:[2,91],80:[2,91],81:[2,91],82:[2,91],83:[2,91],84:[2,91],85:[2,91]},{33:[2,93]},{5:[2,22],14:[2,22],15:[2,22],19:[2,22],29:[2,22],34:[2,22],39:[2,22],44:[2,22],47:[2,22],48:[2,22],51:[2,22],55:[2,22],60:[2,22]},{23:[2,99],33:[2,99],54:[2,99],68:[2,99],72:[2,99],75:[2,99]},{73:[1,109]},{20:75,63:126,64:76,65:[1,44],72:[1,35],78:26,79:27,80:[1,28],81:[1,29],82:[1,30],83:[1,31],84:[1,32],85:[1,34],86:33},{5:[2,23],14:[2,23],15:[2,23],19:[2,23],29:[2,23],34:[2,23],39:[2,23],44:[2,23],47:[2,23],48:[2,23],51:[2,23],55:[2,23],60:[2,23]},{47:[2,19]},{47:[2,77]},{20:75,33:[2,72],41:127,63:128,64:76,65:[1,44],69:129,70:77,71:78,72:[1,79],75:[2,72],78:26,79:27,80:[1,28],81:[1,29],82:[1,30],83:[1,31],84:[1,32],85:[1,34],86:33},{5:[2,24],14:[2,24],15:[2,24],19:[2,24],29:[2,24],34:[2,24],39:[2,24],44:[2,24],47:[2,24],48:[2,24],51:[2,24],55:[2,24],60:[2,24]},{68:[1,130]},{65:[2,95],68:[2,95],72:[2,95],80:[2,95],81:[2,95],82:[2,95],83:[2,95],84:[2,95],85:[2,95]},{68:[2,97]},{5:[2,21],14:[2,21],15:[2,21],19:[2,21],29:[2,21],34:[2,21],39:[2,21],44:[2,21],47:[2,21],48:[2,21],51:[2,21],55:[2,21],60:[2,21]},{33:[1,131]},{33:[2,63]},{72:[1,133],76:132},{33:[1,134]},{33:[2,69]},{15:[2,12]},{14:[2,26],15:[2,26],19:[2,26],29:[2,26],34:[2,26],47:[2,26],48:[2,26],51:[2,26],55:[2,26],60:[2,26]},{23:[2,31],33:[2,31],54:[2,31],68:[2,31],72:[2,31],75:[2,31]},{33:[2,74],42:135,74:136,75:[1,121]},{33:[2,71],65:[2,71],72:[2,71],75:[2,71],80:[2,71],81:[2,71],82:[2,71],83:[2,71],84:[2,71],85:[2,71]},{33:[2,73],75:[2,73]},{23:[2,29],33:[2,29],54:[2,29],65:[2,29],68:[2,29],72:[2,29],75:[2,29],80:[2,29],81:[2,29],82:[2,29],83:[2,29],84:[2,29],85:[2,29]},{14:[2,15],15:[2,15],19:[2,15],29:[2,15],34:[2,15],39:[2,15],44:[2,15],47:[2,15],48:[2,15],51:[2,15],55:[2,15],60:[2,15]},{72:[1,138],77:[1,137]},{72:[2,100],77:[2,100]},{14:[2,16],15:[2,16],19:[2,16],29:[2,16],34:[2,16],44:[2,16],47:[2,16],
	48:[2,16],51:[2,16],55:[2,16],60:[2,16]},{33:[1,139]},{33:[2,75]},{33:[2,32]},{72:[2,101],77:[2,101]},{14:[2,17],15:[2,17],19:[2,17],29:[2,17],34:[2,17],39:[2,17],44:[2,17],47:[2,17],48:[2,17],51:[2,17],55:[2,17],60:[2,17]}],defaultActions:{4:[2,1],55:[2,55],57:[2,20],61:[2,57],74:[2,81],83:[2,85],87:[2,18],91:[2,89],102:[2,53],105:[2,93],111:[2,19],112:[2,77],117:[2,97],120:[2,63],123:[2,69],124:[2,12],136:[2,75],137:[2,32]},parseError:function(a,b){throw new Error(a)},parse:function(a){function b(){var a;return a=c.lexer.lex()||1,"number"!=typeof a&&(a=c.symbols_[a]||a),a}var c=this,d=[0],e=[null],f=[],g=this.table,h="",i=0,j=0,k=0;this.lexer.setInput(a),this.lexer.yy=this.yy,this.yy.lexer=this.lexer,this.yy.parser=this,"undefined"==typeof this.lexer.yylloc&&(this.lexer.yylloc={});var l=this.lexer.yylloc;f.push(l);var m=this.lexer.options&&this.lexer.options.ranges;"function"==typeof this.yy.parseError&&(this.parseError=this.yy.parseError);for(var n,o,p,q,r,s,t,u,v,w={};;){if(p=d[d.length-1],this.defaultActions[p]?q=this.defaultActions[p]:((null===n||"undefined"==typeof n)&&(n=b()),q=g[p]&&g[p][n]),"undefined"==typeof q||!q.length||!q[0]){var x="";if(!k){v=[];for(s in g[p])this.terminals_[s]&&s>2&&v.push("'"+this.terminals_[s]+"'");x=this.lexer.showPosition?"Parse error on line "+(i+1)+":\n"+this.lexer.showPosition()+"\nExpecting "+v.join(", ")+", got '"+(this.terminals_[n]||n)+"'":"Parse error on line "+(i+1)+": Unexpected "+(1==n?"end of input":"'"+(this.terminals_[n]||n)+"'"),this.parseError(x,{text:this.lexer.match,token:this.terminals_[n]||n,line:this.lexer.yylineno,loc:l,expected:v})}}if(q[0]instanceof Array&&q.length>1)throw new Error("Parse Error: multiple actions possible at state: "+p+", token: "+n);switch(q[0]){case 1:d.push(n),e.push(this.lexer.yytext),f.push(this.lexer.yylloc),d.push(q[1]),n=null,o?(n=o,o=null):(j=this.lexer.yyleng,h=this.lexer.yytext,i=this.lexer.yylineno,l=this.lexer.yylloc,k>0&&k--);break;case 2:if(t=this.productions_[q[1]][1],w.$=e[e.length-t],w._$={first_line:f[f.length-(t||1)].first_line,last_line:f[f.length-1].last_line,first_column:f[f.length-(t||1)].first_column,last_column:f[f.length-1].last_column},m&&(w._$.range=[f[f.length-(t||1)].range[0],f[f.length-1].range[1]]),r=this.performAction.call(w,h,j,i,this.yy,q[1],e,f),"undefined"!=typeof r)return r;t&&(d=d.slice(0,-1*t*2),e=e.slice(0,-1*t),f=f.slice(0,-1*t)),d.push(this.productions_[q[1]][0]),e.push(w.$),f.push(w._$),u=g[d[d.length-2]][d[d.length-1]],d.push(u);break;case 3:return!0}}return!0}},c=function(){var a={EOF:1,parseError:function(a,b){if(!this.yy.parser)throw new Error(a);this.yy.parser.parseError(a,b)},setInput:function(a){return this._input=a,this._more=this._less=this.done=!1,this.yylineno=this.yyleng=0,this.yytext=this.matched=this.match="",this.conditionStack=["INITIAL"],this.yylloc={first_line:1,first_column:0,last_line:1,last_column:0},this.options.ranges&&(this.yylloc.range=[0,0]),this.offset=0,this},input:function(){var a=this._input[0];this.yytext+=a,this.yyleng++,this.offset++,this.match+=a,this.matched+=a;var b=a.match(/(?:\r\n?|\n).*/g);return b?(this.yylineno++,this.yylloc.last_line++):this.yylloc.last_column++,this.options.ranges&&this.yylloc.range[1]++,this._input=this._input.slice(1),a},unput:function(a){var b=a.length,c=a.split(/(?:\r\n?|\n)/g);this._input=a+this._input,this.yytext=this.yytext.substr(0,this.yytext.length-b-1),this.offset-=b;var d=this.match.split(/(?:\r\n?|\n)/g);this.match=this.match.substr(0,this.match.length-1),this.matched=this.matched.substr(0,this.matched.length-1),c.length-1&&(this.yylineno-=c.length-1);var e=this.yylloc.range;return this.yylloc={first_line:this.yylloc.first_line,last_line:this.yylineno+1,first_column:this.yylloc.first_column,last_column:c?(c.length===d.length?this.yylloc.first_column:0)+d[d.length-c.length].length-c[0].length:this.yylloc.first_column-b},this.options.ranges&&(this.yylloc.range=[e[0],e[0]+this.yyleng-b]),this},more:function(){return this._more=!0,this},less:function(a){this.unput(this.match.slice(a))},pastInput:function(){var a=this.matched.substr(0,this.matched.length-this.match.length);return(a.length>20?"...":"")+a.substr(-20).replace(/\n/g,"")},upcomingInput:function(){var a=this.match;return a.length<20&&(a+=this._input.substr(0,20-a.length)),(a.substr(0,20)+(a.length>20?"...":"")).replace(/\n/g,"")},showPosition:function(){var a=this.pastInput(),b=new Array(a.length+1).join("-");return a+this.upcomingInput()+"\n"+b+"^"},next:function(){if(this.done)return this.EOF;this._input||(this.done=!0);var a,b,c,d,e;this._more||(this.yytext="",this.match="");for(var f=this._currentRules(),g=0;g<f.length&&(c=this._input.match(this.rules[f[g]]),!c||b&&!(c[0].length>b[0].length)||(b=c,d=g,this.options.flex));g++);return b?(e=b[0].match(/(?:\r\n?|\n).*/g),e&&(this.yylineno+=e.length),this.yylloc={first_line:this.yylloc.last_line,last_line:this.yylineno+1,first_column:this.yylloc.last_column,last_column:e?e[e.length-1].length-e[e.length-1].match(/\r?\n?/)[0].length:this.yylloc.last_column+b[0].length},this.yytext+=b[0],this.match+=b[0],this.matches=b,this.yyleng=this.yytext.length,this.options.ranges&&(this.yylloc.range=[this.offset,this.offset+=this.yyleng]),this._more=!1,this._input=this._input.slice(b[0].length),this.matched+=b[0],a=this.performAction.call(this,this.yy,this,f[d],this.conditionStack[this.conditionStack.length-1]),this.done&&this._input&&(this.done=!1),a?a:void 0):""===this._input?this.EOF:this.parseError("Lexical error on line "+(this.yylineno+1)+". Unrecognized text.\n"+this.showPosition(),{text:"",token:null,line:this.yylineno})},lex:function(){var a=this.next();return"undefined"!=typeof a?a:this.lex()},begin:function(a){this.conditionStack.push(a)},popState:function(){return this.conditionStack.pop()},_currentRules:function(){return this.conditions[this.conditionStack[this.conditionStack.length-1]].rules},topState:function(){return this.conditionStack[this.conditionStack.length-2]},pushState:function(a){this.begin(a)}};return a.options={},a.performAction=function(a,b,c,d){function e(a,c){return b.yytext=b.yytext.substr(a,b.yyleng-c)}switch(c){case 0:if("\\\\"===b.yytext.slice(-2)?(e(0,1),this.begin("mu")):"\\"===b.yytext.slice(-1)?(e(0,1),this.begin("emu")):this.begin("mu"),b.yytext)return 15;break;case 1:return 15;case 2:return this.popState(),15;case 3:return this.begin("raw"),15;case 4:return this.popState(),"raw"===this.conditionStack[this.conditionStack.length-1]?15:(b.yytext=b.yytext.substr(5,b.yyleng-9),"END_RAW_BLOCK");case 5:return 15;case 6:return this.popState(),14;case 7:return 65;case 8:return 68;case 9:return 19;case 10:return this.popState(),this.begin("raw"),23;case 11:return 55;case 12:return 60;case 13:return 29;case 14:return 47;case 15:return this.popState(),44;case 16:return this.popState(),44;case 17:return 34;case 18:return 39;case 19:return 51;case 20:return 48;case 21:this.unput(b.yytext),this.popState(),this.begin("com");break;case 22:return this.popState(),14;case 23:return 48;case 24:return 73;case 25:return 72;case 26:return 72;case 27:return 87;case 28:break;case 29:return this.popState(),54;case 30:return this.popState(),33;case 31:return b.yytext=e(1,2).replace(/\\"/g,'"'),80;case 32:return b.yytext=e(1,2).replace(/\\'/g,"'"),80;case 33:return 85;case 34:return 82;case 35:return 82;case 36:return 83;case 37:return 84;case 38:return 81;case 39:return 75;case 40:return 77;case 41:return 72;case 42:return b.yytext=b.yytext.replace(/\\([\\\]])/g,"$1"),72;case 43:return"INVALID";case 44:return 5}},a.rules=[/^(?:[^\x00]*?(?=(\{\{)))/,/^(?:[^\x00]+)/,/^(?:[^\x00]{2,}?(?=(\{\{|\\\{\{|\\\\\{\{|$)))/,/^(?:\{\{\{\{(?=[^\/]))/,/^(?:\{\{\{\{\/[^\s!"#%-,\.\/;->@\[-\^`\{-~]+(?=[=}\s\/.])\}\}\}\})/,/^(?:[^\x00]*?(?=(\{\{\{\{)))/,/^(?:[\s\S]*?--(~)?\}\})/,/^(?:\()/,/^(?:\))/,/^(?:\{\{\{\{)/,/^(?:\}\}\}\})/,/^(?:\{\{(~)?>)/,/^(?:\{\{(~)?#>)/,/^(?:\{\{(~)?#\*?)/,/^(?:\{\{(~)?\/)/,/^(?:\{\{(~)?\^\s*(~)?\}\})/,/^(?:\{\{(~)?\s*else\s*(~)?\}\})/,/^(?:\{\{(~)?\^)/,/^(?:\{\{(~)?\s*else\b)/,/^(?:\{\{(~)?\{)/,/^(?:\{\{(~)?&)/,/^(?:\{\{(~)?!--)/,/^(?:\{\{(~)?![\s\S]*?\}\})/,/^(?:\{\{(~)?\*?)/,/^(?:=)/,/^(?:\.\.)/,/^(?:\.(?=([=~}\s\/.)|])))/,/^(?:[\/.])/,/^(?:\s+)/,/^(?:\}(~)?\}\})/,/^(?:(~)?\}\})/,/^(?:"(\\["]|[^"])*")/,/^(?:'(\\[']|[^'])*')/,/^(?:@)/,/^(?:true(?=([~}\s)])))/,/^(?:false(?=([~}\s)])))/,/^(?:undefined(?=([~}\s)])))/,/^(?:null(?=([~}\s)])))/,/^(?:-?[0-9]+(?:\.[0-9]+)?(?=([~}\s)])))/,/^(?:as\s+\|)/,/^(?:\|)/,/^(?:([^\s!"#%-,\.\/;->@\[-\^`\{-~]+(?=([=~}\s\/.)|]))))/,/^(?:\[(\\\]|[^\]])*\])/,/^(?:.)/,/^(?:$)/],a.conditions={mu:{rules:[7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,26,27,28,29,30,31,32,33,34,35,36,37,38,39,40,41,42,43,44],inclusive:!1},emu:{rules:[2],inclusive:!1},com:{rules:[6],inclusive:!1},raw:{rules:[3,4,5],inclusive:!1},INITIAL:{rules:[0,1,44],inclusive:!0}},a}();return b.lexer=c,a.prototype=b,b.Parser=a,new a}();b.__esModule=!0,b["default"]=c},function(a,b,c){"use strict";function d(){var a=arguments.length<=0||void 0===arguments[0]?{}:arguments[0];this.options=a}function e(a,b,c){void 0===b&&(b=a.length);var d=a[b-1],e=a[b-2];return d?"ContentStatement"===d.type?(e||!c?/\r?\n\s*?$/:/(^|\r?\n)\s*?$/).test(d.original):void 0:c}function f(a,b,c){void 0===b&&(b=-1);var d=a[b+1],e=a[b+2];return d?"ContentStatement"===d.type?(e||!c?/^\s*?\r?\n/:/^\s*?(\r?\n|$)/).test(d.original):void 0:c}function g(a,b,c){var d=a[null==b?0:b+1];if(d&&"ContentStatement"===d.type&&(c||!d.rightStripped)){var e=d.value;d.value=d.value.replace(c?/^\s+/:/^[ \t]*\r?\n?/,""),d.rightStripped=d.value!==e}}function h(a,b,c){var d=a[null==b?a.length-1:b-1];if(d&&"ContentStatement"===d.type&&(c||!d.leftStripped)){var e=d.value;return d.value=d.value.replace(c?/\s+$/:/[ \t]+$/,""),d.leftStripped=d.value!==e,d.leftStripped}}var i=c(1)["default"];b.__esModule=!0;var j=c(25),k=i(j);d.prototype=new k["default"],d.prototype.Program=function(a){var b=!this.options.ignoreStandalone,c=!this.isRootSeen;this.isRootSeen=!0;for(var d=a.body,i=0,j=d.length;j>i;i++){var k=d[i],l=this.accept(k);if(l){var m=e(d,i,c),n=f(d,i,c),o=l.openStandalone&&m,p=l.closeStandalone&&n,q=l.inlineStandalone&&m&&n;l.close&&g(d,i,!0),l.open&&h(d,i,!0),b&&q&&(g(d,i),h(d,i)&&"PartialStatement"===k.type&&(k.indent=/([ \t]+$)/.exec(d[i-1].original)[1])),b&&o&&(g((k.program||k.inverse).body),h(d,i)),b&&p&&(g(d,i),h((k.inverse||k.program).body))}}return a},d.prototype.BlockStatement=d.prototype.DecoratorBlock=d.prototype.PartialBlockStatement=function(a){this.accept(a.program),this.accept(a.inverse);var b=a.program||a.inverse,c=a.program&&a.inverse,d=c,i=c;if(c&&c.chained)for(d=c.body[0].program;i.chained;)i=i.body[i.body.length-1].program;var j={open:a.openStrip.open,close:a.closeStrip.close,openStandalone:f(b.body),closeStandalone:e((d||b).body)};if(a.openStrip.close&&g(b.body,null,!0),c){var k=a.inverseStrip;k.open&&h(b.body,null,!0),k.close&&g(d.body,null,!0),a.closeStrip.open&&h(i.body,null,!0),!this.options.ignoreStandalone&&e(b.body)&&f(d.body)&&(h(b.body),g(d.body))}else a.closeStrip.open&&h(b.body,null,!0);return j},d.prototype.Decorator=d.prototype.MustacheStatement=function(a){return a.strip},d.prototype.PartialStatement=d.prototype.CommentStatement=function(a){var b=a.strip||{};return{inlineStandalone:!0,open:b.open,close:b.close}},b["default"]=d,a.exports=b["default"]},function(a,b,c){"use strict";function d(){this.parents=[]}function e(a){this.acceptRequired(a,"path"),this.acceptArray(a.params),this.acceptKey(a,"hash")}function f(a){e.call(this,a),this.acceptKey(a,"program"),this.acceptKey(a,"inverse")}function g(a){this.acceptRequired(a,"name"),this.acceptArray(a.params),this.acceptKey(a,"hash")}var h=c(1)["default"];b.__esModule=!0;var i=c(6),j=h(i);d.prototype={constructor:d,mutating:!1,acceptKey:function(a,b){var c=this.accept(a[b]);if(this.mutating){if(c&&!d.prototype[c.type])throw new j["default"]('Unexpected node type "'+c.type+'" found when accepting '+b+" on "+a.type);a[b]=c}},acceptRequired:function(a,b){if(this.acceptKey(a,b),!a[b])throw new j["default"](a.type+" requires "+b)},acceptArray:function(a){for(var b=0,c=a.length;c>b;b++)this.acceptKey(a,b),a[b]||(a.splice(b,1),b--,c--)},accept:function(a){if(a){if(!this[a.type])throw new j["default"]("Unknown type: "+a.type,a);this.current&&this.parents.unshift(this.current),this.current=a;var b=this[a.type](a);return this.current=this.parents.shift(),!this.mutating||b?b:b!==!1?a:void 0}},Program:function(a){this.acceptArray(a.body)},MustacheStatement:e,Decorator:e,BlockStatement:f,DecoratorBlock:f,PartialStatement:g,PartialBlockStatement:function(a){g.call(this,a),this.acceptKey(a,"program")},ContentStatement:function(){},CommentStatement:function(){},SubExpression:e,PathExpression:function(){},StringLiteral:function(){},NumberLiteral:function(){},BooleanLiteral:function(){},UndefinedLiteral:function(){},NullLiteral:function(){},Hash:function(a){this.acceptArray(a.pairs)},HashPair:function(a){this.acceptRequired(a,"value")}},b["default"]=d,a.exports=b["default"]},function(a,b,c){"use strict";function d(a,b){if(b=b.path?b.path.original:b,a.path.original!==b){var c={loc:a.path.loc};throw new q["default"](a.path.original+" doesn't match "+b,c)}}function e(a,b){this.source=a,this.start={line:b.first_line,column:b.first_column},this.end={line:b.last_line,column:b.last_column}}function f(a){return/^\[.*\]$/.test(a)?a.substr(1,a.length-2):a}function g(a,b){return{open:"~"===a.charAt(2),close:"~"===b.charAt(b.length-3)}}function h(a){return a.replace(/^\{\{~?\!-?-?/,"").replace(/-?-?~?\}\}$/,"")}function i(a,b,c){c=this.locInfo(c);for(var d=a?"@":"",e=[],f=0,g="",h=0,i=b.length;i>h;h++){var j=b[h].part,k=b[h].original!==j;if(d+=(b[h].separator||"")+j,k||".."!==j&&"."!==j&&"this"!==j)e.push(j);else{if(e.length>0)throw new q["default"]("Invalid path: "+d,{loc:c});".."===j&&(f++,g+="../")}}return{type:"PathExpression",data:a,depth:f,parts:e,original:d,loc:c}}function j(a,b,c,d,e,f){var g=d.charAt(3)||d.charAt(2),h="{"!==g&&"&"!==g,i=/\*/.test(d);return{type:i?"Decorator":"MustacheStatement",path:a,params:b,hash:c,escaped:h,strip:e,loc:this.locInfo(f)}}function k(a,b,c,e){d(a,c),e=this.locInfo(e);var f={type:"Program",body:b,strip:{},loc:e};return{type:"BlockStatement",path:a.path,params:a.params,hash:a.hash,program:f,openStrip:{},inverseStrip:{},closeStrip:{},loc:e}}function l(a,b,c,e,f,g){e&&e.path&&d(a,e);var h=/\*/.test(a.open);b.blockParams=a.blockParams;var i=void 0,j=void 0;if(c){if(h)throw new q["default"]("Unexpected inverse block on decorator",c);c.chain&&(c.program.body[0].closeStrip=e.strip),j=c.strip,i=c.program}return f&&(f=i,i=b,b=f),{type:h?"DecoratorBlock":"BlockStatement",path:a.path,params:a.params,hash:a.hash,program:b,inverse:i,openStrip:a.strip,inverseStrip:j,closeStrip:e&&e.strip,loc:this.locInfo(g)}}function m(a,b){if(!b&&a.length){var c=a[0].loc,d=a[a.length-1].loc;c&&d&&(b={source:c.source,start:{line:c.start.line,column:c.start.column},end:{line:d.end.line,column:d.end.column}})}return{type:"Program",body:a,strip:{},loc:b}}function n(a,b,c,e){return d(a,c),{type:"PartialBlockStatement",name:a.path,params:a.params,hash:a.hash,program:b,openStrip:a.strip,closeStrip:c&&c.strip,loc:this.locInfo(e)}}var o=c(1)["default"];b.__esModule=!0,b.SourceLocation=e,b.id=f,b.stripFlags=g,b.stripComment=h,b.preparePath=i,b.prepareMustache=j,b.prepareRawBlock=k,b.prepareBlock=l,b.prepareProgram=m,b.preparePartialBlock=n;var p=c(6),q=o(p)},function(a,b,c){"use strict";function d(){}function e(a,b,c){if(null==a||"string"!=typeof a&&"Program"!==a.type)throw new k["default"]("You must pass a string or Handlebars AST to Handlebars.precompile. You passed "+a);b=b||{},"data"in b||(b.data=!0),b.compat&&(b.useDepths=!0);var d=c.parse(a,b),e=(new c.Compiler).compile(d,b);return(new c.JavaScriptCompiler).compile(e,b)}function f(a,b,c){function d(){var d=c.parse(a,b),e=(new c.Compiler).compile(d,b),f=(new c.JavaScriptCompiler).compile(e,b,void 0,!0);return c.template(f)}function e(a,b){return f||(f=d()),f.call(this,a,b)}if(void 0===b&&(b={}),null==a||"string"!=typeof a&&"Program"!==a.type)throw new k["default"]("You must pass a string or Handlebars AST to Handlebars.compile. You passed "+a);"data"in b||(b.data=!0),b.compat&&(b.useDepths=!0);var f=void 0;return e._setup=function(a){return f||(f=d()),f._setup(a)},e._child=function(a,b,c,e){return f||(f=d()),f._child(a,b,c,e)},e}function g(a,b){if(a===b)return!0;if(l.isArray(a)&&l.isArray(b)&&a.length===b.length){for(var c=0;c<a.length;c++)if(!g(a[c],b[c]))return!1;return!0}}function h(a){if(!a.path.parts){var b=a.path;a.path={type:"PathExpression",data:!1,depth:0,parts:[b.original+""],original:b.original+"",loc:b.loc}}}var i=c(1)["default"];b.__esModule=!0,b.Compiler=d,b.precompile=e,b.compile=f;var j=c(6),k=i(j),l=c(5),m=c(21),n=i(m),o=[].slice;d.prototype={compiler:d,equals:function(a){var b=this.opcodes.length;if(a.opcodes.length!==b)return!1;for(var c=0;b>c;c++){var d=this.opcodes[c],e=a.opcodes[c];if(d.opcode!==e.opcode||!g(d.args,e.args))return!1}b=this.children.length;for(var c=0;b>c;c++)if(!this.children[c].equals(a.children[c]))return!1;return!0},guid:0,compile:function(a,b){this.sourceNode=[],this.opcodes=[],this.children=[],this.options=b,this.stringParams=b.stringParams,this.trackIds=b.trackIds,b.blockParams=b.blockParams||[];var c=b.knownHelpers;if(b.knownHelpers={helperMissing:!0,blockHelperMissing:!0,each:!0,"if":!0,unless:!0,"with":!0,log:!0,lookup:!0},c)for(var d in c)d in c&&(b.knownHelpers[d]=c[d]);return this.accept(a)},compileProgram:function(a){var b=new this.compiler,c=b.compile(a,this.options),d=this.guid++;return this.usePartial=this.usePartial||c.usePartial,this.children[d]=c,this.useDepths=this.useDepths||c.useDepths,d},accept:function(a){if(!this[a.type])throw new k["default"]("Unknown type: "+a.type,a);this.sourceNode.unshift(a);var b=this[a.type](a);return this.sourceNode.shift(),b},Program:function(a){this.options.blockParams.unshift(a.blockParams);for(var b=a.body,c=b.length,d=0;c>d;d++)this.accept(b[d]);return this.options.blockParams.shift(),this.isSimple=1===c,this.blockParams=a.blockParams?a.blockParams.length:0,this},BlockStatement:function(a){h(a);var b=a.program,c=a.inverse;b=b&&this.compileProgram(b),c=c&&this.compileProgram(c);var d=this.classifySexpr(a);"helper"===d?this.helperSexpr(a,b,c):"simple"===d?(this.simpleSexpr(a),this.opcode("pushProgram",b),this.opcode("pushProgram",c),this.opcode("emptyHash"),this.opcode("blockValue",a.path.original)):(this.ambiguousSexpr(a,b,c),this.opcode("pushProgram",b),this.opcode("pushProgram",c),this.opcode("emptyHash"),this.opcode("ambiguousBlockValue")),this.opcode("append")},DecoratorBlock:function(a){var b=a.program&&this.compileProgram(a.program),c=this.setupFullMustacheParams(a,b,void 0),d=a.path;this.useDecorators=!0,this.opcode("registerDecorator",c.length,d.original)},PartialStatement:function(a){this.usePartial=!0;var b=a.program;b&&(b=this.compileProgram(a.program));var c=a.params;if(c.length>1)throw new k["default"]("Unsupported number of partial arguments: "+c.length,a);c.length||(this.options.explicitPartialContext?this.opcode("pushLiteral","undefined"):c.push({type:"PathExpression",parts:[],depth:0}));var d=a.name.original,e="SubExpression"===a.name.type;e&&this.accept(a.name),this.setupFullMustacheParams(a,b,void 0,!0);var f=a.indent||"";this.options.preventIndent&&f&&(this.opcode("appendContent",f),f=""),this.opcode("invokePartial",e,d,f),this.opcode("append")},PartialBlockStatement:function(a){this.PartialStatement(a)},MustacheStatement:function(a){this.SubExpression(a),a.escaped&&!this.options.noEscape?this.opcode("appendEscaped"):this.opcode("append")},Decorator:function(a){this.DecoratorBlock(a)},ContentStatement:function(a){a.value&&this.opcode("appendContent",a.value)},CommentStatement:function(){},SubExpression:function(a){h(a);var b=this.classifySexpr(a);"simple"===b?this.simpleSexpr(a):"helper"===b?this.helperSexpr(a):this.ambiguousSexpr(a)},ambiguousSexpr:function(a,b,c){var d=a.path,e=d.parts[0],f=null!=b||null!=c;this.opcode("getContext",d.depth),this.opcode("pushProgram",b),this.opcode("pushProgram",c),d.strict=!0,this.accept(d),this.opcode("invokeAmbiguous",e,f)},simpleSexpr:function(a){var b=a.path;b.strict=!0,this.accept(b),this.opcode("resolvePossibleLambda")},helperSexpr:function(a,b,c){var d=this.setupFullMustacheParams(a,b,c),e=a.path,f=e.parts[0];if(this.options.knownHelpers[f])this.opcode("invokeKnownHelper",d.length,f);else{if(this.options.knownHelpersOnly)throw new k["default"]("You specified knownHelpersOnly, but used the unknown helper "+f,a);e.strict=!0,e.falsy=!0,this.accept(e),this.opcode("invokeHelper",d.length,e.original,n["default"].helpers.simpleId(e))}},PathExpression:function(a){this.addDepth(a.depth),this.opcode("getContext",a.depth);var b=a.parts[0],c=n["default"].helpers.scopedId(a),d=!a.depth&&!c&&this.blockParamIndex(b);d?this.opcode("lookupBlockParam",d,a.parts):b?a.data?(this.options.data=!0,this.opcode("lookupData",a.depth,a.parts,a.strict)):this.opcode("lookupOnContext",a.parts,a.falsy,a.strict,c):this.opcode("pushContext")},StringLiteral:function(a){this.opcode("pushString",a.value)},NumberLiteral:function(a){this.opcode("pushLiteral",a.value)},BooleanLiteral:function(a){this.opcode("pushLiteral",a.value)},UndefinedLiteral:function(){this.opcode("pushLiteral","undefined")},NullLiteral:function(){this.opcode("pushLiteral","null")},Hash:function(a){var b=a.pairs,c=0,d=b.length;for(this.opcode("pushHash");d>c;c++)this.pushParam(b[c].value);for(;c--;)this.opcode("assignToHash",b[c].key);this.opcode("popHash")},opcode:function(a){this.opcodes.push({opcode:a,args:o.call(arguments,1),loc:this.sourceNode[0].loc})},addDepth:function(a){a&&(this.useDepths=!0)},classifySexpr:function(a){var b=n["default"].helpers.simpleId(a.path),c=b&&!!this.blockParamIndex(a.path.parts[0]),d=!c&&n["default"].helpers.helperExpression(a),e=!c&&(d||b);if(e&&!d){var f=a.path.parts[0],g=this.options;g.knownHelpers[f]?d=!0:g.knownHelpersOnly&&(e=!1)}return d?"helper":e?"ambiguous":"simple"},pushParams:function(a){for(var b=0,c=a.length;c>b;b++)this.pushParam(a[b])},pushParam:function(a){var b=null!=a.value?a.value:a.original||"";if(this.stringParams)b.replace&&(b=b.replace(/^(\.?\.\/)*/g,"").replace(/\//g,".")),a.depth&&this.addDepth(a.depth),this.opcode("getContext",a.depth||0),this.opcode("pushStringParam",b,a.type),"SubExpression"===a.type&&this.accept(a);else{if(this.trackIds){var c=void 0;if(!a.parts||n["default"].helpers.scopedId(a)||a.depth||(c=this.blockParamIndex(a.parts[0])),c){var d=a.parts.slice(1).join(".");this.opcode("pushId","BlockParam",c,d)}else b=a.original||b,b.replace&&(b=b.replace(/^this(?:\.|$)/,"").replace(/^\.\//,"").replace(/^\.$/,"")),this.opcode("pushId",a.type,b)}this.accept(a)}},setupFullMustacheParams:function(a,b,c,d){var e=a.params;return this.pushParams(e),this.opcode("pushProgram",b),this.opcode("pushProgram",c),a.hash?this.accept(a.hash):this.opcode("emptyHash",d),e},blockParamIndex:function(a){for(var b=0,c=this.options.blockParams.length;c>b;b++){var d=this.options.blockParams[b],e=d&&l.indexOf(d,a);if(d&&e>=0)return[b,e]}}}},function(a,b,c){"use strict";function d(a){this.value=a}function e(){}function f(a,b,c,d){var e=b.popStack(),f=0,g=c.length;for(a&&g--;g>f;f++)e=b.nameLookup(e,c[f],d);return a?[b.aliasable("container.strict"),"(",e,", ",b.quotedString(c[f]),")"]:e}var g=c(1)["default"];b.__esModule=!0;var h=c(4),i=c(6),j=g(i),k=c(5),l=c(29),m=g(l);e.prototype={nameLookup:function(a,b){return e.isValidJavaScriptVariableName(b)?[a,".",b]:[a,"[",JSON.stringify(b),"]"]},depthedLookup:function(a){return[this.aliasable("container.lookup"),'(depths, "',a,'")']},compilerInfo:function(){var a=h.COMPILER_REVISION,b=h.REVISION_CHANGES[a];return[a,b]},appendToBuffer:function(a,b,c){return k.isArray(a)||(a=[a]),a=this.source.wrap(a,b),this.environment.isSimple?["return ",a,";"]:c?["buffer += ",a,";"]:(a.appendToBuffer=!0,a)},initializeBuffer:function(){return this.quotedString("")},compile:function(a,b,c,d){this.environment=a,this.options=b,this.stringParams=this.options.stringParams,this.trackIds=this.options.trackIds,this.precompile=!d,this.name=this.environment.name,this.isChild=!!c,this.context=c||{decorators:[],programs:[],environments:[]},this.preamble(),this.stackSlot=0,this.stackVars=[],this.aliases={},this.registers={list:[]},this.hashes=[],this.compileStack=[],this.inlineStack=[],this.blockParams=[],this.compileChildren(a,b),this.useDepths=this.useDepths||a.useDepths||a.useDecorators||this.options.compat,this.useBlockParams=this.useBlockParams||a.useBlockParams;var e=a.opcodes,f=void 0,g=void 0,h=void 0,i=void 0;for(h=0,i=e.length;i>h;h++)f=e[h],this.source.currentLocation=f.loc,g=g||f.loc,this[f.opcode].apply(this,f.args);if(this.source.currentLocation=g,this.pushSource(""),this.stackSlot||this.inlineStack.length||this.compileStack.length)throw new j["default"]("Compile completed with content left on stack");this.decorators.isEmpty()?this.decorators=void 0:(this.useDecorators=!0,this.decorators.prepend("var decorators = container.decorators;\n"),this.decorators.push("return fn;"),d?this.decorators=Function.apply(this,["fn","props","container","depth0","data","blockParams","depths",this.decorators.merge()]):(this.decorators.prepend("function(fn, props, container, depth0, data, blockParams, depths) {\n"),this.decorators.push("}\n"),this.decorators=this.decorators.merge()));var k=this.createFunctionContext(d);if(this.isChild)return k;var l={compiler:this.compilerInfo(),main:k};this.decorators&&(l.main_d=this.decorators,l.useDecorators=!0);var m=this.context,n=m.programs,o=m.decorators;for(h=0,i=n.length;i>h;h++)n[h]&&(l[h]=n[h],o[h]&&(l[h+"_d"]=o[h],l.useDecorators=!0));return this.environment.usePartial&&(l.usePartial=!0),this.options.data&&(l.useData=!0),this.useDepths&&(l.useDepths=!0),this.useBlockParams&&(l.useBlockParams=!0),this.options.compat&&(l.compat=!0),d?l.compilerOptions=this.options:(l.compiler=JSON.stringify(l.compiler),this.source.currentLocation={start:{line:1,column:0}},l=this.objectLiteral(l),b.srcName?(l=l.toStringWithSourceMap({file:b.destName}),l.map=l.map&&l.map.toString()):l=l.toString()),l},preamble:function(){this.lastContext=0,this.source=new m["default"](this.options.srcName),this.decorators=new m["default"](this.options.srcName)},createFunctionContext:function(a){var b="",c=this.stackVars.concat(this.registers.list);c.length>0&&(b+=", "+c.join(", "));var d=0;for(var e in this.aliases){var f=this.aliases[e];this.aliases.hasOwnProperty(e)&&f.children&&f.referenceCount>1&&(b+=", alias"+ ++d+"="+e,f.children[0]="alias"+d)}var g=["container","depth0","helpers","partials","data"];(this.useBlockParams||this.useDepths)&&g.push("blockParams"),this.useDepths&&g.push("depths");var h=this.mergeSource(b);return a?(g.push(h),Function.apply(this,g)):this.source.wrap(["function(",g.join(","),") {\n  ",h,"}"])},mergeSource:function(a){var b=this.environment.isSimple,c=!this.forceBuffer,d=void 0,e=void 0,f=void 0,g=void 0;return this.source.each(function(a){a.appendToBuffer?(f?a.prepend("  + "):f=a,g=a):(f&&(e?f.prepend("buffer += "):d=!0,g.add(";"),f=g=void 0),e=!0,b||(c=!1))}),c?f?(f.prepend("return "),g.add(";")):e||this.source.push('return "";'):(a+=", buffer = "+(d?"":this.initializeBuffer()),f?(f.prepend("return buffer + "),g.add(";")):this.source.push("return buffer;")),a&&this.source.prepend("var "+a.substring(2)+(d?"":";\n")),this.source.merge()},blockValue:function(a){var b=this.aliasable("helpers.blockHelperMissing"),c=[this.contextName(0)];this.setupHelperArgs(a,0,c);var d=this.popStack();c.splice(1,0,d),this.push(this.source.functionCall(b,"call",c))},ambiguousBlockValue:function(){var a=this.aliasable("helpers.blockHelperMissing"),b=[this.contextName(0)];this.setupHelperArgs("",0,b,!0),this.flushInline();var c=this.topStack();b.splice(1,0,c),this.pushSource(["if (!",this.lastHelper,") { ",c," = ",this.source.functionCall(a,"call",b),"}"])},appendContent:function(a){this.pendingContent?a=this.pendingContent+a:this.pendingLocation=this.source.currentLocation,this.pendingContent=a},append:function(){if(this.isInline())this.replaceStack(function(a){return[" != null ? ",a,' : ""']}),this.pushSource(this.appendToBuffer(this.popStack()));else{var a=this.popStack();this.pushSource(["if (",a," != null) { ",this.appendToBuffer(a,void 0,!0)," }"]),this.environment.isSimple&&this.pushSource(["else { ",this.appendToBuffer("''",void 0,!0)," }"])}},appendEscaped:function(){this.pushSource(this.appendToBuffer([this.aliasable("container.escapeExpression"),"(",this.popStack(),")"]))},getContext:function(a){this.lastContext=a},pushContext:function(){this.pushStackLiteral(this.contextName(this.lastContext))},lookupOnContext:function(a,b,c,d){var e=0;d||!this.options.compat||this.lastContext?this.pushContext():this.push(this.depthedLookup(a[e++])),this.resolvePath("context",a,e,b,c)},lookupBlockParam:function(a,b){this.useBlockParams=!0,this.push(["blockParams[",a[0],"][",a[1],"]"]),this.resolvePath("context",b,1)},lookupData:function(a,b,c){a?this.pushStackLiteral("container.data(data, "+a+")"):this.pushStackLiteral("data"),this.resolvePath("data",b,0,!0,c)},resolvePath:function(a,b,c,d,e){var g=this;if(this.options.strict||this.options.assumeObjects)return void this.push(f(this.options.strict&&e,this,b,a));for(var h=b.length;h>c;c++)this.replaceStack(function(e){var f=g.nameLookup(e,b[c],a);return d?[" && ",f]:[" != null ? ",f," : ",e]})},resolvePossibleLambda:function(){this.push([this.aliasable("container.lambda"),"(",this.popStack(),", ",this.contextName(0),")"])},pushStringParam:function(a,b){this.pushContext(),this.pushString(b),"SubExpression"!==b&&("string"==typeof a?this.pushString(a):this.pushStackLiteral(a))},emptyHash:function(a){this.trackIds&&this.push("{}"),this.stringParams&&(this.push("{}"),this.push("{}")),this.pushStackLiteral(a?"undefined":"{}")},pushHash:function(){this.hash&&this.hashes.push(this.hash),this.hash={values:[],types:[],contexts:[],ids:[]}},popHash:function(){var a=this.hash;this.hash=this.hashes.pop(),this.trackIds&&this.push(this.objectLiteral(a.ids)),this.stringParams&&(this.push(this.objectLiteral(a.contexts)),this.push(this.objectLiteral(a.types))),this.push(this.objectLiteral(a.values))},pushString:function(a){this.pushStackLiteral(this.quotedString(a))},pushLiteral:function(a){this.pushStackLiteral(a)},pushProgram:function(a){null!=a?this.pushStackLiteral(this.programExpression(a)):this.pushStackLiteral(null)},registerDecorator:function(a,b){var c=this.nameLookup("decorators",b,"decorator"),d=this.setupHelperArgs(b,a);this.decorators.push(["fn = ",this.decorators.functionCall(c,"",["fn","props","container",d])," || fn;"])},invokeHelper:function(a,b,c){var d=this.popStack(),e=this.setupHelper(a,b),f=c?[e.name," || "]:"",g=["("].concat(f,d);this.options.strict||g.push(" || ",this.aliasable("helpers.helperMissing")),g.push(")"),this.push(this.source.functionCall(g,"call",e.callParams))},invokeKnownHelper:function(a,b){var c=this.setupHelper(a,b);this.push(this.source.functionCall(c.name,"call",c.callParams))},invokeAmbiguous:function(a,b){this.useRegister("helper");var c=this.popStack();this.emptyHash();var d=this.setupHelper(0,a,b),e=this.lastHelper=this.nameLookup("helpers",a,"helper"),f=["(","(helper = ",e," || ",c,")"];this.options.strict||(f[0]="(helper = ",f.push(" != null ? helper : ",this.aliasable("helpers.helperMissing"))),this.push(["(",f,d.paramsInit?["),(",d.paramsInit]:[],"),","(typeof helper === ",this.aliasable('"function"')," ? ",this.source.functionCall("helper","call",d.callParams)," : helper))"])},invokePartial:function(a,b,c){var d=[],e=this.setupParams(b,1,d);a&&(b=this.popStack(),delete e.name),c&&(e.indent=JSON.stringify(c)),e.helpers="helpers",e.partials="partials",e.decorators="container.decorators",a?d.unshift(b):d.unshift(this.nameLookup("partials",b,"partial")),this.options.compat&&(e.depths="depths"),e=this.objectLiteral(e),
	d.push(e),this.push(this.source.functionCall("container.invokePartial","",d))},assignToHash:function(a){var b=this.popStack(),c=void 0,d=void 0,e=void 0;this.trackIds&&(e=this.popStack()),this.stringParams&&(d=this.popStack(),c=this.popStack());var f=this.hash;c&&(f.contexts[a]=c),d&&(f.types[a]=d),e&&(f.ids[a]=e),f.values[a]=b},pushId:function(a,b,c){"BlockParam"===a?this.pushStackLiteral("blockParams["+b[0]+"].path["+b[1]+"]"+(c?" + "+JSON.stringify("."+c):"")):"PathExpression"===a?this.pushString(b):"SubExpression"===a?this.pushStackLiteral("true"):this.pushStackLiteral("null")},compiler:e,compileChildren:function(a,b){for(var c=a.children,d=void 0,e=void 0,f=0,g=c.length;g>f;f++){d=c[f],e=new this.compiler;var h=this.matchExistingProgram(d);null==h?(this.context.programs.push(""),h=this.context.programs.length,d.index=h,d.name="program"+h,this.context.programs[h]=e.compile(d,b,this.context,!this.precompile),this.context.decorators[h]=e.decorators,this.context.environments[h]=d,this.useDepths=this.useDepths||e.useDepths,this.useBlockParams=this.useBlockParams||e.useBlockParams):(d.index=h,d.name="program"+h,this.useDepths=this.useDepths||d.useDepths,this.useBlockParams=this.useBlockParams||d.useBlockParams)}},matchExistingProgram:function(a){for(var b=0,c=this.context.environments.length;c>b;b++){var d=this.context.environments[b];if(d&&d.equals(a))return b}},programExpression:function(a){var b=this.environment.children[a],c=[b.index,"data",b.blockParams];return(this.useBlockParams||this.useDepths)&&c.push("blockParams"),this.useDepths&&c.push("depths"),"container.program("+c.join(", ")+")"},useRegister:function(a){this.registers[a]||(this.registers[a]=!0,this.registers.list.push(a))},push:function(a){return a instanceof d||(a=this.source.wrap(a)),this.inlineStack.push(a),a},pushStackLiteral:function(a){this.push(new d(a))},pushSource:function(a){this.pendingContent&&(this.source.push(this.appendToBuffer(this.source.quotedString(this.pendingContent),this.pendingLocation)),this.pendingContent=void 0),a&&this.source.push(a)},replaceStack:function(a){var b=["("],c=void 0,e=void 0,f=void 0;if(!this.isInline())throw new j["default"]("replaceStack on non-inline");var g=this.popStack(!0);if(g instanceof d)c=[g.value],b=["(",c],f=!0;else{e=!0;var h=this.incrStack();b=["((",this.push(h)," = ",g,")"],c=this.topStack()}var i=a.call(this,c);f||this.popStack(),e&&this.stackSlot--,this.push(b.concat(i,")"))},incrStack:function(){return this.stackSlot++,this.stackSlot>this.stackVars.length&&this.stackVars.push("stack"+this.stackSlot),this.topStackName()},topStackName:function(){return"stack"+this.stackSlot},flushInline:function(){var a=this.inlineStack;this.inlineStack=[];for(var b=0,c=a.length;c>b;b++){var e=a[b];if(e instanceof d)this.compileStack.push(e);else{var f=this.incrStack();this.pushSource([f," = ",e,";"]),this.compileStack.push(f)}}},isInline:function(){return this.inlineStack.length},popStack:function(a){var b=this.isInline(),c=(b?this.inlineStack:this.compileStack).pop();if(!a&&c instanceof d)return c.value;if(!b){if(!this.stackSlot)throw new j["default"]("Invalid stack pop");this.stackSlot--}return c},topStack:function(){var a=this.isInline()?this.inlineStack:this.compileStack,b=a[a.length-1];return b instanceof d?b.value:b},contextName:function(a){return this.useDepths&&a?"depths["+a+"]":"depth"+a},quotedString:function(a){return this.source.quotedString(a)},objectLiteral:function(a){return this.source.objectLiteral(a)},aliasable:function(a){var b=this.aliases[a];return b?(b.referenceCount++,b):(b=this.aliases[a]=this.source.wrap(a),b.aliasable=!0,b.referenceCount=1,b)},setupHelper:function(a,b,c){var d=[],e=this.setupHelperArgs(b,a,d,c),f=this.nameLookup("helpers",b,"helper"),g=this.aliasable(this.contextName(0)+" != null ? "+this.contextName(0)+" : {}");return{params:d,paramsInit:e,name:f,callParams:[g].concat(d)}},setupParams:function(a,b,c){var d={},e=[],f=[],g=[],h=!c,i=void 0;h&&(c=[]),d.name=this.quotedString(a),d.hash=this.popStack(),this.trackIds&&(d.hashIds=this.popStack()),this.stringParams&&(d.hashTypes=this.popStack(),d.hashContexts=this.popStack());var j=this.popStack(),k=this.popStack();(k||j)&&(d.fn=k||"container.noop",d.inverse=j||"container.noop");for(var l=b;l--;)i=this.popStack(),c[l]=i,this.trackIds&&(g[l]=this.popStack()),this.stringParams&&(f[l]=this.popStack(),e[l]=this.popStack());return h&&(d.args=this.source.generateArray(c)),this.trackIds&&(d.ids=this.source.generateArray(g)),this.stringParams&&(d.types=this.source.generateArray(f),d.contexts=this.source.generateArray(e)),this.options.data&&(d.data="data"),this.useBlockParams&&(d.blockParams="blockParams"),d},setupHelperArgs:function(a,b,c,d){var e=this.setupParams(a,b,c);return e=this.objectLiteral(e),d?(this.useRegister("options"),c.push("options"),["options=",e]):c?(c.push(e),""):e}},function(){for(var a="break else new var case finally return void catch for switch while continue function this with default if throw delete in try do instanceof typeof abstract enum int short boolean export interface static byte extends long super char final native synchronized class float package throws const goto private transient debugger implements protected volatile double import public let yield await null true false".split(" "),b=e.RESERVED_WORDS={},c=0,d=a.length;d>c;c++)b[a[c]]=!0}(),e.isValidJavaScriptVariableName=function(a){return!e.RESERVED_WORDS[a]&&/^[a-zA-Z_$][0-9a-zA-Z_$]*$/.test(a)},b["default"]=e,a.exports=b["default"]},function(a,b,c){"use strict";function d(a,b,c){if(f.isArray(a)){for(var d=[],e=0,g=a.length;g>e;e++)d.push(b.wrap(a[e],c));return d}return"boolean"==typeof a||"number"==typeof a?a+"":a}function e(a){this.srcFile=a,this.source=[]}b.__esModule=!0;var f=c(5),g=void 0;try{}catch(h){}g||(g=function(a,b,c,d){this.src="",d&&this.add(d)},g.prototype={add:function(a){f.isArray(a)&&(a=a.join("")),this.src+=a},prepend:function(a){f.isArray(a)&&(a=a.join("")),this.src=a+this.src},toStringWithSourceMap:function(){return{code:this.toString()}},toString:function(){return this.src}}),e.prototype={isEmpty:function(){return!this.source.length},prepend:function(a,b){this.source.unshift(this.wrap(a,b))},push:function(a,b){this.source.push(this.wrap(a,b))},merge:function(){var a=this.empty();return this.each(function(b){a.add(["  ",b,"\n"])}),a},each:function(a){for(var b=0,c=this.source.length;c>b;b++)a(this.source[b])},empty:function(){var a=this.currentLocation||{start:{}};return new g(a.start.line,a.start.column,this.srcFile)},wrap:function(a){var b=arguments.length<=1||void 0===arguments[1]?this.currentLocation||{start:{}}:arguments[1];return a instanceof g?a:(a=d(a,this,b),new g(b.start.line,b.start.column,this.srcFile,a))},functionCall:function(a,b,c){return c=this.generateList(c),this.wrap([a,b?"."+b+"(":"(",c,")"])},quotedString:function(a){return'"'+(a+"").replace(/\\/g,"\\\\").replace(/"/g,'\\"').replace(/\n/g,"\\n").replace(/\r/g,"\\r").replace(/\u2028/g,"\\u2028").replace(/\u2029/g,"\\u2029")+'"'},objectLiteral:function(a){var b=[];for(var c in a)if(a.hasOwnProperty(c)){var e=d(a[c],this);"undefined"!==e&&b.push([this.quotedString(c),":",e])}var f=this.generateList(b);return f.prepend("{"),f.add("}"),f},generateList:function(a){for(var b=this.empty(),c=0,e=a.length;e>c;c++)c&&b.add(","),b.add(d(a[c],this));return b},generateArray:function(a){var b=this.generateList(a);return b.prepend("["),b.add("]"),b}},b["default"]=e,a.exports=b["default"]}])});

/***/ },

/***/ 8:
/***/ function(module, exports, __webpack_require__) {

	/* WEBPACK VAR INJECTION */(function($) {'use strict';
	
	Object.defineProperty(exports, "__esModule", {
	  value: true
	});
	
	var _stringify = __webpack_require__(9);
	
	var _stringify2 = _interopRequireDefault(_stringify);
	
	var _typeof2 = __webpack_require__(12);
	
	var _typeof3 = _interopRequireDefault(_typeof2);
	
	exports.init = init;
	
	function _interopRequireDefault(obj) { return obj && obj.__esModule ? obj : { default: obj }; }
	
	__webpack_require__(79); // add .waypoint to jquery
	
	var DOMHelpers = __webpack_require__(2);
	var LinkHelpers = __webpack_require__(80);
	var HandlebarsHelpers = __webpack_require__(3);
	var APIModule = __webpack_require__(81);
	
	var FolderTreeModule = __webpack_require__(106);
	
	var linkTable = null;
	var dragStartPosition = null;
	var lastRowToggleTime = 0;
	var selectedFolderID = null;
	
	function init() {
	  linkTable = $('.item-rows');
	  setupEventHandlers();
	  setupLinksTableEventHandlers();
	}
	
	function setupEventHandlers() {
	  $(window).on("FolderTreeModule.selectionChange", function (evt, data) {
	    if ((typeof data === 'undefined' ? 'undefined' : (0, _typeof3.default)(data)) !== 'object') data = JSON.parse(data);
	    selectedFolderID = data.folderId;
	    showFolderContents(data.folderId);
	  });
	  // search form
	  $('.search-query-form').on('submit', function (e) {
	    e.preventDefault();
	    var query = DOMHelpers.getValue('.search-query');
	    if (query && query.trim()) {
	      showFolderContents(selectedFolderID, query);
	    }
	  });
	}
	
	function getLinkIDForFormElement(element) {
	  return element.closest('.item-container').find('.item-row').data('link_id');
	}
	
	function setupLinksTableEventHandlers() {
	  linkTable.on('click', 'a.clear-search', function (e) {
	    e.preventDefault();
	    showFolderContents(selectedFolderID);
	  }).on('mousedown touchstart', '.item-row', function (e) {
	    handleMouseDown(e);
	  })
	
	  // .item-row mouseup -- hide and show link details, if not dragging
	  .on('mouseup touchend', '.item-row', function (e) {
	    handleMouseUp(e);
	  })
	
	  // save changes to notes field
	  .on('input propertychange change', '.link-notes', function () {
	    var textarea = $(this);
	    var guid = getLinkIDForFormElement(textarea);
	    LinkHelpers.saveInput(guid, textarea, textarea.prevAll('.notes-save-status'), 'notes');
	  })
	
	  // save changes to title field
	  .on('input', '.link-title', function () {
	    var textarea = $(this);
	    var guid = getLinkIDForFormElement(textarea);
	    LinkHelpers.saveInput(guid, textarea, textarea.prevAll('.title-save-status'), 'title', function (data) {
	      // update display title when saved
	      textarea.closest('.item-container').find('.item-title span').text(data.title);
	    });
	  }).on('input', '.link-description', function () {
	    var textarea = $(this);
	    var guid = getLinkIDForFormElement(textarea);
	    LinkHelpers.saveInput(guid, textarea, textarea.prevAll('.description-save-status'), 'description');
	  })
	
	  // handle move-to-folder dropdown
	  .on('change', '.move-to-folder', function () {
	    var moveSelect = $(this);
	    var data = (0, _stringify2.default)({ folderId: moveSelect.val(), linkId: getLinkIDForFormElement(moveSelect) });
	    $(window).trigger("LinksListModule.moveLink", data);
	  });
	}
	
	// *** actions ***
	
	var showLoadingMessage = false;
	function initShowFolderDOM(query) {
	  if (!query || !query.trim()) {
	    // clear query after user clicks a folder
	    DOMHelpers.setInputValue('.search-query', '');
	  }
	
	  // if fetching folder contents takes more than 500ms, show a loading message
	  showLoadingMessage = true;
	  setTimeout(function () {
	    if (showLoadingMessage) {
	      DOMHelpers.emptyElement(linkTable);
	      DOMHelpers.changeHTML(linkTable, '<div class="alert-info">Loading folder contents...</div>');
	    }
	  }, 500);
	}
	
	function generateLinkFields(query, link) {
	  return LinkHelpers.generateLinkFields(link, query);
	};
	
	function showFolderContents(folderID, query) {
	  initShowFolderDOM(query);
	
	  var requestCount = 20,
	      requestData = { limit: requestCount, offset: 0 },
	      endpoint;
	
	  if (query) {
	    requestData.q = query;
	    endpoint = '/archives/';
	  } else {
	    endpoint = '/folders/' + folderID + '/archives/';
	  }
	  // Content fetcher.
	  // This is wrapped in a function so it can be called repeatedly for infinite scrolling.
	  function getNextContents() {
	    APIModule.request("GET", endpoint, requestData).success(function (response) {
	      showLoadingMessage = false;
	      var links = response.objects.map(generateLinkFields.bind(this, query));
	
	      // append HTML
	      if (requestData.offset === 0) {
	        // first run -- initialize folder
	        DOMHelpers.emptyElement(linkTable);
	      } else {
	        // subsequent run -- appending to folder
	        var linksLoadingMore = linkTable.find('.links-loading-more');
	        DOMHelpers.removeElement(linksLoadingMore);
	        if (!links.length) return;
	      }
	
	      displayLinks(links, query);
	
	      // If we received exactly `requestCount` number of links, there may be more to fetch from the server.
	      // Set a waypoint event to trigger when the last link comes into view.
	      if (links.length == requestCount) {
	        requestData.offset += requestCount;
	        linkTable.find('.item-container:last').waypoint(function (direction) {
	          this.destroy(); // cancel waypoint
	          linkTable.append('<div class="links-loading-more">Loading more ...</div>');
	          getNextContents();
	        }, {
	          offset: '100%' // trigger waypoint when element hits bottom of window
	        });
	      }
	    });
	  }
	  getNextContents();
	}
	
	function displayLinks(links, query) {
	  var templateId = '#created-link-items-template';
	  var templateArgs = { links: links, query: query };
	  var template = HandlebarsHelpers.renderTemplate(templateId, templateArgs);
	  linkTable.append(template);
	}
	
	function handleMouseDown(e) {
	  if ($(e.target).hasClass('no-drag')) return;
	
	  $.vakata.dnd.start(e, {
	    jstree: true,
	    obj: $(e.currentTarget),
	    nodes: [{ id: $(e.currentTarget).data('link_id') }]
	  }, '<div id="jstree-dnd" class="jstree-default"><i class="jstree-icon jstree-er"></i>[link]</div>');
	
	  // record drag start position so we can check how far we were dragged on mouseup
	  dragStartPosition = [e.pageX || e.originalEvent.touches[0].pageX, e.pageY || e.originalEvent.touches[0].pageY];
	}
	
	function handleMouseUp(e) {
	  // prevent JSTree's tap-to-drag behavior
	  $.vakata.dnd.stop(e);
	
	  // don't treat this as a click if the mouse has moved more than 5 pixels -- it's probably an aborted drag'n'drop or touch scroll
	  if (dragStartPosition && Math.sqrt(Math.pow(e.pageX - dragStartPosition[0], 2) * Math.pow(e.pageY - dragStartPosition[1], 2)) > 5) return;
	
	  // don't toggle faster than twice a second (in case we get both mouseup and touchend events)
	  if (new Date().getTime() - lastRowToggleTime < 500) return;
	  lastRowToggleTime = new Date().getTime();
	
	  // hide/show link details
	  var linkContainer = $(e.target).closest('.item-container'),
	      details = linkContainer.find('.item-details');
	
	  if (details.is(':visible')) {
	    details.hide();
	    linkContainer.toggleClass('_active');
	  } else {
	    var currentFolderID, moveSelect;
	
	    (function () {
	
	      // recursively populate select ...
	      var addChildren = function addChildren(node, depth) {
	        for (var i = 0; i < node.children.length; i++) {
	          var childNode = FolderTreeModule.folderTree.get_node(node.children[i]);
	
	          // For each node, we create an <option> using text() for the folder name,
	          // and then prepend some &nbsp; to show the tree structure using html().
	          // Using html for the whole thing would be an XSS risk.
	          moveSelect.append($("<option/>", {
	            value: childNode.data.folder_id,
	            text: childNode.text.trim(),
	            selected: childNode.data.folder_id == currentFolderID
	          }).prepend(new Array(depth).join('&nbsp;&nbsp;') + '- '));
	
	          // recurse
	          if (childNode.children && childNode.children.length) addChildren(childNode, depth + 1);
	        }
	      };
	
	      // when showing link details, update the move-to-folder select input
	      // based on the current folderTree structure
	
	      // first clear the select ...
	      currentFolderID = selectedFolderID;
	      moveSelect = details.find('.move-to-folder');
	
	      moveSelect.find('option').remove();
	      addChildren(FolderTreeModule.folderTree.get_node('#'), 1);
	
	      details.show();
	      linkContainer.toggleClass('_active');
	    })();
	  }
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
[330, 45],

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

/***/ 79:
/***/ function(module, exports, __webpack_require__) {

	/* WEBPACK VAR INJECTION */(function(__webpack_provided_window_dot_jQuery) {/*!
	Waypoints - 4.0.1
	Copyright © 2011-2016 Caleb Troughton
	Licensed under the MIT license.
	https://github.com/imakewebthings/waypoints/blob/master/licenses.txt
	*/
	(function() {
	  'use strict'
	
	  var keyCounter = 0
	  var allWaypoints = {}
	
	  /* http://imakewebthings.com/waypoints/api/waypoint */
	  function Waypoint(options) {
	    if (!options) {
	      throw new Error('No options passed to Waypoint constructor')
	    }
	    if (!options.element) {
	      throw new Error('No element option passed to Waypoint constructor')
	    }
	    if (!options.handler) {
	      throw new Error('No handler option passed to Waypoint constructor')
	    }
	
	    this.key = 'waypoint-' + keyCounter
	    this.options = Waypoint.Adapter.extend({}, Waypoint.defaults, options)
	    this.element = this.options.element
	    this.adapter = new Waypoint.Adapter(this.element)
	    this.callback = options.handler
	    this.axis = this.options.horizontal ? 'horizontal' : 'vertical'
	    this.enabled = this.options.enabled
	    this.triggerPoint = null
	    this.group = Waypoint.Group.findOrCreate({
	      name: this.options.group,
	      axis: this.axis
	    })
	    this.context = Waypoint.Context.findOrCreateByElement(this.options.context)
	
	    if (Waypoint.offsetAliases[this.options.offset]) {
	      this.options.offset = Waypoint.offsetAliases[this.options.offset]
	    }
	    this.group.add(this)
	    this.context.add(this)
	    allWaypoints[this.key] = this
	    keyCounter += 1
	  }
	
	  /* Private */
	  Waypoint.prototype.queueTrigger = function(direction) {
	    this.group.queueTrigger(this, direction)
	  }
	
	  /* Private */
	  Waypoint.prototype.trigger = function(args) {
	    if (!this.enabled) {
	      return
	    }
	    if (this.callback) {
	      this.callback.apply(this, args)
	    }
	  }
	
	  /* Public */
	  /* http://imakewebthings.com/waypoints/api/destroy */
	  Waypoint.prototype.destroy = function() {
	    this.context.remove(this)
	    this.group.remove(this)
	    delete allWaypoints[this.key]
	  }
	
	  /* Public */
	  /* http://imakewebthings.com/waypoints/api/disable */
	  Waypoint.prototype.disable = function() {
	    this.enabled = false
	    return this
	  }
	
	  /* Public */
	  /* http://imakewebthings.com/waypoints/api/enable */
	  Waypoint.prototype.enable = function() {
	    this.context.refresh()
	    this.enabled = true
	    return this
	  }
	
	  /* Public */
	  /* http://imakewebthings.com/waypoints/api/next */
	  Waypoint.prototype.next = function() {
	    return this.group.next(this)
	  }
	
	  /* Public */
	  /* http://imakewebthings.com/waypoints/api/previous */
	  Waypoint.prototype.previous = function() {
	    return this.group.previous(this)
	  }
	
	  /* Private */
	  Waypoint.invokeAll = function(method) {
	    var allWaypointsArray = []
	    for (var waypointKey in allWaypoints) {
	      allWaypointsArray.push(allWaypoints[waypointKey])
	    }
	    for (var i = 0, end = allWaypointsArray.length; i < end; i++) {
	      allWaypointsArray[i][method]()
	    }
	  }
	
	  /* Public */
	  /* http://imakewebthings.com/waypoints/api/destroy-all */
	  Waypoint.destroyAll = function() {
	    Waypoint.invokeAll('destroy')
	  }
	
	  /* Public */
	  /* http://imakewebthings.com/waypoints/api/disable-all */
	  Waypoint.disableAll = function() {
	    Waypoint.invokeAll('disable')
	  }
	
	  /* Public */
	  /* http://imakewebthings.com/waypoints/api/enable-all */
	  Waypoint.enableAll = function() {
	    Waypoint.Context.refreshAll()
	    for (var waypointKey in allWaypoints) {
	      allWaypoints[waypointKey].enabled = true
	    }
	    return this
	  }
	
	  /* Public */
	  /* http://imakewebthings.com/waypoints/api/refresh-all */
	  Waypoint.refreshAll = function() {
	    Waypoint.Context.refreshAll()
	  }
	
	  /* Public */
	  /* http://imakewebthings.com/waypoints/api/viewport-height */
	  Waypoint.viewportHeight = function() {
	    return window.innerHeight || document.documentElement.clientHeight
	  }
	
	  /* Public */
	  /* http://imakewebthings.com/waypoints/api/viewport-width */
	  Waypoint.viewportWidth = function() {
	    return document.documentElement.clientWidth
	  }
	
	  Waypoint.adapters = []
	
	  Waypoint.defaults = {
	    context: window,
	    continuous: true,
	    enabled: true,
	    group: 'default',
	    horizontal: false,
	    offset: 0
	  }
	
	  Waypoint.offsetAliases = {
	    'bottom-in-view': function() {
	      return this.context.innerHeight() - this.adapter.outerHeight()
	    },
	    'right-in-view': function() {
	      return this.context.innerWidth() - this.adapter.outerWidth()
	    }
	  }
	
	  window.Waypoint = Waypoint
	}())
	;(function() {
	  'use strict'
	
	  function requestAnimationFrameShim(callback) {
	    window.setTimeout(callback, 1000 / 60)
	  }
	
	  var keyCounter = 0
	  var contexts = {}
	  var Waypoint = window.Waypoint
	  var oldWindowLoad = window.onload
	
	  /* http://imakewebthings.com/waypoints/api/context */
	  function Context(element) {
	    this.element = element
	    this.Adapter = Waypoint.Adapter
	    this.adapter = new this.Adapter(element)
	    this.key = 'waypoint-context-' + keyCounter
	    this.didScroll = false
	    this.didResize = false
	    this.oldScroll = {
	      x: this.adapter.scrollLeft(),
	      y: this.adapter.scrollTop()
	    }
	    this.waypoints = {
	      vertical: {},
	      horizontal: {}
	    }
	
	    element.waypointContextKey = this.key
	    contexts[element.waypointContextKey] = this
	    keyCounter += 1
	    if (!Waypoint.windowContext) {
	      Waypoint.windowContext = true
	      Waypoint.windowContext = new Context(window)
	    }
	
	    this.createThrottledScrollHandler()
	    this.createThrottledResizeHandler()
	  }
	
	  /* Private */
	  Context.prototype.add = function(waypoint) {
	    var axis = waypoint.options.horizontal ? 'horizontal' : 'vertical'
	    this.waypoints[axis][waypoint.key] = waypoint
	    this.refresh()
	  }
	
	  /* Private */
	  Context.prototype.checkEmpty = function() {
	    var horizontalEmpty = this.Adapter.isEmptyObject(this.waypoints.horizontal)
	    var verticalEmpty = this.Adapter.isEmptyObject(this.waypoints.vertical)
	    var isWindow = this.element == this.element.window
	    if (horizontalEmpty && verticalEmpty && !isWindow) {
	      this.adapter.off('.waypoints')
	      delete contexts[this.key]
	    }
	  }
	
	  /* Private */
	  Context.prototype.createThrottledResizeHandler = function() {
	    var self = this
	
	    function resizeHandler() {
	      self.handleResize()
	      self.didResize = false
	    }
	
	    this.adapter.on('resize.waypoints', function() {
	      if (!self.didResize) {
	        self.didResize = true
	        Waypoint.requestAnimationFrame(resizeHandler)
	      }
	    })
	  }
	
	  /* Private */
	  Context.prototype.createThrottledScrollHandler = function() {
	    var self = this
	    function scrollHandler() {
	      self.handleScroll()
	      self.didScroll = false
	    }
	
	    this.adapter.on('scroll.waypoints', function() {
	      if (!self.didScroll || Waypoint.isTouch) {
	        self.didScroll = true
	        Waypoint.requestAnimationFrame(scrollHandler)
	      }
	    })
	  }
	
	  /* Private */
	  Context.prototype.handleResize = function() {
	    Waypoint.Context.refreshAll()
	  }
	
	  /* Private */
	  Context.prototype.handleScroll = function() {
	    var triggeredGroups = {}
	    var axes = {
	      horizontal: {
	        newScroll: this.adapter.scrollLeft(),
	        oldScroll: this.oldScroll.x,
	        forward: 'right',
	        backward: 'left'
	      },
	      vertical: {
	        newScroll: this.adapter.scrollTop(),
	        oldScroll: this.oldScroll.y,
	        forward: 'down',
	        backward: 'up'
	      }
	    }
	
	    for (var axisKey in axes) {
	      var axis = axes[axisKey]
	      var isForward = axis.newScroll > axis.oldScroll
	      var direction = isForward ? axis.forward : axis.backward
	
	      for (var waypointKey in this.waypoints[axisKey]) {
	        var waypoint = this.waypoints[axisKey][waypointKey]
	        if (waypoint.triggerPoint === null) {
	          continue
	        }
	        var wasBeforeTriggerPoint = axis.oldScroll < waypoint.triggerPoint
	        var nowAfterTriggerPoint = axis.newScroll >= waypoint.triggerPoint
	        var crossedForward = wasBeforeTriggerPoint && nowAfterTriggerPoint
	        var crossedBackward = !wasBeforeTriggerPoint && !nowAfterTriggerPoint
	        if (crossedForward || crossedBackward) {
	          waypoint.queueTrigger(direction)
	          triggeredGroups[waypoint.group.id] = waypoint.group
	        }
	      }
	    }
	
	    for (var groupKey in triggeredGroups) {
	      triggeredGroups[groupKey].flushTriggers()
	    }
	
	    this.oldScroll = {
	      x: axes.horizontal.newScroll,
	      y: axes.vertical.newScroll
	    }
	  }
	
	  /* Private */
	  Context.prototype.innerHeight = function() {
	    /*eslint-disable eqeqeq */
	    if (this.element == this.element.window) {
	      return Waypoint.viewportHeight()
	    }
	    /*eslint-enable eqeqeq */
	    return this.adapter.innerHeight()
	  }
	
	  /* Private */
	  Context.prototype.remove = function(waypoint) {
	    delete this.waypoints[waypoint.axis][waypoint.key]
	    this.checkEmpty()
	  }
	
	  /* Private */
	  Context.prototype.innerWidth = function() {
	    /*eslint-disable eqeqeq */
	    if (this.element == this.element.window) {
	      return Waypoint.viewportWidth()
	    }
	    /*eslint-enable eqeqeq */
	    return this.adapter.innerWidth()
	  }
	
	  /* Public */
	  /* http://imakewebthings.com/waypoints/api/context-destroy */
	  Context.prototype.destroy = function() {
	    var allWaypoints = []
	    for (var axis in this.waypoints) {
	      for (var waypointKey in this.waypoints[axis]) {
	        allWaypoints.push(this.waypoints[axis][waypointKey])
	      }
	    }
	    for (var i = 0, end = allWaypoints.length; i < end; i++) {
	      allWaypoints[i].destroy()
	    }
	  }
	
	  /* Public */
	  /* http://imakewebthings.com/waypoints/api/context-refresh */
	  Context.prototype.refresh = function() {
	    /*eslint-disable eqeqeq */
	    var isWindow = this.element == this.element.window
	    /*eslint-enable eqeqeq */
	    var contextOffset = isWindow ? undefined : this.adapter.offset()
	    var triggeredGroups = {}
	    var axes
	
	    this.handleScroll()
	    axes = {
	      horizontal: {
	        contextOffset: isWindow ? 0 : contextOffset.left,
	        contextScroll: isWindow ? 0 : this.oldScroll.x,
	        contextDimension: this.innerWidth(),
	        oldScroll: this.oldScroll.x,
	        forward: 'right',
	        backward: 'left',
	        offsetProp: 'left'
	      },
	      vertical: {
	        contextOffset: isWindow ? 0 : contextOffset.top,
	        contextScroll: isWindow ? 0 : this.oldScroll.y,
	        contextDimension: this.innerHeight(),
	        oldScroll: this.oldScroll.y,
	        forward: 'down',
	        backward: 'up',
	        offsetProp: 'top'
	      }
	    }
	
	    for (var axisKey in axes) {
	      var axis = axes[axisKey]
	      for (var waypointKey in this.waypoints[axisKey]) {
	        var waypoint = this.waypoints[axisKey][waypointKey]
	        var adjustment = waypoint.options.offset
	        var oldTriggerPoint = waypoint.triggerPoint
	        var elementOffset = 0
	        var freshWaypoint = oldTriggerPoint == null
	        var contextModifier, wasBeforeScroll, nowAfterScroll
	        var triggeredBackward, triggeredForward
	
	        if (waypoint.element !== waypoint.element.window) {
	          elementOffset = waypoint.adapter.offset()[axis.offsetProp]
	        }
	
	        if (typeof adjustment === 'function') {
	          adjustment = adjustment.apply(waypoint)
	        }
	        else if (typeof adjustment === 'string') {
	          adjustment = parseFloat(adjustment)
	          if (waypoint.options.offset.indexOf('%') > - 1) {
	            adjustment = Math.ceil(axis.contextDimension * adjustment / 100)
	          }
	        }
	
	        contextModifier = axis.contextScroll - axis.contextOffset
	        waypoint.triggerPoint = Math.floor(elementOffset + contextModifier - adjustment)
	        wasBeforeScroll = oldTriggerPoint < axis.oldScroll
	        nowAfterScroll = waypoint.triggerPoint >= axis.oldScroll
	        triggeredBackward = wasBeforeScroll && nowAfterScroll
	        triggeredForward = !wasBeforeScroll && !nowAfterScroll
	
	        if (!freshWaypoint && triggeredBackward) {
	          waypoint.queueTrigger(axis.backward)
	          triggeredGroups[waypoint.group.id] = waypoint.group
	        }
	        else if (!freshWaypoint && triggeredForward) {
	          waypoint.queueTrigger(axis.forward)
	          triggeredGroups[waypoint.group.id] = waypoint.group
	        }
	        else if (freshWaypoint && axis.oldScroll >= waypoint.triggerPoint) {
	          waypoint.queueTrigger(axis.forward)
	          triggeredGroups[waypoint.group.id] = waypoint.group
	        }
	      }
	    }
	
	    Waypoint.requestAnimationFrame(function() {
	      for (var groupKey in triggeredGroups) {
	        triggeredGroups[groupKey].flushTriggers()
	      }
	    })
	
	    return this
	  }
	
	  /* Private */
	  Context.findOrCreateByElement = function(element) {
	    return Context.findByElement(element) || new Context(element)
	  }
	
	  /* Private */
	  Context.refreshAll = function() {
	    for (var contextId in contexts) {
	      contexts[contextId].refresh()
	    }
	  }
	
	  /* Public */
	  /* http://imakewebthings.com/waypoints/api/context-find-by-element */
	  Context.findByElement = function(element) {
	    return contexts[element.waypointContextKey]
	  }
	
	  window.onload = function() {
	    if (oldWindowLoad) {
	      oldWindowLoad()
	    }
	    Context.refreshAll()
	  }
	
	
	  Waypoint.requestAnimationFrame = function(callback) {
	    var requestFn = window.requestAnimationFrame ||
	      window.mozRequestAnimationFrame ||
	      window.webkitRequestAnimationFrame ||
	      requestAnimationFrameShim
	    requestFn.call(window, callback)
	  }
	  Waypoint.Context = Context
	}())
	;(function() {
	  'use strict'
	
	  function byTriggerPoint(a, b) {
	    return a.triggerPoint - b.triggerPoint
	  }
	
	  function byReverseTriggerPoint(a, b) {
	    return b.triggerPoint - a.triggerPoint
	  }
	
	  var groups = {
	    vertical: {},
	    horizontal: {}
	  }
	  var Waypoint = window.Waypoint
	
	  /* http://imakewebthings.com/waypoints/api/group */
	  function Group(options) {
	    this.name = options.name
	    this.axis = options.axis
	    this.id = this.name + '-' + this.axis
	    this.waypoints = []
	    this.clearTriggerQueues()
	    groups[this.axis][this.name] = this
	  }
	
	  /* Private */
	  Group.prototype.add = function(waypoint) {
	    this.waypoints.push(waypoint)
	  }
	
	  /* Private */
	  Group.prototype.clearTriggerQueues = function() {
	    this.triggerQueues = {
	      up: [],
	      down: [],
	      left: [],
	      right: []
	    }
	  }
	
	  /* Private */
	  Group.prototype.flushTriggers = function() {
	    for (var direction in this.triggerQueues) {
	      var waypoints = this.triggerQueues[direction]
	      var reverse = direction === 'up' || direction === 'left'
	      waypoints.sort(reverse ? byReverseTriggerPoint : byTriggerPoint)
	      for (var i = 0, end = waypoints.length; i < end; i += 1) {
	        var waypoint = waypoints[i]
	        if (waypoint.options.continuous || i === waypoints.length - 1) {
	          waypoint.trigger([direction])
	        }
	      }
	    }
	    this.clearTriggerQueues()
	  }
	
	  /* Private */
	  Group.prototype.next = function(waypoint) {
	    this.waypoints.sort(byTriggerPoint)
	    var index = Waypoint.Adapter.inArray(waypoint, this.waypoints)
	    var isLast = index === this.waypoints.length - 1
	    return isLast ? null : this.waypoints[index + 1]
	  }
	
	  /* Private */
	  Group.prototype.previous = function(waypoint) {
	    this.waypoints.sort(byTriggerPoint)
	    var index = Waypoint.Adapter.inArray(waypoint, this.waypoints)
	    return index ? this.waypoints[index - 1] : null
	  }
	
	  /* Private */
	  Group.prototype.queueTrigger = function(waypoint, direction) {
	    this.triggerQueues[direction].push(waypoint)
	  }
	
	  /* Private */
	  Group.prototype.remove = function(waypoint) {
	    var index = Waypoint.Adapter.inArray(waypoint, this.waypoints)
	    if (index > -1) {
	      this.waypoints.splice(index, 1)
	    }
	  }
	
	  /* Public */
	  /* http://imakewebthings.com/waypoints/api/first */
	  Group.prototype.first = function() {
	    return this.waypoints[0]
	  }
	
	  /* Public */
	  /* http://imakewebthings.com/waypoints/api/last */
	  Group.prototype.last = function() {
	    return this.waypoints[this.waypoints.length - 1]
	  }
	
	  /* Private */
	  Group.findOrCreate = function(options) {
	    return groups[options.axis][options.name] || new Group(options)
	  }
	
	  Waypoint.Group = Group
	}())
	;(function() {
	  'use strict'
	
	  var $ = __webpack_provided_window_dot_jQuery
	  var Waypoint = window.Waypoint
	
	  function JQueryAdapter(element) {
	    this.$element = $(element)
	  }
	
	  $.each([
	    'innerHeight',
	    'innerWidth',
	    'off',
	    'offset',
	    'on',
	    'outerHeight',
	    'outerWidth',
	    'scrollLeft',
	    'scrollTop'
	  ], function(i, method) {
	    JQueryAdapter.prototype[method] = function() {
	      var args = Array.prototype.slice.call(arguments)
	      return this.$element[method].apply(this.$element, args)
	    }
	  })
	
	  $.each([
	    'extend',
	    'inArray',
	    'isEmptyObject'
	  ], function(i, method) {
	    JQueryAdapter[method] = $[method]
	  })
	
	  Waypoint.adapters.push({
	    name: 'jquery',
	    Adapter: JQueryAdapter
	  })
	  Waypoint.Adapter = JQueryAdapter
	}())
	;(function() {
	  'use strict'
	
	  var Waypoint = window.Waypoint
	
	  function createExtension(framework) {
	    return function() {
	      var waypoints = []
	      var overrides = arguments[0]
	
	      if (framework.isFunction(arguments[0])) {
	        overrides = framework.extend({}, arguments[1])
	        overrides.handler = arguments[0]
	      }
	
	      this.each(function() {
	        var options = framework.extend({}, overrides, {
	          element: this
	        })
	        if (typeof options.context === 'string') {
	          options.context = framework(this).closest(options.context)[0]
	        }
	        waypoints.push(new Waypoint(options))
	      })
	
	      return waypoints
	    }
	  }
	
	  if (__webpack_provided_window_dot_jQuery) {
	    __webpack_provided_window_dot_jQuery.fn.waypoint = createExtension(__webpack_provided_window_dot_jQuery)
	  }
	  if (window.Zepto) {
	    window.Zepto.fn.waypoint = createExtension(window.Zepto)
	  }
	}())
	;
	/* WEBPACK VAR INJECTION */}.call(exports, __webpack_require__(1)))

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

/***/ 106:
/***/ function(module, exports, __webpack_require__) {

	/* WEBPACK VAR INJECTION */(function($) {'use strict';
	
	Object.defineProperty(exports, "__esModule", {
	  value: true
	});
	exports.ls = exports.folderTree = undefined;
	
	var _stringify = __webpack_require__(9);
	
	var _stringify2 = _interopRequireDefault(_stringify);
	
	exports.init = init;
	exports.getSavedFolder = getSavedFolder;
	exports.getSavedOrg = getSavedOrg;
	
	function _interopRequireDefault(obj) { return obj && obj.__esModule ? obj : { default: obj }; }
	
	__webpack_require__(107); // add jquery support for .tree
	__webpack_require__(108);
	__webpack_require__(141);
	
	var APIModule = __webpack_require__(81);
	var Helpers = __webpack_require__(95);
	
	var localStorageKey = Helpers.variables.localStorageKey;
	var allowedEventsCount = 0;
	var lastSelectedFolder = null;
	var hoveredNode = null; // track currently hovered node in jsTree
	var folderTree = exports.folderTree = null;
	
	function init() {
	  domTreeInit();
	  setupEventHandlers();
	  folderTree.deselect_all();
	}
	
	// When a user selects a folder, we store that choice in Local Storage
	// and attempt to reselect on subsequent page loads.
	var ls = exports.ls = {
	  // This data structure was built such that multiple users' last-used folders could be
	  // stored simultaneously. At present, this feature is not in use: when a user logs out,
	  // local storage is cleared. getAll remains in the codebase, with getCurrent, in case we ever
	  // decide to change that behavior (not recommended at present due to the complications it may
	  // introduce to user support: we don't want to have to walk people through clearing local
	  // storage if unexpected behavior surfaces)
	  getAll: function getAll() {
	    var folders = Helpers.jsonLocalStorage.getItem(localStorageKey);
	    return folders || {};
	  },
	  getCurrent: function getCurrent() {
	    var folders = ls.getAll();
	    return folders[current_user.id] || {};
	  },
	  setCurrent: function setCurrent(orgId, folderIds) {
	    var selectedFolders = ls.getAll();
	    selectedFolders[current_user.id] = { 'folderIds': folderIds, 'orgId': orgId };
	    Helpers.jsonLocalStorage.setItem(localStorageKey, selectedFolders);
	    Helpers.triggerOnWindow("CreateLinkModule.updateLinker");
	  }
	};
	
	function getSavedFolder() {
	  // Look up the ID of the previously selected folder (if any) from localStorage.
	  var folderIds = ls.getCurrent().folderIds;
	  if (folderIds && folderIds.length) return folderIds[folderIds.length - 1];
	  return null;
	}
	
	function getSavedOrg() {
	  // Look up the ID of the previously selected folder's org (if any) from localStorage.
	  return ls.getCurrent().orgId;
	}
	
	function getSelectedNode() {
	  return folderTree.get_selected(true)[0];
	}
	
	function getSelectedFolderID() {
	  return getSelectedNode().data.folder_id;
	}
	
	function getNodeByFolderID(folderId) {
	  var folderData = folderTree._model.data;
	  for (var i in folderData) {
	    if (folderData.hasOwnProperty(i) && folderData[i].data && folderData[i].data.folder_id === folderId) {
	      return folderTree.get_node(i);
	    }
	  }
	  return null;
	}
	
	function handleSelectionChange() {
	  folderTree.close_all();
	  folderTree.deselect_all();
	  selectSavedFolder();
	}
	
	function selectSavedFolder() {
	  var folderToSelect = getSavedFolder();
	
	  //select default for users with no orgs and no saved selections
	  if (!folderToSelect && current_user.top_level_folders.length == 1) {
	    folderToSelect = current_user.top_level_folders[0].id;
	  }
	
	  folderTree.select_node(getNodeByFolderID(folderToSelect));
	}
	
	function setSavedFolder(node) {
	  var data = node.data;
	  if (data) {
	    var folderIds = folderTree.get_path(node, false, true).map(function (id) {
	      return folderTree.get_node(id).data.folder_id;
	    });
	    ls.setCurrent(data.organization_id, folderIds);
	  }
	  sendSelectionChangeEvent(node);
	}
	
	function sendSelectionChangeEvent(node) {
	  var data = {};
	  if (node.data) {
	    data.folderId = node.data.folder_id;
	    data.orgId = node.data.organization_id;
	    data.path = folderTree.get_path(node);
	  }
	  Helpers.triggerOnWindow("FolderTreeModule.selectionChange", (0, _stringify2.default)(data));
	}
	
	function handleShowFoldersEvent(currentFolder, callback) {
	  // This function gets called by jsTree with the current folder, and a callback to return subfolders.
	  // We either fetch subfolders from the API, or if currentFolder.data is empty, show the root folders.
	  var simpleCallback = function simpleCallback(callbackData) {
	    return callback.call(folderTree, callbackData);
	  };
	
	  if (currentFolder.data) {
	    loadSingleFolder(currentFolder.data.folder_id, simpleCallback);
	  } else {
	    loadInitialFolders(apiFoldersToJsTreeFolders(current_user.top_level_folders), ls.getCurrent().folderIds, simpleCallback);
	  }
	}
	
	function apiFoldersToJsTreeFolders(apiFolders) {
	  // Helper to process a list of folders from our API into the form expected by jsTree.
	  return apiFolders.map(function (folder) {
	    var jsTreeFolder = {
	      text: folder.name,
	      data: {
	        folder_id: folder.id,
	        organization_id: folder.organization
	      },
	      li_attr: {
	        "data-folder_id": folder.id,
	        "data-organization_id": folder.organization
	      },
	      "children": folder.has_children
	    };
	    if (folder.organization && !folder.parent) jsTreeFolder.type = "shared_folder";
	    return jsTreeFolder;
	  });
	}
	
	function loadSingleFolder(folderId, callback) {
	  // Grab a single folder ID from the server and pass back to jsTree.
	  APIModule.request("GET", "/folders/" + folderId + "/folders/").done(function (data) {
	    callback(apiFoldersToJsTreeFolders(data.objects));
	  });
	}
	
	function loadInitialFolders(preloadedData, subfoldersToPreload, callback) {
	  // This runs once at startup. Starting from the list of the user's root folders, fetch any
	  // subfolders in the tree that the user previously had open, and load the entire tree into jsTree at the end.
	
	  // simple case -- user has no folders selected
	  if (!subfoldersToPreload) {
	    callback(preloadedData);
	    return;
	  }
	
	  // User does have folders selected. First, have jquery fetch contents of all folders in the selected path.
	  // Set requestArgs["error"] to null to prevent a 404 from propagating up to the user.)
	  $.when.apply($, subfoldersToPreload.map(function (folderId) {
	    return APIModule.request("GET", "/folders/" + folderId + "/folders/", null, { "error": null });
	  }))
	
	  // When all API requests have returned, loop through the responses and build the folder tree:
	  .done(function () {
	    var apiResponses = arguments;
	    var parentFolders = preloadedData;
	
	    // for each folder in the path ...
	    for (var i = 0; i < subfoldersToPreload.length; i++) {
	
	      // find the parent folder to load subfolders into, and mark it opened:
	      var folderId = subfoldersToPreload[i];
	      var parentFolder = parentFolders.find(function (folder) {
	        return folderId == folder.data.folder_id;
	      });
	      if (!parentFolder)
	        // tree must have changed since last time user visited
	        break;
	      parentFolder.state = { opened: true };
	
	      // find the subfolders and load them in:
	      var apiResponse = apiResponses[i][0];
	      var subfolders = apiResponse ? apiResponse.objects : null; // if API response doesn't make sense, we'll just stop loading the tree here
	      if (subfolders && subfolders.length) {
	        parentFolder.children = apiFoldersToJsTreeFolders(subfolders);
	
	        // set the loaded subfolders as the target for the next pass through this loop
	        parentFolders = parentFolder.children;
	
	        // if no subfolders, we're done
	      } else {
	        break;
	      }
	    }
	
	    // pass our folder tree to jsTree for display
	    callback(preloadedData);
	  })
	
	  // If fetching saved folders threw any API errors, something is wrong with the saved folder path (like maybe another user
	  // moved the target folder) -- wipe the path and show top-level folders only.
	  .fail(function () {
	    localStorage.clear();
	    callback(preloadedData);
	  });
	}
	
	function domTreeInit() {
	  $('#folder-tree').jstree({
	    core: {
	      strings: {
	        'New node': 'New Folder'
	      },
	
	      'data': handleShowFoldersEvent,
	
	      check_callback: function check_callback(operation, node, node_parent, node_position, more) {
	        // Here we handle all actions on folders that have to be checked with the server.
	        // That means we have to intercept the jsTree event, cancel it,
	        // submit a request to the server, and in the success handler for that request
	        // re-trigger the event so jsTree's UI will update.
	
	        // Since we can't tell in this event handler whether an event was triggered by the user
	        // (step 1) or by us (step 2), we increment allowedEventsCount when triggering
	        // an event and decrement when the event is received:
	        if (allowedEventsCount) {
	          allowedEventsCount--;
	          return true;
	        }
	
	        var targetNode = hoveredNode;
	
	        if (more && more.is_foreign) {
	          // link dragged onto folder
	          if (operation == 'copy_node') {
	            moveLink(targetNode.data.folder_id, node.id);
	          }
	        } else {
	          // internal folder action
	          if (operation == 'rename_node') {
	            var newName = node_position;
	            renameFolder(node.data.folder_id, newName).done(function () {
	              allowedEventsCount++;
	              folderTree.rename_node(node, newName);
	              sendSelectionChangeEvent(node);
	            });
	          } else if (operation == 'move_node') {
	            moveFolder(targetNode.data.folder_id, node.data.folder_id).done(function () {
	              allowedEventsCount++;
	              folderTree.move_node(node, targetNode);
	            });
	          } else if (operation == 'delete_node') {
	            deleteFolder(node.data.folder_id).done(function () {
	              allowedEventsCount++;
	              folderTree.delete_node(node);
	              folderTree.select_node(node.parent);
	            });
	          } else if (operation == 'create_node') {
	            var newName = node.text;
	            createFolder(node_parent.data.folder_id, newName).done(function (server_response) {
	              allowedEventsCount++;
	              folderTree.create_node(node_parent, node, "last", function (new_folder_node) {
	                new_folder_node.data = { folder_id: server_response.id, organization_id: node_parent.data.organization_id };
	                editNodeName(new_folder_node);
	              });
	            });
	          }
	        }
	        return false; // cancel first instance of event while we check with server
	      },
	
	      error: function error(errorInfo) {
	        if (errorInfo.reason.substr(0, 11) != "User config" // "User config" means we canceled the operation ourself while we talk to the server
	        && errorInfo.reason != "Moving parent inside child") {
	          // error is self-explanatory
	          Helpers.informUser(errorInfo.reason);
	        }
	      },
	
	      multiple: true
	    },
	    plugins: ['contextmenu', 'dnd', 'unique', 'types'],
	    dnd: {
	      check_while_dragging: false,
	      drag_target: '.item-row',
	      drag_finish: function drag_finish(data) {},
	      // Disable opening of closed folders on drag-n-drop hover -- hover-opening causes problems because moving a folder finishes
	      // on the server before starting on the client, resulting in a moved folder colliding with itself.
	      open_timeout: 0
	    },
	    types: {
	      "default": { // requires quotes because reserved word in IE8
	        icon: "icon-folder-close-alt"
	      },
	      shared_folder: {
	        icon: "icon-sitemap"
	      }
	    }
	    // handle single clicks on folders -- show contents
	  }).on("select_node.jstree", function (e, data) {
	    if (data.selected.length == 1) {
	      // showFolderContents(data.node.data.folder_id);
	
	      // The intuitive interaction seems to be, any time you click on a closed folder we toggle it open,
	      // but we only toggle to closed if you click again on the folder that was already selected.
	      if (!data.node.state.opened || data.node == lastSelectedFolder) data.instance.toggle_node(data.node);
	    }
	
	    var lastSelectedNode = data.node;
	    setSavedFolder(lastSelectedNode);
	
	    // handle open/close folder icon
	  }).on('open_node.jstree', function (e, data) {
	    if (data.node.type == "default") data.instance.set_icon(data.node, "icon-folder-open-alt");
	  }).on('close_node.jstree', function (e, data) {
	    if (data.node.type == "default") data.instance.set_icon(data.node, "icon-folder-close-alt");
	  }).on('load_node.jstree', function (e, data) {
	    // when a new node is loaded, see if it should be selected based on a user's previous visit.
	    // (without this, doesn't select saved folders on load.)
	    selectSavedFolder();
	  })
	
	  // track currently hovered node in the hoveredNode variable:
	  .on('hover_node.jstree', function (e, data) {
	    return hoveredNode = data.node;
	  }).on('dehover_node.jstree', function (e, data) {
	    return hoveredNode = null;
	  });
	
	  exports.folderTree = folderTree = $.jstree.reference('#folder-tree');
	}
	
	function createFolder(parentFolderID, newName) {
	  return APIModule.request("POST", "/folders/" + parentFolderID + "/folders/", { name: newName });
	}
	
	function renameFolder(folderID, newName) {
	  return APIModule.request("PATCH", "/folders/" + folderID + "/", { name: newName });
	}
	
	function moveFolder(parentID, childID) {
	  return APIModule.request("PUT", "/folders/" + parentID + "/folders/" + childID + "/");
	}
	
	function deleteFolder(folderID) {
	  return APIModule.request("DELETE", "/folders/" + folderID + "/");
	}
	
	function moveLink(folderID, linkID) {
	  return APIModule.request("PUT", "/folders/" + folderID + "/archives/" + linkID + "/").done(function (data) {
	    $(window).trigger("FolderTreeModule.updateLinksRemaining", data.links_remaining);
	    // once we're done moving the link, hide it from the current folder
	    $('.item-row[data-link_id="' + linkID + '"]').closest('.item-container').remove();
	  });
	}
	
	function setupEventHandlers() {
	  $(window).on('dropdown.selectionChange', handleSelectionChange).on('LinksListModule.moveLink', function (evt, data) {
	    data = JSON.parse(data);
	    moveLink(data.folderId, data.linkId);
	  });
	
	  // set body class during drag'n'drop
	  $(document).on('dnd_start.vakata', function (e, data) {
	    $('body').addClass("dragging");
	  }).on('dnd_stop.vakata', function (e, data) {
	    $('body').removeClass("dragging");
	  });
	
	  // folder buttons
	  $('a.new-folder').on('click', function () {
	    folderTree.create_node(getSelectedNode(), {}, "last");
	    return false;
	  });
	  $('a.edit-folder').on('click', function () {
	    editNodeName(getSelectedNode());
	    return false;
	  });
	  $('a.delete-folder').on('click', function () {
	    var node = getSelectedNode();
	    if (!confirm("Really delete folder '" + node.text.trim() + "'?")) return false;
	    folderTree.delete_node(node);
	    return false;
	  });
	}
	
	function editNodeName(node) {
	  setTimeout(function () {
	    folderTree.edit(node);
	  }, 0);
	}
	/* WEBPACK VAR INJECTION */}.call(exports, __webpack_require__(1)))

/***/ },

/***/ 107:
/***/ function(module, exports, __webpack_require__) {

	var __WEBPACK_AMD_DEFINE_FACTORY__, __WEBPACK_AMD_DEFINE_ARRAY__, __WEBPACK_AMD_DEFINE_RESULT__;/*globals jQuery, define, module, exports, require, window, document, postMessage */
	(function (factory) {
		"use strict";
		if (true) {
			!(__WEBPACK_AMD_DEFINE_ARRAY__ = [__webpack_require__(1)], __WEBPACK_AMD_DEFINE_FACTORY__ = (factory), __WEBPACK_AMD_DEFINE_RESULT__ = (typeof __WEBPACK_AMD_DEFINE_FACTORY__ === 'function' ? (__WEBPACK_AMD_DEFINE_FACTORY__.apply(exports, __WEBPACK_AMD_DEFINE_ARRAY__)) : __WEBPACK_AMD_DEFINE_FACTORY__), __WEBPACK_AMD_DEFINE_RESULT__ !== undefined && (module.exports = __WEBPACK_AMD_DEFINE_RESULT__));
		}
		else if(typeof module !== 'undefined' && module.exports) {
			module.exports = factory(require('jquery'));
		}
		else {
			factory(jQuery);
		}
	}(function ($, undefined) {
		"use strict";
	/*!
	 * jsTree 3.3.2
	 * http://jstree.com/
	 *
	 * Copyright (c) 2014 Ivan Bozhanov (http://vakata.com)
	 *
	 * Licensed same as jquery - under the terms of the MIT License
	 *   http://www.opensource.org/licenses/mit-license.php
	 */
	/*!
	 * if using jslint please allow for the jQuery global and use following options:
	 * jslint: loopfunc: true, browser: true, ass: true, bitwise: true, continue: true, nomen: true, plusplus: true, regexp: true, unparam: true, todo: true, white: true
	 */
	/*jshint -W083 */
	
		// prevent another load? maybe there is a better way?
		if($.jstree) {
			return;
		}
	
		/**
		 * ### jsTree core functionality
		 */
	
		// internal variables
		var instance_counter = 0,
			ccp_node = false,
			ccp_mode = false,
			ccp_inst = false,
			themes_loaded = [],
			src = $('script:last').attr('src'),
			document = window.document, // local variable is always faster to access then a global
			_node = document.createElement('LI'), _temp1, _temp2;
	
		_node.setAttribute('role', 'treeitem');
		_temp1 = document.createElement('I');
		_temp1.className = 'jstree-icon jstree-ocl';
		_temp1.setAttribute('role', 'presentation');
		_node.appendChild(_temp1);
		_temp1 = document.createElement('A');
		_temp1.className = 'jstree-anchor';
		_temp1.setAttribute('href','#');
		_temp1.setAttribute('tabindex','-1');
		_temp2 = document.createElement('I');
		_temp2.className = 'jstree-icon jstree-themeicon';
		_temp2.setAttribute('role', 'presentation');
		_temp1.appendChild(_temp2);
		_node.appendChild(_temp1);
		_temp1 = _temp2 = null;
	
	
		/**
		 * holds all jstree related functions and variables, including the actual class and methods to create, access and manipulate instances.
		 * @name $.jstree
		 */
		$.jstree = {
			/**
			 * specifies the jstree version in use
			 * @name $.jstree.version
			 */
			version : '3.3.2',
			/**
			 * holds all the default options used when creating new instances
			 * @name $.jstree.defaults
			 */
			defaults : {
				/**
				 * configure which plugins will be active on an instance. Should be an array of strings, where each element is a plugin name. The default is `[]`
				 * @name $.jstree.defaults.plugins
				 */
				plugins : []
			},
			/**
			 * stores all loaded jstree plugins (used internally)
			 * @name $.jstree.plugins
			 */
			plugins : {},
			path : src && src.indexOf('/') !== -1 ? src.replace(/\/[^\/]+$/,'') : '',
			idregex : /[\\:&!^|()\[\]<>@*'+~#";.,=\- \/${}%?`]/g,
			root : '#'
		};
		/**
		 * creates a jstree instance
		 * @name $.jstree.create(el [, options])
		 * @param {DOMElement|jQuery|String} el the element to create the instance on, can be jQuery extended or a selector
		 * @param {Object} options options for this instance (extends `$.jstree.defaults`)
		 * @return {jsTree} the new instance
		 */
		$.jstree.create = function (el, options) {
			var tmp = new $.jstree.core(++instance_counter),
				opt = options;
			options = $.extend(true, {}, $.jstree.defaults, options);
			if(opt && opt.plugins) {
				options.plugins = opt.plugins;
			}
			$.each(options.plugins, function (i, k) {
				if(i !== 'core') {
					tmp = tmp.plugin(k, options[k]);
				}
			});
			$(el).data('jstree', tmp);
			tmp.init(el, options);
			return tmp;
		};
		/**
		 * remove all traces of jstree from the DOM and destroy all instances
		 * @name $.jstree.destroy()
		 */
		$.jstree.destroy = function () {
			$('.jstree:jstree').jstree('destroy');
			$(document).off('.jstree');
		};
		/**
		 * the jstree class constructor, used only internally
		 * @private
		 * @name $.jstree.core(id)
		 * @param {Number} id this instance's index
		 */
		$.jstree.core = function (id) {
			this._id = id;
			this._cnt = 0;
			this._wrk = null;
			this._data = {
				core : {
					themes : {
						name : false,
						dots : false,
						icons : false
					},
					selected : [],
					last_error : {},
					working : false,
					worker_queue : [],
					focused : null
				}
			};
		};
		/**
		 * get a reference to an existing instance
		 *
		 * __Examples__
		 *
		 *	// provided a container with an ID of "tree", and a nested node with an ID of "branch"
		 *	// all of there will return the same instance
		 *	$.jstree.reference('tree');
		 *	$.jstree.reference('#tree');
		 *	$.jstree.reference($('#tree'));
		 *	$.jstree.reference(document.getElementByID('tree'));
		 *	$.jstree.reference('branch');
		 *	$.jstree.reference('#branch');
		 *	$.jstree.reference($('#branch'));
		 *	$.jstree.reference(document.getElementByID('branch'));
		 *
		 * @name $.jstree.reference(needle)
		 * @param {DOMElement|jQuery|String} needle
		 * @return {jsTree|null} the instance or `null` if not found
		 */
		$.jstree.reference = function (needle) {
			var tmp = null,
				obj = null;
			if(needle && needle.id && (!needle.tagName || !needle.nodeType)) { needle = needle.id; }
	
			if(!obj || !obj.length) {
				try { obj = $(needle); } catch (ignore) { }
			}
			if(!obj || !obj.length) {
				try { obj = $('#' + needle.replace($.jstree.idregex,'\\$&')); } catch (ignore) { }
			}
			if(obj && obj.length && (obj = obj.closest('.jstree')).length && (obj = obj.data('jstree'))) {
				tmp = obj;
			}
			else {
				$('.jstree').each(function () {
					var inst = $(this).data('jstree');
					if(inst && inst._model.data[needle]) {
						tmp = inst;
						return false;
					}
				});
			}
			return tmp;
		};
		/**
		 * Create an instance, get an instance or invoke a command on a instance.
		 *
		 * If there is no instance associated with the current node a new one is created and `arg` is used to extend `$.jstree.defaults` for this new instance. There would be no return value (chaining is not broken).
		 *
		 * If there is an existing instance and `arg` is a string the command specified by `arg` is executed on the instance, with any additional arguments passed to the function. If the function returns a value it will be returned (chaining could break depending on function).
		 *
		 * If there is an existing instance and `arg` is not a string the instance itself is returned (similar to `$.jstree.reference`).
		 *
		 * In any other case - nothing is returned and chaining is not broken.
		 *
		 * __Examples__
		 *
		 *	$('#tree1').jstree(); // creates an instance
		 *	$('#tree2').jstree({ plugins : [] }); // create an instance with some options
		 *	$('#tree1').jstree('open_node', '#branch_1'); // call a method on an existing instance, passing additional arguments
		 *	$('#tree2').jstree(); // get an existing instance (or create an instance)
		 *	$('#tree2').jstree(true); // get an existing instance (will not create new instance)
		 *	$('#branch_1').jstree().select_node('#branch_1'); // get an instance (using a nested element and call a method)
		 *
		 * @name $().jstree([arg])
		 * @param {String|Object} arg
		 * @return {Mixed}
		 */
		$.fn.jstree = function (arg) {
			// check for string argument
			var is_method	= (typeof arg === 'string'),
				args		= Array.prototype.slice.call(arguments, 1),
				result		= null;
			if(arg === true && !this.length) { return false; }
			this.each(function () {
				// get the instance (if there is one) and method (if it exists)
				var instance = $.jstree.reference(this),
					method = is_method && instance ? instance[arg] : null;
				// if calling a method, and method is available - execute on the instance
				result = is_method && method ?
					method.apply(instance, args) :
					null;
				// if there is no instance and no method is being called - create one
				if(!instance && !is_method && (arg === undefined || $.isPlainObject(arg))) {
					$.jstree.create(this, arg);
				}
				// if there is an instance and no method is called - return the instance
				if( (instance && !is_method) || arg === true ) {
					result = instance || false;
				}
				// if there was a method call which returned a result - break and return the value
				if(result !== null && result !== undefined) {
					return false;
				}
			});
			// if there was a method call with a valid return value - return that, otherwise continue the chain
			return result !== null && result !== undefined ?
				result : this;
		};
		/**
		 * used to find elements containing an instance
		 *
		 * __Examples__
		 *
		 *	$('div:jstree').each(function () {
		 *		$(this).jstree('destroy');
		 *	});
		 *
		 * @name $(':jstree')
		 * @return {jQuery}
		 */
		$.expr.pseudos.jstree = $.expr.createPseudo(function(search) {
			return function(a) {
				return $(a).hasClass('jstree') &&
					$(a).data('jstree') !== undefined;
			};
		});
	
		/**
		 * stores all defaults for the core
		 * @name $.jstree.defaults.core
		 */
		$.jstree.defaults.core = {
			/**
			 * data configuration
			 *
			 * If left as `false` the HTML inside the jstree container element is used to populate the tree (that should be an unordered list with list items).
			 *
			 * You can also pass in a HTML string or a JSON array here.
			 *
			 * It is possible to pass in a standard jQuery-like AJAX config and jstree will automatically determine if the response is JSON or HTML and use that to populate the tree.
			 * In addition to the standard jQuery ajax options here you can suppy functions for `data` and `url`, the functions will be run in the current instance's scope and a param will be passed indicating which node is being loaded, the return value of those functions will be used.
			 *
			 * The last option is to specify a function, that function will receive the node being loaded as argument and a second param which is a function which should be called with the result.
			 *
			 * __Examples__
			 *
			 *	// AJAX
			 *	$('#tree').jstree({
			 *		'core' : {
			 *			'data' : {
			 *				'url' : '/get/children/',
			 *				'data' : function (node) {
			 *					return { 'id' : node.id };
			 *				}
			 *			}
			 *		});
			 *
			 *	// direct data
			 *	$('#tree').jstree({
			 *		'core' : {
			 *			'data' : [
			 *				'Simple root node',
			 *				{
			 *					'id' : 'node_2',
			 *					'text' : 'Root node with options',
			 *					'state' : { 'opened' : true, 'selected' : true },
			 *					'children' : [ { 'text' : 'Child 1' }, 'Child 2']
			 *				}
			 *			]
			 *		}
			 *	});
			 *
			 *	// function
			 *	$('#tree').jstree({
			 *		'core' : {
			 *			'data' : function (obj, callback) {
			 *				callback.call(this, ['Root 1', 'Root 2']);
			 *			}
			 *		});
			 *
			 * @name $.jstree.defaults.core.data
			 */
			data			: false,
			/**
			 * configure the various strings used throughout the tree
			 *
			 * You can use an object where the key is the string you need to replace and the value is your replacement.
			 * Another option is to specify a function which will be called with an argument of the needed string and should return the replacement.
			 * If left as `false` no replacement is made.
			 *
			 * __Examples__
			 *
			 *	$('#tree').jstree({
			 *		'core' : {
			 *			'strings' : {
			 *				'Loading ...' : 'Please wait ...'
			 *			}
			 *		}
			 *	});
			 *
			 * @name $.jstree.defaults.core.strings
			 */
			strings			: false,
			/**
			 * determines what happens when a user tries to modify the structure of the tree
			 * If left as `false` all operations like create, rename, delete, move or copy are prevented.
			 * You can set this to `true` to allow all interactions or use a function to have better control.
			 *
			 * __Examples__
			 *
			 *	$('#tree').jstree({
			 *		'core' : {
			 *			'check_callback' : function (operation, node, node_parent, node_position, more) {
			 *				// operation can be 'create_node', 'rename_node', 'delete_node', 'move_node' or 'copy_node'
			 *				// in case of 'rename_node' node_position is filled with the new node name
			 *				return operation === 'rename_node' ? true : false;
			 *			}
			 *		}
			 *	});
			 *
			 * @name $.jstree.defaults.core.check_callback
			 */
			check_callback	: false,
			/**
			 * a callback called with a single object parameter in the instance's scope when something goes wrong (operation prevented, ajax failed, etc)
			 * @name $.jstree.defaults.core.error
			 */
			error			: $.noop,
			/**
			 * the open / close animation duration in milliseconds - set this to `false` to disable the animation (default is `200`)
			 * @name $.jstree.defaults.core.animation
			 */
			animation		: 200,
			/**
			 * a boolean indicating if multiple nodes can be selected
			 * @name $.jstree.defaults.core.multiple
			 */
			multiple		: true,
			/**
			 * theme configuration object
			 * @name $.jstree.defaults.core.themes
			 */
			themes			: {
				/**
				 * the name of the theme to use (if left as `false` the default theme is used)
				 * @name $.jstree.defaults.core.themes.name
				 */
				name			: false,
				/**
				 * the URL of the theme's CSS file, leave this as `false` if you have manually included the theme CSS (recommended). You can set this to `true` too which will try to autoload the theme.
				 * @name $.jstree.defaults.core.themes.url
				 */
				url				: false,
				/**
				 * the location of all jstree themes - only used if `url` is set to `true`
				 * @name $.jstree.defaults.core.themes.dir
				 */
				dir				: false,
				/**
				 * a boolean indicating if connecting dots are shown
				 * @name $.jstree.defaults.core.themes.dots
				 */
				dots			: true,
				/**
				 * a boolean indicating if node icons are shown
				 * @name $.jstree.defaults.core.themes.icons
				 */
				icons			: true,
				/**
				 * a boolean indicating if the tree background is striped
				 * @name $.jstree.defaults.core.themes.stripes
				 */
				stripes			: false,
				/**
				 * a string (or boolean `false`) specifying the theme variant to use (if the theme supports variants)
				 * @name $.jstree.defaults.core.themes.variant
				 */
				variant			: false,
				/**
				 * a boolean specifying if a reponsive version of the theme should kick in on smaller screens (if the theme supports it). Defaults to `false`.
				 * @name $.jstree.defaults.core.themes.responsive
				 */
				responsive		: false
			},
			/**
			 * if left as `true` all parents of all selected nodes will be opened once the tree loads (so that all selected nodes are visible to the user)
			 * @name $.jstree.defaults.core.expand_selected_onload
			 */
			expand_selected_onload : true,
			/**
			 * if left as `true` web workers will be used to parse incoming JSON data where possible, so that the UI will not be blocked by large requests. Workers are however about 30% slower. Defaults to `true`
			 * @name $.jstree.defaults.core.worker
			 */
			worker : true,
			/**
			 * Force node text to plain text (and escape HTML). Defaults to `false`
			 * @name $.jstree.defaults.core.force_text
			 */
			force_text : false,
			/**
			 * Should the node should be toggled if the text is double clicked . Defaults to `true`
			 * @name $.jstree.defaults.core.dblclick_toggle
			 */
			dblclick_toggle : true
		};
		$.jstree.core.prototype = {
			/**
			 * used to decorate an instance with a plugin. Used internally.
			 * @private
			 * @name plugin(deco [, opts])
			 * @param  {String} deco the plugin to decorate with
			 * @param  {Object} opts options for the plugin
			 * @return {jsTree}
			 */
			plugin : function (deco, opts) {
				var Child = $.jstree.plugins[deco];
				if(Child) {
					this._data[deco] = {};
					Child.prototype = this;
					return new Child(opts, this);
				}
				return this;
			},
			/**
			 * initialize the instance. Used internally.
			 * @private
			 * @name init(el, optons)
			 * @param {DOMElement|jQuery|String} el the element we are transforming
			 * @param {Object} options options for this instance
			 * @trigger init.jstree, loading.jstree, loaded.jstree, ready.jstree, changed.jstree
			 */
			init : function (el, options) {
				this._model = {
					data : {},
					changed : [],
					force_full_redraw : false,
					redraw_timeout : false,
					default_state : {
						loaded : true,
						opened : false,
						selected : false,
						disabled : false
					}
				};
				this._model.data[$.jstree.root] = {
					id : $.jstree.root,
					parent : null,
					parents : [],
					children : [],
					children_d : [],
					state : { loaded : false }
				};
	
				this.element = $(el).addClass('jstree jstree-' + this._id);
				this.settings = options;
	
				this._data.core.ready = false;
				this._data.core.loaded = false;
				this._data.core.rtl = (this.element.css("direction") === "rtl");
				this.element[this._data.core.rtl ? 'addClass' : 'removeClass']("jstree-rtl");
				this.element.attr('role','tree');
				if(this.settings.core.multiple) {
					this.element.attr('aria-multiselectable', true);
				}
				if(!this.element.attr('tabindex')) {
					this.element.attr('tabindex','0');
				}
	
				this.bind();
				/**
				 * triggered after all events are bound
				 * @event
				 * @name init.jstree
				 */
				this.trigger("init");
	
				this._data.core.original_container_html = this.element.find(" > ul > li").clone(true);
				this._data.core.original_container_html
					.find("li").addBack()
					.contents().filter(function() {
						return this.nodeType === 3 && (!this.nodeValue || /^\s+$/.test(this.nodeValue));
					})
					.remove();
				this.element.html("<"+"ul class='jstree-container-ul jstree-children' role='group'><"+"li id='j"+this._id+"_loading' class='jstree-initial-node jstree-loading jstree-leaf jstree-last' role='tree-item'><i class='jstree-icon jstree-ocl'></i><"+"a class='jstree-anchor' href='#'><i class='jstree-icon jstree-themeicon-hidden'></i>" + this.get_string("Loading ...") + "</a></li></ul>");
				this.element.attr('aria-activedescendant','j' + this._id + '_loading');
				this._data.core.li_height = this.get_container_ul().children("li").first().height() || 24;
				/**
				 * triggered after the loading text is shown and before loading starts
				 * @event
				 * @name loading.jstree
				 */
				this.trigger("loading");
				this.load_node($.jstree.root);
			},
			/**
			 * destroy an instance
			 * @name destroy()
			 * @param  {Boolean} keep_html if not set to `true` the container will be emptied, otherwise the current DOM elements will be kept intact
			 */
			destroy : function (keep_html) {
				if(this._wrk) {
					try {
						window.URL.revokeObjectURL(this._wrk);
						this._wrk = null;
					}
					catch (ignore) { }
				}
				if(!keep_html) { this.element.empty(); }
				this.teardown();
			},
			/**
			 * part of the destroying of an instance. Used internally.
			 * @private
			 * @name teardown()
			 */
			teardown : function () {
				this.unbind();
				this.element
					.removeClass('jstree')
					.removeData('jstree')
					.find("[class^='jstree']")
						.addBack()
						.attr("class", function () { return this.className.replace(/jstree[^ ]*|$/ig,''); });
				this.element = null;
			},
			/**
			 * bind all events. Used internally.
			 * @private
			 * @name bind()
			 */
			bind : function () {
				var word = '',
					tout = null,
					was_click = 0;
				this.element
					.on("dblclick.jstree", function (e) {
							if(e.target.tagName && e.target.tagName.toLowerCase() === "input") { return true; }
							if(document.selection && document.selection.empty) {
								document.selection.empty();
							}
							else {
								if(window.getSelection) {
									var sel = window.getSelection();
									try {
										sel.removeAllRanges();
										sel.collapse();
									} catch (ignore) { }
								}
							}
						})
					.on("mousedown.jstree", $.proxy(function (e) {
							if(e.target === this.element[0]) {
								e.preventDefault(); // prevent losing focus when clicking scroll arrows (FF, Chrome)
								was_click = +(new Date()); // ie does not allow to prevent losing focus
							}
						}, this))
					.on("mousedown.jstree", ".jstree-ocl", function (e) {
							e.preventDefault(); // prevent any node inside from losing focus when clicking the open/close icon
						})
					.on("click.jstree", ".jstree-ocl", $.proxy(function (e) {
							this.toggle_node(e.target);
						}, this))
					.on("dblclick.jstree", ".jstree-anchor", $.proxy(function (e) {
							if(e.target.tagName && e.target.tagName.toLowerCase() === "input") { return true; }
							if(this.settings.core.dblclick_toggle) {
								this.toggle_node(e.target);
							}
						}, this))
					.on("click.jstree", ".jstree-anchor", $.proxy(function (e) {
							e.preventDefault();
							if(e.currentTarget !== document.activeElement) { $(e.currentTarget).focus(); }
							this.activate_node(e.currentTarget, e);
						}, this))
					.on('keydown.jstree', '.jstree-anchor', $.proxy(function (e) {
							if(e.target.tagName && e.target.tagName.toLowerCase() === "input") { return true; }
							if(e.which !== 32 && e.which !== 13 && (e.shiftKey || e.ctrlKey || e.altKey || e.metaKey)) { return true; }
							var o = null;
							if(this._data.core.rtl) {
								if(e.which === 37) { e.which = 39; }
								else if(e.which === 39) { e.which = 37; }
							}
							switch(e.which) {
								case 32: // aria defines space only with Ctrl
									if(e.ctrlKey) {
										e.type = "click";
										$(e.currentTarget).trigger(e);
									}
									break;
								case 13: // enter
									e.type = "click";
									$(e.currentTarget).trigger(e);
									break;
								case 37: // left
									e.preventDefault();
									if(this.is_open(e.currentTarget)) {
										this.close_node(e.currentTarget);
									}
									else {
										o = this.get_parent(e.currentTarget);
										if(o && o.id !== $.jstree.root) { this.get_node(o, true).children('.jstree-anchor').focus(); }
									}
									break;
								case 38: // up
									e.preventDefault();
									o = this.get_prev_dom(e.currentTarget);
									if(o && o.length) { o.children('.jstree-anchor').focus(); }
									break;
								case 39: // right
									e.preventDefault();
									if(this.is_closed(e.currentTarget)) {
										this.open_node(e.currentTarget, function (o) { this.get_node(o, true).children('.jstree-anchor').focus(); });
									}
									else if (this.is_open(e.currentTarget)) {
										o = this.get_node(e.currentTarget, true).children('.jstree-children')[0];
										if(o) { $(this._firstChild(o)).children('.jstree-anchor').focus(); }
									}
									break;
								case 40: // down
									e.preventDefault();
									o = this.get_next_dom(e.currentTarget);
									if(o && o.length) { o.children('.jstree-anchor').focus(); }
									break;
								case 106: // aria defines * on numpad as open_all - not very common
									this.open_all();
									break;
								case 36: // home
									e.preventDefault();
									o = this._firstChild(this.get_container_ul()[0]);
									if(o) { $(o).children('.jstree-anchor').filter(':visible').focus(); }
									break;
								case 35: // end
									e.preventDefault();
									this.element.find('.jstree-anchor').filter(':visible').last().focus();
									break;
								case 113: // f2 - safe to include - if check_callback is false it will fail
									e.preventDefault();
									this.edit(e.currentTarget);
									break;
								default:
									break;
								/*!
								// delete
								case 46:
									e.preventDefault();
									o = this.get_node(e.currentTarget);
									if(o && o.id && o.id !== $.jstree.root) {
										o = this.is_selected(o) ? this.get_selected() : o;
										this.delete_node(o);
									}
									break;
	
								*/
							}
						}, this))
					.on("load_node.jstree", $.proxy(function (e, data) {
							if(data.status) {
								if(data.node.id === $.jstree.root && !this._data.core.loaded) {
									this._data.core.loaded = true;
									if(this._firstChild(this.get_container_ul()[0])) {
										this.element.attr('aria-activedescendant',this._firstChild(this.get_container_ul()[0]).id);
									}
									/**
									 * triggered after the root node is loaded for the first time
									 * @event
									 * @name loaded.jstree
									 */
									this.trigger("loaded");
								}
								if(!this._data.core.ready) {
									setTimeout($.proxy(function() {
										if(this.element && !this.get_container_ul().find('.jstree-loading').length) {
											this._data.core.ready = true;
											if(this._data.core.selected.length) {
												if(this.settings.core.expand_selected_onload) {
													var tmp = [], i, j;
													for(i = 0, j = this._data.core.selected.length; i < j; i++) {
														tmp = tmp.concat(this._model.data[this._data.core.selected[i]].parents);
													}
													tmp = $.vakata.array_unique(tmp);
													for(i = 0, j = tmp.length; i < j; i++) {
														this.open_node(tmp[i], false, 0);
													}
												}
												this.trigger('changed', { 'action' : 'ready', 'selected' : this._data.core.selected });
											}
											/**
											 * triggered after all nodes are finished loading
											 * @event
											 * @name ready.jstree
											 */
											this.trigger("ready");
										}
									}, this), 0);
								}
							}
						}, this))
					// quick searching when the tree is focused
					.on('keypress.jstree', $.proxy(function (e) {
							if(e.target.tagName && e.target.tagName.toLowerCase() === "input") { return true; }
							if(tout) { clearTimeout(tout); }
							tout = setTimeout(function () {
								word = '';
							}, 500);
	
							var chr = String.fromCharCode(e.which).toLowerCase(),
								col = this.element.find('.jstree-anchor').filter(':visible'),
								ind = col.index(document.activeElement) || 0,
								end = false;
							word += chr;
	
							// match for whole word from current node down (including the current node)
							if(word.length > 1) {
								col.slice(ind).each($.proxy(function (i, v) {
									if($(v).text().toLowerCase().indexOf(word) === 0) {
										$(v).focus();
										end = true;
										return false;
									}
								}, this));
								if(end) { return; }
	
								// match for whole word from the beginning of the tree
								col.slice(0, ind).each($.proxy(function (i, v) {
									if($(v).text().toLowerCase().indexOf(word) === 0) {
										$(v).focus();
										end = true;
										return false;
									}
								}, this));
								if(end) { return; }
							}
							// list nodes that start with that letter (only if word consists of a single char)
							if(new RegExp('^' + chr.replace(/[-\/\\^$*+?.()|[\]{}]/g, '\\$&') + '+$').test(word)) {
								// search for the next node starting with that letter
								col.slice(ind + 1).each($.proxy(function (i, v) {
									if($(v).text().toLowerCase().charAt(0) === chr) {
										$(v).focus();
										end = true;
										return false;
									}
								}, this));
								if(end) { return; }
	
								// search from the beginning
								col.slice(0, ind + 1).each($.proxy(function (i, v) {
									if($(v).text().toLowerCase().charAt(0) === chr) {
										$(v).focus();
										end = true;
										return false;
									}
								}, this));
								if(end) { return; }
							}
						}, this))
					// THEME RELATED
					.on("init.jstree", $.proxy(function () {
							var s = this.settings.core.themes;
							this._data.core.themes.dots			= s.dots;
							this._data.core.themes.stripes		= s.stripes;
							this._data.core.themes.icons		= s.icons;
							this.set_theme(s.name || "default", s.url);
							this.set_theme_variant(s.variant);
						}, this))
					.on("loading.jstree", $.proxy(function () {
							this[ this._data.core.themes.dots ? "show_dots" : "hide_dots" ]();
							this[ this._data.core.themes.icons ? "show_icons" : "hide_icons" ]();
							this[ this._data.core.themes.stripes ? "show_stripes" : "hide_stripes" ]();
						}, this))
					.on('blur.jstree', '.jstree-anchor', $.proxy(function (e) {
							this._data.core.focused = null;
							$(e.currentTarget).filter('.jstree-hovered').mouseleave();
							this.element.attr('tabindex', '0');
						}, this))
					.on('focus.jstree', '.jstree-anchor', $.proxy(function (e) {
							var tmp = this.get_node(e.currentTarget);
							if(tmp && tmp.id) {
								this._data.core.focused = tmp.id;
							}
							this.element.find('.jstree-hovered').not(e.currentTarget).mouseleave();
							$(e.currentTarget).mouseenter();
							this.element.attr('tabindex', '-1');
						}, this))
					.on('focus.jstree', $.proxy(function () {
							if(+(new Date()) - was_click > 500 && !this._data.core.focused) {
								was_click = 0;
								var act = this.get_node(this.element.attr('aria-activedescendant'), true);
								if(act) {
									act.find('> .jstree-anchor').focus();
								}
							}
						}, this))
					.on('mouseenter.jstree', '.jstree-anchor', $.proxy(function (e) {
							this.hover_node(e.currentTarget);
						}, this))
					.on('mouseleave.jstree', '.jstree-anchor', $.proxy(function (e) {
							this.dehover_node(e.currentTarget);
						}, this));
			},
			/**
			 * part of the destroying of an instance. Used internally.
			 * @private
			 * @name unbind()
			 */
			unbind : function () {
				this.element.off('.jstree');
				$(document).off('.jstree-' + this._id);
			},
			/**
			 * trigger an event. Used internally.
			 * @private
			 * @name trigger(ev [, data])
			 * @param  {String} ev the name of the event to trigger
			 * @param  {Object} data additional data to pass with the event
			 */
			trigger : function (ev, data) {
				if(!data) {
					data = {};
				}
				data.instance = this;
				this.element.triggerHandler(ev.replace('.jstree','') + '.jstree', data);
			},
			/**
			 * returns the jQuery extended instance container
			 * @name get_container()
			 * @return {jQuery}
			 */
			get_container : function () {
				return this.element;
			},
			/**
			 * returns the jQuery extended main UL node inside the instance container. Used internally.
			 * @private
			 * @name get_container_ul()
			 * @return {jQuery}
			 */
			get_container_ul : function () {
				return this.element.children(".jstree-children").first();
			},
			/**
			 * gets string replacements (localization). Used internally.
			 * @private
			 * @name get_string(key)
			 * @param  {String} key
			 * @return {String}
			 */
			get_string : function (key) {
				var a = this.settings.core.strings;
				if($.isFunction(a)) { return a.call(this, key); }
				if(a && a[key]) { return a[key]; }
				return key;
			},
			/**
			 * gets the first child of a DOM node. Used internally.
			 * @private
			 * @name _firstChild(dom)
			 * @param  {DOMElement} dom
			 * @return {DOMElement}
			 */
			_firstChild : function (dom) {
				dom = dom ? dom.firstChild : null;
				while(dom !== null && dom.nodeType !== 1) {
					dom = dom.nextSibling;
				}
				return dom;
			},
			/**
			 * gets the next sibling of a DOM node. Used internally.
			 * @private
			 * @name _nextSibling(dom)
			 * @param  {DOMElement} dom
			 * @return {DOMElement}
			 */
			_nextSibling : function (dom) {
				dom = dom ? dom.nextSibling : null;
				while(dom !== null && dom.nodeType !== 1) {
					dom = dom.nextSibling;
				}
				return dom;
			},
			/**
			 * gets the previous sibling of a DOM node. Used internally.
			 * @private
			 * @name _previousSibling(dom)
			 * @param  {DOMElement} dom
			 * @return {DOMElement}
			 */
			_previousSibling : function (dom) {
				dom = dom ? dom.previousSibling : null;
				while(dom !== null && dom.nodeType !== 1) {
					dom = dom.previousSibling;
				}
				return dom;
			},
			/**
			 * get the JSON representation of a node (or the actual jQuery extended DOM node) by using any input (child DOM element, ID string, selector, etc)
			 * @name get_node(obj [, as_dom])
			 * @param  {mixed} obj
			 * @param  {Boolean} as_dom
			 * @return {Object|jQuery}
			 */
			get_node : function (obj, as_dom) {
				if(obj && obj.id) {
					obj = obj.id;
				}
				var dom;
				try {
					if(this._model.data[obj]) {
						obj = this._model.data[obj];
					}
					else if(typeof obj === "string" && this._model.data[obj.replace(/^#/, '')]) {
						obj = this._model.data[obj.replace(/^#/, '')];
					}
					else if(typeof obj === "string" && (dom = $('#' + obj.replace($.jstree.idregex,'\\$&'), this.element)).length && this._model.data[dom.closest('.jstree-node').attr('id')]) {
						obj = this._model.data[dom.closest('.jstree-node').attr('id')];
					}
					else if((dom = $(obj, this.element)).length && this._model.data[dom.closest('.jstree-node').attr('id')]) {
						obj = this._model.data[dom.closest('.jstree-node').attr('id')];
					}
					else if((dom = $(obj, this.element)).length && dom.hasClass('jstree')) {
						obj = this._model.data[$.jstree.root];
					}
					else {
						return false;
					}
	
					if(as_dom) {
						obj = obj.id === $.jstree.root ? this.element : $('#' + obj.id.replace($.jstree.idregex,'\\$&'), this.element);
					}
					return obj;
				} catch (ex) { return false; }
			},
			/**
			 * get the path to a node, either consisting of node texts, or of node IDs, optionally glued together (otherwise an array)
			 * @name get_path(obj [, glue, ids])
			 * @param  {mixed} obj the node
			 * @param  {String} glue if you want the path as a string - pass the glue here (for example '/'), if a falsy value is supplied here, an array is returned
			 * @param  {Boolean} ids if set to true build the path using ID, otherwise node text is used
			 * @return {mixed}
			 */
			get_path : function (obj, glue, ids) {
				obj = obj.parents ? obj : this.get_node(obj);
				if(!obj || obj.id === $.jstree.root || !obj.parents) {
					return false;
				}
				var i, j, p = [];
				p.push(ids ? obj.id : obj.text);
				for(i = 0, j = obj.parents.length; i < j; i++) {
					p.push(ids ? obj.parents[i] : this.get_text(obj.parents[i]));
				}
				p = p.reverse().slice(1);
				return glue ? p.join(glue) : p;
			},
			/**
			 * get the next visible node that is below the `obj` node. If `strict` is set to `true` only sibling nodes are returned.
			 * @name get_next_dom(obj [, strict])
			 * @param  {mixed} obj
			 * @param  {Boolean} strict
			 * @return {jQuery}
			 */
			get_next_dom : function (obj, strict) {
				var tmp;
				obj = this.get_node(obj, true);
				if(obj[0] === this.element[0]) {
					tmp = this._firstChild(this.get_container_ul()[0]);
					while (tmp && tmp.offsetHeight === 0) {
						tmp = this._nextSibling(tmp);
					}
					return tmp ? $(tmp) : false;
				}
				if(!obj || !obj.length) {
					return false;
				}
				if(strict) {
					tmp = obj[0];
					do {
						tmp = this._nextSibling(tmp);
					} while (tmp && tmp.offsetHeight === 0);
					return tmp ? $(tmp) : false;
				}
				if(obj.hasClass("jstree-open")) {
					tmp = this._firstChild(obj.children('.jstree-children')[0]);
					while (tmp && tmp.offsetHeight === 0) {
						tmp = this._nextSibling(tmp);
					}
					if(tmp !== null) {
						return $(tmp);
					}
				}
				tmp = obj[0];
				do {
					tmp = this._nextSibling(tmp);
				} while (tmp && tmp.offsetHeight === 0);
				if(tmp !== null) {
					return $(tmp);
				}
				return obj.parentsUntil(".jstree",".jstree-node").nextAll(".jstree-node:visible").first();
			},
			/**
			 * get the previous visible node that is above the `obj` node. If `strict` is set to `true` only sibling nodes are returned.
			 * @name get_prev_dom(obj [, strict])
			 * @param  {mixed} obj
			 * @param  {Boolean} strict
			 * @return {jQuery}
			 */
			get_prev_dom : function (obj, strict) {
				var tmp;
				obj = this.get_node(obj, true);
				if(obj[0] === this.element[0]) {
					tmp = this.get_container_ul()[0].lastChild;
					while (tmp && tmp.offsetHeight === 0) {
						tmp = this._previousSibling(tmp);
					}
					return tmp ? $(tmp) : false;
				}
				if(!obj || !obj.length) {
					return false;
				}
				if(strict) {
					tmp = obj[0];
					do {
						tmp = this._previousSibling(tmp);
					} while (tmp && tmp.offsetHeight === 0);
					return tmp ? $(tmp) : false;
				}
				tmp = obj[0];
				do {
					tmp = this._previousSibling(tmp);
				} while (tmp && tmp.offsetHeight === 0);
				if(tmp !== null) {
					obj = $(tmp);
					while(obj.hasClass("jstree-open")) {
						obj = obj.children(".jstree-children").first().children(".jstree-node:visible:last");
					}
					return obj;
				}
				tmp = obj[0].parentNode.parentNode;
				return tmp && tmp.className && tmp.className.indexOf('jstree-node') !== -1 ? $(tmp) : false;
			},
			/**
			 * get the parent ID of a node
			 * @name get_parent(obj)
			 * @param  {mixed} obj
			 * @return {String}
			 */
			get_parent : function (obj) {
				obj = this.get_node(obj);
				if(!obj || obj.id === $.jstree.root) {
					return false;
				}
				return obj.parent;
			},
			/**
			 * get a jQuery collection of all the children of a node (node must be rendered)
			 * @name get_children_dom(obj)
			 * @param  {mixed} obj
			 * @return {jQuery}
			 */
			get_children_dom : function (obj) {
				obj = this.get_node(obj, true);
				if(obj[0] === this.element[0]) {
					return this.get_container_ul().children(".jstree-node");
				}
				if(!obj || !obj.length) {
					return false;
				}
				return obj.children(".jstree-children").children(".jstree-node");
			},
			/**
			 * checks if a node has children
			 * @name is_parent(obj)
			 * @param  {mixed} obj
			 * @return {Boolean}
			 */
			is_parent : function (obj) {
				obj = this.get_node(obj);
				return obj && (obj.state.loaded === false || obj.children.length > 0);
			},
			/**
			 * checks if a node is loaded (its children are available)
			 * @name is_loaded(obj)
			 * @param  {mixed} obj
			 * @return {Boolean}
			 */
			is_loaded : function (obj) {
				obj = this.get_node(obj);
				return obj && obj.state.loaded;
			},
			/**
			 * check if a node is currently loading (fetching children)
			 * @name is_loading(obj)
			 * @param  {mixed} obj
			 * @return {Boolean}
			 */
			is_loading : function (obj) {
				obj = this.get_node(obj);
				return obj && obj.state && obj.state.loading;
			},
			/**
			 * check if a node is opened
			 * @name is_open(obj)
			 * @param  {mixed} obj
			 * @return {Boolean}
			 */
			is_open : function (obj) {
				obj = this.get_node(obj);
				return obj && obj.state.opened;
			},
			/**
			 * check if a node is in a closed state
			 * @name is_closed(obj)
			 * @param  {mixed} obj
			 * @return {Boolean}
			 */
			is_closed : function (obj) {
				obj = this.get_node(obj);
				return obj && this.is_parent(obj) && !obj.state.opened;
			},
			/**
			 * check if a node has no children
			 * @name is_leaf(obj)
			 * @param  {mixed} obj
			 * @return {Boolean}
			 */
			is_leaf : function (obj) {
				return !this.is_parent(obj);
			},
			/**
			 * loads a node (fetches its children using the `core.data` setting). Multiple nodes can be passed to by using an array.
			 * @name load_node(obj [, callback])
			 * @param  {mixed} obj
			 * @param  {function} callback a function to be executed once loading is complete, the function is executed in the instance's scope and receives two arguments - the node and a boolean status
			 * @return {Boolean}
			 * @trigger load_node.jstree
			 */
			load_node : function (obj, callback) {
				var k, l, i, j, c;
				if($.isArray(obj)) {
					this._load_nodes(obj.slice(), callback);
					return true;
				}
				obj = this.get_node(obj);
				if(!obj) {
					if(callback) { callback.call(this, obj, false); }
					return false;
				}
				// if(obj.state.loading) { } // the node is already loading - just wait for it to load and invoke callback? but if called implicitly it should be loaded again?
				if(obj.state.loaded) {
					obj.state.loaded = false;
					for(i = 0, j = obj.parents.length; i < j; i++) {
						this._model.data[obj.parents[i]].children_d = $.vakata.array_filter(this._model.data[obj.parents[i]].children_d, function (v) {
							return $.inArray(v, obj.children_d) === -1;
						});
					}
					for(k = 0, l = obj.children_d.length; k < l; k++) {
						if(this._model.data[obj.children_d[k]].state.selected) {
							c = true;
						}
						delete this._model.data[obj.children_d[k]];
					}
					if (c) {
						this._data.core.selected = $.vakata.array_filter(this._data.core.selected, function (v) {
							return $.inArray(v, obj.children_d) === -1;
						});
					}
					obj.children = [];
					obj.children_d = [];
					if(c) {
						this.trigger('changed', { 'action' : 'load_node', 'node' : obj, 'selected' : this._data.core.selected });
					}
				}
				obj.state.failed = false;
				obj.state.loading = true;
				this.get_node(obj, true).addClass("jstree-loading").attr('aria-busy',true);
				this._load_node(obj, $.proxy(function (status) {
					obj = this._model.data[obj.id];
					obj.state.loading = false;
					obj.state.loaded = status;
					obj.state.failed = !obj.state.loaded;
					var dom = this.get_node(obj, true), i = 0, j = 0, m = this._model.data, has_children = false;
					for(i = 0, j = obj.children.length; i < j; i++) {
						if(m[obj.children[i]] && !m[obj.children[i]].state.hidden) {
							has_children = true;
							break;
						}
					}
					if(obj.state.loaded && dom && dom.length) {
						dom.removeClass('jstree-closed jstree-open jstree-leaf');
						if (!has_children) {
							dom.addClass('jstree-leaf');
						}
						else {
							if (obj.id !== '#') {
								dom.addClass(obj.state.opened ? 'jstree-open' : 'jstree-closed');
							}
						}
					}
					dom.removeClass("jstree-loading").attr('aria-busy',false);
					/**
					 * triggered after a node is loaded
					 * @event
					 * @name load_node.jstree
					 * @param {Object} node the node that was loading
					 * @param {Boolean} status was the node loaded successfully
					 */
					this.trigger('load_node', { "node" : obj, "status" : status });
					if(callback) {
						callback.call(this, obj, status);
					}
				}, this));
				return true;
			},
			/**
			 * load an array of nodes (will also load unavailable nodes as soon as the appear in the structure). Used internally.
			 * @private
			 * @name _load_nodes(nodes [, callback])
			 * @param  {array} nodes
			 * @param  {function} callback a function to be executed once loading is complete, the function is executed in the instance's scope and receives one argument - the array passed to _load_nodes
			 */
			_load_nodes : function (nodes, callback, is_callback, force_reload) {
				var r = true,
					c = function () { this._load_nodes(nodes, callback, true); },
					m = this._model.data, i, j, tmp = [];
				for(i = 0, j = nodes.length; i < j; i++) {
					if(m[nodes[i]] && ( (!m[nodes[i]].state.loaded && !m[nodes[i]].state.failed) || (!is_callback && force_reload) )) {
						if(!this.is_loading(nodes[i])) {
							this.load_node(nodes[i], c);
						}
						r = false;
					}
				}
				if(r) {
					for(i = 0, j = nodes.length; i < j; i++) {
						if(m[nodes[i]] && m[nodes[i]].state.loaded) {
							tmp.push(nodes[i]);
						}
					}
					if(callback && !callback.done) {
						callback.call(this, tmp);
						callback.done = true;
					}
				}
			},
			/**
			 * loads all unloaded nodes
			 * @name load_all([obj, callback])
			 * @param {mixed} obj the node to load recursively, omit to load all nodes in the tree
			 * @param {function} callback a function to be executed once loading all the nodes is complete,
			 * @trigger load_all.jstree
			 */
			load_all : function (obj, callback) {
				if(!obj) { obj = $.jstree.root; }
				obj = this.get_node(obj);
				if(!obj) { return false; }
				var to_load = [],
					m = this._model.data,
					c = m[obj.id].children_d,
					i, j;
				if(obj.state && !obj.state.loaded) {
					to_load.push(obj.id);
				}
				for(i = 0, j = c.length; i < j; i++) {
					if(m[c[i]] && m[c[i]].state && !m[c[i]].state.loaded) {
						to_load.push(c[i]);
					}
				}
				if(to_load.length) {
					this._load_nodes(to_load, function () {
						this.load_all(obj, callback);
					});
				}
				else {
					/**
					 * triggered after a load_all call completes
					 * @event
					 * @name load_all.jstree
					 * @param {Object} node the recursively loaded node
					 */
					if(callback) { callback.call(this, obj); }
					this.trigger('load_all', { "node" : obj });
				}
			},
			/**
			 * handles the actual loading of a node. Used only internally.
			 * @private
			 * @name _load_node(obj [, callback])
			 * @param  {mixed} obj
			 * @param  {function} callback a function to be executed once loading is complete, the function is executed in the instance's scope and receives one argument - a boolean status
			 * @return {Boolean}
			 */
			_load_node : function (obj, callback) {
				var s = this.settings.core.data, t;
				var notTextOrCommentNode = function notTextOrCommentNode () {
					return this.nodeType !== 3 && this.nodeType !== 8;
				};
				// use original HTML
				if(!s) {
					if(obj.id === $.jstree.root) {
						return this._append_html_data(obj, this._data.core.original_container_html.clone(true), function (status) {
							callback.call(this, status);
						});
					}
					else {
						return callback.call(this, false);
					}
					// return callback.call(this, obj.id === $.jstree.root ? this._append_html_data(obj, this._data.core.original_container_html.clone(true)) : false);
				}
				if($.isFunction(s)) {
					return s.call(this, obj, $.proxy(function (d) {
						if(d === false) {
							callback.call(this, false);
						}
						else {
							this[typeof d === 'string' ? '_append_html_data' : '_append_json_data'](obj, typeof d === 'string' ? $($.parseHTML(d)).filter(notTextOrCommentNode) : d, function (status) {
								callback.call(this, status);
							});
						}
						// return d === false ? callback.call(this, false) : callback.call(this, this[typeof d === 'string' ? '_append_html_data' : '_append_json_data'](obj, typeof d === 'string' ? $(d) : d));
					}, this));
				}
				if(typeof s === 'object') {
					if(s.url) {
						s = $.extend(true, {}, s);
						if($.isFunction(s.url)) {
							s.url = s.url.call(this, obj);
						}
						if($.isFunction(s.data)) {
							s.data = s.data.call(this, obj);
						}
						return $.ajax(s)
							.done($.proxy(function (d,t,x) {
									var type = x.getResponseHeader('Content-Type');
									if((type && type.indexOf('json') !== -1) || typeof d === "object") {
										return this._append_json_data(obj, d, function (status) { callback.call(this, status); });
										//return callback.call(this, this._append_json_data(obj, d));
									}
									if((type && type.indexOf('html') !== -1) || typeof d === "string") {
										return this._append_html_data(obj, $($.parseHTML(d)).filter(notTextOrCommentNode), function (status) { callback.call(this, status); });
										// return callback.call(this, this._append_html_data(obj, $(d)));
									}
									this._data.core.last_error = { 'error' : 'ajax', 'plugin' : 'core', 'id' : 'core_04', 'reason' : 'Could not load node', 'data' : JSON.stringify({ 'id' : obj.id, 'xhr' : x }) };
									this.settings.core.error.call(this, this._data.core.last_error);
									return callback.call(this, false);
								}, this))
							.fail($.proxy(function (f) {
									callback.call(this, false);
									this._data.core.last_error = { 'error' : 'ajax', 'plugin' : 'core', 'id' : 'core_04', 'reason' : 'Could not load node', 'data' : JSON.stringify({ 'id' : obj.id, 'xhr' : f }) };
									this.settings.core.error.call(this, this._data.core.last_error);
								}, this));
					}
					t = ($.isArray(s) || $.isPlainObject(s)) ? JSON.parse(JSON.stringify(s)) : s;
					if(obj.id === $.jstree.root) {
						return this._append_json_data(obj, t, function (status) {
							callback.call(this, status);
						});
					}
					else {
						this._data.core.last_error = { 'error' : 'nodata', 'plugin' : 'core', 'id' : 'core_05', 'reason' : 'Could not load node', 'data' : JSON.stringify({ 'id' : obj.id }) };
						this.settings.core.error.call(this, this._data.core.last_error);
						return callback.call(this, false);
					}
					//return callback.call(this, (obj.id === $.jstree.root ? this._append_json_data(obj, t) : false) );
				}
				if(typeof s === 'string') {
					if(obj.id === $.jstree.root) {
						return this._append_html_data(obj, $($.parseHTML(s)).filter(notTextOrCommentNode), function (status) {
							callback.call(this, status);
						});
					}
					else {
						this._data.core.last_error = { 'error' : 'nodata', 'plugin' : 'core', 'id' : 'core_06', 'reason' : 'Could not load node', 'data' : JSON.stringify({ 'id' : obj.id }) };
						this.settings.core.error.call(this, this._data.core.last_error);
						return callback.call(this, false);
					}
					//return callback.call(this, (obj.id === $.jstree.root ? this._append_html_data(obj, $(s)) : false) );
				}
				return callback.call(this, false);
			},
			/**
			 * adds a node to the list of nodes to redraw. Used only internally.
			 * @private
			 * @name _node_changed(obj [, callback])
			 * @param  {mixed} obj
			 */
			_node_changed : function (obj) {
				obj = this.get_node(obj);
				if(obj) {
					this._model.changed.push(obj.id);
				}
			},
			/**
			 * appends HTML content to the tree. Used internally.
			 * @private
			 * @name _append_html_data(obj, data)
			 * @param  {mixed} obj the node to append to
			 * @param  {String} data the HTML string to parse and append
			 * @trigger model.jstree, changed.jstree
			 */
			_append_html_data : function (dom, data, cb) {
				dom = this.get_node(dom);
				dom.children = [];
				dom.children_d = [];
				var dat = data.is('ul') ? data.children() : data,
					par = dom.id,
					chd = [],
					dpc = [],
					m = this._model.data,
					p = m[par],
					s = this._data.core.selected.length,
					tmp, i, j;
				dat.each($.proxy(function (i, v) {
					tmp = this._parse_model_from_html($(v), par, p.parents.concat());
					if(tmp) {
						chd.push(tmp);
						dpc.push(tmp);
						if(m[tmp].children_d.length) {
							dpc = dpc.concat(m[tmp].children_d);
						}
					}
				}, this));
				p.children = chd;
				p.children_d = dpc;
				for(i = 0, j = p.parents.length; i < j; i++) {
					m[p.parents[i]].children_d = m[p.parents[i]].children_d.concat(dpc);
				}
				/**
				 * triggered when new data is inserted to the tree model
				 * @event
				 * @name model.jstree
				 * @param {Array} nodes an array of node IDs
				 * @param {String} parent the parent ID of the nodes
				 */
				this.trigger('model', { "nodes" : dpc, 'parent' : par });
				if(par !== $.jstree.root) {
					this._node_changed(par);
					this.redraw();
				}
				else {
					this.get_container_ul().children('.jstree-initial-node').remove();
					this.redraw(true);
				}
				if(this._data.core.selected.length !== s) {
					this.trigger('changed', { 'action' : 'model', 'selected' : this._data.core.selected });
				}
				cb.call(this, true);
			},
			/**
			 * appends JSON content to the tree. Used internally.
			 * @private
			 * @name _append_json_data(obj, data)
			 * @param  {mixed} obj the node to append to
			 * @param  {String} data the JSON object to parse and append
			 * @param  {Boolean} force_processing internal param - do not set
			 * @trigger model.jstree, changed.jstree
			 */
			_append_json_data : function (dom, data, cb, force_processing) {
				if(this.element === null) { return; }
				dom = this.get_node(dom);
				dom.children = [];
				dom.children_d = [];
				// *%$@!!!
				if(data.d) {
					data = data.d;
					if(typeof data === "string") {
						data = JSON.parse(data);
					}
				}
				if(!$.isArray(data)) { data = [data]; }
				var w = null,
					args = {
						'df'	: this._model.default_state,
						'dat'	: data,
						'par'	: dom.id,
						'm'		: this._model.data,
						't_id'	: this._id,
						't_cnt'	: this._cnt,
						'sel'	: this._data.core.selected
					},
					func = function (data, undefined) {
						if(data.data) { data = data.data; }
						var dat = data.dat,
							par = data.par,
							chd = [],
							dpc = [],
							add = [],
							df = data.df,
							t_id = data.t_id,
							t_cnt = data.t_cnt,
							m = data.m,
							p = m[par],
							sel = data.sel,
							tmp, i, j, rslt,
							parse_flat = function (d, p, ps) {
								if(!ps) { ps = []; }
								else { ps = ps.concat(); }
								if(p) { ps.unshift(p); }
								var tid = d.id.toString(),
									i, j, c, e,
									tmp = {
										id			: tid,
										text		: d.text || '',
										icon		: d.icon !== undefined ? d.icon : true,
										parent		: p,
										parents		: ps,
										children	: d.children || [],
										children_d	: d.children_d || [],
										data		: d.data,
										state		: { },
										li_attr		: { id : false },
										a_attr		: { href : '#' },
										original	: false
									};
								for(i in df) {
									if(df.hasOwnProperty(i)) {
										tmp.state[i] = df[i];
									}
								}
								if(d && d.data && d.data.jstree && d.data.jstree.icon) {
									tmp.icon = d.data.jstree.icon;
								}
								if(tmp.icon === undefined || tmp.icon === null || tmp.icon === "") {
									tmp.icon = true;
								}
								if(d && d.data) {
									tmp.data = d.data;
									if(d.data.jstree) {
										for(i in d.data.jstree) {
											if(d.data.jstree.hasOwnProperty(i)) {
												tmp.state[i] = d.data.jstree[i];
											}
										}
									}
								}
								if(d && typeof d.state === 'object') {
									for (i in d.state) {
										if(d.state.hasOwnProperty(i)) {
											tmp.state[i] = d.state[i];
										}
									}
								}
								if(d && typeof d.li_attr === 'object') {
									for (i in d.li_attr) {
										if(d.li_attr.hasOwnProperty(i)) {
											tmp.li_attr[i] = d.li_attr[i];
										}
									}
								}
								if(!tmp.li_attr.id) {
									tmp.li_attr.id = tid;
								}
								if(d && typeof d.a_attr === 'object') {
									for (i in d.a_attr) {
										if(d.a_attr.hasOwnProperty(i)) {
											tmp.a_attr[i] = d.a_attr[i];
										}
									}
								}
								if(d && d.children && d.children === true) {
									tmp.state.loaded = false;
									tmp.children = [];
									tmp.children_d = [];
								}
								m[tmp.id] = tmp;
								for(i = 0, j = tmp.children.length; i < j; i++) {
									c = parse_flat(m[tmp.children[i]], tmp.id, ps);
									e = m[c];
									tmp.children_d.push(c);
									if(e.children_d.length) {
										tmp.children_d = tmp.children_d.concat(e.children_d);
									}
								}
								delete d.data;
								delete d.children;
								m[tmp.id].original = d;
								if(tmp.state.selected) {
									add.push(tmp.id);
								}
								return tmp.id;
							},
							parse_nest = function (d, p, ps) {
								if(!ps) { ps = []; }
								else { ps = ps.concat(); }
								if(p) { ps.unshift(p); }
								var tid = false, i, j, c, e, tmp;
								do {
									tid = 'j' + t_id + '_' + (++t_cnt);
								} while(m[tid]);
	
								tmp = {
									id			: false,
									text		: typeof d === 'string' ? d : '',
									icon		: typeof d === 'object' && d.icon !== undefined ? d.icon : true,
									parent		: p,
									parents		: ps,
									children	: [],
									children_d	: [],
									data		: null,
									state		: { },
									li_attr		: { id : false },
									a_attr		: { href : '#' },
									original	: false
								};
								for(i in df) {
									if(df.hasOwnProperty(i)) {
										tmp.state[i] = df[i];
									}
								}
								if(d && d.id) { tmp.id = d.id.toString(); }
								if(d && d.text) { tmp.text = d.text; }
								if(d && d.data && d.data.jstree && d.data.jstree.icon) {
									tmp.icon = d.data.jstree.icon;
								}
								if(tmp.icon === undefined || tmp.icon === null || tmp.icon === "") {
									tmp.icon = true;
								}
								if(d && d.data) {
									tmp.data = d.data;
									if(d.data.jstree) {
										for(i in d.data.jstree) {
											if(d.data.jstree.hasOwnProperty(i)) {
												tmp.state[i] = d.data.jstree[i];
											}
										}
									}
								}
								if(d && typeof d.state === 'object') {
									for (i in d.state) {
										if(d.state.hasOwnProperty(i)) {
											tmp.state[i] = d.state[i];
										}
									}
								}
								if(d && typeof d.li_attr === 'object') {
									for (i in d.li_attr) {
										if(d.li_attr.hasOwnProperty(i)) {
											tmp.li_attr[i] = d.li_attr[i];
										}
									}
								}
								if(tmp.li_attr.id && !tmp.id) {
									tmp.id = tmp.li_attr.id.toString();
								}
								if(!tmp.id) {
									tmp.id = tid;
								}
								if(!tmp.li_attr.id) {
									tmp.li_attr.id = tmp.id;
								}
								if(d && typeof d.a_attr === 'object') {
									for (i in d.a_attr) {
										if(d.a_attr.hasOwnProperty(i)) {
											tmp.a_attr[i] = d.a_attr[i];
										}
									}
								}
								if(d && d.children && d.children.length) {
									for(i = 0, j = d.children.length; i < j; i++) {
										c = parse_nest(d.children[i], tmp.id, ps);
										e = m[c];
										tmp.children.push(c);
										if(e.children_d.length) {
											tmp.children_d = tmp.children_d.concat(e.children_d);
										}
									}
									tmp.children_d = tmp.children_d.concat(tmp.children);
								}
								if(d && d.children && d.children === true) {
									tmp.state.loaded = false;
									tmp.children = [];
									tmp.children_d = [];
								}
								delete d.data;
								delete d.children;
								tmp.original = d;
								m[tmp.id] = tmp;
								if(tmp.state.selected) {
									add.push(tmp.id);
								}
								return tmp.id;
							};
	
						if(dat.length && dat[0].id !== undefined && dat[0].parent !== undefined) {
							// Flat JSON support (for easy import from DB):
							// 1) convert to object (foreach)
							for(i = 0, j = dat.length; i < j; i++) {
								if(!dat[i].children) {
									dat[i].children = [];
								}
								m[dat[i].id.toString()] = dat[i];
							}
							// 2) populate children (foreach)
							for(i = 0, j = dat.length; i < j; i++) {
								m[dat[i].parent.toString()].children.push(dat[i].id.toString());
								// populate parent.children_d
								p.children_d.push(dat[i].id.toString());
							}
							// 3) normalize && populate parents and children_d with recursion
							for(i = 0, j = p.children.length; i < j; i++) {
								tmp = parse_flat(m[p.children[i]], par, p.parents.concat());
								dpc.push(tmp);
								if(m[tmp].children_d.length) {
									dpc = dpc.concat(m[tmp].children_d);
								}
							}
							for(i = 0, j = p.parents.length; i < j; i++) {
								m[p.parents[i]].children_d = m[p.parents[i]].children_d.concat(dpc);
							}
							// ?) three_state selection - p.state.selected && t - (if three_state foreach(dat => ch) -> foreach(parents) if(parent.selected) child.selected = true;
							rslt = {
								'cnt' : t_cnt,
								'mod' : m,
								'sel' : sel,
								'par' : par,
								'dpc' : dpc,
								'add' : add
							};
						}
						else {
							for(i = 0, j = dat.length; i < j; i++) {
								tmp = parse_nest(dat[i], par, p.parents.concat());
								if(tmp) {
									chd.push(tmp);
									dpc.push(tmp);
									if(m[tmp].children_d.length) {
										dpc = dpc.concat(m[tmp].children_d);
									}
								}
							}
							p.children = chd;
							p.children_d = dpc;
							for(i = 0, j = p.parents.length; i < j; i++) {
								m[p.parents[i]].children_d = m[p.parents[i]].children_d.concat(dpc);
							}
							rslt = {
								'cnt' : t_cnt,
								'mod' : m,
								'sel' : sel,
								'par' : par,
								'dpc' : dpc,
								'add' : add
							};
						}
						if(typeof window === 'undefined' || typeof window.document === 'undefined') {
							postMessage(rslt);
						}
						else {
							return rslt;
						}
					},
					rslt = function (rslt, worker) {
						if(this.element === null) { return; }
						this._cnt = rslt.cnt;
						var i, m = this._model.data;
						for (i in m) {
							if (m.hasOwnProperty(i) && m[i].state && m[i].state.loading && rslt.mod[i]) {
								rslt.mod[i].state.loading = true;
							}
						}
						this._model.data = rslt.mod; // breaks the reference in load_node - careful
	
						if(worker) {
							var j, a = rslt.add, r = rslt.sel, s = this._data.core.selected.slice();
							m = this._model.data;
							// if selection was changed while calculating in worker
							if(r.length !== s.length || $.vakata.array_unique(r.concat(s)).length !== r.length) {
								// deselect nodes that are no longer selected
								for(i = 0, j = r.length; i < j; i++) {
									if($.inArray(r[i], a) === -1 && $.inArray(r[i], s) === -1) {
										m[r[i]].state.selected = false;
									}
								}
								// select nodes that were selected in the mean time
								for(i = 0, j = s.length; i < j; i++) {
									if($.inArray(s[i], r) === -1) {
										m[s[i]].state.selected = true;
									}
								}
							}
						}
						if(rslt.add.length) {
							this._data.core.selected = this._data.core.selected.concat(rslt.add);
						}
	
						this.trigger('model', { "nodes" : rslt.dpc, 'parent' : rslt.par });
	
						if(rslt.par !== $.jstree.root) {
							this._node_changed(rslt.par);
							this.redraw();
						}
						else {
							// this.get_container_ul().children('.jstree-initial-node').remove();
							this.redraw(true);
						}
						if(rslt.add.length) {
							this.trigger('changed', { 'action' : 'model', 'selected' : this._data.core.selected });
						}
						cb.call(this, true);
					};
				if(this.settings.core.worker && window.Blob && window.URL && window.Worker) {
					try {
						if(this._wrk === null) {
							this._wrk = window.URL.createObjectURL(
								new window.Blob(
									['self.onmessage = ' + func.toString()],
									{type:"text/javascript"}
								)
							);
						}
						if(!this._data.core.working || force_processing) {
							this._data.core.working = true;
							w = new window.Worker(this._wrk);
							w.onmessage = $.proxy(function (e) {
								rslt.call(this, e.data, true);
								try { w.terminate(); w = null; } catch(ignore) { }
								if(this._data.core.worker_queue.length) {
									this._append_json_data.apply(this, this._data.core.worker_queue.shift());
								}
								else {
									this._data.core.working = false;
								}
							}, this);
							if(!args.par) {
								if(this._data.core.worker_queue.length) {
									this._append_json_data.apply(this, this._data.core.worker_queue.shift());
								}
								else {
									this._data.core.working = false;
								}
							}
							else {
								w.postMessage(args);
							}
						}
						else {
							this._data.core.worker_queue.push([dom, data, cb, true]);
						}
					}
					catch(e) {
						rslt.call(this, func(args), false);
						if(this._data.core.worker_queue.length) {
							this._append_json_data.apply(this, this._data.core.worker_queue.shift());
						}
						else {
							this._data.core.working = false;
						}
					}
				}
				else {
					rslt.call(this, func(args), false);
				}
			},
			/**
			 * parses a node from a jQuery object and appends them to the in memory tree model. Used internally.
			 * @private
			 * @name _parse_model_from_html(d [, p, ps])
			 * @param  {jQuery} d the jQuery object to parse
			 * @param  {String} p the parent ID
			 * @param  {Array} ps list of all parents
			 * @return {String} the ID of the object added to the model
			 */
			_parse_model_from_html : function (d, p, ps) {
				if(!ps) { ps = []; }
				else { ps = [].concat(ps); }
				if(p) { ps.unshift(p); }
				var c, e, m = this._model.data,
					data = {
						id			: false,
						text		: false,
						icon		: true,
						parent		: p,
						parents		: ps,
						children	: [],
						children_d	: [],
						data		: null,
						state		: { },
						li_attr		: { id : false },
						a_attr		: { href : '#' },
						original	: false
					}, i, tmp, tid;
				for(i in this._model.default_state) {
					if(this._model.default_state.hasOwnProperty(i)) {
						data.state[i] = this._model.default_state[i];
					}
				}
				tmp = $.vakata.attributes(d, true);
				$.each(tmp, function (i, v) {
					v = $.trim(v);
					if(!v.length) { return true; }
					data.li_attr[i] = v;
					if(i === 'id') {
						data.id = v.toString();
					}
				});
				tmp = d.children('a').first();
				if(tmp.length) {
					tmp = $.vakata.attributes(tmp, true);
					$.each(tmp, function (i, v) {
						v = $.trim(v);
						if(v.length) {
							data.a_attr[i] = v;
						}
					});
				}
				tmp = d.children("a").first().length ? d.children("a").first().clone() : d.clone();
				tmp.children("ins, i, ul").remove();
				tmp = tmp.html();
				tmp = $('<div />').html(tmp);
				data.text = this.settings.core.force_text ? tmp.text() : tmp.html();
				tmp = d.data();
				data.data = tmp ? $.extend(true, {}, tmp) : null;
				data.state.opened = d.hasClass('jstree-open');
				data.state.selected = d.children('a').hasClass('jstree-clicked');
				data.state.disabled = d.children('a').hasClass('jstree-disabled');
				if(data.data && data.data.jstree) {
					for(i in data.data.jstree) {
						if(data.data.jstree.hasOwnProperty(i)) {
							data.state[i] = data.data.jstree[i];
						}
					}
				}
				tmp = d.children("a").children(".jstree-themeicon");
				if(tmp.length) {
					data.icon = tmp.hasClass('jstree-themeicon-hidden') ? false : tmp.attr('rel');
				}
				if(data.state.icon !== undefined) {
					data.icon = data.state.icon;
				}
				if(data.icon === undefined || data.icon === null || data.icon === "") {
					data.icon = true;
				}
				tmp = d.children("ul").children("li");
				do {
					tid = 'j' + this._id + '_' + (++this._cnt);
				} while(m[tid]);
				data.id = data.li_attr.id ? data.li_attr.id.toString() : tid;
				if(tmp.length) {
					tmp.each($.proxy(function (i, v) {
						c = this._parse_model_from_html($(v), data.id, ps);
						e = this._model.data[c];
						data.children.push(c);
						if(e.children_d.length) {
							data.children_d = data.children_d.concat(e.children_d);
						}
					}, this));
					data.children_d = data.children_d.concat(data.children);
				}
				else {
					if(d.hasClass('jstree-closed')) {
						data.state.loaded = false;
					}
				}
				if(data.li_attr['class']) {
					data.li_attr['class'] = data.li_attr['class'].replace('jstree-closed','').replace('jstree-open','');
				}
				if(data.a_attr['class']) {
					data.a_attr['class'] = data.a_attr['class'].replace('jstree-clicked','').replace('jstree-disabled','');
				}
				m[data.id] = data;
				if(data.state.selected) {
					this._data.core.selected.push(data.id);
				}
				return data.id;
			},
			/**
			 * parses a node from a JSON object (used when dealing with flat data, which has no nesting of children, but has id and parent properties) and appends it to the in memory tree model. Used internally.
			 * @private
			 * @name _parse_model_from_flat_json(d [, p, ps])
			 * @param  {Object} d the JSON object to parse
			 * @param  {String} p the parent ID
			 * @param  {Array} ps list of all parents
			 * @return {String} the ID of the object added to the model
			 */
			_parse_model_from_flat_json : function (d, p, ps) {
				if(!ps) { ps = []; }
				else { ps = ps.concat(); }
				if(p) { ps.unshift(p); }
				var tid = d.id.toString(),
					m = this._model.data,
					df = this._model.default_state,
					i, j, c, e,
					tmp = {
						id			: tid,
						text		: d.text || '',
						icon		: d.icon !== undefined ? d.icon : true,
						parent		: p,
						parents		: ps,
						children	: d.children || [],
						children_d	: d.children_d || [],
						data		: d.data,
						state		: { },
						li_attr		: { id : false },
						a_attr		: { href : '#' },
						original	: false
					};
				for(i in df) {
					if(df.hasOwnProperty(i)) {
						tmp.state[i] = df[i];
					}
				}
				if(d && d.data && d.data.jstree && d.data.jstree.icon) {
					tmp.icon = d.data.jstree.icon;
				}
				if(tmp.icon === undefined || tmp.icon === null || tmp.icon === "") {
					tmp.icon = true;
				}
				if(d && d.data) {
					tmp.data = d.data;
					if(d.data.jstree) {
						for(i in d.data.jstree) {
							if(d.data.jstree.hasOwnProperty(i)) {
								tmp.state[i] = d.data.jstree[i];
							}
						}
					}
				}
				if(d && typeof d.state === 'object') {
					for (i in d.state) {
						if(d.state.hasOwnProperty(i)) {
							tmp.state[i] = d.state[i];
						}
					}
				}
				if(d && typeof d.li_attr === 'object') {
					for (i in d.li_attr) {
						if(d.li_attr.hasOwnProperty(i)) {
							tmp.li_attr[i] = d.li_attr[i];
						}
					}
				}
				if(!tmp.li_attr.id) {
					tmp.li_attr.id = tid;
				}
				if(d && typeof d.a_attr === 'object') {
					for (i in d.a_attr) {
						if(d.a_attr.hasOwnProperty(i)) {
							tmp.a_attr[i] = d.a_attr[i];
						}
					}
				}
				if(d && d.children && d.children === true) {
					tmp.state.loaded = false;
					tmp.children = [];
					tmp.children_d = [];
				}
				m[tmp.id] = tmp;
				for(i = 0, j = tmp.children.length; i < j; i++) {
					c = this._parse_model_from_flat_json(m[tmp.children[i]], tmp.id, ps);
					e = m[c];
					tmp.children_d.push(c);
					if(e.children_d.length) {
						tmp.children_d = tmp.children_d.concat(e.children_d);
					}
				}
				delete d.data;
				delete d.children;
				m[tmp.id].original = d;
				if(tmp.state.selected) {
					this._data.core.selected.push(tmp.id);
				}
				return tmp.id;
			},
			/**
			 * parses a node from a JSON object and appends it to the in memory tree model. Used internally.
			 * @private
			 * @name _parse_model_from_json(d [, p, ps])
			 * @param  {Object} d the JSON object to parse
			 * @param  {String} p the parent ID
			 * @param  {Array} ps list of all parents
			 * @return {String} the ID of the object added to the model
			 */
			_parse_model_from_json : function (d, p, ps) {
				if(!ps) { ps = []; }
				else { ps = ps.concat(); }
				if(p) { ps.unshift(p); }
				var tid = false, i, j, c, e, m = this._model.data, df = this._model.default_state, tmp;
				do {
					tid = 'j' + this._id + '_' + (++this._cnt);
				} while(m[tid]);
	
				tmp = {
					id			: false,
					text		: typeof d === 'string' ? d : '',
					icon		: typeof d === 'object' && d.icon !== undefined ? d.icon : true,
					parent		: p,
					parents		: ps,
					children	: [],
					children_d	: [],
					data		: null,
					state		: { },
					li_attr		: { id : false },
					a_attr		: { href : '#' },
					original	: false
				};
				for(i in df) {
					if(df.hasOwnProperty(i)) {
						tmp.state[i] = df[i];
					}
				}
				if(d && d.id) { tmp.id = d.id.toString(); }
				if(d && d.text) { tmp.text = d.text; }
				if(d && d.data && d.data.jstree && d.data.jstree.icon) {
					tmp.icon = d.data.jstree.icon;
				}
				if(tmp.icon === undefined || tmp.icon === null || tmp.icon === "") {
					tmp.icon = true;
				}
				if(d && d.data) {
					tmp.data = d.data;
					if(d.data.jstree) {
						for(i in d.data.jstree) {
							if(d.data.jstree.hasOwnProperty(i)) {
								tmp.state[i] = d.data.jstree[i];
							}
						}
					}
				}
				if(d && typeof d.state === 'object') {
					for (i in d.state) {
						if(d.state.hasOwnProperty(i)) {
							tmp.state[i] = d.state[i];
						}
					}
				}
				if(d && typeof d.li_attr === 'object') {
					for (i in d.li_attr) {
						if(d.li_attr.hasOwnProperty(i)) {
							tmp.li_attr[i] = d.li_attr[i];
						}
					}
				}
				if(tmp.li_attr.id && !tmp.id) {
					tmp.id = tmp.li_attr.id.toString();
				}
				if(!tmp.id) {
					tmp.id = tid;
				}
				if(!tmp.li_attr.id) {
					tmp.li_attr.id = tmp.id;
				}
				if(d && typeof d.a_attr === 'object') {
					for (i in d.a_attr) {
						if(d.a_attr.hasOwnProperty(i)) {
							tmp.a_attr[i] = d.a_attr[i];
						}
					}
				}
				if(d && d.children && d.children.length) {
					for(i = 0, j = d.children.length; i < j; i++) {
						c = this._parse_model_from_json(d.children[i], tmp.id, ps);
						e = m[c];
						tmp.children.push(c);
						if(e.children_d.length) {
							tmp.children_d = tmp.children_d.concat(e.children_d);
						}
					}
					tmp.children_d = tmp.children_d.concat(tmp.children);
				}
				if(d && d.children && d.children === true) {
					tmp.state.loaded = false;
					tmp.children = [];
					tmp.children_d = [];
				}
				delete d.data;
				delete d.children;
				tmp.original = d;
				m[tmp.id] = tmp;
				if(tmp.state.selected) {
					this._data.core.selected.push(tmp.id);
				}
				return tmp.id;
			},
			/**
			 * redraws all nodes that need to be redrawn. Used internally.
			 * @private
			 * @name _redraw()
			 * @trigger redraw.jstree
			 */
			_redraw : function () {
				var nodes = this._model.force_full_redraw ? this._model.data[$.jstree.root].children.concat([]) : this._model.changed.concat([]),
					f = document.createElement('UL'), tmp, i, j, fe = this._data.core.focused;
				for(i = 0, j = nodes.length; i < j; i++) {
					tmp = this.redraw_node(nodes[i], true, this._model.force_full_redraw);
					if(tmp && this._model.force_full_redraw) {
						f.appendChild(tmp);
					}
				}
				if(this._model.force_full_redraw) {
					f.className = this.get_container_ul()[0].className;
					f.setAttribute('role','group');
					this.element.empty().append(f);
					//this.get_container_ul()[0].appendChild(f);
				}
				if(fe !== null) {
					tmp = this.get_node(fe, true);
					if(tmp && tmp.length && tmp.children('.jstree-anchor')[0] !== document.activeElement) {
						tmp.children('.jstree-anchor').focus();
					}
					else {
						this._data.core.focused = null;
					}
				}
				this._model.force_full_redraw = false;
				this._model.changed = [];
				/**
				 * triggered after nodes are redrawn
				 * @event
				 * @name redraw.jstree
				 * @param {array} nodes the redrawn nodes
				 */
				this.trigger('redraw', { "nodes" : nodes });
			},
			/**
			 * redraws all nodes that need to be redrawn or optionally - the whole tree
			 * @name redraw([full])
			 * @param {Boolean} full if set to `true` all nodes are redrawn.
			 */
			redraw : function (full) {
				if(full) {
					this._model.force_full_redraw = true;
				}
				//if(this._model.redraw_timeout) {
				//	clearTimeout(this._model.redraw_timeout);
				//}
				//this._model.redraw_timeout = setTimeout($.proxy(this._redraw, this),0);
				this._redraw();
			},
			/**
			 * redraws a single node's children. Used internally.
			 * @private
			 * @name draw_children(node)
			 * @param {mixed} node the node whose children will be redrawn
			 */
			draw_children : function (node) {
				var obj = this.get_node(node),
					i = false,
					j = false,
					k = false,
					d = document;
				if(!obj) { return false; }
				if(obj.id === $.jstree.root) { return this.redraw(true); }
				node = this.get_node(node, true);
				if(!node || !node.length) { return false; } // TODO: quick toggle
	
				node.children('.jstree-children').remove();
				node = node[0];
				if(obj.children.length && obj.state.loaded) {
					k = d.createElement('UL');
					k.setAttribute('role', 'group');
					k.className = 'jstree-children';
					for(i = 0, j = obj.children.length; i < j; i++) {
						k.appendChild(this.redraw_node(obj.children[i], true, true));
					}
					node.appendChild(k);
				}
			},
			/**
			 * redraws a single node. Used internally.
			 * @private
			 * @name redraw_node(node, deep, is_callback, force_render)
			 * @param {mixed} node the node to redraw
			 * @param {Boolean} deep should child nodes be redrawn too
			 * @param {Boolean} is_callback is this a recursion call
			 * @param {Boolean} force_render should children of closed parents be drawn anyway
			 */
			redraw_node : function (node, deep, is_callback, force_render) {
				var obj = this.get_node(node),
					par = false,
					ind = false,
					old = false,
					i = false,
					j = false,
					k = false,
					c = '',
					d = document,
					m = this._model.data,
					f = false,
					s = false,
					tmp = null,
					t = 0,
					l = 0,
					has_children = false,
					last_sibling = false;
				if(!obj) { return false; }
				if(obj.id === $.jstree.root) {  return this.redraw(true); }
				deep = deep || obj.children.length === 0;
				node = !document.querySelector ? document.getElementById(obj.id) : this.element[0].querySelector('#' + ("0123456789".indexOf(obj.id[0]) !== -1 ? '\\3' + obj.id[0] + ' ' + obj.id.substr(1).replace($.jstree.idregex,'\\$&') : obj.id.replace($.jstree.idregex,'\\$&')) ); //, this.element);
				if(!node) {
					deep = true;
					//node = d.createElement('LI');
					if(!is_callback) {
						par = obj.parent !== $.jstree.root ? $('#' + obj.parent.replace($.jstree.idregex,'\\$&'), this.element)[0] : null;
						if(par !== null && (!par || !m[obj.parent].state.opened)) {
							return false;
						}
						ind = $.inArray(obj.id, par === null ? m[$.jstree.root].children : m[obj.parent].children);
					}
				}
				else {
					node = $(node);
					if(!is_callback) {
						par = node.parent().parent()[0];
						if(par === this.element[0]) {
							par = null;
						}
						ind = node.index();
					}
					// m[obj.id].data = node.data(); // use only node's data, no need to touch jquery storage
					if(!deep && obj.children.length && !node.children('.jstree-children').length) {
						deep = true;
					}
					if(!deep) {
						old = node.children('.jstree-children')[0];
					}
					f = node.children('.jstree-anchor')[0] === document.activeElement;
					node.remove();
					//node = d.createElement('LI');
					//node = node[0];
				}
				node = _node.cloneNode(true);
				// node is DOM, deep is boolean
	
				c = 'jstree-node ';
				for(i in obj.li_attr) {
					if(obj.li_attr.hasOwnProperty(i)) {
						if(i === 'id') { continue; }
						if(i !== 'class') {
							node.setAttribute(i, obj.li_attr[i]);
						}
						else {
							c += obj.li_attr[i];
						}
					}
				}
				if(!obj.a_attr.id) {
					obj.a_attr.id = obj.id + '_anchor';
				}
				node.setAttribute('aria-selected', !!obj.state.selected);
				node.setAttribute('aria-level', obj.parents.length);
				node.setAttribute('aria-labelledby', obj.a_attr.id);
				if(obj.state.disabled) {
					node.setAttribute('aria-disabled', true);
				}
	
				for(i = 0, j = obj.children.length; i < j; i++) {
					if(!m[obj.children[i]].state.hidden) {
						has_children = true;
						break;
					}
				}
				if(obj.parent !== null && m[obj.parent] && !obj.state.hidden) {
					i = $.inArray(obj.id, m[obj.parent].children);
					last_sibling = obj.id;
					if(i !== -1) {
						i++;
						for(j = m[obj.parent].children.length; i < j; i++) {
							if(!m[m[obj.parent].children[i]].state.hidden) {
								last_sibling = m[obj.parent].children[i];
							}
							if(last_sibling !== obj.id) {
								break;
							}
						}
					}
				}
	
				if(obj.state.hidden) {
					c += ' jstree-hidden';
				}
				if(obj.state.loaded && !has_children) {
					c += ' jstree-leaf';
				}
				else {
					c += obj.state.opened && obj.state.loaded ? ' jstree-open' : ' jstree-closed';
					node.setAttribute('aria-expanded', (obj.state.opened && obj.state.loaded) );
				}
				if(last_sibling === obj.id) {
					c += ' jstree-last';
				}
				node.id = obj.id;
				node.className = c;
				c = ( obj.state.selected ? ' jstree-clicked' : '') + ( obj.state.disabled ? ' jstree-disabled' : '');
				for(j in obj.a_attr) {
					if(obj.a_attr.hasOwnProperty(j)) {
						if(j === 'href' && obj.a_attr[j] === '#') { continue; }
						if(j !== 'class') {
							node.childNodes[1].setAttribute(j, obj.a_attr[j]);
						}
						else {
							c += ' ' + obj.a_attr[j];
						}
					}
				}
				if(c.length) {
					node.childNodes[1].className = 'jstree-anchor ' + c;
				}
				if((obj.icon && obj.icon !== true) || obj.icon === false) {
					if(obj.icon === false) {
						node.childNodes[1].childNodes[0].className += ' jstree-themeicon-hidden';
					}
					else if(obj.icon.indexOf('/') === -1 && obj.icon.indexOf('.') === -1) {
						node.childNodes[1].childNodes[0].className += ' ' + obj.icon + ' jstree-themeicon-custom';
					}
					else {
						node.childNodes[1].childNodes[0].style.backgroundImage = 'url("'+obj.icon+'")';
						node.childNodes[1].childNodes[0].style.backgroundPosition = 'center center';
						node.childNodes[1].childNodes[0].style.backgroundSize = 'auto';
						node.childNodes[1].childNodes[0].className += ' jstree-themeicon-custom';
					}
				}
	
				if(this.settings.core.force_text) {
					node.childNodes[1].appendChild(d.createTextNode(obj.text));
				}
				else {
					node.childNodes[1].innerHTML += obj.text;
				}
	
	
				if(deep && obj.children.length && (obj.state.opened || force_render) && obj.state.loaded) {
					k = d.createElement('UL');
					k.setAttribute('role', 'group');
					k.className = 'jstree-children';
					for(i = 0, j = obj.children.length; i < j; i++) {
						k.appendChild(this.redraw_node(obj.children[i], deep, true));
					}
					node.appendChild(k);
				}
				if(old) {
					node.appendChild(old);
				}
				if(!is_callback) {
					// append back using par / ind
					if(!par) {
						par = this.element[0];
					}
					for(i = 0, j = par.childNodes.length; i < j; i++) {
						if(par.childNodes[i] && par.childNodes[i].className && par.childNodes[i].className.indexOf('jstree-children') !== -1) {
							tmp = par.childNodes[i];
							break;
						}
					}
					if(!tmp) {
						tmp = d.createElement('UL');
						tmp.setAttribute('role', 'group');
						tmp.className = 'jstree-children';
						par.appendChild(tmp);
					}
					par = tmp;
	
					if(ind < par.childNodes.length) {
						par.insertBefore(node, par.childNodes[ind]);
					}
					else {
						par.appendChild(node);
					}
					if(f) {
						t = this.element[0].scrollTop;
						l = this.element[0].scrollLeft;
						node.childNodes[1].focus();
						this.element[0].scrollTop = t;
						this.element[0].scrollLeft = l;
					}
				}
				if(obj.state.opened && !obj.state.loaded) {
					obj.state.opened = false;
					setTimeout($.proxy(function () {
						this.open_node(obj.id, false, 0);
					}, this), 0);
				}
				return node;
			},
			/**
			 * opens a node, revaling its children. If the node is not loaded it will be loaded and opened once ready.
			 * @name open_node(obj [, callback, animation])
			 * @param {mixed} obj the node to open
			 * @param {Function} callback a function to execute once the node is opened
			 * @param {Number} animation the animation duration in milliseconds when opening the node (overrides the `core.animation` setting). Use `false` for no animation.
			 * @trigger open_node.jstree, after_open.jstree, before_open.jstree
			 */
			open_node : function (obj, callback, animation) {
				var t1, t2, d, t;
				if($.isArray(obj)) {
					obj = obj.slice();
					for(t1 = 0, t2 = obj.length; t1 < t2; t1++) {
						this.open_node(obj[t1], callback, animation);
					}
					return true;
				}
				obj = this.get_node(obj);
				if(!obj || obj.id === $.jstree.root) {
					return false;
				}
				animation = animation === undefined ? this.settings.core.animation : animation;
				if(!this.is_closed(obj)) {
					if(callback) {
						callback.call(this, obj, false);
					}
					return false;
				}
				if(!this.is_loaded(obj)) {
					if(this.is_loading(obj)) {
						return setTimeout($.proxy(function () {
							this.open_node(obj, callback, animation);
						}, this), 500);
					}
					this.load_node(obj, function (o, ok) {
						return ok ? this.open_node(o, callback, animation) : (callback ? callback.call(this, o, false) : false);
					});
				}
				else {
					d = this.get_node(obj, true);
					t = this;
					if(d.length) {
						if(animation && d.children(".jstree-children").length) {
							d.children(".jstree-children").stop(true, true);
						}
						if(obj.children.length && !this._firstChild(d.children('.jstree-children')[0])) {
							this.draw_children(obj);
							//d = this.get_node(obj, true);
						}
						if(!animation) {
							this.trigger('before_open', { "node" : obj });
							d[0].className = d[0].className.replace('jstree-closed', 'jstree-open');
							d[0].setAttribute("aria-expanded", true);
						}
						else {
							this.trigger('before_open', { "node" : obj });
							d
								.children(".jstree-children").css("display","none").end()
								.removeClass("jstree-closed").addClass("jstree-open").attr("aria-expanded", true)
								.children(".jstree-children").stop(true, true)
									.slideDown(animation, function () {
										this.style.display = "";
										if (t.element) {
											t.trigger("after_open", { "node" : obj });
										}
									});
						}
					}
					obj.state.opened = true;
					if(callback) {
						callback.call(this, obj, true);
					}
					if(!d.length) {
						/**
						 * triggered when a node is about to be opened (if the node is supposed to be in the DOM, it will be, but it won't be visible yet)
						 * @event
						 * @name before_open.jstree
						 * @param {Object} node the opened node
						 */
						this.trigger('before_open', { "node" : obj });
					}
					/**
					 * triggered when a node is opened (if there is an animation it will not be completed yet)
					 * @event
					 * @name open_node.jstree
					 * @param {Object} node the opened node
					 */
					this.trigger('open_node', { "node" : obj });
					if(!animation || !d.length) {
						/**
						 * triggered when a node is opened and the animation is complete
						 * @event
						 * @name after_open.jstree
						 * @param {Object} node the opened node
						 */
						this.trigger("after_open", { "node" : obj });
					}
					return true;
				}
			},
			/**
			 * opens every parent of a node (node should be loaded)
			 * @name _open_to(obj)
			 * @param {mixed} obj the node to reveal
			 * @private
			 */
			_open_to : function (obj) {
				obj = this.get_node(obj);
				if(!obj || obj.id === $.jstree.root) {
					return false;
				}
				var i, j, p = obj.parents;
				for(i = 0, j = p.length; i < j; i+=1) {
					if(i !== $.jstree.root) {
						this.open_node(p[i], false, 0);
					}
				}
				return $('#' + obj.id.replace($.jstree.idregex,'\\$&'), this.element);
			},
			/**
			 * closes a node, hiding its children
			 * @name close_node(obj [, animation])
			 * @param {mixed} obj the node to close
			 * @param {Number} animation the animation duration in milliseconds when closing the node (overrides the `core.animation` setting). Use `false` for no animation.
			 * @trigger close_node.jstree, after_close.jstree
			 */
			close_node : function (obj, animation) {
				var t1, t2, t, d;
				if($.isArray(obj)) {
					obj = obj.slice();
					for(t1 = 0, t2 = obj.length; t1 < t2; t1++) {
						this.close_node(obj[t1], animation);
					}
					return true;
				}
				obj = this.get_node(obj);
				if(!obj || obj.id === $.jstree.root) {
					return false;
				}
				if(this.is_closed(obj)) {
					return false;
				}
				animation = animation === undefined ? this.settings.core.animation : animation;
				t = this;
				d = this.get_node(obj, true);
	
				obj.state.opened = false;
				/**
				 * triggered when a node is closed (if there is an animation it will not be complete yet)
				 * @event
				 * @name close_node.jstree
				 * @param {Object} node the closed node
				 */
				this.trigger('close_node',{ "node" : obj });
				if(!d.length) {
					/**
					 * triggered when a node is closed and the animation is complete
					 * @event
					 * @name after_close.jstree
					 * @param {Object} node the closed node
					 */
					this.trigger("after_close", { "node" : obj });
				}
				else {
					if(!animation) {
						d[0].className = d[0].className.replace('jstree-open', 'jstree-closed');
						d.attr("aria-expanded", false).children('.jstree-children').remove();
						this.trigger("after_close", { "node" : obj });
					}
					else {
						d
							.children(".jstree-children").attr("style","display:block !important").end()
							.removeClass("jstree-open").addClass("jstree-closed").attr("aria-expanded", false)
							.children(".jstree-children").stop(true, true).slideUp(animation, function () {
								this.style.display = "";
								d.children('.jstree-children').remove();
								if (t.element) {
									t.trigger("after_close", { "node" : obj });
								}
							});
					}
				}
			},
			/**
			 * toggles a node - closing it if it is open, opening it if it is closed
			 * @name toggle_node(obj)
			 * @param {mixed} obj the node to toggle
			 */
			toggle_node : function (obj) {
				var t1, t2;
				if($.isArray(obj)) {
					obj = obj.slice();
					for(t1 = 0, t2 = obj.length; t1 < t2; t1++) {
						this.toggle_node(obj[t1]);
					}
					return true;
				}
				if(this.is_closed(obj)) {
					return this.open_node(obj);
				}
				if(this.is_open(obj)) {
					return this.close_node(obj);
				}
			},
			/**
			 * opens all nodes within a node (or the tree), revaling their children. If the node is not loaded it will be loaded and opened once ready.
			 * @name open_all([obj, animation, original_obj])
			 * @param {mixed} obj the node to open recursively, omit to open all nodes in the tree
			 * @param {Number} animation the animation duration in milliseconds when opening the nodes, the default is no animation
			 * @param {jQuery} reference to the node that started the process (internal use)
			 * @trigger open_all.jstree
			 */
			open_all : function (obj, animation, original_obj) {
				if(!obj) { obj = $.jstree.root; }
				obj = this.get_node(obj);
				if(!obj) { return false; }
				var dom = obj.id === $.jstree.root ? this.get_container_ul() : this.get_node(obj, true), i, j, _this;
				if(!dom.length) {
					for(i = 0, j = obj.children_d.length; i < j; i++) {
						if(this.is_closed(this._model.data[obj.children_d[i]])) {
							this._model.data[obj.children_d[i]].state.opened = true;
						}
					}
					return this.trigger('open_all', { "node" : obj });
				}
				original_obj = original_obj || dom;
				_this = this;
				dom = this.is_closed(obj) ? dom.find('.jstree-closed').addBack() : dom.find('.jstree-closed');
				dom.each(function () {
					_this.open_node(
						this,
						function(node, status) { if(status && this.is_parent(node)) { this.open_all(node, animation, original_obj); } },
						animation || 0
					);
				});
				if(original_obj.find('.jstree-closed').length === 0) {
					/**
					 * triggered when an `open_all` call completes
					 * @event
					 * @name open_all.jstree
					 * @param {Object} node the opened node
					 */
					this.trigger('open_all', { "node" : this.get_node(original_obj) });
				}
			},
			/**
			 * closes all nodes within a node (or the tree), revaling their children
			 * @name close_all([obj, animation])
			 * @param {mixed} obj the node to close recursively, omit to close all nodes in the tree
			 * @param {Number} animation the animation duration in milliseconds when closing the nodes, the default is no animation
			 * @trigger close_all.jstree
			 */
			close_all : function (obj, animation) {
				if(!obj) { obj = $.jstree.root; }
				obj = this.get_node(obj);
				if(!obj) { return false; }
				var dom = obj.id === $.jstree.root ? this.get_container_ul() : this.get_node(obj, true),
					_this = this, i, j;
				if(dom.length) {
					dom = this.is_open(obj) ? dom.find('.jstree-open').addBack() : dom.find('.jstree-open');
					$(dom.get().reverse()).each(function () { _this.close_node(this, animation || 0); });
				}
				for(i = 0, j = obj.children_d.length; i < j; i++) {
					this._model.data[obj.children_d[i]].state.opened = false;
				}
				/**
				 * triggered when an `close_all` call completes
				 * @event
				 * @name close_all.jstree
				 * @param {Object} node the closed node
				 */
				this.trigger('close_all', { "node" : obj });
			},
			/**
			 * checks if a node is disabled (not selectable)
			 * @name is_disabled(obj)
			 * @param  {mixed} obj
			 * @return {Boolean}
			 */
			is_disabled : function (obj) {
				obj = this.get_node(obj);
				return obj && obj.state && obj.state.disabled;
			},
			/**
			 * enables a node - so that it can be selected
			 * @name enable_node(obj)
			 * @param {mixed} obj the node to enable
			 * @trigger enable_node.jstree
			 */
			enable_node : function (obj) {
				var t1, t2;
				if($.isArray(obj)) {
					obj = obj.slice();
					for(t1 = 0, t2 = obj.length; t1 < t2; t1++) {
						this.enable_node(obj[t1]);
					}
					return true;
				}
				obj = this.get_node(obj);
				if(!obj || obj.id === $.jstree.root) {
					return false;
				}
				obj.state.disabled = false;
				this.get_node(obj,true).children('.jstree-anchor').removeClass('jstree-disabled').attr('aria-disabled', false);
				/**
				 * triggered when an node is enabled
				 * @event
				 * @name enable_node.jstree
				 * @param {Object} node the enabled node
				 */
				this.trigger('enable_node', { 'node' : obj });
			},
			/**
			 * disables a node - so that it can not be selected
			 * @name disable_node(obj)
			 * @param {mixed} obj the node to disable
			 * @trigger disable_node.jstree
			 */
			disable_node : function (obj) {
				var t1, t2;
				if($.isArray(obj)) {
					obj = obj.slice();
					for(t1 = 0, t2 = obj.length; t1 < t2; t1++) {
						this.disable_node(obj[t1]);
					}
					return true;
				}
				obj = this.get_node(obj);
				if(!obj || obj.id === $.jstree.root) {
					return false;
				}
				obj.state.disabled = true;
				this.get_node(obj,true).children('.jstree-anchor').addClass('jstree-disabled').attr('aria-disabled', true);
				/**
				 * triggered when an node is disabled
				 * @event
				 * @name disable_node.jstree
				 * @param {Object} node the disabled node
				 */
				this.trigger('disable_node', { 'node' : obj });
			},
			/**
			 * determines if a node is hidden
			 * @name is_hidden(obj)
			 * @param {mixed} obj the node
			 */
			is_hidden : function (obj) {
				obj = this.get_node(obj);
				return obj.state.hidden === true;
			},
			/**
			 * hides a node - it is still in the structure but will not be visible
			 * @name hide_node(obj)
			 * @param {mixed} obj the node to hide
			 * @param {Boolean} redraw internal parameter controlling if redraw is called
			 * @trigger hide_node.jstree
			 */
			hide_node : function (obj, skip_redraw) {
				var t1, t2;
				if($.isArray(obj)) {
					obj = obj.slice();
					for(t1 = 0, t2 = obj.length; t1 < t2; t1++) {
						this.hide_node(obj[t1], true);
					}
					if (!skip_redraw) {
						this.redraw();
					}
					return true;
				}
				obj = this.get_node(obj);
				if(!obj || obj.id === $.jstree.root) {
					return false;
				}
				if(!obj.state.hidden) {
					obj.state.hidden = true;
					this._node_changed(obj.parent);
					if(!skip_redraw) {
						this.redraw();
					}
					/**
					 * triggered when an node is hidden
					 * @event
					 * @name hide_node.jstree
					 * @param {Object} node the hidden node
					 */
					this.trigger('hide_node', { 'node' : obj });
				}
			},
			/**
			 * shows a node
			 * @name show_node(obj)
			 * @param {mixed} obj the node to show
			 * @param {Boolean} skip_redraw internal parameter controlling if redraw is called
			 * @trigger show_node.jstree
			 */
			show_node : function (obj, skip_redraw) {
				var t1, t2;
				if($.isArray(obj)) {
					obj = obj.slice();
					for(t1 = 0, t2 = obj.length; t1 < t2; t1++) {
						this.show_node(obj[t1], true);
					}
					if (!skip_redraw) {
						this.redraw();
					}
					return true;
				}
				obj = this.get_node(obj);
				if(!obj || obj.id === $.jstree.root) {
					return false;
				}
				if(obj.state.hidden) {
					obj.state.hidden = false;
					this._node_changed(obj.parent);
					if(!skip_redraw) {
						this.redraw();
					}
					/**
					 * triggered when an node is shown
					 * @event
					 * @name show_node.jstree
					 * @param {Object} node the shown node
					 */
					this.trigger('show_node', { 'node' : obj });
				}
			},
			/**
			 * hides all nodes
			 * @name hide_all()
			 * @trigger hide_all.jstree
			 */
			hide_all : function (skip_redraw) {
				var i, m = this._model.data, ids = [];
				for(i in m) {
					if(m.hasOwnProperty(i) && i !== $.jstree.root && !m[i].state.hidden) {
						m[i].state.hidden = true;
						ids.push(i);
					}
				}
				this._model.force_full_redraw = true;
				if(!skip_redraw) {
					this.redraw();
				}
				/**
				 * triggered when all nodes are hidden
				 * @event
				 * @name hide_all.jstree
				 * @param {Array} nodes the IDs of all hidden nodes
				 */
				this.trigger('hide_all', { 'nodes' : ids });
				return ids;
			},
			/**
			 * shows all nodes
			 * @name show_all()
			 * @trigger show_all.jstree
			 */
			show_all : function (skip_redraw) {
				var i, m = this._model.data, ids = [];
				for(i in m) {
					if(m.hasOwnProperty(i) && i !== $.jstree.root && m[i].state.hidden) {
						m[i].state.hidden = false;
						ids.push(i);
					}
				}
				this._model.force_full_redraw = true;
				if(!skip_redraw) {
					this.redraw();
				}
				/**
				 * triggered when all nodes are shown
				 * @event
				 * @name show_all.jstree
				 * @param {Array} nodes the IDs of all shown nodes
				 */
				this.trigger('show_all', { 'nodes' : ids });
				return ids;
			},
			/**
			 * called when a node is selected by the user. Used internally.
			 * @private
			 * @name activate_node(obj, e)
			 * @param {mixed} obj the node
			 * @param {Object} e the related event
			 * @trigger activate_node.jstree, changed.jstree
			 */
			activate_node : function (obj, e) {
				if(this.is_disabled(obj)) {
					return false;
				}
				if(!e || typeof e !== 'object') {
					e = {};
				}
	
				// ensure last_clicked is still in the DOM, make it fresh (maybe it was moved?) and make sure it is still selected, if not - make last_clicked the last selected node
				this._data.core.last_clicked = this._data.core.last_clicked && this._data.core.last_clicked.id !== undefined ? this.get_node(this._data.core.last_clicked.id) : null;
				if(this._data.core.last_clicked && !this._data.core.last_clicked.state.selected) { this._data.core.last_clicked = null; }
				if(!this._data.core.last_clicked && this._data.core.selected.length) { this._data.core.last_clicked = this.get_node(this._data.core.selected[this._data.core.selected.length - 1]); }
	
				if(!this.settings.core.multiple || (!e.metaKey && !e.ctrlKey && !e.shiftKey) || (e.shiftKey && (!this._data.core.last_clicked || !this.get_parent(obj) || this.get_parent(obj) !== this._data.core.last_clicked.parent ) )) {
					if(!this.settings.core.multiple && (e.metaKey || e.ctrlKey || e.shiftKey) && this.is_selected(obj)) {
						this.deselect_node(obj, false, e);
					}
					else {
						this.deselect_all(true);
						this.select_node(obj, false, false, e);
						this._data.core.last_clicked = this.get_node(obj);
					}
				}
				else {
					if(e.shiftKey) {
						var o = this.get_node(obj).id,
							l = this._data.core.last_clicked.id,
							p = this.get_node(this._data.core.last_clicked.parent).children,
							c = false,
							i, j;
						for(i = 0, j = p.length; i < j; i += 1) {
							// separate IFs work whem o and l are the same
							if(p[i] === o) {
								c = !c;
							}
							if(p[i] === l) {
								c = !c;
							}
							if(!this.is_disabled(p[i]) && (c || p[i] === o || p[i] === l)) {
								if (!this.is_hidden(p[i])) {
									this.select_node(p[i], true, false, e);
								}
							}
							else {
								this.deselect_node(p[i], true, e);
							}
						}
						this.trigger('changed', { 'action' : 'select_node', 'node' : this.get_node(obj), 'selected' : this._data.core.selected, 'event' : e });
					}
					else {
						if(!this.is_selected(obj)) {
							this.select_node(obj, false, false, e);
						}
						else {
							this.deselect_node(obj, false, e);
						}
					}
				}
				/**
				 * triggered when an node is clicked or intercated with by the user
				 * @event
				 * @name activate_node.jstree
				 * @param {Object} node
				 * @param {Object} event the ooriginal event (if any) which triggered the call (may be an empty object)
				 */
				this.trigger('activate_node', { 'node' : this.get_node(obj), 'event' : e });
			},
			/**
			 * applies the hover state on a node, called when a node is hovered by the user. Used internally.
			 * @private
			 * @name hover_node(obj)
			 * @param {mixed} obj
			 * @trigger hover_node.jstree
			 */
			hover_node : function (obj) {
				obj = this.get_node(obj, true);
				if(!obj || !obj.length || obj.children('.jstree-hovered').length) {
					return false;
				}
				var o = this.element.find('.jstree-hovered'), t = this.element;
				if(o && o.length) { this.dehover_node(o); }
	
				obj.children('.jstree-anchor').addClass('jstree-hovered');
				/**
				 * triggered when an node is hovered
				 * @event
				 * @name hover_node.jstree
				 * @param {Object} node
				 */
				this.trigger('hover_node', { 'node' : this.get_node(obj) });
				setTimeout(function () { t.attr('aria-activedescendant', obj[0].id); }, 0);
			},
			/**
			 * removes the hover state from a nodecalled when a node is no longer hovered by the user. Used internally.
			 * @private
			 * @name dehover_node(obj)
			 * @param {mixed} obj
			 * @trigger dehover_node.jstree
			 */
			dehover_node : function (obj) {
				obj = this.get_node(obj, true);
				if(!obj || !obj.length || !obj.children('.jstree-hovered').length) {
					return false;
				}
				obj.children('.jstree-anchor').removeClass('jstree-hovered');
				/**
				 * triggered when an node is no longer hovered
				 * @event
				 * @name dehover_node.jstree
				 * @param {Object} node
				 */
				this.trigger('dehover_node', { 'node' : this.get_node(obj) });
			},
			/**
			 * select a node
			 * @name select_node(obj [, supress_event, prevent_open])
			 * @param {mixed} obj an array can be used to select multiple nodes
			 * @param {Boolean} supress_event if set to `true` the `changed.jstree` event won't be triggered
			 * @param {Boolean} prevent_open if set to `true` parents of the selected node won't be opened
			 * @trigger select_node.jstree, changed.jstree
			 */
			select_node : function (obj, supress_event, prevent_open, e) {
				var dom, t1, t2, th;
				if($.isArray(obj)) {
					obj = obj.slice();
					for(t1 = 0, t2 = obj.length; t1 < t2; t1++) {
						this.select_node(obj[t1], supress_event, prevent_open, e);
					}
					return true;
				}
				obj = this.get_node(obj);
				if(!obj || obj.id === $.jstree.root) {
					return false;
				}
				dom = this.get_node(obj, true);
				if(!obj.state.selected) {
					obj.state.selected = true;
					this._data.core.selected.push(obj.id);
					if(!prevent_open) {
						dom = this._open_to(obj);
					}
					if(dom && dom.length) {
						dom.attr('aria-selected', true).children('.jstree-anchor').addClass('jstree-clicked');
					}
					/**
					 * triggered when an node is selected
					 * @event
					 * @name select_node.jstree
					 * @param {Object} node
					 * @param {Array} selected the current selection
					 * @param {Object} event the event (if any) that triggered this select_node
					 */
					this.trigger('select_node', { 'node' : obj, 'selected' : this._data.core.selected, 'event' : e });
					if(!supress_event) {
						/**
						 * triggered when selection changes
						 * @event
						 * @name changed.jstree
						 * @param {Object} node
						 * @param {Object} action the action that caused the selection to change
						 * @param {Array} selected the current selection
						 * @param {Object} event the event (if any) that triggered this changed event
						 */
						this.trigger('changed', { 'action' : 'select_node', 'node' : obj, 'selected' : this._data.core.selected, 'event' : e });
					}
				}
			},
			/**
			 * deselect a node
			 * @name deselect_node(obj [, supress_event])
			 * @param {mixed} obj an array can be used to deselect multiple nodes
			 * @param {Boolean} supress_event if set to `true` the `changed.jstree` event won't be triggered
			 * @trigger deselect_node.jstree, changed.jstree
			 */
			deselect_node : function (obj, supress_event, e) {
				var t1, t2, dom;
				if($.isArray(obj)) {
					obj = obj.slice();
					for(t1 = 0, t2 = obj.length; t1 < t2; t1++) {
						this.deselect_node(obj[t1], supress_event, e);
					}
					return true;
				}
				obj = this.get_node(obj);
				if(!obj || obj.id === $.jstree.root) {
					return false;
				}
				dom = this.get_node(obj, true);
				if(obj.state.selected) {
					obj.state.selected = false;
					this._data.core.selected = $.vakata.array_remove_item(this._data.core.selected, obj.id);
					if(dom.length) {
						dom.attr('aria-selected', false).children('.jstree-anchor').removeClass('jstree-clicked');
					}
					/**
					 * triggered when an node is deselected
					 * @event
					 * @name deselect_node.jstree
					 * @param {Object} node
					 * @param {Array} selected the current selection
					 * @param {Object} event the event (if any) that triggered this deselect_node
					 */
					this.trigger('deselect_node', { 'node' : obj, 'selected' : this._data.core.selected, 'event' : e });
					if(!supress_event) {
						this.trigger('changed', { 'action' : 'deselect_node', 'node' : obj, 'selected' : this._data.core.selected, 'event' : e });
					}
				}
			},
			/**
			 * select all nodes in the tree
			 * @name select_all([supress_event])
			 * @param {Boolean} supress_event if set to `true` the `changed.jstree` event won't be triggered
			 * @trigger select_all.jstree, changed.jstree
			 */
			select_all : function (supress_event) {
				var tmp = this._data.core.selected.concat([]), i, j;
				this._data.core.selected = this._model.data[$.jstree.root].children_d.concat();
				for(i = 0, j = this._data.core.selected.length; i < j; i++) {
					if(this._model.data[this._data.core.selected[i]]) {
						this._model.data[this._data.core.selected[i]].state.selected = true;
					}
				}
				this.redraw(true);
				/**
				 * triggered when all nodes are selected
				 * @event
				 * @name select_all.jstree
				 * @param {Array} selected the current selection
				 */
				this.trigger('select_all', { 'selected' : this._data.core.selected });
				if(!supress_event) {
					this.trigger('changed', { 'action' : 'select_all', 'selected' : this._data.core.selected, 'old_selection' : tmp });
				}
			},
			/**
			 * deselect all selected nodes
			 * @name deselect_all([supress_event])
			 * @param {Boolean} supress_event if set to `true` the `changed.jstree` event won't be triggered
			 * @trigger deselect_all.jstree, changed.jstree
			 */
			deselect_all : function (supress_event) {
				var tmp = this._data.core.selected.concat([]), i, j;
				for(i = 0, j = this._data.core.selected.length; i < j; i++) {
					if(this._model.data[this._data.core.selected[i]]) {
						this._model.data[this._data.core.selected[i]].state.selected = false;
					}
				}
				this._data.core.selected = [];
				this.element.find('.jstree-clicked').removeClass('jstree-clicked').parent().attr('aria-selected', false);
				/**
				 * triggered when all nodes are deselected
				 * @event
				 * @name deselect_all.jstree
				 * @param {Object} node the previous selection
				 * @param {Array} selected the current selection
				 */
				this.trigger('deselect_all', { 'selected' : this._data.core.selected, 'node' : tmp });
				if(!supress_event) {
					this.trigger('changed', { 'action' : 'deselect_all', 'selected' : this._data.core.selected, 'old_selection' : tmp });
				}
			},
			/**
			 * checks if a node is selected
			 * @name is_selected(obj)
			 * @param  {mixed}  obj
			 * @return {Boolean}
			 */
			is_selected : function (obj) {
				obj = this.get_node(obj);
				if(!obj || obj.id === $.jstree.root) {
					return false;
				}
				return obj.state.selected;
			},
			/**
			 * get an array of all selected nodes
			 * @name get_selected([full])
			 * @param  {mixed}  full if set to `true` the returned array will consist of the full node objects, otherwise - only IDs will be returned
			 * @return {Array}
			 */
			get_selected : function (full) {
				return full ? $.map(this._data.core.selected, $.proxy(function (i) { return this.get_node(i); }, this)) : this._data.core.selected.slice();
			},
			/**
			 * get an array of all top level selected nodes (ignoring children of selected nodes)
			 * @name get_top_selected([full])
			 * @param  {mixed}  full if set to `true` the returned array will consist of the full node objects, otherwise - only IDs will be returned
			 * @return {Array}
			 */
			get_top_selected : function (full) {
				var tmp = this.get_selected(true),
					obj = {}, i, j, k, l;
				for(i = 0, j = tmp.length; i < j; i++) {
					obj[tmp[i].id] = tmp[i];
				}
				for(i = 0, j = tmp.length; i < j; i++) {
					for(k = 0, l = tmp[i].children_d.length; k < l; k++) {
						if(obj[tmp[i].children_d[k]]) {
							delete obj[tmp[i].children_d[k]];
						}
					}
				}
				tmp = [];
				for(i in obj) {
					if(obj.hasOwnProperty(i)) {
						tmp.push(i);
					}
				}
				return full ? $.map(tmp, $.proxy(function (i) { return this.get_node(i); }, this)) : tmp;
			},
			/**
			 * get an array of all bottom level selected nodes (ignoring selected parents)
			 * @name get_bottom_selected([full])
			 * @param  {mixed}  full if set to `true` the returned array will consist of the full node objects, otherwise - only IDs will be returned
			 * @return {Array}
			 */
			get_bottom_selected : function (full) {
				var tmp = this.get_selected(true),
					obj = [], i, j;
				for(i = 0, j = tmp.length; i < j; i++) {
					if(!tmp[i].children.length) {
						obj.push(tmp[i].id);
					}
				}
				return full ? $.map(obj, $.proxy(function (i) { return this.get_node(i); }, this)) : obj;
			},
			/**
			 * gets the current state of the tree so that it can be restored later with `set_state(state)`. Used internally.
			 * @name get_state()
			 * @private
			 * @return {Object}
			 */
			get_state : function () {
				var state	= {
					'core' : {
						'open' : [],
						'scroll' : {
							'left' : this.element.scrollLeft(),
							'top' : this.element.scrollTop()
						},
						/*!
						'themes' : {
							'name' : this.get_theme(),
							'icons' : this._data.core.themes.icons,
							'dots' : this._data.core.themes.dots
						},
						*/
						'selected' : []
					}
				}, i;
				for(i in this._model.data) {
					if(this._model.data.hasOwnProperty(i)) {
						if(i !== $.jstree.root) {
							if(this._model.data[i].state.opened) {
								state.core.open.push(i);
							}
							if(this._model.data[i].state.selected) {
								state.core.selected.push(i);
							}
						}
					}
				}
				return state;
			},
			/**
			 * sets the state of the tree. Used internally.
			 * @name set_state(state [, callback])
			 * @private
			 * @param {Object} state the state to restore. Keep in mind this object is passed by reference and jstree will modify it.
			 * @param {Function} callback an optional function to execute once the state is restored.
			 * @trigger set_state.jstree
			 */
			set_state : function (state, callback) {
				if(state) {
					if(state.core) {
						var res, n, t, _this, i;
						if(state.core.open) {
							if(!$.isArray(state.core.open) || !state.core.open.length) {
								delete state.core.open;
								this.set_state(state, callback);
							}
							else {
								this._load_nodes(state.core.open, function (nodes) {
									this.open_node(nodes, false, 0);
									delete state.core.open;
									this.set_state(state, callback);
								});
							}
							return false;
						}
						if(state.core.scroll) {
							if(state.core.scroll && state.core.scroll.left !== undefined) {
								this.element.scrollLeft(state.core.scroll.left);
							}
							if(state.core.scroll && state.core.scroll.top !== undefined) {
								this.element.scrollTop(state.core.scroll.top);
							}
							delete state.core.scroll;
							this.set_state(state, callback);
							return false;
						}
						if(state.core.selected) {
							_this = this;
							this.deselect_all();
							$.each(state.core.selected, function (i, v) {
								_this.select_node(v, false, true);
							});
							delete state.core.selected;
							this.set_state(state, callback);
							return false;
						}
						for(i in state) {
							if(state.hasOwnProperty(i) && i !== "core" && $.inArray(i, this.settings.plugins) === -1) {
								delete state[i];
							}
						}
						if($.isEmptyObject(state.core)) {
							delete state.core;
							this.set_state(state, callback);
							return false;
						}
					}
					if($.isEmptyObject(state)) {
						state = null;
						if(callback) { callback.call(this); }
						/**
						 * triggered when a `set_state` call completes
						 * @event
						 * @name set_state.jstree
						 */
						this.trigger('set_state');
						return false;
					}
					return true;
				}
				return false;
			},
			/**
			 * refreshes the tree - all nodes are reloaded with calls to `load_node`.
			 * @name refresh()
			 * @param {Boolean} skip_loading an option to skip showing the loading indicator
			 * @param {Mixed} forget_state if set to `true` state will not be reapplied, if set to a function (receiving the current state as argument) the result of that function will be used as state
			 * @trigger refresh.jstree
			 */
			refresh : function (skip_loading, forget_state) {
				this._data.core.state = forget_state === true ? {} : this.get_state();
				if(forget_state && $.isFunction(forget_state)) { this._data.core.state = forget_state.call(this, this._data.core.state); }
				this._cnt = 0;
				this._model.data = {};
				this._model.data[$.jstree.root] = {
					id : $.jstree.root,
					parent : null,
					parents : [],
					children : [],
					children_d : [],
					state : { loaded : false }
				};
				this._data.core.selected = [];
				this._data.core.last_clicked = null;
				this._data.core.focused = null;
	
				var c = this.get_container_ul()[0].className;
				if(!skip_loading) {
					this.element.html("<"+"ul class='"+c+"' role='group'><"+"li class='jstree-initial-node jstree-loading jstree-leaf jstree-last' role='treeitem' id='j"+this._id+"_loading'><i class='jstree-icon jstree-ocl'></i><"+"a class='jstree-anchor' href='#'><i class='jstree-icon jstree-themeicon-hidden'></i>" + this.get_string("Loading ...") + "</a></li></ul>");
					this.element.attr('aria-activedescendant','j'+this._id+'_loading');
				}
				this.load_node($.jstree.root, function (o, s) {
					if(s) {
						this.get_container_ul()[0].className = c;
						if(this._firstChild(this.get_container_ul()[0])) {
							this.element.attr('aria-activedescendant',this._firstChild(this.get_container_ul()[0]).id);
						}
						this.set_state($.extend(true, {}, this._data.core.state), function () {
							/**
							 * triggered when a `refresh` call completes
							 * @event
							 * @name refresh.jstree
							 */
							this.trigger('refresh');
						});
					}
					this._data.core.state = null;
				});
			},
			/**
			 * refreshes a node in the tree (reload its children) all opened nodes inside that node are reloaded with calls to `load_node`.
			 * @name refresh_node(obj)
			 * @param  {mixed} obj the node
			 * @trigger refresh_node.jstree
			 */
			refresh_node : function (obj) {
				obj = this.get_node(obj);
				if(!obj || obj.id === $.jstree.root) { return false; }
				var opened = [], to_load = [], s = this._data.core.selected.concat([]);
				to_load.push(obj.id);
				if(obj.state.opened === true) { opened.push(obj.id); }
				this.get_node(obj, true).find('.jstree-open').each(function() { to_load.push(this.id); opened.push(this.id); });
				this._load_nodes(to_load, $.proxy(function (nodes) {
					this.open_node(opened, false, 0);
					this.select_node(s);
					/**
					 * triggered when a node is refreshed
					 * @event
					 * @name refresh_node.jstree
					 * @param {Object} node - the refreshed node
					 * @param {Array} nodes - an array of the IDs of the nodes that were reloaded
					 */
					this.trigger('refresh_node', { 'node' : obj, 'nodes' : nodes });
				}, this), false, true);
			},
			/**
			 * set (change) the ID of a node
			 * @name set_id(obj, id)
			 * @param  {mixed} obj the node
			 * @param  {String} id the new ID
			 * @return {Boolean}
			 * @trigger set_id.jstree
			 */
			set_id : function (obj, id) {
				obj = this.get_node(obj);
				if(!obj || obj.id === $.jstree.root) { return false; }
				var i, j, m = this._model.data, old = obj.id;
				id = id.toString();
				// update parents (replace current ID with new one in children and children_d)
				m[obj.parent].children[$.inArray(obj.id, m[obj.parent].children)] = id;
				for(i = 0, j = obj.parents.length; i < j; i++) {
					m[obj.parents[i]].children_d[$.inArray(obj.id, m[obj.parents[i]].children_d)] = id;
				}
				// update children (replace current ID with new one in parent and parents)
				for(i = 0, j = obj.children.length; i < j; i++) {
					m[obj.children[i]].parent = id;
				}
				for(i = 0, j = obj.children_d.length; i < j; i++) {
					m[obj.children_d[i]].parents[$.inArray(obj.id, m[obj.children_d[i]].parents)] = id;
				}
				i = $.inArray(obj.id, this._data.core.selected);
				if(i !== -1) { this._data.core.selected[i] = id; }
				// update model and obj itself (obj.id, this._model.data[KEY])
				i = this.get_node(obj.id, true);
				if(i) {
					i.attr('id', id); //.children('.jstree-anchor').attr('id', id + '_anchor').end().attr('aria-labelledby', id + '_anchor');
					if(this.element.attr('aria-activedescendant') === obj.id) {
						this.element.attr('aria-activedescendant', id);
					}
				}
				delete m[obj.id];
				obj.id = id;
				obj.li_attr.id = id;
				m[id] = obj;
				/**
				 * triggered when a node id value is changed
				 * @event
				 * @name set_id.jstree
				 * @param {Object} node
				 * @param {String} old the old id
				 */
				this.trigger('set_id',{ "node" : obj, "new" : obj.id, "old" : old });
				return true;
			},
			/**
			 * get the text value of a node
			 * @name get_text(obj)
			 * @param  {mixed} obj the node
			 * @return {String}
			 */
			get_text : function (obj) {
				obj = this.get_node(obj);
				return (!obj || obj.id === $.jstree.root) ? false : obj.text;
			},
			/**
			 * set the text value of a node. Used internally, please use `rename_node(obj, val)`.
			 * @private
			 * @name set_text(obj, val)
			 * @param  {mixed} obj the node, you can pass an array to set the text on multiple nodes
			 * @param  {String} val the new text value
			 * @return {Boolean}
			 * @trigger set_text.jstree
			 */
			set_text : function (obj, val) {
				var t1, t2;
				if($.isArray(obj)) {
					obj = obj.slice();
					for(t1 = 0, t2 = obj.length; t1 < t2; t1++) {
						this.set_text(obj[t1], val);
					}
					return true;
				}
				obj = this.get_node(obj);
				if(!obj || obj.id === $.jstree.root) { return false; }
				obj.text = val;
				if(this.get_node(obj, true).length) {
					this.redraw_node(obj.id);
				}
				/**
				 * triggered when a node text value is changed
				 * @event
				 * @name set_text.jstree
				 * @param {Object} obj
				 * @param {String} text the new value
				 */
				this.trigger('set_text',{ "obj" : obj, "text" : val });
				return true;
			},
			/**
			 * gets a JSON representation of a node (or the whole tree)
			 * @name get_json([obj, options])
			 * @param  {mixed} obj
			 * @param  {Object} options
			 * @param  {Boolean} options.no_state do not return state information
			 * @param  {Boolean} options.no_id do not return ID
			 * @param  {Boolean} options.no_children do not include children
			 * @param  {Boolean} options.no_data do not include node data
			 * @param  {Boolean} options.no_li_attr do not include LI attributes
			 * @param  {Boolean} options.no_a_attr do not include A attributes
			 * @param  {Boolean} options.flat return flat JSON instead of nested
			 * @return {Object}
			 */
			get_json : function (obj, options, flat) {
				obj = this.get_node(obj || $.jstree.root);
				if(!obj) { return false; }
				if(options && options.flat && !flat) { flat = []; }
				var tmp = {
					'id' : obj.id,
					'text' : obj.text,
					'icon' : this.get_icon(obj),
					'li_attr' : $.extend(true, {}, obj.li_attr),
					'a_attr' : $.extend(true, {}, obj.a_attr),
					'state' : {},
					'data' : options && options.no_data ? false : $.extend(true, {}, obj.data)
					//( this.get_node(obj, true).length ? this.get_node(obj, true).data() : obj.data ),
				}, i, j;
				if(options && options.flat) {
					tmp.parent = obj.parent;
				}
				else {
					tmp.children = [];
				}
				if(!options || !options.no_state) {
					for(i in obj.state) {
						if(obj.state.hasOwnProperty(i)) {
							tmp.state[i] = obj.state[i];
						}
					}
				} else {
					delete tmp.state;
				}
				if(options && options.no_li_attr) {
					delete tmp.li_attr;
				}
				if(options && options.no_a_attr) {
					delete tmp.a_attr;
				}
				if(options && options.no_id) {
					delete tmp.id;
					if(tmp.li_attr && tmp.li_attr.id) {
						delete tmp.li_attr.id;
					}
					if(tmp.a_attr && tmp.a_attr.id) {
						delete tmp.a_attr.id;
					}
				}
				if(options && options.flat && obj.id !== $.jstree.root) {
					flat.push(tmp);
				}
				if(!options || !options.no_children) {
					for(i = 0, j = obj.children.length; i < j; i++) {
						if(options && options.flat) {
							this.get_json(obj.children[i], options, flat);
						}
						else {
							tmp.children.push(this.get_json(obj.children[i], options));
						}
					}
				}
				return options && options.flat ? flat : (obj.id === $.jstree.root ? tmp.children : tmp);
			},
			/**
			 * create a new node (do not confuse with load_node)
			 * @name create_node([par, node, pos, callback, is_loaded])
			 * @param  {mixed}   par       the parent node (to create a root node use either "#" (string) or `null`)
			 * @param  {mixed}   node      the data for the new node (a valid JSON object, or a simple string with the name)
			 * @param  {mixed}   pos       the index at which to insert the node, "first" and "last" are also supported, default is "last"
			 * @param  {Function} callback a function to be called once the node is created
			 * @param  {Boolean} is_loaded internal argument indicating if the parent node was succesfully loaded
			 * @return {String}            the ID of the newly create node
			 * @trigger model.jstree, create_node.jstree
			 */
			create_node : function (par, node, pos, callback, is_loaded) {
				if(par === null) { par = $.jstree.root; }
				par = this.get_node(par);
				if(!par) { return false; }
				pos = pos === undefined ? "last" : pos;
				if(!pos.toString().match(/^(before|after)$/) && !is_loaded && !this.is_loaded(par)) {
					return this.load_node(par, function () { this.create_node(par, node, pos, callback, true); });
				}
				if(!node) { node = { "text" : this.get_string('New node') }; }
				if(typeof node === "string") { node = { "text" : node }; }
				if(node.text === undefined) { node.text = this.get_string('New node'); }
				var tmp, dpc, i, j;
	
				if(par.id === $.jstree.root) {
					if(pos === "before") { pos = "first"; }
					if(pos === "after") { pos = "last"; }
				}
				switch(pos) {
					case "before":
						tmp = this.get_node(par.parent);
						pos = $.inArray(par.id, tmp.children);
						par = tmp;
						break;
					case "after" :
						tmp = this.get_node(par.parent);
						pos = $.inArray(par.id, tmp.children) + 1;
						par = tmp;
						break;
					case "inside":
					case "first":
						pos = 0;
						break;
					case "last":
						pos = par.children.length;
						break;
					default:
						if(!pos) { pos = 0; }
						break;
				}
				if(pos > par.children.length) { pos = par.children.length; }
				if(!node.id) { node.id = true; }
				if(!this.check("create_node", node, par, pos)) {
					this.settings.core.error.call(this, this._data.core.last_error);
					return false;
				}
				if(node.id === true) { delete node.id; }
				node = this._parse_model_from_json(node, par.id, par.parents.concat());
				if(!node) { return false; }
				tmp = this.get_node(node);
				dpc = [];
				dpc.push(node);
				dpc = dpc.concat(tmp.children_d);
				this.trigger('model', { "nodes" : dpc, "parent" : par.id });
	
				par.children_d = par.children_d.concat(dpc);
				for(i = 0, j = par.parents.length; i < j; i++) {
					this._model.data[par.parents[i]].children_d = this._model.data[par.parents[i]].children_d.concat(dpc);
				}
				node = tmp;
				tmp = [];
				for(i = 0, j = par.children.length; i < j; i++) {
					tmp[i >= pos ? i+1 : i] = par.children[i];
				}
				tmp[pos] = node.id;
				par.children = tmp;
	
				this.redraw_node(par, true);
				if(callback) { callback.call(this, this.get_node(node)); }
				/**
				 * triggered when a node is created
				 * @event
				 * @name create_node.jstree
				 * @param {Object} node
				 * @param {String} parent the parent's ID
				 * @param {Number} position the position of the new node among the parent's children
				 */
				this.trigger('create_node', { "node" : this.get_node(node), "parent" : par.id, "position" : pos });
				return node.id;
			},
			/**
			 * set the text value of a node
			 * @name rename_node(obj, val)
			 * @param  {mixed} obj the node, you can pass an array to rename multiple nodes to the same name
			 * @param  {String} val the new text value
			 * @return {Boolean}
			 * @trigger rename_node.jstree
			 */
			rename_node : function (obj, val) {
				var t1, t2, old;
				if($.isArray(obj)) {
					obj = obj.slice();
					for(t1 = 0, t2 = obj.length; t1 < t2; t1++) {
						this.rename_node(obj[t1], val);
					}
					return true;
				}
				obj = this.get_node(obj);
				if(!obj || obj.id === $.jstree.root) { return false; }
				old = obj.text;
				if(!this.check("rename_node", obj, this.get_parent(obj), val)) {
					this.settings.core.error.call(this, this._data.core.last_error);
					return false;
				}
				this.set_text(obj, val); // .apply(this, Array.prototype.slice.call(arguments))
				/**
				 * triggered when a node is renamed
				 * @event
				 * @name rename_node.jstree
				 * @param {Object} node
				 * @param {String} text the new value
				 * @param {String} old the old value
				 */
				this.trigger('rename_node', { "node" : obj, "text" : val, "old" : old });
				return true;
			},
			/**
			 * remove a node
			 * @name delete_node(obj)
			 * @param  {mixed} obj the node, you can pass an array to delete multiple nodes
			 * @return {Boolean}
			 * @trigger delete_node.jstree, changed.jstree
			 */
			delete_node : function (obj) {
				var t1, t2, par, pos, tmp, i, j, k, l, c, top, lft;
				if($.isArray(obj)) {
					obj = obj.slice();
					for(t1 = 0, t2 = obj.length; t1 < t2; t1++) {
						this.delete_node(obj[t1]);
					}
					return true;
				}
				obj = this.get_node(obj);
				if(!obj || obj.id === $.jstree.root) { return false; }
				par = this.get_node(obj.parent);
				pos = $.inArray(obj.id, par.children);
				c = false;
				if(!this.check("delete_node", obj, par, pos)) {
					this.settings.core.error.call(this, this._data.core.last_error);
					return false;
				}
				if(pos !== -1) {
					par.children = $.vakata.array_remove(par.children, pos);
				}
				tmp = obj.children_d.concat([]);
				tmp.push(obj.id);
				for(i = 0, j = obj.parents.length; i < j; i++) {
					this._model.data[obj.parents[i]].children_d = $.vakata.array_filter(this._model.data[obj.parents[i]].children_d, function (v) {
						return $.inArray(v, tmp) === -1;
					});
				}
				for(k = 0, l = tmp.length; k < l; k++) {
					if(this._model.data[tmp[k]].state.selected) {
						c = true;
						break;
					}
				}
				if (c) {
					this._data.core.selected = $.vakata.array_filter(this._data.core.selected, function (v) {
						return $.inArray(v, tmp) === -1;
					});
				}
				/**
				 * triggered when a node is deleted
				 * @event
				 * @name delete_node.jstree
				 * @param {Object} node
				 * @param {String} parent the parent's ID
				 */
				this.trigger('delete_node', { "node" : obj, "parent" : par.id });
				if(c) {
					this.trigger('changed', { 'action' : 'delete_node', 'node' : obj, 'selected' : this._data.core.selected, 'parent' : par.id });
				}
				for(k = 0, l = tmp.length; k < l; k++) {
					delete this._model.data[tmp[k]];
				}
				if($.inArray(this._data.core.focused, tmp) !== -1) {
					this._data.core.focused = null;
					top = this.element[0].scrollTop;
					lft = this.element[0].scrollLeft;
					if(par.id === $.jstree.root) {
						if (this._model.data[$.jstree.root].children[0]) {
							this.get_node(this._model.data[$.jstree.root].children[0], true).children('.jstree-anchor').focus();
						}
					}
					else {
						this.get_node(par, true).children('.jstree-anchor').focus();
					}
					this.element[0].scrollTop  = top;
					this.element[0].scrollLeft = lft;
				}
				this.redraw_node(par, true);
				return true;
			},
			/**
			 * check if an operation is premitted on the tree. Used internally.
			 * @private
			 * @name check(chk, obj, par, pos)
			 * @param  {String} chk the operation to check, can be "create_node", "rename_node", "delete_node", "copy_node" or "move_node"
			 * @param  {mixed} obj the node
			 * @param  {mixed} par the parent
			 * @param  {mixed} pos the position to insert at, or if "rename_node" - the new name
			 * @param  {mixed} more some various additional information, for example if a "move_node" operations is triggered by DND this will be the hovered node
			 * @return {Boolean}
			 */
			check : function (chk, obj, par, pos, more) {
				obj = obj && obj.id ? obj : this.get_node(obj);
				par = par && par.id ? par : this.get_node(par);
				var tmp = chk.match(/^move_node|copy_node|create_node$/i) ? par : obj,
					chc = this.settings.core.check_callback;
				if(chk === "move_node" || chk === "copy_node") {
					if((!more || !more.is_multi) && (obj.id === par.id || (chk === "move_node" && $.inArray(obj.id, par.children) === pos) || $.inArray(par.id, obj.children_d) !== -1)) {
						this._data.core.last_error = { 'error' : 'check', 'plugin' : 'core', 'id' : 'core_01', 'reason' : 'Moving parent inside child', 'data' : JSON.stringify({ 'chk' : chk, 'pos' : pos, 'obj' : obj && obj.id ? obj.id : false, 'par' : par && par.id ? par.id : false }) };
						return false;
					}
				}
				if(tmp && tmp.data) { tmp = tmp.data; }
				if(tmp && tmp.functions && (tmp.functions[chk] === false || tmp.functions[chk] === true)) {
					if(tmp.functions[chk] === false) {
						this._data.core.last_error = { 'error' : 'check', 'plugin' : 'core', 'id' : 'core_02', 'reason' : 'Node data prevents function: ' + chk, 'data' : JSON.stringify({ 'chk' : chk, 'pos' : pos, 'obj' : obj && obj.id ? obj.id : false, 'par' : par && par.id ? par.id : false }) };
					}
					return tmp.functions[chk];
				}
				if(chc === false || ($.isFunction(chc) && chc.call(this, chk, obj, par, pos, more) === false) || (chc && chc[chk] === false)) {
					this._data.core.last_error = { 'error' : 'check', 'plugin' : 'core', 'id' : 'core_03', 'reason' : 'User config for core.check_callback prevents function: ' + chk, 'data' : JSON.stringify({ 'chk' : chk, 'pos' : pos, 'obj' : obj && obj.id ? obj.id : false, 'par' : par && par.id ? par.id : false }) };
					return false;
				}
				return true;
			},
			/**
			 * get the last error
			 * @name last_error()
			 * @return {Object}
			 */
			last_error : function () {
				return this._data.core.last_error;
			},
			/**
			 * move a node to a new parent
			 * @name move_node(obj, par [, pos, callback, is_loaded])
			 * @param  {mixed} obj the node to move, pass an array to move multiple nodes
			 * @param  {mixed} par the new parent
			 * @param  {mixed} pos the position to insert at (besides integer values, "first" and "last" are supported, as well as "before" and "after"), defaults to integer `0`
			 * @param  {function} callback a function to call once the move is completed, receives 3 arguments - the node, the new parent and the position
			 * @param  {Boolean} is_loaded internal parameter indicating if the parent node has been loaded
			 * @param  {Boolean} skip_redraw internal parameter indicating if the tree should be redrawn
			 * @param  {Boolean} instance internal parameter indicating if the node comes from another instance
			 * @trigger move_node.jstree
			 */
			move_node : function (obj, par, pos, callback, is_loaded, skip_redraw, origin) {
				var t1, t2, old_par, old_pos, new_par, old_ins, is_multi, dpc, tmp, i, j, k, l, p;
	
				par = this.get_node(par);
				pos = pos === undefined ? 0 : pos;
				if(!par) { return false; }
				if(!pos.toString().match(/^(before|after)$/) && !is_loaded && !this.is_loaded(par)) {
					return this.load_node(par, function () { this.move_node(obj, par, pos, callback, true, false, origin); });
				}
	
				if($.isArray(obj)) {
					if(obj.length === 1) {
						obj = obj[0];
					}
					else {
						//obj = obj.slice();
						for(t1 = 0, t2 = obj.length; t1 < t2; t1++) {
							if((tmp = this.move_node(obj[t1], par, pos, callback, is_loaded, false, origin))) {
								par = tmp;
								pos = "after";
							}
						}
						this.redraw();
						return true;
					}
				}
				obj = obj && obj.id ? obj : this.get_node(obj);
	
				if(!obj || obj.id === $.jstree.root) { return false; }
	
				old_par = (obj.parent || $.jstree.root).toString();
				new_par = (!pos.toString().match(/^(before|after)$/) || par.id === $.jstree.root) ? par : this.get_node(par.parent);
				old_ins = origin ? origin : (this._model.data[obj.id] ? this : $.jstree.reference(obj.id));
				is_multi = !old_ins || !old_ins._id || (this._id !== old_ins._id);
				old_pos = old_ins && old_ins._id && old_par && old_ins._model.data[old_par] && old_ins._model.data[old_par].children ? $.inArray(obj.id, old_ins._model.data[old_par].children) : -1;
				if(old_ins && old_ins._id) {
					obj = old_ins._model.data[obj.id];
				}
	
				if(is_multi) {
					if((tmp = this.copy_node(obj, par, pos, callback, is_loaded, false, origin))) {
						if(old_ins) { old_ins.delete_node(obj); }
						return tmp;
					}
					return false;
				}
				//var m = this._model.data;
				if(par.id === $.jstree.root) {
					if(pos === "before") { pos = "first"; }
					if(pos === "after") { pos = "last"; }
				}
				switch(pos) {
					case "before":
						pos = $.inArray(par.id, new_par.children);
						break;
					case "after" :
						pos = $.inArray(par.id, new_par.children) + 1;
						break;
					case "inside":
					case "first":
						pos = 0;
						break;
					case "last":
						pos = new_par.children.length;
						break;
					default:
						if(!pos) { pos = 0; }
						break;
				}
				if(pos > new_par.children.length) { pos = new_par.children.length; }
				if(!this.check("move_node", obj, new_par, pos, { 'core' : true, 'origin' : origin, 'is_multi' : (old_ins && old_ins._id && old_ins._id !== this._id), 'is_foreign' : (!old_ins || !old_ins._id) })) {
					this.settings.core.error.call(this, this._data.core.last_error);
					return false;
				}
				if(obj.parent === new_par.id) {
					dpc = new_par.children.concat();
					tmp = $.inArray(obj.id, dpc);
					if(tmp !== -1) {
						dpc = $.vakata.array_remove(dpc, tmp);
						if(pos > tmp) { pos--; }
					}
					tmp = [];
					for(i = 0, j = dpc.length; i < j; i++) {
						tmp[i >= pos ? i+1 : i] = dpc[i];
					}
					tmp[pos] = obj.id;
					new_par.children = tmp;
					this._node_changed(new_par.id);
					this.redraw(new_par.id === $.jstree.root);
				}
				else {
					// clean old parent and up
					tmp = obj.children_d.concat();
					tmp.push(obj.id);
					for(i = 0, j = obj.parents.length; i < j; i++) {
						dpc = [];
						p = old_ins._model.data[obj.parents[i]].children_d;
						for(k = 0, l = p.length; k < l; k++) {
							if($.inArray(p[k], tmp) === -1) {
								dpc.push(p[k]);
							}
						}
						old_ins._model.data[obj.parents[i]].children_d = dpc;
					}
					old_ins._model.data[old_par].children = $.vakata.array_remove_item(old_ins._model.data[old_par].children, obj.id);
	
					// insert into new parent and up
					for(i = 0, j = new_par.parents.length; i < j; i++) {
						this._model.data[new_par.parents[i]].children_d = this._model.data[new_par.parents[i]].children_d.concat(tmp);
					}
					dpc = [];
					for(i = 0, j = new_par.children.length; i < j; i++) {
						dpc[i >= pos ? i+1 : i] = new_par.children[i];
					}
					dpc[pos] = obj.id;
					new_par.children = dpc;
					new_par.children_d.push(obj.id);
					new_par.children_d = new_par.children_d.concat(obj.children_d);
	
					// update object
					obj.parent = new_par.id;
					tmp = new_par.parents.concat();
					tmp.unshift(new_par.id);
					p = obj.parents.length;
					obj.parents = tmp;
	
					// update object children
					tmp = tmp.concat();
					for(i = 0, j = obj.children_d.length; i < j; i++) {
						this._model.data[obj.children_d[i]].parents = this._model.data[obj.children_d[i]].parents.slice(0,p*-1);
						Array.prototype.push.apply(this._model.data[obj.children_d[i]].parents, tmp);
					}
	
					if(old_par === $.jstree.root || new_par.id === $.jstree.root) {
						this._model.force_full_redraw = true;
					}
					if(!this._model.force_full_redraw) {
						this._node_changed(old_par);
						this._node_changed(new_par.id);
					}
					if(!skip_redraw) {
						this.redraw();
					}
				}
				if(callback) { callback.call(this, obj, new_par, pos); }
				/**
				 * triggered when a node is moved
				 * @event
				 * @name move_node.jstree
				 * @param {Object} node
				 * @param {String} parent the parent's ID
				 * @param {Number} position the position of the node among the parent's children
				 * @param {String} old_parent the old parent of the node
				 * @param {Number} old_position the old position of the node
				 * @param {Boolean} is_multi do the node and new parent belong to different instances
				 * @param {jsTree} old_instance the instance the node came from
				 * @param {jsTree} new_instance the instance of the new parent
				 */
				this.trigger('move_node', { "node" : obj, "parent" : new_par.id, "position" : pos, "old_parent" : old_par, "old_position" : old_pos, 'is_multi' : (old_ins && old_ins._id && old_ins._id !== this._id), 'is_foreign' : (!old_ins || !old_ins._id), 'old_instance' : old_ins, 'new_instance' : this });
				return obj.id;
			},
			/**
			 * copy a node to a new parent
			 * @name copy_node(obj, par [, pos, callback, is_loaded])
			 * @param  {mixed} obj the node to copy, pass an array to copy multiple nodes
			 * @param  {mixed} par the new parent
			 * @param  {mixed} pos the position to insert at (besides integer values, "first" and "last" are supported, as well as "before" and "after"), defaults to integer `0`
			 * @param  {function} callback a function to call once the move is completed, receives 3 arguments - the node, the new parent and the position
			 * @param  {Boolean} is_loaded internal parameter indicating if the parent node has been loaded
			 * @param  {Boolean} skip_redraw internal parameter indicating if the tree should be redrawn
			 * @param  {Boolean} instance internal parameter indicating if the node comes from another instance
			 * @trigger model.jstree copy_node.jstree
			 */
			copy_node : function (obj, par, pos, callback, is_loaded, skip_redraw, origin) {
				var t1, t2, dpc, tmp, i, j, node, old_par, new_par, old_ins, is_multi;
	
				par = this.get_node(par);
				pos = pos === undefined ? 0 : pos;
				if(!par) { return false; }
				if(!pos.toString().match(/^(before|after)$/) && !is_loaded && !this.is_loaded(par)) {
					return this.load_node(par, function () { this.copy_node(obj, par, pos, callback, true, false, origin); });
				}
	
				if($.isArray(obj)) {
					if(obj.length === 1) {
						obj = obj[0];
					}
					else {
						//obj = obj.slice();
						for(t1 = 0, t2 = obj.length; t1 < t2; t1++) {
							if((tmp = this.copy_node(obj[t1], par, pos, callback, is_loaded, true, origin))) {
								par = tmp;
								pos = "after";
							}
						}
						this.redraw();
						return true;
					}
				}
				obj = obj && obj.id ? obj : this.get_node(obj);
				if(!obj || obj.id === $.jstree.root) { return false; }
	
				old_par = (obj.parent || $.jstree.root).toString();
				new_par = (!pos.toString().match(/^(before|after)$/) || par.id === $.jstree.root) ? par : this.get_node(par.parent);
				old_ins = origin ? origin : (this._model.data[obj.id] ? this : $.jstree.reference(obj.id));
				is_multi = !old_ins || !old_ins._id || (this._id !== old_ins._id);
	
				if(old_ins && old_ins._id) {
					obj = old_ins._model.data[obj.id];
				}
	
				if(par.id === $.jstree.root) {
					if(pos === "before") { pos = "first"; }
					if(pos === "after") { pos = "last"; }
				}
				switch(pos) {
					case "before":
						pos = $.inArray(par.id, new_par.children);
						break;
					case "after" :
						pos = $.inArray(par.id, new_par.children) + 1;
						break;
					case "inside":
					case "first":
						pos = 0;
						break;
					case "last":
						pos = new_par.children.length;
						break;
					default:
						if(!pos) { pos = 0; }
						break;
				}
				if(pos > new_par.children.length) { pos = new_par.children.length; }
				if(!this.check("copy_node", obj, new_par, pos, { 'core' : true, 'origin' : origin, 'is_multi' : (old_ins && old_ins._id && old_ins._id !== this._id), 'is_foreign' : (!old_ins || !old_ins._id) })) {
					this.settings.core.error.call(this, this._data.core.last_error);
					return false;
				}
				node = old_ins ? old_ins.get_json(obj, { no_id : true, no_data : true, no_state : true }) : obj;
				if(!node) { return false; }
				if(node.id === true) { delete node.id; }
				node = this._parse_model_from_json(node, new_par.id, new_par.parents.concat());
				if(!node) { return false; }
				tmp = this.get_node(node);
				if(obj && obj.state && obj.state.loaded === false) { tmp.state.loaded = false; }
				dpc = [];
				dpc.push(node);
				dpc = dpc.concat(tmp.children_d);
				this.trigger('model', { "nodes" : dpc, "parent" : new_par.id });
	
				// insert into new parent and up
				for(i = 0, j = new_par.parents.length; i < j; i++) {
					this._model.data[new_par.parents[i]].children_d = this._model.data[new_par.parents[i]].children_d.concat(dpc);
				}
				dpc = [];
				for(i = 0, j = new_par.children.length; i < j; i++) {
					dpc[i >= pos ? i+1 : i] = new_par.children[i];
				}
				dpc[pos] = tmp.id;
				new_par.children = dpc;
				new_par.children_d.push(tmp.id);
				new_par.children_d = new_par.children_d.concat(tmp.children_d);
	
				if(new_par.id === $.jstree.root) {
					this._model.force_full_redraw = true;
				}
				if(!this._model.force_full_redraw) {
					this._node_changed(new_par.id);
				}
				if(!skip_redraw) {
					this.redraw(new_par.id === $.jstree.root);
				}
				if(callback) { callback.call(this, tmp, new_par, pos); }
				/**
				 * triggered when a node is copied
				 * @event
				 * @name copy_node.jstree
				 * @param {Object} node the copied node
				 * @param {Object} original the original node
				 * @param {String} parent the parent's ID
				 * @param {Number} position the position of the node among the parent's children
				 * @param {String} old_parent the old parent of the node
				 * @param {Number} old_position the position of the original node
				 * @param {Boolean} is_multi do the node and new parent belong to different instances
				 * @param {jsTree} old_instance the instance the node came from
				 * @param {jsTree} new_instance the instance of the new parent
				 */
				this.trigger('copy_node', { "node" : tmp, "original" : obj, "parent" : new_par.id, "position" : pos, "old_parent" : old_par, "old_position" : old_ins && old_ins._id && old_par && old_ins._model.data[old_par] && old_ins._model.data[old_par].children ? $.inArray(obj.id, old_ins._model.data[old_par].children) : -1,'is_multi' : (old_ins && old_ins._id && old_ins._id !== this._id), 'is_foreign' : (!old_ins || !old_ins._id), 'old_instance' : old_ins, 'new_instance' : this });
				return tmp.id;
			},
			/**
			 * cut a node (a later call to `paste(obj)` would move the node)
			 * @name cut(obj)
			 * @param  {mixed} obj multiple objects can be passed using an array
			 * @trigger cut.jstree
			 */
			cut : function (obj) {
				if(!obj) { obj = this._data.core.selected.concat(); }
				if(!$.isArray(obj)) { obj = [obj]; }
				if(!obj.length) { return false; }
				var tmp = [], o, t1, t2;
				for(t1 = 0, t2 = obj.length; t1 < t2; t1++) {
					o = this.get_node(obj[t1]);
					if(o && o.id && o.id !== $.jstree.root) { tmp.push(o); }
				}
				if(!tmp.length) { return false; }
				ccp_node = tmp;
				ccp_inst = this;
				ccp_mode = 'move_node';
				/**
				 * triggered when nodes are added to the buffer for moving
				 * @event
				 * @name cut.jstree
				 * @param {Array} node
				 */
				this.trigger('cut', { "node" : obj });
			},
			/**
			 * copy a node (a later call to `paste(obj)` would copy the node)
			 * @name copy(obj)
			 * @param  {mixed} obj multiple objects can be passed using an array
			 * @trigger copy.jstree
			 */
			copy : function (obj) {
				if(!obj) { obj = this._data.core.selected.concat(); }
				if(!$.isArray(obj)) { obj = [obj]; }
				if(!obj.length) { return false; }
				var tmp = [], o, t1, t2;
				for(t1 = 0, t2 = obj.length; t1 < t2; t1++) {
					o = this.get_node(obj[t1]);
					if(o && o.id && o.id !== $.jstree.root) { tmp.push(o); }
				}
				if(!tmp.length) { return false; }
				ccp_node = tmp;
				ccp_inst = this;
				ccp_mode = 'copy_node';
				/**
				 * triggered when nodes are added to the buffer for copying
				 * @event
				 * @name copy.jstree
				 * @param {Array} node
				 */
				this.trigger('copy', { "node" : obj });
			},
			/**
			 * get the current buffer (any nodes that are waiting for a paste operation)
			 * @name get_buffer()
			 * @return {Object} an object consisting of `mode` ("copy_node" or "move_node"), `node` (an array of objects) and `inst` (the instance)
			 */
			get_buffer : function () {
				return { 'mode' : ccp_mode, 'node' : ccp_node, 'inst' : ccp_inst };
			},
			/**
			 * check if there is something in the buffer to paste
			 * @name can_paste()
			 * @return {Boolean}
			 */
			can_paste : function () {
				return ccp_mode !== false && ccp_node !== false; // && ccp_inst._model.data[ccp_node];
			},
			/**
			 * copy or move the previously cut or copied nodes to a new parent
			 * @name paste(obj [, pos])
			 * @param  {mixed} obj the new parent
			 * @param  {mixed} pos the position to insert at (besides integer, "first" and "last" are supported), defaults to integer `0`
			 * @trigger paste.jstree
			 */
			paste : function (obj, pos) {
				obj = this.get_node(obj);
				if(!obj || !ccp_mode || !ccp_mode.match(/^(copy_node|move_node)$/) || !ccp_node) { return false; }
				if(this[ccp_mode](ccp_node, obj, pos, false, false, false, ccp_inst)) {
					/**
					 * triggered when paste is invoked
					 * @event
					 * @name paste.jstree
					 * @param {String} parent the ID of the receiving node
					 * @param {Array} node the nodes in the buffer
					 * @param {String} mode the performed operation - "copy_node" or "move_node"
					 */
					this.trigger('paste', { "parent" : obj.id, "node" : ccp_node, "mode" : ccp_mode });
				}
				ccp_node = false;
				ccp_mode = false;
				ccp_inst = false;
			},
			/**
			 * clear the buffer of previously copied or cut nodes
			 * @name clear_buffer()
			 * @trigger clear_buffer.jstree
			 */
			clear_buffer : function () {
				ccp_node = false;
				ccp_mode = false;
				ccp_inst = false;
				/**
				 * triggered when the copy / cut buffer is cleared
				 * @event
				 * @name clear_buffer.jstree
				 */
				this.trigger('clear_buffer');
			},
			/**
			 * put a node in edit mode (input field to rename the node)
			 * @name edit(obj [, default_text, callback])
			 * @param  {mixed} obj
			 * @param  {String} default_text the text to populate the input with (if omitted or set to a non-string value the node's text value is used)
			 * @param  {Function} callback a function to be called once the text box is blurred, it is called in the instance's scope and receives the node, a status parameter (true if the rename is successful, false otherwise) and a boolean indicating if the user cancelled the edit. You can access the node's title using .text
			 */
			edit : function (obj, default_text, callback) {
				var rtl, w, a, s, t, h1, h2, fn, tmp, cancel = false;
				obj = this.get_node(obj);
				if(!obj) { return false; }
				if(this.settings.core.check_callback === false) {
					this._data.core.last_error = { 'error' : 'check', 'plugin' : 'core', 'id' : 'core_07', 'reason' : 'Could not edit node because of check_callback' };
					this.settings.core.error.call(this, this._data.core.last_error);
					return false;
				}
				tmp = obj;
				default_text = typeof default_text === 'string' ? default_text : obj.text;
				this.set_text(obj, "");
				obj = this._open_to(obj);
				tmp.text = default_text;
	
				rtl = this._data.core.rtl;
				w  = this.element.width();
				this._data.core.focused = tmp.id;
				a  = obj.children('.jstree-anchor').focus();
				s  = $('<span>');
				/*!
				oi = obj.children("i:visible"),
				ai = a.children("i:visible"),
				w1 = oi.width() * oi.length,
				w2 = ai.width() * ai.length,
				*/
				t  = default_text;
				h1 = $("<"+"div />", { css : { "position" : "absolute", "top" : "-200px", "left" : (rtl ? "0px" : "-1000px"), "visibility" : "hidden" } }).appendTo("body");
				h2 = $("<"+"input />", {
							"value" : t,
							"class" : "jstree-rename-input",
							// "size" : t.length,
							"css" : {
								"padding" : "0",
								"border" : "1px solid silver",
								"box-sizing" : "border-box",
								"display" : "inline-block",
								"height" : (this._data.core.li_height) + "px",
								"lineHeight" : (this._data.core.li_height) + "px",
								"width" : "150px" // will be set a bit further down
							},
							"blur" : $.proxy(function (e) {
								e.stopImmediatePropagation();
								e.preventDefault();
								var i = s.children(".jstree-rename-input"),
									v = i.val(),
									f = this.settings.core.force_text,
									nv;
								if(v === "") { v = t; }
								h1.remove();
								s.replaceWith(a);
								s.remove();
								t = f ? t : $('<div></div>').append($.parseHTML(t)).html();
								this.set_text(obj, t);
								nv = !!this.rename_node(obj, f ? $('<div></div>').text(v).text() : $('<div></div>').append($.parseHTML(v)).html());
								if(!nv) {
									this.set_text(obj, t); // move this up? and fix #483
								}
								this._data.core.focused = tmp.id;
								setTimeout($.proxy(function () {
									var node = this.get_node(tmp.id, true);
									if(node.length) {
										this._data.core.focused = tmp.id;
										node.children('.jstree-anchor').focus();
									}
								}, this), 0);
								if(callback) {
									callback.call(this, tmp, nv, cancel);
								}
								h2 = null;
							}, this),
							"keydown" : function (e) {
								var key = e.which;
								if(key === 27) {
									cancel = true;
									this.value = t;
								}
								if(key === 27 || key === 13 || key === 37 || key === 38 || key === 39 || key === 40 || key === 32) {
									e.stopImmediatePropagation();
								}
								if(key === 27 || key === 13) {
									e.preventDefault();
									this.blur();
								}
							},
							"click" : function (e) { e.stopImmediatePropagation(); },
							"mousedown" : function (e) { e.stopImmediatePropagation(); },
							"keyup" : function (e) {
								h2.width(Math.min(h1.text("pW" + this.value).width(),w));
							},
							"keypress" : function(e) {
								if(e.which === 13) { return false; }
							}
						});
					fn = {
							fontFamily		: a.css('fontFamily')		|| '',
							fontSize		: a.css('fontSize')			|| '',
							fontWeight		: a.css('fontWeight')		|| '',
							fontStyle		: a.css('fontStyle')		|| '',
							fontStretch		: a.css('fontStretch')		|| '',
							fontVariant		: a.css('fontVariant')		|| '',
							letterSpacing	: a.css('letterSpacing')	|| '',
							wordSpacing		: a.css('wordSpacing')		|| ''
					};
				s.attr('class', a.attr('class')).append(a.contents().clone()).append(h2);
				a.replaceWith(s);
				h1.css(fn);
				h2.css(fn).width(Math.min(h1.text("pW" + h2[0].value).width(),w))[0].select();
				$(document).one('mousedown.jstree touchstart.jstree dnd_start.vakata', function (e) {
					if (h2 && e.target !== h2) {
						$(h2).blur();
					}
				});
			},
	
	
			/**
			 * changes the theme
			 * @name set_theme(theme_name [, theme_url])
			 * @param {String} theme_name the name of the new theme to apply
			 * @param {mixed} theme_url  the location of the CSS file for this theme. Omit or set to `false` if you manually included the file. Set to `true` to autoload from the `core.themes.dir` directory.
			 * @trigger set_theme.jstree
			 */
			set_theme : function (theme_name, theme_url) {
				if(!theme_name) { return false; }
				if(theme_url === true) {
					var dir = this.settings.core.themes.dir;
					if(!dir) { dir = $.jstree.path + '/themes'; }
					theme_url = dir + '/' + theme_name + '/style.css';
				}
				if(theme_url && $.inArray(theme_url, themes_loaded) === -1) {
					$('head').append('<'+'link rel="stylesheet" href="' + theme_url + '" type="text/css" />');
					themes_loaded.push(theme_url);
				}
				if(this._data.core.themes.name) {
					this.element.removeClass('jstree-' + this._data.core.themes.name);
				}
				this._data.core.themes.name = theme_name;
				this.element.addClass('jstree-' + theme_name);
				this.element[this.settings.core.themes.responsive ? 'addClass' : 'removeClass' ]('jstree-' + theme_name + '-responsive');
				/**
				 * triggered when a theme is set
				 * @event
				 * @name set_theme.jstree
				 * @param {String} theme the new theme
				 */
				this.trigger('set_theme', { 'theme' : theme_name });
			},
			/**
			 * gets the name of the currently applied theme name
			 * @name get_theme()
			 * @return {String}
			 */
			get_theme : function () { return this._data.core.themes.name; },
			/**
			 * changes the theme variant (if the theme has variants)
			 * @name set_theme_variant(variant_name)
			 * @param {String|Boolean} variant_name the variant to apply (if `false` is used the current variant is removed)
			 */
			set_theme_variant : function (variant_name) {
				if(this._data.core.themes.variant) {
					this.element.removeClass('jstree-' + this._data.core.themes.name + '-' + this._data.core.themes.variant);
				}
				this._data.core.themes.variant = variant_name;
				if(variant_name) {
					this.element.addClass('jstree-' + this._data.core.themes.name + '-' + this._data.core.themes.variant);
				}
			},
			/**
			 * gets the name of the currently applied theme variant
			 * @name get_theme()
			 * @return {String}
			 */
			get_theme_variant : function () { return this._data.core.themes.variant; },
			/**
			 * shows a striped background on the container (if the theme supports it)
			 * @name show_stripes()
			 */
			show_stripes : function () { this._data.core.themes.stripes = true; this.get_container_ul().addClass("jstree-striped"); },
			/**
			 * hides the striped background on the container
			 * @name hide_stripes()
			 */
			hide_stripes : function () { this._data.core.themes.stripes = false; this.get_container_ul().removeClass("jstree-striped"); },
			/**
			 * toggles the striped background on the container
			 * @name toggle_stripes()
			 */
			toggle_stripes : function () { if(this._data.core.themes.stripes) { this.hide_stripes(); } else { this.show_stripes(); } },
			/**
			 * shows the connecting dots (if the theme supports it)
			 * @name show_dots()
			 */
			show_dots : function () { this._data.core.themes.dots = true; this.get_container_ul().removeClass("jstree-no-dots"); },
			/**
			 * hides the connecting dots
			 * @name hide_dots()
			 */
			hide_dots : function () { this._data.core.themes.dots = false; this.get_container_ul().addClass("jstree-no-dots"); },
			/**
			 * toggles the connecting dots
			 * @name toggle_dots()
			 */
			toggle_dots : function () { if(this._data.core.themes.dots) { this.hide_dots(); } else { this.show_dots(); } },
			/**
			 * show the node icons
			 * @name show_icons()
			 */
			show_icons : function () { this._data.core.themes.icons = true; this.get_container_ul().removeClass("jstree-no-icons"); },
			/**
			 * hide the node icons
			 * @name hide_icons()
			 */
			hide_icons : function () { this._data.core.themes.icons = false; this.get_container_ul().addClass("jstree-no-icons"); },
			/**
			 * toggle the node icons
			 * @name toggle_icons()
			 */
			toggle_icons : function () { if(this._data.core.themes.icons) { this.hide_icons(); } else { this.show_icons(); } },
			/**
			 * set the node icon for a node
			 * @name set_icon(obj, icon)
			 * @param {mixed} obj
			 * @param {String} icon the new icon - can be a path to an icon or a className, if using an image that is in the current directory use a `./` prefix, otherwise it will be detected as a class
			 */
			set_icon : function (obj, icon) {
				var t1, t2, dom, old;
				if($.isArray(obj)) {
					obj = obj.slice();
					for(t1 = 0, t2 = obj.length; t1 < t2; t1++) {
						this.set_icon(obj[t1], icon);
					}
					return true;
				}
				obj = this.get_node(obj);
				if(!obj || obj.id === $.jstree.root) { return false; }
				old = obj.icon;
				obj.icon = icon === true || icon === null || icon === undefined || icon === '' ? true : icon;
				dom = this.get_node(obj, true).children(".jstree-anchor").children(".jstree-themeicon");
				if(icon === false) {
					this.hide_icon(obj);
				}
				else if(icon === true || icon === null || icon === undefined || icon === '') {
					dom.removeClass('jstree-themeicon-custom ' + old).css("background","").removeAttr("rel");
					if(old === false) { this.show_icon(obj); }
				}
				else if(icon.indexOf("/") === -1 && icon.indexOf(".") === -1) {
					dom.removeClass(old).css("background","");
					dom.addClass(icon + ' jstree-themeicon-custom').attr("rel",icon);
					if(old === false) { this.show_icon(obj); }
				}
				else {
					dom.removeClass(old).css("background","");
					dom.addClass('jstree-themeicon-custom').css("background", "url('" + icon + "') center center no-repeat").attr("rel",icon);
					if(old === false) { this.show_icon(obj); }
				}
				return true;
			},
			/**
			 * get the node icon for a node
			 * @name get_icon(obj)
			 * @param {mixed} obj
			 * @return {String}
			 */
			get_icon : function (obj) {
				obj = this.get_node(obj);
				return (!obj || obj.id === $.jstree.root) ? false : obj.icon;
			},
			/**
			 * hide the icon on an individual node
			 * @name hide_icon(obj)
			 * @param {mixed} obj
			 */
			hide_icon : function (obj) {
				var t1, t2;
				if($.isArray(obj)) {
					obj = obj.slice();
					for(t1 = 0, t2 = obj.length; t1 < t2; t1++) {
						this.hide_icon(obj[t1]);
					}
					return true;
				}
				obj = this.get_node(obj);
				if(!obj || obj === $.jstree.root) { return false; }
				obj.icon = false;
				this.get_node(obj, true).children(".jstree-anchor").children(".jstree-themeicon").addClass('jstree-themeicon-hidden');
				return true;
			},
			/**
			 * show the icon on an individual node
			 * @name show_icon(obj)
			 * @param {mixed} obj
			 */
			show_icon : function (obj) {
				var t1, t2, dom;
				if($.isArray(obj)) {
					obj = obj.slice();
					for(t1 = 0, t2 = obj.length; t1 < t2; t1++) {
						this.show_icon(obj[t1]);
					}
					return true;
				}
				obj = this.get_node(obj);
				if(!obj || obj === $.jstree.root) { return false; }
				dom = this.get_node(obj, true);
				obj.icon = dom.length ? dom.children(".jstree-anchor").children(".jstree-themeicon").attr('rel') : true;
				if(!obj.icon) { obj.icon = true; }
				dom.children(".jstree-anchor").children(".jstree-themeicon").removeClass('jstree-themeicon-hidden');
				return true;
			}
		};
	
		// helpers
		$.vakata = {};
		// collect attributes
		$.vakata.attributes = function(node, with_values) {
			node = $(node)[0];
			var attr = with_values ? {} : [];
			if(node && node.attributes) {
				$.each(node.attributes, function (i, v) {
					if($.inArray(v.name.toLowerCase(),['style','contenteditable','hasfocus','tabindex']) !== -1) { return; }
					if(v.value !== null && $.trim(v.value) !== '') {
						if(with_values) { attr[v.name] = v.value; }
						else { attr.push(v.name); }
					}
				});
			}
			return attr;
		};
		$.vakata.array_unique = function(array) {
			var a = [], i, j, l, o = {};
			for(i = 0, l = array.length; i < l; i++) {
				if(o[array[i]] === undefined) {
					a.push(array[i]);
					o[array[i]] = true;
				}
			}
			return a;
		};
		// remove item from array
		$.vakata.array_remove = function(array, from) {
			array.splice(from, 1);
			return array;
			//var rest = array.slice((to || from) + 1 || array.length);
			//array.length = from < 0 ? array.length + from : from;
			//array.push.apply(array, rest);
			//return array;
		};
		// remove item from array
		$.vakata.array_remove_item = function(array, item) {
			var tmp = $.inArray(item, array);
			return tmp !== -1 ? $.vakata.array_remove(array, tmp) : array;
		};
		$.vakata.array_filter = function(c,a,b,d,e) {
			if (c.filter) {
				return c.filter(a, b);
			}
			d=[];
			for (e in c) {
				if (~~e+''===e+'' && e>=0 && a.call(b,c[e],+e,c)) {
					d.push(c[e]);
				}
			}
			return d;
		};
	
	
	/**
	 * ### Changed plugin
	 *
	 * This plugin adds more information to the `changed.jstree` event. The new data is contained in the `changed` event data property, and contains a lists of `selected` and `deselected` nodes.
	 */
	
		$.jstree.plugins.changed = function (options, parent) {
			var last = [];
			this.trigger = function (ev, data) {
				var i, j;
				if(!data) {
					data = {};
				}
				if(ev.replace('.jstree','') === 'changed') {
					data.changed = { selected : [], deselected : [] };
					var tmp = {};
					for(i = 0, j = last.length; i < j; i++) {
						tmp[last[i]] = 1;
					}
					for(i = 0, j = data.selected.length; i < j; i++) {
						if(!tmp[data.selected[i]]) {
							data.changed.selected.push(data.selected[i]);
						}
						else {
							tmp[data.selected[i]] = 2;
						}
					}
					for(i = 0, j = last.length; i < j; i++) {
						if(tmp[last[i]] === 1) {
							data.changed.deselected.push(last[i]);
						}
					}
					last = data.selected.slice();
				}
				/**
				 * triggered when selection changes (the "changed" plugin enhances the original event with more data)
				 * @event
				 * @name changed.jstree
				 * @param {Object} node
				 * @param {Object} action the action that caused the selection to change
				 * @param {Array} selected the current selection
				 * @param {Object} changed an object containing two properties `selected` and `deselected` - both arrays of node IDs, which were selected or deselected since the last changed event
				 * @param {Object} event the event (if any) that triggered this changed event
				 * @plugin changed
				 */
				parent.trigger.call(this, ev, data);
			};
			this.refresh = function (skip_loading, forget_state) {
				last = [];
				return parent.refresh.apply(this, arguments);
			};
		};
	
	/**
	 * ### Checkbox plugin
	 *
	 * This plugin renders checkbox icons in front of each node, making multiple selection much easier.
	 * It also supports tri-state behavior, meaning that if a node has a few of its children checked it will be rendered as undetermined, and state will be propagated up.
	 */
	
		var _i = document.createElement('I');
		_i.className = 'jstree-icon jstree-checkbox';
		_i.setAttribute('role', 'presentation');
		/**
		 * stores all defaults for the checkbox plugin
		 * @name $.jstree.defaults.checkbox
		 * @plugin checkbox
		 */
		$.jstree.defaults.checkbox = {
			/**
			 * a boolean indicating if checkboxes should be visible (can be changed at a later time using `show_checkboxes()` and `hide_checkboxes`). Defaults to `true`.
			 * @name $.jstree.defaults.checkbox.visible
			 * @plugin checkbox
			 */
			visible				: true,
			/**
			 * a boolean indicating if checkboxes should cascade down and have an undetermined state. Defaults to `true`.
			 * @name $.jstree.defaults.checkbox.three_state
			 * @plugin checkbox
			 */
			three_state			: true,
			/**
			 * a boolean indicating if clicking anywhere on the node should act as clicking on the checkbox. Defaults to `true`.
			 * @name $.jstree.defaults.checkbox.whole_node
			 * @plugin checkbox
			 */
			whole_node			: true,
			/**
			 * a boolean indicating if the selected style of a node should be kept, or removed. Defaults to `true`.
			 * @name $.jstree.defaults.checkbox.keep_selected_style
			 * @plugin checkbox
			 */
			keep_selected_style	: true,
			/**
			 * This setting controls how cascading and undetermined nodes are applied.
			 * If 'up' is in the string - cascading up is enabled, if 'down' is in the string - cascading down is enabled, if 'undetermined' is in the string - undetermined nodes will be used.
			 * If `three_state` is set to `true` this setting is automatically set to 'up+down+undetermined'. Defaults to ''.
			 * @name $.jstree.defaults.checkbox.cascade
			 * @plugin checkbox
			 */
			cascade				: '',
			/**
			 * This setting controls if checkbox are bound to the general tree selection or to an internal array maintained by the checkbox plugin. Defaults to `true`, only set to `false` if you know exactly what you are doing.
			 * @name $.jstree.defaults.checkbox.tie_selection
			 * @plugin checkbox
			 */
			tie_selection		: true
		};
		$.jstree.plugins.checkbox = function (options, parent) {
			this.bind = function () {
				parent.bind.call(this);
				this._data.checkbox.uto = false;
				this._data.checkbox.selected = [];
				if(this.settings.checkbox.three_state) {
					this.settings.checkbox.cascade = 'up+down+undetermined';
				}
				this.element
					.on("init.jstree", $.proxy(function () {
							this._data.checkbox.visible = this.settings.checkbox.visible;
							if(!this.settings.checkbox.keep_selected_style) {
								this.element.addClass('jstree-checkbox-no-clicked');
							}
							if(this.settings.checkbox.tie_selection) {
								this.element.addClass('jstree-checkbox-selection');
							}
						}, this))
					.on("loading.jstree", $.proxy(function () {
							this[ this._data.checkbox.visible ? 'show_checkboxes' : 'hide_checkboxes' ]();
						}, this));
				if(this.settings.checkbox.cascade.indexOf('undetermined') !== -1) {
					this.element
						.on('changed.jstree uncheck_node.jstree check_node.jstree uncheck_all.jstree check_all.jstree move_node.jstree copy_node.jstree redraw.jstree open_node.jstree', $.proxy(function () {
								// only if undetermined is in setting
								if(this._data.checkbox.uto) { clearTimeout(this._data.checkbox.uto); }
								this._data.checkbox.uto = setTimeout($.proxy(this._undetermined, this), 50);
							}, this));
				}
				if(!this.settings.checkbox.tie_selection) {
					this.element
						.on('model.jstree', $.proxy(function (e, data) {
							var m = this._model.data,
								p = m[data.parent],
								dpc = data.nodes,
								i, j;
							for(i = 0, j = dpc.length; i < j; i++) {
								m[dpc[i]].state.checked = m[dpc[i]].state.checked || (m[dpc[i]].original && m[dpc[i]].original.state && m[dpc[i]].original.state.checked);
								if(m[dpc[i]].state.checked) {
									this._data.checkbox.selected.push(dpc[i]);
								}
							}
						}, this));
				}
				if(this.settings.checkbox.cascade.indexOf('up') !== -1 || this.settings.checkbox.cascade.indexOf('down') !== -1) {
					this.element
						.on('model.jstree', $.proxy(function (e, data) {
								var m = this._model.data,
									p = m[data.parent],
									dpc = data.nodes,
									chd = [],
									c, i, j, k, l, tmp, s = this.settings.checkbox.cascade, t = this.settings.checkbox.tie_selection;
	
								if(s.indexOf('down') !== -1) {
									// apply down
									if(p.state[ t ? 'selected' : 'checked' ]) {
										for(i = 0, j = dpc.length; i < j; i++) {
											m[dpc[i]].state[ t ? 'selected' : 'checked' ] = true;
										}
										this._data[ t ? 'core' : 'checkbox' ].selected = this._data[ t ? 'core' : 'checkbox' ].selected.concat(dpc);
									}
									else {
										for(i = 0, j = dpc.length; i < j; i++) {
											if(m[dpc[i]].state[ t ? 'selected' : 'checked' ]) {
												for(k = 0, l = m[dpc[i]].children_d.length; k < l; k++) {
													m[m[dpc[i]].children_d[k]].state[ t ? 'selected' : 'checked' ] = true;
												}
												this._data[ t ? 'core' : 'checkbox' ].selected = this._data[ t ? 'core' : 'checkbox' ].selected.concat(m[dpc[i]].children_d);
											}
										}
									}
								}
	
								if(s.indexOf('up') !== -1) {
									// apply up
									for(i = 0, j = p.children_d.length; i < j; i++) {
										if(!m[p.children_d[i]].children.length) {
											chd.push(m[p.children_d[i]].parent);
										}
									}
									chd = $.vakata.array_unique(chd);
									for(k = 0, l = chd.length; k < l; k++) {
										p = m[chd[k]];
										while(p && p.id !== $.jstree.root) {
											c = 0;
											for(i = 0, j = p.children.length; i < j; i++) {
												c += m[p.children[i]].state[ t ? 'selected' : 'checked' ];
											}
											if(c === j) {
												p.state[ t ? 'selected' : 'checked' ] = true;
												this._data[ t ? 'core' : 'checkbox' ].selected.push(p.id);
												tmp = this.get_node(p, true);
												if(tmp && tmp.length) {
													tmp.attr('aria-selected', true).children('.jstree-anchor').addClass( t ? 'jstree-clicked' : 'jstree-checked');
												}
											}
											else {
												break;
											}
											p = this.get_node(p.parent);
										}
									}
								}
	
								this._data[ t ? 'core' : 'checkbox' ].selected = $.vakata.array_unique(this._data[ t ? 'core' : 'checkbox' ].selected);
							}, this))
						.on(this.settings.checkbox.tie_selection ? 'select_node.jstree' : 'check_node.jstree', $.proxy(function (e, data) {
								var obj = data.node,
									m = this._model.data,
									par = this.get_node(obj.parent),
									dom = this.get_node(obj, true),
									i, j, c, tmp, s = this.settings.checkbox.cascade, t = this.settings.checkbox.tie_selection,
									sel = {}, cur = this._data[ t ? 'core' : 'checkbox' ].selected;
	
								for (i = 0, j = cur.length; i < j; i++) {
									sel[cur[i]] = true;
								}
								// apply down
								if(s.indexOf('down') !== -1) {
									//this._data[ t ? 'core' : 'checkbox' ].selected = $.vakata.array_unique(this._data[ t ? 'core' : 'checkbox' ].selected.concat(obj.children_d));
									for(i = 0, j = obj.children_d.length; i < j; i++) {
										sel[obj.children_d[i]] = true;
										tmp = m[obj.children_d[i]];
										tmp.state[ t ? 'selected' : 'checked' ] = true;
										if(tmp && tmp.original && tmp.original.state && tmp.original.state.undetermined) {
											tmp.original.state.undetermined = false;
										}
									}
								}
	
								// apply up
								if(s.indexOf('up') !== -1) {
									while(par && par.id !== $.jstree.root) {
										c = 0;
										for(i = 0, j = par.children.length; i < j; i++) {
											c += m[par.children[i]].state[ t ? 'selected' : 'checked' ];
										}
										if(c === j) {
											par.state[ t ? 'selected' : 'checked' ] = true;
											sel[par.id] = true;
											//this._data[ t ? 'core' : 'checkbox' ].selected.push(par.id);
											tmp = this.get_node(par, true);
											if(tmp && tmp.length) {
												tmp.attr('aria-selected', true).children('.jstree-anchor').addClass(t ? 'jstree-clicked' : 'jstree-checked');
											}
										}
										else {
											break;
										}
										par = this.get_node(par.parent);
									}
								}
	
								cur = [];
								for (i in sel) {
									if (sel.hasOwnProperty(i)) {
										cur.push(i);
									}
								}
								this._data[ t ? 'core' : 'checkbox' ].selected = cur;
	
								// apply down (process .children separately?)
								if(s.indexOf('down') !== -1 && dom.length) {
									dom.find('.jstree-anchor').addClass(t ? 'jstree-clicked' : 'jstree-checked').parent().attr('aria-selected', true);
								}
							}, this))
						.on(this.settings.checkbox.tie_selection ? 'deselect_all.jstree' : 'uncheck_all.jstree', $.proxy(function (e, data) {
								var obj = this.get_node($.jstree.root),
									m = this._model.data,
									i, j, tmp;
								for(i = 0, j = obj.children_d.length; i < j; i++) {
									tmp = m[obj.children_d[i]];
									if(tmp && tmp.original && tmp.original.state && tmp.original.state.undetermined) {
										tmp.original.state.undetermined = false;
									}
								}
							}, this))
						.on(this.settings.checkbox.tie_selection ? 'deselect_node.jstree' : 'uncheck_node.jstree', $.proxy(function (e, data) {
								var obj = data.node,
									dom = this.get_node(obj, true),
									i, j, tmp, s = this.settings.checkbox.cascade, t = this.settings.checkbox.tie_selection,
									cur = this._data[ t ? 'core' : 'checkbox' ].selected, sel = {};
								if(obj && obj.original && obj.original.state && obj.original.state.undetermined) {
									obj.original.state.undetermined = false;
								}
	
								// apply down
								if(s.indexOf('down') !== -1) {
									for(i = 0, j = obj.children_d.length; i < j; i++) {
										tmp = this._model.data[obj.children_d[i]];
										tmp.state[ t ? 'selected' : 'checked' ] = false;
										if(tmp && tmp.original && tmp.original.state && tmp.original.state.undetermined) {
											tmp.original.state.undetermined = false;
										}
									}
								}
	
								// apply up
								if(s.indexOf('up') !== -1) {
									for(i = 0, j = obj.parents.length; i < j; i++) {
										tmp = this._model.data[obj.parents[i]];
										tmp.state[ t ? 'selected' : 'checked' ] = false;
										if(tmp && tmp.original && tmp.original.state && tmp.original.state.undetermined) {
											tmp.original.state.undetermined = false;
										}
										tmp = this.get_node(obj.parents[i], true);
										if(tmp && tmp.length) {
											tmp.attr('aria-selected', false).children('.jstree-anchor').removeClass(t ? 'jstree-clicked' : 'jstree-checked');
										}
									}
								}
								sel = {};
								for(i = 0, j = cur.length; i < j; i++) {
									// apply down + apply up
									if(
										(s.indexOf('down') === -1 || $.inArray(cur[i], obj.children_d) === -1) &&
										(s.indexOf('up') === -1 || $.inArray(cur[i], obj.parents) === -1)
									) {
										sel[cur[i]] = true;
									}
								}
								cur = [];
								for (i in sel) {
									if (sel.hasOwnProperty(i)) {
										cur.push(i);
									}
								}
								this._data[ t ? 'core' : 'checkbox' ].selected = cur;
								
								// apply down (process .children separately?)
								if(s.indexOf('down') !== -1 && dom.length) {
									dom.find('.jstree-anchor').removeClass(t ? 'jstree-clicked' : 'jstree-checked').parent().attr('aria-selected', false);
								}
							}, this));
				}
				if(this.settings.checkbox.cascade.indexOf('up') !== -1) {
					this.element
						.on('delete_node.jstree', $.proxy(function (e, data) {
								// apply up (whole handler)
								var p = this.get_node(data.parent),
									m = this._model.data,
									i, j, c, tmp, t = this.settings.checkbox.tie_selection;
								while(p && p.id !== $.jstree.root && !p.state[ t ? 'selected' : 'checked' ]) {
									c = 0;
									for(i = 0, j = p.children.length; i < j; i++) {
										c += m[p.children[i]].state[ t ? 'selected' : 'checked' ];
									}
									if(j > 0 && c === j) {
										p.state[ t ? 'selected' : 'checked' ] = true;
										this._data[ t ? 'core' : 'checkbox' ].selected.push(p.id);
										tmp = this.get_node(p, true);
										if(tmp && tmp.length) {
											tmp.attr('aria-selected', true).children('.jstree-anchor').addClass(t ? 'jstree-clicked' : 'jstree-checked');
										}
									}
									else {
										break;
									}
									p = this.get_node(p.parent);
								}
							}, this))
						.on('move_node.jstree', $.proxy(function (e, data) {
								// apply up (whole handler)
								var is_multi = data.is_multi,
									old_par = data.old_parent,
									new_par = this.get_node(data.parent),
									m = this._model.data,
									p, c, i, j, tmp, t = this.settings.checkbox.tie_selection;
								if(!is_multi) {
									p = this.get_node(old_par);
									while(p && p.id !== $.jstree.root && !p.state[ t ? 'selected' : 'checked' ]) {
										c = 0;
										for(i = 0, j = p.children.length; i < j; i++) {
											c += m[p.children[i]].state[ t ? 'selected' : 'checked' ];
										}
										if(j > 0 && c === j) {
											p.state[ t ? 'selected' : 'checked' ] = true;
											this._data[ t ? 'core' : 'checkbox' ].selected.push(p.id);
											tmp = this.get_node(p, true);
											if(tmp && tmp.length) {
												tmp.attr('aria-selected', true).children('.jstree-anchor').addClass(t ? 'jstree-clicked' : 'jstree-checked');
											}
										}
										else {
											break;
										}
										p = this.get_node(p.parent);
									}
								}
								p = new_par;
								while(p && p.id !== $.jstree.root) {
									c = 0;
									for(i = 0, j = p.children.length; i < j; i++) {
										c += m[p.children[i]].state[ t ? 'selected' : 'checked' ];
									}
									if(c === j) {
										if(!p.state[ t ? 'selected' : 'checked' ]) {
											p.state[ t ? 'selected' : 'checked' ] = true;
											this._data[ t ? 'core' : 'checkbox' ].selected.push(p.id);
											tmp = this.get_node(p, true);
											if(tmp && tmp.length) {
												tmp.attr('aria-selected', true).children('.jstree-anchor').addClass(t ? 'jstree-clicked' : 'jstree-checked');
											}
										}
									}
									else {
										if(p.state[ t ? 'selected' : 'checked' ]) {
											p.state[ t ? 'selected' : 'checked' ] = false;
											this._data[ t ? 'core' : 'checkbox' ].selected = $.vakata.array_remove_item(this._data[ t ? 'core' : 'checkbox' ].selected, p.id);
											tmp = this.get_node(p, true);
											if(tmp && tmp.length) {
												tmp.attr('aria-selected', false).children('.jstree-anchor').removeClass(t ? 'jstree-clicked' : 'jstree-checked');
											}
										}
										else {
											break;
										}
									}
									p = this.get_node(p.parent);
								}
							}, this));
				}
			};
			/**
			 * set the undetermined state where and if necessary. Used internally.
			 * @private
			 * @name _undetermined()
			 * @plugin checkbox
			 */
			this._undetermined = function () {
				if(this.element === null) { return; }
				var i, j, k, l, o = {}, m = this._model.data, t = this.settings.checkbox.tie_selection, s = this._data[ t ? 'core' : 'checkbox' ].selected, p = [], tt = this;
				for(i = 0, j = s.length; i < j; i++) {
					if(m[s[i]] && m[s[i]].parents) {
						for(k = 0, l = m[s[i]].parents.length; k < l; k++) {
							if(o[m[s[i]].parents[k]] !== undefined) {
								break;
							}
							if(m[s[i]].parents[k] !== $.jstree.root) {
								o[m[s[i]].parents[k]] = true;
								p.push(m[s[i]].parents[k]);
							}
						}
					}
				}
				// attempt for server side undetermined state
				this.element.find('.jstree-closed').not(':has(.jstree-children)')
					.each(function () {
						var tmp = tt.get_node(this), tmp2;
						if(!tmp.state.loaded) {
							if(tmp.original && tmp.original.state && tmp.original.state.undetermined && tmp.original.state.undetermined === true) {
								if(o[tmp.id] === undefined && tmp.id !== $.jstree.root) {
									o[tmp.id] = true;
									p.push(tmp.id);
								}
								for(k = 0, l = tmp.parents.length; k < l; k++) {
									if(o[tmp.parents[k]] === undefined && tmp.parents[k] !== $.jstree.root) {
										o[tmp.parents[k]] = true;
										p.push(tmp.parents[k]);
									}
								}
							}
						}
						else {
							for(i = 0, j = tmp.children_d.length; i < j; i++) {
								tmp2 = m[tmp.children_d[i]];
								if(!tmp2.state.loaded && tmp2.original && tmp2.original.state && tmp2.original.state.undetermined && tmp2.original.state.undetermined === true) {
									if(o[tmp2.id] === undefined && tmp2.id !== $.jstree.root) {
										o[tmp2.id] = true;
										p.push(tmp2.id);
									}
									for(k = 0, l = tmp2.parents.length; k < l; k++) {
										if(o[tmp2.parents[k]] === undefined && tmp2.parents[k] !== $.jstree.root) {
											o[tmp2.parents[k]] = true;
											p.push(tmp2.parents[k]);
										}
									}
								}
							}
						}
					});
	
				this.element.find('.jstree-undetermined').removeClass('jstree-undetermined');
				for(i = 0, j = p.length; i < j; i++) {
					if(!m[p[i]].state[ t ? 'selected' : 'checked' ]) {
						s = this.get_node(p[i], true);
						if(s && s.length) {
							s.children('.jstree-anchor').children('.jstree-checkbox').addClass('jstree-undetermined');
						}
					}
				}
			};
			this.redraw_node = function(obj, deep, is_callback, force_render) {
				obj = parent.redraw_node.apply(this, arguments);
				if(obj) {
					var i, j, tmp = null, icon = null;
					for(i = 0, j = obj.childNodes.length; i < j; i++) {
						if(obj.childNodes[i] && obj.childNodes[i].className && obj.childNodes[i].className.indexOf("jstree-anchor") !== -1) {
							tmp = obj.childNodes[i];
							break;
						}
					}
					if(tmp) {
						if(!this.settings.checkbox.tie_selection && this._model.data[obj.id].state.checked) { tmp.className += ' jstree-checked'; }
						icon = _i.cloneNode(false);
						if(this._model.data[obj.id].state.checkbox_disabled) { icon.className += ' jstree-checkbox-disabled'; }
						tmp.insertBefore(icon, tmp.childNodes[0]);
					}
				}
				if(!is_callback && this.settings.checkbox.cascade.indexOf('undetermined') !== -1) {
					if(this._data.checkbox.uto) { clearTimeout(this._data.checkbox.uto); }
					this._data.checkbox.uto = setTimeout($.proxy(this._undetermined, this), 50);
				}
				return obj;
			};
			/**
			 * show the node checkbox icons
			 * @name show_checkboxes()
			 * @plugin checkbox
			 */
			this.show_checkboxes = function () { this._data.core.themes.checkboxes = true; this.get_container_ul().removeClass("jstree-no-checkboxes"); };
			/**
			 * hide the node checkbox icons
			 * @name hide_checkboxes()
			 * @plugin checkbox
			 */
			this.hide_checkboxes = function () { this._data.core.themes.checkboxes = false; this.get_container_ul().addClass("jstree-no-checkboxes"); };
			/**
			 * toggle the node icons
			 * @name toggle_checkboxes()
			 * @plugin checkbox
			 */
			this.toggle_checkboxes = function () { if(this._data.core.themes.checkboxes) { this.hide_checkboxes(); } else { this.show_checkboxes(); } };
			/**
			 * checks if a node is in an undetermined state
			 * @name is_undetermined(obj)
			 * @param  {mixed} obj
			 * @return {Boolean}
			 */
			this.is_undetermined = function (obj) {
				obj = this.get_node(obj);
				var s = this.settings.checkbox.cascade, i, j, t = this.settings.checkbox.tie_selection, d = this._data[ t ? 'core' : 'checkbox' ].selected, m = this._model.data;
				if(!obj || obj.state[ t ? 'selected' : 'checked' ] === true || s.indexOf('undetermined') === -1 || (s.indexOf('down') === -1 && s.indexOf('up') === -1)) {
					return false;
				}
				if(!obj.state.loaded && obj.original.state.undetermined === true) {
					return true;
				}
				for(i = 0, j = obj.children_d.length; i < j; i++) {
					if($.inArray(obj.children_d[i], d) !== -1 || (!m[obj.children_d[i]].state.loaded && m[obj.children_d[i]].original.state.undetermined)) {
						return true;
					}
				}
				return false;
			};
			/**
			 * disable a node's checkbox
			 * @name disable_checkbox(obj)
			 * @param {mixed} obj an array can be used too
			 * @trigger disable_checkbox.jstree
			 * @plugin checkbox
			 */
			this.disable_checkbox = function (obj) {
				var t1, t2, dom;
				if($.isArray(obj)) {
					obj = obj.slice();
					for(t1 = 0, t2 = obj.length; t1 < t2; t1++) {
						this.disable_checkbox(obj[t1]);
					}
					return true;
				}
				obj = this.get_node(obj);
				if(!obj || obj.id === $.jstree.root) {
					return false;
				}
				dom = this.get_node(obj, true);
				if(!obj.state.checkbox_disabled) {
					obj.state.checkbox_disabled = true;
					if(dom && dom.length) {
						dom.children('.jstree-anchor').children('.jstree-checkbox').addClass('jstree-checkbox-disabled');
					}
					/**
					 * triggered when an node's checkbox is disabled
					 * @event
					 * @name disable_checkbox.jstree
					 * @param {Object} node
					 * @plugin checkbox
					 */
					this.trigger('disable_checkbox', { 'node' : obj });
				}
			};
			/**
			 * enable a node's checkbox
			 * @name disable_checkbox(obj)
			 * @param {mixed} obj an array can be used too
			 * @trigger enable_checkbox.jstree
			 * @plugin checkbox
			 */
			this.enable_checkbox = function (obj) {
				var t1, t2, dom;
				if($.isArray(obj)) {
					obj = obj.slice();
					for(t1 = 0, t2 = obj.length; t1 < t2; t1++) {
						this.enable_checkbox(obj[t1]);
					}
					return true;
				}
				obj = this.get_node(obj);
				if(!obj || obj.id === $.jstree.root) {
					return false;
				}
				dom = this.get_node(obj, true);
				if(obj.state.checkbox_disabled) {
					obj.state.checkbox_disabled = false;
					if(dom && dom.length) {
						dom.children('.jstree-anchor').children('.jstree-checkbox').removeClass('jstree-checkbox-disabled');
					}
					/**
					 * triggered when an node's checkbox is enabled
					 * @event
					 * @name enable_checkbox.jstree
					 * @param {Object} node
					 * @plugin checkbox
					 */
					this.trigger('enable_checkbox', { 'node' : obj });
				}
			};
	
			this.activate_node = function (obj, e) {
				if($(e.target).hasClass('jstree-checkbox-disabled')) {
					return false;
				}
				if(this.settings.checkbox.tie_selection && (this.settings.checkbox.whole_node || $(e.target).hasClass('jstree-checkbox'))) {
					e.ctrlKey = true;
				}
				if(this.settings.checkbox.tie_selection || (!this.settings.checkbox.whole_node && !$(e.target).hasClass('jstree-checkbox'))) {
					return parent.activate_node.call(this, obj, e);
				}
				if(this.is_disabled(obj)) {
					return false;
				}
				if(this.is_checked(obj)) {
					this.uncheck_node(obj, e);
				}
				else {
					this.check_node(obj, e);
				}
				this.trigger('activate_node', { 'node' : this.get_node(obj) });
			};
	
			/**
			 * check a node (only if tie_selection in checkbox settings is false, otherwise select_node will be called internally)
			 * @name check_node(obj)
			 * @param {mixed} obj an array can be used to check multiple nodes
			 * @trigger check_node.jstree
			 * @plugin checkbox
			 */
			this.check_node = function (obj, e) {
				if(this.settings.checkbox.tie_selection) { return this.select_node(obj, false, true, e); }
				var dom, t1, t2, th;
				if($.isArray(obj)) {
					obj = obj.slice();
					for(t1 = 0, t2 = obj.length; t1 < t2; t1++) {
						this.check_node(obj[t1], e);
					}
					return true;
				}
				obj = this.get_node(obj);
				if(!obj || obj.id === $.jstree.root) {
					return false;
				}
				dom = this.get_node(obj, true);
				if(!obj.state.checked) {
					obj.state.checked = true;
					this._data.checkbox.selected.push(obj.id);
					if(dom && dom.length) {
						dom.children('.jstree-anchor').addClass('jstree-checked');
					}
					/**
					 * triggered when an node is checked (only if tie_selection in checkbox settings is false)
					 * @event
					 * @name check_node.jstree
					 * @param {Object} node
					 * @param {Array} selected the current selection
					 * @param {Object} event the event (if any) that triggered this check_node
					 * @plugin checkbox
					 */
					this.trigger('check_node', { 'node' : obj, 'selected' : this._data.checkbox.selected, 'event' : e });
				}
			};
			/**
			 * uncheck a node (only if tie_selection in checkbox settings is false, otherwise deselect_node will be called internally)
			 * @name uncheck_node(obj)
			 * @param {mixed} obj an array can be used to uncheck multiple nodes
			 * @trigger uncheck_node.jstree
			 * @plugin checkbox
			 */
			this.uncheck_node = function (obj, e) {
				if(this.settings.checkbox.tie_selection) { return this.deselect_node(obj, false, e); }
				var t1, t2, dom;
				if($.isArray(obj)) {
					obj = obj.slice();
					for(t1 = 0, t2 = obj.length; t1 < t2; t1++) {
						this.uncheck_node(obj[t1], e);
					}
					return true;
				}
				obj = this.get_node(obj);
				if(!obj || obj.id === $.jstree.root) {
					return false;
				}
				dom = this.get_node(obj, true);
				if(obj.state.checked) {
					obj.state.checked = false;
					this._data.checkbox.selected = $.vakata.array_remove_item(this._data.checkbox.selected, obj.id);
					if(dom.length) {
						dom.children('.jstree-anchor').removeClass('jstree-checked');
					}
					/**
					 * triggered when an node is unchecked (only if tie_selection in checkbox settings is false)
					 * @event
					 * @name uncheck_node.jstree
					 * @param {Object} node
					 * @param {Array} selected the current selection
					 * @param {Object} event the event (if any) that triggered this uncheck_node
					 * @plugin checkbox
					 */
					this.trigger('uncheck_node', { 'node' : obj, 'selected' : this._data.checkbox.selected, 'event' : e });
				}
			};
			/**
			 * checks all nodes in the tree (only if tie_selection in checkbox settings is false, otherwise select_all will be called internally)
			 * @name check_all()
			 * @trigger check_all.jstree, changed.jstree
			 * @plugin checkbox
			 */
			this.check_all = function () {
				if(this.settings.checkbox.tie_selection) { return this.select_all(); }
				var tmp = this._data.checkbox.selected.concat([]), i, j;
				this._data.checkbox.selected = this._model.data[$.jstree.root].children_d.concat();
				for(i = 0, j = this._data.checkbox.selected.length; i < j; i++) {
					if(this._model.data[this._data.checkbox.selected[i]]) {
						this._model.data[this._data.checkbox.selected[i]].state.checked = true;
					}
				}
				this.redraw(true);
				/**
				 * triggered when all nodes are checked (only if tie_selection in checkbox settings is false)
				 * @event
				 * @name check_all.jstree
				 * @param {Array} selected the current selection
				 * @plugin checkbox
				 */
				this.trigger('check_all', { 'selected' : this._data.checkbox.selected });
			};
			/**
			 * uncheck all checked nodes (only if tie_selection in checkbox settings is false, otherwise deselect_all will be called internally)
			 * @name uncheck_all()
			 * @trigger uncheck_all.jstree
			 * @plugin checkbox
			 */
			this.uncheck_all = function () {
				if(this.settings.checkbox.tie_selection) { return this.deselect_all(); }
				var tmp = this._data.checkbox.selected.concat([]), i, j;
				for(i = 0, j = this._data.checkbox.selected.length; i < j; i++) {
					if(this._model.data[this._data.checkbox.selected[i]]) {
						this._model.data[this._data.checkbox.selected[i]].state.checked = false;
					}
				}
				this._data.checkbox.selected = [];
				this.element.find('.jstree-checked').removeClass('jstree-checked');
				/**
				 * triggered when all nodes are unchecked (only if tie_selection in checkbox settings is false)
				 * @event
				 * @name uncheck_all.jstree
				 * @param {Object} node the previous selection
				 * @param {Array} selected the current selection
				 * @plugin checkbox
				 */
				this.trigger('uncheck_all', { 'selected' : this._data.checkbox.selected, 'node' : tmp });
			};
			/**
			 * checks if a node is checked (if tie_selection is on in the settings this function will return the same as is_selected)
			 * @name is_checked(obj)
			 * @param  {mixed}  obj
			 * @return {Boolean}
			 * @plugin checkbox
			 */
			this.is_checked = function (obj) {
				if(this.settings.checkbox.tie_selection) { return this.is_selected(obj); }
				obj = this.get_node(obj);
				if(!obj || obj.id === $.jstree.root) { return false; }
				return obj.state.checked;
			};
			/**
			 * get an array of all checked nodes (if tie_selection is on in the settings this function will return the same as get_selected)
			 * @name get_checked([full])
			 * @param  {mixed}  full if set to `true` the returned array will consist of the full node objects, otherwise - only IDs will be returned
			 * @return {Array}
			 * @plugin checkbox
			 */
			this.get_checked = function (full) {
				if(this.settings.checkbox.tie_selection) { return this.get_selected(full); }
				return full ? $.map(this._data.checkbox.selected, $.proxy(function (i) { return this.get_node(i); }, this)) : this._data.checkbox.selected;
			};
			/**
			 * get an array of all top level checked nodes (ignoring children of checked nodes) (if tie_selection is on in the settings this function will return the same as get_top_selected)
			 * @name get_top_checked([full])
			 * @param  {mixed}  full if set to `true` the returned array will consist of the full node objects, otherwise - only IDs will be returned
			 * @return {Array}
			 * @plugin checkbox
			 */
			this.get_top_checked = function (full) {
				if(this.settings.checkbox.tie_selection) { return this.get_top_selected(full); }
				var tmp = this.get_checked(true),
					obj = {}, i, j, k, l;
				for(i = 0, j = tmp.length; i < j; i++) {
					obj[tmp[i].id] = tmp[i];
				}
				for(i = 0, j = tmp.length; i < j; i++) {
					for(k = 0, l = tmp[i].children_d.length; k < l; k++) {
						if(obj[tmp[i].children_d[k]]) {
							delete obj[tmp[i].children_d[k]];
						}
					}
				}
				tmp = [];
				for(i in obj) {
					if(obj.hasOwnProperty(i)) {
						tmp.push(i);
					}
				}
				return full ? $.map(tmp, $.proxy(function (i) { return this.get_node(i); }, this)) : tmp;
			};
			/**
			 * get an array of all bottom level checked nodes (ignoring selected parents) (if tie_selection is on in the settings this function will return the same as get_bottom_selected)
			 * @name get_bottom_checked([full])
			 * @param  {mixed}  full if set to `true` the returned array will consist of the full node objects, otherwise - only IDs will be returned
			 * @return {Array}
			 * @plugin checkbox
			 */
			this.get_bottom_checked = function (full) {
				if(this.settings.checkbox.tie_selection) { return this.get_bottom_selected(full); }
				var tmp = this.get_checked(true),
					obj = [], i, j;
				for(i = 0, j = tmp.length; i < j; i++) {
					if(!tmp[i].children.length) {
						obj.push(tmp[i].id);
					}
				}
				return full ? $.map(obj, $.proxy(function (i) { return this.get_node(i); }, this)) : obj;
			};
			this.load_node = function (obj, callback) {
				var k, l, i, j, c, tmp;
				if(!$.isArray(obj) && !this.settings.checkbox.tie_selection) {
					tmp = this.get_node(obj);
					if(tmp && tmp.state.loaded) {
						for(k = 0, l = tmp.children_d.length; k < l; k++) {
							if(this._model.data[tmp.children_d[k]].state.checked) {
								c = true;
								this._data.checkbox.selected = $.vakata.array_remove_item(this._data.checkbox.selected, tmp.children_d[k]);
							}
						}
					}
				}
				return parent.load_node.apply(this, arguments);
			};
			this.get_state = function () {
				var state = parent.get_state.apply(this, arguments);
				if(this.settings.checkbox.tie_selection) { return state; }
				state.checkbox = this._data.checkbox.selected.slice();
				return state;
			};
			this.set_state = function (state, callback) {
				var res = parent.set_state.apply(this, arguments);
				if(res && state.checkbox) {
					if(!this.settings.checkbox.tie_selection) {
						this.uncheck_all();
						var _this = this;
						$.each(state.checkbox, function (i, v) {
							_this.check_node(v);
						});
					}
					delete state.checkbox;
					this.set_state(state, callback);
					return false;
				}
				return res;
			};
			this.refresh = function (skip_loading, forget_state) {
				if(!this.settings.checkbox.tie_selection) {
					this._data.checkbox.selected = [];
				}
				return parent.refresh.apply(this, arguments);
			};
		};
	
		// include the checkbox plugin by default
		// $.jstree.defaults.plugins.push("checkbox");
	
	/**
	 * ### Conditionalselect plugin
	 *
	 * This plugin allows defining a callback to allow or deny node selection by user input (activate node method).
	 */
	
		/**
		 * a callback (function) which is invoked in the instance's scope and receives two arguments - the node and the event that triggered the `activate_node` call. Returning false prevents working with the node, returning true allows invoking activate_node. Defaults to returning `true`.
		 * @name $.jstree.defaults.checkbox.visible
		 * @plugin checkbox
		 */
		$.jstree.defaults.conditionalselect = function () { return true; };
		$.jstree.plugins.conditionalselect = function (options, parent) {
			// own function
			this.activate_node = function (obj, e) {
				if(this.settings.conditionalselect.call(this, this.get_node(obj), e)) {
					parent.activate_node.call(this, obj, e);
				}
			};
		};
	
	
	/**
	 * ### Contextmenu plugin
	 *
	 * Shows a context menu when a node is right-clicked.
	 */
	
		/**
		 * stores all defaults for the contextmenu plugin
		 * @name $.jstree.defaults.contextmenu
		 * @plugin contextmenu
		 */
		$.jstree.defaults.contextmenu = {
			/**
			 * a boolean indicating if the node should be selected when the context menu is invoked on it. Defaults to `true`.
			 * @name $.jstree.defaults.contextmenu.select_node
			 * @plugin contextmenu
			 */
			select_node : true,
			/**
			 * a boolean indicating if the menu should be shown aligned with the node. Defaults to `true`, otherwise the mouse coordinates are used.
			 * @name $.jstree.defaults.contextmenu.show_at_node
			 * @plugin contextmenu
			 */
			show_at_node : true,
			/**
			 * an object of actions, or a function that accepts a node and a callback function and calls the callback function with an object of actions available for that node (you can also return the items too).
			 *
			 * Each action consists of a key (a unique name) and a value which is an object with the following properties (only label and action are required). Once a menu item is activated the `action` function will be invoked with an object containing the following keys: item - the contextmenu item definition as seen below, reference - the DOM node that was used (the tree node), element - the contextmenu DOM element, position - an object with x/y properties indicating the position of the menu.
			 *
			 * * `separator_before` - a boolean indicating if there should be a separator before this item
			 * * `separator_after` - a boolean indicating if there should be a separator after this item
			 * * `_disabled` - a boolean indicating if this action should be disabled
			 * * `label` - a string - the name of the action (could be a function returning a string)
			 * * `title` - a string - an optional tooltip for the item
			 * * `action` - a function to be executed if this item is chosen, the function will receive 
			 * * `icon` - a string, can be a path to an icon or a className, if using an image that is in the current directory use a `./` prefix, otherwise it will be detected as a class
			 * * `shortcut` - keyCode which will trigger the action if the menu is open (for example `113` for rename, which equals F2)
			 * * `shortcut_label` - shortcut label (like for example `F2` for rename)
			 * * `submenu` - an object with the same structure as $.jstree.defaults.contextmenu.items which can be used to create a submenu - each key will be rendered as a separate option in a submenu that will appear once the current item is hovered
			 *
			 * @name $.jstree.defaults.contextmenu.items
			 * @plugin contextmenu
			 */
			items : function (o, cb) { // Could be an object directly
				return {
					"create" : {
						"separator_before"	: false,
						"separator_after"	: true,
						"_disabled"			: false, //(this.check("create_node", data.reference, {}, "last")),
						"label"				: "Create",
						"action"			: function (data) {
							var inst = $.jstree.reference(data.reference),
								obj = inst.get_node(data.reference);
							inst.create_node(obj, {}, "last", function (new_node) {
								setTimeout(function () { inst.edit(new_node); },0);
							});
						}
					},
					"rename" : {
						"separator_before"	: false,
						"separator_after"	: false,
						"_disabled"			: false, //(this.check("rename_node", data.reference, this.get_parent(data.reference), "")),
						"label"				: "Rename",
						/*!
						"shortcut"			: 113,
						"shortcut_label"	: 'F2',
						"icon"				: "glyphicon glyphicon-leaf",
						*/
						"action"			: function (data) {
							var inst = $.jstree.reference(data.reference),
								obj = inst.get_node(data.reference);
							inst.edit(obj);
						}
					},
					"remove" : {
						"separator_before"	: false,
						"icon"				: false,
						"separator_after"	: false,
						"_disabled"			: false, //(this.check("delete_node", data.reference, this.get_parent(data.reference), "")),
						"label"				: "Delete",
						"action"			: function (data) {
							var inst = $.jstree.reference(data.reference),
								obj = inst.get_node(data.reference);
							if(inst.is_selected(obj)) {
								inst.delete_node(inst.get_selected());
							}
							else {
								inst.delete_node(obj);
							}
						}
					},
					"ccp" : {
						"separator_before"	: true,
						"icon"				: false,
						"separator_after"	: false,
						"label"				: "Edit",
						"action"			: false,
						"submenu" : {
							"cut" : {
								"separator_before"	: false,
								"separator_after"	: false,
								"label"				: "Cut",
								"action"			: function (data) {
									var inst = $.jstree.reference(data.reference),
										obj = inst.get_node(data.reference);
									if(inst.is_selected(obj)) {
										inst.cut(inst.get_top_selected());
									}
									else {
										inst.cut(obj);
									}
								}
							},
							"copy" : {
								"separator_before"	: false,
								"icon"				: false,
								"separator_after"	: false,
								"label"				: "Copy",
								"action"			: function (data) {
									var inst = $.jstree.reference(data.reference),
										obj = inst.get_node(data.reference);
									if(inst.is_selected(obj)) {
										inst.copy(inst.get_top_selected());
									}
									else {
										inst.copy(obj);
									}
								}
							},
							"paste" : {
								"separator_before"	: false,
								"icon"				: false,
								"_disabled"			: function (data) {
									return !$.jstree.reference(data.reference).can_paste();
								},
								"separator_after"	: false,
								"label"				: "Paste",
								"action"			: function (data) {
									var inst = $.jstree.reference(data.reference),
										obj = inst.get_node(data.reference);
									inst.paste(obj);
								}
							}
						}
					}
				};
			}
		};
	
		$.jstree.plugins.contextmenu = function (options, parent) {
			this.bind = function () {
				parent.bind.call(this);
	
				var last_ts = 0, cto = null, ex, ey;
				this.element
					.on("contextmenu.jstree", ".jstree-anchor", $.proxy(function (e, data) {
							if (e.target.tagName.toLowerCase() === 'input') {
								return;
							}
							e.preventDefault();
							last_ts = e.ctrlKey ? +new Date() : 0;
							if(data || cto) {
								last_ts = (+new Date()) + 10000;
							}
							if(cto) {
								clearTimeout(cto);
							}
							if(!this.is_loading(e.currentTarget)) {
								this.show_contextmenu(e.currentTarget, e.pageX, e.pageY, e);
							}
						}, this))
					.on("click.jstree", ".jstree-anchor", $.proxy(function (e) {
							if(this._data.contextmenu.visible && (!last_ts || (+new Date()) - last_ts > 250)) { // work around safari & macOS ctrl+click
								$.vakata.context.hide();
							}
							last_ts = 0;
						}, this))
					.on("touchstart.jstree", ".jstree-anchor", function (e) {
							if(!e.originalEvent || !e.originalEvent.changedTouches || !e.originalEvent.changedTouches[0]) {
								return;
							}
							ex = e.originalEvent.changedTouches[0].clientX;
							ey = e.originalEvent.changedTouches[0].clientY;
							cto = setTimeout(function () {
								$(e.currentTarget).trigger('contextmenu', true);
							}, 750);
						})
					.on('touchmove.vakata.jstree', function (e) {
							if(cto && e.originalEvent && e.originalEvent.changedTouches && e.originalEvent.changedTouches[0] && (Math.abs(ex - e.originalEvent.changedTouches[0].clientX) > 50 || Math.abs(ey - e.originalEvent.changedTouches[0].clientY) > 50)) {
								clearTimeout(cto);
							}
						})
					.on('touchend.vakata.jstree', function (e) {
							if(cto) {
								clearTimeout(cto);
							}
						});
	
				/*!
				if(!('oncontextmenu' in document.body) && ('ontouchstart' in document.body)) {
					var el = null, tm = null;
					this.element
						.on("touchstart", ".jstree-anchor", function (e) {
							el = e.currentTarget;
							tm = +new Date();
							$(document).one("touchend", function (e) {
								e.target = document.elementFromPoint(e.originalEvent.targetTouches[0].pageX - window.pageXOffset, e.originalEvent.targetTouches[0].pageY - window.pageYOffset);
								e.currentTarget = e.target;
								tm = ((+(new Date())) - tm);
								if(e.target === el && tm > 600 && tm < 1000) {
									e.preventDefault();
									$(el).trigger('contextmenu', e);
								}
								el = null;
								tm = null;
							});
						});
				}
				*/
				$(document).on("context_hide.vakata.jstree", $.proxy(function (e, data) {
					this._data.contextmenu.visible = false;
					$(data.reference).removeClass('jstree-context');
				}, this));
			};
			this.teardown = function () {
				if(this._data.contextmenu.visible) {
					$.vakata.context.hide();
				}
				parent.teardown.call(this);
			};
	
			/**
			 * prepare and show the context menu for a node
			 * @name show_contextmenu(obj [, x, y])
			 * @param {mixed} obj the node
			 * @param {Number} x the x-coordinate relative to the document to show the menu at
			 * @param {Number} y the y-coordinate relative to the document to show the menu at
			 * @param {Object} e the event if available that triggered the contextmenu
			 * @plugin contextmenu
			 * @trigger show_contextmenu.jstree
			 */
			this.show_contextmenu = function (obj, x, y, e) {
				obj = this.get_node(obj);
				if(!obj || obj.id === $.jstree.root) { return false; }
				var s = this.settings.contextmenu,
					d = this.get_node(obj, true),
					a = d.children(".jstree-anchor"),
					o = false,
					i = false;
				if(s.show_at_node || x === undefined || y === undefined) {
					o = a.offset();
					x = o.left;
					y = o.top + this._data.core.li_height;
				}
				if(this.settings.contextmenu.select_node && !this.is_selected(obj)) {
					this.activate_node(obj, e);
				}
	
				i = s.items;
				if($.isFunction(i)) {
					i = i.call(this, obj, $.proxy(function (i) {
						this._show_contextmenu(obj, x, y, i);
					}, this));
				}
				if($.isPlainObject(i)) {
					this._show_contextmenu(obj, x, y, i);
				}
			};
			/**
			 * show the prepared context menu for a node
			 * @name _show_contextmenu(obj, x, y, i)
			 * @param {mixed} obj the node
			 * @param {Number} x the x-coordinate relative to the document to show the menu at
			 * @param {Number} y the y-coordinate relative to the document to show the menu at
			 * @param {Number} i the object of items to show
			 * @plugin contextmenu
			 * @trigger show_contextmenu.jstree
			 * @private
			 */
			this._show_contextmenu = function (obj, x, y, i) {
				var d = this.get_node(obj, true),
					a = d.children(".jstree-anchor");
				$(document).one("context_show.vakata.jstree", $.proxy(function (e, data) {
					var cls = 'jstree-contextmenu jstree-' + this.get_theme() + '-contextmenu';
					$(data.element).addClass(cls);
					a.addClass('jstree-context');
				}, this));
				this._data.contextmenu.visible = true;
				$.vakata.context.show(a, { 'x' : x, 'y' : y }, i);
				/**
				 * triggered when the contextmenu is shown for a node
				 * @event
				 * @name show_contextmenu.jstree
				 * @param {Object} node the node
				 * @param {Number} x the x-coordinate of the menu relative to the document
				 * @param {Number} y the y-coordinate of the menu relative to the document
				 * @plugin contextmenu
				 */
				this.trigger('show_contextmenu', { "node" : obj, "x" : x, "y" : y });
			};
		};
	
		// contextmenu helper
		(function ($) {
			var right_to_left = false,
				vakata_context = {
					element		: false,
					reference	: false,
					position_x	: 0,
					position_y	: 0,
					items		: [],
					html		: "",
					is_visible	: false
				};
	
			$.vakata.context = {
				settings : {
					hide_onmouseleave	: 0,
					icons				: true
				},
				_trigger : function (event_name) {
					$(document).triggerHandler("context_" + event_name + ".vakata", {
						"reference"	: vakata_context.reference,
						"element"	: vakata_context.element,
						"position"	: {
							"x" : vakata_context.position_x,
							"y" : vakata_context.position_y
						}
					});
				},
				_execute : function (i) {
					i = vakata_context.items[i];
					return i && (!i._disabled || ($.isFunction(i._disabled) && !i._disabled({ "item" : i, "reference" : vakata_context.reference, "element" : vakata_context.element }))) && i.action ? i.action.call(null, {
								"item"		: i,
								"reference"	: vakata_context.reference,
								"element"	: vakata_context.element,
								"position"	: {
									"x" : vakata_context.position_x,
									"y" : vakata_context.position_y
								}
							}) : false;
				},
				_parse : function (o, is_callback) {
					if(!o) { return false; }
					if(!is_callback) {
						vakata_context.html		= "";
						vakata_context.items	= [];
					}
					var str = "",
						sep = false,
						tmp;
	
					if(is_callback) { str += "<"+"ul>"; }
					$.each(o, function (i, val) {
						if(!val) { return true; }
						vakata_context.items.push(val);
						if(!sep && val.separator_before) {
							str += "<"+"li class='vakata-context-separator'><"+"a href='#' " + ($.vakata.context.settings.icons ? '' : 'style="margin-left:0px;"') + ">&#160;<"+"/a><"+"/li>";
						}
						sep = false;
						str += "<"+"li class='" + (val._class || "") + (val._disabled === true || ($.isFunction(val._disabled) && val._disabled({ "item" : val, "reference" : vakata_context.reference, "element" : vakata_context.element })) ? " vakata-contextmenu-disabled " : "") + "' "+(val.shortcut?" data-shortcut='"+val.shortcut+"' ":'')+">";
						str += "<"+"a href='#' rel='" + (vakata_context.items.length - 1) + "' " + (val.title ? "title='" + val.title + "'" : "") + ">";
						if($.vakata.context.settings.icons) {
							str += "<"+"i ";
							if(val.icon) {
								if(val.icon.indexOf("/") !== -1 || val.icon.indexOf(".") !== -1) { str += " style='background:url(\"" + val.icon + "\") center center no-repeat' "; }
								else { str += " class='" + val.icon + "' "; }
							}
							str += "><"+"/i><"+"span class='vakata-contextmenu-sep'>&#160;<"+"/span>";
						}
						str += ($.isFunction(val.label) ? val.label({ "item" : i, "reference" : vakata_context.reference, "element" : vakata_context.element }) : val.label) + (val.shortcut?' <span class="vakata-contextmenu-shortcut vakata-contextmenu-shortcut-'+val.shortcut+'">'+ (val.shortcut_label || '') +'</span>':'') + "<"+"/a>";
						if(val.submenu) {
							tmp = $.vakata.context._parse(val.submenu, true);
							if(tmp) { str += tmp; }
						}
						str += "<"+"/li>";
						if(val.separator_after) {
							str += "<"+"li class='vakata-context-separator'><"+"a href='#' " + ($.vakata.context.settings.icons ? '' : 'style="margin-left:0px;"') + ">&#160;<"+"/a><"+"/li>";
							sep = true;
						}
					});
					str  = str.replace(/<li class\='vakata-context-separator'\><\/li\>$/,"");
					if(is_callback) { str += "</ul>"; }
					/**
					 * triggered on the document when the contextmenu is parsed (HTML is built)
					 * @event
					 * @plugin contextmenu
					 * @name context_parse.vakata
					 * @param {jQuery} reference the element that was right clicked
					 * @param {jQuery} element the DOM element of the menu itself
					 * @param {Object} position the x & y coordinates of the menu
					 */
					if(!is_callback) { vakata_context.html = str; $.vakata.context._trigger("parse"); }
					return str.length > 10 ? str : false;
				},
				_show_submenu : function (o) {
					o = $(o);
					if(!o.length || !o.children("ul").length) { return; }
					var e = o.children("ul"),
						xl = o.offset().left,
						x = xl + o.outerWidth(),
						y = o.offset().top,
						w = e.width(),
						h = e.height(),
						dw = $(window).width() + $(window).scrollLeft(),
						dh = $(window).height() + $(window).scrollTop();
					// може да се спести е една проверка - дали няма някой от класовете вече нагоре
					if(right_to_left) {
						o[x - (w + 10 + o.outerWidth()) < 0 ? "addClass" : "removeClass"]("vakata-context-left");
					}
					else {
						o[x + w > dw  && xl > dw - x ? "addClass" : "removeClass"]("vakata-context-right");
					}
					if(y + h + 10 > dh) {
						e.css("bottom","-1px");
					}
	
					//if does not fit - stick it to the side
					if (o.hasClass('vakata-context-right')) {
						if (xl < w) {
							e.css("margin-right", xl - w);
						}
					} else {
						if (dw - x < w) {
							e.css("margin-left", dw - x - w);
						}
					}
	
					e.show();
				},
				show : function (reference, position, data) {
					var o, e, x, y, w, h, dw, dh, cond = true;
					if(vakata_context.element && vakata_context.element.length) {
						vakata_context.element.width('');
					}
					switch(cond) {
						case (!position && !reference):
							return false;
						case (!!position && !!reference):
							vakata_context.reference	= reference;
							vakata_context.position_x	= position.x;
							vakata_context.position_y	= position.y;
							break;
						case (!position && !!reference):
							vakata_context.reference	= reference;
							o = reference.offset();
							vakata_context.position_x	= o.left + reference.outerHeight();
							vakata_context.position_y	= o.top;
							break;
						case (!!position && !reference):
							vakata_context.position_x	= position.x;
							vakata_context.position_y	= position.y;
							break;
					}
					if(!!reference && !data && $(reference).data('vakata_contextmenu')) {
						data = $(reference).data('vakata_contextmenu');
					}
					if($.vakata.context._parse(data)) {
						vakata_context.element.html(vakata_context.html);
					}
					if(vakata_context.items.length) {
						vakata_context.element.appendTo("body");
						e = vakata_context.element;
						x = vakata_context.position_x;
						y = vakata_context.position_y;
						w = e.width();
						h = e.height();
						dw = $(window).width() + $(window).scrollLeft();
						dh = $(window).height() + $(window).scrollTop();
						if(right_to_left) {
							x -= (e.outerWidth() - $(reference).outerWidth());
							if(x < $(window).scrollLeft() + 20) {
								x = $(window).scrollLeft() + 20;
							}
						}
						if(x + w + 20 > dw) {
							x = dw - (w + 20);
						}
						if(y + h + 20 > dh) {
							y = dh - (h + 20);
						}
	
						vakata_context.element
							.css({ "left" : x, "top" : y })
							.show()
							.find('a').first().focus().parent().addClass("vakata-context-hover");
						vakata_context.is_visible = true;
						/**
						 * triggered on the document when the contextmenu is shown
						 * @event
						 * @plugin contextmenu
						 * @name context_show.vakata
						 * @param {jQuery} reference the element that was right clicked
						 * @param {jQuery} element the DOM element of the menu itself
						 * @param {Object} position the x & y coordinates of the menu
						 */
						$.vakata.context._trigger("show");
					}
				},
				hide : function () {
					if(vakata_context.is_visible) {
						vakata_context.element.hide().find("ul").hide().end().find(':focus').blur().end().detach();
						vakata_context.is_visible = false;
						/**
						 * triggered on the document when the contextmenu is hidden
						 * @event
						 * @plugin contextmenu
						 * @name context_hide.vakata
						 * @param {jQuery} reference the element that was right clicked
						 * @param {jQuery} element the DOM element of the menu itself
						 * @param {Object} position the x & y coordinates of the menu
						 */
						$.vakata.context._trigger("hide");
					}
				}
			};
			$(function () {
				right_to_left = $("body").css("direction") === "rtl";
				var to = false;
	
				vakata_context.element = $("<ul class='vakata-context'></ul>");
				vakata_context.element
					.on("mouseenter", "li", function (e) {
						e.stopImmediatePropagation();
	
						if($.contains(this, e.relatedTarget)) {
							// премахнато заради delegate mouseleave по-долу
							// $(this).find(".vakata-context-hover").removeClass("vakata-context-hover");
							return;
						}
	
						if(to) { clearTimeout(to); }
						vakata_context.element.find(".vakata-context-hover").removeClass("vakata-context-hover").end();
	
						$(this)
							.siblings().find("ul").hide().end().end()
							.parentsUntil(".vakata-context", "li").addBack().addClass("vakata-context-hover");
						$.vakata.context._show_submenu(this);
					})
					// тестово - дали не натоварва?
					.on("mouseleave", "li", function (e) {
						if($.contains(this, e.relatedTarget)) { return; }
						$(this).find(".vakata-context-hover").addBack().removeClass("vakata-context-hover");
					})
					.on("mouseleave", function (e) {
						$(this).find(".vakata-context-hover").removeClass("vakata-context-hover");
						if($.vakata.context.settings.hide_onmouseleave) {
							to = setTimeout(
								(function (t) {
									return function () { $.vakata.context.hide(); };
								}(this)), $.vakata.context.settings.hide_onmouseleave);
						}
					})
					.on("click", "a", function (e) {
						e.preventDefault();
					//})
					//.on("mouseup", "a", function (e) {
						if(!$(this).blur().parent().hasClass("vakata-context-disabled") && $.vakata.context._execute($(this).attr("rel")) !== false) {
							$.vakata.context.hide();
						}
					})
					.on('keydown', 'a', function (e) {
							var o = null;
							switch(e.which) {
								case 13:
								case 32:
									e.type = "mouseup";
									e.preventDefault();
									$(e.currentTarget).trigger(e);
									break;
								case 37:
									if(vakata_context.is_visible) {
										vakata_context.element.find(".vakata-context-hover").last().closest("li").first().find("ul").hide().find(".vakata-context-hover").removeClass("vakata-context-hover").end().end().children('a').focus();
										e.stopImmediatePropagation();
										e.preventDefault();
									}
									break;
								case 38:
									if(vakata_context.is_visible) {
										o = vakata_context.element.find("ul:visible").addBack().last().children(".vakata-context-hover").removeClass("vakata-context-hover").prevAll("li:not(.vakata-context-separator)").first();
										if(!o.length) { o = vakata_context.element.find("ul:visible").addBack().last().children("li:not(.vakata-context-separator)").last(); }
										o.addClass("vakata-context-hover").children('a').focus();
										e.stopImmediatePropagation();
										e.preventDefault();
									}
									break;
								case 39:
									if(vakata_context.is_visible) {
										vakata_context.element.find(".vakata-context-hover").last().children("ul").show().children("li:not(.vakata-context-separator)").removeClass("vakata-context-hover").first().addClass("vakata-context-hover").children('a').focus();
										e.stopImmediatePropagation();
										e.preventDefault();
									}
									break;
								case 40:
									if(vakata_context.is_visible) {
										o = vakata_context.element.find("ul:visible").addBack().last().children(".vakata-context-hover").removeClass("vakata-context-hover").nextAll("li:not(.vakata-context-separator)").first();
										if(!o.length) { o = vakata_context.element.find("ul:visible").addBack().last().children("li:not(.vakata-context-separator)").first(); }
										o.addClass("vakata-context-hover").children('a').focus();
										e.stopImmediatePropagation();
										e.preventDefault();
									}
									break;
								case 27:
									$.vakata.context.hide();
									e.preventDefault();
									break;
								default:
									//console.log(e.which);
									break;
							}
						})
					.on('keydown', function (e) {
						e.preventDefault();
						var a = vakata_context.element.find('.vakata-contextmenu-shortcut-' + e.which).parent();
						if(a.parent().not('.vakata-context-disabled')) {
							a.click();
						}
					});
	
				$(document)
					.on("mousedown.vakata.jstree", function (e) {
						if(vakata_context.is_visible && !$.contains(vakata_context.element[0], e.target)) {
							$.vakata.context.hide();
						}
					})
					.on("context_show.vakata.jstree", function (e, data) {
						vakata_context.element.find("li:has(ul)").children("a").addClass("vakata-context-parent");
						if(right_to_left) {
							vakata_context.element.addClass("vakata-context-rtl").css("direction", "rtl");
						}
						// also apply a RTL class?
						vakata_context.element.find("ul").hide().end();
					});
			});
		}($));
		// $.jstree.defaults.plugins.push("contextmenu");
	
	
	/**
	 * ### Drag'n'drop plugin
	 *
	 * Enables dragging and dropping of nodes in the tree, resulting in a move or copy operations.
	 */
	
		/**
		 * stores all defaults for the drag'n'drop plugin
		 * @name $.jstree.defaults.dnd
		 * @plugin dnd
		 */
		$.jstree.defaults.dnd = {
			/**
			 * a boolean indicating if a copy should be possible while dragging (by pressint the meta key or Ctrl). Defaults to `true`.
			 * @name $.jstree.defaults.dnd.copy
			 * @plugin dnd
			 */
			copy : true,
			/**
			 * a number indicating how long a node should remain hovered while dragging to be opened. Defaults to `500`.
			 * @name $.jstree.defaults.dnd.open_timeout
			 * @plugin dnd
			 */
			open_timeout : 500,
			/**
			 * a function invoked each time a node is about to be dragged, invoked in the tree's scope and receives the nodes about to be dragged as an argument (array) and the event that started the drag - return `false` to prevent dragging
			 * @name $.jstree.defaults.dnd.is_draggable
			 * @plugin dnd
			 */
			is_draggable : true,
			/**
			 * a boolean indicating if checks should constantly be made while the user is dragging the node (as opposed to checking only on drop), default is `true`
			 * @name $.jstree.defaults.dnd.check_while_dragging
			 * @plugin dnd
			 */
			check_while_dragging : true,
			/**
			 * a boolean indicating if nodes from this tree should only be copied with dnd (as opposed to moved), default is `false`
			 * @name $.jstree.defaults.dnd.always_copy
			 * @plugin dnd
			 */
			always_copy : false,
			/**
			 * when dropping a node "inside", this setting indicates the position the node should go to - it can be an integer or a string: "first" (same as 0) or "last", default is `0`
			 * @name $.jstree.defaults.dnd.inside_pos
			 * @plugin dnd
			 */
			inside_pos : 0,
			/**
			 * when starting the drag on a node that is selected this setting controls if all selected nodes are dragged or only the single node, default is `true`, which means all selected nodes are dragged when the drag is started on a selected node
			 * @name $.jstree.defaults.dnd.drag_selection
			 * @plugin dnd
			 */
			drag_selection : true,
			/**
			 * controls whether dnd works on touch devices. If left as boolean true dnd will work the same as in desktop browsers, which in some cases may impair scrolling. If set to boolean false dnd will not work on touch devices. There is a special third option - string "selected" which means only selected nodes can be dragged on touch devices.
			 * @name $.jstree.defaults.dnd.touch
			 * @plugin dnd
			 */
			touch : true,
			/**
			 * controls whether items can be dropped anywhere on the node, not just on the anchor, by default only the node anchor is a valid drop target. Works best with the wholerow plugin. If enabled on mobile depending on the interface it might be hard for the user to cancel the drop, since the whole tree container will be a valid drop target.
			 * @name $.jstree.defaults.dnd.large_drop_target
			 * @plugin dnd
			 */
			large_drop_target : false,
			/**
			 * controls whether a drag can be initiated from any part of the node and not just the text/icon part, works best with the wholerow plugin. Keep in mind it can cause problems with tree scrolling on mobile depending on the interface - in that case set the touch option to "selected".
			 * @name $.jstree.defaults.dnd.large_drag_target
			 * @plugin dnd
			 */
			large_drag_target : false,
			/**
			 * controls whether use HTML5 dnd api instead of classical. That will allow better integration of dnd events with other HTML5 controls.
			 * @reference http://caniuse.com/#feat=dragndrop
			 * @name $.jstree.defaults.dnd.use_html5
			 * @plugin dnd
			 */
			use_html5: false
		};
		var drg, elm;
		// TODO: now check works by checking for each node individually, how about max_children, unique, etc?
		$.jstree.plugins.dnd = function (options, parent) {
			this.init = function (el, options) {
				parent.init.call(this, el, options);
				this.settings.dnd.use_html5 = this.settings.dnd.use_html5 && ('draggable' in document.createElement('span'));
			};
			this.bind = function () {
				parent.bind.call(this);
	
				this.element
					.on(this.settings.dnd.use_html5 ? 'dragstart.jstree' : 'mousedown.jstree touchstart.jstree', this.settings.dnd.large_drag_target ? '.jstree-node' : '.jstree-anchor', $.proxy(function (e) {
							if(this.settings.dnd.large_drag_target && $(e.target).closest('.jstree-node')[0] !== e.currentTarget) {
								return true;
							}
							if(e.type === "touchstart" && (!this.settings.dnd.touch || (this.settings.dnd.touch === 'selected' && !$(e.currentTarget).closest('.jstree-node').children('.jstree-anchor').hasClass('jstree-clicked')))) {
								return true;
							}
							var obj = this.get_node(e.target),
								mlt = this.is_selected(obj) && this.settings.dnd.drag_selection ? this.get_top_selected().length : 1,
								txt = (mlt > 1 ? mlt + ' ' + this.get_string('nodes') : this.get_text(e.currentTarget));
							if(this.settings.core.force_text) {
								txt = $.vakata.html.escape(txt);
							}
							if(obj && obj.id && obj.id !== $.jstree.root && (e.which === 1 || e.type === "touchstart" || e.type === "dragstart") &&
								(this.settings.dnd.is_draggable === true || ($.isFunction(this.settings.dnd.is_draggable) && this.settings.dnd.is_draggable.call(this, (mlt > 1 ? this.get_top_selected(true) : [obj]), e)))
							) {
								drg = { 'jstree' : true, 'origin' : this, 'obj' : this.get_node(obj,true), 'nodes' : mlt > 1 ? this.get_top_selected() : [obj.id] };
								elm = e.currentTarget;
								if (this.settings.dnd.use_html5) {
									$.vakata.dnd._trigger('start', e, { 'helper': $(), 'element': elm, 'data': drg });
								} else {
									this.element.trigger('mousedown.jstree');
									return $.vakata.dnd.start(e, drg, '<div id="jstree-dnd" class="jstree-' + this.get_theme() + ' jstree-' + this.get_theme() + '-' + this.get_theme_variant() + ' ' + ( this.settings.core.themes.responsive ? ' jstree-dnd-responsive' : '' ) + '"><i class="jstree-icon jstree-er"></i>' + txt + '<ins class="jstree-copy" style="display:none;">+</ins></div>');
								}
							}
						}, this));
				if (this.settings.dnd.use_html5) {
					this.element
						.on('dragover.jstree', function (e) {
								e.preventDefault();
								$.vakata.dnd._trigger('move', e, { 'helper': $(), 'element': elm, 'data': drg });
								return false;
							})
						//.on('dragenter.jstree', this.settings.dnd.large_drop_target ? '.jstree-node' : '.jstree-anchor', $.proxy(function (e) {
						//		e.preventDefault();
						//		$.vakata.dnd._trigger('move', e, { 'helper': $(), 'element': elm, 'data': drg });
						//		return false;
						//	}, this))
						.on('drop.jstree', $.proxy(function (e) {
								e.preventDefault();
								$.vakata.dnd._trigger('stop', e, { 'helper': $(), 'element': elm, 'data': drg });
								return false;
							}, this));
				}
			};
			this.redraw_node = function(obj, deep, callback, force_render) {
				obj = parent.redraw_node.apply(this, arguments);
				if (obj && this.settings.dnd.use_html5) {
					if (this.settings.dnd.large_drag_target) {
						obj.setAttribute('draggable', true);
					} else {
						var i, j, tmp = null;
						for(i = 0, j = obj.childNodes.length; i < j; i++) {
							if(obj.childNodes[i] && obj.childNodes[i].className && obj.childNodes[i].className.indexOf("jstree-anchor") !== -1) {
								tmp = obj.childNodes[i];
								break;
							}
						}
						if(tmp) {
							tmp.setAttribute('draggable', true);
						}
					}
				}
				return obj;
			};
		};
	
		$(function() {
			// bind only once for all instances
			var lastmv = false,
				laster = false,
				lastev = false,
				opento = false,
				marker = $('<div id="jstree-marker">&#160;</div>').hide(); //.appendTo('body');
	
			$(document)
				.on('dnd_start.vakata.jstree', function (e, data) {
					lastmv = false;
					lastev = false;
					if(!data || !data.data || !data.data.jstree) { return; }
					marker.appendTo('body'); //.show();
				})
				.on('dnd_move.vakata.jstree', function (e, data) {
					if(opento) {
						if (!data.event || data.event.type !== 'dragover' || data.event.target !== lastev.target) {
							clearTimeout(opento);
						}
					}
					if(!data || !data.data || !data.data.jstree) { return; }
	
					// if we are hovering the marker image do nothing (can happen on "inside" drags)
					if(data.event.target.id && data.event.target.id === 'jstree-marker') {
						return;
					}
					lastev = data.event;
	
					var ins = $.jstree.reference(data.event.target),
						ref = false,
						off = false,
						rel = false,
						tmp, l, t, h, p, i, o, ok, t1, t2, op, ps, pr, ip, tm, is_copy, pn;
					// if we are over an instance
					if(ins && ins._data && ins._data.dnd) {
						marker.attr('class', 'jstree-' + ins.get_theme() + ( ins.settings.core.themes.responsive ? ' jstree-dnd-responsive' : '' ));
						is_copy = data.data.origin && (data.data.origin.settings.dnd.always_copy || (data.data.origin.settings.dnd.copy && (data.event.metaKey || data.event.ctrlKey)));
						data.helper
							.children().attr('class', 'jstree-' + ins.get_theme() + ' jstree-' + ins.get_theme() + '-' + ins.get_theme_variant() + ' ' + ( ins.settings.core.themes.responsive ? ' jstree-dnd-responsive' : '' ))
							.find('.jstree-copy').first()[ is_copy ? 'show' : 'hide' ]();
	
						// if are hovering the container itself add a new root node
						//console.log(data.event);
						if( (data.event.target === ins.element[0] || data.event.target === ins.get_container_ul()[0]) && ins.get_container_ul().children().length === 0) {
							ok = true;
							for(t1 = 0, t2 = data.data.nodes.length; t1 < t2; t1++) {
								ok = ok && ins.check( (data.data.origin && (data.data.origin.settings.dnd.always_copy || (data.data.origin.settings.dnd.copy && (data.event.metaKey || data.event.ctrlKey)) ) ? "copy_node" : "move_node"), (data.data.origin && data.data.origin !== ins ? data.data.origin.get_node(data.data.nodes[t1]) : data.data.nodes[t1]), $.jstree.root, 'last', { 'dnd' : true, 'ref' : ins.get_node($.jstree.root), 'pos' : 'i', 'origin' : data.data.origin, 'is_multi' : (data.data.origin && data.data.origin !== ins), 'is_foreign' : (!data.data.origin) });
								if(!ok) { break; }
							}
							if(ok) {
								lastmv = { 'ins' : ins, 'par' : $.jstree.root, 'pos' : 'last' };
								marker.hide();
								data.helper.find('.jstree-icon').first().removeClass('jstree-er').addClass('jstree-ok');
								if (data.event.originalEvent && data.event.originalEvent.dataTransfer) {
									data.event.originalEvent.dataTransfer.dropEffect = is_copy ? 'copy' : 'move';
								}
								return;
							}
						}
						else {
							// if we are hovering a tree node
							ref = ins.settings.dnd.large_drop_target ? $(data.event.target).closest('.jstree-node').children('.jstree-anchor') : $(data.event.target).closest('.jstree-anchor');
							if(ref && ref.length && ref.parent().is('.jstree-closed, .jstree-open, .jstree-leaf')) {
								off = ref.offset();
								rel = (data.event.pageY !== undefined ? data.event.pageY : data.event.originalEvent.pageY) - off.top;
								h = ref.outerHeight();
								if(rel < h / 3) {
									o = ['b', 'i', 'a'];
								}
								else if(rel > h - h / 3) {
									o = ['a', 'i', 'b'];
								}
								else {
									o = rel > h / 2 ? ['i', 'a', 'b'] : ['i', 'b', 'a'];
								}
								$.each(o, function (j, v) {
									switch(v) {
										case 'b':
											l = off.left - 6;
											t = off.top;
											p = ins.get_parent(ref);
											i = ref.parent().index();
											break;
										case 'i':
											ip = ins.settings.dnd.inside_pos;
											tm = ins.get_node(ref.parent());
											l = off.left - 2;
											t = off.top + h / 2 + 1;
											p = tm.id;
											i = ip === 'first' ? 0 : (ip === 'last' ? tm.children.length : Math.min(ip, tm.children.length));
											break;
										case 'a':
											l = off.left - 6;
											t = off.top + h;
											p = ins.get_parent(ref);
											i = ref.parent().index() + 1;
											break;
									}
									ok = true;
									for(t1 = 0, t2 = data.data.nodes.length; t1 < t2; t1++) {
										op = data.data.origin && (data.data.origin.settings.dnd.always_copy || (data.data.origin.settings.dnd.copy && (data.event.metaKey || data.event.ctrlKey))) ? "copy_node" : "move_node";
										ps = i;
										if(op === "move_node" && v === 'a' && (data.data.origin && data.data.origin === ins) && p === ins.get_parent(data.data.nodes[t1])) {
											pr = ins.get_node(p);
											if(ps > $.inArray(data.data.nodes[t1], pr.children)) {
												ps -= 1;
											}
										}
										ok = ok && ( (ins && ins.settings && ins.settings.dnd && ins.settings.dnd.check_while_dragging === false) || ins.check(op, (data.data.origin && data.data.origin !== ins ? data.data.origin.get_node(data.data.nodes[t1]) : data.data.nodes[t1]), p, ps, { 'dnd' : true, 'ref' : ins.get_node(ref.parent()), 'pos' : v, 'origin' : data.data.origin, 'is_multi' : (data.data.origin && data.data.origin !== ins), 'is_foreign' : (!data.data.origin) }) );
										if(!ok) {
											if(ins && ins.last_error) { laster = ins.last_error(); }
											break;
										}
									}
									if(v === 'i' && ref.parent().is('.jstree-closed') && ins.settings.dnd.open_timeout) {
										opento = setTimeout((function (x, z) { return function () { x.open_node(z); }; }(ins, ref)), ins.settings.dnd.open_timeout);
									}
									if(ok) {
										pn = ins.get_node(p, true);
										if (!pn.hasClass('.jstree-dnd-parent')) {
											$('.jstree-dnd-parent').removeClass('jstree-dnd-parent');
											pn.addClass('jstree-dnd-parent');
										}
										lastmv = { 'ins' : ins, 'par' : p, 'pos' : v === 'i' && ip === 'last' && i === 0 && !ins.is_loaded(tm) ? 'last' : i };
										marker.css({ 'left' : l + 'px', 'top' : t + 'px' }).show();
										data.helper.find('.jstree-icon').first().removeClass('jstree-er').addClass('jstree-ok');
										if (data.event.originalEvent && data.event.originalEvent.dataTransfer) {
											data.event.originalEvent.dataTransfer.dropEffect = is_copy ? 'copy' : 'move';
										}
										laster = {};
										o = true;
										return false;
									}
								});
								if(o === true) { return; }
							}
						}
					}
					$('.jstree-dnd-parent').removeClass('jstree-dnd-parent');
					lastmv = false;
					data.helper.find('.jstree-icon').removeClass('jstree-ok').addClass('jstree-er');
					if (data.event.originalEvent && data.event.originalEvent.dataTransfer) {
						data.event.originalEvent.dataTransfer.dropEffect = 'none';
					}
					marker.hide();
				})
				.on('dnd_scroll.vakata.jstree', function (e, data) {
					if(!data || !data.data || !data.data.jstree) { return; }
					marker.hide();
					lastmv = false;
					lastev = false;
					data.helper.find('.jstree-icon').first().removeClass('jstree-ok').addClass('jstree-er');
				})
				.on('dnd_stop.vakata.jstree', function (e, data) {
					$('.jstree-dnd-parent').removeClass('jstree-dnd-parent');
					if(opento) { clearTimeout(opento); }
					if(!data || !data.data || !data.data.jstree) { return; }
					marker.hide().detach();
					var i, j, nodes = [];
					if(lastmv) {
						for(i = 0, j = data.data.nodes.length; i < j; i++) {
							nodes[i] = data.data.origin ? data.data.origin.get_node(data.data.nodes[i]) : data.data.nodes[i];
						}
						lastmv.ins[ data.data.origin && (data.data.origin.settings.dnd.always_copy || (data.data.origin.settings.dnd.copy && (data.event.metaKey || data.event.ctrlKey))) ? 'copy_node' : 'move_node' ](nodes, lastmv.par, lastmv.pos, false, false, false, data.data.origin);
					}
					else {
						i = $(data.event.target).closest('.jstree');
						if(i.length && laster && laster.error && laster.error === 'check') {
							i = i.jstree(true);
							if(i) {
								i.settings.core.error.call(this, laster);
							}
						}
					}
					lastev = false;
					lastmv = false;
				})
				.on('keyup.jstree keydown.jstree', function (e, data) {
					data = $.vakata.dnd._get();
					if(data && data.data && data.data.jstree) {
						if (e.type === "keyup" && e.which === 27) {
							if (opento) { clearTimeout(opento); }
							lastmv = false;
							laster = false;
							lastev = false;
							opento = false;
							marker.hide().detach();
							$.vakata.dnd._clean();
						} else {
							data.helper.find('.jstree-copy').first()[ data.data.origin && (data.data.origin.settings.dnd.always_copy || (data.data.origin.settings.dnd.copy && (e.metaKey || e.ctrlKey))) ? 'show' : 'hide' ]();
							if(lastev) {
								lastev.metaKey = e.metaKey;
								lastev.ctrlKey = e.ctrlKey;
								$.vakata.dnd._trigger('move', lastev);
							}
						}
					}
				});
		});
	
		// helpers
		(function ($) {
			$.vakata.html = {
				div : $('<div />'),
				escape : function (str) {
					return $.vakata.html.div.text(str).html();
				},
				strip : function (str) {
					return $.vakata.html.div.empty().append($.parseHTML(str)).text();
				}
			};
			// private variable
			var vakata_dnd = {
				element	: false,
				target	: false,
				is_down	: false,
				is_drag	: false,
				helper	: false,
				helper_w: 0,
				data	: false,
				init_x	: 0,
				init_y	: 0,
				scroll_l: 0,
				scroll_t: 0,
				scroll_e: false,
				scroll_i: false,
				is_touch: false
			};
			$.vakata.dnd = {
				settings : {
					scroll_speed		: 10,
					scroll_proximity	: 20,
					helper_left			: 5,
					helper_top			: 10,
					threshold			: 5,
					threshold_touch		: 50
				},
				_trigger : function (event_name, e, data) {
					if (data === undefined) {
						data = $.vakata.dnd._get();
					}
					data.event = e;
					$(document).triggerHandler("dnd_" + event_name + ".vakata", data);
				},
				_get : function () {
					return {
						"data"		: vakata_dnd.data,
						"element"	: vakata_dnd.element,
						"helper"	: vakata_dnd.helper
					};
				},
				_clean : function () {
					if(vakata_dnd.helper) { vakata_dnd.helper.remove(); }
					if(vakata_dnd.scroll_i) { clearInterval(vakata_dnd.scroll_i); vakata_dnd.scroll_i = false; }
					vakata_dnd = {
						element	: false,
						target	: false,
						is_down	: false,
						is_drag	: false,
						helper	: false,
						helper_w: 0,
						data	: false,
						init_x	: 0,
						init_y	: 0,
						scroll_l: 0,
						scroll_t: 0,
						scroll_e: false,
						scroll_i: false,
						is_touch: false
					};
					$(document).off("mousemove.vakata.jstree touchmove.vakata.jstree", $.vakata.dnd.drag);
					$(document).off("mouseup.vakata.jstree touchend.vakata.jstree", $.vakata.dnd.stop);
				},
				_scroll : function (init_only) {
					if(!vakata_dnd.scroll_e || (!vakata_dnd.scroll_l && !vakata_dnd.scroll_t)) {
						if(vakata_dnd.scroll_i) { clearInterval(vakata_dnd.scroll_i); vakata_dnd.scroll_i = false; }
						return false;
					}
					if(!vakata_dnd.scroll_i) {
						vakata_dnd.scroll_i = setInterval($.vakata.dnd._scroll, 100);
						return false;
					}
					if(init_only === true) { return false; }
	
					var i = vakata_dnd.scroll_e.scrollTop(),
						j = vakata_dnd.scroll_e.scrollLeft();
					vakata_dnd.scroll_e.scrollTop(i + vakata_dnd.scroll_t * $.vakata.dnd.settings.scroll_speed);
					vakata_dnd.scroll_e.scrollLeft(j + vakata_dnd.scroll_l * $.vakata.dnd.settings.scroll_speed);
					if(i !== vakata_dnd.scroll_e.scrollTop() || j !== vakata_dnd.scroll_e.scrollLeft()) {
						/**
						 * triggered on the document when a drag causes an element to scroll
						 * @event
						 * @plugin dnd
						 * @name dnd_scroll.vakata
						 * @param {Mixed} data any data supplied with the call to $.vakata.dnd.start
						 * @param {DOM} element the DOM element being dragged
						 * @param {jQuery} helper the helper shown next to the mouse
						 * @param {jQuery} event the element that is scrolling
						 */
						$.vakata.dnd._trigger("scroll", vakata_dnd.scroll_e);
					}
				},
				start : function (e, data, html) {
					if(e.type === "touchstart" && e.originalEvent && e.originalEvent.changedTouches && e.originalEvent.changedTouches[0]) {
						e.pageX = e.originalEvent.changedTouches[0].pageX;
						e.pageY = e.originalEvent.changedTouches[0].pageY;
						e.target = document.elementFromPoint(e.originalEvent.changedTouches[0].pageX - window.pageXOffset, e.originalEvent.changedTouches[0].pageY - window.pageYOffset);
					}
					if(vakata_dnd.is_drag) { $.vakata.dnd.stop({}); }
					try {
						e.currentTarget.unselectable = "on";
						e.currentTarget.onselectstart = function() { return false; };
						if(e.currentTarget.style) {
							e.currentTarget.style.touchAction = "none";
							e.currentTarget.style.msTouchAction = "none";
							e.currentTarget.style.MozUserSelect = "none";
						}
					} catch(ignore) { }
					vakata_dnd.init_x	= e.pageX;
					vakata_dnd.init_y	= e.pageY;
					vakata_dnd.data		= data;
					vakata_dnd.is_down	= true;
					vakata_dnd.element	= e.currentTarget;
					vakata_dnd.target	= e.target;
					vakata_dnd.is_touch	= e.type === "touchstart";
					if(html !== false) {
						vakata_dnd.helper = $("<div id='vakata-dnd'></div>").html(html).css({
							"display"		: "block",
							"margin"		: "0",
							"padding"		: "0",
							"position"		: "absolute",
							"top"			: "-2000px",
							"lineHeight"	: "16px",
							"zIndex"		: "10000"
						});
					}
					$(document).on("mousemove.vakata.jstree touchmove.vakata.jstree", $.vakata.dnd.drag);
					$(document).on("mouseup.vakata.jstree touchend.vakata.jstree", $.vakata.dnd.stop);
					return false;
				},
				drag : function (e) {
					if(e.type === "touchmove" && e.originalEvent && e.originalEvent.changedTouches && e.originalEvent.changedTouches[0]) {
						e.pageX = e.originalEvent.changedTouches[0].pageX;
						e.pageY = e.originalEvent.changedTouches[0].pageY;
						e.target = document.elementFromPoint(e.originalEvent.changedTouches[0].pageX - window.pageXOffset, e.originalEvent.changedTouches[0].pageY - window.pageYOffset);
					}
					if(!vakata_dnd.is_down) { return; }
					if(!vakata_dnd.is_drag) {
						if(
							Math.abs(e.pageX - vakata_dnd.init_x) > (vakata_dnd.is_touch ? $.vakata.dnd.settings.threshold_touch : $.vakata.dnd.settings.threshold) ||
							Math.abs(e.pageY - vakata_dnd.init_y) > (vakata_dnd.is_touch ? $.vakata.dnd.settings.threshold_touch : $.vakata.dnd.settings.threshold)
						) {
							if(vakata_dnd.helper) {
								vakata_dnd.helper.appendTo("body");
								vakata_dnd.helper_w = vakata_dnd.helper.outerWidth();
							}
							vakata_dnd.is_drag = true;
							$(vakata_dnd.target).one('click.vakata', false);
							/**
							 * triggered on the document when a drag starts
							 * @event
							 * @plugin dnd
							 * @name dnd_start.vakata
							 * @param {Mixed} data any data supplied with the call to $.vakata.dnd.start
							 * @param {DOM} element the DOM element being dragged
							 * @param {jQuery} helper the helper shown next to the mouse
							 * @param {Object} event the event that caused the start (probably mousemove)
							 */
							$.vakata.dnd._trigger("start", e);
						}
						else { return; }
					}
	
					var d  = false, w  = false,
						dh = false, wh = false,
						dw = false, ww = false,
						dt = false, dl = false,
						ht = false, hl = false;
	
					vakata_dnd.scroll_t = 0;
					vakata_dnd.scroll_l = 0;
					vakata_dnd.scroll_e = false;
					$($(e.target).parentsUntil("body").addBack().get().reverse())
						.filter(function () {
							return	(/^auto|scroll$/).test($(this).css("overflow")) &&
									(this.scrollHeight > this.offsetHeight || this.scrollWidth > this.offsetWidth);
						})
						.each(function () {
							var t = $(this), o = t.offset();
							if(this.scrollHeight > this.offsetHeight) {
								if(o.top + t.height() - e.pageY < $.vakata.dnd.settings.scroll_proximity)	{ vakata_dnd.scroll_t = 1; }
								if(e.pageY - o.top < $.vakata.dnd.settings.scroll_proximity)				{ vakata_dnd.scroll_t = -1; }
							}
							if(this.scrollWidth > this.offsetWidth) {
								if(o.left + t.width() - e.pageX < $.vakata.dnd.settings.scroll_proximity)	{ vakata_dnd.scroll_l = 1; }
								if(e.pageX - o.left < $.vakata.dnd.settings.scroll_proximity)				{ vakata_dnd.scroll_l = -1; }
							}
							if(vakata_dnd.scroll_t || vakata_dnd.scroll_l) {
								vakata_dnd.scroll_e = $(this);
								return false;
							}
						});
	
					if(!vakata_dnd.scroll_e) {
						d  = $(document); w = $(window);
						dh = d.height(); wh = w.height();
						dw = d.width(); ww = w.width();
						dt = d.scrollTop(); dl = d.scrollLeft();
						if(dh > wh && e.pageY - dt < $.vakata.dnd.settings.scroll_proximity)		{ vakata_dnd.scroll_t = -1;  }
						if(dh > wh && wh - (e.pageY - dt) < $.vakata.dnd.settings.scroll_proximity)	{ vakata_dnd.scroll_t = 1; }
						if(dw > ww && e.pageX - dl < $.vakata.dnd.settings.scroll_proximity)		{ vakata_dnd.scroll_l = -1; }
						if(dw > ww && ww - (e.pageX - dl) < $.vakata.dnd.settings.scroll_proximity)	{ vakata_dnd.scroll_l = 1; }
						if(vakata_dnd.scroll_t || vakata_dnd.scroll_l) {
							vakata_dnd.scroll_e = d;
						}
					}
					if(vakata_dnd.scroll_e) { $.vakata.dnd._scroll(true); }
	
					if(vakata_dnd.helper) {
						ht = parseInt(e.pageY + $.vakata.dnd.settings.helper_top, 10);
						hl = parseInt(e.pageX + $.vakata.dnd.settings.helper_left, 10);
						if(dh && ht + 25 > dh) { ht = dh - 50; }
						if(dw && hl + vakata_dnd.helper_w > dw) { hl = dw - (vakata_dnd.helper_w + 2); }
						vakata_dnd.helper.css({
							left	: hl + "px",
							top		: ht + "px"
						});
					}
					/**
					 * triggered on the document when a drag is in progress
					 * @event
					 * @plugin dnd
					 * @name dnd_move.vakata
					 * @param {Mixed} data any data supplied with the call to $.vakata.dnd.start
					 * @param {DOM} element the DOM element being dragged
					 * @param {jQuery} helper the helper shown next to the mouse
					 * @param {Object} event the event that caused this to trigger (most likely mousemove)
					 */
					$.vakata.dnd._trigger("move", e);
					return false;
				},
				stop : function (e) {
					if(e.type === "touchend" && e.originalEvent && e.originalEvent.changedTouches && e.originalEvent.changedTouches[0]) {
						e.pageX = e.originalEvent.changedTouches[0].pageX;
						e.pageY = e.originalEvent.changedTouches[0].pageY;
						e.target = document.elementFromPoint(e.originalEvent.changedTouches[0].pageX - window.pageXOffset, e.originalEvent.changedTouches[0].pageY - window.pageYOffset);
					}
					if(vakata_dnd.is_drag) {
						/**
						 * triggered on the document when a drag stops (the dragged element is dropped)
						 * @event
						 * @plugin dnd
						 * @name dnd_stop.vakata
						 * @param {Mixed} data any data supplied with the call to $.vakata.dnd.start
						 * @param {DOM} element the DOM element being dragged
						 * @param {jQuery} helper the helper shown next to the mouse
						 * @param {Object} event the event that caused the stop
						 */
						if (e.target !== vakata_dnd.target) {
							$(vakata_dnd.target).off('click.vakata');
						}
						$.vakata.dnd._trigger("stop", e);
					}
					else {
						if(e.type === "touchend" && e.target === vakata_dnd.target) {
							var to = setTimeout(function () { $(e.target).click(); }, 100);
							$(e.target).one('click', function() { if(to) { clearTimeout(to); } });
						}
					}
					$.vakata.dnd._clean();
					return false;
				}
			};
		}($));
	
		// include the dnd plugin by default
		// $.jstree.defaults.plugins.push("dnd");
	
	
	/**
	 * ### Massload plugin
	 *
	 * Adds massload functionality to jsTree, so that multiple nodes can be loaded in a single request (only useful with lazy loading).
	 */
	
		/**
		 * massload configuration
		 *
		 * It is possible to set this to a standard jQuery-like AJAX config.
		 * In addition to the standard jQuery ajax options here you can supply functions for `data` and `url`, the functions will be run in the current instance's scope and a param will be passed indicating which node IDs need to be loaded, the return value of those functions will be used.
		 *
		 * You can also set this to a function, that function will receive the node IDs being loaded as argument and a second param which is a function (callback) which should be called with the result.
		 *
		 * Both the AJAX and the function approach rely on the same return value - an object where the keys are the node IDs, and the value is the children of that node as an array.
		 *
		 *	{
		 *		"id1" : [{ "text" : "Child of ID1", "id" : "c1" }, { "text" : "Another child of ID1", "id" : "c2" }],
		 *		"id2" : [{ "text" : "Child of ID2", "id" : "c3" }]
		 *	}
		 * 
		 * @name $.jstree.defaults.massload
		 * @plugin massload
		 */
		$.jstree.defaults.massload = null;
		$.jstree.plugins.massload = function (options, parent) {
			this.init = function (el, options) {
				this._data.massload = {};
				parent.init.call(this, el, options);
			};
			this._load_nodes = function (nodes, callback, is_callback, force_reload) {
				var s = this.settings.massload,
					nodesString = JSON.stringify(nodes),
					toLoad = [],
					m = this._model.data,
					i, j, dom;
				if (!is_callback) {
					for(i = 0, j = nodes.length; i < j; i++) {
						if(!m[nodes[i]] || ( (!m[nodes[i]].state.loaded && !m[nodes[i]].state.failed) || force_reload) ) {
							toLoad.push(nodes[i]);
							dom = this.get_node(nodes[i], true);
							if (dom && dom.length) {
								dom.addClass("jstree-loading").attr('aria-busy',true);
							}
						}
					}
					this._data.massload = {};
					if (toLoad.length) {
						if($.isFunction(s)) {
							return s.call(this, toLoad, $.proxy(function (data) {
								var i, j;
								if(data) {
									for(i in data) {
										if(data.hasOwnProperty(i)) {
											this._data.massload[i] = data[i];
										}
									}
								}
								for(i = 0, j = nodes.length; i < j; i++) {
									dom = this.get_node(nodes[i], true);
									if (dom && dom.length) {
										dom.removeClass("jstree-loading").attr('aria-busy',false);
									}
								}
								parent._load_nodes.call(this, nodes, callback, is_callback, force_reload);
							}, this));
						}
						if(typeof s === 'object' && s && s.url) {
							s = $.extend(true, {}, s);
							if($.isFunction(s.url)) {
								s.url = s.url.call(this, toLoad);
							}
							if($.isFunction(s.data)) {
								s.data = s.data.call(this, toLoad);
							}
							return $.ajax(s)
								.done($.proxy(function (data,t,x) {
										var i, j;
										if(data) {
											for(i in data) {
												if(data.hasOwnProperty(i)) {
													this._data.massload[i] = data[i];
												}
											}
										}
										for(i = 0, j = nodes.length; i < j; i++) {
											dom = this.get_node(nodes[i], true);
											if (dom && dom.length) {
												dom.removeClass("jstree-loading").attr('aria-busy',false);
											}
										}
										parent._load_nodes.call(this, nodes, callback, is_callback, force_reload);
									}, this))
								.fail($.proxy(function (f) {
										parent._load_nodes.call(this, nodes, callback, is_callback, force_reload);
									}, this));
						}
					}
				}
				return parent._load_nodes.call(this, nodes, callback, is_callback, force_reload);
			};
			this._load_node = function (obj, callback) {
				var data = this._data.massload[obj.id],
					rslt = null, dom;
				if(data) {
					rslt = this[typeof data === 'string' ? '_append_html_data' : '_append_json_data'](
						obj,
						typeof data === 'string' ? $($.parseHTML(data)).filter(function () { return this.nodeType !== 3; }) : data,
						function (status) { callback.call(this, status); }
					);
					dom = this.get_node(obj.id, true);
					if (dom && dom.length) {
						dom.removeClass("jstree-loading").attr('aria-busy',false);
					}
					delete this._data.massload[obj.id];
					return rslt;
				}
				return parent._load_node.call(this, obj, callback);
			};
		};
	
	/**
	 * ### Search plugin
	 *
	 * Adds search functionality to jsTree.
	 */
	
		/**
		 * stores all defaults for the search plugin
		 * @name $.jstree.defaults.search
		 * @plugin search
		 */
		$.jstree.defaults.search = {
			/**
			 * a jQuery-like AJAX config, which jstree uses if a server should be queried for results.
			 *
			 * A `str` (which is the search string) parameter will be added with the request, an optional `inside` parameter will be added if the search is limited to a node id. The expected result is a JSON array with nodes that need to be opened so that matching nodes will be revealed.
			 * Leave this setting as `false` to not query the server. You can also set this to a function, which will be invoked in the instance's scope and receive 3 parameters - the search string, the callback to call with the array of nodes to load, and the optional node ID to limit the search to
			 * @name $.jstree.defaults.search.ajax
			 * @plugin search
			 */
			ajax : false,
			/**
			 * Indicates if the search should be fuzzy or not (should `chnd3` match `child node 3`). Default is `false`.
			 * @name $.jstree.defaults.search.fuzzy
			 * @plugin search
			 */
			fuzzy : false,
			/**
			 * Indicates if the search should be case sensitive. Default is `false`.
			 * @name $.jstree.defaults.search.case_sensitive
			 * @plugin search
			 */
			case_sensitive : false,
			/**
			 * Indicates if the tree should be filtered (by default) to show only matching nodes (keep in mind this can be a heavy on large trees in old browsers).
			 * This setting can be changed at runtime when calling the search method. Default is `false`.
			 * @name $.jstree.defaults.search.show_only_matches
			 * @plugin search
			 */
			show_only_matches : false,
			/**
			 * Indicates if the children of matched element are shown (when show_only_matches is true)
			 * This setting can be changed at runtime when calling the search method. Default is `false`.
			 * @name $.jstree.defaults.search.show_only_matches_children
			 * @plugin search
			 */
			show_only_matches_children : false,
			/**
			 * Indicates if all nodes opened to reveal the search result, should be closed when the search is cleared or a new search is performed. Default is `true`.
			 * @name $.jstree.defaults.search.close_opened_onclear
			 * @plugin search
			 */
			close_opened_onclear : true,
			/**
			 * Indicates if only leaf nodes should be included in search results. Default is `false`.
			 * @name $.jstree.defaults.search.search_leaves_only
			 * @plugin search
			 */
			search_leaves_only : false,
			/**
			 * If set to a function it wil be called in the instance's scope with two arguments - search string and node (where node will be every node in the structure, so use with caution).
			 * If the function returns a truthy value the node will be considered a match (it might not be displayed if search_only_leaves is set to true and the node is not a leaf). Default is `false`.
			 * @name $.jstree.defaults.search.search_callback
			 * @plugin search
			 */
			search_callback : false
		};
	
		$.jstree.plugins.search = function (options, parent) {
			this.bind = function () {
				parent.bind.call(this);
	
				this._data.search.str = "";
				this._data.search.dom = $();
				this._data.search.res = [];
				this._data.search.opn = [];
				this._data.search.som = false;
				this._data.search.smc = false;
				this._data.search.hdn = [];
	
				this.element
					.on("search.jstree", $.proxy(function (e, data) {
							if(this._data.search.som && data.res.length) {
								var m = this._model.data, i, j, p = [], k, l;
								for(i = 0, j = data.res.length; i < j; i++) {
									if(m[data.res[i]] && !m[data.res[i]].state.hidden) {
										p.push(data.res[i]);
										p = p.concat(m[data.res[i]].parents);
										if(this._data.search.smc) {
											for (k = 0, l = m[data.res[i]].children_d.length; k < l; k++) {
												if (m[m[data.res[i]].children_d[k]] && !m[m[data.res[i]].children_d[k]].state.hidden) {
													p.push(m[data.res[i]].children_d[k]);
												}
											}
										}
									}
								}
								p = $.vakata.array_remove_item($.vakata.array_unique(p), $.jstree.root);
								this._data.search.hdn = this.hide_all(true);
								this.show_node(p, true);
								this.redraw(true);
							}
						}, this))
					.on("clear_search.jstree", $.proxy(function (e, data) {
							if(this._data.search.som && data.res.length) {
								this.show_node(this._data.search.hdn, true);
								this.redraw(true);
							}
						}, this));
			};
			/**
			 * used to search the tree nodes for a given string
			 * @name search(str [, skip_async])
			 * @param {String} str the search string
			 * @param {Boolean} skip_async if set to true server will not be queried even if configured
			 * @param {Boolean} show_only_matches if set to true only matching nodes will be shown (keep in mind this can be very slow on large trees or old browsers)
			 * @param {mixed} inside an optional node to whose children to limit the search
			 * @param {Boolean} append if set to true the results of this search are appended to the previous search
			 * @plugin search
			 * @trigger search.jstree
			 */
			this.search = function (str, skip_async, show_only_matches, inside, append, show_only_matches_children) {
				if(str === false || $.trim(str.toString()) === "") {
					return this.clear_search();
				}
				inside = this.get_node(inside);
				inside = inside && inside.id ? inside.id : null;
				str = str.toString();
				var s = this.settings.search,
					a = s.ajax ? s.ajax : false,
					m = this._model.data,
					f = null,
					r = [],
					p = [], i, j;
				if(this._data.search.res.length && !append) {
					this.clear_search();
				}
				if(show_only_matches === undefined) {
					show_only_matches = s.show_only_matches;
				}
				if(show_only_matches_children === undefined) {
					show_only_matches_children = s.show_only_matches_children;
				}
				if(!skip_async && a !== false) {
					if($.isFunction(a)) {
						return a.call(this, str, $.proxy(function (d) {
								if(d && d.d) { d = d.d; }
								this._load_nodes(!$.isArray(d) ? [] : $.vakata.array_unique(d), function () {
									this.search(str, true, show_only_matches, inside, append);
								});
							}, this), inside);
					}
					else {
						a = $.extend({}, a);
						if(!a.data) { a.data = {}; }
						a.data.str = str;
						if(inside) {
							a.data.inside = inside;
						}
						return $.ajax(a)
							.fail($.proxy(function () {
								this._data.core.last_error = { 'error' : 'ajax', 'plugin' : 'search', 'id' : 'search_01', 'reason' : 'Could not load search parents', 'data' : JSON.stringify(a) };
								this.settings.core.error.call(this, this._data.core.last_error);
							}, this))
							.done($.proxy(function (d) {
								if(d && d.d) { d = d.d; }
								this._load_nodes(!$.isArray(d) ? [] : $.vakata.array_unique(d), function () {
									this.search(str, true, show_only_matches, inside, append);
								});
							}, this));
					}
				}
				if(!append) {
					this._data.search.str = str;
					this._data.search.dom = $();
					this._data.search.res = [];
					this._data.search.opn = [];
					this._data.search.som = show_only_matches;
					this._data.search.smc = show_only_matches_children;
				}
	
				f = new $.vakata.search(str, true, { caseSensitive : s.case_sensitive, fuzzy : s.fuzzy });
				$.each(m[inside ? inside : $.jstree.root].children_d, function (ii, i) {
					var v = m[i];
					if(v.text && !v.state.hidden && (!s.search_leaves_only || (v.state.loaded && v.children.length === 0)) && ( (s.search_callback && s.search_callback.call(this, str, v)) || (!s.search_callback && f.search(v.text).isMatch) ) ) {
						r.push(i);
						p = p.concat(v.parents);
					}
				});
				if(r.length) {
					p = $.vakata.array_unique(p);
					for(i = 0, j = p.length; i < j; i++) {
						if(p[i] !== $.jstree.root && m[p[i]] && this.open_node(p[i], null, 0) === true) {
							this._data.search.opn.push(p[i]);
						}
					}
					if(!append) {
						this._data.search.dom = $(this.element[0].querySelectorAll('#' + $.map(r, function (v) { return "0123456789".indexOf(v[0]) !== -1 ? '\\3' + v[0] + ' ' + v.substr(1).replace($.jstree.idregex,'\\$&') : v.replace($.jstree.idregex,'\\$&'); }).join(', #')));
						this._data.search.res = r;
					}
					else {
						this._data.search.dom = this._data.search.dom.add($(this.element[0].querySelectorAll('#' + $.map(r, function (v) { return "0123456789".indexOf(v[0]) !== -1 ? '\\3' + v[0] + ' ' + v.substr(1).replace($.jstree.idregex,'\\$&') : v.replace($.jstree.idregex,'\\$&'); }).join(', #'))));
						this._data.search.res = $.vakata.array_unique(this._data.search.res.concat(r));
					}
					this._data.search.dom.children(".jstree-anchor").addClass('jstree-search');
				}
				/**
				 * triggered after search is complete
				 * @event
				 * @name search.jstree
				 * @param {jQuery} nodes a jQuery collection of matching nodes
				 * @param {String} str the search string
				 * @param {Array} res a collection of objects represeing the matching nodes
				 * @plugin search
				 */
				this.trigger('search', { nodes : this._data.search.dom, str : str, res : this._data.search.res, show_only_matches : show_only_matches });
			};
			/**
			 * used to clear the last search (removes classes and shows all nodes if filtering is on)
			 * @name clear_search()
			 * @plugin search
			 * @trigger clear_search.jstree
			 */
			this.clear_search = function () {
				if(this.settings.search.close_opened_onclear) {
					this.close_node(this._data.search.opn, 0);
				}
				/**
				 * triggered after search is complete
				 * @event
				 * @name clear_search.jstree
				 * @param {jQuery} nodes a jQuery collection of matching nodes (the result from the last search)
				 * @param {String} str the search string (the last search string)
				 * @param {Array} res a collection of objects represeing the matching nodes (the result from the last search)
				 * @plugin search
				 */
				this.trigger('clear_search', { 'nodes' : this._data.search.dom, str : this._data.search.str, res : this._data.search.res });
				if(this._data.search.res.length) {
					this._data.search.dom = $(this.element[0].querySelectorAll('#' + $.map(this._data.search.res, function (v) {
						return "0123456789".indexOf(v[0]) !== -1 ? '\\3' + v[0] + ' ' + v.substr(1).replace($.jstree.idregex,'\\$&') : v.replace($.jstree.idregex,'\\$&');
					}).join(', #')));
					this._data.search.dom.children(".jstree-anchor").removeClass("jstree-search");
				}
				this._data.search.str = "";
				this._data.search.res = [];
				this._data.search.opn = [];
				this._data.search.dom = $();
			};
	
			this.redraw_node = function(obj, deep, callback, force_render) {
				obj = parent.redraw_node.apply(this, arguments);
				if(obj) {
					if($.inArray(obj.id, this._data.search.res) !== -1) {
						var i, j, tmp = null;
						for(i = 0, j = obj.childNodes.length; i < j; i++) {
							if(obj.childNodes[i] && obj.childNodes[i].className && obj.childNodes[i].className.indexOf("jstree-anchor") !== -1) {
								tmp = obj.childNodes[i];
								break;
							}
						}
						if(tmp) {
							tmp.className += ' jstree-search';
						}
					}
				}
				return obj;
			};
		};
	
		// helpers
		(function ($) {
			// from http://kiro.me/projects/fuse.html
			$.vakata.search = function(pattern, txt, options) {
				options = options || {};
				options = $.extend({}, $.vakata.search.defaults, options);
				if(options.fuzzy !== false) {
					options.fuzzy = true;
				}
				pattern = options.caseSensitive ? pattern : pattern.toLowerCase();
				var MATCH_LOCATION	= options.location,
					MATCH_DISTANCE	= options.distance,
					MATCH_THRESHOLD	= options.threshold,
					patternLen = pattern.length,
					matchmask, pattern_alphabet, match_bitapScore, search;
				if(patternLen > 32) {
					options.fuzzy = false;
				}
				if(options.fuzzy) {
					matchmask = 1 << (patternLen - 1);
					pattern_alphabet = (function () {
						var mask = {},
							i = 0;
						for (i = 0; i < patternLen; i++) {
							mask[pattern.charAt(i)] = 0;
						}
						for (i = 0; i < patternLen; i++) {
							mask[pattern.charAt(i)] |= 1 << (patternLen - i - 1);
						}
						return mask;
					}());
					match_bitapScore = function (e, x) {
						var accuracy = e / patternLen,
							proximity = Math.abs(MATCH_LOCATION - x);
						if(!MATCH_DISTANCE) {
							return proximity ? 1.0 : accuracy;
						}
						return accuracy + (proximity / MATCH_DISTANCE);
					};
				}
				search = function (text) {
					text = options.caseSensitive ? text : text.toLowerCase();
					if(pattern === text || text.indexOf(pattern) !== -1) {
						return {
							isMatch: true,
							score: 0
						};
					}
					if(!options.fuzzy) {
						return {
							isMatch: false,
							score: 1
						};
					}
					var i, j,
						textLen = text.length,
						scoreThreshold = MATCH_THRESHOLD,
						bestLoc = text.indexOf(pattern, MATCH_LOCATION),
						binMin, binMid,
						binMax = patternLen + textLen,
						lastRd, start, finish, rd, charMatch,
						score = 1,
						locations = [];
					if (bestLoc !== -1) {
						scoreThreshold = Math.min(match_bitapScore(0, bestLoc), scoreThreshold);
						bestLoc = text.lastIndexOf(pattern, MATCH_LOCATION + patternLen);
						if (bestLoc !== -1) {
							scoreThreshold = Math.min(match_bitapScore(0, bestLoc), scoreThreshold);
						}
					}
					bestLoc = -1;
					for (i = 0; i < patternLen; i++) {
						binMin = 0;
						binMid = binMax;
						while (binMin < binMid) {
							if (match_bitapScore(i, MATCH_LOCATION + binMid) <= scoreThreshold) {
								binMin = binMid;
							} else {
								binMax = binMid;
							}
							binMid = Math.floor((binMax - binMin) / 2 + binMin);
						}
						binMax = binMid;
						start = Math.max(1, MATCH_LOCATION - binMid + 1);
						finish = Math.min(MATCH_LOCATION + binMid, textLen) + patternLen;
						rd = new Array(finish + 2);
						rd[finish + 1] = (1 << i) - 1;
						for (j = finish; j >= start; j--) {
							charMatch = pattern_alphabet[text.charAt(j - 1)];
							if (i === 0) {
								rd[j] = ((rd[j + 1] << 1) | 1) & charMatch;
							} else {
								rd[j] = ((rd[j + 1] << 1) | 1) & charMatch | (((lastRd[j + 1] | lastRd[j]) << 1) | 1) | lastRd[j + 1];
							}
							if (rd[j] & matchmask) {
								score = match_bitapScore(i, j - 1);
								if (score <= scoreThreshold) {
									scoreThreshold = score;
									bestLoc = j - 1;
									locations.push(bestLoc);
									if (bestLoc > MATCH_LOCATION) {
										start = Math.max(1, 2 * MATCH_LOCATION - bestLoc);
									} else {
										break;
									}
								}
							}
						}
						if (match_bitapScore(i + 1, MATCH_LOCATION) > scoreThreshold) {
							break;
						}
						lastRd = rd;
					}
					return {
						isMatch: bestLoc >= 0,
						score: score
					};
				};
				return txt === true ? { 'search' : search } : search(txt);
			};
			$.vakata.search.defaults = {
				location : 0,
				distance : 100,
				threshold : 0.6,
				fuzzy : false,
				caseSensitive : false
			};
		}($));
	
		// include the search plugin by default
		// $.jstree.defaults.plugins.push("search");
	
	
	/**
	 * ### Sort plugin
	 *
	 * Automatically sorts all siblings in the tree according to a sorting function.
	 */
	
		/**
		 * the settings function used to sort the nodes.
		 * It is executed in the tree's context, accepts two nodes as arguments and should return `1` or `-1`.
		 * @name $.jstree.defaults.sort
		 * @plugin sort
		 */
		$.jstree.defaults.sort = function (a, b) {
			//return this.get_type(a) === this.get_type(b) ? (this.get_text(a) > this.get_text(b) ? 1 : -1) : this.get_type(a) >= this.get_type(b);
			return this.get_text(a) > this.get_text(b) ? 1 : -1;
		};
		$.jstree.plugins.sort = function (options, parent) {
			this.bind = function () {
				parent.bind.call(this);
				this.element
					.on("model.jstree", $.proxy(function (e, data) {
							this.sort(data.parent, true);
						}, this))
					.on("rename_node.jstree create_node.jstree", $.proxy(function (e, data) {
							this.sort(data.parent || data.node.parent, false);
							this.redraw_node(data.parent || data.node.parent, true);
						}, this))
					.on("move_node.jstree copy_node.jstree", $.proxy(function (e, data) {
							this.sort(data.parent, false);
							this.redraw_node(data.parent, true);
						}, this));
			};
			/**
			 * used to sort a node's children
			 * @private
			 * @name sort(obj [, deep])
			 * @param  {mixed} obj the node
			 * @param {Boolean} deep if set to `true` nodes are sorted recursively.
			 * @plugin sort
			 * @trigger search.jstree
			 */
			this.sort = function (obj, deep) {
				var i, j;
				obj = this.get_node(obj);
				if(obj && obj.children && obj.children.length) {
					obj.children.sort($.proxy(this.settings.sort, this));
					if(deep) {
						for(i = 0, j = obj.children_d.length; i < j; i++) {
							this.sort(obj.children_d[i], false);
						}
					}
				}
			};
		};
	
		// include the sort plugin by default
		// $.jstree.defaults.plugins.push("sort");
	
	/**
	 * ### State plugin
	 *
	 * Saves the state of the tree (selected nodes, opened nodes) on the user's computer using available options (localStorage, cookies, etc)
	 */
	
		var to = false;
		/**
		 * stores all defaults for the state plugin
		 * @name $.jstree.defaults.state
		 * @plugin state
		 */
		$.jstree.defaults.state = {
			/**
			 * A string for the key to use when saving the current tree (change if using multiple trees in your project). Defaults to `jstree`.
			 * @name $.jstree.defaults.state.key
			 * @plugin state
			 */
			key		: 'jstree',
			/**
			 * A space separated list of events that trigger a state save. Defaults to `changed.jstree open_node.jstree close_node.jstree`.
			 * @name $.jstree.defaults.state.events
			 * @plugin state
			 */
			events	: 'changed.jstree open_node.jstree close_node.jstree check_node.jstree uncheck_node.jstree',
			/**
			 * Time in milliseconds after which the state will expire. Defaults to 'false' meaning - no expire.
			 * @name $.jstree.defaults.state.ttl
			 * @plugin state
			 */
			ttl		: false,
			/**
			 * A function that will be executed prior to restoring state with one argument - the state object. Can be used to clear unwanted parts of the state.
			 * @name $.jstree.defaults.state.filter
			 * @plugin state
			 */
			filter	: false
		};
		$.jstree.plugins.state = function (options, parent) {
			this.bind = function () {
				parent.bind.call(this);
				var bind = $.proxy(function () {
					this.element.on(this.settings.state.events, $.proxy(function () {
						if(to) { clearTimeout(to); }
						to = setTimeout($.proxy(function () { this.save_state(); }, this), 100);
					}, this));
					/**
					 * triggered when the state plugin is finished restoring the state (and immediately after ready if there is no state to restore).
					 * @event
					 * @name state_ready.jstree
					 * @plugin state
					 */
					this.trigger('state_ready');
				}, this);
				this.element
					.on("ready.jstree", $.proxy(function (e, data) {
							this.element.one("restore_state.jstree", bind);
							if(!this.restore_state()) { bind(); }
						}, this));
			};
			/**
			 * save the state
			 * @name save_state()
			 * @plugin state
			 */
			this.save_state = function () {
				var st = { 'state' : this.get_state(), 'ttl' : this.settings.state.ttl, 'sec' : +(new Date()) };
				$.vakata.storage.set(this.settings.state.key, JSON.stringify(st));
			};
			/**
			 * restore the state from the user's computer
			 * @name restore_state()
			 * @plugin state
			 */
			this.restore_state = function () {
				var k = $.vakata.storage.get(this.settings.state.key);
				if(!!k) { try { k = JSON.parse(k); } catch(ex) { return false; } }
				if(!!k && k.ttl && k.sec && +(new Date()) - k.sec > k.ttl) { return false; }
				if(!!k && k.state) { k = k.state; }
				if(!!k && $.isFunction(this.settings.state.filter)) { k = this.settings.state.filter.call(this, k); }
				if(!!k) {
					this.element.one("set_state.jstree", function (e, data) { data.instance.trigger('restore_state', { 'state' : $.extend(true, {}, k) }); });
					this.set_state(k);
					return true;
				}
				return false;
			};
			/**
			 * clear the state on the user's computer
			 * @name clear_state()
			 * @plugin state
			 */
			this.clear_state = function () {
				return $.vakata.storage.del(this.settings.state.key);
			};
		};
	
		(function ($, undefined) {
			$.vakata.storage = {
				// simply specifying the functions in FF throws an error
				set : function (key, val) { return window.localStorage.setItem(key, val); },
				get : function (key) { return window.localStorage.getItem(key); },
				del : function (key) { return window.localStorage.removeItem(key); }
			};
		}($));
	
		// include the state plugin by default
		// $.jstree.defaults.plugins.push("state");
	
	/**
	 * ### Types plugin
	 *
	 * Makes it possible to add predefined types for groups of nodes, which make it possible to easily control nesting rules and icon for each group.
	 */
	
		/**
		 * An object storing all types as key value pairs, where the key is the type name and the value is an object that could contain following keys (all optional).
		 *
		 * * `max_children` the maximum number of immediate children this node type can have. Do not specify or set to `-1` for unlimited.
		 * * `max_depth` the maximum number of nesting this node type can have. A value of `1` would mean that the node can have children, but no grandchildren. Do not specify or set to `-1` for unlimited.
		 * * `valid_children` an array of node type strings, that nodes of this type can have as children. Do not specify or set to `-1` for no limits.
		 * * `icon` a string - can be a path to an icon or a className, if using an image that is in the current directory use a `./` prefix, otherwise it will be detected as a class. Omit to use the default icon from your theme.
		 * * `li_attr` an object of values which will be used to add HTML attributes on the resulting LI DOM node (merged with the node's own data)
		 * * `a_attr` an object of values which will be used to add HTML attributes on the resulting A DOM node (merged with the node's own data)
		 *
		 * There are two predefined types:
		 *
		 * * `#` represents the root of the tree, for example `max_children` would control the maximum number of root nodes.
		 * * `default` represents the default node - any settings here will be applied to all nodes that do not have a type specified.
		 *
		 * @name $.jstree.defaults.types
		 * @plugin types
		 */
		$.jstree.defaults.types = {
			'default' : {}
		};
		$.jstree.defaults.types[$.jstree.root] = {};
	
		$.jstree.plugins.types = function (options, parent) {
			this.init = function (el, options) {
				var i, j;
				if(options && options.types && options.types['default']) {
					for(i in options.types) {
						if(i !== "default" && i !== $.jstree.root && options.types.hasOwnProperty(i)) {
							for(j in options.types['default']) {
								if(options.types['default'].hasOwnProperty(j) && options.types[i][j] === undefined) {
									options.types[i][j] = options.types['default'][j];
								}
							}
						}
					}
				}
				parent.init.call(this, el, options);
				this._model.data[$.jstree.root].type = $.jstree.root;
			};
			this.refresh = function (skip_loading, forget_state) {
				parent.refresh.call(this, skip_loading, forget_state);
				this._model.data[$.jstree.root].type = $.jstree.root;
			};
			this.bind = function () {
				this.element
					.on('model.jstree', $.proxy(function (e, data) {
							var m = this._model.data,
								dpc = data.nodes,
								t = this.settings.types,
								i, j, c = 'default', k;
							for(i = 0, j = dpc.length; i < j; i++) {
								c = 'default';
								if(m[dpc[i]].original && m[dpc[i]].original.type && t[m[dpc[i]].original.type]) {
									c = m[dpc[i]].original.type;
								}
								if(m[dpc[i]].data && m[dpc[i]].data.jstree && m[dpc[i]].data.jstree.type && t[m[dpc[i]].data.jstree.type]) {
									c = m[dpc[i]].data.jstree.type;
								}
								m[dpc[i]].type = c;
								if(m[dpc[i]].icon === true && t[c].icon !== undefined) {
									m[dpc[i]].icon = t[c].icon;
								}
								if(t[c].li_attr !== undefined && typeof t[c].li_attr === 'object') {
									for (k in t[c].li_attr) {
										if (t[c].li_attr.hasOwnProperty(k)) {
											if (k === 'id') {
												continue;
											}
											else if (m[dpc[i]].li_attr[k] === undefined) {
												m[dpc[i]].li_attr[k] = t[c].li_attr[k];
											}
											else if (k === 'class') {
												m[dpc[i]].li_attr['class'] = t[c].li_attr['class'] + ' ' + m[dpc[i]].li_attr['class'];
											}
										}
									}
								}
								if(t[c].a_attr !== undefined && typeof t[c].a_attr === 'object') {
									for (k in t[c].a_attr) {
										if (t[c].a_attr.hasOwnProperty(k)) {
											if (k === 'id') {
												continue;
											}
											else if (m[dpc[i]].a_attr[k] === undefined) {
												m[dpc[i]].a_attr[k] = t[c].a_attr[k];
											}
											else if (k === 'href' && m[dpc[i]].a_attr[k] === '#') {
												m[dpc[i]].a_attr['href'] = t[c].a_attr['href'];
											}
											else if (k === 'class') {
												m[dpc[i]].a_attr['class'] = t[c].a_attr['class'] + ' ' + m[dpc[i]].a_attr['class'];
											}
										}
									}
								}
							}
							m[$.jstree.root].type = $.jstree.root;
						}, this));
				parent.bind.call(this);
			};
			this.get_json = function (obj, options, flat) {
				var i, j,
					m = this._model.data,
					opt = options ? $.extend(true, {}, options, {no_id:false}) : {},
					tmp = parent.get_json.call(this, obj, opt, flat);
				if(tmp === false) { return false; }
				if($.isArray(tmp)) {
					for(i = 0, j = tmp.length; i < j; i++) {
						tmp[i].type = tmp[i].id && m[tmp[i].id] && m[tmp[i].id].type ? m[tmp[i].id].type : "default";
						if(options && options.no_id) {
							delete tmp[i].id;
							if(tmp[i].li_attr && tmp[i].li_attr.id) {
								delete tmp[i].li_attr.id;
							}
							if(tmp[i].a_attr && tmp[i].a_attr.id) {
								delete tmp[i].a_attr.id;
							}
						}
					}
				}
				else {
					tmp.type = tmp.id && m[tmp.id] && m[tmp.id].type ? m[tmp.id].type : "default";
					if(options && options.no_id) {
						tmp = this._delete_ids(tmp);
					}
				}
				return tmp;
			};
			this._delete_ids = function (tmp) {
				if($.isArray(tmp)) {
					for(var i = 0, j = tmp.length; i < j; i++) {
						tmp[i] = this._delete_ids(tmp[i]);
					}
					return tmp;
				}
				delete tmp.id;
				if(tmp.li_attr && tmp.li_attr.id) {
					delete tmp.li_attr.id;
				}
				if(tmp.a_attr && tmp.a_attr.id) {
					delete tmp.a_attr.id;
				}
				if(tmp.children && $.isArray(tmp.children)) {
					tmp.children = this._delete_ids(tmp.children);
				}
				return tmp;
			};
			this.check = function (chk, obj, par, pos, more) {
				if(parent.check.call(this, chk, obj, par, pos, more) === false) { return false; }
				obj = obj && obj.id ? obj : this.get_node(obj);
				par = par && par.id ? par : this.get_node(par);
				var m = obj && obj.id ? (more && more.origin ? more.origin : $.jstree.reference(obj.id)) : null, tmp, d, i, j;
				m = m && m._model && m._model.data ? m._model.data : null;
				switch(chk) {
					case "create_node":
					case "move_node":
					case "copy_node":
						if(chk !== 'move_node' || $.inArray(obj.id, par.children) === -1) {
							tmp = this.get_rules(par);
							if(tmp.max_children !== undefined && tmp.max_children !== -1 && tmp.max_children === par.children.length) {
								this._data.core.last_error = { 'error' : 'check', 'plugin' : 'types', 'id' : 'types_01', 'reason' : 'max_children prevents function: ' + chk, 'data' : JSON.stringify({ 'chk' : chk, 'pos' : pos, 'obj' : obj && obj.id ? obj.id : false, 'par' : par && par.id ? par.id : false }) };
								return false;
							}
							if(tmp.valid_children !== undefined && tmp.valid_children !== -1 && $.inArray((obj.type || 'default'), tmp.valid_children) === -1) {
								this._data.core.last_error = { 'error' : 'check', 'plugin' : 'types', 'id' : 'types_02', 'reason' : 'valid_children prevents function: ' + chk, 'data' : JSON.stringify({ 'chk' : chk, 'pos' : pos, 'obj' : obj && obj.id ? obj.id : false, 'par' : par && par.id ? par.id : false }) };
								return false;
							}
							if(m && obj.children_d && obj.parents) {
								d = 0;
								for(i = 0, j = obj.children_d.length; i < j; i++) {
									d = Math.max(d, m[obj.children_d[i]].parents.length);
								}
								d = d - obj.parents.length + 1;
							}
							if(d <= 0 || d === undefined) { d = 1; }
							do {
								if(tmp.max_depth !== undefined && tmp.max_depth !== -1 && tmp.max_depth < d) {
									this._data.core.last_error = { 'error' : 'check', 'plugin' : 'types', 'id' : 'types_03', 'reason' : 'max_depth prevents function: ' + chk, 'data' : JSON.stringify({ 'chk' : chk, 'pos' : pos, 'obj' : obj && obj.id ? obj.id : false, 'par' : par && par.id ? par.id : false }) };
									return false;
								}
								par = this.get_node(par.parent);
								tmp = this.get_rules(par);
								d++;
							} while(par);
						}
						break;
				}
				return true;
			};
			/**
			 * used to retrieve the type settings object for a node
			 * @name get_rules(obj)
			 * @param {mixed} obj the node to find the rules for
			 * @return {Object}
			 * @plugin types
			 */
			this.get_rules = function (obj) {
				obj = this.get_node(obj);
				if(!obj) { return false; }
				var tmp = this.get_type(obj, true);
				if(tmp.max_depth === undefined) { tmp.max_depth = -1; }
				if(tmp.max_children === undefined) { tmp.max_children = -1; }
				if(tmp.valid_children === undefined) { tmp.valid_children = -1; }
				return tmp;
			};
			/**
			 * used to retrieve the type string or settings object for a node
			 * @name get_type(obj [, rules])
			 * @param {mixed} obj the node to find the rules for
			 * @param {Boolean} rules if set to `true` instead of a string the settings object will be returned
			 * @return {String|Object}
			 * @plugin types
			 */
			this.get_type = function (obj, rules) {
				obj = this.get_node(obj);
				return (!obj) ? false : ( rules ? $.extend({ 'type' : obj.type }, this.settings.types[obj.type]) : obj.type);
			};
			/**
			 * used to change a node's type
			 * @name set_type(obj, type)
			 * @param {mixed} obj the node to change
			 * @param {String} type the new type
			 * @plugin types
			 */
			this.set_type = function (obj, type) {
				var m = this._model.data, t, t1, t2, old_type, old_icon, k, d, a;
				if($.isArray(obj)) {
					obj = obj.slice();
					for(t1 = 0, t2 = obj.length; t1 < t2; t1++) {
						this.set_type(obj[t1], type);
					}
					return true;
				}
				t = this.settings.types;
				obj = this.get_node(obj);
				if(!t[type] || !obj) { return false; }
				d = this.get_node(obj, true);
				if (d && d.length) {
					a = d.children('.jstree-anchor');
				}
				old_type = obj.type;
				old_icon = this.get_icon(obj);
				obj.type = type;
				if(old_icon === true || (t[old_type] && t[old_type].icon !== undefined && old_icon === t[old_type].icon)) {
					this.set_icon(obj, t[type].icon !== undefined ? t[type].icon : true);
				}
	
				// remove old type props
				if(t[old_type].li_attr !== undefined && typeof t[old_type].li_attr === 'object') {
					for (k in t[old_type].li_attr) {
						if (t[old_type].li_attr.hasOwnProperty(k)) {
							if (k === 'id') {
								continue;
							}
							else if (k === 'class') {
								m[obj.id].li_attr['class'] = (m[obj.id].li_attr['class'] || '').replace(t[old_type].li_attr[k], '');
								if (d) { d.removeClass(t[old_type].li_attr[k]); }
							}
							else if (m[obj.id].li_attr[k] === t[old_type].li_attr[k]) {
								m[obj.id].li_attr[k] = null;
								if (d) { d.removeAttr(k); }
							}
						}
					}
				}
				if(t[old_type].a_attr !== undefined && typeof t[old_type].a_attr === 'object') {
					for (k in t[old_type].a_attr) {
						if (t[old_type].a_attr.hasOwnProperty(k)) {
							if (k === 'id') {
								continue;
							}
							else if (k === 'class') {
								m[obj.id].a_attr['class'] = (m[obj.id].a_attr['class'] || '').replace(t[old_type].a_attr[k], '');
								if (a) { a.removeClass(t[old_type].a_attr[k]); }
							}
							else if (m[obj.id].a_attr[k] === t[old_type].a_attr[k]) {
								if (k === 'href') {
									m[obj.id].a_attr[k] = '#';
									if (a) { a.attr('href', '#'); }
								}
								else {
									delete m[obj.id].a_attr[k];
									if (a) { a.removeAttr(k); }
								}
							}
						}
					}
				}
	
				// add new props
				if(t[type].li_attr !== undefined && typeof t[type].li_attr === 'object') {
					for (k in t[type].li_attr) {
						if (t[type].li_attr.hasOwnProperty(k)) {
							if (k === 'id') {
								continue;
							}
							else if (m[obj.id].li_attr[k] === undefined) {
								m[obj.id].li_attr[k] = t[type].li_attr[k];
								if (d) {
									if (k === 'class') {
										d.addClass(t[type].li_attr[k]);
									}
									else {
										d.attr(k, t[type].li_attr[k]);
									}
								}
							}
							else if (k === 'class') {
								m[obj.id].li_attr['class'] = t[type].li_attr[k] + ' ' + m[obj.id].li_attr['class'];
								if (d) { d.addClass(t[type].li_attr[k]); }
							}
						}
					}
				}
				if(t[type].a_attr !== undefined && typeof t[type].a_attr === 'object') {
					for (k in t[type].a_attr) {
						if (t[type].a_attr.hasOwnProperty(k)) {
							if (k === 'id') {
								continue;
							}
							else if (m[obj.id].a_attr[k] === undefined) {
								m[obj.id].a_attr[k] = t[type].a_attr[k];
								if (a) {
									if (k === 'class') {
										a.addClass(t[type].a_attr[k]);
									}
									else {
										a.attr(k, t[type].a_attr[k]);
									}
								}
							}
							else if (k === 'href' && m[obj.id].a_attr[k] === '#') {
								m[obj.id].a_attr['href'] = t[type].a_attr['href'];
								if (a) { a.attr('href', t[type].a_attr['href']); }
							}
							else if (k === 'class') {
								m[obj.id].a_attr['class'] = t[type].a_attr['class'] + ' ' + m[obj.id].a_attr['class'];
								if (a) { a.addClass(t[type].a_attr[k]); }
							}
						}
					}
				}
	
				return true;
			};
		};
		// include the types plugin by default
		// $.jstree.defaults.plugins.push("types");
	
	
	/**
	 * ### Unique plugin
	 *
	 * Enforces that no nodes with the same name can coexist as siblings.
	 */
	
		/**
		 * stores all defaults for the unique plugin
		 * @name $.jstree.defaults.unique
		 * @plugin unique
		 */
		$.jstree.defaults.unique = {
			/**
			 * Indicates if the comparison should be case sensitive. Default is `false`.
			 * @name $.jstree.defaults.unique.case_sensitive
			 * @plugin unique
			 */
			case_sensitive : false,
			/**
			 * A callback executed in the instance's scope when a new node is created and the name is already taken, the two arguments are the conflicting name and the counter. The default will produce results like `New node (2)`.
			 * @name $.jstree.defaults.unique.duplicate
			 * @plugin unique
			 */
			duplicate : function (name, counter) {
				return name + ' (' + counter + ')';
			}
		};
	
		$.jstree.plugins.unique = function (options, parent) {
			this.check = function (chk, obj, par, pos, more) {
				if(parent.check.call(this, chk, obj, par, pos, more) === false) { return false; }
				obj = obj && obj.id ? obj : this.get_node(obj);
				par = par && par.id ? par : this.get_node(par);
				if(!par || !par.children) { return true; }
				var n = chk === "rename_node" ? pos : obj.text,
					c = [],
					s = this.settings.unique.case_sensitive,
					m = this._model.data, i, j;
				for(i = 0, j = par.children.length; i < j; i++) {
					c.push(s ? m[par.children[i]].text : m[par.children[i]].text.toLowerCase());
				}
				if(!s) { n = n.toLowerCase(); }
				switch(chk) {
					case "delete_node":
						return true;
					case "rename_node":
						i = ($.inArray(n, c) === -1 || (obj.text && obj.text[ s ? 'toString' : 'toLowerCase']() === n));
						if(!i) {
							this._data.core.last_error = { 'error' : 'check', 'plugin' : 'unique', 'id' : 'unique_01', 'reason' : 'Child with name ' + n + ' already exists. Preventing: ' + chk, 'data' : JSON.stringify({ 'chk' : chk, 'pos' : pos, 'obj' : obj && obj.id ? obj.id : false, 'par' : par && par.id ? par.id : false }) };
						}
						return i;
					case "create_node":
						i = ($.inArray(n, c) === -1);
						if(!i) {
							this._data.core.last_error = { 'error' : 'check', 'plugin' : 'unique', 'id' : 'unique_04', 'reason' : 'Child with name ' + n + ' already exists. Preventing: ' + chk, 'data' : JSON.stringify({ 'chk' : chk, 'pos' : pos, 'obj' : obj && obj.id ? obj.id : false, 'par' : par && par.id ? par.id : false }) };
						}
						return i;
					case "copy_node":
						i = ($.inArray(n, c) === -1);
						if(!i) {
							this._data.core.last_error = { 'error' : 'check', 'plugin' : 'unique', 'id' : 'unique_02', 'reason' : 'Child with name ' + n + ' already exists. Preventing: ' + chk, 'data' : JSON.stringify({ 'chk' : chk, 'pos' : pos, 'obj' : obj && obj.id ? obj.id : false, 'par' : par && par.id ? par.id : false }) };
						}
						return i;
					case "move_node":
						i = ( (obj.parent === par.id && (!more || !more.is_multi)) || $.inArray(n, c) === -1);
						if(!i) {
							this._data.core.last_error = { 'error' : 'check', 'plugin' : 'unique', 'id' : 'unique_03', 'reason' : 'Child with name ' + n + ' already exists. Preventing: ' + chk, 'data' : JSON.stringify({ 'chk' : chk, 'pos' : pos, 'obj' : obj && obj.id ? obj.id : false, 'par' : par && par.id ? par.id : false }) };
						}
						return i;
				}
				return true;
			};
			this.create_node = function (par, node, pos, callback, is_loaded) {
				if(!node || node.text === undefined) {
					if(par === null) {
						par = $.jstree.root;
					}
					par = this.get_node(par);
					if(!par) {
						return parent.create_node.call(this, par, node, pos, callback, is_loaded);
					}
					pos = pos === undefined ? "last" : pos;
					if(!pos.toString().match(/^(before|after)$/) && !is_loaded && !this.is_loaded(par)) {
						return parent.create_node.call(this, par, node, pos, callback, is_loaded);
					}
					if(!node) { node = {}; }
					var tmp, n, dpc, i, j, m = this._model.data, s = this.settings.unique.case_sensitive, cb = this.settings.unique.duplicate;
					n = tmp = this.get_string('New node');
					dpc = [];
					for(i = 0, j = par.children.length; i < j; i++) {
						dpc.push(s ? m[par.children[i]].text : m[par.children[i]].text.toLowerCase());
					}
					i = 1;
					while($.inArray(s ? n : n.toLowerCase(), dpc) !== -1) {
						n = cb.call(this, tmp, (++i)).toString();
					}
					node.text = n;
				}
				return parent.create_node.call(this, par, node, pos, callback, is_loaded);
			};
		};
	
		// include the unique plugin by default
		// $.jstree.defaults.plugins.push("unique");
	
	
	/**
	 * ### Wholerow plugin
	 *
	 * Makes each node appear block level. Making selection easier. May cause slow down for large trees in old browsers.
	 */
	
		var div = document.createElement('DIV');
		div.setAttribute('unselectable','on');
		div.setAttribute('role','presentation');
		div.className = 'jstree-wholerow';
		div.innerHTML = '&#160;';
		$.jstree.plugins.wholerow = function (options, parent) {
			this.bind = function () {
				parent.bind.call(this);
	
				this.element
					.on('ready.jstree set_state.jstree', $.proxy(function () {
							this.hide_dots();
						}, this))
					.on("init.jstree loading.jstree ready.jstree", $.proxy(function () {
							//div.style.height = this._data.core.li_height + 'px';
							this.get_container_ul().addClass('jstree-wholerow-ul');
						}, this))
					.on("deselect_all.jstree", $.proxy(function (e, data) {
							this.element.find('.jstree-wholerow-clicked').removeClass('jstree-wholerow-clicked');
						}, this))
					.on("changed.jstree", $.proxy(function (e, data) {
							this.element.find('.jstree-wholerow-clicked').removeClass('jstree-wholerow-clicked');
							var tmp = false, i, j;
							for(i = 0, j = data.selected.length; i < j; i++) {
								tmp = this.get_node(data.selected[i], true);
								if(tmp && tmp.length) {
									tmp.children('.jstree-wholerow').addClass('jstree-wholerow-clicked');
								}
							}
						}, this))
					.on("open_node.jstree", $.proxy(function (e, data) {
							this.get_node(data.node, true).find('.jstree-clicked').parent().children('.jstree-wholerow').addClass('jstree-wholerow-clicked');
						}, this))
					.on("hover_node.jstree dehover_node.jstree", $.proxy(function (e, data) {
							if(e.type === "hover_node" && this.is_disabled(data.node)) { return; }
							this.get_node(data.node, true).children('.jstree-wholerow')[e.type === "hover_node"?"addClass":"removeClass"]('jstree-wholerow-hovered');
						}, this))
					.on("contextmenu.jstree", ".jstree-wholerow", $.proxy(function (e) {
							if (this._data.contextmenu) {
								e.preventDefault();
								var tmp = $.Event('contextmenu', { metaKey : e.metaKey, ctrlKey : e.ctrlKey, altKey : e.altKey, shiftKey : e.shiftKey, pageX : e.pageX, pageY : e.pageY });
								$(e.currentTarget).closest(".jstree-node").children(".jstree-anchor").first().trigger(tmp);
							}
						}, this))
					/*!
					.on("mousedown.jstree touchstart.jstree", ".jstree-wholerow", function (e) {
							if(e.target === e.currentTarget) {
								var a = $(e.currentTarget).closest(".jstree-node").children(".jstree-anchor");
								e.target = a[0];
								a.trigger(e);
							}
						})
					*/
					.on("click.jstree", ".jstree-wholerow", function (e) {
							e.stopImmediatePropagation();
							var tmp = $.Event('click', { metaKey : e.metaKey, ctrlKey : e.ctrlKey, altKey : e.altKey, shiftKey : e.shiftKey });
							$(e.currentTarget).closest(".jstree-node").children(".jstree-anchor").first().trigger(tmp).focus();
						})
					.on("click.jstree", ".jstree-leaf > .jstree-ocl", $.proxy(function (e) {
							e.stopImmediatePropagation();
							var tmp = $.Event('click', { metaKey : e.metaKey, ctrlKey : e.ctrlKey, altKey : e.altKey, shiftKey : e.shiftKey });
							$(e.currentTarget).closest(".jstree-node").children(".jstree-anchor").first().trigger(tmp).focus();
						}, this))
					.on("mouseover.jstree", ".jstree-wholerow, .jstree-icon", $.proxy(function (e) {
							e.stopImmediatePropagation();
							if(!this.is_disabled(e.currentTarget)) {
								this.hover_node(e.currentTarget);
							}
							return false;
						}, this))
					.on("mouseleave.jstree", ".jstree-node", $.proxy(function (e) {
							this.dehover_node(e.currentTarget);
						}, this));
			};
			this.teardown = function () {
				if(this.settings.wholerow) {
					this.element.find(".jstree-wholerow").remove();
				}
				parent.teardown.call(this);
			};
			this.redraw_node = function(obj, deep, callback, force_render) {
				obj = parent.redraw_node.apply(this, arguments);
				if(obj) {
					var tmp = div.cloneNode(true);
					//tmp.style.height = this._data.core.li_height + 'px';
					if($.inArray(obj.id, this._data.core.selected) !== -1) { tmp.className += ' jstree-wholerow-clicked'; }
					if(this._data.core.focused && this._data.core.focused === obj.id) { tmp.className += ' jstree-wholerow-hovered'; }
					obj.insertBefore(tmp, obj.childNodes[0]);
				}
				return obj;
			};
		};
		// include the wholerow plugin by default
		// $.jstree.defaults.plugins.push("wholerow");
		if(document.registerElement && Object && Object.create) {
			var proto = Object.create(HTMLElement.prototype);
			proto.createdCallback = function () {
				var c = { core : {}, plugins : [] }, i;
				for(i in $.jstree.plugins) {
					if($.jstree.plugins.hasOwnProperty(i) && this.attributes[i]) {
						c.plugins.push(i);
						if(this.getAttribute(i) && JSON.parse(this.getAttribute(i))) {
							c[i] = JSON.parse(this.getAttribute(i));
						}
					}
				}
				for(i in $.jstree.defaults.core) {
					if($.jstree.defaults.core.hasOwnProperty(i) && this.attributes[i]) {
						c.core[i] = JSON.parse(this.getAttribute(i)) || this.getAttribute(i);
					}
				}
				$(this).jstree(c);
			};
			// proto.attributeChangedCallback = function (name, previous, value) { };
			try {
				document.registerElement("vakata-jstree", { prototype: proto });
			} catch(ignore) { }
		}
	
	}));

/***/ },

/***/ 108:
/***/ function(module, exports, __webpack_require__) {

	__webpack_require__(109);
	module.exports = __webpack_require__(112).Array.find;

/***/ },

/***/ 109:
/***/ function(module, exports, __webpack_require__) {

	'use strict';
	// 22.1.3.8 Array.prototype.find(predicate, thisArg = undefined)
	var $export = __webpack_require__(110)
	  , $find   = __webpack_require__(128)(5)
	  , KEY     = 'find'
	  , forced  = true;
	// Shouldn't skip holes
	if(KEY in [])Array(1)[KEY](function(){ forced = false; });
	$export($export.P + $export.F * forced, 'Array', {
	  find: function find(callbackfn/*, that = undefined */){
	    return $find(this, callbackfn, arguments.length > 1 ? arguments[1] : undefined);
	  }
	});
	__webpack_require__(140)(KEY);

/***/ },

/***/ 110:
/***/ function(module, exports, __webpack_require__) {

	var global    = __webpack_require__(111)
	  , core      = __webpack_require__(112)
	  , hide      = __webpack_require__(113)
	  , redefine  = __webpack_require__(123)
	  , ctx       = __webpack_require__(126)
	  , PROTOTYPE = 'prototype';
	
	var $export = function(type, name, source){
	  var IS_FORCED = type & $export.F
	    , IS_GLOBAL = type & $export.G
	    , IS_STATIC = type & $export.S
	    , IS_PROTO  = type & $export.P
	    , IS_BIND   = type & $export.B
	    , target    = IS_GLOBAL ? global : IS_STATIC ? global[name] || (global[name] = {}) : (global[name] || {})[PROTOTYPE]
	    , exports   = IS_GLOBAL ? core : core[name] || (core[name] = {})
	    , expProto  = exports[PROTOTYPE] || (exports[PROTOTYPE] = {})
	    , key, own, out, exp;
	  if(IS_GLOBAL)source = name;
	  for(key in source){
	    // contains in native
	    own = !IS_FORCED && target && target[key] !== undefined;
	    // export native or passed
	    out = (own ? target : source)[key];
	    // bind timers to global for call from export context
	    exp = IS_BIND && own ? ctx(out, global) : IS_PROTO && typeof out == 'function' ? ctx(Function.call, out) : out;
	    // extend global
	    if(target)redefine(target, key, out, type & $export.U);
	    // export
	    if(exports[key] != out)hide(exports, key, exp);
	    if(IS_PROTO && expProto[key] != out)expProto[key] = out;
	  }
	};
	global.core = core;
	// type bitmap
	$export.F = 1;   // forced
	$export.G = 2;   // global
	$export.S = 4;   // static
	$export.P = 8;   // proto
	$export.B = 16;  // bind
	$export.W = 32;  // wrap
	$export.U = 64;  // safe
	$export.R = 128; // real proto method for `library` 
	module.exports = $export;

/***/ },

/***/ 111:
22,

/***/ 112:
11,

/***/ 113:
[336, 114, 122, 118],

/***/ 114:
[337, 115, 117, 121, 118],

/***/ 115:
[338, 116],

/***/ 116:
28,

/***/ 117:
[339, 118, 119, 120],

/***/ 118:
[340, 119],

/***/ 119:
31,

/***/ 120:
[341, 116, 111],

/***/ 121:
[342, 116],

/***/ 122:
34,

/***/ 123:
/***/ function(module, exports, __webpack_require__) {

	var global    = __webpack_require__(111)
	  , hide      = __webpack_require__(113)
	  , has       = __webpack_require__(124)
	  , SRC       = __webpack_require__(125)('src')
	  , TO_STRING = 'toString'
	  , $toString = Function[TO_STRING]
	  , TPL       = ('' + $toString).split(TO_STRING);
	
	__webpack_require__(112).inspectSource = function(it){
	  return $toString.call(it);
	};
	
	(module.exports = function(O, key, val, safe){
	  var isFunction = typeof val == 'function';
	  if(isFunction)has(val, 'name') || hide(val, 'name', key);
	  if(O[key] === val)return;
	  if(isFunction)has(val, SRC) || hide(val, SRC, O[key] ? '' + O[key] : TPL.join(String(key)));
	  if(O === global){
	    O[key] = val;
	  } else {
	    if(!safe){
	      delete O[key];
	      hide(O, key, val);
	    } else {
	      if(O[key])O[key] = val;
	      else hide(O, key, val);
	    }
	  }
	// add fake Function#toString for correct work wrapped methods / constructors with methods like LoDash isNative
	})(Function.prototype, TO_STRING, function toString(){
	  return typeof this == 'function' && this[SRC] || $toString.call(this);
	});

/***/ },

/***/ 124:
36,

/***/ 125:
51,

/***/ 126:
[335, 127],

/***/ 127:
24,

/***/ 128:
/***/ function(module, exports, __webpack_require__) {

	// 0 -> Array#forEach
	// 1 -> Array#map
	// 2 -> Array#filter
	// 3 -> Array#some
	// 4 -> Array#every
	// 5 -> Array#find
	// 6 -> Array#findIndex
	var ctx      = __webpack_require__(126)
	  , IObject  = __webpack_require__(129)
	  , toObject = __webpack_require__(131)
	  , toLength = __webpack_require__(133)
	  , asc      = __webpack_require__(135);
	module.exports = function(TYPE, $create){
	  var IS_MAP        = TYPE == 1
	    , IS_FILTER     = TYPE == 2
	    , IS_SOME       = TYPE == 3
	    , IS_EVERY      = TYPE == 4
	    , IS_FIND_INDEX = TYPE == 6
	    , NO_HOLES      = TYPE == 5 || IS_FIND_INDEX
	    , create        = $create || asc;
	  return function($this, callbackfn, that){
	    var O      = toObject($this)
	      , self   = IObject(O)
	      , f      = ctx(callbackfn, that, 3)
	      , length = toLength(self.length)
	      , index  = 0
	      , result = IS_MAP ? create($this, length) : IS_FILTER ? create($this, 0) : undefined
	      , val, res;
	    for(;length > index; index++)if(NO_HOLES || index in self){
	      val = self[index];
	      res = f(val, index, O);
	      if(TYPE){
	        if(IS_MAP)result[index] = res;            // map
	        else if(res)switch(TYPE){
	          case 3: return true;                    // some
	          case 5: return val;                     // find
	          case 6: return index;                   // findIndex
	          case 2: result.push(val);               // filter
	        } else if(IS_EVERY)return false;          // every
	      }
	    }
	    return IS_FIND_INDEX ? -1 : IS_SOME || IS_EVERY ? IS_EVERY : result;
	  };
	};

/***/ },

/***/ 129:
[332, 130],

/***/ 130:
45,

/***/ 131:
[331, 132],

/***/ 132:
18,

/***/ 133:
[333, 134],

/***/ 134:
17,

/***/ 135:
/***/ function(module, exports, __webpack_require__) {

	// 9.4.2.3 ArraySpeciesCreate(originalArray, length)
	var speciesConstructor = __webpack_require__(136);
	
	module.exports = function(original, length){
	  return new (speciesConstructor(original))(length);
	};

/***/ },

/***/ 136:
/***/ function(module, exports, __webpack_require__) {

	var isObject = __webpack_require__(116)
	  , isArray  = __webpack_require__(137)
	  , SPECIES  = __webpack_require__(138)('species');
	
	module.exports = function(original){
	  var C;
	  if(isArray(original)){
	    C = original.constructor;
	    // cross-realm fallback
	    if(typeof C == 'function' && (C === Array || isArray(C.prototype)))C = undefined;
	    if(isObject(C)){
	      C = C[SPECIES];
	      if(C === null)C = undefined;
	    }
	  } return C === undefined ? Array : C;
	};

/***/ },

/***/ 137:
[330, 130],

/***/ 138:
[343, 139, 125, 111],

/***/ 139:
[334, 111],

/***/ 140:
/***/ function(module, exports, __webpack_require__) {

	// 22.1.3.31 Array.prototype[@@unscopables]
	var UNSCOPABLES = __webpack_require__(138)('unscopables')
	  , ArrayProto  = Array.prototype;
	if(ArrayProto[UNSCOPABLES] == undefined)__webpack_require__(113)(ArrayProto, UNSCOPABLES, {});
	module.exports = function(key){
	  ArrayProto[UNSCOPABLES][key] = true;
	};

/***/ },

/***/ 141:
/***/ function(module, exports) {

	// removed by extract-text-webpack-plugin

/***/ },

/***/ 146:
/***/ function(module, exports, __webpack_require__) {

	/* WEBPACK VAR INJECTION */(function($, jQuery) {'use strict';
	
	Object.defineProperty(exports, "__esModule", {
	  value: true
	});
	
	var _typeof2 = __webpack_require__(12);
	
	var _typeof3 = _interopRequireDefault(_typeof2);
	
	var _keys = __webpack_require__(96);
	
	var _keys2 = _interopRequireDefault(_keys);
	
	exports.populateWithUrl = populateWithUrl;
	exports.updateLinker = updateLinker;
	exports.updateLinksRemaining = updateLinksRemaining;
	exports.init = init;
	
	function _interopRequireDefault(obj) { return obj && obj.__esModule ? obj : { default: obj }; }
	
	var Spinner = __webpack_require__(147);
	__webpack_require__(148); // add jquery support for ajaxSubmit/ajaxForm
	__webpack_require__(149); // add .modal to jquery
	
	var Helpers = __webpack_require__(95);
	var DOMHelpers = __webpack_require__(2);
	var HandlebarsHelpers = __webpack_require__(3);
	var APIModule = __webpack_require__(81);
	var FolderTreeModule = __webpack_require__(106);
	
	var newGUID = null;
	var refreshIntervalIds = [];
	var spinner;
	var organizations = {};
	
	// Get parameter by name
	// from https://stackoverflow.com/questions/901115/how-can-i-get-query-string-values-in-javascript
	function getParameterByName(name) {
	  name = name.replace(/[\[]/, "\\[").replace(/[\]]/, "\\]");
	  var regex = new RegExp("[\\?&]" + name + "=([^&#]*)"),
	      results = regex.exec(location.search);
	  return results == null ? "" : decodeURIComponent(results[1].replace(/\+/g, " "));
	}
	
	function linkIt(data) {
	  // Success message from API. We should have a GUID now (but the
	  // archive is still be generated)
	  // Clear any error messages out
	  DOMHelpers.removeElement('.error-row');
	
	  newGUID = data.guid;
	
	  refreshIntervalIds.push(setInterval(check_status, 2000));
	}
	
	function linkNot(jqXHR) {
	  // The API told us something went wrong.
	  var message = APIModule.getErrorMessage(jqXHR);
	
	  var upload_allowed = true;
	  if (message.indexOf("limit") > -1) {
	    $('.links-remaining').text('0');
	    upload_allowed = false;
	  }
	
	  var templateArgs = {
	    message: message,
	    upload_allowed: upload_allowed,
	    contact_url: contact_url
	  };
	
	  changeTemplate('#error-template', templateArgs, '#error-container');
	
	  $('.create-errors').addClass('_active');
	  $('#error-container').hide().fadeIn(0);
	
	  toggleCreateAvailable();
	}
	
	/* Handle an upload - start */
	function uploadNot(jqXHR) {
	  // Display an error message in our upload modal
	
	  // special handling if user becomes unexpectedly logged out
	  if (jqXHR.status == 401) {
	    APIModule.showError(jqXHR);
	    return;
	  }
	  var reasons = [],
	      response;
	
	  try {
	    response = jQuery.parseJSON(jqXHR.responseText);
	  } catch (e) {
	    reasons = [jqXHR.responseText];
	  }
	
	  DOMHelpers.hideElement('.spinner');
	
	  $('.js-warning').remove();
	  $('.has-error').removeClass('has-error');
	
	  if (response) {
	    // Can be removed when Tastypie API no longer used
	    if (response.archives) response = response.archives;
	
	    // If error message comes in as {file:"message",url:"message"},
	    // show appropriate error message next to each field.
	    for (var key in response) {
	      if (response.hasOwnProperty(key)) {
	        var input = $('#' + key);
	        if (input.length) {
	          input.after('<span class="help-block js-warning">' + response[key] + '</span>');
	          input.closest('div').addClass('has-error');
	        } else {
	          reasons.push(response[key]);
	        }
	      }
	    }
	  }
	
	  $('#upload-error').text('Upload failed. ' + reasons.join(". "));
	  DOMHelpers.toggleBtnDisable('#uploadLinky', false);
	  DOMHelpers.toggleBtnDisable('.cancel', false);
	}
	
	function uploadIt(data) {
	  // If a user wants to upload their own screen capture, we display
	  // a modal and the form in that modal is handled here
	  $('#archive-upload').modal('hide');
	
	  window.location.href = '/' + data.guid;
	}
	
	function upload_form() {
	  $('#upload-error').text('');
	  $('#archive_upload_form input[name="url"]').val($('#rawUrl').val());
	  $('#archive-upload').modal('show');
	  return false;
	}
	
	/* Handle the the main action (enter url, hit the button) button - start */
	
	function toggleCreateAvailable() {
	  // Get our spinner going and display a "we're working" message
	  var $addlink = $('#addlink');
	  if ($addlink.hasClass('_isWorking')) {
	    $addlink.html('Create Perma Link').removeAttr('disabled').removeClass('_isWorking');
	    spinner.stop();
	    $('#rawUrl, #organization_select_form button').removeAttr('disabled');
	    $('#links-remaining-message').removeClass('_isWorking');
	  } else {
	    $addlink.html('<div id="capture-status">Creating your Perma Link</div>').attr('disabled', 'disabled').addClass('_isWorking');
	    // spinner opts -- see http://spin.js.org/
	    spinner = new Spinner({ lines: 15, length: 2, width: 2, radius: 9, corners: 0, color: '#2D76EE', trail: 50, top: '12px' });
	    spinner.spin($addlink[0]);
	    $('#rawUrl, #organization_select_form button').attr('disabled', 'disabled');
	    $('#links-remaining-message').addClass('_isWorking');
	  }
	}
	
	/* The plan is to set a timer to periodically check if the thumbnail
	 exists. Once it does, we append it to the page and clear the
	 thumbnail. The reason we're keeping a list of interval IDs rather
	 than just one is as a hacky solution to the problem of a user
	 creating a Perma link for some URL and then immediately clicking
	 the button again for the same URL. Since all these requests are
	 done with AJAX, that results in two different interval IDs getting
	 created. Both requests will end up completing but the old interval
	 ID will be overwritten and never cleared, causing a bunch of copies
	 of the screenshot to get appended to the page. We thus just append
	 them to the list and then clear the whole list once the request
	 succeeds. */
	
	function check_status() {
	
	  // Check our status service to see if we have archiving jobs pending
	  var request = APIModule.request("GET", "/user/capture_jobs/" + newGUID + "/");
	  request.done(function (data) {
	    // While status is pending or in progress, update progress display
	    if (data.status == "pending") {
	      // todo -- could display data.queue_position here
	
	    } else if (data.status == "in_progress") {
	
	      // add progress bar if doesn't exist
	      if (!$('#capture-progress-bar').length) {
	        $('#addlink').append('<div style="position: relative; width: 100%; height: 0">' + '  <div id="capture-progress-bar" class="progress" style="width: 100%; height: 0.3em; position:absolute; margin-bottom: 0">' + '    <div class="progress-bar" role="progressbar" aria-valuenow="0" aria-valuemin="0" aria-valuemax="100" style="width: 0; background-color: #2D76EE">' + '      <span class="sr-only">0% Complete</span>' + '    </div>' + '  </div>' + '</div>');
	      }
	
	      // update progress
	      var progress = data.step_count / 5 * 100;
	      $('#capture-progress-bar .progress-bar').attr('aria-valuenow', progress).css('width', progress + '%').find('span').text(progress + '% Complete');
	    } else {
	
	      // Capture is done (one way or another) -- clear out our pending jobs
	      $.each(refreshIntervalIds, function (ndx, id) {
	        clearInterval(id);
	      });
	
	      // If we succeeded, forward to the new archive
	      if (data.status == "completed") {
	        window.location.href = "/" + newGUID;
	
	        // Else show failure message and reset form.
	      } else {
	        var templateArgs = { message: "Error: URL capture failed." };
	        changeTemplate('#error-template', templateArgs, '#error-container');
	
	        $('#error-container').removeClass('_hide _success _wait').addClass('_error');
	
	        // Toggle our create button
	        toggleCreateAvailable();
	      }
	    }
	  });
	}
	
	/* Our polling function for the thumbnail completion - end */
	function populateWithUrl() {
	  var url = Helpers.getWindowLocationSearch().split("url=")[1];
	  if (url) {
	    url = decodeURIComponent(url);
	    DOMHelpers.setInputValue("#rawUrl", url);
	    return url;
	  }
	}
	
	// This handles the dropdown menu for selecting a folder, which only appears for
	// org users, registrar users, and admins, and alters related UI elements depending
	// on what has been selected.
	function updateLinker() {
	  var currentOrg = FolderTreeModule.getSavedOrg();
	  var organizationsExist = (0, _keys2.default)(organizations).length;
	
	  // if user has organizations available but hasn't picked one yet, require them to pick
	  if (!FolderTreeModule.getSavedFolder() && organizationsExist) {
	    $('#addlink').attr('disabled', 'disabled');
	    return;
	  }
	
	  // disable button if user is out of links
	  if (!currentOrg && links_remaining < 1) {
	    $('#addlink').attr('disabled', 'disabled');
	  } else {
	    $('#addlink').removeAttr('disabled');
	  }
	
	  // UI indications that links saved to current org will default to private
	  if (organizations[currentOrg] && organizations[currentOrg]['default_to_private']) {
	    $('#addlink').text("Create Private Perma Link");
	    $('#linker').addClass('_isPrivate');
	    // add the little eye icon to the dropdown
	    $('#organization_select_form').find('.dropdown-toggle > span').addClass('ui-private');
	  } else {
	    $('#addlink').text("Create Perma Link");
	    $('#linker').removeClass('_isPrivate');
	    $('#organization_select_form').find('.dropdown-toggle > span').removeClass('ui-private');
	  }
	
	  // suggest switching folder if user has orgs and is running out of personal links
	  var already_warned = Helpers.getCookie("suppress_link_warning");
	  if (already_warned != "true" && !currentOrg && organizationsExist && links_remaining == 3) {
	    var message = "Your personal links for the month are almost used up! Create more links in 'unlimited' folders.";
	    Helpers.informUser(message, 'danger');
	    Helpers.setCookie("suppress_link_warning", "true", 120);
	  }
	}
	
	function handleSelectionChange(data) {
	  updateLinker();
	
	  if (data && data.path) {
	    updateAffiliationPath(data.orgId, data.path);
	  }
	}
	
	function updateAffiliationPath(currentOrg, path) {
	
	  var stringPath = path.join(" &gt; ");
	  stringPath += "<span></span>";
	
	  $('#organization_select_form').find('.dropdown-toggle').html(stringPath);
	
	  if (organizations[currentOrg] && organizations[currentOrg]['default_to_private']) {
	    $('#organization_select_form').find('.dropdown-toggle > span').addClass('ui-private');
	  }
	
	  if (!currentOrg || currentOrg === "None") {
	    $('#organization_select_form').find('.dropdown-toggle > span').addClass('links-remaining').text(links_remaining);
	  }
	}
	
	function updateLinksRemaining(links_num) {
	  links_remaining = links_num;
	  DOMHelpers.changeText('.links-remaining', links_remaining);
	}
	
	function setupEventHandlers() {
	  $(window).on('FolderTreeModule.selectionChange', function (evt, data) {
	    if ((typeof data === 'undefined' ? 'undefined' : (0, _typeof3.default)(data)) !== 'object') data = JSON.parse(data);
	    handleSelectionChange(data);
	  }).on('CreateLinkModule.updateLinker', function () {
	    updateLinker();
	  }).on('FolderTreeModule.updateLinksRemaining', function (evt, data) {
	    updateLinksRemaining(data);
	  });
	
	  // When a user uploads their own capture
	  $(document).on('submit', '#archive_upload_form', function () {
	    DOMHelpers.toggleBtnDisable('#uploadLinky', true);
	    DOMHelpers.toggleBtnDisable('.cancel', true);
	    var extraUploadData = {},
	        selectedFolder = FolderTreeModule.getSavedFolder();
	    if (selectedFolder) extraUploadData.folder = selectedFolder;
	    spinner = new Spinner({ lines: 15, length: 2, width: 2, radius: 9, corners: 0, color: '#2D76EE', trail: 50, top: '300px' });
	    spinner.spin(this);
	    $(this).ajaxSubmit({
	      url: api_path + "/archives/",
	      data: extraUploadData,
	      success: uploadIt,
	      error: uploadNot
	    });
	    return false;
	  });
	
	  // Toggle users dropdown
	  $('#dashboard-users').click(function () {
	    $('.users-secondary').toggle();
	  });
	
	  // When a new url is entered into our form
	  $('#linker').submit(function () {
	    var $this = $(this);
	    var linker_data = {
	      url: $this.find("input[name=url]").val(),
	      human: true
	    };
	    var selectedFolder = FolderTreeModule.getSavedFolder();
	
	    if (selectedFolder) linker_data.folder = selectedFolder;
	
	    // Start our spinner and disable our input field with just a tiny delay
	    window.setTimeout(toggleCreateAvailable, 150);
	
	    APIModule.request("POST", "/archives/", linker_data, { error: linkNot }).success(linkIt);
	
	    return false;
	  });
	}
	
	/* templateContainer: DOM selector, where the newly rendered template will live */
	function changeTemplate(template, args, templateContainer) {
	  var renderedTemplate = HandlebarsHelpers.renderTemplate(template, args);
	  DOMHelpers.changeHTML(templateContainer, renderedTemplate);
	}
	
	function init() {
	  // Dismiss browser tools message
	  $('.close-browser-tools').click(function () {
	    $('#browser-tools-message').hide();
	    Helpers.setCookie("suppress_reminder", "true", 120);
	  });
	
	  var $organization_select = $("#organization_select");
	
	  // populate organization dropdown
	  APIModule.request("GET", "/user/organizations/", { limit: 300, order_by: 'registrar' }).success(function (data) {
	
	    var sorted = [];
	    (0, _keys2.default)(data.objects).sort(function (a, b) {
	      return data.objects[a].registrar < data.objects[b].registrar ? -1 : 1;
	    }).forEach(function (key) {
	      sorted.push(data.objects[key]);
	    });
	    data.objects = sorted;
	
	    if (data.objects.length > 0) {
	      var optgroup = data.objects[0].registrar;
	      $organization_select.append("<li class='dropdown-header'>" + optgroup + "</li>");
	      data.objects.map(function (organization) {
	        organizations[organization.id] = organization;
	
	        if (organization.registrar !== optgroup) {
	          optgroup = organization.registrar;
	          $organization_select.append("<li class='dropdown-header'>" + optgroup + "</li>");
	        }
	        var opt_text = organization.name;
	        if (organization.default_to_private) {
	          opt_text += ' <span class="ui-private">(Private)</span>';
	        }
	        $organization_select.append("<li><a href='#' data-orgid='" + organization.id + "' data-folderid='" + organization.shared_folder.id + "'>" + opt_text + " <span class='links-unlimited'>unlimited</span></a></li>");
	      });
	
	      $organization_select.append("<li class='personal-links'><a href='#' data-folderid='" + current_user.top_level_folders[0].id + "'> Personal Links <span class='links-remaining'>" + links_remaining + "</span></a></li>");
	      updateLinker();
	    }
	  });
	
	  // handle dropdown changes
	  $organization_select.on('click', 'a', function () {
	    FolderTreeModule.ls.setCurrent(+$(this).attr('data-orgid'), [+$(this).attr('data-folderid')]);
	    Helpers.triggerOnWindow("dropdown.selectionChange");
	  });
	
	  // handle upload form button
	  $(document.body).on('click', '#upload-form-button', upload_form);
	
	  setupEventHandlers();
	  populateWithUrl();
	}
	/* WEBPACK VAR INJECTION */}.call(exports, __webpack_require__(1), __webpack_require__(1)))

/***/ },

/***/ 147:
/***/ function(module, exports, __webpack_require__) {

	var __WEBPACK_AMD_DEFINE_FACTORY__, __WEBPACK_AMD_DEFINE_RESULT__;/**
	 * Copyright (c) 2011-2014 Felix Gnass
	 * Licensed under the MIT license
	 * http://spin.js.org/
	 *
	 * Example:
	    var opts = {
	      lines: 12             // The number of lines to draw
	    , length: 7             // The length of each line
	    , width: 5              // The line thickness
	    , radius: 10            // The radius of the inner circle
	    , scale: 1.0            // Scales overall size of the spinner
	    , corners: 1            // Roundness (0..1)
	    , color: '#000'         // #rgb or #rrggbb
	    , opacity: 1/4          // Opacity of the lines
	    , rotate: 0             // Rotation offset
	    , direction: 1          // 1: clockwise, -1: counterclockwise
	    , speed: 1              // Rounds per second
	    , trail: 100            // Afterglow percentage
	    , fps: 20               // Frames per second when using setTimeout()
	    , zIndex: 2e9           // Use a high z-index by default
	    , className: 'spinner'  // CSS class to assign to the element
	    , top: '50%'            // center vertically
	    , left: '50%'           // center horizontally
	    , shadow: false         // Whether to render a shadow
	    , hwaccel: false        // Whether to use hardware acceleration (might be buggy)
	    , position: 'absolute'  // Element positioning
	    }
	    var target = document.getElementById('foo')
	    var spinner = new Spinner(opts).spin(target)
	 */
	;(function (root, factory) {
	
	  /* CommonJS */
	  if (typeof module == 'object' && module.exports) module.exports = factory()
	
	  /* AMD module */
	  else if (true) !(__WEBPACK_AMD_DEFINE_FACTORY__ = (factory), __WEBPACK_AMD_DEFINE_RESULT__ = (typeof __WEBPACK_AMD_DEFINE_FACTORY__ === 'function' ? (__WEBPACK_AMD_DEFINE_FACTORY__.call(exports, __webpack_require__, exports, module)) : __WEBPACK_AMD_DEFINE_FACTORY__), __WEBPACK_AMD_DEFINE_RESULT__ !== undefined && (module.exports = __WEBPACK_AMD_DEFINE_RESULT__))
	
	  /* Browser global */
	  else root.Spinner = factory()
	}(this, function () {
	  "use strict"
	
	  var prefixes = ['webkit', 'Moz', 'ms', 'O'] /* Vendor prefixes */
	    , animations = {} /* Animation rules keyed by their name */
	    , useCssAnimations /* Whether to use CSS animations or setTimeout */
	    , sheet /* A stylesheet to hold the @keyframe or VML rules. */
	
	  /**
	   * Utility function to create elements. If no tag name is given,
	   * a DIV is created. Optionally properties can be passed.
	   */
	  function createEl (tag, prop) {
	    var el = document.createElement(tag || 'div')
	      , n
	
	    for (n in prop) el[n] = prop[n]
	    return el
	  }
	
	  /**
	   * Appends children and returns the parent.
	   */
	  function ins (parent /* child1, child2, ...*/) {
	    for (var i = 1, n = arguments.length; i < n; i++) {
	      parent.appendChild(arguments[i])
	    }
	
	    return parent
	  }
	
	  /**
	   * Creates an opacity keyframe animation rule and returns its name.
	   * Since most mobile Webkits have timing issues with animation-delay,
	   * we create separate rules for each line/segment.
	   */
	  function addAnimation (alpha, trail, i, lines) {
	    var name = ['opacity', trail, ~~(alpha * 100), i, lines].join('-')
	      , start = 0.01 + i/lines * 100
	      , z = Math.max(1 - (1-alpha) / trail * (100-start), alpha)
	      , prefix = useCssAnimations.substring(0, useCssAnimations.indexOf('Animation')).toLowerCase()
	      , pre = prefix && '-' + prefix + '-' || ''
	
	    if (!animations[name]) {
	      sheet.insertRule(
	        '@' + pre + 'keyframes ' + name + '{' +
	        '0%{opacity:' + z + '}' +
	        start + '%{opacity:' + alpha + '}' +
	        (start+0.01) + '%{opacity:1}' +
	        (start+trail) % 100 + '%{opacity:' + alpha + '}' +
	        '100%{opacity:' + z + '}' +
	        '}', sheet.cssRules.length)
	
	      animations[name] = 1
	    }
	
	    return name
	  }
	
	  /**
	   * Tries various vendor prefixes and returns the first supported property.
	   */
	  function vendor (el, prop) {
	    var s = el.style
	      , pp
	      , i
	
	    prop = prop.charAt(0).toUpperCase() + prop.slice(1)
	    if (s[prop] !== undefined) return prop
	    for (i = 0; i < prefixes.length; i++) {
	      pp = prefixes[i]+prop
	      if (s[pp] !== undefined) return pp
	    }
	  }
	
	  /**
	   * Sets multiple style properties at once.
	   */
	  function css (el, prop) {
	    for (var n in prop) {
	      el.style[vendor(el, n) || n] = prop[n]
	    }
	
	    return el
	  }
	
	  /**
	   * Fills in default values.
	   */
	  function merge (obj) {
	    for (var i = 1; i < arguments.length; i++) {
	      var def = arguments[i]
	      for (var n in def) {
	        if (obj[n] === undefined) obj[n] = def[n]
	      }
	    }
	    return obj
	  }
	
	  /**
	   * Returns the line color from the given string or array.
	   */
	  function getColor (color, idx) {
	    return typeof color == 'string' ? color : color[idx % color.length]
	  }
	
	  // Built-in defaults
	
	  var defaults = {
	    lines: 12             // The number of lines to draw
	  , length: 7             // The length of each line
	  , width: 5              // The line thickness
	  , radius: 10            // The radius of the inner circle
	  , scale: 1.0            // Scales overall size of the spinner
	  , corners: 1            // Roundness (0..1)
	  , color: '#000'         // #rgb or #rrggbb
	  , opacity: 1/4          // Opacity of the lines
	  , rotate: 0             // Rotation offset
	  , direction: 1          // 1: clockwise, -1: counterclockwise
	  , speed: 1              // Rounds per second
	  , trail: 100            // Afterglow percentage
	  , fps: 20               // Frames per second when using setTimeout()
	  , zIndex: 2e9           // Use a high z-index by default
	  , className: 'spinner'  // CSS class to assign to the element
	  , top: '50%'            // center vertically
	  , left: '50%'           // center horizontally
	  , shadow: false         // Whether to render a shadow
	  , hwaccel: false        // Whether to use hardware acceleration (might be buggy)
	  , position: 'absolute'  // Element positioning
	  }
	
	  /** The constructor */
	  function Spinner (o) {
	    this.opts = merge(o || {}, Spinner.defaults, defaults)
	  }
	
	  // Global defaults that override the built-ins:
	  Spinner.defaults = {}
	
	  merge(Spinner.prototype, {
	    /**
	     * Adds the spinner to the given target element. If this instance is already
	     * spinning, it is automatically removed from its previous target b calling
	     * stop() internally.
	     */
	    spin: function (target) {
	      this.stop()
	
	      var self = this
	        , o = self.opts
	        , el = self.el = createEl(null, {className: o.className})
	
	      css(el, {
	        position: o.position
	      , width: 0
	      , zIndex: o.zIndex
	      , left: o.left
	      , top: o.top
	      })
	
	      if (target) {
	        target.insertBefore(el, target.firstChild || null)
	      }
	
	      el.setAttribute('role', 'progressbar')
	      self.lines(el, self.opts)
	
	      if (!useCssAnimations) {
	        // No CSS animation support, use setTimeout() instead
	        var i = 0
	          , start = (o.lines - 1) * (1 - o.direction) / 2
	          , alpha
	          , fps = o.fps
	          , f = fps / o.speed
	          , ostep = (1 - o.opacity) / (f * o.trail / 100)
	          , astep = f / o.lines
	
	        ;(function anim () {
	          i++
	          for (var j = 0; j < o.lines; j++) {
	            alpha = Math.max(1 - (i + (o.lines - j) * astep) % f * ostep, o.opacity)
	
	            self.opacity(el, j * o.direction + start, alpha, o)
	          }
	          self.timeout = self.el && setTimeout(anim, ~~(1000 / fps))
	        })()
	      }
	      return self
	    }
	
	    /**
	     * Stops and removes the Spinner.
	     */
	  , stop: function () {
	      var el = this.el
	      if (el) {
	        clearTimeout(this.timeout)
	        if (el.parentNode) el.parentNode.removeChild(el)
	        this.el = undefined
	      }
	      return this
	    }
	
	    /**
	     * Internal method that draws the individual lines. Will be overwritten
	     * in VML fallback mode below.
	     */
	  , lines: function (el, o) {
	      var i = 0
	        , start = (o.lines - 1) * (1 - o.direction) / 2
	        , seg
	
	      function fill (color, shadow) {
	        return css(createEl(), {
	          position: 'absolute'
	        , width: o.scale * (o.length + o.width) + 'px'
	        , height: o.scale * o.width + 'px'
	        , background: color
	        , boxShadow: shadow
	        , transformOrigin: 'left'
	        , transform: 'rotate(' + ~~(360/o.lines*i + o.rotate) + 'deg) translate(' + o.scale*o.radius + 'px' + ',0)'
	        , borderRadius: (o.corners * o.scale * o.width >> 1) + 'px'
	        })
	      }
	
	      for (; i < o.lines; i++) {
	        seg = css(createEl(), {
	          position: 'absolute'
	        , top: 1 + ~(o.scale * o.width / 2) + 'px'
	        , transform: o.hwaccel ? 'translate3d(0,0,0)' : ''
	        , opacity: o.opacity
	        , animation: useCssAnimations && addAnimation(o.opacity, o.trail, start + i * o.direction, o.lines) + ' ' + 1 / o.speed + 's linear infinite'
	        })
	
	        if (o.shadow) ins(seg, css(fill('#000', '0 0 4px #000'), {top: '2px'}))
	        ins(el, ins(seg, fill(getColor(o.color, i), '0 0 1px rgba(0,0,0,.1)')))
	      }
	      return el
	    }
	
	    /**
	     * Internal method that adjusts the opacity of a single line.
	     * Will be overwritten in VML fallback mode below.
	     */
	  , opacity: function (el, i, val) {
	      if (i < el.childNodes.length) el.childNodes[i].style.opacity = val
	    }
	
	  })
	
	
	  function initVML () {
	
	    /* Utility function to create a VML tag */
	    function vml (tag, attr) {
	      return createEl('<' + tag + ' xmlns="urn:schemas-microsoft.com:vml" class="spin-vml">', attr)
	    }
	
	    // No CSS transforms but VML support, add a CSS rule for VML elements:
	    sheet.addRule('.spin-vml', 'behavior:url(#default#VML)')
	
	    Spinner.prototype.lines = function (el, o) {
	      var r = o.scale * (o.length + o.width)
	        , s = o.scale * 2 * r
	
	      function grp () {
	        return css(
	          vml('group', {
	            coordsize: s + ' ' + s
	          , coordorigin: -r + ' ' + -r
	          })
	        , { width: s, height: s }
	        )
	      }
	
	      var margin = -(o.width + o.length) * o.scale * 2 + 'px'
	        , g = css(grp(), {position: 'absolute', top: margin, left: margin})
	        , i
	
	      function seg (i, dx, filter) {
	        ins(
	          g
	        , ins(
	            css(grp(), {rotation: 360 / o.lines * i + 'deg', left: ~~dx})
	          , ins(
	              css(
	                vml('roundrect', {arcsize: o.corners})
	              , { width: r
	                , height: o.scale * o.width
	                , left: o.scale * o.radius
	                , top: -o.scale * o.width >> 1
	                , filter: filter
	                }
	              )
	            , vml('fill', {color: getColor(o.color, i), opacity: o.opacity})
	            , vml('stroke', {opacity: 0}) // transparent stroke to fix color bleeding upon opacity change
	            )
	          )
	        )
	      }
	
	      if (o.shadow)
	        for (i = 1; i <= o.lines; i++) {
	          seg(i, -2, 'progid:DXImageTransform.Microsoft.Blur(pixelradius=2,makeshadow=1,shadowopacity=.3)')
	        }
	
	      for (i = 1; i <= o.lines; i++) seg(i)
	      return ins(el, g)
	    }
	
	    Spinner.prototype.opacity = function (el, i, val, o) {
	      var c = el.firstChild
	      o = o.shadow && o.lines || 0
	      if (c && i + o < c.childNodes.length) {
	        c = c.childNodes[i + o]; c = c && c.firstChild; c = c && c.firstChild
	        if (c) c.opacity = val
	      }
	    }
	  }
	
	  if (typeof document !== 'undefined') {
	    sheet = (function () {
	      var el = createEl('style', {type : 'text/css'})
	      ins(document.getElementsByTagName('head')[0], el)
	      return el.sheet || el.styleSheet
	    }())
	
	    var probe = css(createEl('group'), {behavior: 'url(#default#VML)'})
	
	    if (!vendor(probe, 'transform') && probe.adj) initVML()
	    else useCssAnimations = vendor(probe, 'animation')
	  }
	
	  return Spinner
	
	}));


/***/ },

/***/ 148:
/***/ function(module, exports, __webpack_require__) {

	var __WEBPACK_AMD_DEFINE_FACTORY__, __WEBPACK_AMD_DEFINE_ARRAY__, __WEBPACK_AMD_DEFINE_RESULT__;/*!
	 * jQuery Form Plugin
	 * version: 3.50.0-2014.02.05
	 * Requires jQuery v1.5 or later
	 * Copyright (c) 2013 M. Alsup
	 * Examples and documentation at: http://malsup.com/jquery/form/
	 * Project repository: https://github.com/malsup/form
	 * Dual licensed under the MIT and GPL licenses.
	 * https://github.com/malsup/form#copyright-and-license
	 */
	/*global ActiveXObject */
	
	// AMD support
	(function (factory) {
	    "use strict";
	    if (true) {
	        // using AMD; register as anon module
	        !(__WEBPACK_AMD_DEFINE_ARRAY__ = [__webpack_require__(1)], __WEBPACK_AMD_DEFINE_FACTORY__ = (factory), __WEBPACK_AMD_DEFINE_RESULT__ = (typeof __WEBPACK_AMD_DEFINE_FACTORY__ === 'function' ? (__WEBPACK_AMD_DEFINE_FACTORY__.apply(exports, __WEBPACK_AMD_DEFINE_ARRAY__)) : __WEBPACK_AMD_DEFINE_FACTORY__), __WEBPACK_AMD_DEFINE_RESULT__ !== undefined && (module.exports = __WEBPACK_AMD_DEFINE_RESULT__));
	    } else {
	        // no AMD; invoke directly
	        factory( (typeof(jQuery) != 'undefined') ? jQuery : window.Zepto );
	    }
	}
	
	(function($) {
	"use strict";
	
	/*
	    Usage Note:
	    -----------
	    Do not use both ajaxSubmit and ajaxForm on the same form.  These
	    functions are mutually exclusive.  Use ajaxSubmit if you want
	    to bind your own submit handler to the form.  For example,
	
	    $(document).ready(function() {
	        $('#myForm').on('submit', function(e) {
	            e.preventDefault(); // <-- important
	            $(this).ajaxSubmit({
	                target: '#output'
	            });
	        });
	    });
	
	    Use ajaxForm when you want the plugin to manage all the event binding
	    for you.  For example,
	
	    $(document).ready(function() {
	        $('#myForm').ajaxForm({
	            target: '#output'
	        });
	    });
	
	    You can also use ajaxForm with delegation (requires jQuery v1.7+), so the
	    form does not have to exist when you invoke ajaxForm:
	
	    $('#myForm').ajaxForm({
	        delegation: true,
	        target: '#output'
	    });
	
	    When using ajaxForm, the ajaxSubmit function will be invoked for you
	    at the appropriate time.
	*/
	
	/**
	 * Feature detection
	 */
	var feature = {};
	feature.fileapi = $("<input type='file'/>").get(0).files !== undefined;
	feature.formdata = window.FormData !== undefined;
	
	var hasProp = !!$.fn.prop;
	
	// attr2 uses prop when it can but checks the return type for
	// an expected string.  this accounts for the case where a form 
	// contains inputs with names like "action" or "method"; in those
	// cases "prop" returns the element
	$.fn.attr2 = function() {
	    if ( ! hasProp ) {
	        return this.attr.apply(this, arguments);
	    }
	    var val = this.prop.apply(this, arguments);
	    if ( ( val && val.jquery ) || typeof val === 'string' ) {
	        return val;
	    }
	    return this.attr.apply(this, arguments);
	};
	
	/**
	 * ajaxSubmit() provides a mechanism for immediately submitting
	 * an HTML form using AJAX.
	 */
	$.fn.ajaxSubmit = function(options) {
	    /*jshint scripturl:true */
	
	    // fast fail if nothing selected (http://dev.jquery.com/ticket/2752)
	    if (!this.length) {
	        log('ajaxSubmit: skipping submit process - no element selected');
	        return this;
	    }
	
	    var method, action, url, $form = this;
	
	    if (typeof options == 'function') {
	        options = { success: options };
	    }
	    else if ( options === undefined ) {
	        options = {};
	    }
	
	    method = options.type || this.attr2('method');
	    action = options.url  || this.attr2('action');
	
	    url = (typeof action === 'string') ? $.trim(action) : '';
	    url = url || window.location.href || '';
	    if (url) {
	        // clean url (don't include hash vaue)
	        url = (url.match(/^([^#]+)/)||[])[1];
	    }
	
	    options = $.extend(true, {
	        url:  url,
	        success: $.ajaxSettings.success,
	        type: method || $.ajaxSettings.type,
	        iframeSrc: /^https/i.test(window.location.href || '') ? 'javascript:false' : 'about:blank'
	    }, options);
	
	    // hook for manipulating the form data before it is extracted;
	    // convenient for use with rich editors like tinyMCE or FCKEditor
	    var veto = {};
	    this.trigger('form-pre-serialize', [this, options, veto]);
	    if (veto.veto) {
	        log('ajaxSubmit: submit vetoed via form-pre-serialize trigger');
	        return this;
	    }
	
	    // provide opportunity to alter form data before it is serialized
	    if (options.beforeSerialize && options.beforeSerialize(this, options) === false) {
	        log('ajaxSubmit: submit aborted via beforeSerialize callback');
	        return this;
	    }
	
	    var traditional = options.traditional;
	    if ( traditional === undefined ) {
	        traditional = $.ajaxSettings.traditional;
	    }
	
	    var elements = [];
	    var qx, a = this.formToArray(options.semantic, elements);
	    if (options.data) {
	        options.extraData = options.data;
	        qx = $.param(options.data, traditional);
	    }
	
	    // give pre-submit callback an opportunity to abort the submit
	    if (options.beforeSubmit && options.beforeSubmit(a, this, options) === false) {
	        log('ajaxSubmit: submit aborted via beforeSubmit callback');
	        return this;
	    }
	
	    // fire vetoable 'validate' event
	    this.trigger('form-submit-validate', [a, this, options, veto]);
	    if (veto.veto) {
	        log('ajaxSubmit: submit vetoed via form-submit-validate trigger');
	        return this;
	    }
	
	    var q = $.param(a, traditional);
	    if (qx) {
	        q = ( q ? (q + '&' + qx) : qx );
	    }
	    if (options.type.toUpperCase() == 'GET') {
	        options.url += (options.url.indexOf('?') >= 0 ? '&' : '?') + q;
	        options.data = null;  // data is null for 'get'
	    }
	    else {
	        options.data = q; // data is the query string for 'post'
	    }
	
	    var callbacks = [];
	    if (options.resetForm) {
	        callbacks.push(function() { $form.resetForm(); });
	    }
	    if (options.clearForm) {
	        callbacks.push(function() { $form.clearForm(options.includeHidden); });
	    }
	
	    // perform a load on the target only if dataType is not provided
	    if (!options.dataType && options.target) {
	        var oldSuccess = options.success || function(){};
	        callbacks.push(function(data) {
	            var fn = options.replaceTarget ? 'replaceWith' : 'html';
	            $(options.target)[fn](data).each(oldSuccess, arguments);
	        });
	    }
	    else if (options.success) {
	        callbacks.push(options.success);
	    }
	
	    options.success = function(data, status, xhr) { // jQuery 1.4+ passes xhr as 3rd arg
	        var context = options.context || this ;    // jQuery 1.4+ supports scope context
	        for (var i=0, max=callbacks.length; i < max; i++) {
	            callbacks[i].apply(context, [data, status, xhr || $form, $form]);
	        }
	    };
	
	    if (options.error) {
	        var oldError = options.error;
	        options.error = function(xhr, status, error) {
	            var context = options.context || this;
	            oldError.apply(context, [xhr, status, error, $form]);
	        };
	    }
	
	     if (options.complete) {
	        var oldComplete = options.complete;
	        options.complete = function(xhr, status) {
	            var context = options.context || this;
	            oldComplete.apply(context, [xhr, status, $form]);
	        };
	    }
	
	    // are there files to upload?
	
	    // [value] (issue #113), also see comment:
	    // https://github.com/malsup/form/commit/588306aedba1de01388032d5f42a60159eea9228#commitcomment-2180219
	    var fileInputs = $('input[type=file]:enabled', this).filter(function() { return $(this).val() !== ''; });
	
	    var hasFileInputs = fileInputs.length > 0;
	    var mp = 'multipart/form-data';
	    var multipart = ($form.attr('enctype') == mp || $form.attr('encoding') == mp);
	
	    var fileAPI = feature.fileapi && feature.formdata;
	    log("fileAPI :" + fileAPI);
	    var shouldUseFrame = (hasFileInputs || multipart) && !fileAPI;
	
	    var jqxhr;
	
	    // options.iframe allows user to force iframe mode
	    // 06-NOV-09: now defaulting to iframe mode if file input is detected
	    if (options.iframe !== false && (options.iframe || shouldUseFrame)) {
	        // hack to fix Safari hang (thanks to Tim Molendijk for this)
	        // see:  http://groups.google.com/group/jquery-dev/browse_thread/thread/36395b7ab510dd5d
	        if (options.closeKeepAlive) {
	            $.get(options.closeKeepAlive, function() {
	                jqxhr = fileUploadIframe(a);
	            });
	        }
	        else {
	            jqxhr = fileUploadIframe(a);
	        }
	    }
	    else if ((hasFileInputs || multipart) && fileAPI) {
	        jqxhr = fileUploadXhr(a);
	    }
	    else {
	        jqxhr = $.ajax(options);
	    }
	
	    $form.removeData('jqxhr').data('jqxhr', jqxhr);
	
	    // clear element array
	    for (var k=0; k < elements.length; k++) {
	        elements[k] = null;
	    }
	
	    // fire 'notify' event
	    this.trigger('form-submit-notify', [this, options]);
	    return this;
	
	    // utility fn for deep serialization
	    function deepSerialize(extraData){
	        var serialized = $.param(extraData, options.traditional).split('&');
	        var len = serialized.length;
	        var result = [];
	        var i, part;
	        for (i=0; i < len; i++) {
	            // #252; undo param space replacement
	            serialized[i] = serialized[i].replace(/\+/g,' ');
	            part = serialized[i].split('=');
	            // #278; use array instead of object storage, favoring array serializations
	            result.push([decodeURIComponent(part[0]), decodeURIComponent(part[1])]);
	        }
	        return result;
	    }
	
	     // XMLHttpRequest Level 2 file uploads (big hat tip to francois2metz)
	    function fileUploadXhr(a) {
	        var formdata = new FormData();
	
	        for (var i=0; i < a.length; i++) {
	            formdata.append(a[i].name, a[i].value);
	        }
	
	        if (options.extraData) {
	            var serializedData = deepSerialize(options.extraData);
	            for (i=0; i < serializedData.length; i++) {
	                if (serializedData[i]) {
	                    formdata.append(serializedData[i][0], serializedData[i][1]);
	                }
	            }
	        }
	
	        options.data = null;
	
	        var s = $.extend(true, {}, $.ajaxSettings, options, {
	            contentType: false,
	            processData: false,
	            cache: false,
	            type: method || 'POST'
	        });
	
	        if (options.uploadProgress) {
	            // workaround because jqXHR does not expose upload property
	            s.xhr = function() {
	                var xhr = $.ajaxSettings.xhr();
	                if (xhr.upload) {
	                    xhr.upload.addEventListener('progress', function(event) {
	                        var percent = 0;
	                        var position = event.loaded || event.position; /*event.position is deprecated*/
	                        var total = event.total;
	                        if (event.lengthComputable) {
	                            percent = Math.ceil(position / total * 100);
	                        }
	                        options.uploadProgress(event, position, total, percent);
	                    }, false);
	                }
	                return xhr;
	            };
	        }
	
	        s.data = null;
	        var beforeSend = s.beforeSend;
	        s.beforeSend = function(xhr, o) {
	            //Send FormData() provided by user
	            if (options.formData) {
	                o.data = options.formData;
	            }
	            else {
	                o.data = formdata;
	            }
	            if(beforeSend) {
	                beforeSend.call(this, xhr, o);
	            }
	        };
	        return $.ajax(s);
	    }
	
	    // private function for handling file uploads (hat tip to YAHOO!)
	    function fileUploadIframe(a) {
	        var form = $form[0], el, i, s, g, id, $io, io, xhr, sub, n, timedOut, timeoutHandle;
	        var deferred = $.Deferred();
	
	        // #341
	        deferred.abort = function(status) {
	            xhr.abort(status);
	        };
	
	        if (a) {
	            // ensure that every serialized input is still enabled
	            for (i=0; i < elements.length; i++) {
	                el = $(elements[i]);
	                if ( hasProp ) {
	                    el.prop('disabled', false);
	                }
	                else {
	                    el.removeAttr('disabled');
	                }
	            }
	        }
	
	        s = $.extend(true, {}, $.ajaxSettings, options);
	        s.context = s.context || s;
	        id = 'jqFormIO' + (new Date().getTime());
	        if (s.iframeTarget) {
	            $io = $(s.iframeTarget);
	            n = $io.attr2('name');
	            if (!n) {
	                $io.attr2('name', id);
	            }
	            else {
	                id = n;
	            }
	        }
	        else {
	            $io = $('<iframe name="' + id + '" src="'+ s.iframeSrc +'" />');
	            $io.css({ position: 'absolute', top: '-1000px', left: '-1000px' });
	        }
	        io = $io[0];
	
	
	        xhr = { // mock object
	            aborted: 0,
	            responseText: null,
	            responseXML: null,
	            status: 0,
	            statusText: 'n/a',
	            getAllResponseHeaders: function() {},
	            getResponseHeader: function() {},
	            setRequestHeader: function() {},
	            abort: function(status) {
	                var e = (status === 'timeout' ? 'timeout' : 'aborted');
	                log('aborting upload... ' + e);
	                this.aborted = 1;
	
	                try { // #214, #257
	                    if (io.contentWindow.document.execCommand) {
	                        io.contentWindow.document.execCommand('Stop');
	                    }
	                }
	                catch(ignore) {}
	
	                $io.attr('src', s.iframeSrc); // abort op in progress
	                xhr.error = e;
	                if (s.error) {
	                    s.error.call(s.context, xhr, e, status);
	                }
	                if (g) {
	                    $.event.trigger("ajaxError", [xhr, s, e]);
	                }
	                if (s.complete) {
	                    s.complete.call(s.context, xhr, e);
	                }
	            }
	        };
	
	        g = s.global;
	        // trigger ajax global events so that activity/block indicators work like normal
	        if (g && 0 === $.active++) {
	            $.event.trigger("ajaxStart");
	        }
	        if (g) {
	            $.event.trigger("ajaxSend", [xhr, s]);
	        }
	
	        if (s.beforeSend && s.beforeSend.call(s.context, xhr, s) === false) {
	            if (s.global) {
	                $.active--;
	            }
	            deferred.reject();
	            return deferred;
	        }
	        if (xhr.aborted) {
	            deferred.reject();
	            return deferred;
	        }
	
	        // add submitting element to data if we know it
	        sub = form.clk;
	        if (sub) {
	            n = sub.name;
	            if (n && !sub.disabled) {
	                s.extraData = s.extraData || {};
	                s.extraData[n] = sub.value;
	                if (sub.type == "image") {
	                    s.extraData[n+'.x'] = form.clk_x;
	                    s.extraData[n+'.y'] = form.clk_y;
	                }
	            }
	        }
	
	        var CLIENT_TIMEOUT_ABORT = 1;
	        var SERVER_ABORT = 2;
	                
	        function getDoc(frame) {
	            /* it looks like contentWindow or contentDocument do not
	             * carry the protocol property in ie8, when running under ssl
	             * frame.document is the only valid response document, since
	             * the protocol is know but not on the other two objects. strange?
	             * "Same origin policy" http://en.wikipedia.org/wiki/Same_origin_policy
	             */
	            
	            var doc = null;
	            
	            // IE8 cascading access check
	            try {
	                if (frame.contentWindow) {
	                    doc = frame.contentWindow.document;
	                }
	            } catch(err) {
	                // IE8 access denied under ssl & missing protocol
	                log('cannot get iframe.contentWindow document: ' + err);
	            }
	
	            if (doc) { // successful getting content
	                return doc;
	            }
	
	            try { // simply checking may throw in ie8 under ssl or mismatched protocol
	                doc = frame.contentDocument ? frame.contentDocument : frame.document;
	            } catch(err) {
	                // last attempt
	                log('cannot get iframe.contentDocument: ' + err);
	                doc = frame.document;
	            }
	            return doc;
	        }
	
	        // Rails CSRF hack (thanks to Yvan Barthelemy)
	        var csrf_token = $('meta[name=csrf-token]').attr('content');
	        var csrf_param = $('meta[name=csrf-param]').attr('content');
	        if (csrf_param && csrf_token) {
	            s.extraData = s.extraData || {};
	            s.extraData[csrf_param] = csrf_token;
	        }
	
	        // take a breath so that pending repaints get some cpu time before the upload starts
	        function doSubmit() {
	            // make sure form attrs are set
	            var t = $form.attr2('target'), 
	                a = $form.attr2('action'), 
	                mp = 'multipart/form-data',
	                et = $form.attr('enctype') || $form.attr('encoding') || mp;
	
	            // update form attrs in IE friendly way
	            form.setAttribute('target',id);
	            if (!method || /post/i.test(method) ) {
	                form.setAttribute('method', 'POST');
	            }
	            if (a != s.url) {
	                form.setAttribute('action', s.url);
	            }
	
	            // ie borks in some cases when setting encoding
	            if (! s.skipEncodingOverride && (!method || /post/i.test(method))) {
	                $form.attr({
	                    encoding: 'multipart/form-data',
	                    enctype:  'multipart/form-data'
	                });
	            }
	
	            // support timout
	            if (s.timeout) {
	                timeoutHandle = setTimeout(function() { timedOut = true; cb(CLIENT_TIMEOUT_ABORT); }, s.timeout);
	            }
	
	            // look for server aborts
	            function checkState() {
	                try {
	                    var state = getDoc(io).readyState;
	                    log('state = ' + state);
	                    if (state && state.toLowerCase() == 'uninitialized') {
	                        setTimeout(checkState,50);
	                    }
	                }
	                catch(e) {
	                    log('Server abort: ' , e, ' (', e.name, ')');
	                    cb(SERVER_ABORT);
	                    if (timeoutHandle) {
	                        clearTimeout(timeoutHandle);
	                    }
	                    timeoutHandle = undefined;
	                }
	            }
	
	            // add "extra" data to form if provided in options
	            var extraInputs = [];
	            try {
	                if (s.extraData) {
	                    for (var n in s.extraData) {
	                        if (s.extraData.hasOwnProperty(n)) {
	                           // if using the $.param format that allows for multiple values with the same name
	                           if($.isPlainObject(s.extraData[n]) && s.extraData[n].hasOwnProperty('name') && s.extraData[n].hasOwnProperty('value')) {
	                               extraInputs.push(
	                               $('<input type="hidden" name="'+s.extraData[n].name+'">').val(s.extraData[n].value)
	                                   .appendTo(form)[0]);
	                           } else {
	                               extraInputs.push(
	                               $('<input type="hidden" name="'+n+'">').val(s.extraData[n])
	                                   .appendTo(form)[0]);
	                           }
	                        }
	                    }
	                }
	
	                if (!s.iframeTarget) {
	                    // add iframe to doc and submit the form
	                    $io.appendTo('body');
	                }
	                if (io.attachEvent) {
	                    io.attachEvent('onload', cb);
	                }
	                else {
	                    io.addEventListener('load', cb, false);
	                }
	                setTimeout(checkState,15);
	
	                try {
	                    form.submit();
	                } catch(err) {
	                    // just in case form has element with name/id of 'submit'
	                    var submitFn = document.createElement('form').submit;
	                    submitFn.apply(form);
	                }
	            }
	            finally {
	                // reset attrs and remove "extra" input elements
	                form.setAttribute('action',a);
	                form.setAttribute('enctype', et); // #380
	                if(t) {
	                    form.setAttribute('target', t);
	                } else {
	                    $form.removeAttr('target');
	                }
	                $(extraInputs).remove();
	            }
	        }
	
	        if (s.forceSync) {
	            doSubmit();
	        }
	        else {
	            setTimeout(doSubmit, 10); // this lets dom updates render
	        }
	
	        var data, doc, domCheckCount = 50, callbackProcessed;
	
	        function cb(e) {
	            if (xhr.aborted || callbackProcessed) {
	                return;
	            }
	            
	            doc = getDoc(io);
	            if(!doc) {
	                log('cannot access response document');
	                e = SERVER_ABORT;
	            }
	            if (e === CLIENT_TIMEOUT_ABORT && xhr) {
	                xhr.abort('timeout');
	                deferred.reject(xhr, 'timeout');
	                return;
	            }
	            else if (e == SERVER_ABORT && xhr) {
	                xhr.abort('server abort');
	                deferred.reject(xhr, 'error', 'server abort');
	                return;
	            }
	
	            if (!doc || doc.location.href == s.iframeSrc) {
	                // response not received yet
	                if (!timedOut) {
	                    return;
	                }
	            }
	            if (io.detachEvent) {
	                io.detachEvent('onload', cb);
	            }
	            else {
	                io.removeEventListener('load', cb, false);
	            }
	
	            var status = 'success', errMsg;
	            try {
	                if (timedOut) {
	                    throw 'timeout';
	                }
	
	                var isXml = s.dataType == 'xml' || doc.XMLDocument || $.isXMLDoc(doc);
	                log('isXml='+isXml);
	                if (!isXml && window.opera && (doc.body === null || !doc.body.innerHTML)) {
	                    if (--domCheckCount) {
	                        // in some browsers (Opera) the iframe DOM is not always traversable when
	                        // the onload callback fires, so we loop a bit to accommodate
	                        log('requeing onLoad callback, DOM not available');
	                        setTimeout(cb, 250);
	                        return;
	                    }
	                    // let this fall through because server response could be an empty document
	                    //log('Could not access iframe DOM after mutiple tries.');
	                    //throw 'DOMException: not available';
	                }
	
	                //log('response detected');
	                var docRoot = doc.body ? doc.body : doc.documentElement;
	                xhr.responseText = docRoot ? docRoot.innerHTML : null;
	                xhr.responseXML = doc.XMLDocument ? doc.XMLDocument : doc;
	                if (isXml) {
	                    s.dataType = 'xml';
	                }
	                xhr.getResponseHeader = function(header){
	                    var headers = {'content-type': s.dataType};
	                    return headers[header.toLowerCase()];
	                };
	                // support for XHR 'status' & 'statusText' emulation :
	                if (docRoot) {
	                    xhr.status = Number( docRoot.getAttribute('status') ) || xhr.status;
	                    xhr.statusText = docRoot.getAttribute('statusText') || xhr.statusText;
	                }
	
	                var dt = (s.dataType || '').toLowerCase();
	                var scr = /(json|script|text)/.test(dt);
	                if (scr || s.textarea) {
	                    // see if user embedded response in textarea
	                    var ta = doc.getElementsByTagName('textarea')[0];
	                    if (ta) {
	                        xhr.responseText = ta.value;
	                        // support for XHR 'status' & 'statusText' emulation :
	                        xhr.status = Number( ta.getAttribute('status') ) || xhr.status;
	                        xhr.statusText = ta.getAttribute('statusText') || xhr.statusText;
	                    }
	                    else if (scr) {
	                        // account for browsers injecting pre around json response
	                        var pre = doc.getElementsByTagName('pre')[0];
	                        var b = doc.getElementsByTagName('body')[0];
	                        if (pre) {
	                            xhr.responseText = pre.textContent ? pre.textContent : pre.innerText;
	                        }
	                        else if (b) {
	                            xhr.responseText = b.textContent ? b.textContent : b.innerText;
	                        }
	                    }
	                }
	                else if (dt == 'xml' && !xhr.responseXML && xhr.responseText) {
	                    xhr.responseXML = toXml(xhr.responseText);
	                }
	
	                try {
	                    data = httpData(xhr, dt, s);
	                }
	                catch (err) {
	                    status = 'parsererror';
	                    xhr.error = errMsg = (err || status);
	                }
	            }
	            catch (err) {
	                log('error caught: ',err);
	                status = 'error';
	                xhr.error = errMsg = (err || status);
	            }
	
	            if (xhr.aborted) {
	                log('upload aborted');
	                status = null;
	            }
	
	            if (xhr.status) { // we've set xhr.status
	                status = (xhr.status >= 200 && xhr.status < 300 || xhr.status === 304) ? 'success' : 'error';
	            }
	
	            // ordering of these callbacks/triggers is odd, but that's how $.ajax does it
	            if (status === 'success') {
	                if (s.success) {
	                    s.success.call(s.context, data, 'success', xhr);
	                }
	                deferred.resolve(xhr.responseText, 'success', xhr);
	                if (g) {
	                    $.event.trigger("ajaxSuccess", [xhr, s]);
	                }
	            }
	            else if (status) {
	                if (errMsg === undefined) {
	                    errMsg = xhr.statusText;
	                }
	                if (s.error) {
	                    s.error.call(s.context, xhr, status, errMsg);
	                }
	                deferred.reject(xhr, 'error', errMsg);
	                if (g) {
	                    $.event.trigger("ajaxError", [xhr, s, errMsg]);
	                }
	            }
	
	            if (g) {
	                $.event.trigger("ajaxComplete", [xhr, s]);
	            }
	
	            if (g && ! --$.active) {
	                $.event.trigger("ajaxStop");
	            }
	
	            if (s.complete) {
	                s.complete.call(s.context, xhr, status);
	            }
	
	            callbackProcessed = true;
	            if (s.timeout) {
	                clearTimeout(timeoutHandle);
	            }
	
	            // clean up
	            setTimeout(function() {
	                if (!s.iframeTarget) {
	                    $io.remove();
	                }
	                else { //adding else to clean up existing iframe response.
	                    $io.attr('src', s.iframeSrc);
	                }
	                xhr.responseXML = null;
	            }, 100);
	        }
	
	        var toXml = $.parseXML || function(s, doc) { // use parseXML if available (jQuery 1.5+)
	            if (window.ActiveXObject) {
	                doc = new ActiveXObject('Microsoft.XMLDOM');
	                doc.async = 'false';
	                doc.loadXML(s);
	            }
	            else {
	                doc = (new DOMParser()).parseFromString(s, 'text/xml');
	            }
	            return (doc && doc.documentElement && doc.documentElement.nodeName != 'parsererror') ? doc : null;
	        };
	        var parseJSON = $.parseJSON || function(s) {
	            /*jslint evil:true */
	            return window['eval']('(' + s + ')');
	        };
	
	        var httpData = function( xhr, type, s ) { // mostly lifted from jq1.4.4
	
	            var ct = xhr.getResponseHeader('content-type') || '',
	                xml = type === 'xml' || !type && ct.indexOf('xml') >= 0,
	                data = xml ? xhr.responseXML : xhr.responseText;
	
	            if (xml && data.documentElement.nodeName === 'parsererror') {
	                if ($.error) {
	                    $.error('parsererror');
	                }
	            }
	            if (s && s.dataFilter) {
	                data = s.dataFilter(data, type);
	            }
	            if (typeof data === 'string') {
	                if (type === 'json' || !type && ct.indexOf('json') >= 0) {
	                    data = parseJSON(data);
	                } else if (type === "script" || !type && ct.indexOf("javascript") >= 0) {
	                    $.globalEval(data);
	                }
	            }
	            return data;
	        };
	
	        return deferred;
	    }
	};
	
	/**
	 * ajaxForm() provides a mechanism for fully automating form submission.
	 *
	 * The advantages of using this method instead of ajaxSubmit() are:
	 *
	 * 1: This method will include coordinates for <input type="image" /> elements (if the element
	 *    is used to submit the form).
	 * 2. This method will include the submit element's name/value data (for the element that was
	 *    used to submit the form).
	 * 3. This method binds the submit() method to the form for you.
	 *
	 * The options argument for ajaxForm works exactly as it does for ajaxSubmit.  ajaxForm merely
	 * passes the options argument along after properly binding events for submit elements and
	 * the form itself.
	 */
	$.fn.ajaxForm = function(options) {
	    options = options || {};
	    options.delegation = options.delegation && $.isFunction($.fn.on);
	
	    // in jQuery 1.3+ we can fix mistakes with the ready state
	    if (!options.delegation && this.length === 0) {
	        var o = { s: this.selector, c: this.context };
	        if (!$.isReady && o.s) {
	            log('DOM not ready, queuing ajaxForm');
	            $(function() {
	                $(o.s,o.c).ajaxForm(options);
	            });
	            return this;
	        }
	        // is your DOM ready?  http://docs.jquery.com/Tutorials:Introducing_$(document).ready()
	        log('terminating; zero elements found by selector' + ($.isReady ? '' : ' (DOM not ready)'));
	        return this;
	    }
	
	    if ( options.delegation ) {
	        $(document)
	            .off('submit.form-plugin', this.selector, doAjaxSubmit)
	            .off('click.form-plugin', this.selector, captureSubmittingElement)
	            .on('submit.form-plugin', this.selector, options, doAjaxSubmit)
	            .on('click.form-plugin', this.selector, options, captureSubmittingElement);
	        return this;
	    }
	
	    return this.ajaxFormUnbind()
	        .bind('submit.form-plugin', options, doAjaxSubmit)
	        .bind('click.form-plugin', options, captureSubmittingElement);
	};
	
	// private event handlers
	function doAjaxSubmit(e) {
	    /*jshint validthis:true */
	    var options = e.data;
	    if (!e.isDefaultPrevented()) { // if event has been canceled, don't proceed
	        e.preventDefault();
	        $(e.target).ajaxSubmit(options); // #365
	    }
	}
	
	function captureSubmittingElement(e) {
	    /*jshint validthis:true */
	    var target = e.target;
	    var $el = $(target);
	    if (!($el.is("[type=submit],[type=image]"))) {
	        // is this a child element of the submit el?  (ex: a span within a button)
	        var t = $el.closest('[type=submit]');
	        if (t.length === 0) {
	            return;
	        }
	        target = t[0];
	    }
	    var form = this;
	    form.clk = target;
	    if (target.type == 'image') {
	        if (e.offsetX !== undefined) {
	            form.clk_x = e.offsetX;
	            form.clk_y = e.offsetY;
	        } else if (typeof $.fn.offset == 'function') {
	            var offset = $el.offset();
	            form.clk_x = e.pageX - offset.left;
	            form.clk_y = e.pageY - offset.top;
	        } else {
	            form.clk_x = e.pageX - target.offsetLeft;
	            form.clk_y = e.pageY - target.offsetTop;
	        }
	    }
	    // clear form vars
	    setTimeout(function() { form.clk = form.clk_x = form.clk_y = null; }, 100);
	}
	
	
	// ajaxFormUnbind unbinds the event handlers that were bound by ajaxForm
	$.fn.ajaxFormUnbind = function() {
	    return this.unbind('submit.form-plugin click.form-plugin');
	};
	
	/**
	 * formToArray() gathers form element data into an array of objects that can
	 * be passed to any of the following ajax functions: $.get, $.post, or load.
	 * Each object in the array has both a 'name' and 'value' property.  An example of
	 * an array for a simple login form might be:
	 *
	 * [ { name: 'username', value: 'jresig' }, { name: 'password', value: 'secret' } ]
	 *
	 * It is this array that is passed to pre-submit callback functions provided to the
	 * ajaxSubmit() and ajaxForm() methods.
	 */
	$.fn.formToArray = function(semantic, elements) {
	    var a = [];
	    if (this.length === 0) {
	        return a;
	    }
	
	    var form = this[0];
	    var formId = this.attr('id');
	    var els = semantic ? form.getElementsByTagName('*') : form.elements;
	    var els2;
	
	    if (els && !/MSIE [678]/.test(navigator.userAgent)) { // #390
	        els = $(els).get();  // convert to standard array
	    }
	
	    // #386; account for inputs outside the form which use the 'form' attribute
	    if ( formId ) {
	        els2 = $(':input[form=' + formId + ']').get();
	        if ( els2.length ) {
	            els = (els || []).concat(els2);
	        }
	    }
	
	    if (!els || !els.length) {
	        return a;
	    }
	
	    var i,j,n,v,el,max,jmax;
	    for(i=0, max=els.length; i < max; i++) {
	        el = els[i];
	        n = el.name;
	        if (!n || el.disabled) {
	            continue;
	        }
	
	        if (semantic && form.clk && el.type == "image") {
	            // handle image inputs on the fly when semantic == true
	            if(form.clk == el) {
	                a.push({name: n, value: $(el).val(), type: el.type });
	                a.push({name: n+'.x', value: form.clk_x}, {name: n+'.y', value: form.clk_y});
	            }
	            continue;
	        }
	
	        v = $.fieldValue(el, true);
	        if (v && v.constructor == Array) {
	            if (elements) {
	                elements.push(el);
	            }
	            for(j=0, jmax=v.length; j < jmax; j++) {
	                a.push({name: n, value: v[j]});
	            }
	        }
	        else if (feature.fileapi && el.type == 'file') {
	            if (elements) {
	                elements.push(el);
	            }
	            var files = el.files;
	            if (files.length) {
	                for (j=0; j < files.length; j++) {
	                    a.push({name: n, value: files[j], type: el.type});
	                }
	            }
	            else {
	                // #180
	                a.push({ name: n, value: '', type: el.type });
	            }
	        }
	        else if (v !== null && typeof v != 'undefined') {
	            if (elements) {
	                elements.push(el);
	            }
	            a.push({name: n, value: v, type: el.type, required: el.required});
	        }
	    }
	
	    if (!semantic && form.clk) {
	        // input type=='image' are not found in elements array! handle it here
	        var $input = $(form.clk), input = $input[0];
	        n = input.name;
	        if (n && !input.disabled && input.type == 'image') {
	            a.push({name: n, value: $input.val()});
	            a.push({name: n+'.x', value: form.clk_x}, {name: n+'.y', value: form.clk_y});
	        }
	    }
	    return a;
	};
	
	/**
	 * Serializes form data into a 'submittable' string. This method will return a string
	 * in the format: name1=value1&amp;name2=value2
	 */
	$.fn.formSerialize = function(semantic) {
	    //hand off to jQuery.param for proper encoding
	    return $.param(this.formToArray(semantic));
	};
	
	/**
	 * Serializes all field elements in the jQuery object into a query string.
	 * This method will return a string in the format: name1=value1&amp;name2=value2
	 */
	$.fn.fieldSerialize = function(successful) {
	    var a = [];
	    this.each(function() {
	        var n = this.name;
	        if (!n) {
	            return;
	        }
	        var v = $.fieldValue(this, successful);
	        if (v && v.constructor == Array) {
	            for (var i=0,max=v.length; i < max; i++) {
	                a.push({name: n, value: v[i]});
	            }
	        }
	        else if (v !== null && typeof v != 'undefined') {
	            a.push({name: this.name, value: v});
	        }
	    });
	    //hand off to jQuery.param for proper encoding
	    return $.param(a);
	};
	
	/**
	 * Returns the value(s) of the element in the matched set.  For example, consider the following form:
	 *
	 *  <form><fieldset>
	 *      <input name="A" type="text" />
	 *      <input name="A" type="text" />
	 *      <input name="B" type="checkbox" value="B1" />
	 *      <input name="B" type="checkbox" value="B2"/>
	 *      <input name="C" type="radio" value="C1" />
	 *      <input name="C" type="radio" value="C2" />
	 *  </fieldset></form>
	 *
	 *  var v = $('input[type=text]').fieldValue();
	 *  // if no values are entered into the text inputs
	 *  v == ['','']
	 *  // if values entered into the text inputs are 'foo' and 'bar'
	 *  v == ['foo','bar']
	 *
	 *  var v = $('input[type=checkbox]').fieldValue();
	 *  // if neither checkbox is checked
	 *  v === undefined
	 *  // if both checkboxes are checked
	 *  v == ['B1', 'B2']
	 *
	 *  var v = $('input[type=radio]').fieldValue();
	 *  // if neither radio is checked
	 *  v === undefined
	 *  // if first radio is checked
	 *  v == ['C1']
	 *
	 * The successful argument controls whether or not the field element must be 'successful'
	 * (per http://www.w3.org/TR/html4/interact/forms.html#successful-controls).
	 * The default value of the successful argument is true.  If this value is false the value(s)
	 * for each element is returned.
	 *
	 * Note: This method *always* returns an array.  If no valid value can be determined the
	 *    array will be empty, otherwise it will contain one or more values.
	 */
	$.fn.fieldValue = function(successful) {
	    for (var val=[], i=0, max=this.length; i < max; i++) {
	        var el = this[i];
	        var v = $.fieldValue(el, successful);
	        if (v === null || typeof v == 'undefined' || (v.constructor == Array && !v.length)) {
	            continue;
	        }
	        if (v.constructor == Array) {
	            $.merge(val, v);
	        }
	        else {
	            val.push(v);
	        }
	    }
	    return val;
	};
	
	/**
	 * Returns the value of the field element.
	 */
	$.fieldValue = function(el, successful) {
	    var n = el.name, t = el.type, tag = el.tagName.toLowerCase();
	    if (successful === undefined) {
	        successful = true;
	    }
	
	    if (successful && (!n || el.disabled || t == 'reset' || t == 'button' ||
	        (t == 'checkbox' || t == 'radio') && !el.checked ||
	        (t == 'submit' || t == 'image') && el.form && el.form.clk != el ||
	        tag == 'select' && el.selectedIndex == -1)) {
	            return null;
	    }
	
	    if (tag == 'select') {
	        var index = el.selectedIndex;
	        if (index < 0) {
	            return null;
	        }
	        var a = [], ops = el.options;
	        var one = (t == 'select-one');
	        var max = (one ? index+1 : ops.length);
	        for(var i=(one ? index : 0); i < max; i++) {
	            var op = ops[i];
	            if (op.selected) {
	                var v = op.value;
	                if (!v) { // extra pain for IE...
	                    v = (op.attributes && op.attributes.value && !(op.attributes.value.specified)) ? op.text : op.value;
	                }
	                if (one) {
	                    return v;
	                }
	                a.push(v);
	            }
	        }
	        return a;
	    }
	    return $(el).val();
	};
	
	/**
	 * Clears the form data.  Takes the following actions on the form's input fields:
	 *  - input text fields will have their 'value' property set to the empty string
	 *  - select elements will have their 'selectedIndex' property set to -1
	 *  - checkbox and radio inputs will have their 'checked' property set to false
	 *  - inputs of type submit, button, reset, and hidden will *not* be effected
	 *  - button elements will *not* be effected
	 */
	$.fn.clearForm = function(includeHidden) {
	    return this.each(function() {
	        $('input,select,textarea', this).clearFields(includeHidden);
	    });
	};
	
	/**
	 * Clears the selected form elements.
	 */
	$.fn.clearFields = $.fn.clearInputs = function(includeHidden) {
	    var re = /^(?:color|date|datetime|email|month|number|password|range|search|tel|text|time|url|week)$/i; // 'hidden' is not in this list
	    return this.each(function() {
	        var t = this.type, tag = this.tagName.toLowerCase();
	        if (re.test(t) || tag == 'textarea') {
	            this.value = '';
	        }
	        else if (t == 'checkbox' || t == 'radio') {
	            this.checked = false;
	        }
	        else if (tag == 'select') {
	            this.selectedIndex = -1;
	        }
			else if (t == "file") {
				if (/MSIE/.test(navigator.userAgent)) {
					$(this).replaceWith($(this).clone(true));
				} else {
					$(this).val('');
				}
			}
	        else if (includeHidden) {
	            // includeHidden can be the value true, or it can be a selector string
	            // indicating a special test; for example:
	            //  $('#myForm').clearForm('.special:hidden')
	            // the above would clean hidden inputs that have the class of 'special'
	            if ( (includeHidden === true && /hidden/.test(t)) ||
	                 (typeof includeHidden == 'string' && $(this).is(includeHidden)) ) {
	                this.value = '';
	            }
	        }
	    });
	};
	
	/**
	 * Resets the form data.  Causes all form elements to be reset to their original value.
	 */
	$.fn.resetForm = function() {
	    return this.each(function() {
	        // guard against an input with the name of 'reset'
	        // note that IE reports the reset function as an 'object'
	        if (typeof this.reset == 'function' || (typeof this.reset == 'object' && !this.reset.nodeType)) {
	            this.reset();
	        }
	    });
	};
	
	/**
	 * Enables or disables any matching elements.
	 */
	$.fn.enable = function(b) {
	    if (b === undefined) {
	        b = true;
	    }
	    return this.each(function() {
	        this.disabled = !b;
	    });
	};
	
	/**
	 * Checks/unchecks any matching checkboxes or radio buttons and
	 * selects/deselects and matching option elements.
	 */
	$.fn.selected = function(select) {
	    if (select === undefined) {
	        select = true;
	    }
	    return this.each(function() {
	        var t = this.type;
	        if (t == 'checkbox' || t == 'radio') {
	            this.checked = select;
	        }
	        else if (this.tagName.toLowerCase() == 'option') {
	            var $sel = $(this).parent('select');
	            if (select && $sel[0] && $sel[0].type == 'select-one') {
	                // deselect all other options
	                $sel.find('option').selected(false);
	            }
	            this.selected = select;
	        }
	    });
	};
	
	// expose debug var
	$.fn.ajaxSubmit.debug = false;
	
	// helper fn for console logging
	function log() {
	    if (!$.fn.ajaxSubmit.debug) {
	        return;
	    }
	    var msg = '[jquery.form] ' + Array.prototype.join.call(arguments,'');
	    if (window.console && window.console.log) {
	        window.console.log(msg);
	    }
	    else if (window.opera && window.opera.postError) {
	        window.opera.postError(msg);
	    }
	}
	
	}));
	


/***/ },

/***/ 149:
/***/ function(module, exports, __webpack_require__) {

	/* WEBPACK VAR INJECTION */(function(jQuery) {/* ========================================================================
	 * Bootstrap: modal.js v3.3.7
	 * http://getbootstrap.com/javascript/#modals
	 * ========================================================================
	 * Copyright 2011-2016 Twitter, Inc.
	 * Licensed under MIT (https://github.com/twbs/bootstrap/blob/master/LICENSE)
	 * ======================================================================== */
	
	
	+function ($) {
	  'use strict';
	
	  // MODAL CLASS DEFINITION
	  // ======================
	
	  var Modal = function (element, options) {
	    this.options             = options
	    this.$body               = $(document.body)
	    this.$element            = $(element)
	    this.$dialog             = this.$element.find('.modal-dialog')
	    this.$backdrop           = null
	    this.isShown             = null
	    this.originalBodyPad     = null
	    this.scrollbarWidth      = 0
	    this.ignoreBackdropClick = false
	
	    if (this.options.remote) {
	      this.$element
	        .find('.modal-content')
	        .load(this.options.remote, $.proxy(function () {
	          this.$element.trigger('loaded.bs.modal')
	        }, this))
	    }
	  }
	
	  Modal.VERSION  = '3.3.7'
	
	  Modal.TRANSITION_DURATION = 300
	  Modal.BACKDROP_TRANSITION_DURATION = 150
	
	  Modal.DEFAULTS = {
	    backdrop: true,
	    keyboard: true,
	    show: true
	  }
	
	  Modal.prototype.toggle = function (_relatedTarget) {
	    return this.isShown ? this.hide() : this.show(_relatedTarget)
	  }
	
	  Modal.prototype.show = function (_relatedTarget) {
	    var that = this
	    var e    = $.Event('show.bs.modal', { relatedTarget: _relatedTarget })
	
	    this.$element.trigger(e)
	
	    if (this.isShown || e.isDefaultPrevented()) return
	
	    this.isShown = true
	
	    this.checkScrollbar()
	    this.setScrollbar()
	    this.$body.addClass('modal-open')
	
	    this.escape()
	    this.resize()
	
	    this.$element.on('click.dismiss.bs.modal', '[data-dismiss="modal"]', $.proxy(this.hide, this))
	
	    this.$dialog.on('mousedown.dismiss.bs.modal', function () {
	      that.$element.one('mouseup.dismiss.bs.modal', function (e) {
	        if ($(e.target).is(that.$element)) that.ignoreBackdropClick = true
	      })
	    })
	
	    this.backdrop(function () {
	      var transition = $.support.transition && that.$element.hasClass('fade')
	
	      if (!that.$element.parent().length) {
	        that.$element.appendTo(that.$body) // don't move modals dom position
	      }
	
	      that.$element
	        .show()
	        .scrollTop(0)
	
	      that.adjustDialog()
	
	      if (transition) {
	        that.$element[0].offsetWidth // force reflow
	      }
	
	      that.$element.addClass('in')
	
	      that.enforceFocus()
	
	      var e = $.Event('shown.bs.modal', { relatedTarget: _relatedTarget })
	
	      transition ?
	        that.$dialog // wait for modal to slide in
	          .one('bsTransitionEnd', function () {
	            that.$element.trigger('focus').trigger(e)
	          })
	          .emulateTransitionEnd(Modal.TRANSITION_DURATION) :
	        that.$element.trigger('focus').trigger(e)
	    })
	  }
	
	  Modal.prototype.hide = function (e) {
	    if (e) e.preventDefault()
	
	    e = $.Event('hide.bs.modal')
	
	    this.$element.trigger(e)
	
	    if (!this.isShown || e.isDefaultPrevented()) return
	
	    this.isShown = false
	
	    this.escape()
	    this.resize()
	
	    $(document).off('focusin.bs.modal')
	
	    this.$element
	      .removeClass('in')
	      .off('click.dismiss.bs.modal')
	      .off('mouseup.dismiss.bs.modal')
	
	    this.$dialog.off('mousedown.dismiss.bs.modal')
	
	    $.support.transition && this.$element.hasClass('fade') ?
	      this.$element
	        .one('bsTransitionEnd', $.proxy(this.hideModal, this))
	        .emulateTransitionEnd(Modal.TRANSITION_DURATION) :
	      this.hideModal()
	  }
	
	  Modal.prototype.enforceFocus = function () {
	    $(document)
	      .off('focusin.bs.modal') // guard against infinite focus loop
	      .on('focusin.bs.modal', $.proxy(function (e) {
	        if (document !== e.target &&
	            this.$element[0] !== e.target &&
	            !this.$element.has(e.target).length) {
	          this.$element.trigger('focus')
	        }
	      }, this))
	  }
	
	  Modal.prototype.escape = function () {
	    if (this.isShown && this.options.keyboard) {
	      this.$element.on('keydown.dismiss.bs.modal', $.proxy(function (e) {
	        e.which == 27 && this.hide()
	      }, this))
	    } else if (!this.isShown) {
	      this.$element.off('keydown.dismiss.bs.modal')
	    }
	  }
	
	  Modal.prototype.resize = function () {
	    if (this.isShown) {
	      $(window).on('resize.bs.modal', $.proxy(this.handleUpdate, this))
	    } else {
	      $(window).off('resize.bs.modal')
	    }
	  }
	
	  Modal.prototype.hideModal = function () {
	    var that = this
	    this.$element.hide()
	    this.backdrop(function () {
	      that.$body.removeClass('modal-open')
	      that.resetAdjustments()
	      that.resetScrollbar()
	      that.$element.trigger('hidden.bs.modal')
	    })
	  }
	
	  Modal.prototype.removeBackdrop = function () {
	    this.$backdrop && this.$backdrop.remove()
	    this.$backdrop = null
	  }
	
	  Modal.prototype.backdrop = function (callback) {
	    var that = this
	    var animate = this.$element.hasClass('fade') ? 'fade' : ''
	
	    if (this.isShown && this.options.backdrop) {
	      var doAnimate = $.support.transition && animate
	
	      this.$backdrop = $(document.createElement('div'))
	        .addClass('modal-backdrop ' + animate)
	        .appendTo(this.$body)
	
	      this.$element.on('click.dismiss.bs.modal', $.proxy(function (e) {
	        if (this.ignoreBackdropClick) {
	          this.ignoreBackdropClick = false
	          return
	        }
	        if (e.target !== e.currentTarget) return
	        this.options.backdrop == 'static'
	          ? this.$element[0].focus()
	          : this.hide()
	      }, this))
	
	      if (doAnimate) this.$backdrop[0].offsetWidth // force reflow
	
	      this.$backdrop.addClass('in')
	
	      if (!callback) return
	
	      doAnimate ?
	        this.$backdrop
	          .one('bsTransitionEnd', callback)
	          .emulateTransitionEnd(Modal.BACKDROP_TRANSITION_DURATION) :
	        callback()
	
	    } else if (!this.isShown && this.$backdrop) {
	      this.$backdrop.removeClass('in')
	
	      var callbackRemove = function () {
	        that.removeBackdrop()
	        callback && callback()
	      }
	      $.support.transition && this.$element.hasClass('fade') ?
	        this.$backdrop
	          .one('bsTransitionEnd', callbackRemove)
	          .emulateTransitionEnd(Modal.BACKDROP_TRANSITION_DURATION) :
	        callbackRemove()
	
	    } else if (callback) {
	      callback()
	    }
	  }
	
	  // these following methods are used to handle overflowing modals
	
	  Modal.prototype.handleUpdate = function () {
	    this.adjustDialog()
	  }
	
	  Modal.prototype.adjustDialog = function () {
	    var modalIsOverflowing = this.$element[0].scrollHeight > document.documentElement.clientHeight
	
	    this.$element.css({
	      paddingLeft:  !this.bodyIsOverflowing && modalIsOverflowing ? this.scrollbarWidth : '',
	      paddingRight: this.bodyIsOverflowing && !modalIsOverflowing ? this.scrollbarWidth : ''
	    })
	  }
	
	  Modal.prototype.resetAdjustments = function () {
	    this.$element.css({
	      paddingLeft: '',
	      paddingRight: ''
	    })
	  }
	
	  Modal.prototype.checkScrollbar = function () {
	    var fullWindowWidth = window.innerWidth
	    if (!fullWindowWidth) { // workaround for missing window.innerWidth in IE8
	      var documentElementRect = document.documentElement.getBoundingClientRect()
	      fullWindowWidth = documentElementRect.right - Math.abs(documentElementRect.left)
	    }
	    this.bodyIsOverflowing = document.body.clientWidth < fullWindowWidth
	    this.scrollbarWidth = this.measureScrollbar()
	  }
	
	  Modal.prototype.setScrollbar = function () {
	    var bodyPad = parseInt((this.$body.css('padding-right') || 0), 10)
	    this.originalBodyPad = document.body.style.paddingRight || ''
	    if (this.bodyIsOverflowing) this.$body.css('padding-right', bodyPad + this.scrollbarWidth)
	  }
	
	  Modal.prototype.resetScrollbar = function () {
	    this.$body.css('padding-right', this.originalBodyPad)
	  }
	
	  Modal.prototype.measureScrollbar = function () { // thx walsh
	    var scrollDiv = document.createElement('div')
	    scrollDiv.className = 'modal-scrollbar-measure'
	    this.$body.append(scrollDiv)
	    var scrollbarWidth = scrollDiv.offsetWidth - scrollDiv.clientWidth
	    this.$body[0].removeChild(scrollDiv)
	    return scrollbarWidth
	  }
	
	
	  // MODAL PLUGIN DEFINITION
	  // =======================
	
	  function Plugin(option, _relatedTarget) {
	    return this.each(function () {
	      var $this   = $(this)
	      var data    = $this.data('bs.modal')
	      var options = $.extend({}, Modal.DEFAULTS, $this.data(), typeof option == 'object' && option)
	
	      if (!data) $this.data('bs.modal', (data = new Modal(this, options)))
	      if (typeof option == 'string') data[option](_relatedTarget)
	      else if (options.show) data.show(_relatedTarget)
	    })
	  }
	
	  var old = $.fn.modal
	
	  $.fn.modal             = Plugin
	  $.fn.modal.Constructor = Modal
	
	
	  // MODAL NO CONFLICT
	  // =================
	
	  $.fn.modal.noConflict = function () {
	    $.fn.modal = old
	    return this
	  }
	
	
	  // MODAL DATA-API
	  // ==============
	
	  $(document).on('click.bs.modal.data-api', '[data-toggle="modal"]', function (e) {
	    var $this   = $(this)
	    var href    = $this.attr('href')
	    var $target = $($this.attr('data-target') || (href && href.replace(/.*(?=#[^\s]+$)/, ''))) // strip for ie7
	    var option  = $target.data('bs.modal') ? 'toggle' : $.extend({ remote: !/#/.test(href) && href }, $target.data(), $this.data())
	
	    if ($this.is('a')) e.preventDefault()
	
	    $target.one('show.bs.modal', function (showEvent) {
	      if (showEvent.isDefaultPrevented()) return // only register focus restorer if modal will actually get shown
	      $target.one('hidden.bs.modal', function () {
	        $this.is(':visible') && $this.trigger('focus')
	      })
	    })
	    Plugin.call($target, option, this)
	  })
	
	}(jQuery);
	
	/* WEBPACK VAR INJECTION */}.call(exports, __webpack_require__(1)))

/***/ },

/***/ 330:
/***/ function(module, exports, __webpack_require__, __webpack_module_template_argument_0__) {

	// 7.2.2 IsArray(argument)
	var cof = __webpack_require__(__webpack_module_template_argument_0__);
	module.exports = Array.isArray || function isArray(arg){
	  return cof(arg) == 'Array';
	};

/***/ }

});
//# sourceMappingURL=create.js.map