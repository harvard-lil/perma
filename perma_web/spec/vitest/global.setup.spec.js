import { describe, expect, it } from 'vitest'

describe('Test global.setup.js', () => {
  it('expects jquery to exist', () => {
    expect(globalThis.$).toBeDefined()
  })
})
