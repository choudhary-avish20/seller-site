"use client";

import Link from "next/link";
import { useState } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/context/AuthContext";
import { useCart } from "@/context/CartContext";
import { useLanguage } from "@/context/LanguageContext";
import { LanguageToggle } from "@/components/LanguageToggle";
import { CategoryTreeNode } from "@/lib/api";

export function Header({ categories }: { categories?: CategoryTreeNode[] }) {
  const router = useRouter();
  const { isAuthenticated, isBuyer, isSeller, isAdmin, user, logout } = useAuth();
  const { count, totalNet } = useCart();
  const { t } = useLanguage();
  const [q, setQ] = useState("");

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    const term = q.trim();
    if (term) router.push(`/search?q=${encodeURIComponent(term)}`);
    else router.push(`/search`);
  };

  return (
    <header className="sticky top-0 z-30">
      {/* Utility bar */}
      <div className="bg-slate-900 text-slate-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 flex items-center justify-between h-8 text-[11px] tracking-wide">
          <div className="flex items-center gap-4">
            <span className="hidden sm:inline-flex items-center gap-1.5">
              <span className="w-1.5 h-1.5 bg-emerald-400 rounded-full animate-pulse" />
              {t("header.b2bOnly")}
            </span>
            <a href="tel:+48579383945" className="hover:text-white hidden sm:inline">+48 579 383 945</a>
            <span className="sm:hidden">{t("header.b2bShort")}</span>
          </div>
          <div className="flex items-center gap-3">
            <Link href="/categories" className="hover:text-white hidden md:inline">{t("header.categories")}</Link>
            <Link href="#" className="hover:text-white hidden md:inline">{t("header.shippingCosts")}</Link>
            <Link href="#" className="hover:text-white hidden md:inline">{t("header.terms")}</Link>
            <LanguageToggle compact />
            {isAuthenticated ? (
              <span className="text-slate-400 hidden md:inline truncate max-w-[160px]">{user?.email}</span>
            ) : (
              <Link href="/auth/login" className="hover:text-white font-medium">{t("header.login")}</Link>
            )}
          </div>
        </div>
      </div>

      {/* Main header */}
      <div className="bg-white/95 backdrop-blur supports-[backdrop-filter]:bg-white/80 border-b border-slate-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center gap-4 lg:gap-8 h-[72px]">
            <Link href="/" className="flex items-center gap-3 shrink-0">
              <div className="w-10 h-10 rounded-xl bg-indigo-600 flex items-center justify-center text-white font-bold text-lg">W</div>
              <div className="hidden sm:block leading-none">
                <div className="font-bold tracking-tight text-slate-900">WHOLESALE</div>
                <div className="text-[10px] tracking-[0.14em] text-slate-500 font-medium">CENTRUM • WÓLKA • B2B</div>
              </div>
              <span className="sm:hidden font-bold text-slate-900">WHOLESALE</span>
            </Link>

            <form onSubmit={handleSearch} className="flex-1 max-w-2xl mx-2 sm:mx-6 relative hidden sm:block">
              <input
                value={q}
                onChange={(e) => setQ(e.target.value)}
                placeholder={t("header.searchPlaceholder")}
                className="w-full bg-slate-100 border border-slate-200 rounded-full pl-5 pr-28 py-3 text-sm placeholder:text-slate-400 focus:bg-white focus:border-indigo-300 focus:ring-4 focus:ring-indigo-100 outline-none transition"
              />
              <button type="submit" className="absolute right-1.5 top-1.5 bottom-1.5 px-6 bg-slate-900 text-white text-sm font-medium rounded-full hover:bg-slate-800 transition">
                {t("header.search")}
              </button>
            </form>

            <div className="flex items-center gap-2 sm:gap-3 ml-auto">
              <Link href="/cart" className="relative flex items-center gap-3 pl-3 pr-2 py-2 bg-slate-900 text-white rounded-full hover:bg-slate-800 transition">
                <span className="hidden lg:inline-flex flex-col leading-none pr-2 border-r border-white/20">
                  <span className="text-[10px] text-white/70 uppercase tracking-wide">{t("header.cart")}</span>
                  <span className="text-sm font-semibold">{totalNet.toFixed(2)} zł <span className="font-normal text-white/70 text-xs">{t("header.net")}</span></span>
                </span>
                <span className="relative">
                  <svg className="w-5 h-5" fill="none" stroke="currentColor" strokeWidth={1.7} viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" d="M6 6h15l-1.5 8H6z M6 6L5 2H2" />
                    <circle cx="9" cy="20" r="1.5" />
                    <circle cx="18" cy="20" r="1.5" />
                  </svg>
                  {count > 0 && (
                    <span className="absolute -top-2 -right-2 min-w-[18px] h-[18px] px-1 bg-white text-slate-900 text-[10px] font-bold rounded-full flex items-center justify-center border border-slate-900">
                      {count}
                    </span>
                  )}
                </span>
                <span className="lg:hidden text-sm font-medium">{t("header.cart")}</span>
              </Link>

              <div className="flex items-center gap-2">
                {!isAuthenticated ? (
                  <>
                    <Link
                      href="/auth/login"
                      className="inline-flex items-center gap-1.5 px-4 py-2 bg-slate-900 text-white rounded-full text-sm font-medium hover:bg-slate-800 transition"
                    >
                      <svg className="w-4 h-4" fill="none" stroke="currentColor" strokeWidth={1.7} viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" d="M11 16l4-4-4-4 M15 12H3 M21 12a9 9 0 11-18 0 9 9 0 0118 0" />
                      </svg>
                      {t("header.loginBtn")}
                    </Link>
                    <Link
                      href="/auth/signup"
                      className="hidden sm:inline-flex px-4 py-2 bg-white border border-slate-200 rounded-full text-sm font-medium hover:bg-slate-50"
                    >
                      {t("header.signup")}
                    </Link>
                  </>
                ) : (
                  <div className="flex items-center gap-2">
                    {isBuyer && (
                      <Link href="/buyer/dashboard" className="hidden lg:block px-3 py-2 text-sm text-slate-600 hover:text-slate-900">
                        Buyer
                      </Link>
                    )}
                    {isSeller && (
                      <Link href="/seller/dashboard" className="hidden lg:block px-3 py-2 text-sm text-slate-600 hover:text-slate-900">
                        Seller
                      </Link>
                    )}
                    {isAdmin && <Link href="/admin/dashboard" className="hidden sm:block px-3 py-2 text-sm text-slate-700 hover:text-slate-900">Admin</Link>}
                    <span className="hidden md:inline text-xs text-slate-500 truncate max-w-[140px]">{user?.email}</span>
                    <button
                      onClick={logout}
                      className="inline-flex items-center gap-1.5 px-4 py-2 bg-white border border-slate-200 text-slate-700 rounded-full text-sm font-medium hover:bg-slate-50 hover:text-red-600 hover:border-red-200 transition"
                      title={t("header.logout")}
                    >
                      <svg className="w-4 h-4" fill="none" stroke="currentColor" strokeWidth={1.7} viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" d="M17 16l4-4-4-4 M21 12H9 M13 12a9 9 0 11-18 0 9 9 0 0118 0" />
                      </svg>
                      <span className="hidden sm:inline">{t("header.logout")}</span>
                      <span className="sm:hidden">Out</span>
                    </button>
                  </div>
                )}
              </div>
            </div>
          </div>

          <form onSubmit={handleSearch} className="sm:hidden pb-3 flex gap-2">
            <input value={q} onChange={(e) => setQ(e.target.value)} placeholder={`${t("header.search")}…`} className="flex-1 bg-slate-100 border border-slate-200 rounded-full px-4 py-2.5 text-sm" />
            <button type="submit" className="px-5 bg-slate-900 text-white rounded-full text-sm">{t("header.search")}</button>
          </form>

          <nav className="flex items-center gap-1 sm:gap-2 py-2 border-t border-slate-100 overflow-x-auto scrollbar-none text-[13px]">
            <Link href="/search?filter=new" className="px-3 py-1.5 rounded-full hover:bg-slate-100 text-slate-700 whitespace-nowrap">
              {t("header.new")}
            </Link>
            <Link href="/search?filter=sale" className="px-3 py-1.5 rounded-full hover:bg-slate-100 text-slate-700 whitespace-nowrap">
              {t("header.sale")}
            </Link>
            <Link href="/search?filter=bestsellers" className="px-3 py-1.5 rounded-full hover:bg-slate-100 text-slate-700 whitespace-nowrap">
              {t("header.bestsellers")}
            </Link>
            <span className="w-px h-4 bg-slate-200 mx-1 hidden sm:block" />
            <Link href="/categories" className="px-3 py-1.5 rounded-full bg-indigo-50 text-indigo-700 font-medium whitespace-nowrap">
              {t("header.allCategories")}
            </Link>
            <Link href="/search" className="px-3 py-1.5 rounded-full hover:bg-slate-100 text-slate-700 whitespace-nowrap">
              {t("header.products")}
            </Link>
            <span className="hidden lg:flex items-center gap-2 ml-auto text-xs text-slate-500">
              <span className="w-2 h-2 bg-emerald-500 rounded-full" /> {t("header.deliveryNote")} <span className="font-medium text-slate-700">{t("header.net")}</span>
            </span>
          </nav>

          {categories && categories.length > 0 && (
            <div className="flex gap-1.5 pb-3 overflow-x-auto scrollbar-none">
              {categories.slice(0, 8).map((c) => (
                <Link key={c.id} href={`/categories/${c.slug}`} className="px-3.5 py-1.5 bg-white border border-slate-200 hover:border-slate-300 hover:bg-slate-50 rounded-full text-xs font-medium text-slate-700 whitespace-nowrap transition">
                  {c.name}
                </Link>
              ))}
              <Link href="/categories" className="px-3.5 py-1.5 text-xs font-medium text-indigo-600 hover:text-indigo-700 whitespace-nowrap">
                {t("header.all")}
              </Link>
            </div>
          )}
        </div>
      </div>
    </header>
  );
}
