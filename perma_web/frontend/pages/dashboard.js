import { createApp } from 'vue'
import { createPinia } from 'pinia'
import App from '../components/App.vue'
import { useGlobalStore } from '../stores/globalStore'

const app = createApp(App)

const pinia = createPinia()
app.use(pinia)

app.mount('#vue-app')
