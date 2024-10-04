<script setup>
import { ref, watch, computed, onBeforeUnmount, onMounted } from 'vue'
import { useGlobalStore } from '../stores/globalStore'
import { getCookie } from '../../static/js/helpers/general.helpers'
import ProgressBar from './ProgressBar.vue';
import Spinner from './Spinner.vue';
import CaptureError from './CaptureError.vue'
import LinkCount from './LinkCount.vue';
import FolderSelect from './FolderSelect.vue';
import { useStorage } from '@vueuse/core'
import CreateLinkBatch from './CreateLinkBatch.vue';
import { getErrorFromNestedObject, getErrorFromResponseOrStatus, getErrorResponse, folderError, defaultError } from "../lib/errors";

const globalStore = useGlobalStore()
const batchDialogRef = ref('')
globalStore.batchDialogRef = batchDialogRef
const batchDialogOpen = () => {
    batchDialogRef.value.handleOpen();
}
const captureStatus = ref('ready')
const isReady = computed(() => ["ready", "urlError", "captureError", "uploadError"].includes(captureStatus.value))
const isLoading = computed(() => ["isValidating", "isQueued", "isCapturing"].includes(captureStatus.value))

const userLink = ref('')
const userLinkProgressBar = ref('0%')

const submitButtonText = computed(() => {
    if (isReady.value) {
        if (globalStore.selectedFolder.isPrivate) {
            return 'Create Private Perma Link'
        }
        return 'Create Perma Link'
    }
    return 'Creating your Perma Link'
})

let progressInterval;

const resetForm = () => {
    captureStatus.value = 'ready'
    globalStore.captureErrorMessage = ''
    userLink.value = ''
    userLinkProgressBar.value = '0%'
}

const isToolsReminderSuppressed = useStorage('perma_tools_reminder', false)
const handleSuppressToolsReminder = () => {
    isToolsReminderSuppressed.value = true
}

const handleArchiveRequest = async () => {
    if (!isReady.value) {
        return
    }

    globalStore.captureErrorMessage = ''
    captureStatus.value = 'isValidating'

    const formData = {
        url: userLink.value,
        human: true,
        folder: globalStore.selectedFolder.folderId
    }

    const csrf = getCookie("csrftoken")

    try {
        if (!formData.folder) {
            const errorMessage = folderError
            globalStore.captureErrorMessage = errorMessage
            throw errorMessage
        }

        const response = await fetch("/api/v1/archives/",
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

        const { guid } = await response.json()
        globalStore.captureGUID = guid
        captureStatus.value = 'isQueued'

    } catch (error) {
        handleCaptureError({ error, errorType: 'urlError' })
    }
};

const handleCaptureError = ({ error, errorType }) => {
    let errorMessage

    // Handle API-generated error messages
    if (error?.response) {
        errorMessage = getErrorFromResponseOrStatus(error.status, error.response)
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

    captureStatus.value = errorType
    globalStore.captureErrorMessage = errorMessage
}

const handleCaptureStatus = async (guid) => {
    try {
        const response = await fetch(`/api/v1/user/capture_jobs/${guid}`)

        if (!response?.ok) {
            throw new Error(response.status)
        }

        const job = await response.json()

        return {
            step_count: job.step_count,
            status: job.status,
            error: job.status === 'failed' ? job.message : ''
        }

    } catch (error) {
        // TODO: Implement maxFailedAttempts logic here
        console.log(error)
        return {
            status: 'indeterminate',
            error
        }
    }
}

const handleProgressUpdate = async () => {
    const response = await handleCaptureStatus(globalStore.captureGUID);
    const { status } = response

    if (status === 'in_progress') {
        captureStatus.value = 'isCapturing'
        userLinkProgressBar.value = `${response.step_count / 5 * 100}%`
    }

    if (status === 'completed') {
        clearInterval(progressInterval)
        resetForm()
        window.location.href = `${window.location.origin}/${globalStore.captureGUID}`
    }

    if (status === 'failed') {
        const errorMessage = response.error.length ? getErrorFromNestedObject(JSON.parse(response.error)) : defaultError

        clearInterval(progressInterval)

        captureStatus.value = 'captureError'
        globalStore.captureErrorMessage = errorMessage
    }
}

watch(() => globalStore.captureGUID, () => {
    if (globalStore.captureErrorMessage === 'testing') {
        return
    }

    handleProgressUpdate()
    progressInterval = setInterval(handleProgressUpdate, 2000);
})

onMounted(() => {
    // handle a ?url= parameter set by the bookmarklet
    const urlParam = new URLSearchParams(window.location.search).get('url');
    if (urlParam)
        userLink.value = urlParam;
});

onBeforeUnmount(() => {
    clearInterval(progressInterval)
});

</script>

<template>
    <!-- regular link creation -->
    <div id="create-item-container" class="container cont-full-bleed">
        <div class="container cont-fixed">
            <h1 class="create-title">Create a new <span class="nobreak">Perma Link</span></h1>
            <p class="create-lede">Enter any URL to preserve it forever.</p>
        </div>
        <div class="container cont-full-bleed cont-sm-fixed">
            <form class="form-priority" :class="{ '_isPrivate': globalStore.selectedFolder.isPrivate }" id="linker">
                <fieldset class="form-priority-fieldset">
                    <input v-model="userLink" id="rawUrl" name="url"
                        class="text-input select-on-click form-priority-input" type="text"
                        placeholder="Paste your URL here." />
                    <div class="wrapper">
                        <button 
                          @click.prevent="handleArchiveRequest" 
                          class="btn btn-large btn-info _active-when-valid"
                          :class="{ '_isWorking': !isReady }"
                          id="addlink" type="submit"
                        >
                            <Spinner v-if="isLoading" top="-20px" />
                            {{ submitButtonText }}
                            <ProgressBar v-if="captureStatus === 'isCapturing'"
                                :progress="userLinkProgressBar" />
                        </button>
                        <p id="create-batch-links">or <button @click.prevent="batchDialogOpen" class="c-button"
                                :class="globalStore.selectedFolder.isPrivate ? 'c-button--privateLink' : 'c-button--link'">create
                                multiple
                                links</button>
                        </p>
                    </div>
                    <LinkCount v-if="globalStore.userTypes.includes('individual')" />
                    <FolderSelect v-if="!globalStore.userTypes.includes('individual')" option="customSelect"
                        selectLabel="This Perma Link will be affiliated with" />
                </fieldset>
                <p v-if="!isToolsReminderSuppressed" id="browser-tools-message" class="u-pb-150"
                    :class="globalStore.userTypes === 'individual' && 'limit-true'">
                    To make Perma links more quickly, try our <a href="/settings/tools">browser tools</a>.
                    <button @click.prevent="handleSuppressToolsReminder" type="button"
                        class="close-browser-tools btn-link">
                        <span aria-hidden="true">&times;</span>
                        <span class="sr-only">Close</span>
                    </button>
                </p>
            </form><!--/#linker-->
        </div><!-- cont-full-bleed cont-sm-fixed -->
    </div><!-- container cont-full-bleed -->
    <CaptureError ref="uploadDialogRef" />

    <CreateLinkBatch ref="batchDialogRef" />
</template>