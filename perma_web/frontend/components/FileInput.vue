<script setup>
const model = defineModel()
const props = defineProps({
    error: String,
    id: String
})

const handleFileChange = (event) => {
    const file = event.target.files[0];
    model.value = {
        ...model.value,
        value: file
    }
};

</script>

<template>
    <div class="form-group" :class="{
        'has-error': props.error
    }">
        <label class="control-label" :for="props.id">{{ model.name }} <span class="label-instruction">{{
        model.description }}</span></label>
        <input v-on:change="handleFileChange" :id="props.id" class="file" :name="props.id" type="file"
            accept=".png,.jpg,.jpeg,.gif,.pdf">
        <span v-if="props.error" class="help-block js-warning">{{ props.error }}</span>
    </div>
</template>