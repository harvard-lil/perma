let Spinner = require('spin.js');
require('jquery-form');  // add jquery support for ajaxSubmit/ajaxForm
require('bootstrap-js/modal');  // add .modal to jquery

let Helpers = require('./helpers/general.helpers.js');
let DOMHelpers = require('./helpers/dom.helpers.js');
let APIModule = require('./helpers/api.module.js');
let ProgressBarHelper = require('./helpers/progress-bar.helper.js');
let Modals = require('./modals.module.js');

// templates
let selectedFolderTemplate = require("./hbs/selected-folder-template.handlebars");
let orgListTemplate = require("./hbs/org-list-template.handlebars");
let errorTemplate = require("./hbs/error-template.handlebars");

let currentFolder;
let currentFolderPrivate;
// links_remaining is available from the global scope, set by the Django template
// link_creation_allowed is available from the global scope, set by the Django template
let newGUID = null;
let organizations = {};
let progress_bar;
let spinner = new Spinner({lines: 15, length: 2, width: 2, radius: 9, corners: 0, color: '#2D76EE', trail: 50, top: '12px'});
let uploadFormSpinner = new Spinner({lines: 15, length: 2, width: 2, radius: 9, corners: 0, color: '#2D76EE', trail: 50, top: '300px'});

// elements in the DOM, retrieved during init()
let $browserToolsMessage, $createButton, $createForm, $closeBrowserTools, $createErrors,
    $errorContainer, $linksRemaining, $linksRemainingMessage, $organizationDropdown,
    $organizationDropdownButton, $organizationSelectForm, $uploadValidationError,
    $uploadForm, $uploadFormUrl, $uploadModal, $url, $personalLinksBanner;


//
// PERMA LINK CREATION HELPERS
//

function toggleInProgress() {
  if ($createButton.hasClass('_isWorking')) {
    // we're done
    updateButtonPrivacy();
    $createButton.prop('disabled', false).removeClass('_isWorking');
    spinner.stop();
    $url.prop('disabled', false);
    $organizationDropdownButton.prop('disabled', false);
    // this looks kind of funny. do we gray it out for a reason?
    // $linksRemainingMessage.removeClass('_isWorking');
    Helpers.triggerOnWindow('createLink.toggleProgress');
  } else {
    // we're getting started
    $createButton.html('<div id="capture-status">Creating your Perma Link</div>');
    $createButton.prop('disabled', true).addClass('_isWorking');
    spinner.spin($createButton[0]);
    $url.prop('disabled', true);
    $organizationDropdownButton.prop('disabled', true);
    // this looks kind of funny. do we gray it out for a reason?
    // $linksRemainingMessage.addClass('_isWorking');
    Helpers.triggerOnWindow('createLink.toggleProgress');
  }
}

function linkSucceeded (data) {
  // we should have a GUID, and the capture job should be underway
  newGUID = data.guid;

  // clear any error messages from previous failed attempts
  $errorContainer.addClass("_hide");
  $errorContainer.empty();

  // monitor capture job status
  let check_capture_status = function () {
    let request = APIModule.request("GET", `/user/capture_jobs/${newGUID}`)
    request.then(function(data) {
      switch(data.status){
        case "pending":
          break
        case "in_progress":
          if (!progress_bar){
            progress_bar = ProgressBarHelper.make_progress_bar('capture-progress-bar');
            progress_bar.appendTo($createButton);
          }
          progress_bar.setProgress(data.step_count/5*100);
          break;
        default:
          // Capture is done (one way or another)
          clearInterval(interval);
          progress_bar = null;
          if (data.status == "completed") {
            // if we succeeded, forward to the new archive
            window.location.href = "/" + newGUID;
          } else {
            // else show failure message and reset form.
            linkFailed();
          }
      }
    }).catch(function(){
      clearInterval(interval);
      progress_bar = null;
      // TODO: more error handling here
    });
  }
  check_capture_status ();
  let interval = setInterval(check_capture_status, 2000);
}

function linkFailed (jqXHR) {
  // can be called after ajax failure or as a standalone function
  let message;
  if (typeof jqXHR == 'undefined') {
    message = "Capture Failed";
  } else {
    message = APIModule.getErrorMessage(jqXHR);
  }

  // special handling of certain errors
  let offer_upload = true;
  let show_generic = true;
  if (message.indexOf("limit") > -1) {
    updateLinksRemaining(0);
    offer_upload = false;
  }
  if (message.indexOf("subscription") > -1) {
    offer_upload = false;
    show_generic = false;
  }
  if (message.indexOf("Error 0") > -1) {
    message = "Perma.cc Temporarily Unavailable";
    offer_upload = false;
  }

  // display error message
  let template = errorTemplate({
    message: message,
    offer_upload: offer_upload,
    contact_url: contact_url,
    show_generic: show_generic,
  });
  $errorContainer.html(template).removeClass("_hide");

  // reset form
  toggleInProgress();
}

