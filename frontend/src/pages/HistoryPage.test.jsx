import { act, screen, within } from '@testing-library/react'
import { describe, expect, it } from 'vitest'
import { SAMPLE_VIDEOS, deferred, jsonResponse, mockFetch, renderApp } from '../test/utils'

const titles = () =>
  screen.getAllByRole('heading', { level: 2 }).map((heading) => heading.textContent)

describe('history page', () => {
  it('shows a loading state first', async () => {
    const pending = deferred()
    mockFetch(() => pending.promise)
    renderApp(['/history'])
    expect(screen.getByRole('status')).toHaveTextContent('Loading your history')
    await act(async () => pending.resolve(jsonResponse([])))
  })

  it('requests the backend list', async () => {
    const fetchMock = mockFetch(() => Promise.resolve(jsonResponse([])))
    renderApp(['/history'])
    await screen.findByText('Nothing here yet')
    expect(fetchMock.mock.calls[0][0]).toBe('http://127.0.0.1:8000/shorts/all/')
  })

  it('lists posts newest first', async () => {
    mockFetch(() => Promise.resolve(jsonResponse(SAMPLE_VIDEOS)))
    renderApp(['/history'])
    await screen.findByText('TIFU by microwaving a fork')
    expect(titles()).toEqual([
      'My roommate eats my food',
      'TIFU by microwaving a fork',
      'Old post about a wedding',
    ])
  })

  it('shows subreddit, background and snippet for each post', async () => {
    mockFetch(() => Promise.resolve(jsonResponse(SAMPLE_VIDEOS)))
    renderApp(['/history'])
    const item = (await screen.findByText('TIFU by microwaving a fork')).closest('li')
    expect(within(item).getByText('r/tifu · Satisfying mobile game')).toBeInTheDocument()
    expect(within(item).getByText('Sparks everywhere.')).toBeInTheDocument()
  })

  it('shows unknown legacy background values as-is', async () => {
    mockFetch(() => Promise.resolve(jsonResponse(SAMPLE_VIDEOS)))
    renderApp(['/history'])
    expect(await screen.findByText('r/relationships · legacyChoice')).toBeInTheDocument()
  })

  it('shows the post count', async () => {
    mockFetch(() => Promise.resolve(jsonResponse(SAMPLE_VIDEOS)))
    renderApp(['/history'])
    expect(await screen.findByText('3 of 3 posts')).toBeInTheDocument()
  })

  it('uses the singular for one post', async () => {
    mockFetch(() => Promise.resolve(jsonResponse([SAMPLE_VIDEOS[0]])))
    renderApp(['/history'])
    expect(await screen.findByText('1 of 1 post')).toBeInTheDocument()
  })

  it('shows an empty state with a link to create', async () => {
    mockFetch(() => Promise.resolve(jsonResponse([])))
    const { user } = renderApp(['/history'])
    await user.click(await screen.findByRole('link', { name: 'Create your first short' }))
    expect(screen.getByTestId('location')).toHaveTextContent(/^\/$/)
  })

  it('shows errors and retries', async () => {
    const fetchMock = mockFetch()
    fetchMock
      .mockRejectedValueOnce(new TypeError('Failed to fetch'))
      .mockResolvedValueOnce(jsonResponse(SAMPLE_VIDEOS))
    const { user } = renderApp(['/history'])

    expect(await screen.findByRole('alert')).toHaveTextContent(/Is the backend running/)
    await user.click(screen.getByRole('button', { name: 'Try again' }))
    expect(await screen.findByText('TIFU by microwaving a fork')).toBeInTheDocument()
    expect(fetchMock).toHaveBeenCalledTimes(2)
  })

  it('shows server error details', async () => {
    mockFetch(() => Promise.resolve(jsonResponse({ detail: 'Database is locked' }, 500)))
    renderApp(['/history'])
    expect(await screen.findByRole('alert')).toHaveTextContent('Database is locked')
  })

  it('aborts the request when leaving the page', async () => {
    const fetchMock = mockFetch(() => new Promise(() => {}))
    const { user } = renderApp(['/history'])
    const signal = fetchMock.mock.calls[0][1].signal
    await user.click(screen.getByRole('link', { name: 'Create' }))
    expect(signal.aborted).toBe(true)
  })
})

describe('search', () => {
  async function setup() {
    mockFetch(() => Promise.resolve(jsonResponse(SAMPLE_VIDEOS)))
    const utils = renderApp(['/history'])
    await screen.findByText('TIFU by microwaving a fork')
    return utils
  }

  it.each([
    ['fork', ['TIFU by microwaving a fork']],
    ['FORK', ['TIFU by microwaving a fork']],
    ['aita', ['Old post about a wedding']],
    ['leftovers', ['My roommate eats my food']],
    ['  wedding  ', ['Old post about a wedding']],
  ])('filters by %j', async (query, expected) => {
    const { user } = await setup()
    await user.type(screen.getByRole('searchbox', { name: 'Search posts' }), query)
    expect(titles()).toEqual(expected)
  })

  it('updates the count', async () => {
    const { user } = await setup()
    await user.type(screen.getByRole('searchbox'), 'fork')
    expect(screen.getByText('1 of 3 posts')).toBeInTheDocument()
  })

  it('shows a no-results message', async () => {
    const { user } = await setup()
    await user.type(screen.getByRole('searchbox'), 'zebra')
    expect(screen.getByText(/No posts match/)).toHaveTextContent('No posts match “zebra”.')
    expect(screen.queryByRole('list')).not.toBeInTheDocument()
  })

  it('restores everything when the search is cleared', async () => {
    const { user } = await setup()
    const box = screen.getByRole('searchbox')
    await user.type(box, 'fork')
    await user.clear(box)
    expect(titles()).toHaveLength(3)
  })
})

describe('use again', () => {
  it('opens the create page prefilled with that post', async () => {
    mockFetch(() => Promise.resolve(jsonResponse(SAMPLE_VIDEOS)))
    const { user } = renderApp(['/history'])
    await user.click(
      await screen.findByRole('button', { name: 'Use "TIFU by microwaving a fork" again' }),
    )

    expect(screen.getByTestId('location')).toHaveTextContent(/^\/$/)
    expect(screen.getByLabelText('Subreddit')).toHaveValue('tifu')
    expect(screen.getByLabelText('Post title')).toHaveValue('TIFU by microwaving a fork')
    expect(screen.getByLabelText('Body')).toHaveValue('Sparks everywhere.')
    expect(screen.getByRole('radio', { name: /mobile game/ })).toBeChecked()
  })

  it('has a button for every post', async () => {
    mockFetch(() => Promise.resolve(jsonResponse(SAMPLE_VIDEOS)))
    renderApp(['/history'])
    await screen.findByText('TIFU by microwaving a fork')
    expect(screen.getAllByRole('button', { name: /^Use ".*" again$/ })).toHaveLength(3)
  })
})
