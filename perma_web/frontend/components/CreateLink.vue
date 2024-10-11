<script setup>
import { ref, computed, onBeforeUnmount, onMounted, getCurrentInstance } from 'vue'
import { useGlobalStore } from '../stores/globalStore'
import ProgressBar from './ProgressBar.vue';
import Spinner from './Spinner.vue';
import CaptureError from './CaptureError.vue'
import LinkCount from './LinkCount.vue';
import FolderSelect from './FolderSelect.vue';
import { useStorage } from '@vueuse/core'
import CreateLinkBatch from './CreateLinkBatch.vue';
import { getErrorFromNestedObject, getErrorFromStatusOrData, folderError, defaultError } from "../lib/errors";
import { fetchDataOrError } from '../lib/data';

const globalStore = useGlobalStore()
const captureStatus = ref('ready')
const captureErrorMessage = ref('')
const captureGUID = ref('')
const isReady = computed(() => ["ready", "urlError", "captureError", "uploadError"].includes(captureStatus.value))
const batchDialogRef = ref('')
const userLink = ref('')
const userLinkProgressBar = ref('0%')

let progressInterval;

const resetForm = () => {
    captureStatus.value = 'ready'
    captureErrorMessage.value = ''
    userLink.value = ''
    userLinkProgressBar.value = '0%'
    clearInterval(progressInterval)
}

const isToolsReminderSuppressed = useStorage('perma_tools_reminder', false)
const handleSuppressToolsReminder = () => {
    isToolsReminderSuppressed.value = true
}

const handleArchiveRequest = async () => {
    if (!isReady.value) {
        return
    }

    // prep and validate form
    captureErrorMessage.value = ''
    captureStatus.value = 'isValidating'

    const formData = {
        url: userLink.value,
        human: true,
        folder: globalStore.selectedFolder.folderId
    }

    if (!formData.folder) {
        captureErrorMessage.value = folderError
        captureStatus.value = 'urlError'
        return
    }

    // send request
    const { data, error, response } = await fetchDataOrError("/archives/", {
        method: "POST",
        data: formData,
    })

    // handle errors
    if (error) {
        let errorMessage
        // Handle API-generated error messages
        errorMessage = getErrorFromStatusOrData(response.status, data)
        captureStatus.value = 'urlError'
        captureErrorMessage.value = errorMessage
        return
    }

    // success
    captureGUID.value = data.guid
    captureStatus.value = 'isQueued'
    handleProgressUpdate()
    progressInterval = setInterval(handleProgressUpdate, 2000)
}

const handleCaptureStatus = async (guid) => {
    const { data, error, response } = await fetchDataOrError(`/user/capture_jobs/${guid}`)

    if (error) {
        // TODO: Implement maxFailedAttempts logic here
        console.log(error)
        return {
            status: 'indeterminate',
            error
        }
    }

    return {
        step_count: data.step_count,
        status: data.status,
        error: data.status === 'failed' ? data.message : ''
    }
}

const handleProgressUpdate = async () => {
    const response = await handleCaptureStatus(captureGUID.value);
    const { status } = response

    if (status === 'in_progress') {
        captureStatus.value = 'isCapturing'
        userLinkProgressBar.value = `${Math.round(response.step_count / 5 * 100)}%`
    }

    if (status === 'completed') {
        resetForm()
        window.location.href = `${window.location.origin}/${captureGUID.value}`
    }

    if (status === 'failed') {
        const errorMessage = response.error.length ? getErrorFromNestedObject(JSON.parse(response.error)) : defaultError

        clearInterval(progressInterval)

        captureStatus.value = 'captureError'
        captureErrorMessage.value = errorMessage
    }
}

onMounted(() => {
    globalStore.components.createLink = getCurrentInstance().exposed

    // handle a ?url= parameter set by the bookmarklet
    const urlParam = new URLSearchParams(window.location.search).get('url');
    if (urlParam)
        userLink.value = urlParam;
});

onBeforeUnmount(() => {
    globalStore.components.createLink = null
    clearInterval(progressInterval)
});

defineExpose({
  resetForm,
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
                    <div class="input-bar">
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
                                <Spinner v-if="captureStatus === 'isValidating' || captureStatus === 'isQueued'" />
                                <ProgressBar v-if="captureStatus === 'isCapturing'" :progress="userLinkProgressBar" style="height: 32px"/>
                                {{ isReady ? "Create" : "Creating" }}
                                {{ globalStore.selectedFolder.isPrivate ? "Private" : "" }}
                                Perma Link
                            </button>
                            <p id="create-batch-links" v-if="isReady">
                                or 
                                <button 
                                    @click.prevent="batchDialogRef.handleOpen" 
                                    class="c-button"
                                    :class="globalStore.selectedFolder.isPrivate ? 'c-button--privateLink' : 'c-button--link'"
                                >
                                    create multiple links
                                </button>
                            </p>
                        </div>
                    </div>
                    <CaptureError
                      v-if="captureErrorMessage"
                      :errorMessage="captureErrorMessage"
                      :captureGUID="captureGUID"
                    />
                    <LinkCount v-if="globalStore.userTypes.includes('individual')" />
                    <div v-if="!globalStore.userTypes.includes('individual')" style="display: flex; align-items: center;">
                        <span class="label-affil" style="flex-shrink: 0; margin-right: 14px;">This Perma Link will be affiliated with</span>
                        <FolderSelect style="flex-grow: 1" />
                    </div>
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

    <CreateLinkBatch ref="batchDialogRef" />
</template>