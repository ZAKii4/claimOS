import { AlertTriangle } from "lucide-react";

interface RoadmapBannerProps {
  /** One short sentence on what's actually missing (e.g. "not yet wired to a persistent backend"). */
  reason: string;
}

/**
 * Honesty banner for pages that show illustrative/preview data rather than
 * data backed by a real, persistent system. Never hide this behind a toggle
 * or remove it silently — the whole point is that a viewer can tell, at a
 * glance, that what they're looking at isn't live production data.
 */
export function RoadmapBanner({ reason }: RoadmapBannerProps) {
  return (
    <div className="mb-6 flex items-start gap-3 rounded-lg border border-amber-300 bg-amber-50 px-4 py-3 text-amber-900 dark:border-amber-700 dark:bg-amber-950 dark:text-amber-200">
      <AlertTriangle className="mt-0.5 h-5 w-5 shrink-0" />
      <div className="text-sm">
        <span className="font-semibold">Roadmap preview.</span> This page shows
        illustrative data, not a live production feed — {reason}.
      </div>
    </div>
  );
}
