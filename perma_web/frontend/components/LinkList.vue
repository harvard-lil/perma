<script setup>
import { ref, computed, onMounted, watch, getCurrentInstance, onBeforeUnmount, nextTick } from 'vue';
import { useGlobalStore } from '../stores/globalStore';
import { storeToRefs } from 'pinia';
import { fetchDataOrError } from '../lib/data'
import { useInfiniteScroll } from '@vueuse/core'
import { useToast } from '../lib/notifications'

/*** Component setup ***/
const globalStore = useGlobalStore();
const { selectedFolder } = storeToRefs(globalStore);
const { addToast } = useToast();

/*** Variables ***/
const searchQuery = ref('');
const links = ref([]);
const query = ref('');
const organization = computed(() => selectedFolder.value.orgId);
const path = computed(() => selectedFolder.value.path.join(' > '));
const folder = computed(() => selectedFolder.value.folderId);
const saveStatuses = ref({});
const folderOptions = ref([]);
const offset = ref(0);
const limit = ref(20);
const loading = ref(false);
const hasMore = ref(true);
const selectedLink = ref(null);
const linkScrollContainer = ref(null);

/*** Methods ***/
const fetchLinks = async (append = false) => {
  if (!folder.value) {
    return;
  }
  loading.value = true;
  const { data, error } = await fetchDataOrError(`/folders/${folder.value}/archives/`, {
    params: {
      q: query.value,
      limit: limit.value,
      offset: offset.value
    }
  });
  loading.value = false;
  if (error) {
    addToast({message: 'Error fetching data. Please try again.', status: 'error'});
    return;
  }
  const newLinks = data.objects.map(link => ({
    ...generateLinkFields(link),
    showDetails: query.value && link.notes.includes(query.value),
  }));
  if (append) {
    links.value = [...links.value, ...newLinks];
  } else {
    links.value = newLinks;
  }
  hasMore.value = newLinks.length === limit.value;
  offset.value += limit.value;
};

const generateLinkFields = (link, query) => {
  if (window.host) {
    link.local_url = window.host + '/' + link.guid;
  }
  if (query && link.notes) {
    link.search_query_in_notes = (query && link.notes.indexOf(query) > -1);
  }
  link.expiration_date_formatted = link.expiration_date ? new Date(link.expiration_date).toLocaleDateString('en-US', { year: 'numeric', month: 'long', day: 'numeric' }) : '';
  link.creation_timestamp_formatted = link.creation_timestamp ? new Date(link.creation_timestamp).toLocaleDateString('en-US', { year: 'numeric', month: 'long', day: 'numeric' }) : '';
  if (Date.now() < Date.parse(link.archive_timestamp)) {
    link.delete_available = true;
  }
  // mark the capture as pending if either the primary or the screenshot capture are pending
  // mark the capture as failed if both the primary and the screenshot capture failed.
  // (ignore the favicon capture)
  let primary_failed = false;
  let screenshot_failed = false;
  let primary_pending = false;
  let screenshot_pending = false;
  link.favicon_url = '';
  link.captures.forEach(function(c){
    if (c.role==="primary"){
      if (c.status==="pending"){
        primary_pending = true;
      } else if (c.status==="failed"){
        primary_failed = true;
      }
    } else if (c.role==="screenshot"){
      if (c.status==="pending"){
        screenshot_pending = true;
      } else if (c.status==="failed"){
        screenshot_failed = true;
      }
    } else if (c.role==="favicon" && c.status==="success"){
      link.favicon_url = c.playback_url;
    }
  });
  if (primary_pending || screenshot_pending){
    link.is_pending = true;
  }
  if (primary_failed && screenshot_failed){
    link.is_failed = true;
  }
  return link;
}

/*** UI interaction methods ***/
const submitSearch = () => {
  query.value = searchQuery.value;
  resetPagination();
  fetchLinks();
};

const clearSearch = () => {
  searchQuery.value = '';
  query.value = '';
  resetPagination();
  fetchLinks();
};

