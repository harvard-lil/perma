window.LinkHelpers = window.LinkHelpers || {};

LinkHelpers.findFaviconURL = function(linkObj) {
  if (!linkObj.captures) return '';

  var favCapture = linkObj.captures.filter(function(capture){
    return capture.role == 'favicon' && capture.status == 'success'
  });

  return favCapture[0] ? favCapture[0].playback_url : '';
}

LinkHelpers.generateLinkFields = function(link, query) {
  link.favicon_url = this.findFaviconURL(link);
  if (window.host) {
    link.local_url = window.host + '/' + link.guid;
  }
  if (query && link.notes) {
    link.search_query_in_notes = (query && link.notes.indexOf(query) > -1);
  }
  link.expiration_date_formatted = new Date(link.expiration_date).format("F j, Y");
  link.creation_timestamp_formatted = new Date(link.creation_timestamp).format("F j, Y");
  if (Date.now() < Date.parse(link.archive_timestamp)) {
    link.delete_available = true;
  }
  return link;
}
