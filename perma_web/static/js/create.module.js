/* Our globals. Look out interwebs - start */

// Where we store our successfully created new archive data
var new_archive = {};

// Where we queue up our archive guids for polling
var refreshIntervalIds = [];
var spinner;
var organizations = {};

/* Our globals. Look out interwebs - end */
var CreateModule = CreateModule || {};
var ls = ls || {};

/* Everything that needs to happen at page load - start */

$(document).ready(function() {
  CreateModule.init();
  CreateModule.setupEventHandlers();
  CreateModule.populateWithUrl();
  $('#archive-upload-confirm').modal({show: false});
  $('#archive-upload').modal({show: false});
});


ls.getAll = function () {
  var folders = JSON.parse(localStorage.getItem("perma_selection"));
  return folders || {};
}

ls.getCurrent = function () {
  var folders = this.getAll();
  return folders[current_user.id] || {};
}

ls.setCurrent = function (orgId, folderId) {
  folderId = folderId ? folderId : 'default';

  var selectedFolders = this.getAll();
  selectedFolders[current_user.id] = {'folderId' : folderId, 'orgId' : orgId };

  localStorage.setItem("perma_selection",JSON.stringify(selectedFolders));
  CreateModule.updateLinker();

  $(window).trigger("dropdown.selectionChange");
}


// localStorage settings
CreateModule.ls = ls


// Get parameter by name
// from https://stackoverflow.com/questions/901115/how-can-i-get-query-string-values-in-javascript
CreateModule.getParameterByName = function (name) {
  name = name.replace(/[\[]/, "\\[").replace(/[\]]/, "\\]");
  var regex = new RegExp("[\\?&]" + name + "=([^&#]*)"),
    results = regex.exec(location.search);
  return results == null ? "" : decodeURIComponent(results[1].replace(/\+/g, " "));
}

CreateModule.linkIt = function (data) {
  // Success message from API. We should have a GUID now (but the
  // archive is still be generated)
  // Clear any error messages out
  $('.error-row').remove();

  new_archive.guid = data.guid;

  refreshIntervalIds.push(setInterval(CreateModule.check_status, 2000));
}

CreateModule.linkNot = function (jqXHR) {
  // The API told us something went wrong.

  if (jqXHR.status == 401) {
  // special handling if user becomes unexpectedly logged out
    showAPIError(jqXHR);
  } else {
    var message = "";
    if (jqXHR.status == 400 && jqXHR.responseText) {
      var errors = JSON.parse(jqXHR.responseText).archives;
      for (var prop in errors) {
          message += errors[prop] + " ";
      }
    }

    var upload_allowed = true;
    if (message.indexOf("limit") > -1) {
      $('.links-remaining').text('0');
      upload_allowed = false;
    }

    $('#error-container').html(templates.error({
      message: message || "Error " + jqXHR.status,
      upload_allowed: upload_allowed,
      contact_url: contact_url
    }));

    $('.create-errors').addClass('_active');
    $('#error-container').hide().fadeIn(0);
  }
  CreateModule.toggleCreateAvailable();
}



/* Handle an upload - start */

CreateModule.uploadNot = function (jqXHR) {
  // Display an error message in our upload modal

  // special handling if user becomes unexpectedly logged out
  if(jqXHR.status == 401){
    showAPIError(jqXHR);
    return;
  }
  var reasons = [],
    response;

  try {
    response = jQuery.parseJSON(jqXHR.responseText);
  } catch (e) {
    response = jqXHR.responseText;
  }

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
}

CreateModule.uploadIt = function (data) {
  // If a user wants to upload their own screen capture, we display
  // a modal and the form in that modal is handled here
  $('#archive-upload').modal('hide');

  var upload_image_url = settings.STATIC_URL + '/img/upload-preview.jpg';
  window.location.href = '/' + data.guid;
}

