<script setup>
import { ref, watch, computed } from 'vue'
import TextInput from './TextInput.vue';
import FileInput from './FileInput.vue';
import Dialog from './Dialog.vue';
import { getCookie } from '../../static/js/helpers/general.helpers';
import { rootUrl } from '../lib/consts'
import { globalStore } from '../stores/globalStore';
import { getErrorResponse, getGlobalErrorValues, getErrorFromStatus } from '../lib/errors'


const defaultFields = {
    title: { name: "New Perma Link title", type: "text", description: "The page title associated", placeholder: "Example Page Title", value: '' },
    description: { name: "New Perma Link description", type: "text", description: "The page description associated with this upload", placeholder: "Example description", value: '' },
    url: { name: 'New Perma Link URL', type: "text", description: "The URL associated with this upload", placeholder: "www.example.com", value: '' },
    file: { name: "Choose a file", type: "file", description: ".gif, .jpg, .pdf, and .png allowed, up to 100 MB", value: '' },
}

const fieldsWithGUID = {
    file: defaultFields.file
}

const initialData = !!globalStore.captureGUID ? fieldsWithGUID : defaultFields

const formData = ref(initialData)

watch(
    () => globalStore.captureGUID,
    (newGUID) => {
        formData.value = newGUID ? fieldsWithGUID : defaultFields;
    }
);

const errors = ref({})
const hasErrors = ref(false)
const globalErrors = computed(() => { return getGlobalErrorValues(formData.value, errors.value) })

const handleErrorReset = () => {
    errors.value = {}
    hasErrors.value = false
}

const formDialogRef = ref('')
const handleOpen = () => {
    formDialogRef.value.handleDialogOpen();
}

const handleClose = () => {
    handleReset()
    formDialogRef.value.handleDialogClose();
}

const handleReset = () => {
    formData.value = defaultFields;
}

const handleClick = (e) => {
    if (e.target.classList.contains('c-dialog')) {
        handleClose();
    }
}

const handleUploadRequest = async () => {
    handleErrorReset()

    const csrf = getCookie("csrftoken")
    const requestType = globalStore.captureGUID ? "PATCH" : "POST"
    const archiveBaseUrl = `${rootUrl}/archives/`
    const requestUrl = globalStore.captureGUID ? `${archiveBaseUrl}${globalStore.captureGUID}/` : archiveBaseUrl

    const formDataObj = new FormData();
    formDataObj.append('folder', globalStore.selectedFolder.folderId);

    for (const [key, { value }] of Object.entries(formData.value)) {
        formDataObj.append(key, value);
    }

    try {
        const response = await fetch(requestUrl,
            {
                headers: {
                    "X-CSRFToken": csrf,
                },
                method: requestType,
                credentials: "same-origin",
                body: formDataObj
            })


        if (!response?.ok) {
            const errorResponse = await getErrorResponse(response)
            throw errorResponse
        }

        const { guid } = await response.json()
        globalStore.updateCapture('success')

        handleReset()

        window.location.href = `${window.location.origin}/${guid}`
    } catch (error) {
        console.error("Upload request failed:", error);

        hasErrors.value = true

        if (error?.response) {
            errors.value = error.response
        } else {
            errors.value = error.status ? getErrorFromStatus(error.status) : defaultError
        }
    }
};


defineExpose({
    handleOpen
});

</script>

<template>
    <Dialog :handleClick="handleClick" :handleClose="handleClose" ref="formDialogRef">
        <div class="modal-dialog modal-content">
            <div class="modal-header">
                <button type="button" class="close" data-dismiss="modal" @click.prevent="handleClose">
                    <span aria-hidden="true">&times;</span>
                    <span class="sr-only" id="loading">Close</span>
                </button>
                <h3 id="batch-modal-title" class="modal-title">
                    Upload a file to Perma.cc
                </h3>
                errors: {{ errors }}
                global errors: {{ globalErrors }}
            </div>
            <p class="modal-description">
                {{
        !!globalStore.captureGUID ?
            "This will update the Perma Link you have created." :
            "This will create a new Perma Link." }}
            </p>
            <div class="modal-body">
                <form id="archive_upload_form" @submit.prevent>
                    <template v-for="(_, key) in formData" :key="key">
                        <TextInput v-if="formData[key].type === 'text'" v-model="formData[key]" :error="errors[key]"
                            :id="key" />
                        <FileInput v-if="formData[key].type === 'file'" v-model="formData[key]" :error="errors[key]"
                            :id="key" />
                    </template>
                    <div class="form-buttons">
                        <button type="submit" @click.prevent="handleUploadRequest" class="btn btn-primary btn-large">{{
        !!globalStore.captureGUID ?
            "Upload" :
            "Create a Perma Link" }}</button>
                        <button type="button" @click.prevent="handleClose" class="btn cancel">Cancel</button>
                    </div>

                    <p v-if="hasErrors" class="field-error">
                        Upload failed.
                        <span v-if="globalErrors">
                            {{ globalErrors }}
                        </span>
                    </p>

                </form>
            </div>
        </div>
    </Dialog>
</template>