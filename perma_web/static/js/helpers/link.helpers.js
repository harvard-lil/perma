import { changeHTML, getValue } from './dom.helpers.js'
import { request } from './api.module.js';
import './local-datetime.js' // add .format() to Date object

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
  // mark the capture as pending if either the primary or the screenshot capture are pending
  // mark the capture as failed if both the primary and the screenshot capture failed.
  // (ignore the favicon capture)
  let primary_failed = false;
  let screenshot_failed = false;
  let primary_pending = false;
  let screenshot_pending = false;
  link.captures.forEach(function(c){
    if (c.role=="primary"){
      if (c.status=="pending"){
        primary_pending = true;
      } else if (c.status=="failed"){
        primary_failed = true;
      }
    }
    if (c.role=="screenshot"){
      if (c.status=="pending"){
        screenshot_pending = true;
      } else if (c.status=="failed"){
        screenshot_failed = true;
      }
    }
  });
  if (primary_pending || screenshot_pending){
    link.is_pending = true;
  };
  if (primary_failed && screenshot_failed){
    link.is_failed = true;
  };
  return link;
}

var timeouts = {};
// save changes in a given text box to the server
export function saveInput(guid, inputElement, statusElement, name, callback) {
  changeHTML(statusElement, 'Saving...');

  var timeoutKey = guid+name;
  if(timeouts[timeoutKey])
    clearTimeout(timeouts[timeoutKey]);

  // use a setTimeout so notes are only saved once every half second
  timeouts[timeoutKey] = setTimeout(function () {
    var data = {};
    data[name] = getValue(inputElement);
    request("PATCH", '/archives/' + guid + '/', data).done(function(data){
      changeHTML(statusElement, 'Saved!');
      if (callback)
        callback(data);
    });
  }, 500);
}
