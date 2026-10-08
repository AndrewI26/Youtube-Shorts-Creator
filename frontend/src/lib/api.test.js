import { describe, expect, it, vi } from 'vitest'
import {
  API_URL,
  ApiError,
  VIDEO_CHOICES,
  choiceLabel,
  createShort,
  estimateSeconds,
  formatDuration,
  listShorts,
  makeFileName,
  normalizeSubreddit,
  parseError,
  toPayload,
  validateForm,
} from './api'
import { jsonResponse, videoResponse } from '../test/utils'

const FORM = {
  subreddit: 'AITA',
  postTitle: 'AITA for testing?',
  content: 'I wrote a lot of tests.',
  videoChoice: 'subwaySurfers',
}

describe('constants', () => {
  it('defaults to the local backend', () => {
    expect(API_URL).toBe('http://127.0.0.1:8000')
  })

  it('offers exactly the backend video choices', () => {
    expect(VIDEO_CHOICES.map((c) => c.value)).toEqual([
      'subwaySurfers',
      'minecraftParkor',
      'mobileGame',
    ])
  })
})

describe('choiceLabel', () => {
  it.each([
    ['subwaySurfers', 'Subway Surfers'],
    ['minecraftParkor', 'Minecraft parkour'],
    ['mobileGame', 'Satisfying mobile game'],
  ])('labels %s', (value, label) => {
    expect(choiceLabel(value)).toBe(label)
  })

  it('falls back to the raw value for unknown choices', () => {
    expect(choiceLabel('legacy')).toBe('legacy')
  })
})

describe('normalizeSubreddit', () => {
  it.each([
    ['AITA', 'AITA'],
    ['  AITA  ', 'AITA'],
    ['r/AITA', 'AITA'],
    ['/r/AITA', 'AITA'],
    ['R/AITA', 'AITA'],
    ['r/', ''],
    ['', ''],
  ])('%j -> %j', (input, expected) => {
    expect(normalizeSubreddit(input)).toBe(expected)
  })
})

describe('makeFileName', () => {
  it('prefers the title', () => {
    expect(makeFileName('My title', 'body')).toBe('My title')
  })

  it('falls back to the content', () => {
    expect(makeFileName('', '  Body text  ')).toBe('Body text')
  })

  it('truncates to 40 characters without trailing space', () => {
    const name = makeFileName(`${'a'.repeat(39)} bbbbbb`, '')
    expect(name).toBe('a'.repeat(39))
  })

  it('never returns an empty name', () => {
    expect(makeFileName('   ', '')).toBe('short')
    expect(makeFileName(undefined, undefined)).toBe('short')
  })
})

describe('estimateSeconds', () => {
  it('assumes about 150 words per minute', () => {
    expect(estimateSeconds('word '.repeat(150))).toBe(60)
  })

  it('rounds up partial seconds', () => {
    expect(estimateSeconds('one two three')).toBe(2)
  })

  it('combines multiple texts', () => {
    expect(estimateSeconds('a b', 'c d', 'e')).toBe(2)
  })

  it('is zero for empty text', () => {
    expect(estimateSeconds('', '   ')).toBe(0)
  })
})

describe('formatDuration', () => {
  it.each([
    [0, '0:00'],
    [5, '0:05'],
    [59.4, '0:59'],
    [60, '1:00'],
    [125, '2:05'],
    [-3, '0:00'],
  ])('%s -> %s', (seconds, expected) => {
    expect(formatDuration(seconds)).toBe(expected)
  })
})

describe('validateForm', () => {
  it('accepts a complete form', () => {
    expect(validateForm(FORM)).toEqual({})
  })

  it('reports every missing field', () => {
    expect(
      validateForm({ subreddit: '', postTitle: '', content: '', videoChoice: '' }),
    ).toEqual({
      subreddit: 'Enter a subreddit',
      postTitle: 'Enter the post title',
      content: 'Paste the body of the post',
      videoChoice: 'Choose a background video',
    })
  })

  it.each(['subreddit', 'postTitle', 'content'])('treats whitespace-only %s as missing', (field) => {
    expect(validateForm({ ...FORM, [field]: '   \n ' })).toHaveProperty(field)
  })

  it('treats a bare r/ prefix as missing', () => {
    expect(validateForm({ ...FORM, subreddit: 'r/' })).toHaveProperty('subreddit')
  })

  it('limits subreddit length like the backend', () => {
    expect(validateForm({ ...FORM, subreddit: 'a'.repeat(255) })).toEqual({})
    expect(validateForm({ ...FORM, subreddit: 'a'.repeat(256) }).subreddit).toMatch(/255/)
  })

  it('rejects unknown video choices', () => {
    expect(validateForm({ ...FORM, videoChoice: 'tiktok' })).toHaveProperty('videoChoice')
  })
})

describe('toPayload', () => {
  it('maps the form to the backend field names', () => {
    expect(toPayload({ ...FORM, subreddit: ' r/AITA ', postTitle: ' Title ', content: ' Body ' })).toEqual({
      subreddit: 'AITA',
      post_title: 'Title',
      content: 'Body',
      file_name: 'Title',
      video_choice: 'subwaySurfers',
    })
  })
})

