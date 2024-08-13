<script setup>
const props = defineProps({
  name: String,
  icon: {
    type: String,
    validator(value) {
      return [
        "organization",
      ].includes(value);
    },
  },
});
</script>

<template>
  <div class="c-sectionHeading">
    <template v-if="!!icon">
      <svg v-if="icon === 'organization'" width="18" height="20" viewBox="0 0 18 20" fill="none" xmlns="http://www.w3.org/2000/svg">
        <rect width="18" height="20" fill="white"/>
        <path fill-rule="evenodd" clip-rule="evenodd" d="M4.73995 9.90178C4.39114 10.0982 4.03265 10.332 3.6354 10.6032C0.563971 12.6699 1.17438 18.8889 1.17438 18.8889H13.4504C13.4504 18.8889 14.0608 12.6699 10.9991 10.5938C10.6018 10.3226 10.2336 10.0888 9.89452 9.89243C11.2994 9.06012 12.2296 7.56383 12.2296 5.85245C12.2296 3.23394 10.0302 1.11108 7.31723 1.11108C4.6043 1.11108 2.40489 3.2433 2.40489 5.8618C2.40489 7.56383 3.33504 9.06012 4.73995 9.90178Z" fill="#2D76EE" stroke="white"/>
        <path fill-rule="evenodd" clip-rule="evenodd" d="M8.10662 9.89243C7.75787 10.0888 7.39943 10.3226 7.00224 10.5938C3.93129 12.6699 4.5513 18.8889 4.5513 18.8889H16.8254C16.8254 18.8889 17.4357 12.6699 14.3745 10.5938C13.9773 10.3226 13.6091 10.0888 13.2701 9.89243C14.6748 9.06012 15.6048 7.56383 15.6048 5.85245C15.6048 3.23394 13.4057 1.11108 10.6932 1.11108C7.98068 1.11108 5.78161 3.23394 5.78161 5.85245C5.78161 7.55448 6.71162 9.05076 8.11631 9.89243H8.10662Z" fill="#2D76EE" stroke="white"/>
      </svg>
    </template>
    <h3 class="c-sectionHeading__name">{{ props.name }}</h3>
  </div>
</template>