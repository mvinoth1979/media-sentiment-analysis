import { useEffect, useState } from "react";
import { fetchBrandConfig, updateBrandConfig } from "../lib/api";

interface Props {
  brandId: string;
  brandName: string;
}

export function BrandConfig({ brandId, brandName }: Props) {
  const [loading, setLoading]               = useState(true);
  const [saving, setSaving]                 = useState(false);
  const [saved, setSaved]                   = useState(false);
  const [error, setError]                   = useState("");

  const [youtubeEnabled, setYoutubeEnabled]           = useState(false);
  const [channelIdsText, setChannelIdsText]           = useState("");
  const [redditEnabled, setRedditEnabled]             = useState(false);
  const [subredditsText, setSubredditsText]           = useState("");
  const [googleReviewsEnabled, setGoogleReviewsEnabled] = useState(false);
  const [googlePlacesId, setGooglePlacesId]           = useState("");

  useEffect(() => {
    setLoading(true);
    fetchBrandConfig(brandId)
      .then((cfg: Record<string, unknown>) => {
        setYoutubeEnabled(Boolean(cfg.youtube_enabled));
        setChannelIdsText(((cfg.youtube_channel_ids as string[]) || []).join("\n"));
        setRedditEnabled(Boolean(cfg.reddit_enabled));
        setSubredditsText(((cfg.reddit_subreddits as string[]) || []).join("\n"));
        setGoogleReviewsEnabled(Boolean(cfg.google_reviews_enabled));
        setGooglePlacesId((cfg.google_places_id as string) || "");
      })
      .catch(() => setError("Failed to load brand config."))
      .finally(() => setLoading(false));
  }, [brandId]);

  async function handleSave() {
    setSaving(true);
    setError("");
    setSaved(false);
    try {
      await updateBrandConfig(brandId, {
        youtube_enabled: youtubeEnabled,
        youtube_channel_ids: channelIdsText.split("\n").map(s => s.trim()).filter(Boolean),
        reddit_enabled: redditEnabled,
        reddit_subreddits: subredditsText.split("\n").map(s => s.trim().replace(/^r\//, "")).filter(Boolean),
        google_reviews_enabled: googleReviewsEnabled,
        google_places_id: googlePlacesId.trim(),
      });
      setSaved(true);
      setTimeout(() => setSaved(false), 3000);
    } catch {
      setError("Save failed — please try again.");
    } finally {
      setSaving(false);
    }
  }

  if (loading) return (
    <div className="flex items-center justify-center h-full text-sm text-gray-400">Loading config…</div>
  );

  return (
    <div className="max-w-xl mx-auto px-6 py-8">
      <h1 className="text-lg font-semibold text-gray-900 mb-1">Channel Settings</h1>
      <p className="text-sm text-gray-500 mb-8">
        Configure external monitoring channels for <span className="font-medium text-gray-700">{brandName}</span>.
      </p>

      {/* YouTube */}
      <section className="mb-8">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-2">
            <svg className="w-5 h-5 text-red-500" viewBox="0 0 24 24" fill="currentColor">
              <path d="M23.498 6.186a3.016 3.016 0 00-2.122-2.136C19.505 3.545 12 3.545 12 3.545s-7.505 0-9.377.505A3.017 3.017 0 00.502 6.186C0 8.07 0 12 0 12s0 3.93.502 5.814a3.016 3.016 0 002.122 2.136c1.871.505 9.376.505 9.376.505s7.505 0 9.377-.505a3.015 3.015 0 002.122-2.136C24 15.93 24 12 24 12s0-3.93-.502-5.814zM9.545 15.568V8.432L15.818 12l-6.273 3.568z" />
            </svg>
            <span className="text-sm font-semibold text-gray-800">YouTube</span>
          </div>
          <button
            onClick={() => setYoutubeEnabled(v => !v)}
            className={`relative inline-flex h-5 w-9 items-center rounded-full transition-colors ${youtubeEnabled ? "bg-red-500" : "bg-gray-200"}`}
          >
            <span className={`inline-block h-3.5 w-3.5 transform rounded-full bg-white shadow transition-transform ${youtubeEnabled ? "translate-x-4" : "translate-x-1"}`} />
          </button>
        </div>
        {youtubeEnabled && (
          <div>
            <label className="block text-xs font-medium text-gray-600 mb-1">
              Channel IDs <span className="text-gray-400">(one per line, optional)</span>
            </label>
            <textarea
              value={channelIdsText}
              onChange={e => setChannelIdsText(e.target.value)}
              rows={3}
              placeholder={"UCxxxxxxxxxxxxxxxxxxxxxx\nUCyyyyyyyyyyyyyyyyyyyyyy"}
              className="w-full text-sm border border-gray-200 rounded-lg px-3 py-2 font-mono text-gray-700 placeholder-gray-300 focus:outline-none focus:ring-2 focus:ring-red-400/50 resize-none"
            />
            <p className="text-[11px] text-gray-400 mt-1">Find channel ID in the channel URL after /channel/ or use a converter tool.</p>
          </div>
        )}
      </section>

      {/* Reddit */}
      <section className="mb-8">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-2">
            <svg className="w-5 h-5 text-orange-500" viewBox="0 0 24 24" fill="currentColor">
              <path d="M12 0A12 12 0 0 0 0 12a12 12 0 0 0 12 12 12 12 0 0 0 12-12A12 12 0 0 0 12 0zm5.01 4.744c.688 0 1.25.561 1.25 1.249a1.25 1.25 0 0 1-2.498.056l-2.597-.547-.8 3.747c1.824.07 3.48.632 4.674 1.488.308-.309.73-.491 1.207-.491.968 0 1.754.786 1.754 1.754 0 .716-.435 1.333-1.01 1.614a3.111 3.111 0 0 1 .042.52c0 2.694-3.13 4.87-7.004 4.87-3.874 0-7.004-2.176-7.004-4.87 0-.183.015-.366.043-.534A1.748 1.748 0 0 1 4.028 12c0-.968.786-1.754 1.754-1.754.463 0 .898.196 1.207.49 1.207-.883 2.878-1.43 4.744-1.487l.885-4.182a.342.342 0 0 1 .14-.197.35.35 0 0 1 .238-.042l2.906.617a1.214 1.214 0 0 1 1.108-.701zM9.25 12C8.561 12 8 12.562 8 13.25c0 .687.561 1.248 1.25 1.248.687 0 1.248-.561 1.248-1.249 0-.688-.561-1.249-1.249-1.249zm5.5 0c-.687 0-1.248.561-1.248 1.25 0 .687.561 1.248 1.249 1.248.688 0 1.249-.561 1.249-1.249 0-.687-.562-1.249-1.25-1.249zm-5.466 3.99a.327.327 0 0 0-.231.094.33.33 0 0 0 0 .463c.842.842 2.484.913 2.961.913.477 0 2.105-.056 2.961-.913a.361.361 0 0 0 .029-.463.33.33 0 0 0-.464 0c-.547.533-1.684.73-2.512.73-.828 0-1.979-.196-2.512-.73a.326.326 0 0 0-.232-.095z"/>
            </svg>
            <span className="text-sm font-semibold text-gray-800">Reddit</span>
          </div>
          <button
            onClick={() => setRedditEnabled(v => !v)}
            className={`relative inline-flex h-5 w-9 items-center rounded-full transition-colors ${redditEnabled ? "bg-orange-500" : "bg-gray-200"}`}
          >
            <span className={`inline-block h-3.5 w-3.5 transform rounded-full bg-white shadow transition-transform ${redditEnabled ? "translate-x-4" : "translate-x-1"}`} />
          </button>
        </div>
        {redditEnabled && (
          <div>
            <label className="block text-xs font-medium text-gray-600 mb-1">
              Subreddits to monitor <span className="text-gray-400">(one per line)</span>
            </label>
            <textarea
              value={subredditsText}
              onChange={e => setSubredditsText(e.target.value)}
              rows={5}
              placeholder={"india\nIndianStockMarket\nindiabusiness\nIndiaInvestments\nLegalAdviceIndia"}
              className="w-full text-sm border border-gray-200 rounded-lg px-3 py-2 font-mono text-gray-700 placeholder-gray-300 focus:outline-none focus:ring-2 focus:ring-orange-400/50 resize-none"
            />
            <p className="text-[11px] text-gray-400 mt-1">Enter without the r/ prefix. Posts from these subreddits matching your brand keywords will be collected hourly.</p>
          </div>
        )}
      </section>

      {/* Google Business Reviews */}
      <section className="mb-8">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-2">
            <svg className="w-5 h-5 text-blue-500" viewBox="0 0 24 24" fill="currentColor">
              <path d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z" fill="#4285F4"/>
              <path d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z" fill="#34A853"/>
              <path d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z" fill="#FBBC05"/>
              <path d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z" fill="#EA4335"/>
            </svg>
            <span className="text-sm font-semibold text-gray-800">Google Business Reviews</span>
          </div>
          <button
            onClick={() => setGoogleReviewsEnabled(v => !v)}
            className={`relative inline-flex h-5 w-9 items-center rounded-full transition-colors ${googleReviewsEnabled ? "bg-blue-500" : "bg-gray-200"}`}
          >
            <span className={`inline-block h-3.5 w-3.5 transform rounded-full bg-white shadow transition-transform ${googleReviewsEnabled ? "translate-x-4" : "translate-x-1"}`} />
          </button>
        </div>
        {googleReviewsEnabled && (
          <div>
            <label className="block text-xs font-medium text-gray-600 mb-1">
              Google Places ID <span className="text-gray-400">(optional — auto-resolved from brand name if blank)</span>
            </label>
            <input
              type="text"
              value={googlePlacesId}
              onChange={e => setGooglePlacesId(e.target.value)}
              placeholder="ChIJ..."
              className="w-full text-sm border border-gray-200 rounded-lg px-3 py-2 font-mono text-gray-700 placeholder-gray-300 focus:outline-none focus:ring-2 focus:ring-blue-400/50"
            />
            <p className="text-[11px] text-gray-400 mt-1">
              Leave blank to auto-resolve from the brand name. Find a specific ID at
              {" "}<a href="https://developers.google.com/maps/documentation/places/web-service/place-id" target="_blank" rel="noreferrer" className="underline">developers.google.com</a>.
            </p>
          </div>
        )}
      </section>

      {error && <p className="text-xs text-red-500 mb-4">{error}</p>}

      <div className="flex items-center gap-3">
        <button
          onClick={handleSave}
          disabled={saving}
          className="px-5 py-2 bg-indigo-600 hover:bg-indigo-700 text-white text-sm font-medium rounded-lg transition-colors disabled:opacity-50"
        >
          {saving ? "Saving…" : "Save Settings"}
        </button>
        {saved && <span className="text-xs text-green-600 font-medium">✓ Saved</span>}
      </div>
    </div>
  );
}
