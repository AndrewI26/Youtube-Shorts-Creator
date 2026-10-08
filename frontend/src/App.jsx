import { Route, Routes } from 'react-router-dom'
import Layout from './components/Layout'
import CreatePage from './pages/CreatePage'
import HistoryPage from './pages/HistoryPage'
import NotFoundPage from './pages/NotFoundPage'

export default function App() {
  return (
    <Routes>
      <Route element={<Layout />}>
        <Route index element={<CreatePage />} />
        <Route path="history" element={<HistoryPage />} />
        <Route path="*" element={<NotFoundPage />} />
      </Route>
    </Routes>
  )
}
