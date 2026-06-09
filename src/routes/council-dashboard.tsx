import { createFileRoute } from '@tanstack/react-router'
import { AlertTriangle, ArrowDownWideNarrow, Database, ExternalLink, FileText, Filter, RefreshCw, Search } from 'lucide-react'
import { useEffect, useMemo, useState } from 'react'

type MatterEvent = {
  date: string
  kind: string
  status: string
  trigger: string
  source: string
}

type Matter = {
  id: string
  status: string
  score: number
  evidenceReferences: number
  actionSignals: number
  events: number
  chronologyPath: string
  eventList: MatterEvent[]
}

type DashboardData = {
  updatedUtc: string
  proofOfFact: number
  proofMeaning: string
  factualStrength: {
    score: number
    band: string
    rationale: string
  }
  summary: Record<string, number>
  matters: Matter[]
  files: Record<string, string>
}

type SortKey = 'score' | 'events' | 'evidenceReferences' | 'actionSignals' | 'id'

const repoBase = 'https://github.com/mayhem82/tanstack-template/blob/main/'
const dataUrl = '/council-dashboard-data.json'

function repoLink(path: string) {
  return `${repoBase}${path}`
}

function formatLabel(value: string) {
  return value
    .replace(/([a-z])([A-Z])/g, '$1 $2')
    .replace(/[-_]/g, ' ')
    .replace(/\b\w/g, (letter) => letter.toUpperCase())
}

function statusTone(status: string) {
  const lower = status.toLowerCase()
  if (lower.includes('resolved')) return 'border-emerald-500/40 bg-emerald-500/10 text-emerald-200'
  if (lower.includes('deferred')) return 'border-amber-500/40 bg-amber-500/10 text-amber-200'
  if (lower.includes('funding')) return 'border-sky-500/40 bg-sky-500/10 text-sky-200'
  if (lower.includes('open')) return 'border-orange-500/40 bg-orange-500/10 text-orange-200'
  return 'border-zinc-500/40 bg-zinc-500/10 text-zinc-200'
}

function metricValue(summary: Record<string, number>, key: string) {
  return typeof summary[key] === 'number' ? summary[key] : 0
}

