// stuff used in user dashboard pages
window.templates = window.templates || {};
$(function(){
    // compile handlebars templates
    $("script[type='text/x-handlebars-template']").each(function(){
        var $this = $(this),
            name = $this.attr('id').replace('-template', '').replace(/-/g, '_');
        templates[name] = Handlebars.compile($this.html());
    });

    // Toggle users dropdown
    $('.manage-users-button').click(function(){
        $('.users-secondary').toggle();
    });
});