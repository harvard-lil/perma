$(function(){
    var table = $('.vested-table');

    // helpers
    function postJSON(url, data, callback){
        return $.post(url, JSON.stringify(data), callback, 'json');
    }

    // new folder form
    $('#new_folder_show, #new_folder_cancel').on('click', function(){
        $('#new_folder_container, #new_folder_name_container').toggle("fast");
    });
    $('#new_folder_name').on('keyup', function(){
        if(this.value)
            $("#new_folder_submit").removeAttr("disabled");
        else
            $("#new_folder_submit").attr("disabled", true);
    });

    function initializeFolders(){
    // only need to do stuff if there are folders

        // folder hover tools
        $('.vested-table tr').on('mouseenter', function () {
            if(!$(this).find('.rename-folder-form').length){
                //$(this).find('.tool-block').show();
            }
            }).on('mouseleave', function () {
                //$(this).find('.tool-block').hide();
        });

        $('.tab-pane').on('click', '.folder-row input[name="delete"]', function(){
            // folder delete
            var td = $(this).parent().parent(),
            aTag = td.find('a');
            if(confirm("Really delete folder?")){
                postJSON(
                    aTag.attr('href'), // subfolder url
                    {action:'delete_folder'},
                    function(data){
                        if(data.success){
                            td.remove();
                        }else{
                            alert(data.error);
                        }
                    }
                );
            }

        }).on('click', '.folder-row input[name="rename"]', function(){
            // folder rename - show form
            $(this).closest('.tool-block').hide();
            var aTag = $(this).parent().parent().find('a');
            aTag.hide().after($('#form_templates .rename-folder-form').clone().hide()).next().show();
            $(this).parent().parent().find('input[name="folder_name"]').val(aTag.text());

        }).on('click', '.folder-row input[name="rename_folder_cancel"]', function(){
            // folder rename - cancel
            var td = $(this).parent().parent(),
            aTag = td.find('a');
            aTag.show();
            aTag.parent().parent().find('.rename-folder-form').remove();
            $('.tool-block').prop('style')['display']=''; // let :hover css rule work again

        }).on('click', '.folder-row input[name="rename_folder_save"]', function(){
            // folder rename - submit
            var td = $(this).parent().parent(),
                aTag = td.find('a'),
                newName = td.find('input[name=folder_name]').val();
            if(!newName)
                return;
            postJSON(
                aTag.attr('href'), // subfolder url
                {action:'rename_folder',name:newName},
                function(data){
                    aTag.text(newName).show();
                    td.find('.rename-folder-form').remove();
                }
            );

        });


        // move items button
        function handleCheckboxClick(){
            $('#new_folder_container .dropdown-toggle').prop('disabled', $('.tab-pane').find('input.checkbox:checked').length==0);
        }
        $('.tab-pane').on('click', 'input.checkbox', handleCheckboxClick);
        handleCheckboxClick();

        // draggable
        table.find('tbody tr').draggable({
            helper: function() {
                return $("<div></div>").append($(this).find('.linky-abbr-title').clone());
            },
            cursor: "move",
            start: function(event, ui ){
                ui.helper.find('.tool-block').hide();
            },
            handle: ''
        });
        
        $('.folder-row').droppable({
            hoverClass: "ui-selected",
            tolerance: "pointer",
            drop: function(event, ui) {
                var links = [],
                    folders = []; // use an array so we can handle multiselect at some point
                if(ui.draggable.hasClass('folder-row')){
                    folders.push(ui.draggable.attr('folder_id'));
                }else{
                    links.push(ui.draggable.attr('link_id'));
                }
                $.ajax({
                    type: "POST",
                    url: '#',
                    data: {move_selected_items_to:$(this).attr('folder_id'),links:links,folders:folders},
                    success: function(data){
                        ui.draggable.remove();
                    },
                    traditional: true // Django-style array serialization
                });
            }
        });
    }

    if($('.folder-row').length){
        initializeFolders();
    }

});