import { useEffect, useState, type ReactNode } from "react";
import { fetchBrandConfig, updateBrandConfig } from "../lib/api";

interface Props {
  brandId: string;
  brandName: string;
}

function Toggle({ on, onChange, color = "bg-indigo-500" }: { on: boolean; onChange: () => void; color?: string }) {
  return (
    <button
      onClick={onChange}
      className={`relative inline-flex h-5 w-9 items-center rounded-full transition-colors ${on ? color : "bg-gray-200"}`}
    >
      <span className={`inline-block h-3.5 w-3.5 transform rounded-full bg-white shadow transition-transform ${on ? "translate-x-4" : "translate-x-1"}`} />
    </button>
  );
}

function SectionHeader({ icon, label, enabled, onToggle, color }: {
  icon: ReactNode; label: string; enabled: boolean; onToggle: () => void; color?: string;
}) {
  return (
    <div className="flex items-center justify-between mb-4">
      <div className="flex items-center gap-2">
        {icon}
        <span className="text-sm font-semibold text-gray-800">{label}</span>
      </div>
      <Toggle on={enabled} onChange={onToggle} color={color} />
    </div>
  );
}

function Field({ label, hint, children }: { label: string; hint?: string; children: React.ReactNode }) {
  return (
    <div>
      <label className="block text-xs font-medium text-gray-600 mb-1">{label}</label>
      {children}
      {hint && <p className="text-[11px] text-gray-400 mt-1">{hint}</p>}
    </div>
  );
}

