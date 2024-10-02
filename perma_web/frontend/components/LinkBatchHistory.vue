<script setup>
import { ref, watch, computed, onMounted } from 'vue'
import { useFetch } from '../lib/data'
import { useGlobalStore } from '../stores/globalStore'

const globalStore = useGlobalStore()
const linkRecords = ref([])
const limit = ref(7)

const { isLoading, hasError, error, data, fetchData } = useFetch('/archives/batches/')

const fetchBatchData = async () => {
  fetchData({params: {limit: limit.value}})
}

onMounted(fetchBatchData)

watch(limit, fetchBatchData)
  
watch(data, () => {
  if (data.value) {
    linkRecords.value = data.value.objects
    // TODO: previously this called
    //     DOMHelpers.scrollIfTallerThanFractionOfViewport(".col-folders", 0.9);
    // not sure if necessary in Vue
  }
})

const handleBatchClick = (e, batch) => {
  e.preventDefault()
  const folderPath = batch.target_folder.path
  const org = parseInt(batch.target_folder.organization)

  // TODO: previously this forced a reload of the folder tree with
  //       Helpers.triggerOnWindow('batchLink.reloadTreeForFolder', {
  //         folderId: folderPath.split('-'),
  //         orgId: org
  //       });
  // not sure if necessary in Vue

  globalStore.batchDialogRef.showBatchHistory(batch.id)
}

function human_timestamp (datetime) {
    return new Date(datetime).toLocaleString("en-us", {
        year:   "numeric",
        month:  "long",
        day:    "numeric",
        hour:   "numeric",
        minute: "2-digit"
    });
}


</script>

<template>
  <div id="batch-list-container" :class="{ '_hide': linkRecords.length === 0 }">
    <div id="batch-list-toggle">
      <a role="button" class="dropdown" data-toggle="collapse" href="#batch-history" aria-expanded="false" aria-controls="batch-history">
        <h3>Link Batch History</h3>
      </a>
    </div>
    <div id="batch-history" class="collapse">
      <ul v-if="!isLoading && !hasError" class="item-container">
        <li v-for="batch in linkRecords" :key="batch.id" class="item-subtitle">
          <a href="#" @click="(e) => handleBatchClick(e, batch)">
            <span class="sr-only">Batch created </span>{{ human_timestamp(batch.started_on) }}
          </a>
        </li>
      </ul>
      <p v-else-if="hasError">{{ error || '(unavailable)' }}</p>
      <p v-else>Loading...</p>
      <a v-if="data?.meta?.next" href="#" id="all-batches" @click="limit = null">all batches</a>
    </div>
  </div>
</template>