describe('parseError', () => {
  it('maps 422 validation errors onto form fields', async () => {
    const error = await parseError(
      jsonResponse(
        {
          detail: [
            { type: 'missing', loc: ['subreddit'], msg: 'Field required' },
            { type: 'string_too_short', loc: ['body', 'post_title'], msg: 'too short' },
            { type: 'enum', loc: ['video_choice'], msg: 'bad enum' },
            { type: 'string_too_long', loc: ['content'], msg: 'too long' },
          ],
        },
        422,
      ),
    )
    expect(error).toBeInstanceOf(ApiError)
    expect(error.status).toBe(422)
    expect(error.fieldErrors).toEqual({
      subreddit: 'This field is required',
      postTitle: 'This field is required',
      videoChoice: 'Choose a background video',
      content: 'This is too long',
    })
  })

  it('shows file_name errors on the title field, keeping the first error', async () => {
    const error = await parseError(
      jsonResponse(
        {
          detail: [
            { type: 'missing', loc: ['post_title'], msg: 'x' },
            { type: 'string_too_long', loc: ['file_name'], msg: 'y' },
          ],
        },
        422,
      ),
    )
    expect(error.fieldErrors).toEqual({ postTitle: 'This field is required' })
  })

  it('uses the backend message for unknown error types', async () => {
    const error = await parseError(
      jsonResponse({ detail: [{ type: 'weird', loc: ['content'], msg: 'Custom' }] }, 422),
    )
    expect(error.fieldErrors.content).toBe('Custom')
  })

  it('ignores errors for unknown fields', async () => {
    const error = await parseError(
      jsonResponse({ detail: [{ type: 'json_invalid', loc: ['body'], msg: 'bad' }] }, 422),
    )
    expect(error.fieldErrors).toEqual({})
    expect(error.message).toMatch(/need fixing/)
  })

  it('surfaces a string detail as the message', async () => {
    const error = await parseError(
      jsonResponse({ detail: "Background video for 'subwaySurfers' is missing" }, 500),
    )
    expect(error.message).toBe("Background video for 'subwaySurfers' is missing")
    expect(error.status).toBe(500)
    expect(error.fieldErrors).toEqual({})
  })

  it('falls back to a generic message for non-JSON bodies', async () => {
    const error = await parseError(new Response('<html>Bad gateway</html>', { status: 502 }))
    expect(error.message).toBe('Something went wrong on our side (error 502).')
  })

  it('falls back when detail is missing or empty', async () => {
    expect((await parseError(jsonResponse({}, 500))).message).toMatch(/error 500/)
    expect((await parseError(jsonResponse({ detail: '' }, 503))).message).toMatch(/error 503/)
  })
})

describe('createShort', () => {
  it('POSTs JSON to the create endpoint and returns the video blob', async () => {
    const fetchImpl = vi.fn().mockResolvedValue(videoResponse('mp4-bytes'))
    const blob = await createShort(FORM, { fetchImpl })

    expect(blob.size).toBe('mp4-bytes'.length)
    expect(blob.type).toBe('video/mp4')
    const [url, options] = fetchImpl.mock.calls[0]
    expect(url).toBe('http://127.0.0.1:8000/shorts/create/')
    expect(options.method).toBe('POST')
    expect(options.headers).toEqual({ 'Content-Type': 'application/json' })
    expect(JSON.parse(options.body)).toEqual(toPayload(FORM))
  })

  it('passes the abort signal through', async () => {
    const fetchImpl = vi.fn().mockResolvedValue(videoResponse())
    const controller = new AbortController()
    await createShort(FORM, { fetchImpl, signal: controller.signal })
    expect(fetchImpl.mock.calls[0][1].signal).toBe(controller.signal)
  })

  it('uses the global fetch by default', async () => {
    const fetchSpy = vi.fn().mockResolvedValue(videoResponse())
    vi.stubGlobal('fetch', fetchSpy)
    await createShort(FORM)
    expect(fetchSpy).toHaveBeenCalledOnce()
    vi.unstubAllGlobals()
  })

  it('throws ApiError on HTTP errors', async () => {
    const fetchImpl = vi.fn().mockResolvedValue(jsonResponse({ detail: 'boom' }, 500))
    await expect(createShort(FORM, { fetchImpl })).rejects.toMatchObject({
      name: 'ApiError',
      message: 'boom',
      status: 500,
    })
  })

  it('explains network failures', async () => {
    const fetchImpl = vi.fn().mockRejectedValue(new TypeError('Failed to fetch'))
    await expect(createShort(FORM, { fetchImpl })).rejects.toThrow(
      "Couldn't reach the server at http://127.0.0.1:8000. Is the backend running?",
    )
  })

  it('rethrows aborts untouched', async () => {
    const abort = new DOMException('Aborted', 'AbortError')
    const fetchImpl = vi.fn().mockRejectedValue(abort)
    await expect(createShort(FORM, { fetchImpl })).rejects.toBe(abort)
  })
})

describe('listShorts', () => {
  it('GETs all shorts, newest first', async () => {
    const fetchImpl = vi.fn().mockResolvedValue(
      jsonResponse([
        { id: 1, post_title: 'a' },
        { id: 3, post_title: 'c' },
        { id: 2, post_title: 'b' },
      ]),
    )
    const videos = await listShorts({ fetchImpl })
    expect(fetchImpl.mock.calls[0][0]).toBe('http://127.0.0.1:8000/shorts/all/')
    expect(videos.map((v) => v.id)).toEqual([3, 2, 1])
  })

  it('returns an empty list', async () => {
    const fetchImpl = vi.fn().mockResolvedValue(jsonResponse([]))
    expect(await listShorts({ fetchImpl })).toEqual([])
  })

  it('throws ApiError on failure', async () => {
    const fetchImpl = vi.fn().mockResolvedValue(new Response('', { status: 500 }))
    await expect(listShorts({ fetchImpl })).rejects.toBeInstanceOf(ApiError)
  })
})