//
// UPLOAD HELPERS
//

function displayUploadModal() {
  $uploadValidationError.text('');
  $uploadFormUrl.val($url.val());
  $uploadModal.modal('show');
}

function successfulUpload (data) {
  $uploadModal.modal('hide');
  window.location.href = '/' + data.guid;
}

function failedUpload (jqXHR) {
  // Display an error message in our upload modal
  // TODO: refactor this when addressing form validation accessibility

  uploadFormSpinner.stop();
  $('.js-warning').remove();
  $('.has-error').removeClass('has-error');

  // special handling if user becomes unexpectedly logged out
  if(jqXHR.status == 401){
    APIModule.showError(jqXHR);
    return;
  }

  let response;
  let reasons = [];
  try {
    response = JSON.parse(jqXHR.responseText);
  } catch (e) {
    reasons = [jqXHR.responseText];
  }
  if (response) {
    // If error message comes in as {file:"message",url:"message"},
    // show appropriate error message next to each field.
    for (let key in response) {
      if (response.hasOwnProperty(key)) {
        let input = $('#' + key);
        if (input.length) {
          input.after('<span class="help-block js-warning">' + response[key] + '</span>');
          input.closest('div').addClass('has-error');
        } else {
          reasons.push(response[key]);
        }
      }
    }
  }
  $uploadValidationError.html('<p class="field-error">Upload failed. ' + reasons.join(". ") + '</p>');
  DOMHelpers.toggleBtnDisable('#uploadPermalink', false);
  DOMHelpers.toggleBtnDisable('.cancel', false);
}

//
// HELPERS FOR RESPONDING TO OTHER USER INTERACTIONS
//

// Exported for access from JS tests
export function updateLinksRemaining (links_num) {
  links_remaining = links_num;
  DOMHelpers.changeText('.links-remaining', links_remaining);
}

function updateButtonPrivacy(){
  if (currentFolderPrivate) {
    $createButton.text("Create Private Perma Link");
    $createForm.addClass('_isPrivate');
  } else {
    $createButton.text("Create Perma Link");
    $createForm.removeClass('_isPrivate')
  }
}

// Exported for access from JS tests
export function handleSelectionChange (data) {
  let currentOrg = data.orgId;
  let currentSponsor = data.sponsorId;
  let readOnly = data.readOnly;
  let path = data.path;
  let outOfLinks = !readOnly && !currentSponsor && !currentOrg && !link_creation_allowed;

  // update top-level variables
  currentFolder = data.folderId;
  currentFolderPrivate = organizations[currentOrg] && organizations[currentOrg]['default_to_private'];

  const updateFolderSelection = new CustomEvent("vueDispatch", {
    bubbles: true,
    detail: { name: 'updateFolderSelection', data: {
      path,
      orgId: data.orgId,
      folderId: currentFolder,
      sponsorId: currentSponsor,
      isPrivate: currentFolderPrivate,
      isReadOnly: readOnly,
      isOutOfLinks: outOfLinks,
    } },
  })

  document.dispatchEvent(updateFolderSelection);

  // update the dropdown (no-op if dropdown isn't displayed)
  let formatted_links_remaining;
  if (readOnly) {
    formatted_links_remaining = '0'
  } else {
    formatted_links_remaining = (currentSponsor || (currentOrg && currentOrg !== "None")) ? null : links_remaining.toString()
  }
  let template = selectedFolderTemplate({
    "path": path.join(" > "),
    "private": currentFolderPrivate,
    "links_remaining": formatted_links_remaining
  });
  $organizationDropdownButton.html(template);

  // update the create button
  updateButtonPrivacy();
  if (outOfLinks) {
    $createButton.prop('disabled', true);
  } else {
    $createButton.prop('disabled', false);
  }

  // display personal subscription information if relevant
  if (path[0] == "Personal Links") {
    $personalLinksBanner.removeClass('hide')
  } else {
    $personalLinksBanner.addClass('hide')
  }

  // suggest switching folder if user has orgs and is running out of personal links
  let already_warned = Helpers.getCookie("suppress_link_warning");
  if (already_warned != "true" &&
      !currentOrg &&
      Object.keys(organizations).length &&
      links_remaining == 3){
    let message = "Your personal links are almost used up! Switch folders to create Perma Links for your organizations."
    Helpers.informUser(message, 'danger');
    Helpers.setCookie("suppress_link_warning", "true", 120);
  }
}

