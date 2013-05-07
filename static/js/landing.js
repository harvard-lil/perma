var linkyUrl = '';
$(document).ready(function() {
  $('#linky-confirm').modal({show: false});
  $('#rawUrl').focus();
  
  $('#linker').submit(function() {
		linkIt();
		return false;
	});

});

function linkIt(){
  var rawUrl = $("#rawUrl").val();
  
  // This is a fill in.  We will get the real linky from the api and fill it in instead.
  $('#linkyUrl').text(rawUrl);
  
  $('#linky-confirm').modal('show');
  $('#saveLinky').on('click', function(event){
    event.preventDefault();
    $.post('http://localhost:5000/api/linky/', { url: rawUrl}, function(data) {
      linkyUrl = static_url + '/linkys/' + data.linky_url + '.jpg';
    });
    linkyUrl = rawUrl;
    $('#linky-confirm').modal('hide');
  });
}

$('#linky-confirm').on('hidden', function () {
  $('#rawUrl').val('').focus();
  $('#linky-list ul').append('<li>' + linkyUrl + '</li>');
});