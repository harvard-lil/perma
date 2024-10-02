<script setup>
import { ref } from 'vue';
import { useGlobalStore } from '../stores/globalStore'

const globalStore = useGlobalStore()

const testGUID = ref('');

const updateGUID = () => {
    triggerError()
    globalStore.captureGUID = testGUID.value
};

const clearGUID = () => {
    globalStore.captureGUID = ''
    testGUID.value = ''
};

const triggerError = () => {
    globalStore.captureError = 'captureError'
    globalStore.captureErrorMessage = 'testing'
};
</script>

<template>
    <div>
        <p>Current GUID in store: {{ globalStore.captureGUID || "None" }}</p>

        <label for="guid-input">GUID</label>
        <input id="guid-input" v-model="testGUID" />
        <button @click="updateGUID">Update GUID</button>
        <button @click="clearGUID">Clear GUID</button>
        <button @click="triggerError">Trigger Error</button>
    </div>
</template>