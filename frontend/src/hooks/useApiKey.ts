import { useState } from 'react'

const STORAGE_KEY = '__api_key__'

export function useApiKey() {
  const [key, setKeyState] = useState(() => localStorage.getItem(STORAGE_KEY) ?? '')

  function setApiKey(value: string) {
    const trimmed = value.trim()
    localStorage.setItem(STORAGE_KEY, trimmed)
    setKeyState(trimmed)
  }

  function clearApiKey() {
    localStorage.removeItem(STORAGE_KEY)
    setKeyState('')
  }

  return { key, setApiKey, clearApiKey }
}
