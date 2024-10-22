<script setup>
import { ref, watch, computed } from 'vue'
import TextInput from './forms/TextInput.vue';
import Dialog from './Dialog.vue'
import { useGlobalStore } from '../stores/globalStore'
import { getErrorFromStatus, defaultError } from '../lib/errors'
import { fetchDataOrError } from '../lib/data'
import Spinner from './Spinner.vue'
import FileInput from './forms/FileInput.vue';

const props = defineProps({
  captureGUID: {
    type: String,
    default: ''
  }
})

const globalStore = useGlobalStore()

const captureStatus = ref('ready')
const errors = ref({})
const globalErrors = ref()
const title = ref('')
const description = ref('')
const url = ref('')
const file = ref(null)

const formDialogRef = ref('')
const handleOpen = () => {
  formDialogRef.value.handleDialogOpen();
}

const handleClose = () => {
  handleReset()
  formDialogRef.value.handleDialogClose();
}

const handleReset = () => {
  captureStatus.value = 'ready'
}

const handleClick = (e) => {
  if (e.target.classList.contains('c-dialog')) {
    handleClose();
  }
}

const handleUploadRequest = async () => {
  if (captureStatus.value !== 'ready') {
    return
  }

  // validation
  errors.value = {}
  if (!file.value) {
    errors.value.file = ['File is required']
  }
  if (!props.captureGUID) {
    if (!url.value) {
      errors.value.url = ['URL is required']
    }
  }
  if (Object.keys(errors.value).length > 0) {
    return
  }

  // prepare form data
  captureStatus.value = "isValidating"
  const formDataObj = new FormData();
  formDataObj.append('folder', globalStore.selectedFolder.folderId);
  formDataObj.append('file', file.value);
  formDataObj.append('title', title.value);
  formDataObj.append('description', description.value);
  if (!props.captureGUID) {
    formDataObj.append('url', url.value);
  }

  // send request
  const requestType = props.captureGUID ? "PATCH" : "POST"
  const requestUrl = "/archives/" + (props.captureGUID ? `${props.captureGUID}/` : "")
  const {data, error, response} = await fetchDataOrError(requestUrl, {
    method: requestType,
    data: formDataObj,
  })

  // error handling
  if (error) {
    console.log(error, response)
    if (data) {
      errors.value = data
    } else {
      globalErrors.value = response.status ? getErrorFromStatus(response.status) : defaultError
    }
    return;
  }

  // success
  const {guid} = data
  globalStore.components.createLink.resetForm()
  window.location.href = `${window.location.origin}/${guid}`
};


defineExpose({
  handleOpen
});

</script>

<template>
  <Dialog :handleClick="handleClick" :handleClose="handleClose" ref="formDialogRef">
    <div class="modal-dialog modal-content modal-lg">
      <div class="modal-header">
        <button type="button" class="close" data-dismiss="modal" @click.prevent="handleClose">
          <span aria-hidden="true">&times;</span>
          <span class="sr-only" id="loading">Close</span>
        </button>
        <h3 id="batch-modal-title" class="modal-title">
          Upload a file to Perma.cc
        </h3>
      </div>
      <p v-if="props.captureGUID" class="modal-description">
        This will update the Perma Link you were trying to create.
      </p>
      <p v-else class="modal-description">
        This will create a new Perma Link.
      </p>
      <div class="modal-body">

        <div class="u-min-h-48" v-if="globalStore.isLoading">
          <Spinner/>
        </div>

        <form id="archive_upload_form" @submit.prevent>
            <TextInput
                v-model="title"
                name="New Perma Link title"
                description="The page title associated with this upload"
                placeholder="Example Page Title"
                id="title"
                :error="errors.title"
            />
            <TextInput
                v-model="description"
                name="New Perma Link description"
                description="The page description associated with this upload"
                placeholder="Example Page Description"
                id="description"
                :error="errors.description"
            />
          <template v-if="!props.captureGUID">
            <TextInput
                v-model="url"
                name="New Perma Link URL"
                description="The URL associated with this upload"
                placeholder="https://www.example.com"
                id="url"
                type="url"
                :error="errors.url"
            />
          </template>

          <FileInput
              v-model="file"
              name="Choose a file"
              :description="`.gif, .jpg, .pdf, and .png allowed, up to ${globalStore.maxSize} MB`"
              id="file"
              accept=".png,.jpg,.jpeg,.gif,.pdf"
              :error="errors.file"
          />

          <div class="form-buttons">
            <button type="submit" @click.prevent="handleUploadRequest" class="btn btn-primary btn-large">
              {{ !!props.captureGUID ? "Upload" : "Create a Perma Link" }}
            </button>
            <button type="button" @click.prevent="handleClose" class="btn cancel">Cancel</button>
          </div>

          <p v-if="globalErrors" class="field-error">
            Upload failed. {{ globalErrors }}
          </p>

        </form>
      </div>
    </div>
  </Dialog>
</template>
