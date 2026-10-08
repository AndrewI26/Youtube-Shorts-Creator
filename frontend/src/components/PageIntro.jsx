import { cx, display, eyebrow, lede } from './ui'

export default function PageIntro({ label, title, description, centered = false, children }) {
  return (
    <section
      className={cx(
        'mb-8 max-w-170 sm:mb-14',
        centered && 'mx-auto my-[10vh] text-center sm:my-[10vh]',
      )}
    >
      <p className={eyebrow}>{label}</p>
      <h1 className={display}>{title}</h1>
      <p className={cx(lede, centered && 'mx-auto mb-8')}>{description}</p>
      {children}
    </section>
  )
}
