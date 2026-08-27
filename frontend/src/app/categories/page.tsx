"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { api, CategoryTreeNode, ProductListItem } from "@/lib/api";
import { Header } from "@/components/Header";
import { CategorySidebar } from "@/components/CategorySidebar";
import { ProductGrid } from "@/components/ProductCard";
import { useLanguage } from "@/context/LanguageContext";

export default function CategoriesPage() {
  const { t } = useLanguage();
  const [tree, setTree] = useState<CategoryTreeNode[]>([]);
  const [products, setProducts] = useState<ProductListItem[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([api.getCategoryTree(false), api.listProducts({ limit: 12 })])
      .then(([t, p]) => {
        setTree(t);
        setProducts(p);
      })
      .finally(() => setLoading(false));
  }, []);

  return (
    <div className="min-h-screen bg-slate-50">
      <Header categories={tree} />
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="flex gap-6 flex-col md:flex-row">
          <CategorySidebar tree={tree} />
          <main className="flex-1 min-w-0">
            <div className="flex items-end justify-between gap-4">
              <div>
                <h1 className="text-2xl font-bold tracking-tight text-slate-900">{t("categories.allTitle")}</h1>
                <p className="text-sm text-slate-500 mt-1">{t("categories.allDesc")}</p>
              </div>
              <span className="hidden sm:inline-flex items-center px-3 py-1 bg-white border border-slate-200 rounded-full text-xs font-medium text-slate-600 shadow-sm">
                {tree.length} {t("header.categories")}
              </span>
            </div>

            <div className="mt-6 grid grid-cols-2 sm:grid-cols-3 gap-4">
              {tree.map((c) => (
                <Link
                  key={c.id}
                  href={`/categories/${c.slug}`}
                  className="group bg-white p-5 rounded-2xl border border-slate-200 shadow-sm hover:border-slate-300 hover:shadow-md transition"
                >
                  <div className="flex items-start justify-between gap-2">
                    <h3 className="font-semibold text-slate-900 group-hover:text-indigo-700 transition">{c.name}</h3>
                    <span className="w-7 h-7 rounded-full bg-slate-900 text-white grid place-items-center text-xs shrink-0 group-hover:bg-indigo-600 transition">
                      →
                    </span>
                  </div>
                  <p className="text-xs text-slate-500 mt-1">/{c.slug} • {c.children.length} {t("categories.subcategoriesLabel")}</p>
                  <div className="mt-3 flex flex-wrap gap-1.5">
                    {c.children.slice(0, 3).map((sub) => (
                      <span key={sub.id} className="text-[11px] px-2.5 py-1 bg-slate-50 border border-slate-200 rounded-full text-slate-600">
                        {sub.name}
                      </span>
                    ))}
                    {c.children.length > 3 && (
                      <span className="text-[11px] px-2 py-1 text-slate-400">+{c.children.length - 3}</span>
                    )}
                    {c.children.length === 0 && (
                      <span className="text-[11px] text-slate-400">{t("home.browseProducts")} →</span>
                    )}
                  </div>
                </Link>
              ))}
              {tree.length === 0 && !loading && (
                <div className="col-span-full bg-white rounded-2xl border border-slate-200 shadow-sm p-8 text-center text-sm text-slate-500">
                  {t("home.noCategories")}
                </div>
              )}
            </div>

            <div className="mt-10">
              <div className="flex items-end justify-between mb-4">
                <h2 className="text-lg font-semibold tracking-tight text-slate-900">{t("categories.allProductsTitle")}</h2>
                <Link href="/search" className="text-sm font-medium text-indigo-600 hover:text-indigo-500">
                  {t("home.viewAll")}
                </Link>
              </div>
              {loading ? (
                <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4 animate-pulse">
                  {[1, 2, 3].map((i) => (
                    <div key={i} className="h-64 bg-white border border-slate-200 rounded-2xl" />
                  ))}
                </div>
              ) : (
                <ProductGrid products={products} />
              )}
            </div>
          </main>
        </div>
      </div>
    </div>
  );
}
