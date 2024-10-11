<script setup>
import BaseInput from './BaseInput.vue'

const props = defineProps({
  modelValue: [String, Number],
  name: String,
  description: String,
  placeholder: String,
  error: Array,
  id: String,
  type: {
    type: String,
    default: 'text'
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
    <input
      :value="props.modelValue"
      @input="updateValue"
      :id="props.id"
      :name="props.id"
      :type="props.type"
      :placeholder="props.placeholder"
      :required="props.required"
    />
  </BaseInput>
</template>