let Papa = require('papaparse');
let Spinner = require('spin.js');

let APIModule = require('./helpers/api.module.js');
let FolderTreeModule = require('./folder-tree.module.js');
let FolderSelectorHelper = require('./helpers/folder-selector.helper.js');
let ProgressBarHelper = require('./helpers/progress-bar.helper.js');
let HandlebarsHelpers = require('./helpers/handlebars.helpers.js');

let target_folder;
let spinner = new Spinner({lines: 15, length: 10, width: 2, radius: 9, corners: 0, color: '#222222', trail: 50});

// elements in the DOM, retrieved during init()
let $batch_details, $batch_details_wrapper, $batch_history, $batch_target_path,
    $export_csv, $input, $input_area, $modal, $spinner, $start_button;


function render_batch(links_in_batch, folder_path) {
    $spinner.hide();
    $spinner.empty();
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
    if (!$spinner[0].childElementCount) {
        spinner.spin($spinner[0]);
    }
    let retrieve_and_render = function() {
        APIModule.request('GET', `/archives/batches/${batch_id}`).then(function(batch_data) {
            let folder_path = FolderTreeModule.getPathForId(batch_data.target_folder).join(" > ");
            let all_completed = render_batch(batch_data.capture_jobs, folder_path);
            if (all_completed) {
                clearInterval(interval);
            }
        })
    }
    retrieve_and_render();
    let interval = setInterval(retrieve_and_render, 2000);
}

export function show_modal_with_batch(batch_id) {
    show_batch(batch_id);
    $modal.modal("show");
}

function start_batch() {
    $input.hide();
    spinner.spin($spinner[0]);
    APIModule.request('POST', '/archives/batches/', {
        "target_folder": target_folder,
        "urls": $input_area.val().split("\n").map(s => {return s.trim()})
    }).then(function(batch_object) {
        let batch_id = batch_object.id;
        show_batch(batch_object.id);
        let template = HandlebarsHelpers.renderTemplate('#link-batch-history-template', {"link_batches": [batch_object]});
        $batch_history.prepend(template);
    });
};

function refresh_target_path_dropdown() {
    FolderSelectorHelper.makeFolderSelector($batch_target_path, target_folder);
};

function set_folder_from_trigger (evt, data) {
    if (typeof data !== 'object') {
        data = JSON.parse(data);
    }
    target_folder = data.folderId;
    $batch_target_path.find("option").each(function() {
        if ($(this).val() == target_folder) {
            $(this).prop("selected", true);
        }
    });
};

function set_folder_from_dropdown(new_folder_id) {
    target_folder = new_folder_id;
};

function populate_link_batch_list() {
    if (settings.ENABLE_BATCH_LINKS) {
        APIModule.request("GET", "/archives/batches/", {"limit": 15}).done(function(data) {
            let template = HandlebarsHelpers.renderTemplate('#link-batch-history-template', {"link_batches": data.objects});
            $batch_history.append(template);
        })
    }
}

function setup_handlers() {
    $(window)
        .on('FolderTreeModule.selectionChange', set_folder_from_trigger)
        .on('dropdown.selectionChange', set_folder_from_trigger);

    $modal
      .on('shown.bs.modal', refresh_target_path_dropdown)
      .on('hidden.bs.modal', function() {
        $input.show();
        $input_area.val("");
        $batch_details_wrapper.hide();
        $spinner.empty();
        $spinner.show();
       });

    $batch_target_path.change(function() {
        let new_folder_id = $(this).val();
        set_folder_from_dropdown(new_folder_id);
    });

    $start_button.click(start_batch);

    $batch_history.delegate('a', 'click', function(e) {
        e.preventDefault();
        $input.hide();
        show_modal_with_batch(this.dataset.batch, parseInt(this.dataset.folder));
    });
 };


export function init() {
    $(function() {
        $batch_details = $('#batch-details');
        $batch_details_wrapper = $('#batch-details-wrapper');
        $batch_history = $("#batch-history");
        $batch_target_path = $('#batch-target-path');
        $export_csv = $('#export-csv');
        $input = $('#batch-create-input');
        $input_area = $('#batch-create-input textarea');
        $modal = $("#batch-modal");
        $spinner = $('.spinner');
        $start_button = $('#start-batch');

        populate_link_batch_list();
        setup_handlers();
    });
}