//
// PAGE LOAD HELPERS
//

// Exported for access from JS tests
export function populateFromUrl () {
  let url = Helpers.getWindowLocationSearch().split("url=")[1];
  if (url) {
    $url.val(decodeURIComponent(url));
  }
}

function populateOrgDropdown(){
  APIModule.request("GET", "/organizations/", {
    limit: 300,
    order_by:'registrar,name'
  }).then(function(data) {
    data.objects.map(org => {organizations[org.id] = org});
    if (current_user.top_level_folders[1].is_sponsored_root_folder){
      APIModule.request("GET", "/folders/" + current_user.top_level_folders[1].id + "/folders/").done(function(sponsored_data){
        let template = orgListTemplate({
          "orgs": data.objects,
          "user_folder": current_user.top_level_folders[0].id,
          "sponsored_folders": sponsored_data.objects,
          "links_remaining": links_remaining
        });
        $organizationDropdown.append(template);
      });
    } else {
      let template = orgListTemplate({
        "orgs": data.objects,
        "user_folder": current_user.top_level_folders[0].id,
        "sponsored_folders": null,
        "links_remaining": links_remaining
      });
      $organizationDropdown.append(template);
    }
  });
}

//
// EVENT HANDLERS
//

function setupEventHandlers () {

  // listen for folder selection changes
  $(window).on('FolderTreeModule.selectionChange', function(evt, data){
    if (typeof data !== 'object') {
       data = JSON.parse(data);
    }
    handleSelectionChange(data);
  });

  // listen for updated link counts after links have been moved
  $(window).on('FolderTreeModule.updateLinksRemaining', function(evt, data){
    updateLinksRemaining(data);
  });

  // listen for updated link counts after batches have been created
  $(window).on('BatchLinkModule.batchCreated', function(evt, data){
    updateLinksRemaining(data);
  });

  // announce dropdown changes
  $organizationDropdown.on('click', 'a', function(e){
    e.preventDefault();
    Helpers.triggerOnWindow("dropdown.selectionChange", {
      folderId: $(this).data('folderid'),
      orgId: $(this).data('orgid')
    });
  });

  // create a normal Perma Link
  $createForm.submit(function(e) {
    e.preventDefault();
    let formData = {
      url: $url.val(),
      human: true
    };
    if (currentFolder) {
      formData.folder = currentFolder;
    }
    toggleInProgress();
    APIModule.request("POST", "/archives/", formData, {error: linkFailed}).done(linkSucceeded);
  });

  // display the upload-modal
  // the button is only present in the DOM after errors,
  // so the event handler must be set on the document
  $(document.body).on('click', '#upload-form-button', function(e){
    e.preventDefault();
    displayUploadModal();
    Modals.returnFocusTo(this);
  });

  // create a Perma Link from an uploaded file
  $uploadForm.submit(function(e) {
    e.preventDefault();
    DOMHelpers.toggleBtnDisable('#uploadPermalink', true);
    DOMHelpers.toggleBtnDisable('.cancel', true);
    let extraUploadData = {};
    if (currentFolder) {
      extraUploadData.folder = currentFolder;
    }
    uploadFormSpinner.spin(this);
    $(this).ajaxSubmit({
      url: api_path + "/archives/",
      data: extraUploadData,
      success: successfulUpload,
      error: failedUpload
    });
  });

  // dismiss browser tools message
  $closeBrowserTools.click(function(){
    $browserToolsMessage.hide();
    Helpers.setCookie("suppress_reminder", "true", 120);
  });

}

//
// PUBLIC METHODS
//

export function init () {
  $browserToolsMessage = $('#browser-tools-message');
  $createButton = $('#addlink');
  $createForm = $('#linker');
  $closeBrowserTools = $('.close-browser-tools');
  $createErrors = $('.create-errors');
  $errorContainer = $('#error-container');
  $linksRemaining = $('.links-remaining');
  $linksRemainingMessage = $('.links-remaining-message');
  $organizationDropdown = $('#organization_select');
  $organizationDropdownButton = $('#dropdownMenu1');
  $organizationSelectForm = $('#organization_select_form');
  $personalLinksBanner = $('#personal-links-banner');
  $uploadValidationError = $('#upload-error');
  $uploadForm = $('#archive_upload_form');
  $uploadFormUrl = $('#archive_upload_form input[name="url"]');
  $uploadModal = $('#archive-upload');
  $url = $('#rawUrl');

  populateOrgDropdown();
  populateFromUrl();
  setupEventHandlers();
}
