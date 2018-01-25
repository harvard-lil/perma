var APIModule = require('./helpers/api.module.js');
var FolderTreeModule = require('./folder-tree.module.js');

var $input_area, $start_button, $batch_target_path;
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

var set_folder_from_trigger = function(evt, data) {
    if (typeof data !== 'object') {
        data = JSON.parse(data);
    }
    target_folder = data.folderId;
    var path = FolderTreeModule.getPathForId(target_folder);
    $batch_target_path.text(path.join(" > "));
};

var setupHandlers = function() {
    $(window)
        .on('FolderTreeModule.selectionChange', set_folder_from_trigger)
        .on('dropdown.selectionChange', set_folder_from_trigger);
    $start_button.click(function() {
        start_batch();
    });
 };

export function init () {
    $(function() {
        $input_area = $('#batch-create-input textarea');
        $start_button = $('#start-batch');
        $batch_target_path = $('#batch-target-path');

        setupHandlers();
    });
}
