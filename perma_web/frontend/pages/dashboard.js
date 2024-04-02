import { createApp } from 'vue'
import App from '../components/App.vue'
import { watch } from 'vue';
import { globalStore } from '../stores/globalStore';

createApp(App).mount('#vue-app')

// const dashboardTestDiv = document.getElementsByClassName("vanilla-div")[0]

// Track updates our Vue app makes to the store
// watch(
//     () => globalStore.count,
//     (count) => {
//         dashboardTestDiv.innerHTML = `Vanilla JavaScript count: ${count}`
//     },
//     { immediate: true }
// )

// Handle updates the legacy application makes to the store
// const handleDispatch = (name) => {
//     switch (name) {
//         case "increment":
//         default:
//             globalStore.increment()
//         break;
//     }
// }

// const increment = new CustomEvent("vueDispatch", {
//     bubbles: true,
//     detail: { name: 'increment' },
// })

// One event listener for all vueDispatch custom events
// document.addEventListener("vueDispatch", (e) => handleDispatch(e.detail.name));

// const vanillaButton = document.getElementsByClassName('vanilla-button')[0]
// vanillaButton.addEventListener("click", function () {
//     this.dispatchEvent(increment)
// });
