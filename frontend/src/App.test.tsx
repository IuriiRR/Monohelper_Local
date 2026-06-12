import { describe, it, expect } from 'vitest'
import { render, screen, act } from '@testing-library/react'
import { MemoryRouter, Route, Routes, useLocation } from 'react-router-dom'
import { MantineProvider } from '@mantine/core'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { UnauthorizedRedirect } from './App'

function LocationDisplay() {
  return <div data-testid="location">{useLocation().pathname}</div>
}

function renderWithRouter(initialPath: string) {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  render(
    <MantineProvider>
      <QueryClientProvider client={qc}>
        <MemoryRouter initialEntries={[initialPath]}>
          <UnauthorizedRedirect />
          <Routes>
            <Route path="*" element={<LocationDisplay />} />
          </Routes>
        </MemoryRouter>
      </QueryClientProvider>
    </MantineProvider>,
  )
}

describe('UnauthorizedRedirect', () => {
  it('navigates to /setup on api:unauthorized event', () => {
    renderWithRouter('/accounts')
    expect(screen.getByTestId('location').textContent).toBe('/accounts')
    act(() => window.dispatchEvent(new CustomEvent('api:unauthorized')))
    expect(screen.getByTestId('location').textContent).toBe('/setup')
  })

  it('does not navigate when already on /setup', () => {
    renderWithRouter('/setup')
    act(() => window.dispatchEvent(new CustomEvent('api:unauthorized')))
    expect(screen.getByTestId('location').textContent).toBe('/setup')
  })
})
