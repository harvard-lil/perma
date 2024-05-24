<script setup>
import { defineProps } from 'vue';
import { validStates } from '../lib/consts.js'
import ProgressBar from './ProgressBar.vue';

const props = defineProps({
  batchCaptureJobs: Object,
  batchCaptureSummary: String,
  handleClose: Function,
  showBatchCSVUrl: Boolean,
  batchCSVUrl: String,
  targetFolder: String,
})
</script>

<template>
  <div id="batch-details-wrapper">
    <p id="batch-progress-report">
      {{ props.batchCaptureSummary }}
      <span v-if="!!props.batchCaptureJobs.errors">{{ props.batchCaptureJobs.errors }} {{
        props.batchCaptureJobs.errors > 1 ? 'errors' : 'error' }}</span>
    </p>
    <div id="batch-details" aria-describedby="batch-progress-report">
      <div class="form-group">
        <p>These Perma Links were added to {{ props.targetFolder }}</p>
      </div>
      <div class="form-group">
        <div v-for="job in props.batchCaptureJobs.details">
          <div class="item-container" :class="{ '_isFailed': !validStates.includes(job.status) }">
            <div class="row">
              <div v-if="!validStates.includes(job.status)" class="link-desc col col-sm-6 col-md-60">
                <div class="failed_header">{{ job.error_message }}</div>
                <div class="item-title">We're unable to create your Perma Link.</div>
                <div class="item-date">submitted: {{ job.submitted_url }}</div>
              </div>
              <div v-else class="link-desc col col-sm-6 col-md-60">
                <div v-if="job.user_deleted" class="failed_header">Deleted</div>
                <div class="item-title">{{ job.title }}</div>
                <div class="item-subtitle">{{ job.submitted_url }}</div>
              </div>
              <div class="link-progress col col-sm-6 col-md-40 align-right item-permalink">
                <span v-if="job.status === 'pending'">Queued.</span>
                <ProgressBar v-if="job.status === 'in_progress'" :progress="`${job.progress}%`" />
                <span v-if="job.status === 'completed'">
                  <a class="perma no-drag" :href="`/${job.guid}`">
                    {{ job.url }}
                  </a>
                </span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
    <div class="form-buttons">
      <button class="btn cancel" @click.prevent="handleClose">Exit</button>
      <a v-if="props.showBatchCSVUrl" :href="props.batchCSVUrl" class="btn">Export list as
        CSV</a>
    </div>
  </div>
</template>
