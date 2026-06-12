import { describe, it, expect, beforeEach } from 'vitest'
import { renderHook, act } from '@testing-library/react'
import { useApiKey } from './useApiKey'

const KEY = '__api_key__'

describe('useApiKey', () => {
  beforeEach(() => localStorage.clear())

  it('initializes with stored localStorage value', () => {
    localStorage.setItem(KEY, 'existing-key')
    const { result } = renderHook(() => useApiKey())
    expect(result.current.key).toBe('existing-key')
  })

  it('initializes with empty string when nothing stored', () => {
    const { result } = renderHook(() => useApiKey())
    expect(result.current.key).toBe('')
  })

  it('setApiKey persists to localStorage and updates state', () => {
    const { result } = renderHook(() => useApiKey())
    act(() => result.current.setApiKey('new-key'))
    expect(localStorage.getItem(KEY)).toBe('new-key')
    expect(result.current.key).toBe('new-key')
  })

  it('setApiKey trims whitespace', () => {
    const { result } = renderHook(() => useApiKey())
    act(() => result.current.setApiKey('  padded  '))
    expect(result.current.key).toBe('padded')
    expect(localStorage.getItem(KEY)).toBe('padded')
  })

  it('clearApiKey removes from localStorage and resets state', () => {
    localStorage.setItem(KEY, 'to-clear')
    const { result } = renderHook(() => useApiKey())
    act(() => result.current.clearApiKey())
    expect(localStorage.getItem(KEY)).toBeNull()
    expect(result.current.key).toBe('')
  })
})
