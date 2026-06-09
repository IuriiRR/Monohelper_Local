import { describe, expect, it } from 'vitest'
import { formatCurrency, formatDate, formatDateTime } from './format'

describe('formatCurrency', () => {
  it('divides integer minor units by 100 and formats as UAH', () => {
    const expected = new Intl.NumberFormat('uk-UA', {
      style: 'currency',
      currency: 'UAH',
      minimumFractionDigits: 2,
    }).format(1200)
    expect(formatCurrency(120000)).toBe(expected)
  })

  it('includes the hryvnia symbol', () => {
    expect(formatCurrency(100)).toContain('₴')
  })

  it('handles zero', () => {
    expect(formatCurrency(0)).toContain('0')
  })
})

describe('formatDate / formatDateTime', () => {
  it('treats the input as Unix seconds', () => {
    const unix = 1_746_144_000 // 2025-05-02T00:00:00Z
    expect(formatDate(unix)).toBe(new Date(unix * 1000).toLocaleDateString())
    expect(formatDateTime(unix)).toBe(new Date(unix * 1000).toLocaleString())
  })
})
