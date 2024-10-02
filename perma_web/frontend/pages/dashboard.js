import { createApp } from 'vue'
import { createPinia } from 'pinia'
import App from '../components/App.vue'
import { useGlobalStore } from '../stores/globalStore'
import { vueDashboardFlag } from '../lib/consts'

const app = createApp(App)

const pinia = createPinia()
app.use(pinia)

app.mount('#vue-app')

if (!vueDashboardFlag) {
    // Handle updates the legacy application needs to make to the store
    const globalStore = useGlobalStore()
    const handleDispatch = (name, data) => {
        switch (name) {
            case "updateFolderSelection":
                globalStore.additionalSubfolder = false
                globalStore.selectedFolder = data
                break;
            default:
                console.warn(`Unhandled dispatch: ${name}`)
                break;
        }
    }
    document.addEventListener("vueDispatch", (e) => handleDispatch(e.detail.name, e.detail.data));
}