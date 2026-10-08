import { Link } from 'react-router-dom'
import PageIntro from '../components/PageIntro'
import { button } from '../components/ui'

export default function NotFoundPage() {
  return (
    <PageIntro
      centered
      label="404"
      title={<>This page doesn&rsquo;t exist.</>}
      description="The link might be broken, or the page may have moved."
    >
      <Link to="/" className={button()}>
        Back to create
      </Link>
    </PageIntro>
  )
}
