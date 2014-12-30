$(function(){
    $("button.delete-confirm").click(function(){
        var $this = $(this),
            prev_text = $this.text();

        if (!$this.hasClass("disabled")){

            $this.addClass("disabled");
            $this.text("Deleting link...");
            
            $.ajax(api_path + "/archives/" + archive.guid + "/", {
                method: "DELETE",
                success: function(){
                    window.location = url_link_browser;
                },
                failure: function(){
                    $this.removeClass("disabled");
                    $this.text(prev_text);
                    alert("There was an error");
                }
            });
        }

        return false;
    });
});
