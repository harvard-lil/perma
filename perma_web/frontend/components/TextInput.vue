<script setup>
const model = defineModel()
const props = defineProps({
    error: String,
    id: String
})

</script>

<template>
    <div class="form-group" :class="{
        'has-error': props.error
    }">
        <label class=" control-label" :for="props.id">{{ model.name }} <span v-if="model.description"
                class="label-instruction">{{
        model.description }}</span></label>
        <input v-model="model.value" :id="props.id" :name="props.id" type="text" :placeholder="model.placeholder" />
        <span v-if="props.error" class="help-block js-warning">{{ props.error }}</span>
    </div>
</template>