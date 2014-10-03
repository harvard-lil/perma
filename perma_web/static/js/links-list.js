$(function() {
    var linkTable = $('.link-rows');

    // helpers
    function postJSON(url, data, callback, failureCallback) {
        return $.ajax({
                          url: url,
                          type: "POST",
                          dataType: 'json',
                          data: data,
                          success: callback,
                          traditional: true // use Django-style array serialization
                      }).fail(
                failureCallback || function (jqXHR) {
                informUser(jqXHR.status == 400 && jqXHR.responseText ? jqXHR.responseText : "Error " + jqXHR.status, 'danger');
            }
        );
    }

    function getLinkIDForFormElement(element){
        return element.closest('.link-container').find('.link-row').attr('link_id');
    }

    // save changes to a given text box to the server
    var saveNeeded = false,
        lastSaveTime = 0,
        saveBufferSeconds = 3;
    function saveInput(inputElement, statusElement, name, callback) {
        statusElement.html('saving ...');
        saveNeeded = true;

        // use a setTimeout so notes are only saved once every few seconds
        setTimeout(function () {
            if (saveNeeded) {
                saveNeeded = false;
                lastSaveTime = new Date().getTime();
                request = postJSON('#',
                                   {
                                       action: 'save_link_attribute',
                                       link_id: getLinkIDForFormElement(inputElement),
                                       name: name,
                                       value: inputElement.val()
                                   },
                                   function (data) {
                                       statusElement.html('saved.')
                                   }
                );
                if (callback)
                    request.done(callback);
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
            var moveSelect = details.find('.move-to-folder');
            moveSelect.find('option').remove();

            // recursively populate select ...
            function addChildren(node, depth){
                for(var i=0;i<node.children.length;i++){
                    var childNode = folderTree.get_node(node.children[i]);

                    // For each node, we create an <option> using text() for the folder name,
                    // and then prepend some &nbsp; to show the tree structure using html().
                    // Using html for the whole thing would be an XSS risk.
                    moveSelect.append($("<option/>", {
                        value: childNode.data.folder_id,
                        text: childNode.text.trim()
                    }).prepend(new Array(depth).join('&nbsp;&nbsp;')+'- '));

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
    }).on('input propertychange', '.link-notes', function () {
        var textarea = $(this);
        saveInput(textarea, textarea.prevAll('.notes-save-status'), 'notes');

    // save changes to title field
    }).on('input propertychange', '.link-title', function () {
        var textarea = $(this);
        saveInput(textarea, textarea.prevAll('.title-save-status'), 'submitted_title', function () {
            // update display title when saved
            textarea.closest('.link-container').find('.link-title-display').text(textarea.val());
        });

    // handle move-to-folder dropdown
    }).on('change', '.move-to-folder', function () {
        moveSelect = $(this);
        moveItems(
            moveSelect.find("option:selected").val(), // selected folder_id to move link to
            [getLinkIDForFormElement(moveSelect)], // link id to move
            []
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

    function getFolderURL(folderID) {
        if (!folderID)
            folderID = getSelectedFolderID();
        return folderContentsURL.replace('FOLDER_ID', folderID);
    }

    function postJSONToFolder(folderID, json) {
        return postJSON(getFolderURL(folderID), json);
    }

    function editNodeName(node) {
        setTimeout(function () {
            folderTree.edit(node)
        }, 0);
    }

    // *** actions ***

    function showFolderContents(folderID) {
        $.get(getFolderURL(folderID))
            .always(function (data) {
                        // same thing runs on success or error
                        linkTable.html(data.responseText || data);
                    });
    }

    function createFolder(parentFolderID, newName) {
        return postJSONToFolder(parentFolderID, {action: 'new_folder', name: newName});
    }

    function renameFolder(folderID, newName) {
        return postJSONToFolder(folderID, {action: 'rename_folder', name: newName});
    }

    function moveItems(targetFolderID, links, folders) {
        return postJSONToFolder(targetFolderID, {action: 'move_items', links: links, folders: folders});
    }

    function deleteFolder(folderID) {
        return postJSON(
            getFolderURL(folderID),
            {action: 'delete_folder'}
        );
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
        $.get(getFolderURL(null) + '?q=' + $('.search-query').val())
            .always(function (data) {
                        // same thing runs on success or error
                        linkTable.html(data.responseText || data);
                    });
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

                    if (more && more.is_foreign) {
                        // link dragged onto folder
                        if (operation == 'copy_node') {
                            moveItems(node_parent.data.folder_id, [node.id], []).done(function () {
                                showFolderContents(getSelectedFolderID());
                            });
                        }
                    } else {
                        // internal folder action
                        if (operation == 'rename_node') {
                            newName = node_position;
                            renameFolder(node.data.folder_id, newName).done(function () {
                                allowedEventsCount++;
                                folderTree.rename_node(node, newName);
                            });
                        } else if (operation == 'move_node') {
                            moveItems(node_parent.data.folder_id, [], [node.data.folder_id]).done(function () {
                                allowedEventsCount++;
                                folderTree.move_node(node, node_parent);
                            });
                        } else if (operation == 'delete_node') {
                            deleteFolder(node.data.folder_id).done(function () {
                                allowedEventsCount++;
                                folderTree.delete_node(node);
                                folderTree.select_node();
                            });
                        } else if (operation == 'create_node') {
                            newName = node.text;
                            createFolder(node_parent.data.folder_id, newName).done(function (server_response) {
                                allowedEventsCount++;
                                folderTree.create_node(node_parent, node, "last", function (new_folder_node) {
                                    new_folder_node.data = {folder_id: server_response.new_folder_id};
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
                default: {
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