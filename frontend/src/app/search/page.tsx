"use client";

import { useEffect, useState } from "react";
import { useSearchParams } from "next/navigation";
import { Suspense } from "react";
import { api, ProductListItem, CategoryTreeNode } from "@/lib/api";
import { Header } from "@/components/Header";
import { ProductGrid } from "@/components/ProductCard";
import { CategorySidebar } from "@/components/CategorySidebar";
import { useLanguage } from "@/context/LanguageContext";

function SearchInner() {
  const searchParams = useSearchParams();
  const q = searchParams.get("q") || "";
  const { t } = useLanguage();
  const [products, setProducts] = useState<ProductListItem[]>([]);
  const [tree, setTree] = useState<CategoryTreeNode[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function load() {
      setLoading(true);
      try {
        const [t, p] = await Promise.all([api.getCategoryTree(false), q ? api.listProducts({ search: q, limit: 50 }) : api.listProducts({ limit: 24 })]);
        setTree(t);
        setProducts(p);
      } finally {
        setLoading(false);
      }
    }
    load();
  }, [q]);

  return (
    <div className="min-h-screen bg-slate-50">
      <Header categories={tree} />
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="flex gap-6 flex-col md:flex-row">
          <CategorySidebar tree={tree} />
          <main className="flex-1 min-w-0">
            <div className="flex items-start justify-between gap-4">
              <div>
                <h1 className="text-2xl font-bold tracking-tight text-slate-900">
                  {q ? `${t("search.titleSearch")} “${q}”` : t("search.titleAll")}
                </h1>
                <p className="text-sm text-slate-500 mt-1">{t("search.desc")}</p>
              </div>
              {!loading && (
                <span className="hidden sm:inline-flex px-3 py-1.5 bg-white border border-slate-200 rounded-full text-xs font-medium text-slate-700 shadow-sm shrink-0">
                  {products.length} {t("categories.slug.productsCount")}
                </span>
              )}
            </div>
            <div className="mt-6">
              {loading ? (
                <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4 animate-pulse">
                  {[1, 2, 3, 4].map((i) => (
                    <div key={i} className="h-64 bg-white border border-slate-200 rounded-2xl" />
                  ))}
                </div>
              ) : (
                <ProductGrid products={products} />
              )}
              {!loading && q && products.length === 0 && (
                <p className="text-sm text-slate-500 bg-white p-8 rounded-2xl border border-slate-200 shadow-sm text-center mt-4">
                  {t("search.noResultsFor")} “{q}”.
                </p>
              )}
            </div>
          </main>
        </div>
      </div>
    </div>
  );
}

export default function SearchPage() {
  return (
    <Suspense fallback={<div className="min-h-screen bg-slate-50 flex items-center justify-center text-sm text-slate-500">Loading…</div>}>
      <SearchInner />
    </Suspense>
  );
}
