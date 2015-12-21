$(function() {
    var linkTable = $('.item-rows'),
        dragStartPosition,
        lastRowToggleTime = 0;

    function getLinkIDForFormElement(element){
        return element.closest('.item-container').find('.item-row').attr('link_id');
    }

    // save changes in a given text box to the server
    var saveBufferSeconds = .5,
        timeouts = {};
    function saveInput(inputElement, statusElement, name, callback) {
        statusElement.html('Saving...');

        var guid = inputElement.attr('id').match(/.+-(.+-.+)/)[1],
            timeoutKey = guid+name;

        if(timeouts[timeoutKey])
            clearTimeout(timeouts[timeoutKey]);

        // use a setTimeout so notes are only saved once every few seconds
        timeouts[timeoutKey] = setTimeout(function () {
            var data = {};
            data[name] = inputElement.val();
            var request = apiRequest("PATCH", '/archives/' + guid + '/', data).done(function(data){
                statusElement.html('Saved!');
            });
            if (callback) request.done(callback);
        }, saveBufferSeconds*1000);
    }

    /*
        Link rows respond to both a *click* to hide/show details, and a *drag* to move to different folders.
        So we start the drag on mousedown, and then check on mouseup whether it's more like a click or drag.
     */

    // .item-row mousedown -- start drag event
    linkTable.on('mousedown touchstart', '.item-row', function (e) {
        if ($(e.target).hasClass('no-drag'))
            return;

        $.vakata.dnd.start(e, {
            jstree: true,
            obj: $(this),
            nodes: [
                {id: $(this).attr('link_id')}
            ]
        }, '<div id="jstree-dnd" class="jstree-default"><i class="jstree-icon jstree-er"></i>[link]</div>');

        // record drag start position so we can check how far we were dragged on mouseup
        dragStartPosition = [e.pageX || e.originalEvent.touches[0].pageX, e.pageY || e.originalEvent.touches[0].pageY];

    // .item-row mouseup -- hide and show link details, if not dragging
    }).on('mouseup touchend', '.item-row', function (e) {
        // prevent JSTree's tap-to-drag behavior
        $.vakata.dnd.stop(e);

        // don't treat this as a click if the mouse has moved more than 5 pixels -- it's probably an aborted drag'n'drop or touch scroll
        if(dragStartPosition && Math.sqrt(Math.pow(e.pageX-dragStartPosition[0], 2)*Math.pow(e.pageY-dragStartPosition[1], 2))>5)
            return;

        // don't toggle faster than twice a second (in case we get both mouseup and touchend events)
        if(new Date().getTime() - lastRowToggleTime < 500)
            return;
        lastRowToggleTime = new Date().getTime();

        // hide/show link details
        var linkContainer = $(this).closest('.item-container'),
            details = linkContainer.find('.item-details');
        if(details.is(":visible")){
            details.hide();
            linkContainer.toggleClass( '_active' )
        }else {
            // when showing link details, update the move-to-folder select input
            // based on the current folderTree structure

            // first clear the select ...
            var currentFolderID = getSelectedFolderID(),
                moveSelect = details.find('.move-to-folder');
            moveSelect.find('option').remove();

            // recursively populate select ...
            function addChildren(node, depth) {
                for (var i = 0; i < node.children.length; i++) {
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
                            new Array(depth).join('&nbsp;&nbsp;') + '- '
                        )
                    );

                    // recurse
                    if (childNode.children && childNode.children.length)
                        addChildren(childNode, depth + 1);
                }
            }

            addChildren(folderTree.get_node('#'), 1);

            details.show();
            linkContainer.toggleClass('_active')
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
            textarea.closest('.item-container').find('.item-title-display span').text(textarea.val());
        });

    // handle move-to-folder dropdown
    }).on('change', '.move-to-folder', function () {
        var moveSelect = $(this);
        moveLink(
            moveSelect.val(), // selected folder_id to move link to
            getLinkIDForFormElement(moveSelect) // link id to move
        );
    });

    // set body class during drag'n'drop
    $(document).on('dnd_start.vakata', function (e, data) {
        $('body').addClass("dragging");

    }).on('dnd_stop.vakata', function (e, data) {
        $('body').removeClass("dragging");

    });


    // *** helpers ***

    function getSelectedNode() {
      var node = findNodeBySavedFolder();
      return node;
    }

    function getSelectedFolderID() {
        return getSelectedNode().data.folder_id;
    }

    function editNodeName(node) {
        setTimeout(function () {
            folderTree.edit(node);
        }, 0);
    }

    function findNodeBySavedFolder () {
      var folder     = localStorage.getItem("perma_selected_folder"),
        parsedFolder = JSON.parse(folder),
        folderData   = folderTree._model.data,
        node;

      if (parsedFolder && parsedFolder.folderID === "default") {
        node = folderTree.get_node('ul > li:first');
        return node;
      }

      if (parsedFolder) {
        for(var i in folderData) {
          if(folderData.hasOwnProperty(i) && folderData[i].data && folderData[i].data.folder_id === parsedFolder.folderID) {
            break;
          }
        }
      }

      node = folderTree.get_node(i);
      node = node || folderTree.get_node('ul > li:first');
      return node;
    }

    function getFolderByNode(node) {
      var folderID = node.data.folder_id,
        folder = { 'folderID' : folderID };
      return folder;
    }

    function updateLocalStorage(node) {
      var folder = getFolderByNode(node);
      localStorage.setItem("perma_selected_folder", JSON.stringify(folder));
    }

    function updatePathWithSelected(node) {
      var path = folderTree.get_path(node);
      if (!path) {
        return;
      }

      var stringPath = path.join(" &gt; ");
      /*
        if node doesn't have an organization id and its parent doesn't have organization id
        that means it's inside "My Links" we have to check because newly created
        folders don't have orgIDs in their data
      */
      var parentNode = folderTree.get_node(node.parent);
      if ((parentNode.data && !parentNode.data.organization_id) || (!node.data.organization_id && !parentNode.data)) {
        stringPath += "<span class='links-remaining'>" + links_remaining + "<span></a></li>";
      }

      $('#organization_select_form').find('.dropdown-toggle').html(stringPath);
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
                linkTable.empty().html('<div class="alert-info">Loading folder contents...</div>');
        }, 500);

        var requestCount = 20,
            requestData = {limit: requestCount, offset:0},
            endpoint;

        if (query) {
            requestData.q = query;
            endpoint = '/archives/';
        }else{
            endpoint = '/folders/' + folderID + '/archives/';
        }

        // Content fetcher.
        // This is wrapped in a function so it can be called repeatedly for infinite scrolling.
        function getNextContents() {
            apiRequest("GET", endpoint, requestData).always(function (response) {
                // same thing runs on success or error, since we get back success or error-displaying HTML
                showLoadingMessage = false;
                var links = response.objects;
                $.each(links, function (i, obj) {
                    $.each(obj.captures, function (i, capture) {
                        if (capture.role == 'favicon' && capture.status == 'success')
                            obj.favicon_url = capture.playback_url;
                    });
                    obj.local_url = host + '/' + obj.guid;
                    obj.can_vest = true;
                    obj.search_query_in_notes = (query && obj.notes.indexOf(query) > -1);
                    obj.expiration_date_formatted = new Date(obj.expiration_date).format("F j, Y");
                    obj.creation_timestamp_formatted = new Date(obj.creation_timestamp).format("F j, Y");
                    if (obj.vested_timestamp) {
                        obj.vested_timestamp_formatted = new Date(obj.vested_timestamp).format("F j, Y");
                    }
                    if (Date.now() < Date.parse(obj.archive_timestamp)) {
                        obj.delete_available = true;
                    }
                });

                // append HTML
                if(requestData.offset==0)
                    linkTable.empty();
                linkTable.find('.links-loading-more').remove();
                linkTable.append(templates.created_link_items({links: links, query: query}));

                // If we received exactly `requestCount` number of links, there may be more to fetch from the server.
                // Set a waypoint event to trigger when the last link comes into view.
                if(links.length == requestCount){
                    requestData.offset += requestCount;
                    linkTable.find('.item-container:last').waypoint(function(direction) {
                        this.destroy();  // cancel waypoint
                        linkTable.append('<div class="links-loading-more">Loading more ...</div>');
                        getNextContents();
                    }, {
                        offset:'100%'  // trigger waypoint when element hits bottom of window
                    });
                }

            });
        }
        getNextContents();
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
        return apiRequest("PUT", "/folders/" + folderID + "/archives/" + linkID + "/").done(function(){
            // once we're done moving the link, hide it from the current folder
            $('.item-row[link_id="'+linkID+'"]').closest('.item-container').remove();
        });
    }

    // *** events ***
    $(window).on('dropdown.selectionChange', function () {
      var saved = localStorage.getItem("perma_selected_folder");
      folderTree.close_all();
      folderTree.deselect_all();
      var node = findNodeBySavedFolder();
      folderTree.select_node(node);

    });

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
        lastSelectedFolder = null,
        initialized = false;
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
                            moveLink(targetNode.data.folder_id, node.id);
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
                                folderTree.select_node(node.parent);
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
                drag_target: '.item-row',
                drag_finish: function (data) {
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
            if (!initialized) {
              initialized = true;
              return
            }
            /*
              only update path and localStorage if
              this is an actual event that's firing
              not on initialization
            */
            var lastSelectedNode = data.node;
            updateLocalStorage(lastSelectedNode);
            updatePathWithSelected(lastSelectedNode);

        // handle open/close folder icon
        }).on('open_node.jstree', function (e, data) {
            if(data.node.type=="default")
                data.instance.set_icon(data.node, "icon-folder-open-alt");

        }).on('close_node.jstree', function (e, data) {
            if(data.node.type=="default")
                data.instance.set_icon(data.node, "icon-folder-close-alt");
        });

      var folderTree = $.jstree.reference('#folder-tree'),
          firstNode = findNodeBySavedFolder();
      folderTree.deselect_all();
      folderTree.select_node(firstNode);

    updatePathWithSelected(firstNode);
    showFolderContents(firstNode.data.folder_id);
});
