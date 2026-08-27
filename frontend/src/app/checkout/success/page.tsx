"use client";

import { useSearchParams } from "next/navigation";
import Link from "next/link";
import { Suspense, useEffect, useState } from "react";
import { api, Order } from "@/lib/api";
import { Header } from "@/components/Header";
import { useLanguage } from "@/context/LanguageContext";

function SuccessInner() {
  const params = useSearchParams();
  const orderId = params.get("orderId");
  const { t } = useLanguage();
  const [order, setOrder] = useState<Order | null>(null);

  useEffect(() => {
    if (orderId) api.getOrder(orderId).then(setOrder).catch(() => {});
  }, [orderId]);

  return (
    <div className="min-h-screen bg-slate-50">
      <Header />
      <div className="max-w-xl mx-auto px-4 py-12">
        <div className="bg-white rounded-2xl border border-slate-200 shadow-sm p-8 text-center">
          <div className="w-14 h-14 bg-emerald-50 border border-emerald-200 text-emerald-600 rounded-full flex items-center justify-center mx-auto text-xl">✓</div>
          <h1 className="mt-4 text-2xl font-bold tracking-tight text-slate-900">{t("checkout.success.title")}</h1>
          <p className="text-sm text-slate-500 mt-2">{t("checkout.success.desc")}</p>
          {orderId && <p className="text-xs font-mono text-slate-400 mt-2 bg-slate-50 border border-slate-200 rounded-full inline-block px-3 py-1">{t("checkout.success.order")} {orderId.slice(0, 8)}…</p>}
          {order && (
            <div className="mt-5 text-left bg-slate-50 rounded-2xl border border-slate-200 p-4 text-sm">
              <p>
                <span className="text-slate-500">{t("checkout.success.totalNet")}</span> <span className="font-medium text-slate-900">{order.total_net.toFixed(2)} zł</span>
              </p>
              <p className="font-bold text-slate-900">{t("checkout.success.totalGross")} {order.total_gross.toFixed(2)} zł</p>
              <p className="text-xs text-slate-500 mt-2">{t("checkout.success.shipping")} {order.shipping_address}</p>
            </div>
          )}
          <div className="mt-6 flex gap-3 justify-center flex-wrap">
            <Link href="/categories" className="px-6 py-2.5 bg-slate-900 text-white rounded-full text-sm font-medium hover:bg-slate-800 transition">
              {t("checkout.success.continueShopping")}
            </Link>
            <Link href="/buyer/orders" className="px-6 py-2.5 bg-white border border-slate-200 rounded-full text-sm font-medium hover:bg-slate-50 transition">
              {t("checkout.success.myOrders")}
            </Link>
          </div>
        </div>
      </div>
    </div>
  );
}

export default function SuccessPage() {
  return (
    <Suspense fallback={<div className="min-h-screen bg-slate-50 flex items-center justify-center text-sm text-slate-500">Loading…</div>}>
      <SuccessInner />
    </Suspense>
  );
}
