var resizeTimeout, wrapper;

export var detailsButton = document.getElementById("details-button");
var detailsTray = document.getElementById("collapse-details");
var viewMode = document.getElementsByClassName("view-mode")[0];

var copyBtn = document.getElementById('copy-link-btn');
var copyText = copyBtn?.querySelector('.copy-text');
var copiedText = copyBtn?.querySelector('.copied-text');

function init () {
  adjustTopMargin();
  var clicked = false;
  if (detailsButton) {
    detailsButton.onclick = function () {
      clicked = !clicked;
      handleShowDetails(clicked);
    };
  }

  initCopyLink();

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

function initCopyLink() {
  if (copyBtn) {
    copyBtn.addEventListener('click', function() {
      const permalinkUrl = document.getElementById('permalink-url').textContent;
      
      // Modern clipboard API
      if (navigator.clipboard && window.isSecureContext) {
        navigator.clipboard.writeText(permalinkUrl).then(function() {
          showCopiedFeedback();
        }).catch(function(err) {
          console.error('Failed to copy: ', err);
          fallbackCopyTextToClipboard(permalinkUrl);
        });
      } else {
        // Fallback for older browsers
        fallbackCopyTextToClipboard(permalinkUrl);
      }
    });
  }
}

function showCopiedFeedback() {
  if (copyBtn) {
    copyBtn.classList.add('copied');
    
    const originalTitle = copyBtn.title;
    copyBtn.title = 'Copied!';
    
    // Reset after 2 seconds
    setTimeout(function() {
      copyBtn.classList.remove('copied');
      copyBtn.title = originalTitle;
    }, 2000);
  }
}

function fallbackCopyTextToClipboard(text) {
  const textArea = document.createElement('textarea');
  textArea.value = text;
  textArea.style.position = 'fixed';
  textArea.style.left = '-999999px';
  textArea.style.top = '-999999px';
  document.body.appendChild(textArea);
  textArea.focus();
  textArea.select();
  
  try {
    // I know this is deprecated, using it purely as a fallback 
    // mechanism for browsers that do not support the clipboard api
    const successful = document.execCommand('copy');
    if (successful) {
      showCopiedFeedback();
    }
  } catch (err) {
    console.error('Fallback copy failed: ', err);
  }
  
  document.body.removeChild(textArea);
}

init();
