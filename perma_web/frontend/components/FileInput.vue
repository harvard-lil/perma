<script setup>
const model = defineModel()
const props = defineProps({
    error: Array,
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
        <template v-for="error in props.error">
            <span class="help-block js-warning">{{ error }}</span>
        </template>
    </div>
</template>