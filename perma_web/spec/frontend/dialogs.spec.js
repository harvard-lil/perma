import { flushPromises, mount } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'
import { afterEach, describe, expect, it, vi } from 'vitest'
import CreateLinkBatch from '../../static/frontend/components/CreateLinkBatch.vue'
import Spinner from '../../static/frontend/components/Spinner.vue'
import UploadForm from '../../static/frontend/components/UploadForm.vue'
import { useGlobalStore } from '../../static/frontend/stores/globalStore'

// These dialogs render on the Bootstrap 3 `.modal`/`.close` class surface today and will be
// migrated to Bootstrap 5's `.btn-close`/`data-bs-*` surface later. Every assertion below targets
// Perma's own headings, labels, exposed methods, and rendered text, never a Bootstrap class or
// data-* attribute name, so this file stays valid across that migration.

const personalFolder = {
  id: 1,
  name: 'Personal Links',
  organization: null,
  sponsored_by: null,
  default_to_private: false,
  read_only: false,
}

const response = (data, options = {}) => ({
  ok: options.ok ?? true,
  status: options.status ?? 200,
  statusText: options.statusText ?? 'OK',
  json: vi.fn().mockResolvedValue(data),
})

// UploadForm's real FileInput opens a native file picker; stand in a control that emits a File.
const FileInputStub = {
  emits: ['update:modelValue'],
  setup(_, {emit}) {
    return {
      selectFile: () => emit('update:modelValue', new File(['content'], 'capture.pdf', {type: 'application/pdf'})),
    }
  },
  template: '<button class="file-select" type="button" @click="selectFile">Choose file</button>',
}

// The visible "x" glyph is aria-hidden; only the sr-only text is the button's accessible name.
// Matching on that text (rather than a class or data-attribute) survives the BS3 -> BS5 markup swap.
const closeButton = (wrapper) => wrapper.findAll('button').find(b => b.text().includes('Close'))

const configureStore = (folderId = 1) => {
  const pinia = createPinia()
  setActivePinia(pinia)
  const store = useGlobalStore(pinia)
  store.currentUser = {top_level_folders: [personalFolder]}
  store.selectedFolder = {
    folderId,
    orgId: null,
    sponsorId: null,
    path: folderId ? ['Personal Links'] : [],
    isPrivate: false,
    isReadOnly: false,
    isOutOfLinks: false,
  }
  return {pinia, store}
}

