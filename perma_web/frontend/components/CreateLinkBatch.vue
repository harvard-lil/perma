<script setup>
import { ref, watch, computed, onBeforeUnmount } from 'vue'
import { globalStore } from '../stores/globalStore'
import { getCookie } from '../../static/js/helpers/general.helpers'
import FolderSelect from './FolderSelect.vue';
import Spinner from './Spinner.vue';
import { useFetch } from '../lib/data';
import LinkBatchDetails from './LinkBatchDetails.vue'
import Dialog from './Dialog.vue';
import { validStates, transitionalStates } from '../lib/consts.js'

const defaultDialogTitle = "Create a Link Batch"
const batchDialogTitle = ref(defaultDialogTitle)

const batchCaptureId = ref('')
const batchCSVUrl = ref('')
const batchCaptureJobs = ref([])
const batchCaptureSummary = ref('')

const showBatchDetails = computed(() => globalStore.batchCaptureStatus !== 'ready')
const userSubmittedLinks = ref('')

const readyStates = ["ready", "captureBatchError"]
const isReady = computed(() => { readyStates.includes(globalStore.batchCaptureStatus) })

let progressInterval;

const dialogRef = ref('')
const handleOpen = () => {
    dialogRef.value.handleDialogOpen();
}

const handleReset = () => {
    clearInterval(progressInterval)
    userSubmittedLinks.value = ''
    batchCaptureJobs.value = []
    batchDialogTitle.value = defaultDialogTitle
    globalStore.batchCaptureStatus = "ready"
}

const handleClose = () => {
    handleReset()
    // $(window).trigger("BatchLinkModule.refreshLinkList");
    dialogRef.value.handleDialogClose();
}

const handleClick = (e) => {
    // Close dialog if users click outside of the inner dialog container
    // For example, a user may click on the dialog's ::backdrop pseudo-element
    if (e.target.classList.contains('c-dialog')) {
        handleClose();
    }
}

// Originally called start_batch
// This is triggered on click
const handleBatchCaptureRequest = async () => {
    if (!isReady) {
        return
    }

    globalStore.updateBatchCaptureErrorMessage('')
    globalStore.updateBatchCapture('isValidating')

    //     $input.hide(); // Handled by conditional rendering
    //     spinner.spin($spinner[0]); // Handled by conditional rendering
    //     $spinner.removeClass("_hide"); // Handled by conditional rendering
    //     $loading.focus(); // Not implementing this

    const formData = {
        urls: userSubmittedLinks.value.split("\n").map(s => { return s.trim() }).filter(Boolean),
        target_folder: globalStore.selectedFolder.folderId,
        human: true,
    }

    const csrf = getCookie("csrftoken")

    try {
        const response = await fetch("/api/v1/archives/batches/",
            {
                headers: {
                    "X-CSRFToken": csrf,
                    "Content-Type": "application/json"
                },
                method: "POST",
                credentials: "same-origin",
                body: JSON.stringify(formData)
            })

        if (!response?.ok) {
            console.log('Nothing happened successfully')
            throw new Error(response.statusText) // This is a placeholder for now
        }

        const data = await response.json()
        batchCaptureId.value = data // Triggers periodic polling
        globalStore.updateBatchCapture('isQueued')



        // This is what originally happens after a POST if no error
        // show_batch(data.id); // This function is no longer needed — it simply updates UI

        // These are the UI updates show_batch tackled 
        // $batch_details_wrapper.removeClass("_hide"); // Handled with conditional rendering

        batchDialogTitle.value = "Link Batch Details"
        // $batch_modal_title.text("Link Batch Details"); // Handled above

        batchCSVUrl.value = `/api/v1/archives/batches/${data.id}/export`
        // $export_csv.attr("href", `/api/v1/archives/batches/${batch_id}/export`); // Handled above

        // Not sure about this? I thought spinner was already disabled/started, above
        //     if (!$spinner[0].childElementCount) {
        //       spinner.spin($spinner[0]);
        //       $spinner.removeClass("_hide");
        //      }

        //      let first_time = true; // Handled above

        // show_batch() originally included the retrieve_and_render function, which triggers on an interval
        // It should be triggered for the first time by setting batchCaptureId.value = data, above

        // Then these functions are also called
        // populate_link_batch_list() // handle below
        // $(window).trigger("BatchLinkModule.batchCreated", data.links_remaining); // Handled below
        const batchCreated = new CustomEvent("BatchLinkModule.batchCreated");
        window.dispatchEvent(batchCreated);

    } catch (error) {
        handleError(error)
    }
};

