import { useCallback, useEffect, useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import PageIntro from '../components/PageIntro'
import { banner, button, card, cx, input, spinner } from '../components/ui'
import { choiceLabel, listShorts } from '../lib/api'

const emptyCard = cx(card, 'flex flex-col items-center gap-2 py-14 text-center sm:py-14')
const muted = 'text-[13px] text-ink-muted'

export default function HistoryPage() {
  const navigate = useNavigate()
  const [videos, setVideos] = useState([])
  const [status, setStatus] = useState('loading')
  const [error, setError] = useState('')
  const [query, setQuery] = useState('')

  const load = useCallback((signal) => {
    setStatus('loading')
    listShorts({ signal })
      .then((result) => {
        setVideos(result)
        setStatus('ready')
      })
      .catch((err) => {
        if (err?.name === 'AbortError') return
        setError(err.message || 'Could not load your history.')
        setStatus('error')
      })
  }, [])

  useEffect(() => {
    const controller = new AbortController()
    load(controller.signal)
    return () => controller.abort()
  }, [load])

  const needle = query.trim().toLowerCase()
  const visible = needle
    ? videos.filter((v) =>
        [v.subreddit, v.post_title, v.content].some((text) => text?.toLowerCase().includes(needle)),
      )
    : videos

  return (
    <>
      <PageIntro
        label="History"
        title={<>Every short you&rsquo;ve requested.</>}
        description="Pick any post to load it back into the editor."
      />

      {status === 'loading' && (
        <div className={emptyCard} role="status">
          <div className={cx(spinner, 'mb-3')} aria-hidden="true" />
          <p>Loading your history…</p>
        </div>
      )}

      {status === 'error' && (
        <div className={emptyCard}>
          <div className={banner('error')} role="alert">
            {error}
          </div>
          <button type="button" className={button({ variant: 'ghost' })} onClick={() => load()}>
            Try again
          </button>
        </div>
      )}

      {status === 'ready' && videos.length === 0 && (
        <div className={emptyCard}>
          <p className="font-serif text-title">Nothing here yet</p>
          <p className={cx(muted, 'mb-2')}>Shorts you create will show up here.</p>
          <Link to="/" className={button()}>
            Create your first short
          </Link>
        </div>
      )}

      {status === 'ready' && videos.length > 0 && (
        <>
          <div className="mb-4 flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
            <input
              type="search"
              className={cx(input, 'sm:max-w-90')}
              placeholder="Search posts"
              aria-label="Search posts"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
            />
            <p className={cx(muted, 'whitespace-nowrap')}>
              {visible.length} of {videos.length} {videos.length === 1 ? 'post' : 'posts'}
            </p>
          </div>

          {visible.length === 0 ? (
            <div className={emptyCard}>
              <p>No posts match &ldquo;{query.trim()}&rdquo;.</p>
            </div>
          ) : (
            <ul className="divide-y divide-line rounded-card border border-line bg-surface">
              {visible.map((video) => (
                <li
                  key={video.id}
                  className="flex flex-col gap-3 px-4 py-5 sm:flex-row sm:items-center sm:gap-6 sm:px-7"
                >
                  <div className="min-w-0 flex-1">
                    <p className={cx(muted, 'mb-1')}>
                      r/{video.subreddit} · {choiceLabel(video.video_choice)}
                    </p>
                    <h2 className="font-serif text-[22px] leading-tight font-normal">
                      {video.post_title}
                    </h2>
                    <p className="mt-1 truncate text-sm text-ink-muted">{video.content}</p>
                  </div>
                  <button
                    type="button"
                    className={button({ variant: 'ghost', size: 'sm', className: 'self-start sm:self-auto' })}
                    onClick={() => navigate('/', { state: { prefill: video } })}
                    aria-label={`Use "${video.post_title}" again`}
                  >
                    Use again
                  </button>
                </li>
              ))}
            </ul>
          )}
        </>
      )}
    </>
  )
}
