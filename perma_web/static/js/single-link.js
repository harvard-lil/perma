$(document).ready(function() {
    $("#details-button").click(function () {
        $(this).text($(this).text() == "Show record details" ? "Hide record details" : "Show record details");
        $('header').toggleClass('_activeDetails');
    });    

    adjustHeight();
    $('#collapse-refresh').on('shown.bs.collapse', function () {
        adjustHeight();
    });
    $('#collapse-refresh').on('hidden.bs.collapse', function () {
        adjustHeight();
    });

	function adjustHeight() {
	    var	headerHeight = $('header').height(),
	    	windowHeight = $(window).height();
	    $('iframe').height(windowHeight - headerHeight - 0);
	}

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
});