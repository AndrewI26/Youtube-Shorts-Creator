import { useEffect, useRef, useState } from 'react'
import { useLocation, useNavigate } from 'react-router-dom'
import {
  VIDEO_CHOICES,
  createShort,
  estimateSeconds,
  formatDuration,
  validateForm,
} from '../lib/api'
import PageIntro from '../components/PageIntro'
import { banner, button, card, cx, input, spinner } from '../components/ui'

const fieldLabel = 'mb-2 block text-sm font-semibold'
const phoneTitle = 'font-serif text-title'
const phoneMeta = 'mb-2 text-[13px] text-ink-muted'

export const EMPTY_FORM = {
  subreddit: '',
  postTitle: '',
  content: '',
  videoChoice: 'subwaySurfers',
}

function formFromVideo(video) {
  return {
    subreddit: video.subreddit ?? '',
    postTitle: video.post_title ?? '',
    content: video.content ?? '',
    videoChoice: VIDEO_CHOICES.some((c) => c.value === video.video_choice)
      ? video.video_choice
      : EMPTY_FORM.videoChoice,
  }
}

function Field({ id, label, error, hint, children }) {
  return (
    <div className="mb-6">
      <label htmlFor={id} className={fieldLabel}>
        {label}
      </label>
      {children}
      {error ? (
        <p id={`${id}-error`} className="mt-2 text-[13px] text-danger">
          {error}
        </p>
      ) : (
        hint && <p className="mt-2 text-[13px] text-ink-muted">{hint}</p>
      )}
    </div>
  )
}

