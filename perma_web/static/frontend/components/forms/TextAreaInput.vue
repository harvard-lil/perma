<script setup>
import BaseInput from './BaseInput.vue'

const props = defineProps({
  modelValue: [String, Number],
  name: String,
  description: String,
  placeholder: String,
  error: Array,
  id: String,
  rows: {
    type: Number,
    default: 3
  },
  required: {
    type: Boolean,
    default: false
  },
})

const emit = defineEmits(['update:modelValue'])

const updateValue = (event) => {
  emit('update:modelValue', event.target.value)
}
</script>

<template>
  <BaseInput v-bind="props">
    <textarea
      :value="props.modelValue"
      @input="updateValue"
      :id="props.id"
      :name="props.id"
      :placeholder="props.placeholder"
      :required="props.required"
      :rows="props.rows"
    ></textarea>
  </BaseInput>
</template>