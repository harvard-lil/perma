chrome.browserAction.onClicked.addListener(function(tab) {
  window.open('https://perma.cc/service/bookmarklet-create/?v=1&url=' + encodeURIComponent(tab.url));
  window.focus();
});
