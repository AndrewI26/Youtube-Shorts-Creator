import { useCallback, useEffect, useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { choiceLabel, listShorts } from '../lib/api'

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
      <section className="intro">
        <p className="eyebrow">History</p>
        <h1 className="display">Every short you&rsquo;ve requested.</h1>
        <p className="lede">Pick any post to load it back into the editor.</p>
      </section>

      {status === 'loading' && (
        <div className="card empty" role="status">
          <div className="spinner" aria-hidden="true" />
          <p>Loading your history…</p>
        </div>
      )}

      {status === 'error' && (
        <div className="card empty">
          <div className="banner error" role="alert">
            {error}
          </div>
          <button type="button" className="button ghost" onClick={() => load()}>
            Try again
          </button>
        </div>
      )}

      {status === 'ready' && videos.length === 0 && (
        <div className="card empty">
          <p className="phone-title">Nothing here yet</p>
          <p className="phone-meta">Shorts you create will show up here.</p>
          <Link to="/" className="button primary">
            Create your first short
          </Link>
        </div>
      )}

      {status === 'ready' && videos.length > 0 && (
        <>
          <div className="history-toolbar">
            <input
              type="search"
              className="input"
              placeholder="Search posts"
              aria-label="Search posts"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
            />
            <p className="phone-meta">
              {visible.length} of {videos.length} {videos.length === 1 ? 'post' : 'posts'}
            </p>
          </div>

          {visible.length === 0 ? (
            <div className="card empty">
              <p>No posts match &ldquo;{query.trim()}&rdquo;.</p>
            </div>
          ) : (
            <ul className="history-list">
              {visible.map((video) => (
                <li key={video.id} className="history-item">
                  <div className="history-main">
                    <p className="history-meta">
                      r/{video.subreddit} · {choiceLabel(video.video_choice)}
                    </p>
                    <h2 className="history-title">{video.post_title}</h2>
                    <p className="history-snippet">{video.content}</p>
                  </div>
                  <button
                    type="button"
                    className="button ghost small"
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
