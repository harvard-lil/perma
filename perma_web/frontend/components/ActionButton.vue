<script setup>

const props = defineProps({
  name: String,
  handleClick: Function,
  iconFamily: {
    type: String,
    default: "fontAwesome",
    validator(value) {
      return ["fontAwesome", "none"].includes(value);
    },
  },
  icon: {
    type: String,
    validator(value) {
      return ["download-alt", "plus", "edit", "trash", "chevron-down", "chevron-up"].includes(value);
    },
  }
});

const isChevron = props.icon === 'chevron-down' || props.icon === 'chevron-up'

</script>

<template>
  <button :onClick="props.handleClick" 
  :class="`c-button c-button--icon ${props.iconFamily === 'fontAwesome' ? `icon-${props.icon}` : ''}`">    
    <svg v-if="isChevron" width="13" height="7" viewBox="0 0 13 7" fill="none" xmlns="http://www.w3.org/2000/svg">
      <path v-if="props.icon === 'chevron-down'" d="M6.5 7L0 1.32432L1.51667 0L6.5 4.35135L11.4833 0L13 1.32432L6.5 7Z" fill="#2E76EE"/>
      <path v-if="props.icon === 'chevron-up'" d="M6.5 1.12443e-07L0 5.67568L1.51667 7L6.5 2.64865L11.4833 7L13 5.67568L6.5 1.12443e-07Z" fill="#2E76EE"/>
    </svg>
    <span class="sr-only">{{ props.name }}</span>
  </button>
</template>
