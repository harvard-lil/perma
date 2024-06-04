<script setup>
import { ref, watch } from 'vue'
import { globalStore } from '../stores/globalStore';

const showUploadLink = ref()
const showGeneric = ref()
const showLoginLink = ref()

watch(
    () => globalStore.captureErrorMessage,
    (errorMessage) => {
        showUploadLink.value = true
        showGeneric.value = true
        showLoginLink.value = false

        if (errorMessage.includes("logged out")) {
            showLoginLink.value = true;
            showUploadLink.value = false;
        }

        else if (errorMessage.includes("limit")) {
            globalStore.updateLinksRemaining(0);
            showUploadLink.value = false;
        }

        else if (errorMessage.includes("subscription")) {
            showUploadLink.value = false;
            showGeneric.value = false;
        }

        else if (errorMessage.includes("Error 0")) {
            showUploadLink.value = false;
        }
    }
);
</script>

<template>
    <div class="container cont-fixed">
        <div v-if="globalStore.captureErrorMessage" id="error-container">
            <p class="message-large">{{ globalStore.captureErrorMessage }} <span v-if="showLoginLink">
                    Please <a href='/login'>login</a> to continue.
                </span></p>
            <p v-if="showGeneric" class="message">We’re unable to create your Perma Link.</p>
            <p v-if="showUploadLink">You can <button id="upload-form-button">upload your own archive</button> or <a
                    href="/contact">contact us
                    about this error.</a></p>
        </div>
    </div>
</template>