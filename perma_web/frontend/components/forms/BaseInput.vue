<script setup>
const props = defineProps({
    modelValue: [String, Number, File],
    name: String,
    description: String,
    error: Array,
    id: String,
    required: {
        type: Boolean,
        default: false
    },
})
</script>

<template>
    <div class="form-group" :class="{ 'has-error': props.error }">
        <label class="control-label" :for="props.id">
            {{ props.name }}
            <span v-if="props.required" class="required-indicator">*</span>
            <span v-if="props.description" class="label-instruction">{{ props.description }}</span>
        </label>
        <slot></slot>
        <template v-for="error in props.error">
            <span class="help-block js-warning">{{ error }}</span>
        </template>
    </div>
</template>