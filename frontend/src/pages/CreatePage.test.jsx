import { act, screen, waitFor, within } from '@testing-library/react'
import { describe, expect, it, vi } from 'vitest'
import {
  abortableFetch,
  deferred,
  jsonResponse,
  mockFetch,
  renderApp,
  videoResponse,
} from '../test/utils'

async function fillForm(user, overrides = {}) {
  const values = {
    subreddit: 'AITA',
    title: 'AITA for testing my app?',
    body: 'I wrote so many tests that my laptop got warm.',
    ...overrides,
  }
  if (values.subreddit) await user.type(screen.getByLabelText('Subreddit'), values.subreddit)
  if (values.title) await user.type(screen.getByLabelText('Post title'), values.title)
  if (values.body) await user.type(screen.getByLabelText('Body'), values.body)
  return values
}

const submit = (user) => user.click(screen.getByRole('button', { name: 'Generate video' }))
const sentBody = (fetchMock, call = 0) => JSON.parse(fetchMock.mock.calls[call][1].body)

describe('initial state', () => {
  it('starts with an empty form and Subway Surfers selected', () => {
    renderApp()
    expect(screen.getByLabelText('Subreddit')).toHaveValue('')
    expect(screen.getByLabelText('Post title')).toHaveValue('')
    expect(screen.getByLabelText('Body')).toHaveValue('')
    expect(screen.getByRole('radio', { name: /Subway Surfers/ })).toBeChecked()
    expect(screen.getByText('Your short will appear here')).toBeInTheDocument()
  })

  it('offers three background videos', () => {
    renderApp()
    const group = screen.getByRole('radiogroup', { name: 'Background video' })
    expect(within(group).getAllByRole('radio')).toHaveLength(3)
  })

  it('shows a length hint before anything is typed', () => {
    renderApp()
    expect(screen.getByText(/roughly 140 words/)).toBeInTheDocument()
  })
})

describe('editing', () => {
  it('counts words and estimates narration length', async () => {
    const { user } = renderApp()
    await user.type(screen.getByLabelText('Post title'), 'One two')
    await user.type(screen.getByLabelText('Body'), 'three four five')
    expect(screen.getByText(/5 words · about 0:04 of narration/)).toBeInTheDocument()
  })

  it('uses the singular for one word', async () => {
    const { user } = renderApp()
    await user.type(screen.getByLabelText('Body'), 'Hello')
    expect(screen.getByText(/^1 word ·/)).toBeInTheDocument()
  })

  it('switches background video', async () => {
    const { user } = renderApp()
    await user.click(screen.getByRole('radio', { name: /Minecraft parkour/ }))
    expect(screen.getByRole('radio', { name: /Minecraft parkour/ })).toBeChecked()
    expect(screen.getByRole('radio', { name: /Subway Surfers/ })).not.toBeChecked()
  })

  it('Clear resets every field', async () => {
    const { user } = renderApp()
    await fillForm(user)
    await user.click(screen.getByRole('radio', { name: /mobile game/ }))
    await user.click(screen.getByRole('button', { name: 'Clear' }))
    expect(screen.getByLabelText('Subreddit')).toHaveValue('')
    expect(screen.getByLabelText('Post title')).toHaveValue('')
    expect(screen.getByLabelText('Body')).toHaveValue('')
    expect(screen.getByRole('radio', { name: /Subway Surfers/ })).toBeChecked()
  })
})

describe('client-side validation', () => {
  it('blocks submission and flags every empty field', async () => {
    const fetchMock = mockFetch()
    const { user } = renderApp()
    await submit(user)

    expect(fetchMock).not.toHaveBeenCalled()
    expect(screen.getByText('Enter a subreddit')).toBeInTheDocument()
    expect(screen.getByText('Enter the post title')).toBeInTheDocument()
    expect(screen.getByText('Paste the body of the post')).toBeInTheDocument()
    expect(screen.getByLabelText('Subreddit')).toHaveAttribute('aria-invalid', 'true')
    expect(screen.getByLabelText('Subreddit')).toHaveAccessibleDescription('Enter a subreddit')
  })

  it('treats whitespace as empty', async () => {
    const fetchMock = mockFetch()
    const { user } = renderApp()
    await fillForm(user, { title: '   ' })
    await submit(user)
    expect(fetchMock).not.toHaveBeenCalled()
    expect(screen.getByText('Enter the post title')).toBeInTheDocument()
    expect(screen.queryByText('Enter a subreddit')).not.toBeInTheDocument()
  })

  it('clears a field error as soon as that field is edited', async () => {
    mockFetch()
    const { user } = renderApp()
    await submit(user)
    await user.type(screen.getByLabelText('Subreddit'), 'x')
    expect(screen.queryByText('Enter a subreddit')).not.toBeInTheDocument()
    expect(screen.getByText('Enter the post title')).toBeInTheDocument()
  })
})

