export function formatCount(n: number): string {
  if (n >= 1_000_000) return `${(n / 1_000_000).toFixed(1)}M`;
  if (n >= 1_000) return `${Math.round(n / 1_000)}K`;
  return String(n);
}

/**
 * Maps existing 3-label + 0–1 score to a 5-level intensity.
 * Avoids NLP rescore — uses the score already stored on each article.
 */
export function sentimentIntensity(
  label: string,
  score: number
): { text: string; color: string; bg: string } {
  if (label === "positive") {
    return score >= 0.75
      ? { text: "Strongly Positive", color: "text-emerald-400", bg: "bg-emerald-900/40" }
      : { text: "Mildly Positive",   color: "text-green-400",   bg: "bg-green-900/30"   };
  }
  if (label === "negative") {
    return score <= 0.25
      ? { text: "Strongly Negative", color: "text-red-400",    bg: "bg-red-900/50"      }
      : { text: "Mildly Negative",   color: "text-orange-400", bg: "bg-orange-900/30"   };
  }
  return { text: "Neutral", color: "text-yellow-400", bg: "bg-yellow-900/30" };
}

/** Source Authority Tier badge style (Web Framework §1.4). */
export function tierBadge(tier: number): { label: string; color: string; bg: string } {
  switch (tier) {
    case 1:  return { label: "Tier 1",  color: "text-violet-300", bg: "bg-violet-900/40" };
    case 2:  return { label: "Tier 2",  color: "text-blue-300",   bg: "bg-blue-900/30"   };
    case 3:  return { label: "Tier 3",  color: "text-gray-300",   bg: "bg-gray-800"      };
    case 4:  return { label: "Tier 4",  color: "text-gray-500",   bg: "bg-gray-900"      };
    case 5:  return { label: "Wire",    color: "text-amber-700",  bg: "bg-amber-50"      };
    default: return { label: "YouTube", color: "text-red-400",    bg: "bg-red-900/30"    };
  }
}

/** YouTube reach tier badge (YouTube Framework §4 virality proxy). */
export function reachBadge(tier: string): { label: string; color: string } {
  switch (tier) {
    case "High":   return { label: "High Reach",   color: "text-orange-400" };
    case "Medium": return { label: "Medium Reach", color: "text-yellow-400" };
    default:       return { label: "Low Reach",    color: "text-gray-500"   };
  }
}
