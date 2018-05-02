let Papa = require('papaparse');
let Spinner = require('spin.js');

let APIModule = require('./helpers/api.module.js');
let FolderTreeModule = require('./folder-tree.module.js');
let FolderSelectorHelper = require('./helpers/folder-selector.helper.js');
let ProgressBarHelper = require('./helpers/progress-bar.helper.js');
let HandlebarsHelpers = require('./helpers/handlebars.helpers.js');

let $modal,
    $input,
    $input_area,
    $start_button,
    $cancel_button,
    $batch_details_wrapper,
    $batch_details,
    $batch_history,
    $batch_target_path,
    $export_csv;
let target_folder;


function render_batch(links_in_batch, folder_path) {
    $('.spinner').hide();
    $batch_details.empty();
    let all_completed = true;
    links_in_batch.forEach(function(link) {
        link.progress = (link.step_count / 5) * 100;
        link.local_url = link.guid ? `${window.host}/${link.guid}` : null;
        switch(link.status){
            case "pending":
            case "in_progress":
                link.isProcessing = true;
                all_completed = false;
                break;
            case "completed":
                link.isComplete = true;
                break;
            default:
                link.isError = true;
                link.error_message = APIModule.stripDataStructure(JSON.parse(link.message));
        }
    });
    let template = HandlebarsHelpers.renderTemplate('#batch-links', {"links": links_in_batch, "folder": folder_path});
    $batch_details.append(template);
    if (all_completed) {
        let export_data = links_in_batch.map(function(link) {
            let to_export = {
                "url": link.submitted_url
            };
            if (link.status === "completed") {
                to_export["status"] = "success"
                to_export["error_message"] = ""
                to_export["title"] = link.title;
                to_export["perma_link"] = `${window.location.protocol}//${link.local_url}`;
            } else {
                to_export["status"] = "error"
                to_export["error_message"] = link.error_message
                to_export["title"] = ""
                to_export["perma_link"] = ""
            }
            return to_export;
        });
        let csv = Papa.unparse(export_data);
        $export_csv.attr("href", "data:text/csv;charset=utf-8," + encodeURI(csv));
        $export_csv.attr("download", "perma.csv");
        $export_csv.show();
    }
    return all_completed;
};

function show_batch(batch_id) {
    $batch_details_wrapper.show();
    $batch_details.empty();
    let spinner = $('.spinner');
    if (spinner[0].childElementCount) {
        spinner.show()
    } else {
        new Spinner({lines: 15, length: 10, width: 2, radius: 9, corners: 0, color: '#222222', trail: 50, top: '20px'}).spin(spinner[0]);
    }
    let interval = setInterval(function() {
        APIModule.request('GET', `/archives/batches/${batch_id}`).then(function(batch_data) {
            let folder_path = FolderTreeModule.getPathForId(batch_data.target_folder).join(" > ");
            let all_completed = render_batch(batch_data.capture_jobs, folder_path);
            if (all_completed) {
                clearInterval(interval);
            }
        })
    }(), 2000);
}

export function show_modal_with_batch(batch_id) {
    show_batch(batch_id);
    $modal.modal("show");
}

var start_batch = function() {
    $input.hide();
    // $input_area.prop("disabled", true).css("cursor", "not-allowed");
    // $cancel_button.css("visibility", "hidden");
    // $start_button.prop("disabled", true).addClass("_isWorking").text(" ");
    // var spinner = new Spinner({lines: 15, length: 2, width: 2, radius: 9, corners: 0, color: '#2D76EE', trail: 50, top: '12px'}).spin($start_button[0]);

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
                show_batch(batch_object.id);
                // prepend a new entry to $batch_history
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

    $modal.on('shown.bs.modal', function() {
        refresh_target_path_dropdown();
    });

    $modal.on('hidden.bs.modal', function() {
        $input.show();
        $input_area.val("");
        $batch_details_wrapper.hide();
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

    $batch_history.delegate('a', 'click', function(e) {
        e.preventDefault();
        $input.hide();
        show_modal_with_batch(this.dataset.batch, parseInt(this.dataset.folder));
    });
 };



export function init() {
    $(function() {

        $modal = $("#batch-modal");
        $input = $('#batch-create-input');
        $input_area = $('#batch-create-input textarea');
        $start_button = $('#start-batch');
        $cancel_button = $modal.find('.cancel');
        $batch_details_wrapper = $('#batch-details-wrapper');
        $batch_details = $('#batch-details');
        $batch_history = $("#batch-history");
        $batch_target_path = $('#batch-target-path');
        $export_csv = $('#export-csv');

        setup_handlers();
    });
}