function CouncilDashboard() {
  const [data, setData] = useState<DashboardData | null>(null)
  const [loadState, setLoadState] = useState<'loading' | 'ready' | 'missing' | 'error'>('loading')
  const [query, setQuery] = useState('')
  const [status, setStatus] = useState('all')
  const [sortKey, setSortKey] = useState<SortKey>('score')
  const [selectedId, setSelectedId] = useState<string | null>(null)

  useEffect(() => {
    let cancelled = false

    async function loadDashboardData() {
      try {
        setLoadState('loading')
        const response = await fetch(dataUrl, { cache: 'no-store' })
        if (response.status === 404) {
          if (!cancelled) setLoadState('missing')
          return
        }
        if (!response.ok) throw new Error(`Dashboard data request failed: ${response.status}`)
        const payload = (await response.json()) as DashboardData
        if (!cancelled) {
          setData(payload)
          setSelectedId(payload.matters[0]?.id ?? null)
          setLoadState('ready')
        }
      } catch (error) {
        console.error(error)
        if (!cancelled) setLoadState('error')
      }
    }

    loadDashboardData()
    return () => {
      cancelled = true
    }
  }, [])

  const statuses = useMemo(() => {
    const values = new Set(data?.matters.map((matter) => matter.status) ?? [])
    return ['all', ...Array.from(values).sort()]
  }, [data])

  const filteredMatters = useMemo(() => {
    const normalizedQuery = query.trim().toLowerCase()
    const matters = data?.matters ?? []
    return matters
      .filter((matter) => {
        const matchesStatus = status === 'all' || matter.status === status
        const searchable = `${matter.id} ${matter.status} ${matter.eventList.map((event) => `${event.kind} ${event.trigger} ${event.source}`).join(' ')}`.toLowerCase()
        return matchesStatus && (!normalizedQuery || searchable.includes(normalizedQuery))
      })
      .sort((left, right) => {
        if (sortKey === 'id') return left.id.localeCompare(right.id)
        return right[sortKey] - left[sortKey]
      })
  }, [data, query, status, sortKey])

  const selectedMatter = useMemo(() => {
    return filteredMatters.find((matter) => matter.id === selectedId) ?? filteredMatters[0] ?? null
  }, [filteredMatters, selectedId])

  const summary = data?.summary ?? {}
  const files = data?.files ?? {
    dashboard: 'upper-macleay-council-intelligence/DASHBOARD.md',
    lifecycle: 'upper-macleay-council-intelligence/reports/matter-lifecycle.md',
    heatmap: 'upper-macleay-council-intelligence/reports/matter-heatmap.md',
    duplicates: 'upper-macleay-council-intelligence/reports/duplicate-source-report.md',
    audit: 'upper-macleay-council-intelligence/reports/evidence-chain-audit.md',
  }

  return (
    <main className="min-h-screen bg-zinc-950 text-zinc-100">
      <div className="mx-auto flex min-h-screen w-full max-w-7xl flex-col px-4 py-5 sm:px-6 lg:px-8">
        <header className="flex flex-col gap-4 border-b border-zinc-800 pb-5 lg:flex-row lg:items-end lg:justify-between">
          <div>
            <p className="text-sm font-medium uppercase tracking-wide text-orange-300">Upper Macleay Council Intelligence</p>
            <h1 className="mt-2 text-3xl font-semibold text-white sm:text-4xl">Evidence Dashboard</h1>
            <p className="mt-2 max-w-3xl text-sm leading-6 text-zinc-300">
              Navigate automated matter signals, source coverage, lifecycle reports, and evidence audit outputs. Automated classifications remain unverified until checked against preserved source records.
            </p>
          </div>
          <div className="flex flex-wrap gap-2">
            <a className="inline-flex items-center gap-2 rounded-md border border-zinc-700 px-3 py-2 text-sm text-zinc-200 hover:border-orange-400 hover:text-white" href={repoLink('upper-macleay-council-intelligence/INTELLIGENCE-HOME.md')} target="_blank" rel="noreferrer">
              <FileText className="h-4 w-4" /> Intelligence Home
            </a>
            <a className="inline-flex items-center gap-2 rounded-md bg-orange-500 px-3 py-2 text-sm font-medium text-zinc-950 hover:bg-orange-400" href={dataUrl} target="_blank" rel="noreferrer">
              <Database className="h-4 w-4" /> Data JSON
            </a>
          </div>
        </header>

        <section className="grid gap-3 py-5 sm:grid-cols-2 lg:grid-cols-4">
          <Metric label="Matters" value={metricValue(summary, 'mattersTracked')} />
          <Metric label="Open Watch" value={metricValue(summary, 'openWatchMatters')} />
          <Metric label="Resolution Candidates" value={metricValue(summary, 'resolutionCandidates')} />
          <Metric label="Evidence Missing" value={metricValue(summary, 'evidenceReferencesMissing')} />
        </section>

        <section className="grid flex-1 gap-4 lg:grid-cols-[320px_minmax(0,1fr)]">
          <aside className="flex min-h-0 flex-col gap-3 rounded-md border border-zinc-800 bg-zinc-900/70 p-3">
            <div className="grid gap-2">
              <label className="text-xs font-medium uppercase tracking-wide text-zinc-400" htmlFor="matter-search">Search</label>
              <div className="flex items-center gap-2 rounded-md border border-zinc-700 bg-zinc-950 px-3 py-2">
                <Search className="h-4 w-4 text-zinc-500" />
                <input id="matter-search" className="w-full bg-transparent text-sm text-zinc-100 outline-none placeholder:text-zinc-600" value={query} onChange={(event) => setQuery(event.target.value)} placeholder="Matter, trigger, source" />
              </div>
            </div>

            <div className="grid grid-cols-2 gap-2">
              <ControlSelect label="Status" icon={<Filter className="h-4 w-4" />} value={status} onChange={setStatus} options={statuses.map((item) => ({ label: item === 'all' ? 'All' : formatLabel(item), value: item }))} />
              <ControlSelect label="Sort" icon={<ArrowDownWideNarrow className="h-4 w-4" />} value={sortKey} onChange={(value) => setSortKey(value as SortKey)} options={[
                { label: 'Heat Score', value: 'score' },
                { label: 'Events', value: 'events' },
                { label: 'Evidence', value: 'evidenceReferences' },
                { label: 'Actions', value: 'actionSignals' },
                { label: 'Name', value: 'id' },
              ]} />
            </div>

            <div className="min-h-[320px] overflow-y-auto rounded-md border border-zinc-800">
              {loadState === 'loading' && <PanelNotice icon={<RefreshCw className="h-5 w-5" />} title="Loading dashboard data" text="Reading generated council-dashboard-data.json." />}
              {loadState === 'missing' && <PanelNotice icon={<AlertTriangle className="h-5 w-5" />} title="No generated data yet" text="Run the Council Records Fetch workflow to generate the dashboard JSON." />}
              {loadState === 'error' && <PanelNotice icon={<AlertTriangle className="h-5 w-5" />} title="Data load failed" text="The dashboard route loaded, but the JSON could not be read." />}
              {loadState === 'ready' && filteredMatters.length === 0 && <PanelNotice icon={<Search className="h-5 w-5" />} title="No matching matters" text="Change the search or filter controls." />}
              {filteredMatters.map((matter) => (
                <button key={matter.id} type="button" onClick={() => setSelectedId(matter.id)} className={`block w-full border-b border-zinc-800 px-3 py-3 text-left hover:bg-zinc-800 ${selectedMatter?.id === matter.id ? 'bg-zinc-800' : 'bg-transparent'}`}>
                  <div className="flex items-center justify-between gap-2">
                    <span className="truncate text-sm font-medium text-white">{formatLabel(matter.id)}</span>
                    <span className="rounded bg-zinc-950 px-2 py-1 text-xs text-orange-200">{matter.score}</span>
                  </div>
                  <div className={`mt-2 inline-flex rounded border px-2 py-1 text-xs ${statusTone(matter.status)}`}>{formatLabel(matter.status)}</div>
                  <div className="mt-2 grid grid-cols-3 gap-2 text-xs text-zinc-400">
                    <span>Refs {matter.evidenceReferences}</span>
                    <span>Actions {matter.actionSignals}</span>
                    <span>Events {matter.events}</span>
                  </div>
                </button>
              ))}
            </div>
          </aside>

          <section className="min-h-[520px] rounded-md border border-zinc-800 bg-zinc-900/50 p-4">
            {selectedMatter ? <MatterDetail matter={selectedMatter} /> : <EmptyDetail loadState={loadState} />}
          </section>
        </section>

        <footer className="grid gap-3 py-5 md:grid-cols-2 lg:grid-cols-5">
          {Object.entries(files).map(([label, path]) => (
            <a key={label} className="flex min-h-20 flex-col justify-between rounded-md border border-zinc-800 bg-zinc-900/60 p-3 text-sm hover:border-orange-400" href={repoLink(path)} target="_blank" rel="noreferrer">
              <span className="font-medium text-zinc-100">{formatLabel(label)}</span>
              <span className="mt-2 inline-flex items-center gap-2 text-xs text-orange-300"><ExternalLink className="h-3.5 w-3.5" /> Open report</span>
            </a>
          ))}
        </footer>
      </div>
    </main>
  )
}

