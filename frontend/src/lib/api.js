export const API_URL = (import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000').replace(/\/+$/, '')

export const VIDEO_CHOICES = [
  { value: 'subwaySurfers', label: 'Subway Surfers', description: 'Endless runner' },
  { value: 'minecraftParkor', label: 'Minecraft parkour', description: 'Blocky jumps' },
  { value: 'mobileGame', label: 'Satisfying mobile game', description: 'Calm and colourful' },
]

export const FIELD_LIMITS = { subreddit: 255 }

const WORDS_PER_SECOND = 2.5

export class ApiError extends Error {
  constructor(message, { status = 0, fieldErrors = {} } = {}) {
    super(message)
    this.name = 'ApiError'
    this.status = status
    this.fieldErrors = fieldErrors
  }
}

export function choiceLabel(value) {
  return VIDEO_CHOICES.find((choice) => choice.value === value)?.label ?? value
}

export function normalizeSubreddit(value) {
  return value.trim().replace(/^\/?r\//i, '')
}

/** The backend only uses file_name to label its temp folder. */
export function makeFileName(title, content) {
  const source = (title || content || '').trim()
  return source.slice(0, 40).trim() || 'short'
}

export function estimateSeconds(...texts) {
  const words = texts.join(' ').trim().split(/\s+/).filter(Boolean).length
  return Math.ceil(words / WORDS_PER_SECOND)
}

export function formatDuration(totalSeconds) {
  const seconds = Math.max(0, Math.round(totalSeconds))
  const minutes = Math.floor(seconds / 60)
  return `${minutes}:${String(seconds % 60).padStart(2, '0')}`
}

export function validateForm(form) {
  const errors = {}
  if (!normalizeSubreddit(form.subreddit)) errors.subreddit = 'Enter a subreddit'
  else if (normalizeSubreddit(form.subreddit).length > FIELD_LIMITS.subreddit)
    errors.subreddit = `Keep it under ${FIELD_LIMITS.subreddit} characters`
  if (!form.postTitle.trim()) errors.postTitle = 'Enter the post title'
  if (!form.content.trim()) errors.content = 'Paste the body of the post'
  if (!VIDEO_CHOICES.some((choice) => choice.value === form.videoChoice))
    errors.videoChoice = 'Choose a background video'
  return errors
}

const BACKEND_FIELDS = {
  subreddit: 'subreddit',
  post_title: 'postTitle',
  content: 'content',
  file_name: 'postTitle',
  video_choice: 'videoChoice',
}

function friendlyMessage(error) {
  switch (error.type) {
    case 'missing':
    case 'string_too_short':
      return 'This field is required'
    case 'string_too_long':
      return 'This is too long'
    case 'enum':
      return 'Choose a background video'
    default:
      return error.msg || 'This value is invalid'
  }
}

export async function parseError(response) {
  let body = null
  try {
    body = await response.json()
  } catch {
    // Not JSON (e.g. a proxy error page); fall through to the generic message.
  }
  const detail = body?.detail

  if (response.status === 422 && Array.isArray(detail)) {
    const fieldErrors = {}
    for (const error of detail) {
      const field = BACKEND_FIELDS[error.loc?.[error.loc.length - 1]]
      if (field && !fieldErrors[field]) fieldErrors[field] = friendlyMessage(error)
    }
    return new ApiError('Some details need fixing before we can make your video.', {
      status: 422,
      fieldErrors,
    })
  }
  if (typeof detail === 'string' && detail) {
    return new ApiError(detail, { status: response.status })
  }
  return new ApiError(`Something went wrong on our side (error ${response.status}).`, {
    status: response.status,
  })
}

async function request(path, options = {}, fetchImpl = fetch) {
  let response
  try {
    response = await fetchImpl(`${API_URL}${path}`, options)
  } catch (error) {
    if (error?.name === 'AbortError') throw error
    throw new ApiError(`Couldn't reach the server at ${API_URL}. Is the backend running?`)
  }
  if (!response.ok) throw await parseError(response)
  return response
}

export function toPayload(form) {
  return {
    subreddit: normalizeSubreddit(form.subreddit),
    post_title: form.postTitle.trim(),
    content: form.content.trim(),
    file_name: makeFileName(form.postTitle, form.content),
    video_choice: form.videoChoice,
  }
}

export async function createShort(form, { signal, fetchImpl } = {}) {
  const response = await request(
    '/shorts/create/',
    {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(toPayload(form)),
      signal,
    },
    fetchImpl,
  )
  return response.blob()
}

export async function listShorts({ signal, fetchImpl } = {}) {
  const response = await request('/shorts/all/', { signal }, fetchImpl)
  const videos = await response.json()
  return [...videos].sort((a, b) => b.id - a.id)
}
