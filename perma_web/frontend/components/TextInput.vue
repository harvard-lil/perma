<script setup>
const model = defineModel()
</script>

<template>
    <div class="form-group" :class="{
        'has-error': model.error
    }">
        <label class=" control-label" :for="model.value">{{ model.name }} <span v-if="model.description"
                class="label-instruction">{{
        model.description }}</span></label>
        <input v-model="model.value" :id="model.name" :name="model.name" type="text" :placeholder="model.placeholder" />
        <span v-if="model.error" class="help-block js-warning">{{ model.error }}</span>'
    </div>
</template>