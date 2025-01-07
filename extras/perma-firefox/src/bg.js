browser.browserAction.onClicked.addListener(function(tab){
  browser.tabs.create({
    "url": "https://perma.cc/service/bookmarklet-create/?v=1&url=" + encodeURIComponent(tab.url)
  });
});
