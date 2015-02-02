$(function(){
    $("button.btn-success").click(function(){
        var $this = $(this),
            prev_text = $this.text();

        if (!$this.hasClass("disabled")){

            $this.addClass("disabled");
            $this.text("Dark archiving link...");
            
            apiRequest("PATCH", "/archives/" + archive.guid + "/", {dark_archived: true}, {
                success: function(){
                    window.location = url_single_linky;
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
