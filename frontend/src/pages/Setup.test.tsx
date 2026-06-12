import { describe, it, expect, beforeEach } from 'vitest'
import { screen, fireEvent } from '@testing-library/react'
import { Setup } from './Setup'
import { renderWithProviders } from '../test/utils'

describe('Setup page', () => {
  beforeEach(() => localStorage.clear())

  it('renders key input and action buttons', () => {
    renderWithProviders(<Setup />)
    expect(screen.getByLabelText(/api key/i)).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /save & continue/i })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /clear saved key/i })).toBeInTheDocument()
  })

  it('pre-fills input from localStorage', () => {
    localStorage.setItem('__api_key__', 'stored-key')
    renderWithProviders(<Setup />)
    expect(screen.getByLabelText(/api key/i)).toHaveValue('stored-key')
  })

  it('save button is disabled when input is empty', () => {
    renderWithProviders(<Setup />)
    expect(screen.getByRole('button', { name: /save & continue/i })).toBeDisabled()
  })

  it('clear button is disabled when no local key stored', () => {
    renderWithProviders(<Setup />)
    expect(screen.getByRole('button', { name: /clear saved key/i })).toBeDisabled()
  })

  it('saves key to localStorage on save', () => {
    renderWithProviders(<Setup />)
    fireEvent.change(screen.getByLabelText(/api key/i), { target: { value: 'my-key' } })
    fireEvent.click(screen.getByRole('button', { name: /save & continue/i }))
    expect(localStorage.getItem('__api_key__')).toBe('my-key')
  })

  it('clear button removes key from localStorage', () => {
    localStorage.setItem('__api_key__', 'key-to-clear')
    renderWithProviders(<Setup />)
    fireEvent.click(screen.getByRole('button', { name: /clear saved key/i }))
    expect(localStorage.getItem('__api_key__')).toBeNull()
  })
})
