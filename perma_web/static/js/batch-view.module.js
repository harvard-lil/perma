var APIModule = require('./helpers/api.module.js');
var FolderTreeModule = require('./folder-tree.module.js');

var $batch_details, $saved_path;

var render_batch = function(links_in_batch, folder_id) {
    $batch_details.text(JSON.stringify(links_in_batch));
};

var get_batch_info = function(batch_id) {
    return APIModule.request('GET', '/batches/' + parseInt(batch_id))
        .then(function(batch_data) {
            var cleaned_batch_data = [];
            if (Array.isArray(batch_data.capture_jobs)) {
                cleaned_batch_data = batch_data.capture_jobs.map(function(capture_job) {
                    return {
                        "url": capture_job.url,
                        "title": capture_job.title,
                        "guid": capture_job.guid,
                        "status": capture_job.status,
                        "step_count": capture_job.step_count
                    };
                });
            }
            return cleaned_batch_data;
        }).fail(function(response) {
            // deal with failure
        });
};

export function show_batch(batch_id, folder_id) {
    var folder_path = FolderTreeModule.getPathForId(folder_id);
    $saved_path.html(folder_path.join(" &gt; "));
    $batch_details.empty();
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
    });
}
