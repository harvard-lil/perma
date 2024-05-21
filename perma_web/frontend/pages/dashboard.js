import { createApp } from 'vue'
import App from '../components/App.vue'
import { globalStore } from '../stores/globalStore'

createApp(App).mount('#vue-app')

// Handle updates the legacy application needs to make to the store
const handleDispatch = (name, data) => {
    switch (name) {
        case "updateFolderSelection":
        default: 
        globalStore.updateAdditionalSubfolder(false)
        globalStore.updateFolderSelection(data)
        break;
    }
}

// One event listener for all vueDispatch custom events
document.addEventListener("vueDispatch", (e) => handleDispatch(e.detail.name, e.detail.data));
