/******/ (function(modules) { // webpackBootstrap
/******/ 	// The module cache
/******/ 	var installedModules = {};
/******/
/******/ 	// The require function
/******/ 	function __webpack_require__(moduleId) {
/******/
/******/ 		// Check if module is in cache
/******/ 		if(installedModules[moduleId])
/******/ 			return installedModules[moduleId].exports;
/******/
/******/ 		// Create a new module (and put it into the cache)
/******/ 		var module = installedModules[moduleId] = {
/******/ 			exports: {},
/******/ 			id: moduleId,
/******/ 			loaded: false
/******/ 		};
/******/
/******/ 		// Execute the module function
/******/ 		modules[moduleId].call(module.exports, module, module.exports, __webpack_require__);
/******/
/******/ 		// Flag the module as loaded
/******/ 		module.loaded = true;
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
/******/ 	// __webpack_public_path__
/******/ 	__webpack_require__.p = "";
/******/
/******/ 	// Load entry module and return exports
/******/ 	return __webpack_require__(0);
/******/ })
/************************************************************************/
/******/ ({

/***/ 0:
/***/ function(module, exports, __webpack_require__) {

	module.exports = __webpack_require__(199);


/***/ },

/***/ 199:
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

/******/ });
//# sourceMappingURL=single-link.js.map