"use client";

import Link from "next/link";
import { ProductListItem, getImageUrl } from "@/lib/api";
import { useCart } from "@/context/CartContext";
import { useLanguage } from "@/context/LanguageContext";
import { useState } from "react";

export function ProductCard({ product }: { product: ProductListItem }) {
  const { addToCart } = useCart();
  const { t } = useLanguage();
  const [qty, setQty] = useState(1);
  const out = product.stock_status === "out_of_stock" || product.stock_quantity === 0;

  return (
    <div className="group bg-white rounded-2xl border border-slate-200 overflow-hidden flex flex-col hover:border-slate-300 hover:shadow-lg hover:shadow-slate-200/50 transition-all duration-200">
      <Link href={`/products/${product.slug}`} className="block relative overflow-hidden bg-slate-50">
        {product.images[0] ? (
          // eslint-disable-next-line @next/next/no-img-element
          <img src={getImageUrl(product.images[0])} alt={product.name} className="w-full h-[190px] object-cover group-hover:scale-[1.02] transition duration-300" />
        ) : (
          <div className="w-full h-[190px] bg-slate-100 flex flex-col items-center justify-center gap-2 text-slate-400">
            <div className="w-10 h-10 rounded-xl bg-white border border-slate-200 grid place-items-center">▦</div>
            <span className="text-xs">{t("product.noImage")}</span>
          </div>
        )}
        <span className="absolute left-3 top-3 px-2 py-1 bg-white/95 backdrop-blur rounded-full text-[11px] font-medium text-slate-700 border border-slate-200 shadow-sm">
          {product.category_name || product.category_slug || t("product.noCategory")}
        </span>
        {out && <span className="absolute right-3 top-3 px-2 py-1 bg-slate-900 text-white rounded-full text-[11px] font-medium">{t("product.out")}</span>}
      </Link>

      <div className="p-4 flex-1 flex flex-col">
        <Link href={`/products/${product.slug}`} className="text-[13px] font-medium leading-snug text-slate-900 hover:text-indigo-600 line-clamp-2 min-h-[36px]">
          {product.name}
        </Link>

        <div className="mt-3 flex items-end justify-between gap-2">
          <div>
            <div className="flex items-baseline gap-1.5">
              <span className="text-lg font-bold tracking-tight text-indigo-700">{product.price_net.toFixed(2)} zł</span>
              <span className="text-xs font-medium text-slate-500">{t("product.net")}</span>
            </div>
            <div className="text-xs text-slate-500">{product.price_gross.toFixed(2)} zł {t("product.gross")} • VAT {product.vat_rate}%</div>
          </div>
          <span className="shrink-0 px-2.5 py-1 bg-indigo-50 text-indigo-700 rounded-full text-xs font-medium border border-indigo-100">
            {t("product.pack")} {product.pack_size}
          </span>
        </div>

        <div className="mt-2 flex items-center gap-2 text-xs">
          <span className={`inline-flex items-center gap-1.5 ${out ? "text-red-600" : "text-emerald-600"}`}>
            <span className={`w-1.5 h-1.5 rounded-full ${out ? "bg-red-500" : "bg-emerald-500"}`} />
            {out ? t("product.out") : `${product.stock_quantity} ${t("product.available")}`}
          </span>
          <span className="text-slate-300">•</span>
          <span className="text-slate-500">{product.stock_status}</span>
        </div>

        <div className="mt-4 flex items-center gap-2">
          <div className="flex items-center rounded-full border border-slate-200 bg-slate-50 p-1">
            <button onClick={() => setQty((v) => Math.max(1, v - 1))} disabled={out} className="w-7 h-7 grid place-items-center rounded-full hover:bg-white disabled:opacity-40 text-slate-700">
              −
            </button>
            <input
              type="number"
              min={1}
              value={qty}
              onChange={(e) => setQty(Math.max(1, parseInt(e.target.value) || 1))}
              className="w-10 text-center bg-transparent text-sm font-medium outline-none"
              disabled={out}
            />
            <button onClick={() => setQty((v) => v + 1)} disabled={out} className="w-7 h-7 grid place-items-center rounded-full hover:bg-white disabled:opacity-40 text-slate-700">
              +
            </button>
          </div>
          <button
            onClick={() => addToCart(product, qty)}
            disabled={out}
            className="flex-1 py-2.5 bg-slate-900 text-white text-sm font-medium rounded-full hover:bg-slate-800 disabled:opacity-50 disabled:cursor-not-allowed transition flex items-center justify-center gap-1.5"
          >
            <svg className="w-4 h-4" fill="none" stroke="currentColor" strokeWidth={1.8} viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" d="M6 6h15l-1.5 8H6z M6 6L5 2H2" />
            </svg>
            {t("product.add")}
          </button>
        </div>
        <p className="text-[11px] text-center text-slate-400 mt-2">{t("product.netPricesNote")}</p>
      </div>
    </div>
  );
}

export function ProductGrid({ products }: { products: ProductListItem[] }) {
  const { t } = useLanguage();
  if (products.length === 0) {
    return <p className="text-sm text-slate-500 bg-white p-8 rounded-2xl border border-slate-200 text-center">{t("search.noResults") || "No products found."}</p>;
  }
  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4 sm:gap-5">
      {products.map((p) => (
        <ProductCard key={p.id} product={p} />
      ))}
    </div>
  );
}