CreateModule.upload_form = function () {
  $('#linky-confirm').modal('hide');
  $('#upload-error').text('');
  $('#archive_upload_form input[name="url"]').val($('#rawUrl').val());
  $('#archive-upload').modal('show');
  return false;
}

/* Handle the the main action (enter url, hit the button) button - start */

CreateModule.toggleCreateAvailable = function() {
  // Get our spinner going and display a "we're working" message
  $addlink = $('#addlink');
  if ($addlink.hasClass('_isWorking')) {
    $addlink.html('Create Perma Link').removeAttr('disabled').removeClass('_isWorking');
    spinner.stop();
    $('#rawUrl, #organization_select_form button').removeAttr('disabled');
    $('#links-remaining-message').removeClass('_isWorking');
  } else {
    $addlink.html('<div id="capture-status">Creating your Perma Link</div>').attr('disabled', 'disabled').addClass('_isWorking');
    spinner = new Spinner(opts);
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

CreateModule.check_status = function () {

  // Check our status service to see if we have archiving jobs pending
  var request = apiRequest("GET", "/archives/" + new_archive.guid + "/", {'cache': false});
  var self = this;
  request.done(function(data) {
    var capturesPending = false,
      capturesSucceeded = false;
    $.each(data.captures, function(i, capture){
      if(capture.role != 'favicon') {
        if (capture.status == 'pending') capturesPending = true;
        if (capture.status == 'success') capturesSucceeded = true;
      }
    });

    // We're done checking status when nothing is pending.
    if (!capturesPending) {
      // Clear out our pending jobs
      $.each(refreshIntervalIds, function(ndx, id) {
        clearInterval(id);
      });

      // If we have at least one success, forward to the new archive
      if (capturesSucceeded) {
        window.location.href = "/" + new_archive.guid;

      // Else show failure message/upload form.
      } else {

        $('#error-container').html(templates.error({
          message: "Error: URL capture failed."
        }));

        $('#error-container').removeClass('_hide _error _success _wait').addClass('_error');

        // Toggle our create button
        CreateModule.toggleCreateAvailable();
      }
    }
  });
}

/* Our polling function for the thumbnail completion - end */
CreateModule.populateWithUrl = function () {
  var url = location.search.split("url=")[1];
  if (url) {
    url = decodeURIComponent(url);
    $("#rawUrl").val(url);
  }
}

CreateModule.updateLinker = function () {
  var userSettings = this.ls.getCurrent();
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
    $('#linker').addClass('_isPrivate')
    // add the little eye icon if org is private
    $('#organization_select_form')
        .find('.dropdown-toggle > span')
        .addClass('ui-private');
  } else {
    $('#linker').removeClass('_isPrivate')
  }
}

CreateModule.updateAffiliationPath = function (currentOrg, path) {
  if (!path) { return; }

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

CreateModule.updateLinksRemaining = function (links_num) {
  links_remaining = links_num;
  $('.links-remaining').text(links_remaining);
}

CreateModule.handleSelectionChange = function (data) {
  var orgId = path = null;

  if (data && (data.orgId || data.path)) {
    orgId = data.orgId;
    path  = data.path;
  }
  this.updateLinker();
  this.updateAffiliationPath(orgId, path);
}


CreateModule.setupEventHandlers = function () {
  var self = this;
  $(window)
    .off('FolderTreeModule.selectionChange')
    .off('FolderTreeModule.updateLinksRemaining')
    .on('FolderTreeModule.selectionChange', function(evt, data){
      if (typeof data !== 'object') data = JSON.parse(data);
      self.handleSelectionChange(data);
    })
    .on('FolderTreeModule.updateLinksRemaining', function(evt, data){
      self.updateLinksRemaining(data)
    });
    // When a user uploads their own capture

  $('#archive_upload_form')
    .submit(function() {

      var extraUploadData = {},
        selectedFolder = CreateModule.ls.getCurrent().folderId;
      if(selectedFolder)
        extraUploadData.folder = selectedFolder;
      $(this).ajaxSubmit({
        data: extraUploadData,
        success: CreateModule.uploadIt,
        error: CreateModule.uploadNot
      });
      return false;

    });

  // Toggle users dropdown
  $('#dashboard-users')
    .click(function(){ $('.users-secondary').toggle(); });
    // When a new url is entered into our form
  $('#linker').submit(function() {
    var $this = $(this);
    var linker_data = {};
    var selectedFolder = CreateModule.ls.getCurrent().folderId;

    if(selectedFolder){
      linker_data = {
        url: $this.find("input[name=url]").val(),
        folder: selectedFolder || null
      }
    } else {
      linker_data = {
        url: $this.find("input[name=url]").val()
      };
    }
    // Start our spinner and disable our input field with just a tiny delay
    window.setTimeout(CreateModule.toggleCreateAvailable, 150);

    $.ajax($this.attr('action'), {
      method: $this.attr('method'),
      contentType: 'application/json',
      data: JSON.stringify(linker_data),
      success: CreateModule.linkIt,
      error: CreateModule.linkNot
    });

    return false;
  });
}


CreateModule.init = function () {
  var self = this;

  apiRequest("GET", "/user/organizations/", {limit: 300, order_by:'registrar'})
    .success(function(data) {
      var $organization_select = $("#organization_select");

      var sorted = [];
      Object.keys(data.objects).sort(function(a,b){
        return data.objects[a].registrar < data.objects[b].registrar ? -1 : 1;
      }).forEach(function(key){
        sorted.push(data.objects[key]);
      });
      data.objects = sorted;

      if (data.objects.length > 0) {
        var optgroup = data.objects[0].registrar;
        data.objects.map(function (organization) {
          organizations[organization.id] = organization;

          if(organization.registrar !== optgroup) {
            $organization_select.prepend("<li class='dropdown-header'>" + optgroup + "</li>");
            optgroup = organization.registrar;
            $organization_select.append("<li class='dropdown-header'>" + optgroup + "</li>");
          }
          var opt_text = organization.name;
          if (organization.default_to_private) {
            opt_text += ' <span class="ui-private">(Private)</span>';
          }
          $organization_select.append("<li><a onClick='CreateModule.ls.setCurrent("+organization.id+", "+organization.shared_folder.id+")'>" + opt_text + "</a></li>");
        });

        $organization_select.append("<li><a onClick='CreateModule.ls.setCurrent()'> My Links <span class='links-remaining'>" + links_remaining + "<span></a></li>");
        self.updateLinker();
      } else {
        // select My Folder for users with no orgs and no saved selections
        var selectedFolder = self.ls.getCurrent().folderId;
        if (!selectedFolder) { self.ls.setCurrent(); }
      }
  });
}


/* Our spinner controller - start */

var opts = {
  lines: 15, // The number of lines to draw
  length: 2, // The length of each line
  width: 2, // The line thickness
  radius: 9, // The radius of the inner circle
  scale: 1, // Scales overall size of the spinner
  corners: 0, // Corner roundness (0..1)
  color: '#2D76EE', // #rgb or #rrggbb or array of colors
  opacity: 0.25, // Opacity of the lines
  rotate: 0, // The rotation offset
  direction: 1, // 1: clockwise, -1: counterclockwise
  speed: 1, // Rounds per second
  trail: 50, // Afterglow percentage
  fps: 20, // Frames per second when using setTimeout() as a fallback for CSS
  zIndex: 2e9, // The z-index (defaults to 2000000000)
  className: 'spinner', // The CSS class to assign to the spinner
  top: '12px', // Top position relative to parent
  left: '50%', // Left position relative to parent
  shadow: false, // Whether to render a shadow
  hwaccel: false, // Whether to use hardware acceleration
  position: 'absolute' // Element positioning
};

/* Our spinner controller - end */
