import { Link } from 'react-router-dom'

export default function NotFoundPage() {
  return (
    <section className="intro centered">
      <p className="eyebrow">404</p>
      <h1 className="display">This page doesn&rsquo;t exist.</h1>
      <p className="lede">The link might be broken, or the page may have moved.</p>
      <Link to="/" className="button primary">
        Back to create
      </Link>
    </section>
  )
}
