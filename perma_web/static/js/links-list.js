$(function() {
    var linkTable = $('.link-rows');

    function getLinkIDForFormElement(element){
        return element.closest('.link-container').find('.link-row').attr('link_id');
    }

    function showError(jqXHR){
        var message;

        if(jqXHR.status == 400 && jqXHR.responseText){
            try{
                var parsedResponse = JSON.parse(jqXHR.responseText);
                while(typeof parsedResponse == 'object'){
                    for(var key in parsedResponse){
                        if (parsedResponse.hasOwnProperty(key)){
                            parsedResponse = parsedResponse[key];
                            break;
                        }
                    }
                }
                message = parsedResponse;
            }catch(SyntaxError){}
        }

        if(!message){
            message = "Error " + jqXHR.status;
        }

        informUser(message, 'danger');
    }

    // save changes to a given text box to the server
    var saveNeeded = false,
        lastSaveTime = 0,
        saveBufferSeconds = 3;
    function saveInput(inputElement, statusElement, name, callback) {
        if(inputElement.val()==inputElement.attr('last_value_saved'))
            return;

        statusElement.html('saving ...');
        saveNeeded = true;

        var guid = inputElement.attr('id').match(/.+-(.+-.+)/)[1],
            data = {};

        data[name] = inputElement.val();

        // use a setTimeout so notes are only saved once every few seconds
        setTimeout(function () {
            if (saveNeeded) {
                saveNeeded = false;
                lastSaveTime = new Date().getTime();
                var saveValue = inputElement.val();

                var request = apiRequest("PATCH", '/archives/' + guid + '/', data);

                request.done(function(data){
                    if(!saveNeeded)
                        statusElement.html('saved.');
                        inputElement.attr('last_value_saved', saveValue);
                });

                if (callback) request.done(callback);
            }
        }, Math.max(saveBufferSeconds * 1000 - (new Date().getTime() - lastSaveTime), 0));
    }

    // hide and show link details
    linkTable.on('mousedown', '.link-expand', function () {
        // handle details link to hide/show link details
        var button = $(this),
            details = button.closest('.link-container').find('.link-details');
        if(details.is(":visible")){
            details.hide();
            button.text('More');
        }else{
            // when showing link details, update the move-to-folder select input
            // based on the current folderTree structure

            // first clear the select ...
            var currentFolderID = getSelectedFolderID(),
                moveSelect = details.find('.move-to-folder');
            moveSelect.find('option').remove();


            // recursively populate select ...
            function addChildren(node, depth){
                for(var i=0;i<node.children.length;i++){
                    var childNode = folderTree.get_node(node.children[i]);

                    // For each node, we create an <option> using text() for the folder name,
                    // and then prepend some &nbsp; to show the tree structure using html().
                    // Using html for the whole thing would be an XSS risk.
                    moveSelect.append(
                        $("<option/>", {
                            value: childNode.data.folder_id,
                            text: childNode.text.trim(),
                            selected: childNode.data.folder_id == currentFolderID
                        }).prepend(
                            new Array(depth).join('&nbsp;&nbsp;')+'- '
                        )
                    );

                    // recurse
                    if(childNode.children && childNode.children.length)
                        addChildren(childNode, depth+1);
                }
            }
            addChildren(folderTree.get_node('#'), 1);

            details.show();
            button.text('Hide');
        }

    // save changes to notes field
    }).on('input propertychange change', '.link-notes', function () {
        var textarea = $(this);
        saveInput(textarea, textarea.prevAll('.notes-save-status'), 'notes');

    // save changes to title field
    }).on('textchange', '.link-title', function () {
        var textarea = $(this);
        saveInput(textarea, textarea.prevAll('.title-save-status'), 'title', function () {
            // update display title when saved
            textarea.closest('.link-container').find('.link-title-display').text(textarea.val());
        });

    // handle move-to-folder dropdown
    }).on('change', '.move-to-folder', function () {
        moveSelect = $(this);
        moveLink(
            moveSelect.val(), // selected folder_id to move link to
            getLinkIDForFormElement(moveSelect) // link id to move
        ).done(function () {
            showFolderContents(getSelectedFolderID());
        });
    });

    // make links draggable
    linkTable.on('mousedown', '.link-row', function (e) {
        if ($(e.target).hasClass('no-drag'))
            return;

        $.vakata.dnd.start(e, {
            jstree: true,
            obj: $(this),
            nodes: [
                { id: $(this).attr('link_id') }
            ]
        }, '<div id="jstree-dnd" class="jstree-default"><i class="jstree-icon jstree-er"></i>[link]</div>');
    }).on('click', '.link-row td', function (e) {
        $(this).closest('tr').next('.link-details').toggle();
    });
    $(document).on('dnd_start.vakata', function (e, data) {
        $('body').addClass("dragging");

    }).on('dnd_stop.vakata', function (e, data) {
        $('body').removeClass("dragging");

    });


    // *** helpers ***

    function getSelectedNode() {
        return folderTree.get_selected(true)[0];
    }

    function getSelectedFolderID() {
        return getSelectedNode().data.folder_id;
    }

    function editNodeName(node) {
        setTimeout(function () {
            folderTree.edit(node);
        }, 0);
    }

    // *** actions ***

    var showLoadingMessage = false;
    function showFolderContents(folderID, query) {
        if(!query || !query.trim()){
            query = null;
            $('.search-query').val('');  // clear query after user clicks a folder
        }

        // if fetching folder contents takes more than 500ms, show a loading message
        showLoadingMessage = true;
        setTimeout(function(){
            if(showLoadingMessage)
                linkTable.html("Loading folder contents ...");
        }, 500);

        var data = {limit: 0},
            endpoint;

        if (query) {
            data.q = query;
            endpoint = '/archives/';
        }else{
            endpoint = '/folders/' + folderID + '/archives/';
        }

        // fetch contents
        apiRequest("GET", endpoint, data)
            .always(function (data) {
                // same thing runs on success or error, since we get back success or error-displaying HTML
                showLoadingMessage = false;
                data.objects.map(function(obj){
                    if(obj.assets && obj.assets.length){
                        if(obj.assets[0].favicon) obj.favicon_url = settings.DIRECT_MEDIA_URL + obj.assets[0].base_storage_path + '/' + obj.assets[0].favicon;
                    }
                    obj.local_url = mirror_server_host + '/' + obj.guid;
                    obj.can_vest = can_vest;
                    obj.search_query_in_notes = (query && obj.notes.indexOf(query) > -1);
                    obj.url_docs_perma_link_vesting = url_docs_perma_link_vesting;
                    obj.expiration_date_formatted = new Date(obj.expiration_date).format("M. j, Y");
                    obj.creation_timestamp_formatted = new Date(obj.creation_timestamp).format("M. j, Y");
                    if (obj.vested_timestamp) obj.vested_timestamp_formatted = new Date(obj.vested_timestamp).format("M. j, Y");
                });
                linkTable.html(templates.created_link_items({objects:data.objects, query:query}));
            });
    }

    function createFolder(parentFolderID, newName) {
        return apiRequest("POST", "/folders/" + parentFolderID + "/folders/", {name: newName});
    }

    function renameFolder(folderID, newName) {
        return apiRequest("PATCH", "/folders/" + folderID + "/", {name: newName});
    }

    function moveFolder(parentID, childID) {
        return apiRequest("PUT", "/folders/" + parentID + "/folders/" + childID + "/");
    }

    function deleteFolder(folderID) {
        return apiRequest("DELETE", "/folders/" + folderID + "/");
    }

    function moveLink(folderID, linkID) {
        return apiRequest("PUT", "/folders/" + folderID + "/archives/" + linkID + "/");
    }


    // folder buttons
    $('a.new-folder').on('click', function () {
        folderTree.create_node(getSelectedNode(), {}, "last");
        return false;
    });
    $('a.edit-folder').on('click', function () {
        editNodeName(getSelectedNode());
        return false;
    });
    $('a.delete-folder').on('click', function () {
        var node = getSelectedNode();
        if (!confirm("Really delete folder '" + node.text.trim() + "'?"))
            return false;
        folderTree.delete_node(node);
        folderTree.select_node();
        return false;
    });

    // search form
    $('.search-query-form').on('submit', function (e) {
        e.preventDefault();
        var query = $('.search-query').val();
        if(query && query.trim()){
            showFolderContents(getSelectedFolderID(), query);
        }
    });
    linkTable.on('click', 'a.clear-search', function () {
        showFolderContents(getSelectedFolderID());
    });

    var allowedEventsCount = 0,
        lastSelectedFolder = null;
    $('#folder-tree')
        .jstree({
            core: {
                strings: {
                    'New node': 'New Folder'
                },
                check_callback: function (operation, node, node_parent, node_position, more) {
                    // Here we handle all actions on folders that have to be checked with the server.
                    // That means we have to intercept the jsTree event, cancel it,
                    // submit a request to the server, and in the success handler for that request
                    // re-trigger the event so jsTree's UI will update.

                    // Since we can't tell in this event handler whether an event was triggered by the user
                    // (step 1) or by us (step 2), we increment allowedEventsCount when triggering
                    // an event and decrement when the event is received:
                    if (allowedEventsCount) {
                        allowedEventsCount--;
                        return true;
                    }

                    function getDropTarget(){
                        return folderTree.get_node($('.jstree-hovered').parent());
                    }

                    if (more && more.is_foreign) {
                        // link dragged onto folder
                        if (operation == 'copy_node') {
                            var targetNode = getDropTarget();
                            moveLink(targetNode.data.folder_id, node.id).done(function () {
                                showFolderContents(getSelectedFolderID());
                            });
                        }
                    } else {
                        // internal folder action
                        if (operation == 'rename_node') {
                            var newName = node_position;
                            renameFolder(node.data.folder_id, newName).done(function () {
                                allowedEventsCount++;
                                folderTree.rename_node(node, newName);
                            });
                        } else if (operation == 'move_node') {
                            var targetNode = getDropTarget();
                            moveFolder(targetNode.data.folder_id, node.data.folder_id).done(function () {
                                allowedEventsCount++;
                                folderTree.move_node(node, targetNode);
                            });
                        } else if (operation == 'delete_node') {
                            deleteFolder(node.data.folder_id).done(function () {
                                allowedEventsCount++;
                                folderTree.delete_node(node);
                                folderTree.select_node();
                            });
                        } else if (operation == 'create_node') {
                            var newName = node.text;
                            createFolder(node_parent.data.folder_id, newName).done(function (server_response) {
                                allowedEventsCount++;
                                folderTree.create_node(node_parent, node, "last", function (new_folder_node) {
                                    new_folder_node.data = {folder_id: server_response.id};
                                    editNodeName(new_folder_node);
                                });
                            });
                        }
                    }
                    return false; // cancel first instance of event while we check with server
                },
                multiple: true
            },
            plugins: ['contextmenu', 'dnd', 'unique', 'types'],
            dnd: {
                check_while_dragging: false,
                drag_target: '.link-row',
                drag_finish: function (data) {
                    console.log(data);
                }
            },
            types: {
                "default": { // requires quotes because reserved word in IE8
                    icon: "icon-folder-close-alt"
                },
                shared_folder: {
                    icon: "icon-sitemap"
                }
            }

        // handle single clicks on folders -- show contents
        }).on("select_node.jstree", function (e, data) {
            if (data.selected.length == 1) {
                showFolderContents(data.node.data.folder_id);

                // The intuitive interaction seems to be, any time you click on a closed folder we toggle it open,
                // but we only toggle to closed if you click again on the folder that was already selected.
                if(!data.node.state.opened || data.node==lastSelectedFolder)
                    data.instance.toggle_node(data.node);
            }
            lastSelectedFolder = data.node;

        // handle open/close folder icon
        }).on('open_node.jstree', function (e, data) {
            if(data.node.type=="default")
                data.instance.set_icon(data.node, "icon-folder-open-alt");

        }).on('close_node.jstree', function (e, data) {
            if(data.node.type=="default")
                data.instance.set_icon(data.node, "icon-folder-close-alt");

        });

    var folderTree = $.jstree.reference('#folder-tree'),
        firstNode = getSelectedNode(folderTree);

    folderTree.toggle_node(firstNode);
    showFolderContents(firstNode.data.folder_id);
});
