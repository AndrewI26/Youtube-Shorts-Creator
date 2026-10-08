import { useEffect, useRef, useState } from 'react'
import { useLocation, useNavigate } from 'react-router-dom'
import {
  VIDEO_CHOICES,
  createShort,
  estimateSeconds,
  formatDuration,
  validateForm,
} from '../lib/api'

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
    <div className={error ? 'field has-error' : 'field'}>
      <label htmlFor={id} className="field-label">
        {label}
      </label>
      {children}
      {error ? (
        <p id={`${id}-error`} className="field-error">
          {error}
        </p>
      ) : (
        hint && <p className="field-hint">{hint}</p>
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
      <section className="intro">
        <p className="eyebrow">Create a short</p>
        <h1 className="display">
          Turn a Reddit post into a video, <em>effortlessly.</em>
        </h1>
        <p className="lede">
          Paste a post, pick some background gameplay, and we&rsquo;ll narrate it and add captions.
        </p>
      </section>

      <div className="create-grid">
        <form className="card" onSubmit={handleSubmit} noValidate aria-label="Create a short">
          {message && (
            <div className={status === 'error' ? 'banner error' : 'banner'} role="alert">
              {message}
            </div>
          )}

          <fieldset disabled={loading} className="fieldset">
            <Field id="subreddit" label="Subreddit" error={fieldErrors.subreddit}>
              <div className="input-affix">
                <span aria-hidden="true">r/</span>
                <input
                  id="subreddit"
                  className="input"
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
                className="input"
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
                className="input textarea"
                rows={7}
                placeholder="Paste the post here…"
                value={form.content}
                onChange={update('content')}
                aria-invalid={Boolean(fieldErrors.content)}
                aria-describedby={fieldErrors.content ? 'content-error' : undefined}
              />
            </Field>

            <div className={fieldErrors.videoChoice ? 'field has-error' : 'field'}>
              <span className="field-label" id="videoChoice-label">
                Background video
              </span>
              <div className="choices" role="radiogroup" aria-labelledby="videoChoice-label">
                {VIDEO_CHOICES.map((choice) => (
                  <label key={choice.value} className="choice">
                    <input
                      type="radio"
                      name="videoChoice"
                      value={choice.value}
                      checked={form.videoChoice === choice.value}
                      onChange={update('videoChoice')}
                    />
                    <span className="choice-body">
                      <span className="choice-title">{choice.label}</span>
                      <span className="choice-description">{choice.description}</span>
                    </span>
                  </label>
                ))}
              </div>
              {fieldErrors.videoChoice && <p className="field-error">{fieldErrors.videoChoice}</p>}
            </div>
          </fieldset>

          <div className="actions">
            <button type="button" className="button ghost" onClick={reset} disabled={loading}>
              Clear
            </button>
            <button type="submit" className="button primary" disabled={loading}>
              {loading ? 'Generating…' : 'Generate video'}
            </button>
          </div>
        </form>

        <aside className="preview" aria-label="Preview" aria-live="polite">
          <div className="phone">
            {status === 'done' && videoUrl ? (
              <video
                className="phone-video"
                src={videoUrl}
                controls
                autoPlay
                playsInline
                data-testid="result-video"
              />
            ) : loading ? (
              <div className="phone-state">
                <div className="spinner" role="progressbar" aria-label="Generating video" />
                <p className="phone-title">Generating your short</p>
                <p className="phone-meta">{formatDuration(elapsed)} elapsed · usually under a minute</p>
                <button type="button" className="button ghost small" onClick={cancel}>
                  Cancel
                </button>
              </div>
            ) : (
              <div className="phone-state">
                <p className="phone-title">Your short will appear here</p>
                <p className="phone-meta">Vertical video · captions included</p>
              </div>
            )}
          </div>

          {status === 'done' && videoUrl && (
            <div className="preview-actions">
              <a className="button primary" href={videoUrl} download="short.mp4">
                Download
              </a>
              <button type="button" className="button ghost" onClick={reset}>
                Make another
              </button>
            </div>
          )}
        </aside>
      </div>
    </>
  )
}
