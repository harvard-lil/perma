require('jstree');  // add jquery support for .tree
require('jstree-css/default/style.min.css');

var APIModule = require('./helpers/api.module.js');


var allowedEventsCount = 0;
var lastSelectedFolder = null;
export var folderTree = null;

export function init () {
  domTreeInit();
  setupEventHandlers ();

  folderTree.deselect_all();

  var firstNode = getSelectedNode();
  if (firstNode)
    folderTree.select_node(firstNode);
}

function setupEventHandlers () {
  $(window)
    .on('dropdown.selectionChange', handleSelectionChange)
    .on('LinksListModule.moveLink', function(evt, data) {
      data = JSON.parse(data);
      moveLink(data.folderId, data.linkId);
    });

  // set body class during drag'n'drop
  $(document).on('dnd_start.vakata', function (e, data) {
    $('body').addClass("dragging");

  }).on('dnd_stop.vakata', function (e, data) {
    $('body').removeClass("dragging");
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
    if (!confirm("Really delete folder '" + node.text.trim() + "'?")) return false;
    folderTree.delete_node(node);
    return false;
  });
}

function handleSelectionChange () {
  folderTree.close_all();
  folderTree.deselect_all();
  var node = findNodeBySavedFolder();
  folderTree.select_node(node);
}

function findNodeBySavedFolder () {
  var selections = JSON.parse(localStorage.getItem("perma_selection")),
    folderData = folderTree._model.data,
    node;
  if (selections && selections[current_user.id] && selections[current_user.id].folderId === "default") {
    node = folderTree.get_node('ul > li:first');
    return node;
  }

  if (selections && selections[current_user.id]) {
    for(var i in folderData) {
      if(folderData.hasOwnProperty(i) && folderData[i].data && folderData[i].data.folder_id === selections[current_user.id].folderId) {
        break;
      }
    }
  }
  return folderTree.get_node(i);
}

function getSelectedNode () {
  return findNodeBySavedFolder();
}

function getSelectedFolderID () {
  return getSelectedNode().data.folder_id;
}

function editNodeName (node) {
  setTimeout(function () {
    folderTree.edit(node);
  }, 0);
}

function getNodeData (node) {
  var data = {};
  if (node.data) {
    data.folderId = node.data.folder_id;
    data.orgId = node.data.organization_id;
    data.path = folderTree.get_path(node);
  }
  return data;
}

function setSelectedFolder (node) {
  var data = getNodeData(node);
  var savedSelections = JSON.parse(localStorage.getItem("perma_selection")) || {};

  if (data.folderId || data.orgId) {
    savedSelections[current_user.id] = {'folderId' : data.folderId, 'orgId' : data.orgId };
    localStorage.setItem("perma_selection",JSON.stringify(savedSelections));
  }
  $(window).trigger("FolderTreeModule.selectionChange", JSON.stringify(data) );
}


function createFolder (parentFolderID, newName) {
  return APIModule.request("POST", "/folders/" + parentFolderID + "/folders/", {name: newName});
}

function renameFolder (folderID, newName) {
  return APIModule.request("PATCH", "/folders/" + folderID + "/", {name: newName});
}

function moveFolder (parentID, childID) {
  return APIModule.request("PUT", "/folders/" + parentID + "/folders/" + childID + "/");
}

function deleteFolder (folderID) {
  return APIModule.request("DELETE", "/folders/" + folderID + "/");
}

function moveLink (folderID, linkID) {
  return APIModule.request("PUT", "/folders/" + folderID + "/archives/" + linkID + "/").done(function(data){
    $(window).trigger("FolderTreeModule.updateLinksRemaining", data.links_remaining);
    // once we're done moving the link, hide it from the current folder
    $('.item-row[data-link_id="'+linkID+'"]').closest('.item-container').remove();
  });
}

function domTreeInit () {
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
              renameFolder(node.data.folder_id, newName)
                .done(function () {
                  allowedEventsCount++;
                  folderTree.rename_node(node, newName);
                  var data = getNodeData(node);
                  data = JSON.stringify(data);
                  $(window).trigger("FolderTreeModule.selectionChange", data );
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
                  new_folder_node.data = { folder_id: server_response.id, organization_id: node_parent.data.organization_id };
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
        // showFolderContents(data.node.data.folder_id);

        // The intuitive interaction seems to be, any time you click on a closed folder we toggle it open,
        // but we only toggle to closed if you click again on the folder that was already selected.
        if(!data.node.state.opened || data.node==lastSelectedFolder)
          data.instance.toggle_node(data.node);
      }

      var lastSelectedNode = data.node;
      setSelectedFolder(lastSelectedNode);

    // handle open/close folder icon
    }).on('open_node.jstree', function (e, data) {
      if(data.node.type=="default")
        data.instance.set_icon(data.node, "icon-folder-open-alt");

    }).on('close_node.jstree', function (e, data) {
      if(data.node.type=="default")
        data.instance.set_icon(data.node, "icon-folder-close-alt");
    });
  folderTree = $.jstree.reference('#folder-tree');
}


