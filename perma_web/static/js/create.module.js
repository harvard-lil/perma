var Spinner = require('spin.js');
require('jquery-form');  // add jquery support for ajaxSubmit/ajaxForm
require('bootstrap-js/modal');  // add .modal to jquery

var Helpers = require('./helpers/general.helpers.js');
var DOMHelpers = require('./helpers/dom.helpers.js');
var HandlebarsHelpers = require('./helpers/handlebars.helpers.js');
var APIModule = require('./helpers/api.module.js');

var newGUID = null;
var refreshIntervalIds = [];
var spinner;
var organizations = {};
var localStorageKey = Helpers.variables.localStorageKey;


export var ls = {
  getAll: function () {
    var folders = Helpers.jsonLocalStorage.getItem(localStorageKey);
    return folders || {};
  },
  getCurrent: function () {
    var folders = ls.getAll();
    return folders[current_user.id] || {};
  },
  setCurrent: function (orgId, folderId) {
    folderId = folderId ? folderId : 'default';

    var selectedFolders = ls.getAll();
    selectedFolders[current_user.id] = {'folderId': folderId, 'orgId': orgId};

    Helpers.jsonLocalStorage.setItem(localStorageKey, selectedFolders);
    exports.updateLinker();  // call via exports to enable Jasmine spyOn
    Helpers.triggerOnWindow("dropdown.selectionChange");
  }
};

// Get parameter by name
// from https://stackoverflow.com/questions/901115/how-can-i-get-query-string-values-in-javascript
function getParameterByName (name) {
  name = name.replace(/[\[]/, "\\[").replace(/[\]]/, "\\]");
  var regex = new RegExp("[\\?&]" + name + "=([^&#]*)"),
    results = regex.exec(location.search);
  return results == null ? "" : decodeURIComponent(results[1].replace(/\+/g, " "));
}

function linkIt (data) {
  // Success message from API. We should have a GUID now (but the
  // archive is still be generated)
  // Clear any error messages out
  DOMHelpers.removeElement('.error-row');

  newGUID = data.guid;

  refreshIntervalIds.push(setInterval(check_status, 2000));
}

function linkNot (jqXHR) {
  // The API told us something went wrong.

  if (jqXHR.status == 401) {
    // special handling if user becomes unexpectedly logged out
    APIModule.showError(jqXHR);
  } else {
    var message = "";
    if (jqXHR.status == 400 && jqXHR.responseText) {
      var errors = JSON.parse(jqXHR.responseText).archives;
      for (var prop of Object.keys(errors)) {
        message += errors[prop] + " ";
      }
    }

    var upload_allowed = true;
    if (message.indexOf("limit") > -1) {
      $('.links-remaining').text('0');
      upload_allowed = false;
    }

    var templateArgs = {
      message: message || "Error " + jqXHR.status,
      upload_allowed: upload_allowed,
      contact_url: contact_url
    };

    changeTemplate('#error-template', templateArgs, '#error-container');

    $('.create-errors').addClass('_active');
    $('#error-container').hide().fadeIn(0);
  }
  toggleCreateAvailable();
}

/* Handle an upload - start */
function uploadNot (jqXHR) {
  // Display an error message in our upload modal

  // special handling if user becomes unexpectedly logged out
  if(jqXHR.status == 401){
    APIModule.showError(jqXHR);
    return;
  }
  var reasons = [],
    response;

  try {
    response = jQuery.parseJSON(jqXHR.responseText);
  } catch (e) {
    response = jqXHR.responseText;
  }

  DOMHelpers.hideElement('.spinner');

  $('.js-warning').remove();
  $('.has-error').removeClass('has-error');
  if (response.archives) {
    // If error message comes in as {archive:{file:"message",url:"message"}},
    // show appropriate error message next to each field.
    for(var key in response.archives) {
      if(response.archives.hasOwnProperty(key)) {
        var input = $('#'+key);
        if(input.length){
          input.after('<span class="help-block js-warning">'+response.archives[key]+'</span>');
          input.closest('div').addClass('has-error');
        } else {
          reasons.push(response.archives[key]);
        }
      }
    }
  } else if (response.reason) {
    reasons.push(response.reason);
  } else {
    reasons.push(response);
  }

  $('#upload-error').text('Upload failed. ' + reasons.join(". "));
  DOMHelpers.toggleBtnDisable('#uploadLinky', false);
  DOMHelpers.toggleBtnDisable('.cancel', false);
}

function uploadIt (data) {
  // If a user wants to upload their own screen capture, we display
  // a modal and the form in that modal is handled here
  $('#archive-upload').modal('hide');

  window.location.href = '/' + data.guid;
}

function upload_form () {
  $('#upload-error').text('');
  $('#archive_upload_form input[name="url"]').val($('#rawUrl').val());
  $('#archive-upload').modal('show');
  return false;
}

/* Handle the the main action (enter url, hit the button) button - start */

