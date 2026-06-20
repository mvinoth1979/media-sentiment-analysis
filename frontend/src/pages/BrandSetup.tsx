import { useState } from "react";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { createBrand } from "../lib/api";
import { YouTubeIcon } from "../components/ui/YouTubeIcon";

const LANGUAGES = [
  { code: "en", label: "English" },
  { code: "ta", label: "Tamil" },
  { code: "hi", label: "Hindi" },
  { code: "gu", label: "Gujarati" },
  { code: "bn", label: "Bengali" },
  { code: "kn", label: "Kannada" },
];

interface Props {
  onSuccess: (brandId: string, brandName: string) => void;
  onClose: () => void;
}

export function BrandSetup({ onSuccess, onClose }: Props) {
  const [step, setStep]               = useState<1 | 2 | 3 | 4>(1);
  const [name, setName]               = useState("");
  const [kwInput, setKwInput]         = useState("");
  const [keywords, setKeywords]       = useState<string[]>([]);
  const [languages, setLanguages]     = useState<string[]>(["en"]);
  const [youtubeEnabled, setYoutubeEnabled] = useState(false);
  const [channelInput, setChannelInput]     = useState("");
  const [channelIds, setChannelIds]         = useState<string[]>([]);
  const [redditEnabled, setRedditEnabled]   = useState(false);
  const [subredditsText, setSubredditsText] = useState("");
  const [error, setError]             = useState("");

  const queryClient = useQueryClient();

  const mutation = useMutation({
    mutationFn: () => createBrand({
      name: name.trim(),
      keywords,
      languages,
      youtube_enabled: youtubeEnabled,
      youtube_channel_ids: channelIds,
      reddit_enabled: redditEnabled,
      reddit_subreddits: subredditsText
        .split("\n")
        .map(s => s.trim().replace(/^r\//, ""))
        .filter(Boolean),
    }),
    onSuccess: (brand) => {
      queryClient.invalidateQueries({ queryKey: ["brands"] });
      onSuccess(brand.id, brand.name);
    },
    onError: (e: Error) => setError(e.message),
  });

  function addKeyword() {
    const kw = kwInput.trim();
    if (kw && !keywords.includes(kw)) setKeywords(prev => [...prev, kw]);
    setKwInput("");
  }

  function toggleLang(code: string) {
    setLanguages(prev =>
      prev.includes(code) ? prev.filter(l => l !== code) : [...prev, code]
    );
  }

  function addChannelId() {
    const id = channelInput.trim();
    if (id && !channelIds.includes(id)) setChannelIds(prev => [...prev, id]);
    setChannelInput("");
  }

  const STEP_LABELS: Record<number, string> = {
    1: "Brand name",
    2: "Keywords",
    3: "Languages",
    4: "External Channels",
  };

  return (
    <div className="fixed inset-0 bg-black/70 flex items-center justify-center z-50 p-4">
      <div className="bg-gray-900 border border-gray-700 rounded-2xl w-full max-w-md p-6 space-y-5">
        {/* Header */}
        <div className="flex items-center justify-between">
          <h2 className="text-lg font-semibold text-gray-100">Add New Brand</h2>
          <button onClick={onClose} className="text-gray-500 hover:text-gray-300 text-xl leading-none">×</button>
        </div>

        {/* Step indicator — 4 steps */}
        <div className="flex gap-2">
          {([1, 2, 3, 4] as const).map(s => (
            <div key={s} className={`h-1 flex-1 rounded-full transition-colors ${
              s <= step ? "bg-indigo-500" : "bg-gray-700"
            }`} />
          ))}
        </div>
        <p className="text-xs text-gray-500">Step {step} of 4 — {STEP_LABELS[step]}</p>

        {/* Step 1: Brand name */}
        {step === 1 && (
          <div className="space-y-3">
            <label className="block text-sm text-gray-300">Brand name</label>
            <input
              autoFocus
              type="text"
              value={name}
              onChange={e => setName(e.target.value)}
              onKeyDown={e => e.key === "Enter" && name.trim() && setStep(2)}
              placeholder="e.g. Tata Motors"
              className="w-full bg-gray-800 border border-gray-700 rounded-lg text-sm text-gray-100 px-3 py-2 focus:outline-none focus:border-indigo-500 placeholder:text-gray-600"
            />
            <button
              onClick={() => name.trim() && setStep(2)}
              disabled={!name.trim()}
              className="w-full py-2 bg-indigo-600 hover:bg-indigo-500 text-white text-sm rounded-lg disabled:opacity-40 transition-colors"
            >
              Next →
            </button>
          </div>
        )}

        {/* Step 2: Keywords */}
        {step === 2 && (
          <div className="space-y-3">
            <label className="block text-sm text-gray-300">
              Keywords <span className="text-gray-500 font-normal">(brand name variants, products, spokespeople)</span>
            </label>
            <div className="flex gap-2">
              <input
                autoFocus
                type="text"
                value={kwInput}
                onChange={e => setKwInput(e.target.value)}
                onKeyDown={e => e.key === "Enter" && (e.preventDefault(), addKeyword())}
                placeholder="Type and press Enter"
                className="flex-1 bg-gray-800 border border-gray-700 rounded-lg text-sm text-gray-100 px-3 py-2 focus:outline-none focus:border-indigo-500 placeholder:text-gray-600"
              />
              <button
                onClick={addKeyword}
                className="px-3 py-2 bg-gray-700 hover:bg-gray-600 text-gray-200 text-sm rounded-lg transition-colors"
              >
                Add
              </button>
            </div>
            {keywords.length > 0 && (
              <div className="flex flex-wrap gap-2">
                {keywords.map(kw => (
                  <span key={kw} className="flex items-center gap-1 text-xs bg-indigo-900/40 border border-indigo-700/50 text-indigo-300 px-2 py-1 rounded-full">
                    {kw}
                    <button onClick={() => setKeywords(prev => prev.filter(k => k !== kw))}
                      className="text-indigo-400 hover:text-white leading-none">×</button>
                  </span>
                ))}
              </div>
            )}
            <div className="flex gap-2 pt-1">
              <button onClick={() => setStep(1)}
                className="flex-1 py-2 border border-gray-700 text-gray-400 text-sm rounded-lg hover:border-gray-500 transition-colors">
                ← Back
              </button>
              <button
                onClick={() => setStep(3)}
                disabled={keywords.length === 0}
                className="flex-1 py-2 bg-indigo-600 hover:bg-indigo-500 text-white text-sm rounded-lg disabled:opacity-40 transition-colors"
              >
                Next →
              </button>
            </div>
          </div>
        )}

        {/* Step 3: Languages */}
        {step === 3 && (
          <div className="space-y-3">
            <label className="block text-sm text-gray-300">Languages to monitor</label>
            <div className="grid grid-cols-2 gap-2">
              {LANGUAGES.map(({ code, label }) => (
                <label key={code}
                  className={`flex items-center gap-2 px-3 py-2 rounded-lg border cursor-pointer transition-colors ${
                    languages.includes(code)
                      ? "border-indigo-500 bg-indigo-900/30 text-indigo-200"
                      : "border-gray-700 text-gray-400 hover:border-gray-500"
                  }`}>
                  <input type="checkbox" checked={languages.includes(code)}
                    onChange={() => toggleLang(code)} className="accent-indigo-500" />
                  <span className="text-sm">{label}</span>
                </label>
              ))}
            </div>
            <div className="flex gap-2 pt-1">
              <button onClick={() => setStep(2)}
                className="flex-1 py-2 border border-gray-700 text-gray-400 text-sm rounded-lg hover:border-gray-500 transition-colors">
                ← Back
              </button>
              <button
                onClick={() => setStep(4)}
                disabled={languages.length === 0}
                className="flex-1 py-2 bg-indigo-600 hover:bg-indigo-500 text-white text-sm rounded-lg disabled:opacity-40 transition-colors"
              >
                Next →
              </button>
            </div>
          </div>
        )}

        {/* Step 4: YouTube */}
        {step === 4 && (
          <div className="space-y-4">
            {/* YouTube toggle */}
            <label className="flex items-center gap-3 p-3 rounded-lg border border-gray-700 hover:border-gray-600 cursor-pointer transition-colors">
              <div className={`relative w-10 h-5 rounded-full transition-colors shrink-0 ${
                youtubeEnabled ? "bg-red-600" : "bg-gray-700"
              }`}>
                <div className={`absolute top-0.5 w-4 h-4 rounded-full bg-white shadow transition-transform ${
                  youtubeEnabled ? "translate-x-5" : "translate-x-0.5"
                }`} />
                <input
                  type="checkbox"
                  checked={youtubeEnabled}
                  onChange={e => setYoutubeEnabled(e.target.checked)}
                  className="sr-only"
                />
              </div>
              <div>
                <div className="flex items-center gap-1.5 text-sm text-gray-200">
                  <YouTubeIcon className="inline w-4 h-4" />
                  Monitor YouTube
                </div>
                <p className="text-xs text-gray-500 mt-0.5">
                  Collect videos and comments mentioning this brand
                </p>
              </div>
            </label>

            {/* Channel IDs — only shown when YouTube is enabled */}
            {youtubeEnabled && (
              <div className="space-y-2 pl-1">
                <label className="block text-xs text-gray-400">
                  YouTube Channel IDs{" "}
                  <span className="text-gray-600 font-normal">(optional — add the brand's own channels)</span>
                </label>
                <div className="flex gap-2">
                  <input
                    autoFocus
                    type="text"
                    value={channelInput}
                    onChange={e => setChannelInput(e.target.value)}
                    onKeyDown={e => e.key === "Enter" && (e.preventDefault(), addChannelId())}
                    placeholder="UCxxxxxxxxxxxxxxxxxxxxxx"
                    className="flex-1 bg-gray-800 border border-gray-700 rounded-lg text-sm text-gray-100 px-3 py-2 focus:outline-none focus:border-red-500 placeholder:text-gray-600 font-mono text-xs"
                  />
                  <button
                    onClick={addChannelId}
                    className="px-3 py-2 bg-gray-700 hover:bg-gray-600 text-gray-200 text-sm rounded-lg transition-colors"
                  >
                    Add
                  </button>
                </div>
                {channelIds.length > 0 && (
                  <div className="flex flex-wrap gap-2">
                    {channelIds.map(id => (
                      <span key={id} className="flex items-center gap-1 text-xs bg-red-900/30 border border-red-800/40 text-red-300 px-2 py-1 rounded-full font-mono">
                        {id.length > 16 ? `${id.slice(0, 16)}…` : id}
                        <button onClick={() => setChannelIds(prev => prev.filter(c => c !== id))}
                          className="text-red-400 hover:text-white leading-none">×</button>
                      </span>
                    ))}
                  </div>
                )}
                <p className="text-[10px] text-gray-600">
                  Find channel ID at youtube.com/channel/YOUR_CHANNEL_ID or in YouTube Studio settings
                </p>
              </div>
            )}

            {/* Divider */}
            <div className="border-t border-gray-700 pt-3">
              {/* Reddit toggle */}
              <label className="flex items-center gap-3 p-3 rounded-lg border border-gray-700 hover:border-gray-600 cursor-pointer transition-colors">
                <div className={`relative w-10 h-5 rounded-full transition-colors shrink-0 ${
                  redditEnabled ? "bg-orange-600" : "bg-gray-700"
                }`}>
                  <div className={`absolute top-0.5 w-4 h-4 rounded-full bg-white shadow transition-transform ${
                    redditEnabled ? "translate-x-5" : "translate-x-0.5"
                  }`} />
                  <input
                    type="checkbox"
                    checked={redditEnabled}
                    onChange={e => setRedditEnabled(e.target.checked)}
                    className="sr-only"
                  />
                </div>
                <div>
                  <div className="flex items-center gap-1.5 text-sm text-gray-200">
                    <span className="text-[11px] px-1.5 py-0.5 bg-orange-600 text-white rounded font-bold">r/</span>
                    Monitor Reddit
                  </div>
                  <p className="text-xs text-gray-500 mt-0.5">
                    Collect posts and comments from subreddits mentioning this brand
                  </p>
                </div>
              </label>

              {/* Subreddits — only shown when Reddit is enabled */}
              {redditEnabled && (
                <div className="space-y-2 pl-1 mt-3">
                  <label className="block text-xs text-gray-400">
                    Subreddits to monitor{" "}
                    <span className="text-gray-600 font-normal">(one per line, without r/)</span>
                  </label>
                  <textarea
                    autoFocus
                    rows={4}
                    value={subredditsText}
                    onChange={e => setSubredditsText(e.target.value)}
                    placeholder={"india\nIndianStockMarket\nindiabusiness"}
                    className="w-full bg-gray-800 border border-gray-700 rounded-lg text-sm text-gray-100 px-3 py-2 focus:outline-none focus:border-orange-500 placeholder:text-gray-600 font-mono text-xs resize-none"
                  />
                  <p className="text-[10px] text-gray-600">
                    Add subreddits where your audience discusses brands in your category
                  </p>
                </div>
              )}
            </div>

            {error && <p className="text-xs text-red-400">{error}</p>}

            <div className="flex gap-2 pt-1">
              <button onClick={() => setStep(3)}
                className="flex-1 py-2 border border-gray-700 text-gray-400 text-sm rounded-lg hover:border-gray-500 transition-colors">
                ← Back
              </button>
              <button
                onClick={() => mutation.mutate()}
                disabled={mutation.isPending}
                className="flex-1 py-2 bg-indigo-600 hover:bg-indigo-500 text-white text-sm rounded-lg disabled:opacity-40 transition-colors"
              >
                {mutation.isPending ? "Creating…" : "Create Brand"}
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