const handleError = (error) => {
    clearInterval(progressInterval)
    globalStore.updateBatchCapture('urlError')
    globalStore.updateBatchCaptureErrorMessage(error)
    console.log(error) // This is a placeholder
    // Fetch errorMessage
    // export function showError (jqXHR) {
    //   var message = getErrorMessage(jqXHR);
    //   Helpers.informUser(message, 'danger');
    // }

    // Show error message
    // export function informUser (message, alertClass) {
    //   /*
    //       Show user some information at top of screen.
    //       alertClass options are 'success', 'info', 'warning', 'danger'
    //    */
    //   $('.popup-alert button.close').click();
    //   alertClass = alertClass || "info";
    //   $('<div class="alert alert-'+alertClass+' alert-dismissible popup-alert" role="alert" style="display: none">' +
    //       '<button type="button" class="close" data-dismiss="alert"><span aria-hidden="true">&times;</span><span class="sr-only">Close</span></button>'+
    //       message +
    //     '</div>').prependTo('body').fadeIn('fast');
    // }
    handleClose()
}

// Originally called retrieve_and_render
const handleBatchDetailsFetch = async () => {
    console.log('batch details fetch initiated')
    const { data, error, errorMessage } = await useFetch(`/api/v1/archives/batches/${batchCaptureId.value.id}`)

    if (error) {
        return globalStore.updateBatchCaptureErrorMessage(errorMessage)
    }

    if (data.value.capture_jobs) {
        const { allJobs, progressSummary } = handleBatchFormatting(data.value.capture_jobs)
        batchCaptureJobs.value = allJobs
        batchCaptureSummary.value = progressSummary
    }
}

const handleBatchFormatting = ((captureJobs) => {
    const steps = 6
    const allJobs = captureJobs.reduce((accumulatedJobs, currentJob) => {
        let jobDetail = {
            ...currentJob,
            progress: (currentJob.step_count / steps) * 100,
            url: currentJob.guid ? `${window.location.hostname}/${currentJob.guid}` : null
        };

        if (transitionalStates.includes(currentJob.status)) {
            accumulatedJobs.completed = false;
        }

        if (!validStates.includes(jobDetail.status)) {
            accumulatedJobs.errors += 1;
        }

        return {
            ...accumulatedJobs,
            details: [...accumulatedJobs.details, jobDetail]
        };
    }, {
        details: [],
        completed: true,
        errors: 0
    });

    if (allJobs.completed) {
        clearInterval(progressInterval)
        globalStore.updateBatchCapture('isCompleted')
    }

    const totalProgress = allJobs.details.reduce((total, job) => total + job.progress, 0);
    const maxProgress = allJobs.details.length * 100;
    const percentComplete = Math.round((totalProgress / maxProgress) * 100);

    const progressSummary = allJobs.completed ? "Batch complete." : `Batch ${percentComplete}% complete.`;

    return { allJobs, progressSummary }
})

// Originally handled in show_batch
watch(batchCaptureId, () => {
    console.log('batch capture id updated')
    handleBatchDetailsFetch()
    progressInterval = setInterval(handleBatchDetailsFetch, 2000);
})

onBeforeUnmount(() => {
    clearInterval(progressInterval)
});

defineExpose({
    handleOpen
});

</script>

<template>
    <Dialog :handleClick="handleClick" :handleClose="handleClose" ref="dialogRef">
        <div class="modal-dialog modal-content">
            <div class="modal-header">
                <button type="button" class="close" data-dismiss="modal" @click.prevent="handleClose">
                    <span aria-hidden="true">&times;</span>
                    <span class="sr-only" id="loading">Close</span>
                </button>
                <h3 id="batch-modal-title" class="modal-title">{{ batchDialogTitle }}</h3>
            </div>
            <!-- <div class="spinner _hide">
                <span class="sr-only" id="loading" tabindex="-1">Loading</span>
            </div> -->
            <!-- // Turns into the below -->
            <template v-if="globalStore.batchCaptureStatus === 'isValidating'">
                <span class="sr-only">Loading</span>
                <Spinner isDisabled />
            </template>
            <div class="modal-body">

                <div id="batch-create-input" v-if="globalStore.batchCaptureStatus === 'ready'">
                    <div class="form-group">
                        <FolderSelect />
                    </div>
                    <div class="form-group">
                        <textarea v-model="userSubmittedLinks" aria-label="Paste your URLs here (one URL per line)"
                            placeholder="Paste your URLs here (one URL per line)"></textarea>
                    </div>
                    <div class="form-buttons">
                        <button class="btn" @click.prevent="handleBatchCaptureRequest">Create Links</button>
                        <button class="btn cancel" @click.prevent="handleClose">Cancel</button>
                    </div>
                </div>

                <LinkBatchDetails v-if="showBatchDetails" :handleClose :batchCaptureJobs :batchCaptureSummary
                    :showBatchCSVUrl="globalStore.batchCaptureStatus === 'isCompleted'" :batchCSVUrl
                    :targetFolder="globalStore.selectedFolder.path.join(' > ')" />
            </div>
        </div>
    </Dialog>
</template>