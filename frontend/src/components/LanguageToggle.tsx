"use client";

import { useLanguage } from "@/context/LanguageContext";

export function LanguageToggle({ compact = false }: { compact?: boolean }) {
  const { lang, setLang } = useLanguage();
  return (
    <div className={`inline-flex items-center rounded-full border border-slate-200 bg-white overflow-hidden ${compact ? "text-xs" : "text-xs"}`}>
      <button
        onClick={() => setLang("pl")}
        className={`px-2.5 py-1 font-medium transition ${lang === "pl" ? "bg-slate-900 text-white" : "text-slate-600 hover:bg-slate-50"}`}
        aria-label="Polish"
      >
        PL
      </button>
      <span className="w-px h-4 bg-slate-200" />
      <button
        onClick={() => setLang("en")}
        className={`px-2.5 py-1 font-medium transition ${lang === "en" ? "bg-slate-900 text-white" : "text-slate-600 hover:bg-slate-50"}`}
        aria-label="English"
      >
        EN
      </button>
    </div>
  );
}
