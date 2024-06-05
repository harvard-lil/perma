<script setup>
import { ref, watch, computed, onBeforeUnmount } from 'vue'
import { globalStore } from '../stores/globalStore'
import { getCookie } from '../../static/js/helpers/general.helpers'
import ProgressBar from './ProgressBar.vue';
import Spinner from './Spinner.vue';
import LinkCount from './LinkCount.vue';
import FolderSelect from './FolderSelect.vue';
import { useStorage } from '@vueuse/core'
import { useToast } from '../lib/notifications';
import CreateLinkBatch from './CreateLinkBatch.vue';

const batchDialogRef = ref('')

const batchDialogOpen = () => {
    batchDialogRef.value.handleOpen();
}

const userLink = ref('')
const userLinkGUID = ref('')
const userLinkProgressBar = ref('0%')

const readyStates = ["ready", "urlError", "captureError"]
const isReady = computed(() => { readyStates.includes(globalStore.captureStatus) })

const loadingStates = ["isValidating", "isQueued", "isCapturing"]
const isLoading = computed(() => { return loadingStates.includes(globalStore.captureStatus) })

const submitButtonText = computed(() => {
    if (readyStates.includes(globalStore.captureStatus) && globalStore.selectedFolder.isPrivate) {
        return 'Create Private Perma Link'
    }
    else if (readyStates.includes(globalStore.captureStatus)) {
        return 'Create Perma Link'
    }
    return 'Creating your Perma Link'
})

let progressInterval;

const isToolsReminderSuppressed = useStorage('perma_tools_reminder', false)
const handleSuppressToolsReminder = () => {
    isToolsReminderSuppressed.value = true
}

const handleArchiveRequest = async () => {
    if (!isReady) {
        return
    }

    globalStore.updateCaptureErrorMessage('')
    globalStore.updateCapture('isValidating')

    const formData = {
        url: userLink.value,
        human: true,
        folder: globalStore.selectedFolder.folderId
    }

    const csrf = getCookie("csrftoken")

    try {
        if (!formData.folder) {
            // These are placeholders
            const errorMessage = 'Missing folder selection'
            globalStore.updateCaptureErrorMessage(errorMessage)
            throw new Error(errorMessage)
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
            throw new Error(response.statusText) // We will handle this more in-depth later
        }

        const { guid } = await response.json() // Needed to poll Perma about the capture status of a link
        userLinkGUID.value = guid
        globalStore.updateCapture('isQueued')

    } catch (error) {
        globalStore.updateCapture('urlError')
        globalStore.updateCaptureErrorMessage(error)
    }
};

const handleCaptureStatus = async (guid) => {
    try {
        const response = await fetch(`/api/v1/user/capture_jobs/${guid}`)

        if (!response?.ok) {
            throw new Error(response.statusText) // We will handle this more in-depth later
        }

        const jobStatus = await response.json()

        return {
            step_count: jobStatus.step_count,
            status: jobStatus.status,
            error: jobStatus.status === 'failed' ? JSON.parse(jobStatus.message).error[0] : '' // We will handle this more in-depth later, too
        }

    } catch (error) {
        clearInterval(progressInterval);
        globalStore.updateCapture('captureError')
        globalStore.updateCaptureErrorMessage(error)
    }
}

const handleProgressUpdate = async () => {
    const { step_count, status, error } = await handleCaptureStatus(userLinkGUID.value);

    if (status === 'in_progress') {
        globalStore.updateCapture('isCapturing')
        userLinkProgressBar.value = `${step_count / 5 * 100}%`
    }

    if (status === 'completed') {
        clearInterval(progressInterval)
        globalStore.updateCapture('success')
        window.location.href = `${window.location.origin}/${userLinkGUID.value}`
    }

    if (status === 'failed') {
        clearInterval(progressInterval)
        globalStore.updateCapture('captureError')
        globalStore.updateCaptureErrorMessage(error)
    }
}

const { addToast } = useToast();

const toggleToast = () => {
    const date = Date.now();
    addToast(`Toast notification ${date}`, 'success');
}

watch(userLinkGUID, () => {
    handleProgressUpdate()
    progressInterval = setInterval(handleProgressUpdate, 2000);
})

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
                        <button @click.prevent="handleArchiveRequest" class="btn btn-large btn-info _active-when-valid"
                            :class="{
                '_isWorking': !readyStates.includes(globalStore.captureStatus),
            }
                " id="addlink" type="submit">
                            <Spinner v-if="isLoading" top="-20px" />
                            {{ submitButtonText }}
                            <ProgressBar v-if="globalStore.captureStatus === 'isCapturing'"
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

    <div class="create-errors container cont-fixed">
        <div v-if="globalStore.captureErrorMessage" id="error-container">
            <p class="message-large">{{ globalStore.captureErrorMessage }}</p>
            <p class="message">We’re unable to create your Perma Link.</p>
            <p>You can <button id="upload-form-button">upload your own archive</button> or <a href="/contact">contact us
                    about this error.</a></p>
        </div>
    </div>

    <CreateLinkBatch ref="batchDialogRef" />
</template>