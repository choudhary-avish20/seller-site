"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useAuth } from "@/context/AuthContext";
import { api, Order } from "@/lib/api";
import { Header } from "@/components/Header";
import { useRouter } from "next/navigation";

export default function BuyerOrdersPage() {
  const { isAuthenticated, isBuyer, loading } = useAuth();
  const router = useRouter();
  const [orders, setOrders] = useState<Order[]>([]);
  const [loadingData, setLoadingData] = useState(true);

  useEffect(() => {
    if (!loading && (!isAuthenticated || !isBuyer)) router.push("/auth/login");
  }, [isAuthenticated, isBuyer, loading, router]);

  useEffect(() => {
    if (isAuthenticated && isBuyer) {
      api
        .listOrders()
        .then(setOrders)
        .finally(() => setLoadingData(false));
    }
  }, [isAuthenticated, isBuyer]);

  if (loading || loadingData)
    return (
      <div className="min-h-screen flex items-center justify-center bg-slate-50">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-slate-900" />
      </div>
    );
  if (!isAuthenticated || !isBuyer) return null;

  const statusPill = (status: string) => {
    if (status === "pending") return "bg-amber-50 text-amber-700 border border-amber-200";
    if (status === "cancelled") return "bg-red-50 text-red-700 border border-red-200";
    return "bg-emerald-50 text-emerald-700 border border-emerald-200";
  };

  return (
    <div className="min-h-screen bg-slate-50">
      <Header />
      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="mb-6">
          <h1 className="text-2xl font-bold tracking-tight text-slate-900">My orders</h1>
          <p className="text-sm text-slate-500 mt-1">Pack-quantity orders • COD • statuses pending → delivered</p>
        </div>

        {orders.length === 0 ? (
          <div className="mt-6 bg-white rounded-2xl border border-slate-200 shadow-sm p-8 text-center">
            <div className="mx-auto w-12 h-12 rounded-full bg-slate-50 border border-slate-200 grid place-items-center mb-3">
              <svg className="w-6 h-6 text-slate-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.7} d="M16 11V7a4 4 0 00-8 0v4M5 9h14l1 12H4L5 9z" />
              </svg>
            </div>
            <p className="text-sm font-medium text-slate-900">No orders yet.</p>
            <p className="text-sm text-slate-500 mt-1">Browse our catalog to place your first wholesale order.</p>
            <Link href="/categories" className="mt-4 inline-flex items-center justify-center px-5 py-2.5 bg-slate-900 text-white text-sm font-medium rounded-full hover:bg-slate-800 shadow transition">
              Browse products →
            </Link>
          </div>
        ) : (
          <div className="mt-6 space-y-4">
            {orders.map((o) => (
              <div key={o.id} className="bg-white rounded-2xl border border-slate-200 shadow-sm p-5">
                <div className="flex flex-wrap justify-between items-center gap-2 text-sm">
                  <span className="font-semibold tracking-tight text-slate-900">Order #{o.id.slice(0, 8)}</span>
                  <span className={`px-2.5 py-0.5 rounded-full text-xs font-medium ${statusPill(o.status)}`}>{o.status}</span>
                </div>
                <p className="text-xs text-slate-500 mt-2">
                  {new Date(o.created_at).toLocaleString()} • <span className="font-medium text-slate-700">Gross {o.total_gross.toFixed(2)} zł</span> (net {o.total_net.toFixed(2)} zł)
                </p>
                <p className="text-xs text-slate-500 mt-1">Ship: {o.shipping_address}</p>
                <div className="mt-3 divide-y divide-slate-100 text-sm bg-slate-50 rounded-xl border border-slate-200 p-3">
                  {o.items.map((it) => (
                    <div key={it.id} className="py-2 flex justify-between gap-3 first:pt-1 last:pb-1">
                      <span className="text-slate-700">
                        {it.product_name_snapshot} <span className="text-slate-500 text-xs">(pack {it.pack_size_snapshot}) × {it.pack_quantity}</span>
                      </span>
                      <span className="font-medium text-slate-900 whitespace-nowrap">{(it.price_gross_snapshot * it.pack_quantity).toFixed(2)} zł</span>
                    </div>
                  ))}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
