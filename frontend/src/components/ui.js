export const cx = (...classes) => classes.filter(Boolean).join(' ')

const BUTTON_BASE =
  'inline-flex cursor-pointer items-center justify-center rounded-full border font-semibold no-underline ' +
  'transition active:not-disabled:scale-[0.98] disabled:cursor-not-allowed disabled:opacity-50 ' +
  'focus-visible:outline-none focus-visible:ring-3 focus-visible:ring-ink/20'

const BUTTON_VARIANTS = {
  primary: 'border-transparent bg-ink text-canvas hover:not-disabled:bg-ink-hover',
  ghost: 'border-line-strong bg-transparent text-ink hover:not-disabled:bg-surface-muted',
}

const BUTTON_SIZES = {
  md: 'px-6.5 py-3.5 text-[15px]',
  sm: 'px-4.5 py-2 text-sm',
}

export function button({ variant = 'primary', size = 'md', className } = {}) {
  return cx(BUTTON_BASE, BUTTON_VARIANTS[variant], BUTTON_SIZES[size], className)
}

export const input =
  'w-full rounded-field border border-line-strong bg-surface px-4 py-3.5 text-ink transition ' +
  'placeholder:text-ink-faint hover:border-ink-muted focus:border-ink focus:outline-none ' +
  'focus:ring-3 focus:ring-ink/10 disabled:opacity-60 aria-invalid:border-danger'

export const card = 'rounded-card border border-line bg-surface p-5 sm:p-9'

export const eyebrow = 'mb-3 text-eyebrow font-semibold uppercase text-ink-muted'

export const display = 'font-serif text-display font-normal'

export const lede = 'mt-5 max-w-130 text-lg text-ink-muted'

export const spinner = 'size-9 animate-spin rounded-full border-3 border-line-strong border-t-ink'

export const banner = (tone) =>
  cx(
    'mb-6 rounded-field px-4 py-3.5 text-sm',
    tone === 'error' ? 'bg-danger-soft text-danger' : 'bg-surface-muted',
  )
