var linkyLinks = [];
var linkyUrl = '';
$(document).ready(function() {
  $('#rawUrl').focus();
  //var params = getParams();
  
  $('#linker').submit(function() {
		linkIt();
		return false;
	});

});

function linkIt(){
  var rawUrl = $("#rawUrl").val();
  $('#linkyUrl').text(rawUrl);
  $('#myModal').modal();
  $('#saveLinky').on('click', function(event){
    event.preventDefault();
    linkyUrl = rawUrl;
    $('#myModal').modal('hide');
  });
}

$('#myModal').on('hidden', function () {
  $('#linky-list ul').append('<li>' + linkyUrl + '</li>');
});