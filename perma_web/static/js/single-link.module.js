window.SingleLinkModule = window.SingleLinkModule || {};
var resizeTimeout, wrapper;

SingleLinkModule.detailsButton = document.getElementById("details-button");
SingleLinkModule.detailsTray = document.getElementById("collapse-details");
SingleLinkModule.init = function () {
  SingleLinkModule.adjustTopMargin();
  var clicked = false;
  if (SingleLinkModule.detailsButton) {
    SingleLinkModule.detailsButton.onclick = function () {
      clicked = !clicked;
      SingleLinkModule.handleShowDetails(clicked);
    };
  }
};

SingleLinkModule.handleShowDetails = function (open) {
  SingleLinkModule.detailsButton.textContent = open ? "Hide record details":"Show record details";
  SingleLinkModule.detailsTray.style.display = open ? "block" : "none";
};

SingleLinkModule.adjustTopMargin = function () {
  wrapper = document.getElementsByClassName("capture-wrapper")[0];
  var header = document.getElementsByTagName('header')[0];
  if (!wrapper) return;
  wrapper.style.marginTop = header.offsetHeight+"px";
};


(function() {
  SingleLinkModule.init();
  window.onresize = function(){
    if (resizeTimeout != null)
      clearTimeout(resizeTimeout);
    resizeTimeout = setTimeout( function () {
      SingleLinkModule.adjustTopMargin();
    }, 200);
  };

})();
