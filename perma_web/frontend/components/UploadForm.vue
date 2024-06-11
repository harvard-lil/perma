<script setup>
import { ref } from 'vue'
import TextInput from './TextInput.vue';

const formData = ref({
    // Data is for debugging only right now
    url: { name: 'New Perma Link URL', description: "The URL associated with this upload", placeholder: "Page URL", value: '' },
    title: { name: "New Perma Link Title", description: "A test description for testing", placeholder: "Placeholder", value: '' },
})

// Match backend format for errors, for example {file:"message",url:"message"},
const errors = ref({
    url: "",
    title: ""
})

// Debug only
const handleErrorToggle = () => {
    errors.value.url = "URL cannot be empty."
}

</script>

<template>
    <form @submit.prevent>
        <div v-for="(input, key) in formData" :key="key">
            {{ formData[key].value }} <!-- Testing only -->
            <TextInput v-model="formData[key]" :error="errors[key]" />
        </div>
        <button @click.prevent="handleErrorToggle">Toggle Error</button>
    </form>
</template>