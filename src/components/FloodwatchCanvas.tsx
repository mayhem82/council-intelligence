import { useEffect, useRef } from 'react'

export interface FloodwatchReading {
  latestTimestamp: string
  latestLevelM: number
  deckM: number
  gapBelowDeckM: number
  pfhe: number
  fs: number
}

const CANVAS_WIDTH = 420
const CANVAS_HEIGHT = 260
const PADDING = 28

const drawRoundedRect = (
  context: CanvasRenderingContext2D,
  x: number,
  y: number,
  width: number,
  height: number,
  radius: number,
) => {
  const cornerRadius = Math.max(0, Math.min(radius, Math.min(width, height) / 2))

  context.beginPath()
  context.moveTo(x + cornerRadius, y)
  context.lineTo(x + width - cornerRadius, y)
  context.quadraticCurveTo(x + width, y, x + width, y + cornerRadius)
  context.lineTo(x + width, y + height - cornerRadius)
  context.quadraticCurveTo(
    x + width,
    y + height,
    x + width - cornerRadius,
    y + height,
  )
  context.lineTo(x + cornerRadius, y + height)
  context.quadraticCurveTo(x, y + height, x, y + height - cornerRadius)
  context.lineTo(x, y + cornerRadius)
  context.quadraticCurveTo(x, y, x + cornerRadius, y)
  context.closePath()
}

const formatTimestamp = (value: string) => {
  try {
    const parsed = new Date(value)
    if (!Number.isNaN(parsed.getTime())) {
      return parsed.toLocaleString()
    }
  } catch (error) {
    console.warn('Unable to parse timestamp for canvas rendering', error)
  }
  return value
}

export const FloodwatchCanvas = ({
  latestTimestamp,
  latestLevelM,
  deckM,
  gapBelowDeckM,
  pfhe,
  fs,
}: FloodwatchReading) => {
  const canvasRef = useRef<HTMLCanvasElement | null>(null)

  useEffect(() => {
    const canvas = canvasRef.current
    if (!canvas) return
    const context = canvas.getContext('2d')
    if (!context) return

    const ratio = window.devicePixelRatio ?? 1

    canvas.width = CANVAS_WIDTH * ratio
    canvas.height = CANVAS_HEIGHT * ratio
    canvas.style.width = `${CANVAS_WIDTH}px`
    canvas.style.height = `${CANVAS_HEIGHT}px`

    context.save()
    context.scale(ratio, ratio)

    context.clearRect(0, 0, CANVAS_WIDTH, CANVAS_HEIGHT)

    // Background
    const gradient = context.createLinearGradient(0, 0, 0, CANVAS_HEIGHT)
    gradient.addColorStop(0, '#0f172a')
    gradient.addColorStop(1, '#1f2937')
    context.fillStyle = gradient
    context.fillRect(0, 0, CANVAS_WIDTH, CANVAS_HEIGHT)

    const chartWidth = CANVAS_WIDTH - PADDING * 2
    const chartHeight = CANVAS_HEIGHT - PADDING * 2

    const maxLevel = Math.max(deckM + 0.6, latestLevelM + 0.6)
    const minLevel = Math.min(0, latestLevelM - 0.6)
    const levelRange = maxLevel - minLevel
    const toCanvasY = (level: number) => {
      if (levelRange === 0) return CANVAS_HEIGHT / 2
      return PADDING + ((maxLevel - level) / levelRange) * chartHeight
    }

    // Gridlines and labels
    context.strokeStyle = 'rgba(148, 163, 184, 0.25)'
    context.fillStyle = '#94a3b8'
    context.lineWidth = 1
    context.setLineDash([4, 6])

    const gridStep = 0.5
    for (let value = Math.ceil(minLevel / gridStep) * gridStep; value <= maxLevel; value += gridStep) {
      const y = toCanvasY(Number(value.toFixed(2)))
      context.beginPath()
      context.moveTo(PADDING, y)
      context.lineTo(PADDING + chartWidth, y)
      context.stroke()

      context.font = '12px Inter, system-ui, sans-serif'
      context.textAlign = 'right'
      context.fillText(`${value.toFixed(2)} m`, PADDING - 8, y + 4)
    }

    context.setLineDash([])

    // Deck line
    const deckY = toCanvasY(deckM)
    context.strokeStyle = '#f97316'
    context.lineWidth = 3
    context.beginPath()
    context.moveTo(PADDING, deckY)
    context.lineTo(PADDING + chartWidth, deckY)
    context.stroke()

    context.font = '14px Inter, system-ui, sans-serif'
    context.textAlign = 'left'
    context.fillStyle = '#fb923c'
    context.fillText(`Deck ${deckM.toFixed(2)} m`, PADDING + 8, deckY - 10)

    // Water level bar
    const waterY = toCanvasY(latestLevelM)
    const waterGradient = context.createLinearGradient(0, waterY, 0, PADDING + chartHeight)
    waterGradient.addColorStop(0, '#38bdf8')
    waterGradient.addColorStop(1, '#0ea5e9')
    context.fillStyle = waterGradient
    drawRoundedRect(
      PADDING + chartWidth / 3,
      waterY,
      chartWidth / 3,
      PADDING + chartHeight - waterY,
      12,
    )
    context.fill()

    context.fillStyle = '#f8fafc'
    context.font = '600 28px Inter, system-ui, sans-serif'
    context.textAlign = 'center'
    context.fillText(`${latestLevelM.toFixed(2)} m`, PADDING + chartWidth / 2, waterY - 16)

    // Gap annotation
    context.font = '13px Inter, system-ui, sans-serif'
    context.textAlign = 'left'
    context.fillStyle = '#38bdf8'
    context.fillText(`Gap below deck: ${gapBelowDeckM.toFixed(2)} m`, PADDING + 8, waterY + 24)

    // Metadata box
    const boxWidth = chartWidth
    const boxHeight = 72
    const boxX = PADDING
    const boxY = CANVAS_HEIGHT - PADDING - boxHeight
    context.fillStyle = 'rgba(15, 23, 42, 0.8)'
    drawRoundedRect(context, boxX, boxY, boxWidth, boxHeight, 12)
    context.fill()

    context.fillStyle = '#e2e8f0'
    context.font = '600 16px Inter, system-ui, sans-serif'
    context.textAlign = 'left'
    context.fillText('Bellbrook Floodwatch Snapshot', boxX + 16, boxY + 26)

    context.font = '13px Inter, system-ui, sans-serif'
    context.fillStyle = '#cbd5f5'
    context.fillText(`Updated: ${formatTimestamp(latestTimestamp)}`, boxX + 16, boxY + 46)

    context.fillStyle = '#94a3b8'
    context.fillText(`PF(H,E): ${pfhe}  •  FS: ${fs}`, boxX + 16, boxY + 62)

    context.restore()
  }, [latestTimestamp, latestLevelM, deckM, gapBelowDeckM, pfhe, fs])

  return (
    <div className="flex flex-col gap-3">
      <canvas
        ref={canvasRef}
        className="w-full max-w-xl rounded-xl shadow-lg shadow-sky-900/40 ring-1 ring-sky-500/40"
      />
    </div>
  )
}

export default FloodwatchCanvas
