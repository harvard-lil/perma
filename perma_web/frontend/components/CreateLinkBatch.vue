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

const showBatchDetails = computed(() => globalStore.batchCaptureStatus !== 'ready' && globalStore.batchCaptureStatus !== 'isValidating')
const userSubmittedLinks = ref('')

const readyStates = ["ready", "urlError", "folderSelectionError"]
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
    dialogRef.value.handleDialogClose();
}

const handleClick = (e) => {
    // Close dialog if users click outside of the inner dialog container
    // For example, clicks on the dialog's ::backdrop pseudo-element will trigger this
    if (e.target.classList.contains('c-dialog')) {
        handleClose();
    }
}

const handleBatchCaptureRequest = async () => {
    if (!isReady) {
        return
    }

    globalStore.updateBatchCaptureErrorMessage('')
    globalStore.updateBatchCapture('isValidating')

    const formData = {
        urls: userSubmittedLinks.value.split("\n").map(s => { return s.trim() }).filter(Boolean),
        target_folder: globalStore.selectedFolder.folderId,
        human: true,
    }

    const csrf = getCookie("csrftoken")

    try {
        if (!formData.target_folder) {
            // These are placeholders
            globalStore.updateBatchCapture('folderSelectionError')
            const errorMessage = 'Missing folder selection'
            globalStore.updateBatchCaptureErrorMessage(errorMessage)
            throw new Error(errorMessage)
        }

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
            throw new Error(response.statusText) // This is a placeholder for now
        }

        const data = await response.json()
        batchCaptureId.value = data // Triggers periodic polling
        globalStore.updateBatchCapture('isQueued')

        batchDialogTitle.value = "Link Batch Details"
        batchCSVUrl.value = `/api/v1/archives/batches/${data.id}/export`

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
    handleClose()
}

const handleBatchDetailsFetch = async () => {
    const { data, error, errorMessage } = await useFetch(`/api/v1/archives/batches/${batchCaptureId.value.id}`)

    if (error || !data.value.capture_jobs) {
        globalStore.updateBatchCapture('batchDetailsError')
        globalStore.updateBatchCaptureErrorMessage(errorMessage)
    }

    const { allJobs, progressSummary } = handleBatchFormatting(data.value.capture_jobs)
    batchCaptureJobs.value = allJobs
    batchCaptureSummary.value = progressSummary
}

const handleBatchFormatting = ((captureJobs) => {
    const steps = 6
    const allJobs = captureJobs.reduce((accumulatedJobs, currentJob) => {
        let jobDetail = {
            ...currentJob,
            progress: (currentJob.step_count / steps) * 100,
            url: `${window.location.hostname}/${currentJob.guid}`
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

watch(batchCaptureId, () => {
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
            <template v-if="globalStore.batchCaptureStatus === 'isValidating'">
                <span class="sr-only">Loading</span>
                <Spinner top="32px" length="10" color="#222222" classList="spinner" />
            </template>
            <div class="modal-body">

                <div id="batch-create-input" v-if="globalStore.batchCaptureStatus === 'ready'">
                    <div class="form-group">
                        <FolderSelect selectLabel="These Perma Links will be affiliated with" />
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