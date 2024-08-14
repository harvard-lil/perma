<script setup>
import { ref, watch, computed, onBeforeUnmount } from 'vue'
import { globalStore } from '../stores/globalStore'
import { getCookie } from '../../static/js/helpers/general.helpers'
import FolderSelect from './FolderSelect.vue';
import Spinner from './Spinner.vue';
import { useBatchDetailsFetch } from '../lib/data';
import LinkBatchDetails from './LinkBatchDetails.vue'
import Dialog from './Dialog.vue';
import { folderError, getErrorFromResponseStatus, missingUrlError, getErrorResponse } from '../lib/errors';
import { useToast } from '../lib/notifications';
import { defaultError } from '../lib/errors';

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
        if (!formData.urls.length) {
            globalStore.updateBatchCapture('urlError')
            const errorMessage = missingUrlError
            globalStore.updateBatchCaptureErrorMessage(errorMessage)
            throw errorMessage
        }

        if (!formData.target_folder) {
            globalStore.updateBatchCapture('folderSelectionError')
            const errorMessage = folderError
            globalStore.updateBatchCaptureErrorMessage(errorMessage)
            throw errorMessage
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
            const errorResponse = await getErrorResponse(response)
            throw errorResponse
        }

        const data = await response.json()

        batchCaptureId.value = data // Triggers periodic polling
        globalStore.updateBatchCapture('isQueued')

        batchDialogTitle.value = "Link Batch Details"
        batchCSVUrl.value = `/api/v1/archives/batches/${data.id}/export`

        const batchCreated = new CustomEvent("BatchLinkModule.batchCreated");
        window.dispatchEvent(batchCreated);

    } catch (error) {
        handleBatchError({ error, errorType: 'urlError' })
    }
};

const handleBatchError = ({ error, errorType }) => {
    clearInterval(progressInterval)
    globalStore.updateBatchCapture(errorType)

    let errorMessage

    // Handle API-generated error messages
    if (error?.response) {
        errorMessage = getErrorFromResponseStatus(error.status, error.response)
    }

    else if (error?.status) {
        errorMessage = `Error: ${error.status}`
    }

    // Handle frontend-generated error messages
    else if (error.length) {
        errorMessage = error
    }

    // Handle uncaught errors
    else {
        errorMessage = defaultError
    }

    toggleToast(errorMessage)
    globalStore.updateBatchCaptureErrorMessage(errorMessage)
    handleClose()
}

const handleBatchDetailsFetch = async () => {
    const batchDetails = await useBatchDetailsFetch(batchCaptureId.value.id)

    if (batchDetails?.allJobs && batchDetails?.progressSummary) {
        batchCaptureJobs.value = batchDetails.allJobs
        batchCaptureSummary.value = batchDetails.progressSummary
    }

    if (batchDetails?.allJobs?.completed) {
        clearInterval(progressInterval)
        globalStore.updateBatchCapture('isCompleted')

        const batchCompleted = new CustomEvent("BatchLinkModule.batchCompleted");
        window.dispatchEvent(batchCompleted);
    }
}

const { addToast } = useToast();

const toggleToast = (errorMessage) => {
    addToast(errorMessage, 'error');
}

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