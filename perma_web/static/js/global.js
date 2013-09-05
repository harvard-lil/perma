// Initializations
$(document).ready(function() {
    // Add class to active text inputs
    $('.text-input').focus(function() { $(this).addClass('text-input-active'); });
    $('.text-input').blur(function() { $(this).removeClass('text-input-active'); });

    // Select the input text when the user clicks the element
    $('.select-on-click').click(function() { $(this).select(); });
});

// Clear fields on focus
$(".clear-on-focus")
  .focus(function() { if (this.value === this.defaultValue) { this.value = ''; } })
  .blur(function() { if (this.value === '') { this.value = this.defaultValue; }
});
