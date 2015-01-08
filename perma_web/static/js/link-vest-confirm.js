$(function(){

    var $select_vesting_org_form = $("#select-vesting-org-form"),
        $select_folder_form = $("#select-folder-form"),
        $vesting_org_select = $select_vesting_org_form.find("select[name='vesting_org']"),
        $folder_select = $select_folder_form.find("select[name='folder']");

    var select_folder = function(vesting_org){
        $select_folder_form.find(".vesting-org-name").text(vesting_org.name);
        $select_folder_form.show();
        $.ajax(api_path + "/user/vesting_orgs/" + vesting_org.id + "/folders/", {
            success: function(data){
                $folder_select.html("").attr("disabled", false);
                data.objects.map(function(folder){
                    $folder_select.append($("<option>").val(folder.id).text(folder.name));
                });
            },
            error: function(jqXHR){
                informUser(jqXHR.status == 400 && jqXHR.responseText ? jqXHR.responseText : "Error " + jqXHR.status, 'danger');
            }
        });
    };
    
    $.ajax(api_path + "/user/vesting_orgs/", {
        success: function(data){
            if (data.objects.length > 1){
                data.objects.map(function(vesting_org){
                    $vesting_org_select.append($("<option>").val(vesting_org.id).text(vesting_org.name));
                });
                $select_vesting_org_form.show();
            } else if (data.objects.length == 1) {
                select_folder(data.objects[0]);
            } else {
                informUser("Please create a vesting organization before vesting links.");
                setTimeout(function(){ window.location = url_single_linky; }, 3000);
            }
        },
        error: function(jqXHR){
            informUser(jqXHR.status == 400 && jqXHR.responseText ? jqXHR.responseText : "Error " + jqXHR.status, 'danger');
        }
    });

    $select_vesting_org_form.find("button").click(function(){
        $select_vesting_org_form.hide();
        select_folder({id: $vesting_org_select.val(), name: $vesting_org_select.find(":selected").text()});
        return false;
    });
    
    $select_folder_form.find("button").click(function(){
        var $this = $(this),
            prev_text = $this.text(),
            folder_id = $("select[name='folder']").val();

        if (!$this.hasClass("disabled")){

            $this.addClass("disabled");
            $this.text("Vesting...");
            
            $.ajax(api_path + "/folders/" + folder_id + "/archives/" + archive.guid + "/", {
                method: "PUT",
                data: JSON.stringify({vested: true}),
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
