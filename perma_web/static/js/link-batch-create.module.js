var Spinner = require('spin.js');

var APIModule = require('./helpers/api.module.js');
var FolderTreeModule = require('./folder-tree.module.js');
var FolderSelectorHelper = require('./helpers/folder-selector.helper.js');
var LinkBatchViewModule = require('./link-batch-view.module.js');
var LinkBatchHelpers = require('./helpers/link-batch.helpers.js');

var $create_modal, $view_modal;
var $input_area, $start_button, $cancel_button, $batch_target_path;
var $batches_history_list;
var target_folder;

var start_batch = function() {
    $input_area.prop("disabled", true).css("cursor", "not-allowed");
    $cancel_button.css("visibility", "hidden");
    $start_button.prop("disabled", true).addClass("_isWorking").text(" ");
    var spinner = new Spinner({lines: 15, length: 2, width: 2, radius: 9, corners: 0, color: '#2D76EE', trail: 50, top: '12px'}).spin($start_button[0]);

    APIModule.request('POST', '/archives/batches/', {
        "target_folder": target_folder
    }).then(function(batch_object) {
        var batch_id = batch_object.id;
        var urls = $input_area.val()
            .split("\n")
            .map(function(s) {
                return s.trim();
            });
        var num_requests = 0;
        urls.forEach(function(url) {
            return APIModule.request('POST', '/archives/', {
                folder: target_folder,
                link_batch_id: batch_id,
                url: url
            }, { "error": function(jqXHR) {} }).then(function(response) {
                num_requests += 1;
            }).fail(function(err) {
                num_requests += 1;
                console.error(err);
            });
        });
        var interval = setInterval(function() {
            if (num_requests === urls.length) {
                clearInterval(interval);
                $input_area.empty();
                $create_modal.modal("hide");
                LinkBatchHelpers.show_modal_with_batch(batch_object);
                var $li = $("<li>");
                LinkBatchHelpers.create_clickable_batch_el($li, batch_object);
                $batches_history_list.prepend($li);
            }
        }, 500);
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

var setup_handlers = function() {
    $create_modal.on('shown.bs.modal', function() {
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

export function init() {
    $(function() {
        $create_modal = $('#batch-create-modal');
        $view_modal = $('#batch-view-modal');
        $input_area = $('#batch-create-input textarea');
        $start_button = $('#start-batch');
        $cancel_button = $create_modal.find('.cancel');
        $batch_target_path = $('#batch-target-path');
        $batches_history_list = $("#batches-history-list");

        setup_handlers();
    });
}
