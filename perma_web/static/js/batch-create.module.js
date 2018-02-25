var APIModule = require('./helpers/api.module.js');
var FolderTreeModule = require('./folder-tree.module.js');
var FolderSelectorHelper = require('./helpers/folder-selector.helper.js');

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
    FolderSelectorHelper.makeFolderSelector($batch_target_path, target_folder);
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
