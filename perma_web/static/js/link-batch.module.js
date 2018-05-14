let Papa = require('papaparse');
let Spinner = require('spin.js');

let APIModule = require('./helpers/api.module.js');
var DOMHelpers = require('./helpers/dom.helpers.js');
let FolderTreeModule = require('./folder-tree.module.js');
let FolderSelectorHelper = require('./helpers/folder-selector.helper.js');
let Modals = require('./modals.module.js');
let ProgressBarHelper = require('./helpers/progress-bar.helper.js');

let batchHistoryTemplate = require("./hbs/link-batch-history.handlebars");
let batchLinksTemplate = require("./hbs/batch-links.handlebars");

let target_folder;
let spinner = new Spinner({lines: 15, length: 10, width: 2, radius: 9, corners: 0, color: '#222222', trail: 50});

// elements in the DOM, retrieved during init()
let $batch_details, $batch_details_wrapper, $batch_history, $batch_list_container,
    $batch_progress_report, $batch_target_path, $create_batch, $export_csv,
    $input, $input_area, $loading, $modal, $modal_close, $spinner, $start_button;


function render_batch(links_in_batch, folder_path) {
    let all_completed = true;
    let batch_progress = []
    let errors = 0;
    links_in_batch.forEach(function(link) {
        link.progress = (link.step_count / 6) * 100;
        link.local_url = link.guid ? `${window.host}/${link.guid}` : null;
        switch(link.status){
            case "pending":
            case "in_progress":
                link.isProcessing = true;
                all_completed = false;
                batch_progress.push(link.progress);
                break;
            case "completed":
                link.isComplete = true;
                batch_progress.push(link.progress);
                break;
            default:
                link.isError = true;
                link.error_message = APIModule.stripDataStructure(JSON.parse(link.message));
                errors += 1;
        }
    });
    let percent_complete = Math.round(batch_progress.reduce((a, b) => a + b, 0) / (batch_progress.length * 100) * 100)
    let message = `Batch ${percent_complete}% complete`;
    if (errors > 0){
        message += `, ${errors} errors.`
    }
    $batch_progress_report.html(message);
    let template = batchLinksTemplate({"links": links_in_batch, "folder": folder_path});
    $batch_details.html(template);
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
        $export_csv.removeClass("_hide");
    }
    return all_completed;
};

function show_batch(batch_id) {
    $batch_details.empty();
    $batch_details_wrapper.removeClass("_hide");
    if (!$spinner[0].childElementCount) {
        spinner.spin($spinner[0]);
        $spinner.removeClass("_hide");
    }
    let first_time = true;
    let retrieve_and_render = function() {
        APIModule.request(
            'GET', `/archives/batches/${batch_id}`
        ).then(function(batch_data) {
            if (first_time) {
                first_time = false;
                $batch_progress_report.focus();
                spinner.stop();
                $spinner.addClass("_hide");
                $batch_details.attr("aria-hidden", "true");
                // prevents tabbing to elements that are getting swapped out
                $batch_details.find('*').each(function(){$(this).attr('tabIndex', '-1')});
            }
            let folder_path = FolderTreeModule.getPathForId(batch_data.target_folder).join(" > ");
            let all_completed = render_batch(batch_data.capture_jobs, folder_path);
            if (all_completed) {
                clearInterval(interval);
                $batch_details.attr("aria-hidden", "false");
                // undo our special focus handling
                $batch_details.find('*').each(function(){$(this).removeAttr('tabIndex')});
            }
        }).catch(function(error){
            console.log(error);
            clearInterval(interval);
            $modal.modal("hide");
        });
    }
    retrieve_and_render();
    let interval = setInterval(retrieve_and_render, 2000);
}

export function show_modal_with_batch(batch_id) {
    show_batch(batch_id);
    $modal.modal("show");
}

function start_batch() {
    $modal_close.hide();
    $input.hide();
    spinner.spin($spinner[0]);
    $spinner.removeClass("_hide");
    $loading.focus();
    APIModule.request('POST', '/archives/batches/', {
        "target_folder": target_folder,
        "urls": $input_area.val().split("\n").map(s => {return s.trim()}).filter(Boolean)
    }).then(function(data) {
        $modal_close.show();
        show_batch(data.id);
        populate_link_batch_list();
        $(window).trigger("BatchLinkModule.batchCreated", data.links_remaining);
    }).catch(function(e){
        console.log(e);
        $modal_close.show();
        $modal.modal("hide");
        // we should flash the error here,
        // instead of just closing the modal
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

function populate_link_batch_list(limit=7) {
    if (settings.ENABLE_BATCH_LINKS) {
        APIModule.request('GET', '/archives/batches/', {
            'limit': limit
        }).then(function(data) {
            if (data.objects.length > 0) {
                let template = batchHistoryTemplate({'link_batches': data.objects, 'next': data.meta.next});
                $batch_history.html(template);
                $batch_list_container.removeClass('_hide');
                DOMHelpers.scrollIfTallerThanFractionOfViewport(".col-folders", 0.9);
            }
        }).catch(function(e){
            console.log(e);
            $batch_history.html('<p>(unavailable)</p>')
        });
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
        $batch_details_wrapper.addClass("_hide");
        spinner.stop();
        $spinner.addClass("_hide");
        $export_csv.addClass("_hide");
        $batch_progress_report.empty();
       });

    $batch_target_path.change(function() {
        let new_folder_id = $(this).val();
        set_folder_from_dropdown(new_folder_id);
    });

    $start_button.click(start_batch);

    $batch_list_container
        .on('shown.bs.collapse', function(){
            DOMHelpers.scrollIfTallerThanFractionOfViewport(".col-folders", 0.9);})
        .on('hidden.bs.collapse', function(){
            DOMHelpers.scrollIfTallerThanFractionOfViewport(".col-folders", 0.9);
        });

    $create_batch.click(function() {
        Modals.returnFocusTo(this);
    });

    $batch_history.delegate('a[data-batch]', 'click', function(e) {
        e.preventDefault();
        $input.hide();
        show_modal_with_batch(this.dataset.batch, parseInt(this.dataset.folder));
        Modals.returnFocusTo(this);
    });

    $batch_history.delegate('#all-batches', 'click', function(e) {
        e.preventDefault();
        populate_link_batch_list(null);
        $batch_history.focus();
    });
 };


export function init() {
    $(function() {
        $batch_details = $('#batch-details');
        $batch_details_wrapper = $('#batch-details-wrapper');
        $batch_history = $("#batch-history");
        $batch_list_container = $('#batch-list-container');
        $batch_progress_report = $('#batch-progress-report');
        $batch_target_path = $('#batch-target-path');
        $create_batch = $('#create-batch');
        $export_csv = $('#export-csv');
        $input = $('#batch-create-input');
        $input_area = $('#batch-create-input textarea');
        $loading = $('#loading');
        $modal = $("#batch-modal");
        $modal_close = $("#batch-modal .close");
        $spinner = $('.spinner');
        $start_button = $('#start-batch');


        populate_link_batch_list();
        setup_handlers();
    });
}
