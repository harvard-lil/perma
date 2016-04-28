var GlobalsModule = {};

// Initializations
$(document).ready(function() {
  // initialize fastclick
  FastClick.attach(document.body);
  GlobalsModule.init();
  GlobalsModule.setupEventHandlers();
});


GlobalsModule.init = function () {
  // set margins for modal windows
  // currently set to hit only special elements
  var windowHeight = $(window).height();
  var windowWidth = $(window).width();
  $('.modal-new').each(function() {
    var thisHeight = $(this).actual('height');
    var opticalOffset = (windowHeight - thisHeight) / 12;
    var marginTop = 0 - opticalOffset - (thisHeight / 2);
    if(windowWidth < 767) {}
    else if( opticalOffset > 0) {
      $(this).css('margin-top', marginTop);
    } else {
      $(this).addClass('_overflow');
    }
  });

  $.ajaxSetup({
    crossdomain: false, // obviates need for sameOrigin test
    beforeSend: function(xhr, settings) {
      if (!Helpers.csrfSafeMethod(settings.type)) {
        xhr.setRequestHeader('X-CSRFToken', Helpers.getCookie('csrftoken'));
      }
    }
  });

}

GlobalsModule.setupEventHandlers = function () {
  // Add class to active text inputs
  $('.text-input')
    .focus(function() { $(this).addClass('text-input-active'); })
    .blur(function() { $(this).removeClass('text-input-active'); });

  // Clear fields on focus
  $('.clear-on-focus')
    .focus(function() { if (this.value === this.defaultValue) { this.value = ''; } })
    .blur(function() { if (this.value === '') { this.value = this.defaultValue; } });

  // Select the input text when the user clicks the element
  $('.select-on-click').click(function() { $(this).select(); });

  // clear popup alerts with a click
  $(document).on('click', '.popup-alert', function(){ $(this).remove(); });

}
