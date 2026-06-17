import { useState } from "react";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { createBrand } from "../lib/api";

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
  const [step, setStep]           = useState<1 | 2 | 3>(1);
  const [name, setName]           = useState("");
  const [kwInput, setKwInput]     = useState("");
  const [keywords, setKeywords]   = useState<string[]>([]);
  const [languages, setLanguages] = useState<string[]>(["en"]);
  const [error, setError]         = useState("");

  const queryClient = useQueryClient();

  const mutation = useMutation({
    mutationFn: () => createBrand({ name: name.trim(), keywords, languages }),
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

  return (
    <div className="fixed inset-0 bg-black/70 flex items-center justify-center z-50 p-4">
      <div className="bg-gray-900 border border-gray-700 rounded-2xl w-full max-w-md p-6 space-y-5">
        {/* Header */}
        <div className="flex items-center justify-between">
          <h2 className="text-lg font-semibold text-gray-100">Add New Brand</h2>
          <button onClick={onClose} className="text-gray-500 hover:text-gray-300 text-xl leading-none">×</button>
        </div>

        {/* Step indicator */}
        <div className="flex gap-2">
          {([1, 2, 3] as const).map(s => (
            <div key={s} className={`h-1 flex-1 rounded-full transition-colors ${
              s <= step ? "bg-indigo-500" : "bg-gray-700"
            }`} />
          ))}
        </div>
        <p className="text-xs text-gray-500">Step {step} of 3 — {
          step === 1 ? "Brand name" : step === 2 ? "Keywords" : "Languages"
        }</p>

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

            {error && <p className="text-xs text-red-400">{error}</p>}

            <div className="flex gap-2 pt-1">
              <button onClick={() => setStep(2)}
                className="flex-1 py-2 border border-gray-700 text-gray-400 text-sm rounded-lg hover:border-gray-500 transition-colors">
                ← Back
              </button>
              <button
                onClick={() => mutation.mutate()}
                disabled={languages.length === 0 || mutation.isPending}
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
