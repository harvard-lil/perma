// stuff used in user dashboard pages
window.templates = window.templates || {};
$(function(){
    // Toggle users dropdown
    $('.manage-users-button').click(function(){
        $('.users-secondary').toggle();
    });
    // Dismiss browser tools message
    $('.close-browser-tools').click(function(){
         $('#browser-tools-message').hide();
         Helpers.setCookie("suppress_reminder", "true", 120);
    });
});
