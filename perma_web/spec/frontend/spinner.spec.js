// Spinner.vue is the sole spin.js consumer in Perma. These tests were written at sub-batch 5A
// against spin.js 2.3.2 and rewritten at 5D for 4.1.2, because the two versions express animation
// through structurally different DOM: v2 computed inline `-webkit-animation` in JavaScript and
// inserted its keyframes at runtime via CSSStyleSheet.insertRule, while v4 sets an unprefixed
// inline `animation` naming a keyframe defined in the separately-imported `spin.js/spin.css`.
//
// The migration's silent-failure mode is what these tests exist to catch: miss that CSS import and
// the spinner still mounts, still renders 15 lines, throws nothing -- it just stops animating.
// "An element mounted" would pass for that broken static asterisk, so every assertion below is on
// concrete animation evidence. The keyframes themselves cannot be asserted here (Vitest does not
// process CSS imports by default), so the companion guard lives in spec/build/webpack-contract.js,
// which checks the built stylesheet actually contains @keyframes spinner-line-fade-default.
// See .plans/plan_dependency-upgrade-roadmap-5.md, sub-batches 5A item 4 and 5D step 3.
import { mount } from '@vue/test-utils'
import { afterEach, describe, expect, it } from 'vitest'
import Spinner from '../../static/frontend/components/Spinner.vue'

const stubMatchMedia = (matches) => {
  window.matchMedia = (query) => ({
    matches: query.includes('prefers-reduced-motion') ? matches : false,
    media: query,
    onchange: null,
    addEventListener: () => {},
    removeEventListener: () => {},
    addListener: () => {},
    removeListener: () => {},
    dispatchEvent: () => false,
  })
}

// vitest.setup.js installs a permanent `matches: false` stub; restore that baseline after any
// test that overrides it to exercise the reduced-motion branch.
afterEach(() => {
  stubMatchMedia(false)
})

// v4 nests each line: the outer div carries position/rotation/radius, the inner one carries the
// colour and the animation.
const lineWrappers = (wrapper) => wrapper.element.querySelectorAll('.spinner > div')
const lineFills = (wrapper) => wrapper.element.querySelectorAll('.spinner > div > div')

describe('Spinner.vue', () => {
  it('renders spin.js\'s 15 default lines inside a single .spinner wrapper', () => {
    const wrapper = mount(Spinner)

    expect(wrapper.find('.spinner').exists()).toBe(true)
    expect(lineWrappers(wrapper)).toHaveLength(15)
  })

  it('sets aria-label and aria-live on the root element for the loading indicator', () => {
    const wrapper = mount(Spinner)

    expect(wrapper.attributes('aria-label')).toBe('Loading')
    expect(wrapper.attributes('aria-live')).toBe('polite')
  })

  it('spin.js 4 also marks its own element as a progressbar', () => {
    const wrapper = mount(Spinner)

    expect(wrapper.element.querySelector('.spinner').getAttribute('role')).toBe('progressbar')
  })

  it('the size prop drives the wrapper dimensions and the computed radius passed to spin.js', () => {
    const defaultSize = mount(Spinner)
    expect(defaultSize.attributes('style')).toContain('width: 32px')
    expect(defaultSize.attributes('style')).toContain('height: 32px')
    // radius = Math.max(1, Math.floor(size / 2 - 2)); size 32 -> 14. v4 encodes radius in each
    // line's translateX distance on the outer div; the first line (0deg) isolates it cleanly.
    expect(lineWrappers(defaultSize)[0].style.transform).toBe('rotate(0deg) translateX(14px)')

    const largeSize = mount(Spinner, {props: {size: 64}})
    expect(largeSize.attributes('style')).toContain('width: 64px')
    expect(largeSize.attributes('style')).toContain('height: 64px')
    expect(lineWrappers(largeSize)[0].style.transform).toBe('rotate(0deg) translateX(30px)') // floor(64/2-2)=30

    // the documented floor: radius is clamped to a minimum of 1
    const tinySize = mount(Spinner, {props: {size: 2}})
    expect(lineWrappers(tinySize)[0].style.transform).toBe('rotate(0deg) translateX(1px)')
  })

  it('the config prop overrides spin.js defaults, e.g. line count and color', () => {
    const wrapper = mount(Spinner, {props: {config: {lines: 5, color: '#ff0000'}}})

    expect(lineWrappers(wrapper)).toHaveLength(5)
    expect(lineFills(wrapper)[0].style.background).toBe('rgb(255, 0, 0)')
  })

  it('config also overrides values Spinner.vue itself computes, like the size-derived radius', () => {
    // `...config` is spread last in Spinner.vue's options object, so it wins even over radius,
    // which the component otherwise derives from the size prop.
    const wrapper = mount(Spinner, {props: {size: 64, config: {radius: 5}}})

    expect(lineWrappers(wrapper)[0].style.transform).toBe('rotate(0deg) translateX(5px)')
  })

  it('normal motion: every line animates the shipped keyframes, staggered so the ring appears to spin', () => {
    // prefersReducedMotion() reads window.matchMedia; vitest.setup.js's global stub already
    // returns matches:false, but state it explicitly since the next test overrides it.
    stubMatchMedia(false)
    const wrapper = mount(Spinner)

    const fills = lineFills(wrapper)
    expect(fills).toHaveLength(15)

    const delays = new Set()
    for (const fill of fills) {
      // duration is 1/speed, and speed is 0.5, so 2s. The name must be the keyframe spin.css
      // defines -- if it ever reads `none` here, the reduced-motion branch has leaked into the
      // normal path and nothing will animate.
      const match = fill.style.animation.match(/^2s linear (-?[\d.]+)s infinite spinner-line-fade-default$/)
      expect(fill.style.animation, 'line must animate the shipped keyframes').not.toBeNull()
      expect(match, `unexpected animation shorthand: ${fill.style.animation}`).not.toBeNull()
      delays.add(match[1])
    }

    // A distinct negative delay per line is what makes the ring read as rotating rather than
    // pulsing in unison; equal delays would still "animate" and still pass a laxer assertion.
    expect(delays.size).toBe(15)
    expect(fills[0].style.animation).toBe('2s linear -2s infinite spinner-line-fade-default')
  })

  it('reduced motion: lines carry a valid animation naming no keyframes, so nothing moves', () => {
    stubMatchMedia(true)
    const wrapper = mount(Spinner)

    const fills = lineFills(wrapper)
    expect(fills).toHaveLength(15)
    for (const fill of fills) {
      // Spinner.vue passes animation:'none' on this branch. The shorthand stays valid CSS and the
      // browser keeps it -- it simply names no keyframes. Under spin.js 2.3.2 the same no-motion
      // outcome came from passing speed:0, which produced the invalid duration "Infinitys" and got
      // the whole declaration discarded. Same result, but now stated rather than stumbled into.
      // spin.js still staggers the per-line delay; only the keyframe name changes.
      expect(fill.style.animation).toMatch(/^2s linear -?[\d.]+s infinite none$/)
      expect(fill.style.animation).not.toContain('spinner-line-fade')
    }
  })

  it('the two motion branches actually differ', () => {
    stubMatchMedia(false)
    const moving = lineFills(mount(Spinner))[0].style.animation
    stubMatchMedia(true)
    const still = lineFills(mount(Spinner))[0].style.animation

    expect(moving).not.toBe(still)
  })
})
