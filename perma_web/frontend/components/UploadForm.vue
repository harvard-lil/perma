<script setup>
import { ref } from 'vue'
import TextInput from './TextInput.vue';

const formData = ref({
    // Data is for debugging only right now
    url: { name: 'New Perma Link URL', type: "text", description: "The URL associated with this upload", placeholder: "Page URL", value: '' },
    title: { name: "New Perma Link Title", type: "text", description: "A test description for testing", placeholder: "Placeholder", value: '' },
})

// Match backend format for errors, for example {file:"message",url:"message"},
const errors = ref({})

// Debug only
const handleErrorToggle = () => {
    errors.value.url = "URL cannot be empty."
}

const handleErrorReset = () => {
    errors.value = {}
}

</script>

<template>
    <div class="modal-content">
        <div class="modal-body">
            <form id="archive_upload_form" @submit.prevent>
                <template v-for="(_, key) in formData" :key="key">
                    {{ formData[key].value }} <!-- Testing only -->
                    <TextInput v-if="formData[key].type === 'text'" v-model="formData[key]" :error="errors[key]"
                        :id="key" />
                </template>
                <button @click.prevent="handleErrorToggle">Toggle Error</button>
                <button @click.prevent="handleErrorReset">Reset Errors</button>
            </form>
        </div>
    </div>
</template>