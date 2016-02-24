$(document).ready(function() {
    $("#details-button").click(function () {
        $(this).text($(this).text() == "Show record details" ? "Hide record details" : "Show record details");
        $('header').toggleClass('_activeDetails');
    });

    function adjustTopMargin() {
      var $wrapper = $('.capture-wrapper');
      var $screenshoterror = $('.screenshot-error');
      var headerHeight = $('header').height();
      $wrapper.css('margin-top', headerHeight);
      $screenshoterror.css('margin-top', headerHeight + 30)
    }

    adjustTopMargin();

    $(window).on('resize', function () {
        adjustTopMargin();
    });

    $("button.darchive").click(function(){
        var $this = $(this);

        if (!$this.hasClass("disabled")){
            var prev_text = $this.text(),
                currently_private = prev_text.indexOf("Public") > -1,
                private_reason = currently_private ? null : $('select[name="private_reason"]').val() || 'user';

            $this.addClass("disabled");
            $this.text("Updating ...");

            apiRequest("PATCH", "/archives/" + archive.guid + "/", {is_private: !currently_private, private_reason: private_reason}, {
                success: function(){
                    window.location.reload(true);
                },
                error: function(jqXHR){
                    $this.removeClass("disabled");
                    $this.text(prev_text);
                    showAPIError(jqXHR);
                }
            });
        }

        return false;
    });

    // On the new-record bar, update the width of the URL input to match its contents,
    // by copying the contents into a temporary span with the same class and measuring its width.
    if($('._isNewRecord')){
        var linkField = $('input.link-field');
        linkField.after("<span class='link-field'></span>");
        var linkSpan = $('span.link-field');
        linkSpan.text(linkField.val());
        linkField.width(linkSpan.width());
        linkSpan.remove();
    }
});