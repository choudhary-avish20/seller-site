"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { api, CategoryTreeNode, ProductListItem } from "@/lib/api";
import { Header } from "@/components/Header";
import { ProductGrid } from "@/components/ProductCard";
import { useLanguage } from "@/context/LanguageContext";

export default function Home() {
  const { t, lang } = useLanguage();
  const [tree, setTree] = useState<CategoryTreeNode[]>([]);
  const [newArrivals, setNewArrivals] = useState<ProductListItem[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function load() {
      try {
        const [t, prods] = await Promise.all([
          api.getCategoryTree(false).catch(() => []),
          api.listProducts({ limit: 8 }).catch(() => []),
        ]);
        setTree(t);
        setNewArrivals(prods);
      } finally {
        setLoading(false);
      }
    }
    load();
  }, []);

  return (
    <div className="min-h-screen bg-slate-50">
      <Header categories={tree} />

      {/* Business-only banner */}
      <div className="bg-amber-50 border-y border-amber-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-3 flex items-center gap-3 text-sm">
          <span className="w-7 h-7 rounded-full bg-amber-500 text-white grid place-items-center text-xs font-bold">!</span>
          <p className="text-slate-800">
            <span className="font-semibold">{t("home.bannerBusiness")}</span>
            <span className="hidden sm:inline text-slate-600"> {t("home.bannerSuffix")}</span>
          </p>
          <Link href="/auth/register-seller" className="ml-auto hidden sm:inline-flex px-3 py-1.5 bg-slate-900 text-white rounded-full text-xs font-medium hover:bg-slate-800">
            {t("home.becomeSeller")}
          </Link>
        </div>
      </div>

      {/* Hero */}
      <section className="relative overflow-hidden bg-white border-b border-slate-200">
        <div className="absolute inset-0 bg-gradient-to-br from-indigo-50 via-white to-slate-50" />
        <div className="absolute -right-20 -top-20 w-[520px] h-[520px] bg-indigo-100 rounded-full blur-3xl opacity-30" />
        <div className="relative max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-10 sm:py-14 grid lg:grid-cols-2 gap-8 items-center">
          <div>
            <p className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-indigo-600 text-white text-xs font-semibold tracking-wide">
              {t("home.badge")}
            </p>
            <h1 className="mt-4 text-3xl sm:text-4xl lg:text-5xl font-bold tracking-tight text-slate-900 leading-tight">
              {t("home.heroTitle1")}
              <br />
              <span className="text-indigo-600">{t("home.heroTitle2")}</span>
            </h1>
            <p className="mt-4 text-slate-600 max-w-xl">
              {t("home.heroDesc")}
            </p>
            <div className="mt-6 flex flex-wrap gap-3">
              <Link href="/categories" className="px-6 py-3 bg-slate-900 text-white text-sm font-medium rounded-full hover:bg-slate-800 shadow">
                {t("home.browseCategories")}
              </Link>
              <Link href="/search" className="px-6 py-3 bg-white border border-slate-200 text-sm font-medium rounded-full hover:bg-slate-50">
                {t("home.newBestsellers")}
              </Link>
            </div>
            <div className="mt-6 flex items-center gap-6 text-xs text-slate-500">
              <span className="flex items-center gap-1.5"><span className="w-2 h-2 bg-emerald-500 rounded-full" /> {t("home.delivery")}</span>
              <span className="flex items-center gap-1.5"><span className="w-2 h-2 bg-slate-300 rounded-full" /> {t("home.pricesNet")} <b className="text-slate-700">{t("header.net")}</b></span>
            </div>
          </div>

          <div className="grid grid-cols-2 gap-3 sm:gap-4">
            <div className="space-y-3 sm:space-y-4">
              <div className="rounded-2xl bg-slate-900 text-white p-5 h-40 flex flex-col justify-between overflow-hidden relative">
                <div className="absolute -right-6 -bottom-6 w-32 h-32 bg-white/10 rounded-full blur-xl" />
                <p className="text-xs tracking-[0.14em] text-white/70">ODZIEŻ DAMSKA</p>
                <p className="text-lg font-semibold leading-tight">{lang === "pl" ? "Bluzki, sukienki, jeansy — hurt" : "Blouses, dresses, jeans — wholesale"}</p>
                <Link href="/categories" className="text-xs underline decoration-white/30 underline-offset-4">{lang === "pl" ? "Zobacz →" : "View →"}</Link>
              </div>
              <div className="rounded-2xl bg-indigo-600 text-white p-5 h-36 flex flex-col justify-between">
                <p className="text-xs tracking-[0.14em] text-white/80">BIELIZNA • 750+ SKU</p>
                <p className="text-base font-semibold">{lang === "pl" ? "Bestsellery Wólka Kosowska" : "Wólka Bestsellers"}</p>
              </div>
            </div>
            <div className="rounded-2xl bg-white border border-slate-200 p-5 h-[304px] flex flex-col">
              <p className="text-xs font-semibold tracking-wide text-slate-500">{lang === "pl" ? "KATEGORIE HURTOWNI" : "WHOLESALE CATEGORIES"}</p>
              <div className="mt-3 space-y-2 flex-1 overflow-hidden">
                {loading ? (
                  <div className="space-y-2 animate-pulse">
                    {[1, 2, 3, 4].map((i) => <div key={i} className="h-8 bg-slate-100 rounded" />)}
                  </div>
                ) : tree.length ? (
                  tree.slice(0, 5).map((c) => (
                    <Link key={c.id} href={`/categories/${c.slug}`} className="flex items-center justify-between px-3 py-2 rounded-xl hover:bg-slate-50 border border-transparent hover:border-slate-200">
                      <span className="text-sm font-medium text-slate-800">{c.name}</span>
                      <span className="text-xs text-slate-400">{c.children.length} ›</span>
                    </Link>
                  ))
                ) : (
                  <p className="text-sm text-slate-500">{t("home.noCategories")}</p>
                )}
              </div>
              <Link href="/categories" className="mt-3 text-xs font-medium text-indigo-600 hover:text-indigo-500">{t("home.viewAll")}</Link>
            </div>
          </div>
        </div>
      </section>

      {/* Trust bar */}
      <section className="bg-white border-b border-slate-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4 grid grid-cols-1 sm:grid-cols-3 gap-3 text-sm">
          <div className="flex items-center gap-3 px-4 py-3 bg-slate-50 rounded-2xl border border-slate-100">
            <span className="w-8 h-8 rounded-full bg-white border grid place-items-center">🚚</span>
            <div>
              <p className="font-medium text-slate-900">{t("home.trustShippingTitle")}</p>
              <p className="text-xs text-slate-500">{t("home.trustShippingDesc")}</p>
            </div>
          </div>
          <div className="flex items-center gap-3 px-4 py-3 bg-slate-50 rounded-2xl border border-slate-100">
            <span className="w-8 h-8 rounded-full bg-white border grid place-items-center">↩</span>
            <div>
              <p className="font-medium text-slate-900">{t("home.trustB2BTitle")}</p>
              <p className="text-xs text-slate-500">{t("home.trustB2BDesc")}</p>
            </div>
          </div>
          <div className="flex items-center gap-3 px-4 py-3 bg-slate-50 rounded-2xl border border-slate-100">
            <span className="w-8 h-8 rounded-full bg-white border grid place-items-center">✓</span>
            <div>
              <p className="font-medium text-slate-900">{t("home.trustNetTitle")}</p>
              <p className="text-xs text-slate-500">{t("home.trustNetDesc")}</p>
            </div>
          </div>
        </div>
      </section>

      {/* Featured categories */}
      <section className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-10">
        <div className="flex items-end justify-between mb-6">
          <div>
            <h2 className="text-xl font-bold tracking-tight text-slate-900">{t("home.featuredTitle")}</h2>
            <p className="text-sm text-slate-500">{t("home.featuredDesc")}</p>
          </div>
          <Link href="/categories" className="hidden sm:inline-flex px-4 py-2 bg-white border border-slate-200 rounded-full text-sm hover:bg-slate-50">
            {t("home.viewAll")}
          </Link>
        </div>
        {loading ? (
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 animate-pulse">
            {[1, 2, 3, 4].map((i) => <div key={i} className="h-28 bg-white border border-slate-200 rounded-2xl" />)}
          </div>
        ) : tree.length === 0 ? (
          <p className="text-sm text-slate-500 bg-white p-8 rounded-2xl border text-center">{t("home.noCategories")}</p>
        ) : (
          <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-4">
            {tree.slice(0, 8).map((cat) => (
              <Link key={cat.id} href={`/categories/${cat.slug}`} className="group bg-white rounded-2xl border border-slate-200 p-5 hover:border-slate-300 hover:shadow-lg hover:shadow-slate-200/50 transition">
                <div className="w-10 h-10 rounded-xl bg-slate-900 text-white grid place-items-center text-sm font-bold group-hover:bg-indigo-600 transition">
                  {cat.name.slice(0, 1).toUpperCase()}
                </div>
                <h3 className="mt-3 font-semibold text-slate-900 group-hover:text-indigo-700">{cat.name}</h3>
                <p className="text-xs text-slate-500">/{cat.slug}</p>
                <div className="mt-3 flex flex-wrap gap-1">
                  {cat.children.slice(0, 3).map((sub) => (
                    <span key={sub.id} className="text-[11px] px-2 py-1 bg-slate-50 border border-slate-200 rounded-full text-slate-600">
                      {sub.name}
                    </span>
                  ))}
                  {cat.children.length > 3 && <span className="text-[11px] px-2 py-1 text-slate-500">+{cat.children.length - 3}</span>}
                </div>
                <p className="text-xs font-medium text-indigo-600 mt-3 flex items-center gap-1">
                  {cat.children.length ? `${cat.children.length} ${t("home.subcategories")}` : t("home.browseProducts")} <span>→</span>
                </p>
              </Link>
            ))}
          </div>
        )}
      </section>

      {/* New arrivals */}
      <section className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 pb-12">
        <div className="flex items-end justify-between mb-6">
          <div>
            <h2 className="text-xl font-bold tracking-tight text-slate-900">{t("home.arrivalsTitle")}</h2>
            <p className="text-sm text-slate-500">{t("home.arrivalsDesc")}</p>
          </div>
          <Link href="/search" className="hidden sm:inline-flex text-sm font-medium text-indigo-600 hover:text-indigo-500">
            {t("home.viewAll")}
          </Link>
        </div>
        {loading ? (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 animate-pulse">
            {[1, 2, 3, 4].map((i) => <div key={i} className="h-64 bg-white border border-slate-200 rounded-2xl" />)}
          </div>
        ) : (
          <ProductGrid products={newArrivals} />
        )}
      </section>

      <footer className="border-t border-slate-200 bg-white">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          <div className="grid sm:grid-cols-3 gap-6 text-sm">
            <div>
              <p className="font-semibold text-slate-900">{t("footer.title")}</p>
              <p className="text-slate-500 mt-1">{t("footer.desc")}</p>
            </div>
            <div className="text-slate-600">
              <p className="font-medium text-slate-900">{t("footer.contact")}</p>
              <p className="mt-1">+48 579 383 945 • kontakt@wholesale.local</p>
              <p className="text-xs text-slate-500">Pn-Pt 8:00 - 17:00</p>
            </div>
            <div className="text-slate-600">
              <p className="font-medium text-slate-900">{t("footer.info")}</p>
              <div className="mt-1 flex flex-wrap gap-3 text-xs">
                <Link href="#" className="hover:text-slate-900">{t("footer.faq")}</Link>
                <Link href="#" className="hover:text-slate-900">{t("header.shippingCosts")}</Link>
                <Link href="#" className="hover:text-slate-900">{t("header.terms")}</Link>
              </div>
            </div>
          </div>
          <p className="mt-6 text-center text-xs text-slate-400">{t("header.netLong")} • Brutto = netto + VAT • {new Date().getFullYear()} Wholesale</p>
        </div>
      </footer>
    </div>
  );
}
