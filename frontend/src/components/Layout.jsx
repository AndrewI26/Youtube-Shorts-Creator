import { NavLink, Outlet } from 'react-router-dom'

const navClass = ({ isActive }) => (isActive ? 'nav-link active' : 'nav-link')

export default function Layout() {
  return (
    <div className="app">
      <header className="nav">
        <NavLink to="/" className="wordmark" aria-label="Shorts Creator home">
          shorts<span className="wordmark-dot">.</span>
        </NavLink>
        <nav aria-label="Main">
          <NavLink to="/" end className={navClass}>
            Create
          </NavLink>
          <NavLink to="/history" className={navClass}>
            History
          </NavLink>
        </nav>
      </header>
      <main className="shell">
        <Outlet />
      </main>
    </div>
  )
}
