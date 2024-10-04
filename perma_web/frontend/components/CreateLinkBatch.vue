<script setup>
import { ref, watch, computed, onBeforeUnmount } from 'vue'
import { useGlobalStore } from '../stores/globalStore'
import { getCookie } from '../../static/js/helpers/general.helpers'
import FolderSelect from './FolderSelect.vue';
import Spinner from './Spinner.vue';
import {fetchDataOrError} from '../lib/data';
import LinkBatchDetails from './LinkBatchDetails.vue'
import Dialog from './Dialog.vue';
import {
  folderError,
  getErrorFromResponseStatus,
  missingUrlError,
  getErrorResponse,
  getErrorFromNestedObject
} from '../lib/errors';
import { useToast } from '../lib/notifications';
import { defaultError } from '../lib/errors';
import {transitionalStates, validStates, showDevPlayground} from "../lib/consts";

const globalStore = useGlobalStore()

const defaultDialogTitle = "Create a Link Batch"
const batchDialogTitle = ref(defaultDialogTitle)

const batchCaptureId = ref('')
const batchCSVUrl = ref('')
const batchCaptureJobs = ref([])
const batchCaptureSummary = ref('')
const batchCaptureStatus = ref('ready')
const targetFolderName = ref('')

const showBatchDetails = computed(() => batchCaptureStatus.value !== 'ready' && batchCaptureStatus.value !== 'isValidating')
const userSubmittedLinks = ref('')

const readyStates = ["ready", "urlError", "folderSelectionError"]
const isReady = computed(() => { readyStates.includes(batchCaptureStatus.value) })

let progressInterval;

const dialogRef = ref('')
const handleOpen = () => {
    dialogRef.value.handleDialogOpen();
}

const showBatchHistory = (id) => {
  /* called from LinkBatchHistory.vue */
  batchCaptureId.value = id
  batchCaptureStatus.value = 'isValidating'
  batchCSVUrl.value = `/api/v1/archives/batches/${id}/export`
  handleBatchDetailsFetch()
  dialogRef.value.handleDialogOpen()
}

const handleReset = () => {
    clearInterval(progressInterval)
    userSubmittedLinks.value = ''
    batchCaptureJobs.value = []
    batchDialogTitle.value = defaultDialogTitle
    batchCaptureStatus.value = "ready"
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

    batchCaptureStatus.value = 'isValidating'

    const formData = {
        urls: userSubmittedLinks.value.split("\n").map(s => { return s.trim() }).filter(Boolean),
        target_folder: globalStore.selectedFolder.folderId,
        human: true,
    }

    const csrf = getCookie("csrftoken")

    try {
        if (!formData.urls.length) {
            batchCaptureStatus.value = 'urlError'
            throw missingUrlError
        }

        if (!formData.target_folder) {
            batchCaptureStatus.value = 'folderSelectionError'
            throw folderError
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
            throw await getErrorResponse(response)
        }

        const data = await response.json()

        batchCaptureId.value = data.id // Triggers periodic polling
        batchCaptureStatus.value = 'isQueued'

        batchDialogTitle.value = "Link Batch Details"
        batchCSVUrl.value = `/api/v1/archives/batches/${data.id}/export`

        // show new links in links list
        if (showDevPlayground) {
            globalStore.refreshLinkList.value();
        } else {
            const batchCreated = new CustomEvent("BatchLinkModule.batchCreated");
            window.dispatchEvent(batchCreated);
        }

    } catch (error) {
        handleBatchError({ error, errorType: 'urlError' })
    }
};

const handleBatchError = ({ error, errorType }) => {
    clearInterval(progressInterval)
    batchCaptureStatus.value = errorType

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
    handleClose()
}

const handleBatchDetailsFetch = async () => {

  const { data, error } = await fetchDataOrError(`/archives/batches/${batchCaptureId.value}`);

  if (error) {
    handleBatchError({ error, errorType: 'urlError' })
    return
  }

  targetFolderName.value = data.target_folder.name;

  const captureJobs = data.capture_jobs;

  const steps = 6;
  const allJobs = captureJobs.reduce((accumulatedJobs, currentJob) => {
    const includesError = !validStates.includes(currentJob.status);
    const isCapturing = transitionalStates.includes(currentJob.status);

    let jobDetail = {
      ...currentJob,
      message: includesError ? getErrorFromNestedObject(JSON.parse(currentJob.message)) : '',
      progress: (currentJob.step_count / steps) * 100,
      url: `${window.location.hostname}/${currentJob.guid}`
    };

    if (isCapturing) {
      accumulatedJobs.completed = false;
    }

    if (includesError) {
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

  const totalProgress = allJobs.details.reduce((total, job) => total + job.progress, 0);
  const maxProgress = allJobs.details.length * 100;
  const percentComplete = Math.round((totalProgress / maxProgress) * 100);

  const progressSummary = allJobs.completed ? "Batch complete." : `Batch ${percentComplete}% complete.`;

  if (allJobs) {
    batchCaptureJobs.value = allJobs;
    batchCaptureSummary.value = progressSummary;
  }

  if (allJobs.completed) {
    clearInterval(progressInterval);
    batchCaptureStatus.value = 'isCompleted';

    // show new links in links list
    if (showDevPlayground) {
      globalStore.refreshLinkList.value();
    } else {
      const batchCreated = new CustomEvent("BatchLinkModule.batchCreated");
      window.dispatchEvent(batchCreated);
    }
  }
};

const { addToast } = useToast();

const toggleToast = (errorMessage) => {
    addToast(errorMessage, 'error');
}

watch(batchCaptureId, () => {
  handleBatchDetailsFetch()
  if (batchCaptureStatus.value === 'isQueued') {
    progressInterval = setInterval(handleBatchDetailsFetch, 2000);
  }
})

onBeforeUnmount(() => {
    clearInterval(progressInterval)
});

defineExpose({
  handleOpen,
  showBatchHistory,
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
            <template v-if="batchCaptureStatus === 'isValidating'">
                <span class="sr-only">Loading</span>
                <Spinner top="32px" length="10" color="#222222" classList="spinner" />
            </template>
            <div class="modal-body">

                <div id="batch-create-input" v-if="batchCaptureStatus === 'ready'">
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
                    :showBatchCSVUrl="batchCaptureStatus === 'isCompleted'" :batchCSVUrl
                    :targetFolder="targetFolderName" />
            </div>
        </div>
    </Dialog>
</template>