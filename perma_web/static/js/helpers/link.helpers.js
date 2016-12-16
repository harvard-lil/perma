var DOMHelpers = require('./dom.helpers.js');
var APIModule = require('./api.module.js');
require('./local-datetime.js');  // add .format() to Date object


export function findFaviconURL(linkObj) {
  if (!linkObj.captures) return '';

  var favCapture = linkObj.captures.filter(function(capture){
    return capture.role == 'favicon' && capture.status == 'success'
  });

  return favCapture[0] ? favCapture[0].playback_url : '';
}

export function generateLinkFields(link, query) {
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

var timeouts = {};
// save changes in a given text box to the server
export function saveInput(guid, inputElement, statusElement, name, callback) {
  DOMHelpers.changeHTML(statusElement, 'Saving...');

  var timeoutKey = guid+name;
  if(timeouts[timeoutKey])
    clearTimeout(timeouts[timeoutKey]);

  // use a setTimeout so notes are only saved once every half second
  timeouts[timeoutKey] = setTimeout(function () {
    var data = {};
    data[name] = DOMHelpers.getValue(inputElement);
    APIModule.request("PATCH", '/archives/' + guid + '/', data).done(function(data){
      DOMHelpers.changeHTML(statusElement, 'Saved!');
      if (callback)
        callback(data);
    });
  }, 500);
}
