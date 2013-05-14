var linkyUrl = '';
var rawUrl = '';
$(document).ready(function() {
  $('#linky-confirm').modal({show: false});
  $('#rawUrl').focus();
  
  $('#linker').submit(function() {
		linkIt();
		return false;
	});
	
	$('#email_request').keyup(function() {                   
    if( !$(this).val() ) {
      $('#saveLinky').text('Save this Linky');    
    }
    else {
      $('#saveLinky').text('Save and send this Linky');
    }
  });

});

function linkIt(){
  $('#linkyUrl').toggleClass('text-center');
  $('#linky-preview img').attr('src', 'http://placekitten.com/500/400');
  $('#linkyUrl a').attr('href', '').html('<i class="icon-spinner icon-spin icon-2x text-center"></i>');
  rawUrl = $("#rawUrl").val();
  var request = $.ajax({
    url: web_base + "/api/linky/",
    type: "POST",
    data: {url: rawUrl},
    dataType: "json"
  });
  request.done(function(data) {
    linkyUrl = web_base  + '/' + data.linky_id;
    $('#linkyUrl').toggleClass('text-center');
    $('#linkyUrl a').html(web_base  + '/' + data.linky_id).attr('href', web_base + '/' + data.linky_id);
    $('#linky-preview img').attr('src', data.linky_url);
  });
  request.fail(function(jqXHR, responseText) {
    //console.log( jqXHR );
  });
  
  $('#linky-confirm').modal('show');
  $('#saveLinky').on('click', function(event){
            
    var request = $.ajax({
      url: web_base + "/service/email-confirm/",
      type: "POST",
      data: {email_address: $('#email_request').val(), linky_link: $('#linkyUrl a').attr('href')},
      dataType: "json"
    });
      
    event.preventDefault();
    $('#linky-confirm').modal('hide');
  });
}

$('#linky-confirm').on('hidden', function () {
  $('#rawUrl').val('').focus();
  $('#linky-list').fadeIn();
  $('#linky-list tbody').append('<tr><td><a href="' + linkyUrl + '" target="_blank">' + linkyUrl + '</a></td><td><a href="' + rawUrl + '" target="_blank">' + rawUrl + '</a></td></tr>');
});