import { Send } from 'lucide-react';
import { FloodwatchCanvas, type FloodwatchReading } from './FloodwatchCanvas';

const demoFloodwatchReading: FloodwatchReading = {
  latestTimestamp: '2024-05-18T05:30:00+10:00',
  latestLevelM: 2.31,
  deckM: 2.8,
  gapBelowDeckM: 0.49,
  pfhe: 1,
  fs: 96,
};

interface WelcomeScreenProps {
  input: string;
  setInput: (value: string) => void;
  handleSubmit: (e: React.FormEvent) => Promise<void>;
  isLoading: boolean;
}

export const WelcomeScreen = ({
  input,
  setInput,
  handleSubmit,
  isLoading
}: WelcomeScreenProps) => (
  <div className="flex items-center justify-center flex-1 px-4">
    <div className="w-full max-w-3xl mx-auto text-center">
      <h1 className="mb-4 text-6xl font-bold text-transparent uppercase bg-gradient-to-r from-orange-500 to-red-600 bg-clip-text">
        <span className="text-white">TanStack</span> Chat
      </h1>
      <p className="w-2/3 mx-auto mb-6 text-lg text-gray-400">
        You can ask me about anything, I might or might not have a good
        answer, but you can still ask.
      </p>
      <div className="px-6 py-5 mb-8 text-left rounded-2xl bg-slate-900/70 border border-slate-700/60">
        <h2 className="mb-4 text-xl font-semibold text-slate-100">
          Bellbrook Floodwatch canvas demo
        </h2>
        <div className="flex flex-col items-center gap-4">
          <FloodwatchCanvas {...demoFloodwatchReading} />
          <p className="text-sm leading-relaxed text-slate-300">
            The canvas visualises the latest Bureau of Meteorology feed you shared: it
            highlights the deck height ({demoFloodwatchReading.deckM.toFixed(2)}&nbsp;m),
            current level ({demoFloodwatchReading.latestLevelM.toFixed(2)}&nbsp;m), and
            remaining gap ({demoFloodwatchReading.gapBelowDeckM.toFixed(2)}&nbsp;m), along with the
            PF(H,E) and Factual Strength values. Swap in live data from
            <code className="px-1 ml-1 text-orange-200 rounded bg-orange-500/10">floodwatch_bellbrook.txt</code>
            to keep the display up to date.
          </p>
        </div>
      </div>
      <form onSubmit={handleSubmit}>
        <div className="relative max-w-xl mx-auto">
          <textarea
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault()
                handleSubmit(e)
              }
            }}
            placeholder="Type something clever (or don't, we won't judge)..."
            className="w-full py-3 pl-4 pr-12 overflow-hidden text-sm text-white placeholder-gray-400 border rounded-lg resize-none border-orange-500/20 bg-gray-800/50 focus:outline-none focus:ring-2 focus:ring-orange-500/50 focus:border-transparent"
            rows={1}
            style={{ minHeight: '88px' }}
          />
          <button
            type="submit"
            disabled={!input.trim() || isLoading}
            className="absolute p-2 text-orange-500 transition-colors -translate-y-1/2 right-2 top-1/2 hover:text-orange-400 disabled:text-gray-500 focus:outline-none"
          >
            <Send className="w-4 h-4" />
          </button>
        </div>
      </form>
    </div>
  </div>
); 