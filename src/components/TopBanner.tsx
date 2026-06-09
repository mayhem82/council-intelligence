import { useCallback } from 'react'
import { BarChart3, ExternalLink, X } from 'lucide-react'
import { useAppState } from '../store'

export function TopBanner() {
  const { isBannerVisible, setBannerVisible } = useAppState();

  const handleCloseBanner = useCallback(() => {
    setBannerVisible(false);
  }, [setBannerVisible]);

  if (!isBannerVisible) {
    return null;
  }

  return (
    <div className="relative w-full max-w-3xl px-4 py-3 mx-auto mt-4 mb-2 font-medium text-white bg-zinc-800 border border-orange-500/40 rounded-md text-sm">
      <button
        onClick={handleCloseBanner}
        className="absolute top-2 right-2 p-1 bg-zinc-700 hover:bg-zinc-600 rounded transition-colors"
        aria-label="Close banner"
      >
        <X className="w-4 h-4" />
      </button>
      <div className="flex flex-wrap items-center gap-3 pr-8">
        <a href="/council-dashboard" className="inline-flex items-center gap-2 rounded-md bg-orange-500 px-3 py-2 text-zinc-950 hover:bg-orange-400">
          <BarChart3 className="h-4 w-4" />
          Council dashboard
        </a>
        <a href="https://github.com/mayhem82/tanstack-template/blob/main/upper-macleay-council-intelligence/INTELLIGENCE-HOME.md" target="_blank" rel="noreferrer" className="inline-flex items-center gap-2 text-orange-200 underline-offset-4 hover:underline">
          <ExternalLink className="h-4 w-4" />
          Evidence repository
        </a>
      </div>
    </div>
  );
}
