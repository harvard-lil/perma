$(function(){
    $("button.btn-success").click(function(){
        var $this = $(this),
            prev_text = $this.text();

        if (!$this.hasClass("disabled")){

            $this.addClass("disabled");
            $this.text("Dark archiving link...");
            
            $.ajax(api_path + "/archives/" + archive.guid + "/", {
                method: "PATCH",
                data: JSON.stringify({dark_archived: true}),
                contentType: 'application/json',
                success: function(){
                    window.location = url_single_linky;
                },
                error: function(jqXHR){
                    $this.removeClass("disabled");
                    $this.text(prev_text);
                    informUser(jqXHR.status == 400 && jqXHR.responseText ? jqXHR.responseText : "Error " + jqXHR.status, 'danger');
                }
            });
        }

        return false;
    });
});
