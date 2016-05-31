var SingleLinkModule = {};

SingleLinkModule.init = function () {
  SingleLinkModule.adjustTopMargin();
  var button = document.getElementById("details-button");
  button.onclick = function () {
    SingleLinkModule.handleShowDetails(button);
    return false;
  };
};

SingleLinkModule.handleShowDetails = function () {
  var el = document.getElementById("details-button");
  var showingDetails = el.textContent.match("Show");
  showingDetails && showingDetails.length > 0 ? "Hide record details" : "Show record details"
  var header = document.getElementsByTagName('header')[0];
  header.classList.toggle('_activeDetails');
}

SingleLinkModule.adjustTopMargin = function () {
  var button = document.getElementById("details-button");
  var wrapper = document.getElementsByClassName("capture-wrapper")[0];
  var headerHeight = document.getElementsByTagName('header')[0].clientHeight;
  wrapper.style.marginTop = headerHeight;
}

SingleLinkModule.init();
