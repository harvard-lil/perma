// stuff used in user dashboard pages
window.templates = window.templates || {};
$(function(){
    // Toggle users dropdown
    $('.manage-users-button').click(function(){
        $('.users-secondary').toggle();
    });
});
