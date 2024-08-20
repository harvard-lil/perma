<script setup>
const model = defineModel()
const props = defineProps({
    error: Array,
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
        <template v-for="error in props.error">
            <span class="help-block js-warning">{{ error }}</span>
        </template>
    </div>
</template>