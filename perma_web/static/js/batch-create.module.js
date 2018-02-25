var APIModule = require('./helpers/api.module.js');
var FolderTreeModule = require('./folder-tree.module.js');

var $input_area, $start_button, $batch_target_path, $modal;
var target_folder;

var start_batch = function() {
    APIModule.request('POST', '/batches/').then(function(batch_object) {
        var urls = $input_area.val()
            .split("\n")
            .map(function(s) {
                return s.trim();
            });
        urls.forEach(function(url) {
            return APIModule.request('POST', '/archives/', {
                folder: target_folder,
                batch_id: batch_object.id,
                url: url
            }).then(function(response) {
                console.log("success!");
                console.log(response);
                // deal with success
            }).fail(function(err) {
                console.log("fail :(");
                console.error(err);
                // deal with fail
            });
        });
    });
};

var refresh_target_path_dropdown = function() {
    $batch_target_path.empty();
    function addChildren(node, depth) {
        for (var i = 0; i < node.children.length; i++) {
            var childNode = FolderTreeModule.folderTree.get_node(node.children[i]);

            // For each node, we create an <option> using text() for the folder name,
            // and then prepend some &nbsp; to show the tree structure using html().
            // Using html for the whole thing would be an XSS risk.
            $batch_target_path.append(
                $("<option/>", {
                    value: childNode.data.folder_id,
                    text: childNode.text.trim(),
                    selected: childNode.data.folder_id == target_folder
                }).prepend(
                    new Array(depth).join('&nbsp;&nbsp;') + '- '
                )
            );

            // recurse
            if (childNode.children && childNode.children.length) {
                addChildren(childNode, depth + 1);
            }
        }
    }
    addChildren(FolderTreeModule.folderTree.get_node('#'), 1);
};

var set_folder_from_trigger = function(evt, data) {
    if (typeof data !== 'object') {
        data = JSON.parse(data);
    }
    target_folder = data.folderId;
    $batch_target_path.find("option").each(function(ndx) {
        if ($(this).val() == target_folder) {
            $(this).prop("selected", true);
        }
    });
};

var set_folder_from_dropdown = function(new_folder_id) {
    target_folder = new_folder_id;
};

var setupHandlers = function() {
    $modal.on('shown.bs.modal', function() {
        refresh_target_path_dropdown();
    });
    $(window)
        .on('FolderTreeModule.selectionChange', set_folder_from_trigger)
        .on('dropdown.selectionChange', set_folder_from_trigger);
    $batch_target_path.change(function() {
        var new_folder_id = $(this).val();
        set_folder_from_dropdown(new_folder_id);
    });
    $start_button.click(function() {
        start_batch();
    });
 };

export function init () {
    $(function() {
        $modal = $('#batch-create-modal');
        $input_area = $('#batch-create-input textarea');
        $start_button = $('#start-batch');
        $batch_target_path = $('#batch-target-path');

        setupHandlers();
    });
}
