/**
 * Custom axis tick renderers for the reporting charts.
 *
 * Recharts renders category ticks as a single <text> anchored at the axis, so a
 * long label (e.g. a URL path like
 * "/airdoctor/insights/popcorn-ceilings-vermiculite-inspections-material-identification/")
 * simply overflows past x=0 of the SVG and gets clipped at its *beginning* -
 * the client then sees a broken, unusable URL such as
 * "-ceilings-vermiculite-inspections-material-identification/".
 *
 * WrappedCategoryTick fixes that by wrapping the label onto multiple lines that
 * fit the space actually available to the left of the tick, so the label always
 * starts at the beginning of the value. If it still does not fit within
 * maxLines, the *end* is trimmed with an ellipsis (the full value is always
 * available in the chart tooltip).
 */

const FONT_FAMILY =
  '"Inter", "Inter var", -apple-system, BlinkMacSystemFont, "Segoe UI", Helvetica, Arial, sans-serif'

// Gap kept between the label and the left edge of the chart
const LABEL_GUTTER = 6

let measureContext = null
const measureCache = new Map()

/**
 * Measure rendered text width in px. Uses a canvas 2d context (accurate for the
 * app font) and falls back to a per-character estimate when canvas is missing.
 */
export function measureTextWidth(text, fontSize) {
  if (!text) return 0
  const cacheKey = `${fontSize}|${text}`
  const cached = measureCache.get(cacheKey)
  if (cached !== undefined) return cached

  let width
  if (measureContext === null && typeof document !== 'undefined') {
    measureContext = document.createElement('canvas').getContext('2d') || false
  }
  if (measureContext) {
    measureContext.font = `${fontSize}px ${FONT_FAMILY}`
    width = measureContext.measureText(text).width
  } else {
    width = text.length * fontSize * 0.55
  }

  measureCache.set(cacheKey, width)
  return width
}

/**
 * Split a label into chunks that can be wrapped, keeping URL/path delimiters
 * attached to the chunk they close so lines break at readable boundaries.
 */
function tokenize(label) {
  return label.match(/[^/\-_?&=\s]*[/\-_?&=\s]+|[^/\-_?&=\s]+/g) || [label]
}

/** Greedy wrap on delimiter boundaries - readable, but leaves lines ragged. */
function wrapOnTokens(text, maxWidth, measure) {
  const lines = []
  let current = ''

  const flushOverflow = () => {
    // A single token can be wider than a whole line - hard split it
    while (measure(current) > maxWidth && current.length > 1) {
      let cut = current.length
      while (cut > 1 && measure(current.slice(0, cut)) > maxWidth) cut--
      lines.push(current.slice(0, cut))
      current = current.slice(cut)
    }
  }

  for (const token of tokenize(text)) {
    if (!current) {
      current = token
    } else if (measure(current + token) <= maxWidth) {
      current += token
    } else {
      lines.push(current)
      current = token
    }
    flushOverflow()
  }
  if (current) lines.push(current)
  return lines
}

/** Greedy wrap on characters - packs the most text into the fewest lines. */
function wrapOnChars(text, maxWidth, measure) {
  const lines = []
  let rest = text
  while (rest) {
    if (measure(rest) <= maxWidth) {
      lines.push(rest)
      break
    }
    let cut = rest.length
    while (cut > 1 && measure(rest.slice(0, cut)) > maxWidth) cut--
    lines.push(rest.slice(0, cut))
    rest = rest.slice(cut)
  }
  return lines
}

/**
 * Wrap a label into at most maxLines lines of maxWidth px.
 *
 * Breaks on path delimiters when that fits, otherwise falls back to character
 * wrapping so the whole value still shows. Only when even that overflows is the
 * end trimmed with an ellipsis - the beginning of the value is never lost.
 *
 * @returns {string[]} lines (always at least one)
 */
export function wrapLabelLines(label, maxWidth, fontSize, maxLines = 2) {
  const text = label == null ? '' : String(label)
  if (!text) return ['']

  const measure = (value) => measureTextWidth(value, fontSize)
  if (maxWidth <= 0 || measure(text) <= maxWidth) return [text]

  const tokenLines = wrapOnTokens(text, maxWidth, measure)
  if (tokenLines.length <= maxLines) return tokenLines

  const charLines = wrapOnChars(text, maxWidth, measure)
  if (charLines.length <= maxLines) return charLines

  const kept = charLines.slice(0, maxLines)
  let last = kept[maxLines - 1]
  while (last.length > 1 && measure(`${last}…`) > maxWidth) {
    last = last.slice(0, -1)
  }
  kept[maxLines - 1] = `${last}…`
  return kept
}

/**
 * Category tick for a left-oriented (horizontal bar) axis that wraps long
 * labels instead of letting them run off the left edge of the chart.
 *
 * Recharts clones this element with the tick props (x, y, payload, ...), so the
 * space available for the label is everything left of the anchor: 0 -> x.
 */
export default function WrappedCategoryTick({
  x,
  y,
  payload,
  fontSize = 11,
  fill = '#71717A',
  maxLines = 2,
}) {
  const label = payload?.value == null ? '' : String(payload.value)
  const available = Math.max(0, (x || 0) - LABEL_GUTTER)
  const lines = wrapLabelLines(label, available, fontSize, maxLines)
  const lineHeight = Math.round(fontSize * 1.2)
  // Keep the wrapped block vertically centred on its bar
  const blockOffset = -((lines.length - 1) * lineHeight) / 2

  return (
    <text
      x={x}
      y={y + blockOffset}
      textAnchor="end"
      fill={fill}
      fontSize={fontSize}
    >
      {lines.map((line, index) => (
        <tspan
          key={index}
          x={x}
          dy={index === 0 ? Math.round(fontSize * 0.355) : lineHeight}
        >
          {line}
        </tspan>
      ))}
    </text>
  )
}
