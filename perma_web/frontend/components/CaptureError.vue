<script setup>
import { ref, watch } from 'vue'
import { useGlobalStore } from '../stores/globalStore';
import UploadForm from './UploadForm.vue';

const globalStore = useGlobalStore()
const showUploadLink = ref()
const showGeneric = ref()
const showLoginLink = ref()

const uploadDialogRef = ref('')
const handleOpen = () => {
    uploadDialogRef.value.handleOpen()
}

const props = defineProps({
    errorMessage: {
        type: String,
        default: ''
    },
    captureGUID: {
        type: String,
        default: ''
    }
})

watch(
    () => props.errorMessage,
    (errorMessage) => {
        showUploadLink.value = true
        showGeneric.value = true
        showLoginLink.value = false

        if (errorMessage.includes("logged out")) {
            showLoginLink.value = true;
            showUploadLink.value = false;
        }

        else if (errorMessage.includes("limit")) {
            globalStore.linksRemaining = 0;
            showUploadLink.value = false;
            showGeneric.value = false;
        }

        else if (errorMessage.includes("subscription")) {
            showUploadLink.value = false;
            showGeneric.value = false;
        }

        else if (errorMessage.includes("Error 0") || errorMessage.includes("folder")) {
            showUploadLink.value = false;
        }

        else if (errorMessage.includes("account needs attention")) {
            showUploadLink.value = false;
            showGeneric.value = false;
        }

        else if (errorMessage.includes("Not a valid URL")) {
            showUploadLink.value = false;
        }
    },
    { immediate: true },
);

defineExpose({
    handleOpen
});

</script>

<template>
    <div id="error-container" role="alert" aria-live="assertive">
        <p class="message">
            {{ errorMessage }}
            <template v-if="showLoginLink">Please <a href='/login'>log in</a> to continue.</template>
            <template v-else-if="showGeneric">We’re unable to create your Perma Link.</template>
        </p>
        <template v-if="showUploadLink">
            <p>You can <button @click.prevent="handleOpen">upload your own
                    archive</button> or <a href="{{contact_url}}">contact
                    us about this error.</a></p>
        </template>
    </div>

    <UploadForm
        v-if="showUploadLink"
        ref="uploadDialogRef"
        :captureGUID="captureGUID"
    />
</template>