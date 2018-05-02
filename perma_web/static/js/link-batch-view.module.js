let Papa = require('papaparse');
let Spinner = require('spin.js');

let APIModule = require('./helpers/api.module.js');
let FolderTreeModule = require('./folder-tree.module.js');
let ProgressBarHelper = require('./helpers/progress-bar.helper.js');
let HandlebarsHelpers = require('./helpers/handlebars.helpers.js');

let $batch_details, $modal, $export_csv;


function render_batch(links_in_batch, folder_path) {
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
    $batch_details.empty();
    let spinner = new Spinner({lines: 15, length: 10, width: 2, radius: 9, corners: 0, color: '#222222', trail: 50, top: '20px'}).spin($batch_details[0]);
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

export function init() {
    $(function() {
        let $batch_history = $('#batch-history');
        $modal = $("#batch-view-modal");
        $batch_details = $('#batch-details');
        $export_csv = $('#export-csv');
        $batch_history.delegate('a', 'click', function(e) {
            e.preventDefault();
            show_modal_with_batch(this.dataset.batch, parseInt(this.dataset.folder));
        });
    });
}
