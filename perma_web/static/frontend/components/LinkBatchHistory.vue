<script setup>
import { ref, watch, computed, onMounted } from 'vue'
import { useFetch } from '../lib/data'
import { useGlobalStore } from '../stores/globalStore'

const globalStore = useGlobalStore()
const linkRecords = ref([])
const limit = ref(7)
const isExpanded = ref(false)

const { isLoading, hasError, error, data, fetchData } = useFetch('/archives/batches/')

const fetchBatchData = async () => {
  fetchData({params: {limit: limit.value}})
}

onMounted(fetchBatchData)

watch(limit, fetchBatchData)
  
watch(data, () => {
  if (data.value) {
    linkRecords.value = data.value.objects
  }
})

const handleBatchClick = (batch) => {
  globalStore.components.batchDialog.showBatchHistory(batch.id)
}

function human_timestamp(datetime) {
  return new Date(datetime).toLocaleString("en-us", {
    year: "numeric",
    month: "long",
    day: "numeric",
    hour: "numeric",
    minute: "2-digit"
  });
}

const toggleExpanded = () => {
  isExpanded.value = !isExpanded.value
}

</script>

<template>
  <div v-if="linkRecords.length > 0" id="batch-list-toggle">
    <a role="button" @click="toggleExpanded" :aria-expanded="isExpanded">
      <h3>Link Batch History</h3>
    </a>
  </div>
  <div id="batch-history" v-show="isExpanded">
    <ul v-if="!isLoading && !hasError" class="item-container">
      <li v-for="batch in linkRecords" :key="batch.id" class="item-subtitle">
        <a href="#" @click.prevent="handleBatchClick(batch)">
          <span class="sr-only">Batch created </span>{{ human_timestamp(batch.started_on) }}
        </a>
      </li>
    </ul>
    <p v-else-if="hasError">{{ error || '(unavailable)' }}</p>
    <p v-else>Loading...</p>
    <a v-if="data?.meta?.next" href="#" id="all-batches" @click.prevent="limit = null">all batches</a>
  </div>
</template>