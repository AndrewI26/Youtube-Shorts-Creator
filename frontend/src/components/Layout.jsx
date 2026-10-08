import { useEffect } from 'react'
import { NavLink, Outlet, useLocation } from 'react-router-dom'
import { cx } from './ui'

const navClass = ({ isActive }) =>
  cx(
    'rounded-full px-4 py-2 text-[15px] font-medium no-underline transition-colors',
    isActive ? 'bg-ink text-canvas' : 'text-ink-muted hover:text-ink',
  )

export default function Layout() {
  const { pathname } = useLocation()

  // Client-side navigation keeps the old scroll position unless we reset it.
  useEffect(() => {
    window.scrollTo(0, 0)
  }, [pathname])

  return (
    <div className="min-h-screen">
      <header className="sticky top-0 z-10 flex items-center justify-between bg-canvas/88 px-4 py-5 backdrop-blur-md sm:px-8 lg:px-12">
        <NavLink
          to="/"
          className="font-serif text-[30px] leading-none tracking-tight no-underline"
          aria-label="Shorts Creator home"
        >
          shorts<span className="text-ink-faint">.</span>
        </NavLink>
        <nav aria-label="Main" className="flex gap-1">
          <NavLink to="/" end className={navClass}>
            Create
          </NavLink>
          <NavLink to="/history" className={navClass}>
            History
          </NavLink>
        </nav>
      </header>
      <main className="mx-auto max-w-shell px-4 pt-8 pb-24 sm:px-8 sm:pt-14 lg:px-12 lg:pt-18">
        <Outlet />
      </main>
    </div>
  )
}