function Metric({ label, value }: { label: string; value: number }) {
  return (
    <div className="rounded-md border border-zinc-800 bg-zinc-900/70 p-4">
      <p className="text-xs font-medium uppercase tracking-wide text-zinc-400">{label}</p>
      <p className="mt-2 text-3xl font-semibold text-white">{value}</p>
    </div>
  )
}

function ControlSelect({ label, icon, value, onChange, options }: { label: string; icon: React.ReactNode; value: string; onChange: (value: string) => void; options: { label: string; value: string }[] }) {
  return (
    <label className="grid gap-2 text-xs font-medium uppercase tracking-wide text-zinc-400">
      <span className="inline-flex items-center gap-1.5">{icon}{label}</span>
      <select className="rounded-md border border-zinc-700 bg-zinc-950 px-2 py-2 text-sm normal-case tracking-normal text-zinc-100 outline-none" value={value} onChange={(event) => onChange(event.target.value)}>
        {options.map((option) => <option key={option.value} value={option.value}>{option.label}</option>)}
      </select>
    </label>
  )
}

function PanelNotice({ icon, title, text }: { icon: React.ReactNode; title: string; text: string }) {
  return (
    <div className="flex min-h-56 flex-col items-center justify-center gap-3 px-5 text-center text-zinc-400">
      <div className="text-orange-300">{icon}</div>
      <div>
        <p className="font-medium text-zinc-100">{title}</p>
        <p className="mt-1 text-sm leading-5">{text}</p>
      </div>
    </div>
  )
}

