$(function(){

    var $select_vesting_org_form = $("#select-vesting-org-form"),
        $select_folder_form = $("#select-folder-form"),
        $vesting_org_select = $select_vesting_org_form.find("select[name='vesting_org']"),
        $folder_select = $select_folder_form.find("select[name='folder']");

    var select_folder = function(vesting_org){
        $select_folder_form.find(".vesting-org-name").text(vesting_org.name);
        $select_folder_form.show();
        apiRequest("GET", "/user/vesting_orgs/" + vesting_org.id + "/folders/")
            .success(function(data){

                // build folder lookup
                var foldersByID = {};
                data.objects.map(function(folder) {
                    foldersByID[folder.id] = folder;
                    folder.children = [];
                });

                // group folders into tree
                var rootFolders = [];
                data.objects.map(function(folder) {
                    if (folder.parent && foldersByID[folder.parent]) {
                        foldersByID[folder.parent].children.push(folder);
                    }else{
                        rootFolders.push(folder);
                    }
                });

                // write tree
                function writeTree(folder, depth){
                    $folder_select.append(
                        $("<option>").val(folder.id).text(folder.name).prepend(new Array(depth*3+1).join('&nbsp;')+'- ')
                    );
                    folder.children.map(function(folder){
                        writeTree(folder, depth+1);
                    });
                }
                $folder_select.html("").attr("disabled", false);
                rootFolders.map(function(folder){
                    writeTree(folder, 0);
                });
            });
    };
    
    apiRequest("GET", "/user/vesting_orgs/", {limit: 300, order_by:'registrar'})
        .success(function(data) {
            var sorted = [];
            Object.keys(data.objects).sort(function(a,b){
                return data.objects[a].registrar < data.objects[b].registrar ? -1 : 1
            }).forEach(function(key){
                sorted.push(data.objects[key]);
            });
            data.objects = sorted;
            var optgroup = data.objects[0].registrar;
            $vesting_org_select.append($("<optgroup>").attr('label', optgroup));
            if (data.objects.length > 1) {
                data.objects.map(function (vesting_org) {
                    if(vesting_org.registrar !== optgroup) {
                        optgroup = vesting_org.registrar;
                        $vesting_org_select.append($("<optgroup>").attr('label', optgroup));
                    }
                    $vesting_org_select.append($("<option>").val(vesting_org.id).text(vesting_org.name));
                });
                $select_vesting_org_form.show();
                $("#vesting_org_select").val(selected_vesting_org);
            } else if (data.objects.length == 1) {
                select_folder(data.objects[0]);
            } else {
                informUser("Please create a vesting organization before vesting links.");
                /*setTimeout(function () {
                    window.location = url_single_linky;
                }, 3000);*/
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
            
            apiRequest("PUT", "/folders/" + folder_id + "/archives/" + archive.guid + "/", {vested: true}, {
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