const toggleLinkDetails = function(e, link) {
  if (e.target.classList.contains('no-drag')) {
    // Don't toggle details if the user has clicked on the Perma Link URL,
    // the original URL, or the delete button
    return
  }

  if (selectedLink.value === link) {
    link.showDetails = false;
    selectedLink.value = null;
  } else {
    if (selectedLink.value) {
      selectedLink.value.showDetails = false;
    }
    selectedLink.value = link;
    link.showDetails = true;

    // populate folder options
    // TODO: we redo this every time because it shows the currently opened folders
    // in the tree. Ideally we'd only do it if the tree was updated.
    const options = [];
    const folderTree = globalStore.components.jstree.getFolderTree();
    // recursively populate select
    function addChildren(node, depth) {
      for (var i = 0; i < node.children.length; i++) {
        var childNode = folderTree.get_node(node.children[i]);
        options.push({
          value: childNode.data.folder_id,
          text: (depth > 1 ? '└'.padStart(depth, '\u00A0') + ' ' : '') + childNode.text.trim(),
          selected: childNode.data.folder_id == folder.value,
          disabled: childNode.data.is_sponsored_root_folder || childNode.data.read_only,
          "data-orgid": childNode.data.organization_id,
        });

        // recurse
        if (childNode.children && childNode.children.length) {
          addChildren(childNode, depth + 1);
        }
      }
    }
    addChildren(folderTree.get_node('#'), 1);
    folderOptions.value = options;
  }
}

const moveLink = async (folderID, guid) => {
  const { data, error } = await fetchDataOrError(`/folders/${folderID}/archives/${guid}/`, {
    method: 'PUT',
  });
  if (error) {
    addToast({message: 'Error fetching data. Please try again.', status: 'error'});
    return;
  }
  globalStore.linksRemaining = data.links_remaining;
  // remove the link from the current folder
  links.value = links.value.filter(link => link.guid !== guid);
}

const onFolderSelectionChange = (e, guid) => {
  const folderId = e.target.value;
  if (!folderId) return;
  moveLink(folderId, guid);
}

/*** Utility methods ***/
const truncateChars = (str, num) => {
  if (str.length <= num) {
    return str;
  }
  return str.slice(0, num) + '...';
};

const timeoutIds = {};
const handleInput = async (guid, field, value) => {
  const statusKey = `${guid}-${field}`;
  saveStatuses.value[statusKey] = 'Saving...';

  if (timeoutIds[statusKey]) {
    clearTimeout(timeoutIds[statusKey]);
  }

  timeoutIds[statusKey] = setTimeout(async () => {
    const { data, error } = await fetchDataOrError(`/archives/${guid}/`, {
      method: 'PATCH',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ [field]: value }),
    });

    if (error) {
      saveStatuses.value[statusKey] = 'Error saving';
      addToast({message: 'Error fetching data. Please try again.', status: 'error'});
      return;
    }

    saveStatuses.value[statusKey] = 'Saved!';
    setTimeout(() => {saveStatuses.value[statusKey] = ''}, 2000);
  }, 500);
};

const resetPagination = () => {
  links.value = [];
  offset.value = 0;
  hasMore.value = true;
};

/*** Drag and drop ***/
let dragStartPosition = null;

function handleMouseDown (e, link) {
  if (e.target.classList.contains('no-drag'))
    return;

  globalStore.components.jstree.dnd.start(e, {
    jstree: true,
    // obj: $(e.currentTarget),
    nodes: [
        {id: link.guid}
    ]
  }, '<div id="jstree-dnd" class="jstree-default"><i class="jstree-icon jstree-er"></i>[link]</div>');

  // record drag start position so we can check how far we were dragged on mouseup
  dragStartPosition = [e.pageX || e.originalEvent.touches[0].pageX, e.pageY || e.originalEvent.touches[0].pageY];
}

function handleMouseUp (e, link) {
  // prevent JSTree's tap-to-drag behavior
  globalStore.components.jstree.dnd.stop(e);

  // don't treat this as a click if the mouse has moved more than 5 pixels -- it's probably an aborted drag'n'drop or touch scroll
  if(dragStartPosition && Math.sqrt(Math.pow(e.pageX-dragStartPosition[0], 2)*Math.pow(e.pageY-dragStartPosition[1], 2))>5)
    return;

  toggleLinkDetails(e, link);
}

