<script setup>
import { ref } from 'vue'
const userLink = ref('')
import { globalStore } from '../stores/globalStore'
import { getCookie } from '../../static/js/helpers/general.helpers'

const handleCreateLink = async () => {
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
            throw new Error(response.statusText)
        }

    } catch (error) {
        globalStore.updateCapture('urlError')
        globalStore.updateCaptureErrorMessage(error)
    }
};
</script>

<template>
    <!-- regular link creation -->
    <div id="create-item-container" class="container cont-full-bleed">
        <div class="container cont-fixed">
            <h2>Capture status: {{ globalStore.captureStatus }}</h2>
        </div>
        <div class="container cont-full-bleed cont-sm-fixed">
            <form class="form-priority" id="linker" method="post">
                <fieldset class="form-priority-fieldset">
                    <input v-model="userLink" id="rawUrl" name="url"
                        class="text-input select-on-click form-priority-input" type="text"
                        placeholder="Paste your URL here." data-placement="bottom"
                        data-content="To save a link, enter its URL and click the <strong>Create Perma Link</strong> button. To see the links you've saved, click <strong>Library</strong> in the menu to the left."
                        data-original-title="Start building your library" data-html="true" data-trigger="manual" />
                    <div class="wrapper">
                        <button @click.prevent="handleCreateLink" class="btn btn-large btn-info _active-when-valid"
                            id="addlink" type="submit">
                            Create Perma Link
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
