import * as SingleLinkModule from './single-link.module';
import { toggleBtnDisable } from './helpers/dom.helpers';
import { request } from './helpers/api.module';
import { sendFormData } from './helpers/general.helpers.js';
import { saveInput } from './helpers/link.helpers.js';


var updateBtnID = '#updatePermalink',
    cancelBtnID = '#cancelUpdatePermalink';

function init () {
  // Hide query parameter from the special Safari redirect
  if (window.location.href.indexOf('safari=1') > -1) {
    history.replaceState({}, "", window.location.href.replace(/\??safari=1/, ''));
  }

  toggleBtnDisable(updateBtnID, true);
  toggleBtnDisable(cancelBtnID, true);

  setupEventHandlers();
}

function setupEventHandlers () {
  $(".edit-link").click( function () {
    $(SingleLinkModule.detailsButton).click();
    return false;
  });

  $("button.darchive").click( function(){
    handleDarchiving($(this));
    return false;
  });

  $("input:file").change(function (){
    var fileName = $(this).val();
    var disableStatus = fileName ? false : true;
    toggleBtnDisable(cancelBtnID,disableStatus);
    toggleBtnDisable(updateBtnID,disableStatus);
  });

  $("button:reset").click(function(){
    toggleBtnDisable(cancelBtnID, true);
    toggleBtnDisable(updateBtnID, true);
  });

  $('#archive_upload_form')
    .submit(function(e) {
      e.preventDefault();
      submitFile();
    });
  var inputValues = {};
  $('#collapse-details')
    .find('input')
    .on('input propertychange change', function () {
      var inputarea = $(this);
      var name = inputarea.attr("name");
      if (name == "file") return;
      if (inputarea.val() == inputValues[name]) return;
      inputValues[name] = inputarea.val();
      var statusElement = inputarea.parents().find(`.${name}-save-status`);

      saveInput(archive.guid, inputarea, statusElement, name, ()=>{
        setTimeout(function() {
          $(statusElement).html('');
        }, 1000);
      });
    });
}

function submitFile () {
  toggleBtnDisable(updateBtnID,true);
  toggleBtnDisable(cancelBtnID, true);
  var url = "/archives/"+archive.guid+"/";
  var data = {};
  data['file'] = $('#archive_upload_form').find('.file')[0].files[0];

  var requestArgs = {
    contentType: false,
    processData: false
  };
  if (window.FormData) {
    sendFormData("PATCH", url, data, requestArgs)
    .done(function(data){
      location=location;
    });
  } else {
    $('#upload-error').text('Your browser version does not allow for this action. Please use a more modern browser.');
  }
}

function handleDarchiving (context) {
  var $this = context;
  if (!$this.hasClass('disabled')){
    var prev_text = $this.text(),
      currently_private = prev_text.indexOf('Public') > -1,
      private_reason = currently_private ? null : $('select[name="private_reason"]').val() || 'user';

    $this.addClass('disabled');
    $this.text('Updating ...');

    request('PATCH', '/archives/' + archive.guid + '/', {is_private: !currently_private, private_reason: private_reason}, {
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

init();
