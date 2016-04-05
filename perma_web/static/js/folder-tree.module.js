var FolderTreeModule = FolderTreeModule || {};

$(document).ready(function() {
  FolderTreeModule.domTreeInit();
  FolderTreeModule.init();
  FolderTreeModule.setupEventHandlers();
});

FolderTreeModule.init = function () {
  var firstNode = this.getSelectedNode(),
    folderPath = this.folderTree.get_path(firstNode),
    folderId;

  if (firstNode && firstNode.data) {
    folderId = firstNode.data.folder_id;
  } else {
    folderId = null;
  }

  this.allowedEventsCount = 0;
  this.lastSelectedFolder = null;

  this.folderTree.deselect_all();

  if (firstNode) {
    this.folderTree.select_node(firstNode);
  }
}

FolderTreeModule.setupEventHandlers = function () {
  var self = this;
  $(window)
    .on('dropdown.selectionChange', function () {
      FolderTreeModule.handleSelectionChange();
    })
    .on('LinksListModule.moveLink', function(evt, data) {
      data = JSON.parse(data);
      FolderTreeModule.moveLink(data.folderId, data.linkId);
    });

  // set body class during drag'n'drop
  $(document).on('dnd_start.vakata', function (e, data) {
    $('body').addClass("dragging");

  }).on('dnd_stop.vakata', function (e, data) {
    $('body').removeClass("dragging");
  });

  // folder buttons
  $('a.new-folder').on('click', function () {
    self.folderTree.create_node(self.getSelectedNode(), {}, "last");
    return false;
  });
  $('a.edit-folder').on('click', function () {
    self.editNodeName(self.getSelectedNode());
    return false;
  });
  $('a.delete-folder').on('click', function () {
    var node = self.getSelectedNode();
    if (!confirm("Really delete folder '" + node.text.trim() + "'?")) return false;
    self.folderTree.delete_node(node);
    return false;
  });
}

FolderTreeModule.handleSelectionChange = function () {
  this.folderTree.close_all();
  this.folderTree.deselect_all();
  var node = this.findNodeBySavedFolder();
  this.folderTree.select_node(node);
}

FolderTreeModule.findNodeBySavedFolder = function () {
  var selections = JSON.parse(localStorage.getItem("perma_selection")),
    folderData = this.folderTree._model.data,
    node;
  if (selections && selections[current_user.id] && selections[current_user.id].folderId === "default") {
    node = this.folderTree.get_node('ul > li:first');
    return node;
  }

  if (selections && selections[current_user.id]) {
    for(var i in folderData) {
      if(folderData.hasOwnProperty(i) && folderData[i].data && folderData[i].data.folder_id === selections[current_user.id].folderId) {
        break;
      }
    }
  }
  return this.folderTree.get_node(i);
}

FolderTreeModule.getSelectedNode = function () {
  return this.findNodeBySavedFolder();
}

FolderTreeModule.getSelectedFolderID = function () {
  return this.getSelectedNode().data.folder_id;
}

FolderTreeModule.editNodeName = function (node) {
  setTimeout(function () {
    FolderTreeModule.folderTree.edit(node);
  }, 0);
}

FolderTreeModule.setSelectedFolder = function (node) {
  var folderPath = this.folderTree.get_path(node),
    data = "null";

  if (node.data) {
    var folderId = node.data.folder_id;
    var orgId = node.data.organization_id;
    data = JSON.stringify({path: folderPath, orgId:orgId, folderId:folderId});
  }

  var savedSelections = JSON.parse(localStorage.getItem("perma_selection")) || {};

  if (folderId || orgId) {
    savedSelections[current_user.id] = {'folderId' : folderId, 'orgId' : orgId };
    localStorage.setItem("perma_selection",JSON.stringify(savedSelections));
  }
  $(window).trigger("FolderTreeModule.selectionChange", data );
}


FolderTreeModule.createFolder = function (parentFolderID, newName) {
  return apiRequest("POST", "/folders/" + parentFolderID + "/folders/", {name: newName});
}

FolderTreeModule.renameFolder = function (folderID, newName) {
  return apiRequest("PATCH", "/folders/" + folderID + "/", {name: newName});
}

FolderTreeModule.moveFolder = function (parentID, childID) {
  return apiRequest("PUT", "/folders/" + parentID + "/folders/" + childID + "/");
}

FolderTreeModule.deleteFolder = function (folderID) {
  return apiRequest("DELETE", "/folders/" + folderID + "/");
}

FolderTreeModule.moveLink = function (folderID, linkID) {
  return apiRequest("PUT", "/folders/" + folderID + "/archives/" + linkID + "/").done(function(data){
    $(window).trigger("FolderTreeModule.updateLinksRemaining", data.links_remaining);
    // once we're done moving the link, hide it from the current folder
    $('.item-row[link_id="'+linkID+'"]').closest('.item-container').remove();
  });
}

FolderTreeModule.domTreeInit = function () {
  var self = this;
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
          if (self.allowedEventsCount) {
            self.allowedEventsCount--;
            return true;
          }

          function getDropTarget(){
            return self.folderTree.get_node($('.jstree-hovered').parent());
          }

          if (more && more.is_foreign) {
            // link dragged onto folder
            if (operation == 'copy_node') {
              var targetNode = getDropTarget();
              self.moveLink(targetNode.data.folder_id, node.id);
            }
          } else {
              // internal folder action
            if (operation == 'rename_node') {
              var newName = node_position;
              self.renameFolder(node.data.folder_id, newName)
                .done(function () {
                  self.allowedEventsCount++;
                  self.folderTree.rename_node(node, newName);
                  var folderPath = self.folderTree.get_path(node)
                  var folderId = node.data.folder_id;
                  var orgId = node.data.organization_id;
                  data = JSON.stringify({path: folderPath, orgId:orgId, folderId:folderId});
                  $(window).trigger("FolderTreeModule.selectionChange", data );
                });
            } else if (operation == 'move_node') {
              var targetNode = getDropTarget();
              self.moveFolder(targetNode.data.folder_id, node.data.folder_id).done(function () {
                self.allowedEventsCount++;
                self.folderTree.move_node(node, targetNode);
              });
            } else if (operation == 'delete_node') {
              self.deleteFolder(node.data.folder_id).done(function () {
                self.allowedEventsCount++;
                self.folderTree.delete_node(node);
                self.folderTree.select_node(node.parent);
              });
            } else if (operation == 'create_node') {
              var newName = node.text;
              self.createFolder(node_parent.data.folder_id, newName).done(function (server_response) {
                self.allowedEventsCount++;
                self.folderTree.create_node(node_parent, node, "last", function (new_folder_node) {
                  new_folder_node.data = {folder_id: server_response.id};
                  self.editNodeName(new_folder_node);
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
        // showFolderContents(data.node.data.folder_id);

        // The intuitive interaction seems to be, any time you click on a closed folder we toggle it open,
        // but we only toggle to closed if you click again on the folder that was already selected.
        if(!data.node.state.opened || data.node==this.lastSelectedFolder)
          data.instance.toggle_node(data.node);
      }

      var lastSelectedNode = data.node;
      self.setSelectedFolder(lastSelectedNode);

    // handle open/close folder icon
    }).on('open_node.jstree', function (e, data) {
      if(data.node.type=="default")
        data.instance.set_icon(data.node, "icon-folder-open-alt");

    }).on('close_node.jstree', function (e, data) {
      if(data.node.type=="default")
        data.instance.set_icon(data.node, "icon-folder-close-alt");
    });
  self.folderTree = $.jstree.reference('#folder-tree');
}
