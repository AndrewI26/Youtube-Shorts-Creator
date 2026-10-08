import { render } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter, useLocation } from 'react-router-dom'
import { vi } from 'vitest'
import App from '../App'
import { ROUTER_FUTURE } from '../router'

export function LocationDisplay() {
  const location = useLocation()
  return <div data-testid="location">{location.pathname}</div>
}

export function renderApp(initialEntries = ['/']) {
  const user = userEvent.setup()
  const result = render(
    <MemoryRouter initialEntries={initialEntries} future={ROUTER_FUTURE}>
      <App />
      <LocationDisplay />
    </MemoryRouter>,
  )
  return { user, ...result }
}

export function jsonResponse(body, status = 200) {
  return new Response(JSON.stringify(body), {
    status,
    headers: { 'Content-Type': 'application/json' },
  })
}

export function videoResponse(bytes = 'fake-mp4') {
  return new Response(bytes, {
    status: 200,
    headers: { 'Content-Type': 'video/mp4' },
  })
}

export function deferred() {
  let resolve
  let reject
  const promise = new Promise((res, rej) => {
    resolve = res
    reject = rej
  })
  return { promise, resolve, reject }
}

export function mockFetch(impl) {
  const fn = vi.fn(impl)
  vi.stubGlobal('fetch', fn)
  return fn
}

export function abortableFetch() {
  return mockFetch(
    (_url, options) =>
      new Promise((_resolve, reject) => {
        options?.signal?.addEventListener('abort', () =>
          reject(new DOMException('Aborted', 'AbortError')),
        )
      }),
  )
}

export const SAMPLE_VIDEOS = [
  {
    id: 1,
    subreddit: 'AITA',
    post_title: 'Old post about a wedding',
    content: 'It was a long time ago.',
    file_name: 'old',
    video_choice: 'minecraftParkor',
  },
  {
    id: 2,
    subreddit: 'tifu',
    post_title: 'TIFU by microwaving a fork',
    content: 'Sparks everywhere.',
    file_name: 'fork',
    video_choice: 'mobileGame',
  },
  {
    id: 3,
    subreddit: 'relationships',
    post_title: 'My roommate eats my food',
    content: 'Every single day, the leftovers vanish.',
    file_name: 'food',
    video_choice: 'legacyChoice',
  },
]
