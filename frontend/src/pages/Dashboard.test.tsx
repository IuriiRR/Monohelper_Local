import { describe, expect, it } from 'vitest'
import { screen } from '@testing-library/react'
import { Dashboard } from './Dashboard'
import { renderWithProviders } from '../test/utils'

describe('Dashboard', () => {
  it('renders the Monthly Report heading', () => {
    renderWithProviders(<Dashboard />)
    expect(screen.getByText('Monthly Report')).toBeInTheDocument()
  })
})
