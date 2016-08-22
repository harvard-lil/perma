window.LinkHelpers = window.LinkHelpers || {};

LinkHelpers.findFaviconURL = function(linkObj) {
  if (!linkObj.captures) return '';

  var favCapture = linkObj.captures.filter(function(capture){
    return capture.role == 'favicon' && capture.status == 'success'
  });

  return favCapture[0] ? favCapture[0].playback_url : '';
}
