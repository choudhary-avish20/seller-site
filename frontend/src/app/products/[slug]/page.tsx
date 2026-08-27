"use client";

import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";
import { api, Product, getImageUrl } from "@/lib/api";
import { Header } from "@/components/Header";
import { useCart } from "@/context/CartContext";
import { useLanguage } from "@/context/LanguageContext";

export default function ProductDetailPage() {
  const params = useParams();
  const slug = params.slug as string;
  const router = useRouter();
  const { addToCart } = useCart();
  const { t } = useLanguage();
  const [product, setProduct] = useState<Product | null>(null);
  const [loading, setLoading] = useState(true);
  const [qty, setQty] = useState(1);
  const [selectedVariant, setSelectedVariant] = useState<string | null>(null);
  const [error, setError] = useState("");

  useEffect(() => {
    api
      .getProductBySlug(slug)
      .then(setProduct)
      .catch((e: unknown) => setError(e instanceof Error ? e.message : "Not found"))
      .finally(() => setLoading(false));
  }, [slug]);

  if (loading) {
    return (
      <div className="min-h-screen bg-slate-50">
        <Header />
        <div className="max-w-7xl mx-auto px-4 py-12 flex justify-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-slate-900" />
        </div>
      </div>
    );
  }

  if (error || !product) {
    return (
      <div className="min-h-screen bg-slate-50">
        <Header />
        <div className="max-w-7xl mx-auto px-4 py-12 text-center">
          <div className="inline-flex flex-col items-center gap-3 bg-white rounded-2xl border border-slate-200 shadow-sm p-8">
            <p className="text-red-600 text-sm">{error || t("products.detail.productNotFound")}</p>
            <Link href="/categories" className="inline-flex px-5 py-2 bg-slate-900 text-white rounded-full text-sm font-medium hover:bg-slate-800 transition">
              {t("products.detail.browseCategories")}
            </Link>
          </div>
        </div>
      </div>
    );
  }

  const out = product.stock_status === "out_of_stock" || product.stock_quantity === 0;
  const variant = product.variants.find((v) => v.id === selectedVariant);
  const priceNet = variant?.price_net_override ?? product.price_net;
  const vat = product.vat_rate;
  const priceGross = variant?.price_net_override ? +(variant.price_net_override * (1 + vat / 100)).toFixed(2) : product.price_gross;

  const handleAdd = () => {
    const label = variant ? `${variant.option_name}: ${variant.option_value} (${variant.sku})` : null;
    addToCart(product, qty, variant?.id, label, priceNet);
    router.push("/cart");
  };

  return (
    <div className="min-h-screen bg-slate-50">
      <Header />
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="text-sm text-slate-500 mb-4">
          <Link href="/categories" className="hover:text-slate-700">{t("products.detail.breadcrumbCategories")}</Link> /{" "}
          <Link href={`/categories/${product.category_slug}`} className="hover:text-slate-700">
            {product.category_name}
          </Link>{" "}
          / <span className="text-slate-900 font-medium">{product.name}</span>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          <div className="bg-white rounded-2xl border border-slate-200 p-3 shadow-sm">
            {product.images[0] ? (
              // eslint-disable-next-line @next/next/no-img-element
              <img src={getImageUrl(product.images[0])} alt={product.name} className="w-full h-96 object-contain bg-slate-50 rounded-xl" />
            ) : (
              <div className="w-full h-96 bg-slate-100 rounded-xl flex items-center justify-center text-slate-500 text-sm">{t("products.detail.noImage")}</div>
            )}
            {product.images.length > 1 && (
              <div className="mt-3 flex gap-2 overflow-x-auto">
                {product.images.map((img, i) => (
                  // eslint-disable-next-line @next/next/no-img-element
                  <img key={i} src={getImageUrl(img)} alt={`thumb ${i}`} className="w-20 h-20 object-cover rounded-xl border border-slate-200 bg-slate-50 shrink-0" />
                ))}
              </div>
            )}
          </div>

          <div>
            <h1 className="text-2xl font-bold tracking-tight text-slate-900">{product.name}</h1>
            <p className="text-sm text-slate-500">/{product.slug} • {product.seller_business_name || t("products.detail.sellerFallback")}</p>

            <div className="mt-4 bg-white rounded-2xl border border-slate-200 p-5 shadow-sm">
              <div className="flex items-baseline gap-2 flex-wrap">
                <span className="text-2xl font-bold tracking-tight text-indigo-700">{priceNet.toFixed(2)} zł</span>
                <span className="text-sm font-medium text-indigo-700">{t("products.detail.net")}</span>
                <span className="text-sm text-slate-500">{priceGross.toFixed(2)} zł {t("products.detail.gross")} • {t("products.detail.vat")} {vat}%</span>
              </div>
              <div className="mt-2 inline-flex items-center gap-2 px-3 py-1 rounded-full bg-indigo-50 border border-indigo-100 text-xs font-medium text-indigo-700">
                {t("products.detail.pack")} {product.pack_size} • {t("products.detail.netPrices")}
              </div>
              <p className={`text-sm mt-3 inline-flex items-center gap-1.5 ${out ? "text-red-600" : "text-emerald-600"}`}>
                <span className={`w-1.5 h-1.5 rounded-full ${out ? "bg-red-500" : "bg-emerald-500"}`} />
                {out ? t("products.detail.outOfStock") : `${product.stock_quantity} ${t("products.detail.inStock")} • ${product.stock_status}`}
              </p>
            </div>

            {product.variants.length > 0 && (
              <div className="mt-4 bg-white rounded-2xl border border-slate-200 p-4 shadow-sm">
                <h3 className="text-sm font-semibold text-slate-900">{t("products.detail.variants")}</h3>
                <div className="mt-2 grid grid-cols-1 gap-2">
                  {product.variants.map((v) => (
                    <label key={v.id} className={`flex items-center gap-2 p-2.5 rounded-xl border cursor-pointer transition ${selectedVariant === v.id ? "border-indigo-300 bg-indigo-50" : "border-slate-200 hover:bg-slate-50"}`}>
                      <input type="radio" name="variant" checked={selectedVariant === v.id} onChange={() => setSelectedVariant(v.id)} className="accent-slate-900" />
                      <span className="text-sm">
                        {v.option_name}: <span className="font-medium">{v.option_value}</span> — {v.sku}
                      </span>
                      <span className="ml-auto text-xs text-slate-600 shrink-0">
                        {v.price_net_override != null ? `${v.price_net_override.toFixed(2)} ${t("products.detail.net")}` : `${product.price_net.toFixed(2)} ${t("products.detail.net")}`} • {v.stock_quantity} packs
                      </span>
                    </label>
                  ))}
                  <label className={`flex items-center gap-2 p-2.5 rounded-xl border cursor-pointer transition ${selectedVariant == null ? "border-indigo-300 bg-indigo-50" : "border-slate-200 hover:bg-slate-50"}`}>
                    <input type="radio" name="variant" checked={selectedVariant == null} onChange={() => setSelectedVariant(null)} className="accent-slate-900" />
                    <span className="text-sm">{t("products.detail.noVariant")}</span>
                  </label>
                </div>
              </div>
            )}

            <div className="mt-4 bg-white rounded-2xl border border-slate-200 p-4 shadow-sm">
              <label className="block text-sm font-medium text-slate-700 mb-1">{t("products.detail.quantityPacks")}</label>
              <div className="flex gap-3">
                <div className="flex items-center rounded-full border border-slate-200 bg-slate-50 p-1">
                  <button type="button" onClick={() => setQty((v) => Math.max(1, v - 1))} disabled={out} className="w-8 h-8 grid place-items-center rounded-full hover:bg-white disabled:opacity-40 text-slate-700">
                    −
                  </button>
                  <input
                    type="number"
                    min={1}
                    max={product.stock_quantity}
                    value={qty}
                    onChange={(e) => setQty(Math.max(1, parseInt(e.target.value) || 1))}
                    className="w-12 text-center bg-transparent text-sm font-medium outline-none"
                    disabled={out}
                  />
                  <button type="button" onClick={() => setQty((v) => v + 1)} disabled={out} className="w-8 h-8 grid place-items-center rounded-full hover:bg-white disabled:opacity-40 text-slate-700">
                    +
                  </button>
                </div>
                <button onClick={handleAdd} disabled={out} className="flex-1 px-4 py-2.5 bg-slate-900 text-white rounded-full hover:bg-slate-800 disabled:opacity-50 text-sm font-medium transition">
                  {t("products.detail.add")} {qty} {qty > 1 ? t("products.detail.packs") : t("products.detail.packSingle")} • {(priceNet * qty).toFixed(2)} zł {t("products.detail.net")}
                </button>
              </div>
              <p className="text-xs text-slate-500 mt-2">
                {t("products.detail.buyingPacks")} {product.pack_size} {t("products.detail.piecesInPack")} • {t("products.detail.gross")} {(priceGross * qty).toFixed(2)} zł
              </p>
            </div>

            {product.description && (
              <div className="mt-6 bg-white rounded-2xl border border-slate-200 p-4 shadow-sm">
                <h3 className="text-sm font-semibold text-slate-900 mb-2">{t("products.detail.description")}</h3>
                <p className="text-sm text-slate-700 whitespace-pre-wrap leading-relaxed">{product.description}</p>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