describe('UploadForm dialog', () => {
  afterEach(() => {
    vi.restoreAllMocks()
  })

  it('names its dialog with a heading, and the captureGUID prop switches the description and submit label', () => {
    const {pinia} = configureStore()
    const forNewLink = mount(UploadForm, {global: {plugins: [pinia]}})

    expect(forNewLink.get('h3').text()).toBe('Upload a file to Perma.cc')
    expect(forNewLink.text()).toContain('This will create a new Perma Link.')
    expect(forNewLink.get('button[type="submit"]').text()).toBe('Create a Perma Link')

    const forExistingCapture = mount(UploadForm, {props: {captureGUID: 'ABCD-1234'}, global: {plugins: [pinia]}})

    expect(forExistingCapture.get('h3').text()).toBe('Upload a file to Perma.cc')
    expect(forExistingCapture.text()).toContain('This will update the Perma Link you were trying to create.')
    expect(forExistingCapture.get('button[type="submit"]').text()).toBe('Upload')
  })

  it('opens via its exposed handleOpen, and its Close control -- reachable by name -- closes the dialog', () => {
    const {pinia} = configureStore()
    const wrapper = mount(UploadForm, {global: {plugins: [pinia]}})

    wrapper.vm.handleOpen()
    expect(wrapper.get('dialog').element.open).toBe(true)

    closeButton(wrapper).trigger('click')
    expect(wrapper.get('dialog').element.open).toBe(false)
  })

  it('also closes on Escape and on a backdrop click (a click landing on the dialog element itself)', async () => {
    const {pinia} = configureStore()
    const wrapper = mount(UploadForm, {global: {plugins: [pinia]}})

    wrapper.vm.handleOpen()
    await wrapper.get('dialog').trigger('keydown.esc')
    expect(wrapper.get('dialog').element.open).toBe(false)

    wrapper.vm.handleOpen()
    await wrapper.get('dialog').trigger('click')
    expect(wrapper.get('dialog').element.open).toBe(false)
  })

  it('label-associates its title, description, and URL fields', () => {
    const {pinia} = configureStore()
    const wrapper = mount(UploadForm, {global: {plugins: [pinia]}})

    for (const id of ['title', 'description', 'url']) {
      expect(wrapper.get(`label[for="${id}"]`).exists()).toBe(true)
      expect(wrapper.get(`#${id}`).exists()).toBe(true)
    }
    // FileInput's own missing id/label association is a pre-existing gap already pinned by
    // spec/frontend/forms-accessibility.spec.js; not re-asserted here.
  })

  it('never shows a loading spinner, because globalStore has no isLoading property anywhere', () => {
    // Pre-existing defect: the `v-if="globalStore.isLoading"` branch is dead code -- nothing in
    // the codebase ever sets globalStore.isLoading. Pinned as-is, not fixed.
    const {pinia} = configureStore()
    const wrapper = mount(UploadForm, {global: {plugins: [pinia]}})

    expect(wrapper.findComponent(Spinner).exists()).toBe(false)
  })

  it('guards against a resubmit while a request is in flight, then lifts the guard on close -- without clearing entered field values', async () => {
    const {pinia} = configureStore()
    const fetchMock = vi.spyOn(globalThis, 'fetch')
      .mockReturnValueOnce(new Promise(() => {})) // first request: left permanently in flight
      .mockReturnValueOnce(new Promise(() => {})) // second request: also left in flight
    const wrapper = mount(UploadForm, {
      global: {plugins: [pinia], stubs: {FileInput: FileInputStub}},
    })

    wrapper.vm.handleOpen()
    await wrapper.get('#url').setValue('https://example.com/upload')
    await wrapper.get('.file-select').trigger('click')

    await wrapper.get('button[type="submit"]').trigger('click')
    expect(fetchMock).toHaveBeenCalledTimes(1)

    await wrapper.get('button[type="submit"]').trigger('click')
    expect(fetchMock).toHaveBeenCalledTimes(1) // still validating -- second click is a no-op

    closeButton(wrapper).trigger('click')
    expect(wrapper.get('dialog').element.open).toBe(false)

    wrapper.vm.handleOpen()
    expect(wrapper.get('#url').element.value).toBe('https://example.com/upload') // closing didn't clear the field

    await wrapper.get('button[type="submit"]').trigger('click')
    expect(fetchMock).toHaveBeenCalledTimes(2) // guard lifted by close, despite the first request never resolving
  })
})