/*** Infinite scroll setup ***/
useInfiniteScroll(
  linkScrollContainer,
  () => {
    if (!loading.value && hasMore.value) {
      fetchLinks(true);
    }
  },
  { distance: 10 }
);

/*** Lifecycle hooks and watchers ***/
// onMounted(fetchLinks);

watch([selectedFolder, query], () => {
  resetPagination();
  fetchLinks();
});

onMounted(() => {
  globalStore.components.linkList = getCurrentInstance().exposed;
});

onBeforeUnmount(() => {
  globalStore.components.linkList = null;
});

defineExpose({
  fetchLinks
});

</script>

<template>
  <div>
    <div class="container link-headers">
      <div class="row">
        <div class="col-xs-12">
          <h3 id="link-list-header" class="body-ah">
            <template v-if="organization">
              <span class="organization">{{ path }} Links</span>
            </template>
            <template v-else>
              Your Perma Links
            </template>
            <a :href="`/api/v1/folders/${folder}/archives/export`" id="export-links-csv" class="pull-right icon-download-alt" aria-label="Export Links" title="Export Links"></a>
          </h3>
        </div>
      </div>
    </div>

    <form class="search-query-form form-inline" @submit.prevent="submitSearch">
      <fieldset>
        <div class="form-group fg-inline fg-search">
          <input aria-label="Enter your search query here" type="text" name="q" v-model="searchQuery" placeholder="Search" class="search-query"/>
        </div>
        <button aria-label="Submit" type="submit" name="submit" value="1" class="btn btn-default btn-inline btn-search"><span class="icon-search"></span></button>
      </fieldset>
    </form>

    <div class="container item-rows" ref="linkScrollContainer" style="overflow-y: auto; height: 60vh">
      <div v-if="query" class="shared-folder-label alert-success">
        Search results for "{{ query }}".
        <a href="#" class="clear-search" @click.prevent="clearSearch">Clear search.</a>
      </div>

      <template v-if="links.length">
        <div v-for="link in links" 
          :key="link.guid" 
          class="item-container _isExpandable" 
          :class="{ '_isPrivate': link.is_private, '_isFailed': link.is_failed, '_isPending': link.is_pending, '_active': link.showDetails }"
          >
          <div 
            class="row item-row row-no-bleed _isDraggable" 
            :data-link_id="link.guid" 
            @mousedown.stop="(e) => handleMouseDown(e, link)"
            @mouseup.stop="(e) => handleMouseUp(e, link)"
          >
            <div class="row">
              <div class="col col-sm-6 col-md-60 item-title-col">
                <button
                  aria-label="Show Details for Link {{ link.guid }}"
                  class="_visuallyHidden toggle-details expand-details"
                  title="Show Link Details for Link {{ link.guid }}"
                  @click.stop="(e) => toggleLinkDetails(e, link)"
                  v-if="!link.showDetails"
                ></button>

                <button
                  aria-label="Hide Details for Link {{ link.guid }}"
                  class="toggle-details collapse-details"
                  title="Hide Link Details for Link {{ link.guid }}"
                  @click.stop="(e) => toggleLinkDetails(e, link)"
                  v-if="link.showDetails"
                ></button>

                <div v-if="link.is_pending" class="failed_header">Capture In Progress</div>
                <div v-if="link.is_failed" class="failed_header">Capture Failed</div>
                <div v-if="link.is_private" class="item-private">
                  <span class="ui-private">[private] </span>
                  <span class="private-hint">Private record</span>
                </div>
                <div class="item-title">
                  <span>{{ link.title }}</span>
                </div>
                <div class="item-subtitle">
                  <a :href="link.url" target="_blank" class="item-link-original no-drag">
                    {{ truncateChars(link.url, 200) }}
                  </a>
                </div>
              </div>
              <div class="col col-sm-6 col-md-40 align-right item-permalink">
                <a v-if="link.delete_available" class="delete no-drag" :href="`/manage/delete-link/${link.guid}`">Delete</a>
                <a class="perma no-drag" :href="`//${link.local_url}`" target="_blank">{{ link.local_url }}</a>
              </div>
            </div>
            <div class="row item-secondary">
              <div class="col col-sm-5 pull-right sm-align-right">
                <span class="item-date"><span class="label">Created </span>{{ link.creation_timestamp_formatted }}</span>
              </div>
            </div>
          </div>

          <div class="row item-details" v-if="link.showDetails" style="display: block">
            <div class="col-sm-7">
              <div class="form-group">
                <label :for="`link-title-${link.guid}`">Display title</label>
                <span class="title-save-status">{{ saveStatuses[`${link.guid}-title`] }}</span>
                <input 
                  type="text" 
                  class="link-title" 
                  :id="`link-title-${link.guid}`" 
                  v-model="link.title"
                  @input="e => handleInput(link.guid, 'title', e.target.value)"
                >
              </div>

              <div class="form-group">
                <label :for="`link-description-${link.guid}`">Display description</label>
                <span class="description-save-status">{{ saveStatuses[`${link.guid}-description`] }}</span>
                <input 
                  type="text" 
                  class="link-description" 
                  :id="`link-description-${link.guid}`" 
                  v-model="link.description"
                  @input="e => handleInput(link.guid, 'description', e.target.value)"
                >
              </div>

              <div class="form-group">
                <label :for="`link-notes-${link.guid}`">Notes</label>
                <span class="notes-save-status">{{ saveStatuses[`${link.guid}-notes`] }}</span>
                <textarea 
                  :id="`link-notes-${link.guid}`" 
                  class="link-notes" 
                  rows="6" 
                  v-model="link.notes"
                  @input="e => handleInput(link.guid, 'notes', e.target.value)"
                ></textarea>
                <span class="muted">
                  Notes are private to you and your organization(s)
                </span>
              </div>

              <div class="form-group">
                <label :for="`move-to-folder-${link.guid}`">Move to folder</label>
                <select 
                  :id="`move-to-folder-${link.guid}`" 
                  class="move-to-folder form-control"
                  @change="(e) => onFolderSelectionChange(e, link.guid)"
                >
                  <option value="" disabled> Please select a folder </option>
                  <option 
                    v-for="option in folderOptions" 
                    :key="option.value" 
                    :value="option.value" 
                    :selected="option.selected" 
                    :disabled="option.disabled" 
                    :data-orgid="option['data-orgid']"
                  >
                    {{ option.text }}
                  </option>
                </select>
              </div>

              <div class="form-group">
                <fieldset class="default-to-screenshot-view">
                  <legend>Default view
                    <span class="default_to_screenshot_view-save-status">{{ saveStatuses[`${link.guid}-default_to_screenshot_view`] }}</span>
                  </legend>
                  <label class="radio-inline">
                    <input 
                      type="radio" 
                      class="link-default-to-screenshot-view" 
                      name="default-view" 
                      :value="false" 
                      v-model="link.default_to_screenshot_view"
                      @change="e => handleInput(link.guid, 'default_to_screenshot_view', false)"
                    >
                    Standard
                  </label>
                  <label class="radio-inline">
                    <input 
                      type="radio" 
                      class="link-default-to-screenshot-view" 
                      name="default-view" 
                      :value="true" 
                      v-model="link.default_to_screenshot_view"
                      @change="e => handleInput(link.guid, 'default_to_screenshot_view', true)"
                    >
                    Screenshot
                  </label>
                </fieldset>
                <span class="muted">
                  Default view preference is private to you and your organization(s)
                </span>
              </div>
            </div>
            <div class="col-sm-5 link-stats">
              <div><span><strong>Created by:</strong> {{ link.created_by.full_name }}</span></div>
            </div>
          </div>
        </div>
      </template>
      <template v-else>
        <div class="row item-row row-no-bleed">
          <div class="row">
            <div class="col col-xs-12">
              <div class="item-title">
                <p class="item-notification">This is an empty folder</p>
              </div>
            </div>
          </div>
        </div>
      </template>
      <!-- do this as an empty div so we can CSS transition -->
      <Transition name="loading">
        <div v-if="loading" class="links-loading-more">Loading links...</div>
      </Transition>
    </div>
  </div>
</template>

<style scoped>
.loading-enter-active {
  transition-delay: 2s;
}
</style>