describe('submitting', () => {
  it('sends the backend payload', async () => {
    const fetchMock = mockFetch(() => Promise.resolve(videoResponse()))
    const { user } = renderApp()
    await fillForm(user, { subreddit: 'r/tifu', title: '  TIFU by testing  ' })
    await user.click(screen.getByRole('radio', { name: /Minecraft parkour/ }))
    await submit(user)

    expect(fetchMock).toHaveBeenCalledOnce()
    expect(fetchMock.mock.calls[0][0]).toBe('http://127.0.0.1:8000/shorts/create/')
    expect(sentBody(fetchMock)).toEqual({
      subreddit: 'tifu',
      post_title: 'TIFU by testing',
      content: 'I wrote so many tests that my laptop got warm.',
      file_name: 'TIFU by testing',
      video_choice: 'minecraftParkor',
    })
  })

  it('shows a loading state and locks the form while generating', async () => {
    const pending = deferred()
    mockFetch(() => pending.promise)
    const { user } = renderApp()
    await fillForm(user)
    await submit(user)

    expect(screen.getByRole('progressbar', { name: 'Generating video' })).toBeInTheDocument()
    expect(screen.getByText('Generating your short')).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Generating…' })).toBeDisabled()
    expect(screen.getByRole('button', { name: 'Clear' })).toBeDisabled()
    expect(screen.getByLabelText('Post title')).toBeDisabled()
    expect(screen.getByRole('radio', { name: /Subway Surfers/ })).toBeDisabled()

    await act(async () => pending.resolve(videoResponse()))
  })

  it('shows elapsed time while generating', async () => {
    vi.useFakeTimers({ shouldAdvanceTime: true })
    const pending = deferred()
    mockFetch(() => pending.promise)
    const { user } = renderApp()
    await fillForm(user)
    await submit(user)

    expect(screen.getByText(/0:00 elapsed/)).toBeInTheDocument()
    await act(async () => vi.advanceTimersByTime(65_000))
    expect(screen.getByText(/1:05 elapsed/)).toBeInTheDocument()

    await act(async () => pending.resolve(videoResponse()))
  })

  it('cannot be submitted twice while generating', async () => {
    const pending = deferred()
    const fetchMock = mockFetch(() => pending.promise)
    const { user } = renderApp()
    await fillForm(user)
    await submit(user)
    await user.click(screen.getByRole('button', { name: 'Generating…' }))
    expect(fetchMock).toHaveBeenCalledOnce()
    await act(async () => pending.resolve(videoResponse()))
  })
})

describe('success', () => {
  async function generate() {
    mockFetch(() => Promise.resolve(videoResponse()))
    const utils = renderApp()
    await fillForm(utils.user)
    await submit(utils.user)
    await screen.findByTestId('result-video')
    return utils
  }

  it('plays the generated video', async () => {
    await generate()
    const video = screen.getByTestId('result-video')
    expect(video).toHaveAttribute('src', 'blob:mock-1')
    expect(video).toHaveAttribute('controls')
    expect(URL.createObjectURL).toHaveBeenCalledOnce()
  })

  it('offers a download link', async () => {
    await generate()
    const link = screen.getByRole('link', { name: 'Download' })
    expect(link).toHaveAttribute('href', 'blob:mock-1')
    expect(link).toHaveAttribute('download', 'short.mp4')
  })

  it('unlocks the form again', async () => {
    await generate()
    expect(screen.getByRole('button', { name: 'Generate video' })).toBeEnabled()
    expect(screen.getByLabelText('Post title')).toBeEnabled()
  })

  it('"Make another" resets the form and frees the video', async () => {
    const { user } = await generate()
    await user.click(screen.getByRole('button', { name: 'Make another' }))
    expect(screen.queryByTestId('result-video')).not.toBeInTheDocument()
    expect(screen.getByLabelText('Post title')).toHaveValue('')
    expect(URL.revokeObjectURL).toHaveBeenCalledWith('blob:mock-1')
  })

  it('frees the previous video when generating a new one', async () => {
    const { user } = await generate()
    await submit(user)
    await waitFor(() => expect(screen.getByTestId('result-video')).toHaveAttribute('src', 'blob:mock-2'))
    expect(URL.revokeObjectURL).toHaveBeenCalledWith('blob:mock-1')
  })

  it('frees the video when leaving the page', async () => {
    const { user } = await generate()
    mockFetch(() => Promise.resolve(jsonResponse([])))
    await user.click(screen.getByRole('link', { name: 'History' }))
    expect(URL.revokeObjectURL).toHaveBeenCalledWith('blob:mock-1')
  })
})