export default function CreatePage() {
  const location = useLocation()
  const navigate = useNavigate()
  const prefill = location.state?.prefill

  const [form, setForm] = useState(() => (prefill ? formFromVideo(prefill) : EMPTY_FORM))
  const [fieldErrors, setFieldErrors] = useState({})
  const [status, setStatus] = useState('idle')
  const [message, setMessage] = useState('')
  const [videoUrl, setVideoUrl] = useState(null)
  const [elapsed, setElapsed] = useState(0)
  const controllerRef = useRef(null)

  // Drop the router state so a refresh doesn't re-apply the prefill.
  useEffect(() => {
    if (prefill) navigate('.', { replace: true, state: null })
  }, [prefill, navigate])

  useEffect(() => {
    if (status !== 'loading') return undefined
    setElapsed(0)
    const started = Date.now()
    const timer = setInterval(() => setElapsed((Date.now() - started) / 1000), 1000)
    return () => clearInterval(timer)
  }, [status])

  useEffect(() => () => videoUrl && URL.revokeObjectURL(videoUrl), [videoUrl])
  useEffect(() => () => controllerRef.current?.abort(), [])

  const update = (field) => (event) => {
    setForm((current) => ({ ...current, [field]: event.target.value }))
    setFieldErrors((current) => ({ ...current, [field]: undefined }))
  }

  const reset = () => {
    setForm(EMPTY_FORM)
    setFieldErrors({})
    setMessage('')
    setVideoUrl(null)
    setStatus('idle')
  }

  const cancel = () => {
    controllerRef.current?.abort()
    setStatus('idle')
    setMessage('Generation cancelled.')
  }

  const handleSubmit = async (event) => {
    event.preventDefault()
    const errors = validateForm(form)
    setFieldErrors(errors)
    if (Object.keys(errors).length) {
      setMessage('')
      return
    }

    const controller = new AbortController()
    controllerRef.current = controller
    setMessage('')
    setVideoUrl(null)
    setStatus('loading')
    try {
      const blob = await createShort(form, { signal: controller.signal })
      setVideoUrl(URL.createObjectURL(blob))
      setStatus('done')
    } catch (error) {
      if (error?.name === 'AbortError') return
      setFieldErrors(error.fieldErrors ?? {})
      setMessage(error.message || 'Something went wrong.')
      setStatus('error')
    } finally {
      if (controllerRef.current === controller) controllerRef.current = null
    }
  }

  const loading = status === 'loading'
  const words = `${form.postTitle} ${form.content}`.trim().split(/\s+/).filter(Boolean).length
  const seconds = estimateSeconds(`From the subreddit ${form.subreddit},`, form.postTitle, form.content)

  return (
    <>
      <PageIntro
        label="Create a short"
        title={
          <>
            Turn a Reddit post into a video, <em className="text-ink-muted">effortlessly.</em>
          </>
        }
        description={
          <>
            Paste a post, pick some background gameplay, and we&rsquo;ll narrate it and add captions.
          </>
        }
      />

      <div className="grid items-start gap-8 lg:grid-cols-[minmax(0,1fr)_340px]">
        <form className={card} onSubmit={handleSubmit} noValidate aria-label="Create a short">
          {message && (
            <div className={banner(status === 'error' ? 'error' : 'info')} role="alert">
              {message}
            </div>
          )}

          <fieldset disabled={loading} className="m-0 min-w-0 border-0 p-0">
            <Field id="subreddit" label="Subreddit" error={fieldErrors.subreddit}>
              <div className="relative">
                <span
                  aria-hidden="true"
                  className="pointer-events-none absolute top-1/2 left-4 -translate-y-1/2 text-ink-muted"
                >
                  r/
                </span>
                <input
                  id="subreddit"
                  className={cx(input, 'pl-9')}
                  placeholder="AmItheAsshole"
                  value={form.subreddit}
                  onChange={update('subreddit')}
                  aria-invalid={Boolean(fieldErrors.subreddit)}
                  aria-describedby={fieldErrors.subreddit ? 'subreddit-error' : undefined}
                  autoComplete="off"
                />
              </div>
            </Field>

            <Field id="postTitle" label="Post title" error={fieldErrors.postTitle}>
              <input
                id="postTitle"
                className={input}
                placeholder="AITA for leaving my friend's party early?"
                value={form.postTitle}
                onChange={update('postTitle')}
                aria-invalid={Boolean(fieldErrors.postTitle)}
                aria-describedby={fieldErrors.postTitle ? 'postTitle-error' : undefined}
              />
            </Field>

            <Field
              id="content"
              label="Body"
              error={fieldErrors.content}
              hint={
                words
                  ? `${words} ${words === 1 ? 'word' : 'words'} · about ${formatDuration(seconds)} of narration`
                  : 'Shorts work best under a minute, so roughly 140 words or fewer.'
              }
            >
              <textarea
                id="content"
                className={cx(input, 'min-h-40 resize-y leading-relaxed')}
                rows={7}
                placeholder="Paste the post here…"
                value={form.content}
                onChange={update('content')}
                aria-invalid={Boolean(fieldErrors.content)}
                aria-describedby={fieldErrors.content ? 'content-error' : undefined}
              />
            </Field>

            <div className="mb-6">
              <span className={fieldLabel} id="videoChoice-label">
                Background video
              </span>
              <div
                className="grid grid-cols-1 gap-3 sm:grid-cols-3"
                role="radiogroup"
                aria-labelledby="videoChoice-label"
                aria-describedby={fieldErrors.videoChoice ? 'videoChoice-error' : undefined}
              >
                {VIDEO_CHOICES.map((choice) => (
                  <label key={choice.value} className="group relative cursor-pointer">
                    <input
                      type="radio"
                      name="videoChoice"
                      value={choice.value}
                      checked={form.videoChoice === choice.value}
                      onChange={update('videoChoice')}
                      className="peer absolute inset-0 m-0 cursor-pointer opacity-0"
                    />
                    <span
                      className={cx(
                        'flex h-full flex-col gap-0.5 rounded-field border border-line-strong px-4 py-3.5 transition',
                        'group-hover:border-ink-muted peer-disabled:opacity-60',
                        'peer-checked:border-ink peer-checked:bg-surface-muted peer-checked:inset-ring peer-checked:inset-ring-ink',
                        'peer-focus-visible:ring-3 peer-focus-visible:ring-ink/15',
                      )}
                    >
                      <span className="text-[15px] font-semibold">{choice.label}</span>
                      <span className="text-[13px] text-ink-muted">{choice.description}</span>
                    </span>
                  </label>
                ))}
              </div>
              {fieldErrors.videoChoice && (
                <p id="videoChoice-error" className="mt-2 text-[13px] text-danger">
                  {fieldErrors.videoChoice}
                </p>
              )}
            </div>
          </fieldset>

          <div className="mt-2 flex flex-col-reverse gap-3 sm:flex-row sm:justify-end">
            <button
              type="button"
              className={button({ variant: 'ghost', className: 'w-full sm:w-auto' })}
              onClick={reset}
              disabled={loading}
            >
              Clear
            </button>
            <button
              type="submit"
              className={button({ className: 'w-full sm:w-auto' })}
              disabled={loading}
            >
              {loading ? 'Generating…' : 'Generate video'}
            </button>
          </div>
        </form>

        <aside
          className="mx-auto w-full max-w-80 lg:sticky lg:top-24 lg:max-w-none"
          aria-label="Preview"
          aria-live="polite"
        >
          <div className="aspect-9/16 w-full overflow-hidden rounded-phone border-8 border-ink bg-ink shadow-phone">
            {status === 'done' && videoUrl ? (
              <video
                className="block size-full rounded-3xl bg-black object-cover"
                src={videoUrl}
                controls
                autoPlay
                playsInline
                data-testid="result-video"
              />
            ) : (
              <div className="flex size-full flex-col items-center justify-center gap-2 rounded-3xl bg-surface-muted p-6 text-center">
                {loading ? (
                  <>
                    <div
                      className={cx(spinner, 'mb-3')}
                      role="progressbar"
                      aria-label="Generating video"
                    />
                    <p className={phoneTitle}>Generating your short</p>
                    <p className={phoneMeta}>
                      {formatDuration(elapsed)} elapsed · usually under a minute
                    </p>
                    <button type="button" className={button({ variant: 'ghost', size: 'sm' })} onClick={cancel}>
                      Cancel
                    </button>
                  </>
                ) : (
                  <>
                    <p className={phoneTitle}>Your short will appear here</p>
                    <p className={phoneMeta}>Vertical video · captions included</p>
                  </>
                )}
              </div>
            )}
          </div>

          {status === 'done' && videoUrl && (
            <div className="mt-5 flex justify-center gap-3">
              <a className={button()} href={videoUrl} download="short.mp4">
                Download
              </a>
              <button type="button" className={button({ variant: 'ghost' })} onClick={reset}>
                Make another
              </button>
            </div>
          )}
        </aside>
      </div>
    </>
  )
}
