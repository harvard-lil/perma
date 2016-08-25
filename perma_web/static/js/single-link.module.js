window.SingleLinkModule = window.SingleLinkModule || {};
var resizeTimeout, wrapper;

SingleLinkModule.detailsButton = document.getElementById("details-button");

SingleLinkModule.init = function () {
  SingleLinkModule.adjustTopMargin();

  if (SingleLinkModule.detailsButton) {
    SingleLinkModule.detailsButton.onclick = function () {
      SingleLinkModule.handleShowDetails();
      return false;
    };
  }
};

SingleLinkModule.handleShowDetails = function () {
  SingleLinkModule.detailsButton.textContent = SingleLinkModule.detailsButton.textContent.indexOf("Show") > -1 ? "Hide record details":"Show record details";
  /* jquery does the heavy lifting for us here, return if it exists */
  if (typeof($) != 'undefined') return;
  header.classList.toggle('_activeDetails');
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
