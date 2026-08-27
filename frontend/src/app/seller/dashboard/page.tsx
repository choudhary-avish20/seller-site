"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { useAuth } from "@/context/AuthContext";
import { api, SellerProfile } from "@/lib/api";
import { useState } from "react";
import { useLanguage } from "@/context/LanguageContext";
import { LanguageToggle } from "@/components/LanguageToggle";

export default function SellerDashboardPage() {
  const router = useRouter();
  const { user, isAuthenticated, isSeller, loading, logout } = useAuth();
  const { t } = useLanguage();
  const [sellerProfile, setSellerProfile] = useState<SellerProfile | null>(null);
  const [profileLoading, setProfileLoading] = useState(true);

  useEffect(() => {
    if (!loading && (!isAuthenticated || !isSeller)) {
      router.push("/auth/login");
    }
  }, [isAuthenticated, isSeller, loading]);

  useEffect(() => {
    if (isAuthenticated && isSeller) {
      fetchProfile();
    }
  }, [isAuthenticated, isSeller]);

  const fetchProfile = async () => {
    try {
      const profile = await api.getMySellerProfile();
      setSellerProfile(profile);
    } catch {
      // Handle error
    } finally {
      setProfileLoading(false);
    }
  };

  if (loading || profileLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-slate-50">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-slate-900"></div>
      </div>
    );
  }

  if (!isAuthenticated || !isSeller) {
    return null;
  }

  if (!sellerProfile || sellerProfile.status !== "approved") {
    router.push("/seller/pending");
    return null;
  }

  return (
    <div className="min-h-screen bg-slate-50">
      <nav className="bg-white border-b border-slate-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between h-16 items-center">
            <div className="flex items-center">
              <h1 className="text-xl font-bold tracking-tight text-slate-900">{t("seller.dashboard.panel")}</h1>
            </div>
            <div className="flex items-center gap-3 sm:gap-4">
              <span className="text-sm font-medium text-slate-700 hidden sm:inline">{user?.full_name}</span>
              <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-emerald-50 text-emerald-700 border border-emerald-200">
                {t("seller.dashboard.approved")}
              </span>
              <LanguageToggle compact />
              <button
                onClick={logout}
                className="text-sm text-slate-500 hover:text-slate-700"
              >
                {t("seller.dashboard.signOut")}
              </button>
            </div>
          </div>
        </div>
      </nav>

      <main className="max-w-7xl mx-auto py-8 sm:py-12 px-4 sm:px-6 lg:px-8">
        <div className="mb-8">
          <h2 className="text-3xl font-bold tracking-tight text-slate-900">{t("seller.dashboard.title")}</h2>
          <p className="mt-2 text-slate-600 text-sm sm:text-base">{t("seller.dashboard.welcome")}, {user?.full_name} — <span className="font-medium text-slate-900">{sellerProfile.business_name}</span></p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          <Link
            href="/seller/categories"
            className="bg-white rounded-2xl border border-slate-200 shadow-sm p-6 hover:shadow-md transition-shadow"
          >
            <div className="w-10 h-10 rounded-xl bg-slate-900 text-white grid place-items-center mb-4">
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 7v10a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2h-6l-2-2H5a2 2 0 00-2 2z" />
              </svg>
            </div>
            <h3 className="text-base font-semibold text-slate-900 mb-1">{t("seller.dashboard.categories")}</h3>
            <p className="text-sm text-slate-600">{t("seller.dashboard.categoriesDesc")}</p>
          </Link>
          <Link
            href="/seller/products"
            className="bg-white rounded-2xl border border-slate-200 shadow-sm p-6 hover:shadow-md transition-shadow"
          >
            <div className="w-10 h-10 rounded-xl bg-slate-900 text-white grid place-items-center mb-4">
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M20 7l-8-4-8 4m16 0l-8 4m8-4v10l-8 4m0-10L4 7m8 4v10M4 7v10l8 4" />
              </svg>
            </div>
            <h3 className="text-base font-semibold text-slate-900 mb-1">{t("seller.dashboard.manageProducts")}</h3>
            <p className="text-sm text-slate-600">{t("seller.dashboard.manageProductsDesc")}</p>
          </Link>

          <Link
            href="/seller/orders"
            className="bg-white rounded-2xl border border-slate-200 shadow-sm p-6 hover:shadow-md transition-shadow"
          >
            <div className="w-10 h-10 rounded-xl bg-white border border-slate-200 text-slate-700 grid place-items-center mb-4">
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-6 9l2 2 4-4" />
              </svg>
            </div>
            <h3 className="text-base font-semibold text-slate-900 mb-1">{t("seller.dashboard.orders")}</h3>
            <p className="text-sm text-slate-600">{t("seller.dashboard.ordersDesc")}</p>
          </Link>

          <Link
            href="/seller/profile"
            className="bg-white rounded-2xl border border-slate-200 shadow-sm p-6 hover:shadow-md transition-shadow"
          >
            <div className="w-10 h-10 rounded-xl bg-white border border-slate-200 text-slate-700 grid place-items-center mb-4">
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 19l-7-7m0 0l7-7m-7 7h18" />
              </svg>
            </div>
            <h3 className="text-base font-semibold text-slate-900 mb-1">{t("seller.dashboard.businessProfile")}</h3>
            <p className="text-sm text-slate-600">{t("seller.dashboard.businessProfileDesc")}</p>
          </Link>
        </div>

        <div className="mt-10">
          <h3 className="text-base font-semibold tracking-tight text-slate-900 mb-4">{t("seller.dashboard.quickStats")}</h3>
          <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
            <div className="bg-white rounded-2xl border border-slate-200 shadow-sm p-6">
              <dt className="text-sm font-medium text-slate-500">{t("seller.dashboard.totalProducts")}</dt>
              <dd className="mt-2 text-3xl font-bold tracking-tight text-slate-900">0</dd>
            </div>
            <div className="bg-white rounded-2xl border border-slate-200 shadow-sm p-6">
              <dt className="text-sm font-medium text-slate-500">{t("seller.dashboard.pendingOrders")}</dt>
              <dd className="mt-2 text-3xl font-bold tracking-tight text-slate-900">0</dd>
            </div>
            <div className="bg-white rounded-2xl border border-slate-200 shadow-sm p-6">
              <dt className="text-sm font-medium text-slate-500">{t("seller.dashboard.completedOrders")}</dt>
              <dd className="mt-2 text-3xl font-bold tracking-tight text-slate-900">0</dd>
            </div>
            <div className="bg-white rounded-2xl border border-slate-200 shadow-sm p-6">
              <dt className="text-sm font-medium text-slate-500">{t("seller.dashboard.revenue")}</dt>
              <dd className="mt-2 text-3xl font-bold tracking-tight text-slate-900">$0.00</dd>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}
