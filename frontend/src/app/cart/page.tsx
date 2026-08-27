"use client";

import Link from "next/link";
import { useCart } from "@/context/CartContext";
import { Header } from "@/components/Header";
import { getImageUrl } from "@/lib/api";
import { useLanguage } from "@/context/LanguageContext";

export default function CartPage() {
  const { items, updateQuantity, removeFromCart, totalNet, totalGross, count } = useCart();
  const { t } = useLanguage();

  if (items.length === 0) {
    return (
      <div className="min-h-screen bg-slate-50">
        <Header />
        <div className="max-w-3xl mx-auto px-4 py-12">
          <div className="bg-white rounded-2xl border border-slate-200 shadow-sm p-10 text-center">
            <div className="w-12 h-12 bg-slate-100 rounded-full grid place-items-center mx-auto text-slate-500">🛒</div>
            <p className="mt-4 font-medium text-slate-900">{t("cart.empty")}</p>
            <p className="text-sm text-slate-500 mt-1">{t("cart.packQuantityBased")}</p>
            <Link href="/categories" className="mt-6 inline-flex px-6 py-2.5 bg-slate-900 text-white rounded-full text-sm font-medium hover:bg-slate-800 transition">
              {t("cart.browse")}
            </Link>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-slate-50">
      <Header />
      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="flex items-end justify-between gap-4">
          <div>
            <h1 className="text-2xl font-bold tracking-tight text-slate-900">
              {t("cart.title")} — {count} {t("cart.packs")}
            </h1>
            <p className="text-sm text-slate-500">{t("cart.packQuantityBased")}</p>
          </div>
          <Link href="/categories" className="hidden sm:inline-flex text-sm font-medium text-indigo-600 hover:text-indigo-500">
            {t("cart.continueShopping")} →
          </Link>
        </div>

        <div className="mt-6 bg-white rounded-2xl border border-slate-200 shadow-sm divide-y divide-slate-100 overflow-hidden">
          {items.map((it) => {
            const net = it.variantPriceNet ?? it.product.price_net;
            const vat = (it.product as { vat_rate: number }).vat_rate ?? 23;
            const gross = it.variantPriceNet != null ? +(net * (1 + vat / 100)).toFixed(2) : it.product.price_gross;
            return (
              <div key={`${it.product.id}-${it.variantId || "base"}`} className="p-4 flex gap-4">
                {it.product.images[0] ? (
                  // eslint-disable-next-line @next/next/no-img-element
                  <img src={getImageUrl(it.product.images[0])} alt={it.product.name} className="w-20 h-20 object-cover rounded-xl border border-slate-200 bg-slate-50 shrink-0" />
                ) : (
                  <div className="w-20 h-20 bg-slate-100 rounded-xl border border-slate-200 flex items-center justify-center text-xs text-slate-500 shrink-0">
                    {t("cart.noImg")}
                  </div>
                )}
                <div className="flex-1 min-w-0">
                  <Link href={`/products/${it.product.slug}`} className="text-sm font-medium text-slate-900 hover:text-indigo-600 line-clamp-2">
                    {it.product.name}
                  </Link>
                  <p className="text-xs text-slate-500">
                    {t("cart.pack")} {it.product.pack_size} • {it.product.category_name || it.product.category_slug}
                  </p>
                  {it.variantLabel && <p className="text-xs font-medium text-indigo-600 mt-0.5">{it.variantLabel}</p>}
                  <p className="text-sm mt-1.5 text-slate-900">
                    {gross.toFixed(2)} zł <span className="text-xs text-slate-500">{t("cart.gross")}</span>{" "}
                    <span className="text-xs text-slate-400">({net.toFixed(2)} {t("cart.net")})</span> × {it.packQuantity} ={" "}
                    <span className="font-semibold">{(gross * it.packQuantity).toFixed(2)} zł</span>
                  </p>
                </div>
                <div className="flex flex-col gap-2 items-end shrink-0">
                  <div className="flex items-center gap-1 rounded-full border border-slate-200 bg-slate-50 p-1">
                    <button
                      onClick={() => updateQuantity(it.product.id, it.variantId, Math.max(1, it.packQuantity - 1))}
                      className="w-7 h-7 grid place-items-center rounded-full hover:bg-white text-slate-700 text-sm transition"
                    >
                      −
                    </button>
                    <span className="w-8 text-center text-sm font-medium text-slate-900">{it.packQuantity}</span>
                    <button
                      onClick={() => updateQuantity(it.product.id, it.variantId, it.packQuantity + 1)}
                      className="w-7 h-7 grid place-items-center rounded-full hover:bg-white text-slate-700 text-sm transition"
                    >
                      +
                    </button>
                  </div>
                  <button onClick={() => removeFromCart(it.product.id, it.variantId)} className="text-xs font-medium text-red-600 hover:text-red-500 px-2 py-1 rounded-full hover:bg-red-50 transition">
                    {t("cart.remove")}
                  </button>
                </div>
              </div>
            );
          })}
        </div>

        <div className="mt-6 bg-white rounded-2xl border border-slate-200 shadow-sm p-6">
          <div className="flex justify-between text-sm">
            <span className="text-slate-500">{t("cart.netTotal")}</span>
            <span className="font-medium text-slate-900">{totalNet.toFixed(2)} zł</span>
          </div>
          <div className="flex justify-between text-base font-bold tracking-tight mt-1">
            <span className="text-slate-900">{t("cart.grossTotal")}</span>
            <span className="text-slate-900">{totalGross.toFixed(2)} zł</span>
          </div>
          <p className="text-xs text-slate-500 mt-2">{t("cart.codNoteDetail")}</p>
          <Link href="/checkout" className="mt-4 flex w-full justify-center px-4 py-3 bg-slate-900 text-white rounded-full hover:bg-slate-800 transition font-medium text-sm">
            {t("cart.proceedCheckout")}
          </Link>
          <Link href="/categories" className="mt-3 block text-center text-sm font-medium text-slate-600 hover:text-slate-900">
            {t("cart.continueShopping")}
          </Link>
        </div>
      </div>
    </div>
  );
}
