let Papa = require('papaparse');
let Spinner = require('spin.js');

let APIModule = require('./helpers/api.module.js');
var DOMHelpers = require('./helpers/dom.helpers.js');
var ErrorHandler = require('./error-handler.js');
let FolderTreeModule = require('./folder-tree.module.js');
let FolderSelectorHelper = require('./helpers/folder-selector.helper.js');
let Helpers = require('./helpers/general.helpers.js');
let Modals = require('./modals.module.js');
let ProgressBarHelper = require('./helpers/progress-bar.helper.js');

let batchHistoryTemplate = require("./hbs/link-batch-history.handlebars");
let batchLinksTemplate = require("./hbs/batch-links.handlebars");

let target_folder;
let spinner = new Spinner({lines: 15, length: 10, width: 2, radius: 9, corners: 0, color: '#222222', trail: 50});
let interval;

// elements in the DOM, retrieved during init()
let $batch_details, $batch_details_wrapper, $batch_history, $batch_list_container,
    $batch_modal_title, $batch_progress_report, $batch_target_path, $create_batch,
    $create_batch_wrapper, $export_csv, $input, $input_area, $loading, $modal,
    $spinner, $start_button;


function render_batch(links_in_batch, folder_path) {
    const average_capture_time = 9;
    const celery_workers = 6;
    const steps = 6;

    let all_completed = true;
    let batch_progress = [];
    let errors = 0;
    links_in_batch.forEach(function(link) {
        link.progress = (link.step_count / steps) * 100;
        link.local_url = link.guid ? `${window.host}/${link.guid}` : null;
        switch(link.status){
            case "pending":
                link.isPending = true;
                let waitMinutes = Math.round(link.queue_position * average_capture_time / celery_workers / 60);
                if (waitMinutes >= 1){
                    link.beginsIn = `about ${waitMinutes} minute${waitMinutes > 1 ? 's' : ''}.`;
                } else {
                    link.beginsIn = `less than 1 minute.`;
                }
                all_completed = false;
                batch_progress.push(link.progress);
                break;
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
                link.error_message = APIModule.stringFromNestedObject(JSON.parse(link.message)) || "Error processing request";
                errors += 1;
        }
    });
    let percent_complete = Math.round(batch_progress.reduce((a, b) => a + b, 0) / (batch_progress.length * 100) * 100)
    let message = `Batch ${percent_complete}% complete.`;
    if (errors > 0){
        message += ` <span>${errors} error${errors > 1 ? 's' : ''}.</span>`;
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

function handle_error(error){
    ErrorHandler.airbrake.notify(error);
    clearInterval(interval);
    APIModule.showError(error);
    $modal.modal("hide");
}

function show_batch(batch_id) {
    $batch_details_wrapper.removeClass("_hide");
    $batch_modal_title.text("Link Batch Details");
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
                $modal.focus();
                spinner.stop();
                $spinner.addClass("_hide");
                $batch_details.attr("aria-hidden", "true");
                // prevents tabbing to elements that are getting swapped out
                $batch_details.find('*').each(function(){$(this).attr('tabIndex', '-1')});
            }
            let folder_path = FolderTreeModule.getPathForId(batch_data.target_folder.id).join(" > ");
            let all_completed = render_batch(batch_data.capture_jobs, folder_path);
            if (all_completed) {
                clearInterval(interval);
                $batch_details.attr("aria-hidden", "false");
                // undo our special focus handling
                $batch_details.find('*').each(function(){$(this).removeAttr('tabIndex')});
            }
        }).catch(function(error){
            handle_error(error);
        });
    }
    retrieve_and_render();
    interval = setInterval(retrieve_and_render, 2000);
}

export function show_modal_with_batch(batch_id) {
    show_batch(batch_id);
    $modal.modal("show");
}

function start_batch() {
    $input.hide();
    spinner.spin($spinner[0]);
    $spinner.removeClass("_hide");
    $loading.focus();
    APIModule.request('POST', '/archives/batches/', {
        "target_folder": target_folder,
        "urls": $input_area.val().split("\n").map(s => {return s.trim()}).filter(Boolean)
    }).then(function(data) {
        show_batch(data.id);
        populate_link_batch_list();
        $(window).trigger("BatchLinkModule.batchCreated", data.links_remaining);
    }).catch(function(error){
        handle_error(error);
    });
};

function refresh_target_path_dropdown() {
    FolderSelectorHelper.makeFolderSelector($batch_target_path, target_folder);
    $start_button.prop('disabled', !Boolean(target_folder));
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
    // listen for folder changes from other UI components
    $(window)
        .on('FolderTreeModule.selectionChange', set_folder_from_trigger)
        .on('dropdown.selectionChange', set_folder_from_trigger)
        .on('createLink.toggleProgress', () => { $create_batch_wrapper.toggle() });

    // update all UI components when folder changed using the modal's dropdown
    $batch_target_path.change(function() {
        let new_folder_id = $(this).val();
        if (new_folder_id) {
            $start_button.prop('disabled', false);
            set_folder_from_dropdown(new_folder_id);
            Helpers.triggerOnWindow("dropdown.selectionChange", {
              folderId: $(this).val(),
              orgId: $(this).data('orgid')
            });
        } else {
            $start_button.prop('disabled', true);
        }
    });

    $modal
      .on('shown.bs.modal', refresh_target_path_dropdown)
      .on('hidden.bs.modal', function() {
        $input.show();
        $input_area.val("");
        $batch_details_wrapper.addClass("_hide");
        $batch_details.empty();
        spinner.stop();
        $spinner.addClass("_hide");
        $export_csv.addClass("_hide");
        $batch_progress_report.empty();
       })
      .on('hide.bs.modal', function(){
        clearInterval(interval);
        $(window).trigger("BatchLinkModule.refreshLinkList");
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
        let batch = this.dataset.batch;
        let folderPath= this.dataset.folderpath;
        let org = parseInt(this.dataset.org);
        Helpers.triggerOnWindow('batchLink.reloadTreeForFolder', {
          folderId: folderPath.split('-'),
          orgId: org
        });
        $(window).bind("folderTree.ready.batchToggle", () => {
          $input.hide();
          show_modal_with_batch(batch);
          Modals.returnFocusTo(this);
          $(window).unbind("folderTree.ready.batchToggle");
        });
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
        $batch_modal_title = $("#batch-modal-title");
        $batch_progress_report = $('#batch-progress-report');
        $batch_target_path = $('#batch-target-path');
        $create_batch = $('#create-batch');
        $create_batch_wrapper = $('#create-batch-links');
        $export_csv = $('#export-csv');
        $input = $('#batch-create-input');
        $input_area = $('#batch-create-input textarea');
        $loading = $('#loading');
        $modal = $("#batch-modal");
        $spinner = $('.spinner');
        $start_button = $('#start-batch');


        populate_link_batch_list();
        setup_handlers();
    });
}