describe('CreateLinkBatch dialog', () => {
  afterEach(() => {
    vi.restoreAllMocks()
  })

  it('names its dialog "Create a Link Batch" by default, with its input controls visible', () => {
    const {pinia} = configureStore()
    const wrapper = mount(CreateLinkBatch, {global: {plugins: [pinia]}})

    expect(wrapper.get('h3').text()).toBe('Create a Link Batch')
    expect(wrapper.get('#batch-create-input').exists()).toBe(true)
  })

  it('opens via its exposed handleOpen, and its Close control -- reachable by name -- closes the dialog', () => {
    const {pinia} = configureStore()
    const wrapper = mount(CreateLinkBatch, {global: {plugins: [pinia]}})

    wrapper.vm.handleOpen()
    expect(wrapper.get('dialog').element.open).toBe(true)

    closeButton(wrapper).trigger('click')
    expect(wrapper.get('dialog').element.open).toBe(false)
  })

  it('also closes on Escape and on a backdrop click (a click landing on the dialog element itself)', async () => {
    const {pinia} = configureStore()
    const wrapper = mount(CreateLinkBatch, {global: {plugins: [pinia]}})

    wrapper.vm.handleOpen()
    await wrapper.get('dialog').trigger('keydown.esc')
    expect(wrapper.get('dialog').element.open).toBe(false)

    wrapper.vm.handleOpen()
    await wrapper.get('dialog').trigger('click')
    expect(wrapper.get('dialog').element.open).toBe(false)
  })

  it('label-associates the URLs field, but the Folder field label has no for/id association today', () => {
    const {pinia} = configureStore()
    const wrapper = mount(CreateLinkBatch, {global: {plugins: [pinia]}})

    expect(wrapper.get('label[for="userSubmittedLinks"]').exists()).toBe(true)
    expect(wrapper.get('#userSubmittedLinks').exists()).toBe(true)

    // Pre-existing defect: CreateLinkBatch never passes an `id` to the BaseInput wrapping
    // FolderSelect, so its "Folder" <label> renders with no `for` attribute at all. FolderSelect's
    // own toggle button does not separately self-label, so this is a real gap. Pinned, not fixed.
    const folderLabel = wrapper.findAll('label').find(l => l.text().startsWith('Folder'))
    expect(folderLabel.attributes('for')).toBeUndefined()
  })

  it('hides the input section and shows a loading spinner while a batch request is in flight', async () => {
    const {pinia} = configureStore()
    vi.spyOn(globalThis, 'fetch').mockReturnValue(new Promise(() => {})) // never resolves
    const wrapper = mount(CreateLinkBatch, {global: {plugins: [pinia]}})

    await wrapper.get('#userSubmittedLinks').setValue('https://example.com')
    await wrapper.get('.form-buttons .btn').trigger('click')

    // Unlike UploadForm's silent no-op guard, the entire input/button section is removed from the
    // DOM here -- there is no control left to click a second time.
    expect(wrapper.find('#batch-create-input').exists()).toBe(false)
    expect(wrapper.findComponent(Spinner).exists()).toBe(true)
  })

  it("opens directly into an existing batch's details via showBatchHistory, without updating the default dialog heading", async () => {
    const {pinia, store} = configureStore()
    store.components.linkList = {fetchLinks: vi.fn()}
    const fetchMock = vi.spyOn(globalThis, 'fetch').mockResolvedValue(response({
      target_folder: {name: 'Personal Links'},
      capture_jobs: [{
        guid: 'ABCD-1234',
        status: 'completed',
        message: '{}',
        step_count: 6,
        submitted_url: 'https://example.com/one',
        title: 'First link',
        user_deleted: false,
      }],
    }))
    const wrapper = mount(CreateLinkBatch, {global: {plugins: [pinia]}})

    wrapper.vm.showBatchHistory(99)
    expect(wrapper.get('dialog').element.open).toBe(true)
    await flushPromises()

    expect(fetchMock).toHaveBeenCalledWith('/api/v1/archives/batches/99', {headers: {'X-CSRFToken': undefined}})
    expect(wrapper.text()).toContain('These Perma Links were added to Personal Links')

    // Pre-existing defect: showBatchHistory never sets batchDialogTitle, so the heading still
    // reads "Create a Link Batch" even though an existing batch's details are being shown.
    expect(wrapper.get('h3').text()).toBe('Create a Link Batch')
  })

  it('fully resets on close -- clearing the entered URLs -- unlike UploadForm, which leaves its fields untouched', async () => {
    const {pinia} = configureStore()
    const wrapper = mount(CreateLinkBatch, {global: {plugins: [pinia]}})

    wrapper.vm.handleOpen()
    await wrapper.get('#userSubmittedLinks').setValue('https://example.com/one')

    await closeButton(wrapper).trigger('click')
    expect(wrapper.get('dialog').element.open).toBe(false)

    wrapper.vm.handleOpen()
    expect(wrapper.get('#userSubmittedLinks').element.value).toBe('')
    expect(wrapper.get('h3').text()).toBe('Create a Link Batch')
  })
})
