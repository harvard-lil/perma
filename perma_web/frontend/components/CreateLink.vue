<script setup>
import { ref, watch, onBeforeUnmount } from 'vue'
import { globalStore } from '../stores/globalStore'
import { getCookie } from '../../static/js/helpers/general.helpers'
// import * as spinner from 'spin.js'

const userLink = ref('')
const userLinkGUID = ref('')
const userLinkProgressBar = ref(0)
let progressInterval;

const handleArchiveRequest = async () => {
    globalStore.updateCaptureErrorMessage('')
    globalStore.updateCapture('isValidating')

    const formData = {
        url: userLink.value,
        human: true
    }

    const csrf = getCookie("csrftoken")

    try {
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
        globalStore.updateCapture('isQueuing')

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
            status: jobStatus.status
        }

    } catch (error) {
        clearInterval(progressInterval);
        globalStore.updateCapture('captureError')
        globalStore.updateCaptureErrorMessage(error)
    }
}

const handleProgressUpdate = async () => {
    const { step_count, status } = await handleCaptureStatus(userLinkGUID.value);

    if (status === 'in_progress') {
        globalStore.updateCapture('isUploading')
        userLinkProgressBar.value = step_count / 5 * 100
    }

    if (status === 'completed') {
        clearInterval(progressInterval)
        globalStore.updateCapture('success')
        window.location.href = `${window.location.origin}/${userLinkGUID.value}`
    }
}

watch(userLinkGUID, async () => {
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
            <h2>Capture status: {{ globalStore.captureStatus }}</h2> <!-- debug only -->
            <h2 v-if="globalStore.captureStatus === 'isUploading'">Capture progress: {{ userLinkProgressBar }}</h2>
            <!-- debug only -->
        </div>
        <div class="container cont-full-bleed cont-sm-fixed">
            <form class="form-priority" id="linker">
                <fieldset class="form-priority-fieldset">
                    <input v-model="userLink" id="rawUrl" name="url"
                        class="text-input select-on-click form-priority-input" type="text"
                        placeholder="Paste your URL here." data-placement="bottom"
                        data-content="To save a link, enter its URL and click the <strong>Create Perma Link</strong> button. To see the links you've saved, click <strong>Library</strong> in the menu to the left."
                        data-original-title="Start building your library" data-html="true" data-trigger="manual" />
                    <div class="wrapper">
                        <button @click.prevent="handleArchiveRequest" class="btn btn-large btn-info _active-when-valid"
                            id="addlink" type="submit">
                            Create Perma Link
                            <!-- <div v-if="globalStore.captureStatus === 'isQueuing'" id="capture-status">Creating your
                                Perma Link</div> -->
                        </button>
                    </div>
                </fieldset>
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
</template>
