import '../css/style-responsive-archive.scss';

var resizeTimeout, wrapper;

export var detailsButton = document.getElementById("details-button");
var detailsTray = document.getElementById("collapse-details");
var viewMode = document.getElementsByClassName("view-mode")[0];

function init () {
  adjustTopMargin();
  var clicked = false;
  if (detailsButton) {
    detailsButton.onclick = function () {
      clicked = !clicked;
      handleShowDetails(clicked);
    };
  }

  window.onresize = function(){
    if (resizeTimeout != null)
      clearTimeout(resizeTimeout);
    resizeTimeout = setTimeout(adjustTopMargin, 200);
  };
}

export function handleShowDetails (open) {
  detailsButton.textContent = open ? "Hide record details":"Show record details";
  detailsTray.style.display = open ? "block" : "none";
  viewMode.style.display = open ? "none" : "block" ;
}

function adjustTopMargin () {
  let wrapper = document.getElementsByClassName("capture-wrapper")[0];
  let header = document.getElementsByTagName('header')[0];
  if (!wrapper) return;
  wrapper.style.marginTop = `${header.offsetHeight}px`;
  wrapper.style.height = `calc(100% - ${header.offsetHeight}px)`;
}

init();
