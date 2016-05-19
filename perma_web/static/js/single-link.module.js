var SingleLinkModule = {};

$(document).ready(function(){
  SingleLinkModule.init();
  SingleLinkModule.setupEventHandlers();
});

SingleLinkModule.init = function () {
  SingleLinkModule.adjustTopMargin();
  if($('._isNewRecord')) { SingleLinkModule.handleNewRecord(); }
  SingleLinkModule.getCurrentFolder();
};

SingleLinkModule.handleNewRecord = function () {
  // On the new-record bar, update the width of the URL input to match its contents,
  // by copying the contents into a temporary span with the same class and measuring its width.

  var linkField = $('input.link-field');
  linkField.after("<span class='link-field'></span>");
  var linkSpan = $('span.link-field');
  linkSpan.text(linkField.val());
  linkField.width(linkSpan.width());
  linkSpan.remove();

}

SingleLinkModule.setupEventHandlers = function () {
  $("#details-button, .edit-link").click( function () {
    SingleLinkModule.handleShowDetails($(this));
    return false;
  });

  $("button.darchive").click( function(){
    SingleLinkModule.handleDarchiving($(this));
    return false;
  });

  $('#archive_upload_form')
    .submit(function() {
      $(this).ajaxSubmit({
        type: "PUT",
        url: api_path+"/archives/"+archive.guid,
        data: {'folder' : SingleLinkModule.currentFolder['folderId'] },
        contentType: 'multipart/form-data',
        processData: false,
        success: function(res){
          // refresh page with location=location rather than location.reload() to work around Firefox bug with iframes:
          // https://bugzilla.mozilla.org/show_bug.cgi?id=363840
          location=location;
        },
        error: function(res){console.log("error~!",res);}
      });
      return false;

    });

  $(window).on('resize', function () { SingleLinkModule.adjustTopMargin(); });
}

SingleLinkModule.getCurrentFolder = function () {
  var folders = JSON.parse(localStorage.getItem("perma_selection"));
  SingleLinkModule.currentFolder = folders[current_user.id] || {};
}

SingleLinkModule.handleShowDetails = function () {
  $this = $("#details-button");
  var showingDetails = $this.text().match("Show");
  $this.text(showingDetails && showingDetails.length > 0 ? "Hide record details" : "Show record details");
  $('header').toggleClass('_activeDetails');
}

SingleLinkModule.adjustTopMargin = function () {
  var $wrapper = $('.capture-wrapper');
  var headerHeight = $('header').height();
  $wrapper.css('margin-top', headerHeight);
}

SingleLinkModule.handleDarchiving = function (context) {
  var $this = context;
  $this.text($this.text() == "Show record details" ? "Hide record details" : "Show record details");
  $('header').toggleClass('_activeDetails');
}

SingleLinkModule.handleDarchiving = function (context) {
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

SingleLinkModule.upload_form = function () {
  $('#linky-confirm').modal('hide');
  $('#upload-error').text('');
  $('#archive_upload_form').removeAttr('action').removeAttr('method');
  $('#archive-upload').modal('show');
  return false;
}
