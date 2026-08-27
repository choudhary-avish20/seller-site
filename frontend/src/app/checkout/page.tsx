"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { useCart } from "@/context/CartContext";
import { useAuth } from "@/context/AuthContext";
import { Header } from "@/components/Header";
import { api } from "@/lib/api";
import { useLanguage } from "@/context/LanguageContext";

export default function CheckoutPage() {
  const router = useRouter();
  const { items, totalNet, totalGross, clearCart } = useCart();
  const { isAuthenticated, isBuyer } = useAuth();
  const { t } = useLanguage();
  const [address, setAddress] = useState("");
  const [notes, setNotes] = useState("");
  const [error, setError] = useState("");
  const [submitting, setSubmitting] = useState(false);

  const handlePlace = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    if (!isAuthenticated) {
      router.push("/auth/login?callbackUrl=/checkout");
      return;
    }
    if (!isBuyer) {
      setError(t("checkout.errorBuyerOnly"));
      return;
    }
    if (items.length === 0) {
      setError(t("checkout.errorCartEmpty"));
      return;
    }
    if (!address.trim()) {
      setError(t("checkout.errorAddress"));
      return;
    }
    setSubmitting(true);
    try {
      const res = await api.createOrder({
        shipping_address: address,
        notes: notes || undefined,
        items: items.map((it) => ({ product_id: it.product.id, variant_id: it.variantId || null, pack_quantity: it.packQuantity })),
      });
      clearCart();
      router.push(`/checkout/success?orderId=${res.id}`);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Checkout failed");
    } finally {
      setSubmitting(false);
    }
  };

  if (items.length === 0) {
    return (
      <div className="min-h-screen bg-slate-50">
        <Header />
        <div className="max-w-xl mx-auto px-4 py-12">
          <div className="bg-white rounded-2xl border border-slate-200 shadow-sm p-8 text-center">
            <p className="text-slate-600">{t("checkout.cartEmpty")}</p>
            <Link href="/categories" className="mt-4 inline-flex px-5 py-2 bg-slate-900 text-white rounded-full text-sm font-medium hover:bg-slate-800 transition">
              {t("checkout.browseProducts")}
            </Link>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-slate-50">
      <Header />
      <div className="max-w-3xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <h1 className="text-2xl font-bold tracking-tight text-slate-900">{t("checkout.title")}</h1>
        <p className="text-sm text-slate-500">{t("checkout.codDesc")}</p>

        <div className="mt-6 grid grid-cols-1 lg:grid-cols-2 gap-6">
          <form onSubmit={handlePlace} className="bg-white rounded-2xl border border-slate-200 shadow-sm p-6 space-y-4">
            {error && <div className="bg-red-50 border border-red-200 text-red-700 p-3 rounded-xl text-sm">{error}</div>}
            {!isAuthenticated && (
              <div className="bg-amber-50 border border-amber-200 text-amber-800 p-3 rounded-xl text-sm">
                {t("checkout.signInPrompt").split("sign in")[0]}
                <Link href="/auth/login" className="underline font-medium">
                  {t("checkout.signIn")}
                </Link>
                {t("checkout.signInPrompt").split("sign in")[1] || ""}
              </div>
            )}

            <div>
              <label className="block text-sm font-medium text-slate-700">{t("checkout.shippingAddress")}</label>
              <textarea
                value={address}
                onChange={(e) => setAddress(e.target.value)}
                rows={3}
                required
                placeholder={t("checkout.shippingPlaceholder")}
                className="mt-1 w-full px-3.5 py-2.5 border border-slate-200 rounded-xl text-sm bg-slate-50 placeholder:text-slate-400 focus:bg-white focus:border-slate-300 focus:ring-4 focus:ring-slate-100 outline-none transition"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-slate-700">{t("checkout.notes")}</label>
              <textarea
                value={notes}
                onChange={(e) => setNotes(e.target.value)}
                rows={2}
                placeholder={t("checkout.notesPlaceholder")}
                className="mt-1 w-full px-3.5 py-2.5 border border-slate-200 rounded-xl text-sm bg-slate-50 placeholder:text-slate-400 focus:bg-white focus:border-slate-300 focus:ring-4 focus:ring-slate-100 outline-none transition"
              />
            </div>

            <div className="bg-slate-50 rounded-xl border border-slate-100 p-3.5 text-sm">
              <div className="flex justify-between">
                <span className="text-slate-600">{t("checkout.net")}</span>
                <span className="font-medium text-slate-900">{totalNet.toFixed(2)} zł</span>
              </div>
              <div className="flex justify-between font-bold tracking-tight">
                <span className="text-slate-900">{t("checkout.grossCOD")}</span>
                <span className="text-slate-900">{totalGross.toFixed(2)} zł</span>
              </div>
              <p className="text-xs text-slate-500 mt-2">{t("checkout.payNote")}</p>
            </div>

            <button
              type="submit"
              disabled={submitting}
              className="w-full px-4 py-3 bg-slate-900 text-white rounded-full hover:bg-slate-800 disabled:opacity-50 transition font-medium text-sm"
            >
              {submitting ? t("checkout.placing") : `${t("checkout.placeOrder")} ${totalGross.toFixed(2)} zł ${t("checkout.codSuffix")}`}
            </button>
          </form>

          <div className="bg-white rounded-2xl border border-slate-200 shadow-sm p-6">
            <h3 className="font-semibold text-slate-900 text-sm">
              {t("checkout.orderSummary")} {items.length} {t("checkout.itemsPackBased")}
            </h3>
            <div className="mt-3 divide-y divide-slate-100 text-sm">
              {items.map((it) => (
                <div key={`${it.product.id}-${it.variantId || "base"}`} className="py-2.5 flex justify-between gap-3">
                  <span className="text-slate-700 truncate pr-2">
                    {it.product.name} {it.variantLabel ? `(${it.variantLabel})` : ""} × {it.packQuantity} {it.packQuantity > 1 ? t("cart.packs") : "pack"}
                  </span>
                  <span className="font-medium text-slate-900 shrink-0">{((it.variantPriceNet ?? it.product.price_gross) * it.packQuantity).toFixed(2)} zł</span>
                </div>
              ))}
            </div>
            <div className="mt-4 flex items-center justify-between">
              <span className="text-xs text-slate-500">{t("cart.codNoteDetail")}</span>
              <Link href="/cart" className="text-sm font-medium text-slate-600 hover:text-slate-900 bg-slate-50 border border-slate-200 px-3.5 py-1.5 rounded-full hover:bg-white transition">
                {t("checkout.editCart")}
              </Link>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
