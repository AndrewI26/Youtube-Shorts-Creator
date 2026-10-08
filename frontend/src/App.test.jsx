import { screen, within } from '@testing-library/react'
import { describe, expect, it, vi } from 'vitest'
import { jsonResponse, mockFetch, renderApp } from './test/utils'

describe('routing', () => {
  it('renders the create page at /', () => {
    renderApp(['/'])
    expect(screen.getByRole('heading', { level: 1 })).toHaveTextContent(/Turn a Reddit post/)
    expect(screen.getByRole('form', { name: 'Create a short' })).toBeInTheDocument()
  })

  it('renders the history page at /history', async () => {
    mockFetch(() => Promise.resolve(jsonResponse([])))
    renderApp(['/history'])
    expect(screen.getByRole('heading', { level: 1 })).toHaveTextContent(/Every short/)
    expect(await screen.findByText('Nothing here yet')).toBeInTheDocument()
  })

  it.each(['/nope', '/history/123', '/shorts/create'])('renders a 404 page for %s', (path) => {
    renderApp([path])
    expect(screen.getByRole('heading', { level: 1 })).toHaveTextContent(/doesn.t exist/)
    expect(screen.getByRole('link', { name: 'Back to create' })).toHaveAttribute('href', '/')
  })

  it('keeps the nav on every page', () => {
    renderApp(['/nope'])
    const nav = screen.getByRole('navigation', { name: 'Main' })
    expect(within(nav).getByRole('link', { name: 'Create' })).toBeInTheDocument()
    expect(within(nav).getByRole('link', { name: 'History' })).toBeInTheDocument()
  })
})

describe('navigation', () => {
  it('marks the current page as active', () => {
    renderApp(['/'])
    const nav = screen.getByRole('navigation', { name: 'Main' })
    expect(within(nav).getByRole('link', { name: 'Create' })).toHaveAttribute('aria-current', 'page')
    expect(within(nav).getByRole('link', { name: 'History' })).not.toHaveAttribute('aria-current')
  })

  it('moves between pages client-side without reloading', async () => {
    mockFetch(() => Promise.resolve(jsonResponse([])))
    const { user } = renderApp(['/'])
    const nav = screen.getByRole('navigation', { name: 'Main' })

    await user.click(within(nav).getByRole('link', { name: 'History' }))
    expect(screen.getByTestId('location')).toHaveTextContent('/history')
    expect(within(nav).getByRole('link', { name: 'History' })).toHaveAttribute('aria-current', 'page')

    await user.click(within(nav).getByRole('link', { name: 'Create' }))
    expect(screen.getByTestId('location')).toHaveTextContent(/^\/$/)
  })

  it('goes home from the wordmark', async () => {
    const { user } = renderApp(['/nope'])
    await user.click(screen.getByRole('link', { name: 'Shorts Creator home' }))
    expect(screen.getByTestId('location')).toHaveTextContent(/^\/$/)
  })

  it('goes home from the 404 page', async () => {
    const { user } = renderApp(['/nope'])
    await user.click(screen.getByRole('link', { name: 'Back to create' }))
    expect(screen.getByRole('form', { name: 'Create a short' })).toBeInTheDocument()
  })

  it('keeps form state per visit (fresh form after navigating away)', async () => {
    mockFetch(() => Promise.resolve(jsonResponse([])))
    const { user } = renderApp(['/'])
    await user.type(screen.getByLabelText('Post title'), 'Draft')
    await user.click(screen.getByRole('link', { name: 'History' }))
    await user.click(screen.getByRole('link', { name: 'Create' }))
    expect(screen.getByLabelText('Post title')).toHaveValue('')
  })

  it('scrolls to the top when the route changes', async () => {
    mockFetch(() => Promise.resolve(jsonResponse([])))
    const scrollTo = vi.fn()
    vi.stubGlobal('scrollTo', scrollTo)
    const { user } = renderApp(['/'])
    scrollTo.mockClear()
    await user.click(screen.getByRole('link', { name: 'History' }))
    expect(scrollTo).toHaveBeenCalledWith(0, 0)
  })
})
