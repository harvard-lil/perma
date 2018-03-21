var Papa = require('papaparse');
var Spinner = require('spin.js');

var APIModule = require('./helpers/api.module.js');
var FolderTreeModule = require('./folder-tree.module.js');
var ProgressBarHelper = require('./helpers/progress-bar.helper.js');
var HandlebarsHelpers = require('./helpers/handlebars.helpers.js');

var $batch_details, $saved_path, $export_csv;

var render_batch = function(links_in_batch, folder_id) {
    $batch_details.empty();
    var all_finished = true;
    links_in_batch.forEach(function(link) {
        link.progress = (link.step_count / 5) * 100;
        link.isProcessing = ((link.status === "pending") || (link.status === "in_progress"));
        if (link.isProcessing) {
            all_finished = false;
        }
        link.isComplete = (link.status === "completed");
        link.isError = (!link.isProcessing && !link.isComplete);
        if (link.isError) {
            // Right now, the CaptureJob doesn't save the Serializer
            // error so we can only save the status, and we always
            // save "invalid" on an error.  Thus, this will always be
            // true.
            if (link.status === "invalid") {
                link.error_message = "error";
            }
        }
        link.local_url = window.host + "/" + link.guid;
        var template = HandlebarsHelpers.renderTemplate('#batch-link-row', {"link": link});
        $batch_details.append(jQuery.parseHTML(template));
    });
    if (all_finished) {
        var export_data = links_in_batch.map(function(link) {
            var to_export = {
                "url": link.url
            };
            if (link.status === "completed") {
                to_export["status"] = "success"
                to_export["title"] = link.title;
                to_export["perma_link"] = "http://" + window.host + "/" + link.guid;
            } else {
                to_export["status"] = "error"
                to_export["title"] = ""
                to_export["perma_link"] = ""
            }
            return to_export;
        });
        var csv = Papa.unparse(export_data);
        $export_csv.attr("href", "data:text/csv;charset=utf-8," + encodeURI(csv));
        $export_csv.attr("download", "perma.csv");
        $export_csv.show();
    }
};

var get_batch_info = function(batch_id) {
    return APIModule.request('GET', '/archives/batches/' + parseInt(batch_id))
        .then(function(batch_data) {
            var cleaned_batch_data = [];
            if (Array.isArray(batch_data.capture_jobs)) {
                cleaned_batch_data = batch_data.capture_jobs.map(function(capture_job) {
                    return {
                        "url": capture_job.submitted_url,
                        "title": capture_job.title,
                        "guid": capture_job.guid,
                        "status": capture_job.status,
                        "step_count": capture_job.step_count
                    };
                });
            }
            return cleaned_batch_data;
        });
};

export function show_batch(batch_id, folder_id) {
    var folder_path = FolderTreeModule.getPathForId(folder_id);
    $saved_path.html(folder_path.join(" &gt; "));
    var spinner = new Spinner({lines: 15, length: 10, width: 2, radius: 9, corners: 0, color: '#222222', trail: 50, top: '20px'}).spin($batch_details[0]);
    var interval = setInterval(function() {
        get_batch_info(batch_id).then(function(links_in_batch) {
            render_batch(links_in_batch, folder_id);
            var all_completed = true;
            for (var i = 0; i < links_in_batch.length; i++) {
                var link = links_in_batch[i];
                if ((link.status === "pending") || (link.status === "in_progress")) {
                    all_completed = false;
                    break;
                }
            }
            if (all_completed) {
                clearInterval(interval);
            }
        });
    }, 2000);
}

export function init() {
    $(function() {
        $batch_details = $('#batch-details');
        $saved_path = $('#batch-saved-path');
        $export_csv = $('#export-csv');
    });
}