function toggleCreateAvailable() {
  // Get our spinner going and display a "we're working" message
  var $addlink = $('#addlink');
  if ($addlink.hasClass('_isWorking')) {
    $addlink.html('Create Perma Link').removeAttr('disabled').removeClass('_isWorking');
    spinner.stop();
    $('#rawUrl, #organization_select_form button').removeAttr('disabled');
    $('#links-remaining-message').removeClass('_isWorking');
  } else {
    $addlink.html('<div id="capture-status">Creating your Perma Link</div>').attr('disabled', 'disabled').addClass('_isWorking');
    // spinner opts -- see http://spin.js.org/
    spinner = new Spinner({lines: 15, length: 2, width: 2, radius: 9, corners: 0, color: '#2D76EE', trail: 50, top: '12px'});
    spinner.spin($addlink[0]);
    $('#rawUrl, #organization_select_form button').attr('disabled', 'disabled');
    $('#links-remaining-message').addClass('_isWorking');
  }
}

/* The plan is to set a timer to periodically check if the thumbnail
 exists. Once it does, we append it to the page and clear the
 thumbnail. The reason we're keeping a list of interval IDs rather
 than just one is as a hacky solution to the problem of a user
 creating a Perma link for some URL and then immediately clicking
 the button again for the same URL. Since all these requests are
 done with AJAX, that results in two different interval IDs getting
 created. Both requests will end up completing but the old interval
 ID will be overwritten and never cleared, causing a bunch of copies
 of the screenshot to get appended to the page. We thus just append
 them to the list and then clear the whole list once the request
 succeeds. */

function check_status () {

  // Check our status service to see if we have archiving jobs pending
  var request = APIModule.request("GET", "/user/capture_jobs/" + newGUID + "/");
  request.done(function(data) {
    // While status is pending or in progress, update progress display
    if (data.status == "pending") {
      // todo -- could display data.queue_position here

    } else if (data.status == "in_progress") {

      // add progress bar if doesn't exist
      if (!$('#capture-progress-bar').length) {
        $('#addlink').append(
          '<div style="position: relative; width: 100%; height: 0">'+
          '  <div id="capture-progress-bar" class="progress" style="width: 100%; height: 0.3em; position:absolute; margin-bottom: 0">' +
          '    <div class="progress-bar" role="progressbar" aria-valuenow="0" aria-valuemin="0" aria-valuemax="100" style="width: 0; background-color: #2D76EE">' +
          '      <span class="sr-only">0% Complete</span>' +
          '    </div>' +
          '  </div>' +
          '</div>');
      }

      // update progress
      var progress = data.step_count/5*100;
      $('#capture-progress-bar .progress-bar').attr('aria-valuenow', progress).css('width', progress+'%').find('span').text(progress+'% Complete');

    } else {

      // Capture is done (one way or another) -- clear out our pending jobs
      $.each(refreshIntervalIds, function(ndx, id) {
        clearInterval(id);
      });

      // If we succeeded, forward to the new archive
      if (data.status == "completed") {
        window.location.href = "/" + newGUID;

        // Else show failure message and reset form.
      } else {
        var templateArgs = {message: "Error: URL capture failed."};
        changeTemplate('#error-template', templateArgs, '#error-container');

        $('#error-container').removeClass('_hide _success _wait').addClass('_error');

        // Toggle our create button
        toggleCreateAvailable();
      }
    }
  });
}

/* Our polling function for the thumbnail completion - end */
export function populateWithUrl () {
  var url = Helpers.getWindowLocationSearch().split("url=")[1];
  if (url) {
    url = decodeURIComponent(url);
    DOMHelpers.setInputValue("#rawUrl", url);
    return url;
  }
}

export function updateLinker () {
  var userSettings = ls.getCurrent();
  var currentOrg = userSettings.orgId;
  var organizationsExist = Object.keys(organizations).length;
  if (!userSettings.folderId && organizationsExist) {
    $('#addlink').attr('disabled', 'disabled');
    return;
  }

  if (!currentOrg && links_remaining < 1) {
    $('#addlink').attr('disabled', 'disabled');
  } else {
    $('#addlink').removeAttr('disabled');
  }

  if (organizations[currentOrg] && organizations[currentOrg]['default_to_private']) {
    $('#addlink').text("Create Private Perma Link");
  } else {
    $('#addlink').text("Create Perma Link");
  }

  if (organizations[currentOrg] && organizations[currentOrg]['default_to_private']) {
    $('#linker').addClass('_isPrivate');
    // add the little eye icon if org is private
    $('#organization_select_form')
      .find('.dropdown-toggle > span')
      .addClass('ui-private');
  } else {
    $('#linker').removeClass('_isPrivate')
  }

  var already_warned = Helpers.getCookie("suppress_link_warning");
  if (already_warned != "true" &&
      currentOrg == 'None' &&
      is_org_user == "True" &&
      links_remaining == 3){
    var message = "Your personal links for the month are almost used up! Create more links in 'unlimited' folders."
    Helpers.informUser(message, 'danger');
    Helpers.setCookie("suppress_link_warning", "true", 120);
  }
}

