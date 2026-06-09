/** Formatting helpers. Monetary amounts are stored as integer minor units (kopecks). */

const UAH = new Intl.NumberFormat('uk-UA', {
  style: 'currency',
  currency: 'UAH',
  minimumFractionDigits: 2,
})

/** Format integer minor units (e.g. 120000) as currency (e.g. "1 200,00 ₴"). */
export function formatCurrency(minorUnits: number): string {
  return UAH.format(minorUnits / 100)
}

/** Format a Unix timestamp (seconds) as a local date-time string. */
export function formatDateTime(unixSeconds: number): string {
  return new Date(unixSeconds * 1000).toLocaleString()
}

/** Format a Unix timestamp (seconds) as a local date string. */
export function formatDate(unixSeconds: number): string {
  return new Date(unixSeconds * 1000).toLocaleDateString()
}
