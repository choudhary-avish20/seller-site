"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { useAuth } from "@/context/AuthContext";

export default function BuyerDashboardPage() {
  const router = useRouter();
  const { user, isAuthenticated, isBuyer, loading, logout } = useAuth();

  useEffect(() => {
    if (!loading && (!isAuthenticated || !isBuyer)) {
      router.push("/auth/login");
    }
  }, [isAuthenticated, isBuyer, loading]);

  if (loading || !isAuthenticated || !isBuyer) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-slate-50">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-slate-900"></div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-slate-50">
      <nav className="bg-white border-b border-slate-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between h-16 items-center">
            <div className="flex items-center gap-3">
              <div className="w-9 h-9 rounded-xl bg-slate-900 text-white grid place-items-center font-bold text-sm">W</div>
              <h1 className="text-base sm:text-xl font-bold tracking-tight text-slate-900">Wholesale Marketplace</h1>
              <span className="hidden sm:inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-slate-50 text-slate-700 border border-slate-200">
                Buyer
              </span>
            </div>
            <div className="flex items-center gap-3 sm:gap-4">
              <span className="text-sm font-medium text-slate-700 hidden sm:inline">{user?.full_name}</span>
              <button onClick={logout} className="text-sm text-slate-500 hover:text-slate-700">
                Sign out
              </button>
            </div>
          </div>
        </div>
      </nav>

      <main className="max-w-7xl mx-auto py-8 sm:py-12 px-4 sm:px-6 lg:px-8">
        <div className="mb-8">
          <h2 className="text-3xl font-bold tracking-tight text-slate-900">Buyer Dashboard</h2>
          <p className="mt-2 text-slate-600 text-sm sm:text-base">Welcome back, <span className="font-medium text-slate-900">{user?.full_name}</span>!</p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          <Link href="/categories" className="bg-white rounded-2xl border border-slate-200 shadow-sm p-6 hover:shadow-md transition-shadow group">
            <div className="w-10 h-10 rounded-xl bg-slate-900 text-white grid place-items-center mb-4 group-hover:bg-indigo-600 transition">
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M20 7l-8-4-8 4m16 0l-8 4m8-4v10l-8 4m0-10L4 7m8 4v10M4 7v10l8 4" />
              </svg>
            </div>
            <h3 className="text-base font-semibold text-slate-900 mb-1">Browse Products</h3>
            <p className="text-sm text-slate-600">Explore our wholesale catalog and find products for your business.</p>
            <span className="mt-3 inline-flex text-xs font-medium text-indigo-600 group-hover:text-indigo-500">Browse catalog →</span>
          </Link>

          <Link href="/buyer/orders" className="bg-white rounded-2xl border border-slate-200 shadow-sm p-6 hover:shadow-md transition-shadow group">
            <div className="w-10 h-10 rounded-xl bg-slate-900 text-white grid place-items-center mb-4 group-hover:bg-indigo-600 transition">
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 11V7a4 4 0 00-8 0v4M5 9h14l1 12H4L5 9z" />
              </svg>
            </div>
            <h3 className="text-base font-semibold text-slate-900 mb-1">My Orders</h3>
            <p className="text-sm text-slate-600">View and track your purchase orders.</p>
            <span className="mt-3 inline-flex text-xs font-medium text-slate-500">Pack-quantity • COD • statuses →</span>
          </Link>

          <Link href="/buyer/profile" className="bg-white rounded-2xl border border-slate-200 shadow-sm p-6 hover:shadow-md transition-shadow">
            <div className="w-10 h-10 rounded-xl bg-white border border-slate-200 text-slate-700 grid place-items-center mb-4">
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
              </svg>
            </div>
            <h3 className="text-base font-semibold text-slate-900 mb-1">Account Settings</h3>
            <p className="text-sm text-slate-600">Manage your profile and preferences.</p>
          </Link>
        </div>

        <div className="mt-8 bg-white rounded-2xl border border-slate-200 shadow-sm p-6 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
          <div>
            <h3 className="text-sm font-semibold text-slate-900">Need help shopping wholesale?</h3>
            <p className="text-sm text-slate-500 mt-1">Prices are net (VAT added at checkout). Check delivery &amp; B2B terms.</p>
          </div>
          <div className="flex gap-2">
            <Link href="/categories" className="px-5 py-2.5 bg-slate-900 text-white text-sm font-medium rounded-full hover:bg-slate-800 shadow transition">
              Browse categories
            </Link>
            <Link href="/buyer/orders" className="px-5 py-2.5 bg-white border border-slate-200 text-sm font-medium rounded-full hover:bg-slate-50 transition">
              My orders
            </Link>
          </div>
        </div>
      </main>
    </div>
  );
}