function updateAffiliationPath (currentOrg, path) {

  var stringPath = path.join(" &gt; ");
  stringPath += "<span></span>";

  $('#organization_select_form')
    .find('.dropdown-toggle')
    .html(stringPath);

  if (organizations[currentOrg] && organizations[currentOrg]['default_to_private']) {
    $('#organization_select_form')
      .find('.dropdown-toggle > span')
      .addClass('ui-private');
  }

  if (!currentOrg || currentOrg === "None") {
    $('#organization_select_form')
      .find('.dropdown-toggle > span')
      .addClass('links-remaining')
      .text(links_remaining);
  }
}

export function updateLinksRemaining (links_num) {
  links_remaining = links_num;
  DOMHelpers.changeText('.links-remaining', links_remaining);
}

function handleSelectionChange (data) {
  updateLinker();

  if (data && data.path) {
    updateAffiliationPath(data.orgId, data.path);
  }
}


function setupEventHandlers () {
  $(window)
    .off('FolderTreeModule.selectionChange')
    .off('FolderTreeModule.updateLinksRemaining')
    .on('FolderTreeModule.selectionChange', function(evt, data){
      if (typeof data !== 'object') data = JSON.parse(data);
      handleSelectionChange(data);
    })
    .on('FolderTreeModule.updateLinksRemaining', function(evt, data){
      updateLinksRemaining(data)
    });

  // When a user uploads their own capture
  $(document).on('submit', '#archive_upload_form', function() {
    DOMHelpers.toggleBtnDisable('#uploadLinky', true);
    DOMHelpers.toggleBtnDisable('.cancel', true);
    var extraUploadData = {},
      selectedFolder = ls.getCurrent().folderId;
    if(selectedFolder)
      extraUploadData.folder = selectedFolder;
    spinner = new Spinner({lines: 15, length: 2, width: 2, radius: 9, corners: 0, color: '#2D76EE', trail: 50, top: '300px'});
    spinner.spin(this);
    $(this).ajaxSubmit({
                         data: extraUploadData,
                         success: uploadIt,
                         error: uploadNot
                       });
    return false;
  });

  // Toggle users dropdown
  $('#dashboard-users')
    .click(function(){ $('.users-secondary').toggle(); });

  // When a new url is entered into our form
  $('#linker').submit(function() {
    var $this = $(this);
    var linker_data = {
      url: $this.find("input[name=url]").val(),
      human: true
    };
    var selectedFolder = ls.getCurrent().folderId;

    if(selectedFolder)
      linker_data.folder = selectedFolder;

    // Start our spinner and disable our input field with just a tiny delay
    window.setTimeout(toggleCreateAvailable, 150);

    $.ajax($this.attr('action'), {
      method: $this.attr('method'),
      contentType: 'application/json',
      data: JSON.stringify(linker_data),
      success: linkIt,
      error: linkNot
    });

    return false;
  });
}

/* templateContainer: DOM selector, where the newly rendered template will live */
function changeTemplate(template, args, templateContainer) {
  var renderedTemplate = HandlebarsHelpers.renderTemplate(template, args)
  DOMHelpers.changeHTML(templateContainer, renderedTemplate);
}

export function init () {
  // Dismiss browser tools message
  $('.close-browser-tools').click(function(){
    $('#browser-tools-message').hide();
    Helpers.setCookie("suppress_reminder", "true", 120);
  });

  var $organization_select = $("#organization_select");

  // populate organization dropdown
  APIModule.request("GET", "/user/organizations/", {limit: 300, order_by:'registrar'})
    .success(function(data) {

      var sorted = [];
      Object.keys(data.objects).sort(function(a,b){
        return data.objects[a].registrar < data.objects[b].registrar ? -1 : 1;
      }).forEach(function(key){
        sorted.push(data.objects[key]);
      });
      data.objects = sorted;

      if (data.objects.length > 0) {
        var optgroup = data.objects[0].registrar;
        $organization_select.append("<li class='dropdown-header'>" + optgroup + "</li>");
        data.objects.map(function (organization) {
          organizations[organization.id] = organization;

          if(organization.registrar !== optgroup) {
            optgroup = organization.registrar;
            $organization_select.append("<li class='dropdown-header'>" + optgroup + "</li>");
          }
          var opt_text = organization.name;
          if (organization.default_to_private) {
            opt_text += ' <span class="ui-private">(Private)</span>';
          }
          $organization_select.append("<li><a href='#' data-orgid='"+organization.id+"' data-orgfolderid='"+organization.shared_folder.id+"'>" + opt_text + " <span class='links-unlimited'>unlimited</span></a></li>");
        });

        $organization_select.append("<li class='personal-links'><a href='#'> Personal Links <span class='links-remaining'>" + links_remaining + "</span></a></li>");
        updateLinker();
      } else {
        // select My Folder for users with no orgs and no saved selections
        var selectedFolder = ls.getCurrent().folderId;
        if (!selectedFolder) { ls.setCurrent(); }
      }
    });

  // handle dropdown changes
  $organization_select.on('click', 'a', function(){
    ls.setCurrent(+$(this).attr('data-orgid'), +$(this).attr('data-orgfolderid'));
  });

  // handle upload form button
  $(document.body).on('click', '#upload-form-button', upload_form);

  setupEventHandlers();
  populateWithUrl();

}