describe('errors', () => {
  it('maps backend validation errors onto fields', async () => {
    mockFetch(() =>
      Promise.resolve(
        jsonResponse(
          {
            detail: [
              { type: 'string_too_long', loc: ['subreddit'], msg: 'x' },
              { type: 'enum', loc: ['video_choice'], msg: 'y' },
            ],
          },
          422,
        ),
      ),
    )
    const { user } = renderApp()
    await fillForm(user)
    await submit(user)

    expect(await screen.findByRole('alert')).toHaveTextContent(/need fixing/)
    expect(screen.getByText('This is too long')).toBeInTheDocument()
    expect(screen.getByText('Choose a background video', { selector: '.field-error' })).toBeInTheDocument()
    expect(screen.getByLabelText('Subreddit')).toHaveAttribute('aria-invalid', 'true')
  })

  it('shows server error messages', async () => {
    mockFetch(() =>
      Promise.resolve(jsonResponse({ detail: "Background video for 'subwaySurfers' is missing" }, 500)),
    )
    const { user } = renderApp()
    await fillForm(user)
    await submit(user)
    expect(await screen.findByRole('alert')).toHaveTextContent(
      "Background video for 'subwaySurfers' is missing",
    )
    expect(screen.getByText('Your short will appear here')).toBeInTheDocument()
  })

  it('explains when the backend is down', async () => {
    mockFetch(() => Promise.reject(new TypeError('Failed to fetch')))
    const { user } = renderApp()
    await fillForm(user)
    await submit(user)
    expect(await screen.findByRole('alert')).toHaveTextContent(/Is the backend running/)
  })

  it('keeps what the user typed after an error', async () => {
    mockFetch(() => Promise.resolve(jsonResponse({ detail: 'boom' }, 500)))
    const { user } = renderApp()
    const values = await fillForm(user)
    await submit(user)
    await screen.findByRole('alert')
    expect(screen.getByLabelText('Post title')).toHaveValue(values.title)
    expect(screen.getByRole('button', { name: 'Generate video' })).toBeEnabled()
  })

  it('clears the error when retrying successfully', async () => {
    const fetchMock = mockFetch()
    fetchMock
      .mockResolvedValueOnce(jsonResponse({ detail: 'boom' }, 500))
      .mockResolvedValueOnce(videoResponse())
    const { user } = renderApp()
    await fillForm(user)
    await submit(user)
    await screen.findByRole('alert')
    await submit(user)
    await screen.findByTestId('result-video')
    expect(screen.queryByRole('alert')).not.toBeInTheDocument()
  })
})

describe('cancelling', () => {
  it('aborts the request and returns to the form', async () => {
    const fetchMock = abortableFetch()
    const { user } = renderApp()
    await fillForm(user)
    await submit(user)

    const signal = fetchMock.mock.calls[0][1].signal
    await user.click(screen.getByRole('button', { name: 'Cancel' }))

    expect(signal.aborted).toBe(true)
    expect(screen.getByRole('alert')).toHaveTextContent('Generation cancelled.')
    expect(screen.getByRole('button', { name: 'Generate video' })).toBeEnabled()
    expect(screen.queryByRole('progressbar')).not.toBeInTheDocument()
  })

  it('aborts an in-flight request when navigating away', async () => {
    const fetchMock = abortableFetch()
    const { user } = renderApp()
    await fillForm(user)
    await submit(user)
    const signal = fetchMock.mock.calls[0][1].signal

    fetchMock.mockImplementation(() => Promise.resolve(jsonResponse([])))
    await user.click(screen.getByRole('link', { name: 'History' }))
    expect(signal.aborted).toBe(true)
  })
})

describe('prefill from history', () => {
  const video = {
    id: 4,
    subreddit: 'tifu',
    post_title: 'TIFU by microwaving a fork',
    content: 'Sparks everywhere.',
    file_name: 'fork',
    video_choice: 'mobileGame',
  }

  it('fills the form from router state', () => {
    renderApp([{ pathname: '/', state: { prefill: video } }])
    expect(screen.getByLabelText('Subreddit')).toHaveValue('tifu')
    expect(screen.getByLabelText('Post title')).toHaveValue('TIFU by microwaving a fork')
    expect(screen.getByLabelText('Body')).toHaveValue('Sparks everywhere.')
    expect(screen.getByRole('radio', { name: /mobile game/ })).toBeChecked()
  })

  it('falls back to the default background for unknown choices', () => {
    renderApp([{ pathname: '/', state: { prefill: { ...video, video_choice: 'legacy' } } }])
    expect(screen.getByRole('radio', { name: /Subway Surfers/ })).toBeChecked()
  })

  it('tolerates missing fields', () => {
    renderApp([{ pathname: '/', state: { prefill: { id: 9 } } }])
    expect(screen.getByLabelText('Post title')).toHaveValue('')
  })
})
