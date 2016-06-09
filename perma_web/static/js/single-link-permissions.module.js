var SingleLinkPermissionsModule = {},
  saveBufferSeconds = 0.5,
  updateBtnID = '#updateLinky',
  cancelBtnID = '#cancelUpdateLinky',
  timeouts = {};

$(document).ready(function(){
  SingleLinkPermissionsModule.init();
  SingleLinkPermissionsModule.setupEventHandlers();
});

SingleLinkPermissionsModule.init = function () {
  DOMHelpers.toggleBtnDisable(updateBtnID, true);
  DOMHelpers.toggleBtnDisable(cancelBtnID, true);

  if($('._isNewRecord')) { SingleLinkPermissionsModule.handleNewRecord(); }
};

SingleLinkPermissionsModule.handleNewRecord = function () {
  // On the new-record bar, update the width of the URL input to match its contents,
  // by copying the contents into a temporary span with the same class and measuring its width.

  var linkField = $('input.link-field');
  linkField.after("<span class='link-field'></span>");
  var linkSpan = $('span.link-field');
  linkSpan.text(linkField.val());
  linkField.width(linkSpan.width());
  linkSpan.remove();
}

SingleLinkPermissionsModule.setupEventHandlers = function () {
  $(".edit-link").click( function () {
    SingleLinkModule.handleShowDetails();
    return false;
  });

  $("button.darchive").click( function(){
    SingleLinkPermissionsModule.handleDarchiving($(this));
    return false;
  });

  $("input:file").change(function (){
    var fileName = $(this).val();
    var disableStatus = fileName ? false : true;
    DOMHelpers.toggleBtnDisable(cancelBtnID,disableStatus);
    DOMHelpers.toggleBtnDisable(updateBtnID,disableStatus);
  });

  $("button:reset").click(function(){
    DOMHelpers.toggleBtnDisable(cancelBtnID, true);
    DOMHelpers.toggleBtnDisable(updateBtnID, true);
  });

  $('#archive_upload_form')
    .submit(function(e) {
      e.preventDefault();
      SingleLinkPermissionsModule.submitFile();
    });
  var inputValues = {};
  $('#collapse-details')
    .find('input')
    .on('input textchange change', function () {
      var inputarea = $(this);
      var name = inputarea.attr("name");
      if (name == "file") return
      if (inputarea.val() == inputValues[name]) return
      inputValues[name] = inputarea.val();
      var statusElement = inputarea.parent().find(".save-status");

      SingleLinkPermissionsModule.saveInput(inputarea, name, statusElement);
    });

  $(window).on('resize', function () { SingleLinkPermissionsModule.adjustTopMargin(); });
}

SingleLinkPermissionsModule.submitFile = function () {
  DOMHelpers.toggleBtnDisable(updateBtnID,true);
  DOMHelpers.toggleBtnDisable(cancelBtnID, true);
  var url = "/archives/"+archive.guid+"/";
  var data = {};
  data['file'] = $('#archive_upload_form').find('.file')[0].files[0];

  var requestArgs = {
    contentType: false,
    processData: false
  };
  if (window.FormData) {
    Helpers.sendFormData("PATCH", url, data, requestArgs)
    .done(function(data){
      location=location;
    });
  } else {
    $('#upload-error').text('Your browser version does not allow for this action. Please use a more modern browser.');
  }
}

SingleLinkPermissionsModule.handleDarchiving = function (context) {
  var $this = context;
  if (!$this.hasClass('disabled')){
    var prev_text = $this.text(),
      currently_private = prev_text.indexOf('Public') > -1,
      private_reason = currently_private ? null : $('select[name="private_reason"]').val() || 'user';

    $this.addClass('disabled');
    $this.text('Updating ...');

    Helpers.apiRequest('PATCH', '/archives/' + archive.guid + '/', {is_private: !currently_private, private_reason: private_reason}, {
      success: function(){
        window.location.reload(true);
      },
      error: function(jqXHR){
        $this.removeClass('disabled');
        $this.text(prev_text);
      }
    });
  }
}

SingleLinkPermissionsModule.saveInput = function (inputElement, name, statusElement) {
  $(statusElement).html('Saving...');
  var data = {};
  data[name] = inputElement.val();
  if(timeouts[name])
    clearTimeout(timeouts[name]);

  timeouts[name] = setTimeout(function () {
    Helpers.apiRequest("PATCH", '/archives/' + archive.guid + '/', data)
      .done(function(data){
        $(statusElement).html('Saved!');
        setTimeout(function() {
          $(statusElement).html('');
        }, 1000)
      });
  }, 500)
}
