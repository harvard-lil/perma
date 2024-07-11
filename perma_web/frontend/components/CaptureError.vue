<script setup>
import { ref, watch } from 'vue'
import { globalStore } from '../stores/globalStore';
import UploadForm from './UploadForm.vue';
import { showDevPlayground } from '../lib/consts'


const showUploadLink = ref()
const showGeneric = ref()
const showLoginLink = ref()

const uploadDialogRef = ref('')
const handleOpen = () => {
    uploadDialogRef.value.handleOpen()
}

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

        else if (errorMessage.includes("Error 0") || errorMessage.includes("folder")) {
            showUploadLink.value = false;
        }
    }
);

defineExpose({
    handleOpen
});

</script>

<template>
    <div class="container cont-fixed">
        <!-- <div v-if="globalStore.captureErrorMessage" id="error-container"> -->
        <div id="error-container">
            <p class="message-large">{{ globalStore.captureErrorMessage }} <span v-if="showLoginLink">
                    Please <a href='/login'>log in</a> to continue.
                </span></p>
            <!-- <p v-if="showGeneric" class="message">We’re unable to create your Perma Link.</p> -->
            <p class="message">We’re unable to create your Perma Link.</p>
            <!-- <template> -->
            <template v-if="showDevPlayground">
                <p>You can <button @click.prevent="handleOpen">upload your own
                        archive</button> or <a href="{{contact_url}}">contact
                        us about this error.</a></p>
                <UploadForm ref="uploadDialogRef" />
            </template>
            <!-- <p v-else>You can <button id="upload-form-button">upload your own archive</button> or <a
                        href="/contact">contact us
                        about this error.</a></p> -->
            <!-- </template> -->

        </div>
    </div>

    <!-- <UploadForm ref="uploadDialogRef" /> -->
</template>