export function BrandConfig({ brandId, brandName }: Props) {
  const [loading, setLoading] = useState(true);
  const [saving, setSaving]   = useState(false);
  const [saved, setSaved]     = useState(false);
  const [error, setError]     = useState("");

  // YouTube
  const [youtubeEnabled, setYoutubeEnabled]   = useState(false);
  const [channelIdsText, setChannelIdsText]   = useState("");
  // Reddit
  const [redditEnabled, setRedditEnabled]     = useState(false);
  const [subredditsText, setSubredditsText]   = useState("");
  // Google Reviews
  const [googleEnabled, setGoogleEnabled]     = useState(false);
  const [googlePlacesId, setGooglePlacesId]   = useState("");
  // Trustpilot
  const [tpEnabled, setTpEnabled]             = useState(false);
  const [tpDomain, setTpDomain]               = useState("");
  // MouthShut
  const [msEnabled, setMsEnabled]             = useState(false);
  const [msSlug, setMsSlug]                   = useState("");
  // JustDial
  const [jdEnabled, setJdEnabled]             = useState(false);
  const [jdUrl, setJdUrl]                     = useState("");
  // AmbitionBox
  const [abEnabled, setAbEnabled]             = useState(false);
  const [abSlug, setAbSlug]                   = useState("");
  // TripAdvisor
  const [taEnabled, setTaEnabled]             = useState(false);
  const [taUrl, setTaUrl]                     = useState("");
  // Team-BHP
  const [tbhpEnabled, setTbhpEnabled]         = useState(false);
  const [tbhpKeywords, setTbhpKeywords]       = useState("");
  // Play Store
  const [psEnabled, setPsEnabled]             = useState(false);
  const [psAppId, setPsAppId]                 = useState("");

  useEffect(() => {
    setLoading(true);
    fetchBrandConfig(brandId)
      .then((cfg: Record<string, unknown>) => {
        setYoutubeEnabled(Boolean(cfg.youtube_enabled));
        setChannelIdsText(((cfg.youtube_channel_ids as string[]) || []).join("\n"));
        setRedditEnabled(Boolean(cfg.reddit_enabled));
        setSubredditsText(((cfg.reddit_subreddits as string[]) || []).join("\n"));
        setGoogleEnabled(Boolean(cfg.google_reviews_enabled));
        setGooglePlacesId((cfg.google_places_id as string) || "");
        setTpEnabled(Boolean(cfg.trustpilot_enabled));
        setTpDomain((cfg.trustpilot_domain as string) || "");
        setMsEnabled(Boolean(cfg.mouthshut_enabled));
        setMsSlug((cfg.mouthshut_slug as string) || "");
        setJdEnabled(Boolean(cfg.justdial_enabled));
        setJdUrl((cfg.justdial_listing_url as string) || "");
        setAbEnabled(Boolean(cfg.ambitionbox_enabled));
        setAbSlug((cfg.ambitionbox_slug as string) || "");
        setTaEnabled(Boolean(cfg.tripadvisor_enabled));
        setTaUrl((cfg.tripadvisor_listing_url as string) || "");
        setTbhpEnabled(Boolean(cfg.team_bhp_enabled));
        setTbhpKeywords(((cfg.team_bhp_keywords as string[]) || []).join("\n"));
        setPsEnabled(Boolean(cfg.play_store_enabled));
        setPsAppId((cfg.play_store_app_id as string) || "");
      })
      .catch(() => setError("Failed to load brand config."))
      .finally(() => setLoading(false));
  }, [brandId]);

  async function handleSave() {
    setSaving(true); setError(""); setSaved(false);
    try {
      await updateBrandConfig(brandId, {
        youtube_enabled: youtubeEnabled,
        youtube_channel_ids: channelIdsText.split("\n").map(s => s.trim()).filter(Boolean),
        reddit_enabled: redditEnabled,
        reddit_subreddits: subredditsText.split("\n").map(s => s.trim().replace(/^r\//, "")).filter(Boolean),
        google_reviews_enabled: googleEnabled,
        google_places_id: googlePlacesId.trim(),
        trustpilot_enabled: tpEnabled,
        trustpilot_domain: tpDomain.trim(),
        mouthshut_enabled: msEnabled,
        mouthshut_slug: msSlug.trim(),
        justdial_enabled: jdEnabled,
        justdial_listing_url: jdUrl.trim(),
        ambitionbox_enabled: abEnabled,
        ambitionbox_slug: abSlug.trim(),
        tripadvisor_enabled: taEnabled,
        tripadvisor_listing_url: taUrl.trim(),
        team_bhp_enabled: tbhpEnabled,
        team_bhp_keywords: tbhpKeywords.split("\n").map(s => s.trim()).filter(Boolean),
        play_store_enabled: psEnabled,
        play_store_app_id: psAppId.trim(),
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

  const inputCls = "w-full text-sm border border-gray-200 rounded-lg px-3 py-2 font-mono text-gray-700 placeholder-gray-300 focus:outline-none focus:ring-2 focus:ring-indigo-400/50";

  return (
    <div className="max-w-xl mx-auto px-6 py-8">
      <h1 className="text-lg font-semibold text-gray-900 mb-1">Channel Settings</h1>
      <p className="text-sm text-gray-500 mb-8">
        Configure external monitoring channels for <span className="font-medium text-gray-700">{brandName}</span>.
      </p>

      {/* ── YouTube ─────────────────────────────────────────────────── */}
      <section className="mb-8">
        <SectionHeader
          label="YouTube"
          enabled={youtubeEnabled}
          onToggle={() => setYoutubeEnabled(v => !v)}
          color="bg-red-500"
          icon={<svg className="w-5 h-5 text-red-500" viewBox="0 0 24 24" fill="currentColor"><path d="M23.498 6.186a3.016 3.016 0 00-2.122-2.136C19.505 3.545 12 3.545 12 3.545s-7.505 0-9.377.505A3.017 3.017 0 00.502 6.186C0 8.07 0 12 0 12s0 3.93.502 5.814a3.016 3.016 0 002.122 2.136c1.871.505 9.376.505 9.376.505s7.505 0 9.377-.505a3.015 3.015 0 002.122-2.136C24 15.93 24 12 24 12s0-3.93-.502-5.814zM9.545 15.568V8.432L15.818 12l-6.273 3.568z"/></svg>}
        />
        {youtubeEnabled && (
          <Field label="Channel IDs" hint="Find channel ID in the channel URL after /channel/ or use a converter tool.">
            <textarea value={channelIdsText} onChange={e => setChannelIdsText(e.target.value)}
              rows={3} placeholder={"UCxxxxxxxxxxxxxxxxxxxxxx\nUCyyyyyyyyyyyyyyyyyyyyyy"}
              className={inputCls + " resize-none focus:ring-red-400/50"} />
          </Field>
        )}
      </section>

      {/* ── Reddit ──────────────────────────────────────────────────── */}
      <section className="mb-8">
        <SectionHeader
          label="Reddit"
          enabled={redditEnabled}
          onToggle={() => setRedditEnabled(v => !v)}
          color="bg-orange-500"
          icon={<svg className="w-5 h-5 text-orange-500" viewBox="0 0 24 24" fill="currentColor"><path d="M12 0A12 12 0 0 0 0 12a12 12 0 0 0 12 12 12 12 0 0 0 12-12A12 12 0 0 0 12 0zm5.01 4.744c.688 0 1.25.561 1.25 1.249a1.25 1.25 0 0 1-2.498.056l-2.597-.547-.8 3.747c1.824.07 3.48.632 4.674 1.488.308-.309.73-.491 1.207-.491.968 0 1.754.786 1.754 1.754 0 .716-.435 1.333-1.01 1.614a3.111 3.111 0 0 1 .042.52c0 2.694-3.13 4.87-7.004 4.87-3.874 0-7.004-2.176-7.004-4.87 0-.183.015-.366.043-.534A1.748 1.748 0 0 1 4.028 12c0-.968.786-1.754 1.754-1.754.463 0 .898.196 1.207.49 1.207-.883 2.878-1.43 4.744-1.487l.885-4.182a.342.342 0 0 1 .14-.197.35.35 0 0 1 .238-.042l2.906.617a1.214 1.214 0 0 1 1.108-.701zM9.25 12C8.561 12 8 12.562 8 13.25c0 .687.561 1.248 1.25 1.248.687 0 1.248-.561 1.248-1.249 0-.688-.561-1.249-1.249-1.249zm5.5 0c-.687 0-1.248.561-1.248 1.25 0 .687.561 1.248 1.249 1.248.688 0 1.249-.561 1.249-1.249 0-.687-.562-1.249-1.25-1.249zm-5.466 3.99a.327.327 0 0 0-.231.094.33.33 0 0 0 0 .463c.842.842 2.484.913 2.961.913.477 0 2.105-.056 2.961-.913a.361.361 0 0 0 .029-.463.33.33 0 0 0-.464 0c-.547.533-1.684.73-2.512.73-.828 0-1.979-.196-2.512-.73a.326.326 0 0 0-.232-.095z"/></svg>}
        />
        {redditEnabled && (
          <Field label="Subreddits to monitor" hint="Enter without the r/ prefix. Posts matching brand keywords collected hourly.">
            <textarea value={subredditsText} onChange={e => setSubredditsText(e.target.value)}
              rows={4} placeholder={"india\nIndianStockMarket\nindiabusiness"}
              className={inputCls + " resize-none focus:ring-orange-400/50"} />
          </Field>
        )}
      </section>

      {/* ── Google Business Reviews ──────────────────────────────────── */}
      <section className="mb-8">
        <SectionHeader
          label="Google Business Reviews"
          enabled={googleEnabled}
          onToggle={() => setGoogleEnabled(v => !v)}
          color="bg-blue-500"
          icon={<svg className="w-5 h-5" viewBox="0 0 24 24" fill="currentColor"><path d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z" fill="#4285F4"/><path d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z" fill="#34A853"/><path d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z" fill="#FBBC05"/><path d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z" fill="#EA4335"/></svg>}
        />
        {googleEnabled && (
          <Field label="Google Places ID" hint="Leave blank to auto-resolve from brand name. Find a specific ID at developers.google.com/maps/documentation/places.">
            <input type="text" value={googlePlacesId} onChange={e => setGooglePlacesId(e.target.value)}
              placeholder="ChIJ..."
              className={inputCls + " focus:ring-blue-400/50"} />
          </Field>
        )}
      </section>

      <div className="border-t border-gray-100 my-8" />
      <h2 className="text-xs font-semibold text-gray-400 uppercase tracking-wider mb-6">Review Sites</h2>

      {/* ── Trustpilot ──────────────────────────────────────────────── */}
      <section className="mb-8">
        <SectionHeader
          label="Trustpilot"
          enabled={tpEnabled}
          onToggle={() => setTpEnabled(v => !v)}
          color="bg-emerald-500"
          icon={<svg className="w-5 h-5 text-emerald-500" viewBox="0 0 24 24" fill="currentColor"><path d="M12 2l2.4 7.4H22l-6.2 4.5 2.4 7.4L12 17l-6.2 4.3 2.4-7.4L2 9.4h7.6z"/></svg>}
        />
        {tpEnabled && (
          <Field
            label="Company domain"
            hint="Enter the domain registered on Trustpilot (e.g. marutisuzuki.com). The business unit ID is cached automatically on first run."
          >
            <input type="text" value={tpDomain} onChange={e => setTpDomain(e.target.value)}
              placeholder="example.com"
              className={inputCls + " focus:ring-emerald-400/50"} />
          </Field>
        )}
      </section>

      {/* ── MouthShut ───────────────────────────────────────────────── */}
      <section className="mb-8">
        <SectionHeader
          label="MouthShut"
          enabled={msEnabled}
          onToggle={() => setMsEnabled(v => !v)}
          color="bg-yellow-500"
          icon={<svg className="w-5 h-5 text-yellow-500" viewBox="0 0 24 24" fill="currentColor"><path d="M20 2H4c-1.1 0-2 .9-2 2v18l4-4h14c1.1 0 2-.9 2-2V4c0-1.1-.9-2-2-2z"/></svg>}
        />
        {msEnabled && (
          <Field
            label="MouthShut review slug"
            hint={`Full slug from the MouthShut URL: mouthshut.com/product-reviews/{slug}. Include the numeric ID at the end (e.g. brand-name-reviews-925925714).`}
          >
            <input type="text" value={msSlug} onChange={e => setMsSlug(e.target.value)}
              placeholder="brand-name-reviews-925925714"
              className={inputCls + " focus:ring-yellow-400/50"} />
          </Field>
        )}
      </section>

      {/* ── JustDial ────────────────────────────────────────────────── */}
      <section className="mb-8">
        <SectionHeader
          label="JustDial"
          enabled={jdEnabled}
          onToggle={() => setJdEnabled(v => !v)}
          color="bg-purple-500"
          icon={<svg className="w-5 h-5 text-purple-500" viewBox="0 0 24 24" fill="currentColor"><path d="M12 2C8.13 2 5 5.13 5 9c0 5.25 7 13 7 13s7-7.75 7-13c0-3.87-3.13-7-7-7zm0 9.5c-1.38 0-2.5-1.12-2.5-2.5S10.62 6.5 12 6.5s2.5 1.12 2.5 2.5S13.38 11.5 12 11.5z"/></svg>}
        />
        {jdEnabled && (
          <Field
            label="JustDial listing URL"
            hint="Full URL of the business listing on JustDial (e.g. https://www.justdial.com/Chennai/Brand-Name/nct-10968458). Must be a specific listing page, not a search result."
          >
            <input type="text" value={jdUrl} onChange={e => setJdUrl(e.target.value)}
              placeholder="https://www.justdial.com/..."
              className={inputCls + " focus:ring-purple-400/50"} />
          </Field>
        )}
      </section>

      {/* ── AmbitionBox ─────────────────────────────────────────────── */}
      <section className="mb-8">
        <SectionHeader
          label="AmbitionBox"
          enabled={abEnabled}
          onToggle={() => setAbEnabled(v => !v)}
          color="bg-blue-600"
          icon={<svg className="w-5 h-5 text-blue-600" viewBox="0 0 24 24" fill="currentColor"><path d="M20 6h-2.18c.07-.44.18-.88.18-1.34C18 2.54 15.76.5 13.5.5c-1.34 0-2.5.56-3.36 1.44L9 3.06 7.86 1.94C6.96 1.06 5.76.5 4.5.5 2.24.5 0 2.54 0 4.66 0 5.12.11 5.56.18 6H0v2h20V6zm-5.5 0h-3V4.66C11.5 3.75 12.42 3 13.5 3s2 .75 2 1.66C15.5 5.12 15.39 5.56 14.5 6z M0 8v12h20V8H0zm4 10H2v-8h2v8zm4 0H6v-8h2v8zm4 0h-2v-8h2v8zm4 0h-2v-8h2v8zm4 0h-2v-8h2v8z"/></svg>}
        />
        {abEnabled && (
          <Field
            label="AmbitionBox company slug"
            hint="Slug from the AmbitionBox URL: ambitionbox.com/reviews/{slug} (e.g. tata-motors, maruti-suzuki-india)."
          >
            <input type="text" value={abSlug} onChange={e => setAbSlug(e.target.value)}
              placeholder="company-name"
              className={inputCls + " focus:ring-blue-500/50"} />
          </Field>
        )}
      </section>

      {/* ── TripAdvisor ──────────────────────────────────────────────── */}
      <section className="mb-8">
        <SectionHeader
          label="TripAdvisor"
          enabled={taEnabled}
          onToggle={() => setTaEnabled(v => !v)}
          color="bg-green-600"
          icon={<svg className="w-5 h-5 text-green-600" viewBox="0 0 24 24" fill="currentColor"><path d="M12 2C8.13 2 4.5 4.13 4.5 7.5c0 3.38 3.63 5.5 7.5 5.5s7.5-2.12 7.5-5.5C19.5 4.13 15.87 2 12 2zm0 9c-2.21 0-4-1.79-4-4s1.79-4 4-4 4 1.79 4 4-1.79 4-4 4zm0-6c-1.1 0-2 .9-2 2s.9 2 2 2 2-.9 2-2-.9-2-2-2zM6 14.5c-2.21 0-4 1.79-4 4S3.79 22.5 6 22.5s4-1.79 4-4-1.79-4-4-4zm0 6c-1.1 0-2-.9-2-2s.9-2 2-2 2 .9 2 2-.9 2-2 2zm12-6c-2.21 0-4 1.79-4 4s1.79 4 4 4 4-1.79 4-4-1.79-4-4-4zm0 6c-1.1 0-2-.9-2-2s.9-2 2-2 2 .9 2 2-.9 2-2 2z"/></svg>}
        />
        {taEnabled && (
          <Field
            label="TripAdvisor listing URL"
            hint="Full URL of the attraction, hotel or business listing on TripAdvisor."
          >
            <input type="text" value={taUrl} onChange={e => setTaUrl(e.target.value)}
              placeholder="https://www.tripadvisor.in/Attraction_Review-..."
              className={inputCls + " focus:ring-green-500/50"} />
          </Field>
        )}
      </section>

      {/* ── Team-BHP ────────────────────────────────────────────────── */}
      <section className="mb-8">
        <SectionHeader
          label="Team-BHP"
          enabled={tbhpEnabled}
          onToggle={() => setTbhpEnabled(v => !v)}
          color="bg-red-700"
          icon={<svg className="w-5 h-5 text-red-700" viewBox="0 0 24 24" fill="currentColor"><path d="M18.92 6.01C18.72 5.42 18.16 5 17.5 5h-11c-.66 0-1.21.42-1.42 1.01L3 12v8c0 .55.45 1 1 1h1c.55 0 1-.45 1-1v-1h12v1c0 .55.45 1 1 1h1c.55 0 1-.45 1-1v-8l-2.08-5.99zM6.5 16c-.83 0-1.5-.67-1.5-1.5S5.67 13 6.5 13s1.5.67 1.5 1.5S7.33 16 6.5 16zm11 0c-.83 0-1.5-.67-1.5-1.5s.67-1.5 1.5-1.5 1.5.67 1.5 1.5-.67 1.5-1.5 1.5zM5 11l1.5-4.5h11L19 11H5z"/></svg>}
        />
        {tbhpEnabled && (
          <Field
            label="Search keywords"
            hint="One model/sub-brand per line. The collector searches Team-BHP for each term and de-dupes. E.g. Maruti Swift, Maruti Baleno, WagonR."
          >
            <textarea value={tbhpKeywords} onChange={e => setTbhpKeywords(e.target.value)}
              rows={4} placeholder={"Maruti Swift\nMaruti Baleno\nWagonR\nErtiga"}
              className={inputCls + " resize-none focus:ring-red-600/50"} />
          </Field>
        )}
      </section>

      {/* ── Google Play Store ───────────────────────────────────────── */}
      <section className="mb-8">
        <SectionHeader
          label="Google Play Store"
          enabled={psEnabled}
          onToggle={() => setPsEnabled(v => !v)}
          color="bg-lime-500"
          icon={<svg className="w-5 h-5" viewBox="0 0 24 24" fill="currentColor"><path d="M3.18 23.76a1.5 1.5 0 0 1-.68-.16A1.56 1.56 0 0 1 1.75 22V2a1.56 1.56 0 0 1 .75-1.6 1.5 1.5 0 0 1 1.56.07l18 10a1.56 1.56 0 0 1 0 2.7l-18 10a1.5 1.5 0 0 1-.88.59z" fill="#00C853"/></svg>}
        />
        {psEnabled && (
          <Field
            label="App package name"
            hint="Package name from the Play Store URL: play.google.com/store/apps/details?id=com.example.app — e.g. com.jio.myjio, com.iob.mobilebanking."
          >
            <input type="text" value={psAppId} onChange={e => setPsAppId(e.target.value)}
              placeholder="com.example.appname"
              className={inputCls + " focus:ring-lime-400/50"} />
          </Field>
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
