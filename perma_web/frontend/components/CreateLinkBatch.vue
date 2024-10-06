<script setup>
import { ref, watch, computed, onMounted, onBeforeUnmount, getCurrentInstance } from 'vue'
import { useGlobalStore } from '../stores/globalStore'
import FolderSelect from './FolderSelect.vue';
import Spinner from './Spinner.vue';
import { fetchDataOrError } from '../lib/data';
import LinkBatchDetails from './LinkBatchDetails.vue'
import Dialog from './Dialog.vue';
import {
  folderError,
  missingUrlError,
  getErrorFromNestedObject
} from '../lib/errors';
import { useToast } from '../lib/notifications';
import { transitionalStates, validStates, showDevPlayground } from "../lib/consts";

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
    if (!["ready", "urlError", "folderSelectionError"].includes(batchCaptureStatus.value)) {
        return
    }

    batchCaptureStatus.value = 'isValidating'

    const formData = {
        urls: userSubmittedLinks.value.split("\n").map(s => { return s.trim() }).filter(Boolean),
        target_folder: globalStore.selectedFolder.folderId,
        human: true,
    }

    if (!formData.urls.length) {
        handleBatchError({ error: missingUrlError, errorType: 'urlError' })
        return;
    }
    if (!formData.target_folder) {
        handleBatchError({ error: folderError, errorType: 'folderSelectionError' })
        return;
    }

    const { data, error } = await fetchDataOrError("/archives/batches/", {
        method: "POST",
        data: formData
    });

    if (error) {
        handleBatchError({ error, errorType: 'urlError' })
        return;
    }

    batchCaptureId.value = data.id
    batchCaptureStatus.value = 'isQueued'
    batchDialogTitle.value = "Link Batch Details"
    batchCSVUrl.value = `/api/v1/archives/batches/${data.id}/export`

    // poll for updates
    handleBatchDetailsFetch()
    progressInterval = setInterval(handleBatchDetailsFetch, 2000)

    // show new links in links list
    if (showDevPlayground) {
        globalStore.components.linkList.fetchLinks();
    } else {
        const batchCreated = new CustomEvent("BatchLinkModule.batchCreated");
        window.dispatchEvent(batchCreated);
    }
};

const handleBatchError = ({ error, errorType }) => {
    clearInterval(progressInterval)
    batchCaptureStatus.value = errorType

    toggleToast(error)
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
      progress: !isCapturing ? 100 : (currentJob.step_count / steps) * 100,
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
      globalStore.components.linkList.fetchLinks();
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

onMounted(() => {
  globalStore.components.batchDialog = getCurrentInstance().exposed
})

onBeforeUnmount(() => {
    globalStore.components.batchDialog = null
    clearInterval(progressInterval)
});

defineExpose({
  handleOpen,
  showBatchHistory,
});

</script>

<template>
    <Dialog :handleClick="handleClick" :handleClose="handleClose" ref="dialogRef">
        <div class="modal-dialog modal-content modal-lg">
            <div class="modal-header">
                <button type="button" class="close" data-dismiss="modal" @click.prevent="handleClose">
                    <span aria-hidden="true">&times;</span>
                    <span class="sr-only" id="loading">Close</span>
                </button>
                <h3 id="batch-modal-title" class="modal-title">{{ batchDialogTitle }}</h3>
            </div>
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

                <div v-if="batchCaptureStatus === 'isValidating'" style="height: 200px;">
                    <Spinner />
                </div>

                <LinkBatchDetails v-if="showBatchDetails" :handleClose :batchCaptureJobs :batchCaptureSummary
                    :showBatchCSVUrl="batchCaptureStatus === 'isCompleted'" :batchCSVUrl
                    :targetFolder="targetFolderName" />
            </div>
        </div>
    </Dialog>
</template>