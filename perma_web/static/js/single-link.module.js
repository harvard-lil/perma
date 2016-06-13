var SingleLinkModule = {},
  resizeTimeout = null;

SingleLinkModule.init = function () {
  SingleLinkModule.adjustTopMargin();
  var button = document.getElementById("details-button");
  button.onclick = function () {
    SingleLinkModule.handleShowDetails();
    return false;
  };
};

SingleLinkModule.handleShowDetails = function () {
  var button = document.getElementById("details-button");
  button.textContent = button.textContent.indexOf("Show record details") !== -1 ? "Hide record details" : "Show record details";
  var header = document.getElementsByTagName('header')[0];
  header.classList.toggle('_activeDetails');
};

SingleLinkModule.adjustTopMargin = function () {
  var wrapper = document.getElementsByClassName("capture-wrapper")[0];
  var header = document.getElementsByTagName('header')[0];
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