function EmptyDetail({ loadState }: { loadState: string }) {
  const title = loadState === 'missing' ? 'Dashboard data is pending' : 'Select a matter'
  const text = loadState === 'missing' ? 'The page is ready. The generated JSON will appear after the workflow runs and commits lifecycle output.' : 'Choose a matter from the left panel to inspect events and source links.'
  return <PanelNotice icon={<Database className="h-5 w-5" />} title={title} text={text} />
}

function MatterDetail({ matter }: { matter: Matter }) {
  return (
    <div className="flex h-full flex-col gap-4">
      <div className="flex flex-col gap-3 border-b border-zinc-800 pb-4 sm:flex-row sm:items-start sm:justify-between">
        <div>
          <h2 className="text-2xl font-semibold text-white">{formatLabel(matter.id)}</h2>
          <div className={`mt-2 inline-flex rounded border px-2 py-1 text-xs ${statusTone(matter.status)}`}>{formatLabel(matter.status)}</div>
        </div>
        <a className="inline-flex items-center gap-2 rounded-md border border-zinc-700 px-3 py-2 text-sm text-zinc-200 hover:border-orange-400 hover:text-white" href={repoLink(`upper-macleay-council-intelligence/${matter.chronologyPath}`)} target="_blank" rel="noreferrer">
          <FileText className="h-4 w-4" /> Chronology
        </a>
      </div>

      <div className="grid gap-3 sm:grid-cols-4">
        <Metric label="Heat Score" value={matter.score} />
        <Metric label="Evidence Refs" value={matter.evidenceReferences} />
        <Metric label="Action Signals" value={matter.actionSignals} />
        <Metric label="Events" value={matter.events} />
      </div>

      <div className="min-h-0 flex-1 overflow-y-auto rounded-md border border-zinc-800">
        {matter.eventList.length === 0 ? (
          <PanelNotice icon={<FileText className="h-5 w-5" />} title="No event sample yet" text="Lifecycle output has not produced event rows for this matter." />
        ) : (
          matter.eventList.map((event, index) => (
            <article key={`${event.date}-${event.kind}-${index}`} className="border-b border-zinc-800 p-4">
              <div className="flex flex-wrap items-center gap-2">
                <span className="rounded bg-zinc-950 px-2 py-1 text-xs text-zinc-300">{event.date || 'unknown-date'}</span>
                <span className="rounded bg-zinc-800 px-2 py-1 text-xs text-orange-200">{formatLabel(event.kind)}</span>
                <span className={`rounded border px-2 py-1 text-xs ${statusTone(event.status)}`}>{formatLabel(event.status)}</span>
              </div>
              {event.trigger && <p className="mt-3 text-sm text-zinc-200">Trigger: {event.trigger}</p>}
              {event.source && <a className="mt-2 inline-flex items-center gap-2 text-sm text-orange-300 hover:text-orange-200" href={event.source} target="_blank" rel="noreferrer"><ExternalLink className="h-4 w-4" /> Source record</a>}
            </article>
          ))
        )}
      </div>
    </div>
  )
}

export const Route = createFileRoute('/council-dashboard')({
  component: CouncilDashboard,
})
