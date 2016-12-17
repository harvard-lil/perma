chrome.browserAction.onClicked.addListener(function(tab){
  chrome.tabs.create({
    "url": chrome.extension.getURL('https://perma.cc/service/bookmarklet-create/?v=1&url=' + encodeURIComponent(tab.url))
  });
});


