"use client";

import Link from "next/link";
import { useState } from "react";
import { CategoryTreeNode } from "@/lib/api";
import { useLanguage } from "@/context/LanguageContext";

export function CategorySidebar({ tree, activeSlug }: { tree: CategoryTreeNode[]; activeSlug?: string }) {
  const { t } = useLanguage();
  return (
    <aside className="w-full md:w-[260px] flex-shrink-0">
      <div className="bg-white rounded-2xl border border-slate-200 shadow-sm overflow-hidden sticky top-[132px]">
        <div className="px-5 py-4 border-b border-slate-100 flex items-center justify-between">
          <h3 className="text-sm font-semibold tracking-wide text-slate-900 uppercase">{t("categorySidebar.title")}</h3>
          <span className="text-[11px] px-2 py-1 bg-slate-100 rounded-full text-slate-600">{tree.length} top</span>
        </div>
        <div className="p-2">
          <Link
            href="/categories"
            className={`flex items-center justify-between px-3 py-2 rounded-xl text-sm ${!activeSlug ? "bg-slate-900 text-white" : "text-slate-700 hover:bg-slate-50"}`}
          >
            <span>{t("categorySidebar.all")}</span>
            <span className="text-xs opacity-60">→</span>
          </Link>
          <div className="mt-2 space-y-1">
            {tree.map((node) => (
              <CategoryItem key={node.id} node={node} activeSlug={activeSlug} depth={0} />
            ))}
          </div>
        </div>
        <div className="px-5 py-3 bg-slate-50 border-t border-slate-100">
          <p className="text-[11px] leading-relaxed text-slate-500">
            {t("header.b2bOnly")} — {t("home.trustB2BDesc")}
          </p>
        </div>
      </div>
    </aside>
  );
}

function CategoryItem({ node, activeSlug, depth }: { node: CategoryTreeNode; activeSlug?: string; depth: number }) {
  const isActive = node.slug === activeSlug;
  const hasChildren = node.children.length > 0;
  const [open, setOpen] = useState(isActive || depth === 0);

  const isAncestor = (() => {
    const walk = (n: CategoryTreeNode): boolean => n.slug === activeSlug || n.children.some(walk);
    return hasChildren && walk(node) && !isActive;
  })();

  return (
    <div>
      <div className={`group flex items-center gap-1 rounded-xl overflow-hidden ${isActive ? "bg-indigo-600 text-white" : isAncestor ? "bg-indigo-50 text-indigo-700" : "hover:bg-slate-50"}`}>
        <Link href={`/categories/${node.slug}`} className={`flex-1 flex items-center gap-2 px-3 py-2 text-sm truncate ${isActive ? "text-white" : "text-slate-700"}`} style={{ paddingLeft: `${12 + depth * 12}px` }}>
          <span className={`w-1.5 h-1.5 rounded-full shrink-0 ${isActive ? "bg-white" : isAncestor ? "bg-indigo-600" : "bg-slate-300 group-hover:bg-slate-400"}`} />
          <span className={`truncate ${isActive ? "font-medium" : ""}`}>{node.name}</span>
          <span className={`ml-auto text-[11px] ${isActive ? "text-white/70" : "text-slate-400"}`}>/{node.slug}</span>
        </Link>
        {hasChildren && (
          <button
            onClick={() => setOpen(!open)}
            aria-label={open ? "Collapse" : "Expand"}
            className={`mr-1 w-7 h-7 grid place-items-center rounded-lg shrink-0 ${isActive ? "hover:bg-white/20 text-white" : "hover:bg-slate-100 text-slate-500"}`}
          >
            <svg className={`w-3.5 h-3.5 transition ${open ? "rotate-180" : ""}`} fill="none" stroke="currentColor" strokeWidth={2} viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" d="M6 9l6 6 6-6" />
            </svg>
          </button>
        )}
      </div>
      {hasChildren && open && (
        <div className="mt-1 ml-2 pl-2 border-l border-slate-100 space-y-1">
          {node.children.map((c) => (
            <CategoryItem key={c.id} node={c} activeSlug={activeSlug} depth={depth + 1} />
          ))}
        </div>
      )}
    </div>
  );
}
