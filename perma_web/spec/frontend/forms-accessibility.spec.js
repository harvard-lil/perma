import { mount } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import BaseInput from '../../static/frontend/components/forms/BaseInput.vue'
import FileInput from '../../static/frontend/components/forms/FileInput.vue'
import FolderSelect from '../../static/frontend/components/FolderSelect.vue'
import TextAreaInput from '../../static/frontend/components/forms/TextAreaInput.vue'
import TextInput from '../../static/frontend/components/forms/TextInput.vue'
import { useGlobalStore } from '../../static/frontend/stores/globalStore'

const personalFolder = {
  id: 1,
  name: 'Personal Links',
  organization: null,
  sponsored_by: null,
  default_to_private: false,
  read_only: false,
}

const organizationFolder = {
  id: 2,
  name: 'Organization Links',
  organization: 9,
  sponsored_by: null,
  default_to_private: true,
  read_only: false,
}

describe('form field accessibility', () => {
  it('associates the label with its control via for/id, and shows the required indicator and description', () => {
    const wrapper = mount(BaseInput, {
      props: {id: 'my-field', name: 'My Field', description: 'Some help text', required: true},
      slots: {default: '<input id="my-field" />'},
    })

    const label = wrapper.get('label')
    expect(label.attributes('for')).toBe('my-field')
    expect(wrapper.get('input').attributes('id')).toBe('my-field')
    expect(label.text()).toContain('My Field')
    expect(label.text()).toContain('Some help text')
    expect(wrapper.get('.required-indicator').text()).toBe('*')
  })

  it('omits the required indicator when not required, and keeps the alert region present but empty without errors', () => {
    const wrapper = mount(BaseInput, {
      props: {id: 'x', name: 'X'},
      slots: {default: '<input id="x" />'},
    })

    expect(wrapper.find('.required-indicator').exists()).toBe(false)
    const errorRegion = wrapper.get('[role="alert"]')
    expect(errorRegion.attributes('aria-live')).toBe('assertive')
    expect(errorRegion.text()).toBe('')
  })

  it('renders every error string in the role="alert" / aria-live="assertive" region', () => {
    const wrapper = mount(BaseInput, {
      props: {id: 'x', name: 'X', error: ['Field is required', 'Must be unique']},
      slots: {default: '<input id="x" />'},
    })

    const errorRegion = wrapper.get('[role="alert"]')
    expect(errorRegion.attributes('aria-live')).toBe('assertive')
    expect(errorRegion.text()).toContain('Field is required')
    expect(errorRegion.text()).toContain('Must be unique')
  })

  it('wires TextInput id/for association, forwards errors through BaseInput, and emits update:modelValue', async () => {
    const wrapper = mount(TextInput, {
      props: {id: 'url', name: 'URL', required: true, error: ['Enter a valid URL'], modelValue: ''},
    })

    expect(wrapper.get('label').attributes('for')).toBe('url')
    expect(wrapper.get('input').attributes('id')).toBe('url')
    expect(wrapper.get('[role="alert"]').text()).toContain('Enter a valid URL')

    await wrapper.get('input').setValue('https://example.com')

    expect(wrapper.emitted('update:modelValue')[0]).toEqual(['https://example.com'])
  })

  it('wires TextAreaInput id/for association, description text, and emits update:modelValue', async () => {
    const wrapper = mount(TextAreaInput, {
      props: {id: 'notes', name: 'Notes', description: 'Private notes', modelValue: ''},
    })

    expect(wrapper.get('label').attributes('for')).toBe('notes')
    expect(wrapper.get('textarea').attributes('id')).toBe('notes')
    expect(wrapper.get('label').text()).toContain('Private notes')

    await wrapper.get('textarea').setValue('hello')

    expect(wrapper.emitted('update:modelValue')[0]).toEqual(['hello'])
  })

  it('renders FileInput required indicator, description, and errors via BaseInput', () => {
    const wrapper = mount(FileInput, {
      props: {id: 'capture-file', name: 'File', description: 'Upload a capture', required: true, error: ['A file is required']},
    })

    expect(wrapper.get('label').attributes('for')).toBe('capture-file')
    expect(wrapper.get('.required-indicator').text()).toBe('*')
    expect(wrapper.get('label').text()).toContain('Upload a capture')
    expect(wrapper.get('[role="alert"]').text()).toContain('A file is required')

    // Unlike TextInput/TextAreaInput's <input>/<textarea>, FileInput's <button> never receives
    // :id="props.id", so the label's for (asserted above) targets no element here -- a real a11y gap.
    expect(wrapper.get('button').attributes('id')).toBeUndefined()
  })
})

describe("FolderSelect's listbox accessibility", () => {
  beforeEach(() => {
    setActivePinia(createPinia())
  })

  it('toggles role="listbox", aria-expanded, and supports arrow-key navigation between options', async () => {
    const store = useGlobalStore()
    store.currentUser = {top_level_folders: [personalFolder, organizationFolder]}
    store.components.jstree = {handleSelectionChange: vi.fn()}
    // `attachTo` calls app.onUnmount(), a Vue 3.5+ API not present on this project's pinned Vue
    // 3.4.21 -- appending the mounted element manually gets real DOM attachment without it.
    const wrapper = mount(FolderSelect)
    document.body.appendChild(wrapper.element)

    const button = wrapper.get('button')
    expect(button.attributes('aria-expanded')).toBe('false')
    expect(wrapper.find('[role="listbox"]').exists()).toBe(false)

    await button.trigger('click')

    expect(button.attributes('aria-expanded')).toBe('true')
    const listbox = wrapper.get('[role="listbox"]')
    expect(listbox.attributes('aria-label')).toBe('Folder options')
    expect(wrapper.findAll('[role="option"]')).toHaveLength(2)

    await wrapper.get('[data-index="0"]').trigger('keydown.down')
    expect(document.activeElement).toBe(wrapper.get('[data-index="1"]').element)

    await button.trigger('click')

    expect(button.attributes('aria-expanded')).toBe('false')
    expect(wrapper.find('[role="listbox"]').exists()).toBe(false)

    wrapper.unmount()
  })
})
