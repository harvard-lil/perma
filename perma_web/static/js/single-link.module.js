var SingleLinkModule = {},
  resizeTimeout = null,
  wrapper;

SingleLinkModule.init = function () {
  SingleLinkModule.adjustTopMargin();
  var button = document.getElementById("details-button");
  if (button) {    
    button.onclick = function () {
      SingleLinkModule.handleShowDetails();
      return false;
    };
  }
};

SingleLinkModule.handleShowDetails = function () {
  var button = document.getElementById("details-button");
  button.textContent = button.textContent.indexOf("Show record details") !== -1 ? "Hide record details" : "Show record details";
  var header = document.getElementsByTagName('header')[0];
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
