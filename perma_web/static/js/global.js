// Initializations
$(document).ready(function() {
    // Add class to active text inputs
    $('.text-input').focus(function() { $(this).addClass('text-input-active'); });
    $('.text-input').blur(function() { $(this).removeClass('text-input-active'); });

    // Select the input text when the user clicks the element
    $('.select-on-click').click(function() { $(this).select(); });
    
    $("input#submit-feedback").click(function(){
      var data = $('form.feedback').serializeArray();
      var csrftoken = getCookie('csrftoken');
      data.push({name: 'csrfmiddlewaretoken', value: csrftoken});
      data.push({name: 'visited_page', value: $(location).attr('href')});
        $.ajax({
            type: "POST",
            url: feedback_url, //process to mail
            data: data,
            success: function(msg){
                $("#feedback-form").modal('hide'); //hide popup 
            },
            error: function(){
                alert("failure");
            }
        });
      return false;
    });
});

// Clear fields on focus
$(".clear-on-focus")
  .focus(function() { if (this.value === this.defaultValue) { this.value = ''; } })
  .blur(function() { if (this.value === '') { this.value = this.defaultValue; }
});

function getCookie(name) {
    var cookieValue = null;
    if (document.cookie && document.cookie != '') {
        var cookies = document.cookie.split(';');
        for (var i = 0; i < cookies.length; i++) {
            var cookie = jQuery.trim(cookies[i]);
            // Does this cookie string begin with the name we want?
            if (cookie.substring(0, name.length + 1) == (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}