"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { useAuth } from "@/context/AuthContext";
import { api, ProductListItem, getImageUrl } from "@/lib/api";
import { useLanguage } from "@/context/LanguageContext";
import { LanguageToggle } from "@/components/LanguageToggle";

export default function SellerProductsPage() {
  const router = useRouter();
  const { isAuthenticated, isSeller, loading } = useAuth();
  const { t } = useLanguage();
  const [products, setProducts] = useState<ProductListItem[]>([]);
  const [loadingData, setLoadingData] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    if (!loading && (!isAuthenticated || !isSeller)) router.push("/auth/login");
  }, [isAuthenticated, isSeller, loading, router]);

  const fetchProducts = async () => {
    setLoadingData(true);
    setError("");
    try {
      const data = await api.listMyProducts();
      setProducts(data);
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "Failed to load products");
    } finally {
      setLoadingData(false);
    }
  };

  useEffect(() => {
    if (isAuthenticated && isSeller) fetchProducts();
  }, [isAuthenticated, isSeller]);

  const handleDelete = async (id: string) => {
    if (!confirm(t("seller.products.confirmDelete"))) return;
    try {
      await api.deleteProduct(id);
      await fetchProducts();
    } catch (e: unknown) {
      alert(e instanceof Error ? e.message : "Delete failed");
    }
  };

  const handleArchive = async (id: string) => {
    try {
      await api.archiveProduct(id);
      await fetchProducts();
    } catch (e: unknown) {
      alert(e instanceof Error ? e.message : "Archive failed");
    }
  };

  const handleStockToggle = async (p: ProductListItem) => {
    const newStatus = p.stock_status === "in_stock" ? "out_of_stock" : "in_stock";
    try {
      await api.toggleStock(p.id, { stock_status: newStatus });
      await fetchProducts();
    } catch (e: unknown) {
      alert(e instanceof Error ? e.message : "Stock toggle failed");
    }
  };

  if (loading || loadingData) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-slate-50">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-slate-900" />
      </div>
    );
  }
  if (!isAuthenticated || !isSeller) return null;

  return (
    <div className="min-h-screen bg-slate-50">
      <nav className="bg-white border-b border-slate-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between h-16 items-center">
            <div className="flex items-center gap-6">
              <h1 className="text-xl font-bold tracking-tight text-slate-900">{t("seller.products.panel")}</h1>
              <Link href="/seller/dashboard" className="text-sm text-slate-500 hover:text-slate-900 transition">{t("seller.products.dashboard")}</Link>
              <span className="text-sm font-semibold text-slate-900 border-b-2 border-slate-900 pb-1 -mb-1">{t("seller.products.products")}</span>
              <Link href="/seller/categories" className="text-sm text-slate-500 hover:text-slate-900 transition hidden sm:inline">{t("seller.products.categories")}</Link>
            </div>
            <div className="flex items-center">
              <LanguageToggle compact />
            </div>
          </div>
        </div>
      </nav>

      <main className="max-w-7xl mx-auto py-8 px-4 sm:px-6 lg:px-8">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-6">
          <div>
            <h2 className="text-2xl font-bold tracking-tight text-slate-900">{t("seller.products.title")}</h2>
            <p className="text-sm text-slate-600 mt-1">{t("seller.products.desc")}</p>
          </div>
          <Link href="/seller/products/new" className="inline-flex items-center justify-center px-5 py-2.5 bg-slate-900 text-white text-sm font-medium rounded-full hover:bg-slate-800 transition shadow-sm">
            {t("seller.products.addProduct")}
          </Link>
        </div>

        {error && <div className="mb-4 bg-red-50 border border-red-200 text-red-700 p-3 rounded-2xl text-sm">{error}</div>}

        {products.length === 0 ? (
          <div className="bg-white rounded-2xl border border-slate-200 shadow-sm p-12 text-center">
            <p className="text-slate-600">{t("seller.products.empty")}</p>
            <Link href="/seller/products/new" className="mt-4 inline-flex px-5 py-2.5 bg-slate-900 text-white rounded-full text-sm font-medium hover:bg-slate-800 transition">{t("seller.products.emptyAdd")}</Link>
          </div>
        ) : (
          <div className="bg-white rounded-2xl border border-slate-200 shadow-sm overflow-hidden">
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-slate-200">
                <thead className="bg-slate-50/80">
                  <tr>
                    <th className="px-4 py-3 text-left text-xs font-semibold text-slate-500 uppercase tracking-wider">{t("seller.products.thProduct")}</th>
                    <th className="px-4 py-3 text-left text-xs font-semibold text-slate-500 uppercase tracking-wider">{t("seller.products.thCategory")}</th>
                    <th className="px-4 py-3 text-left text-xs font-semibold text-slate-500 uppercase tracking-wider">{t("seller.products.thPackPrice")}</th>
                    <th className="px-4 py-3 text-left text-xs font-semibold text-slate-500 uppercase tracking-wider">{t("seller.products.thStock")}</th>
                    <th className="px-4 py-3 text-left text-xs font-semibold text-slate-500 uppercase tracking-wider">{t("seller.products.thStatus")}</th>
                    <th className="px-4 py-3 text-right text-xs font-semibold text-slate-500 uppercase tracking-wider">{t("seller.products.thActions")}</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-200 bg-white">
                  {products.map((p) => (
                    <tr key={p.id} className={p.is_active ? "hover:bg-slate-50 transition" : "bg-slate-100/60 opacity-70"}>
                      <td className="px-4 py-3">
                        <div className="flex gap-3 items-center">
                          {p.images[0] ? (
                            // eslint-disable-next-line @next/next/no-img-element
                            <img src={getImageUrl(p.images[0])} alt={p.name} className="w-12 h-12 object-cover rounded-xl border border-slate-200 bg-slate-50" />
                          ) : (
                            <div className="w-12 h-12 bg-slate-100 rounded-xl border border-slate-200 flex items-center justify-center text-[10px] font-medium text-slate-500">{t("seller.products.noImg")}</div>
                          )}
                          <div className="min-w-0">
                            <p className="text-sm font-semibold text-slate-900 truncate">{p.name}</p>
                            <p className="text-xs text-slate-500 truncate">/{p.slug} {p.is_active ? "" : t("seller.products.archivedLabel")}</p>
                          </div>
                        </div>
                      </td>
                      <td className="px-4 py-3 text-sm text-slate-700">
                        {p.category_name || p.category_slug || "—"}
                        <span className="block text-xs text-slate-500">{p.category_slug}</span>
                      </td>
                      <td className="px-4 py-3 text-sm">
                        <span className="font-semibold text-slate-900">{t("seller.products.pack")} {p.pack_size}</span>
                        <span className="block text-xs text-slate-600">{t("seller.products.net")} {p.price_net.toFixed(2)} • {t("seller.products.gross")} {p.price_gross.toFixed(2)} ({t("seller.products.vat")} {p.vat_rate}%)</span>
                      </td>
                      <td className="px-4 py-3">
                        <div className="flex items-center gap-2 flex-wrap">
                          <span className={`inline-flex px-2.5 py-1 text-xs rounded-full font-medium border ${p.stock_status === "in_stock" ? "bg-emerald-50 text-emerald-700 border-emerald-200" : "bg-red-50 text-red-700 border-red-200"}`}>
                            {p.stock_status}
                          </span>
                          <span className="text-xs text-slate-600">{p.stock_quantity} {t("seller.products.inStock")}</span>
                        </div>
                        <button onClick={() => handleStockToggle(p)} className="mt-1 text-xs font-medium text-slate-900 hover:text-slate-700 underline decoration-slate-300 underline-offset-4">
                          {t("seller.products.toggleStock")}
                        </button>
                      </td>
                      <td className="px-4 py-3">
                        <span className={`inline-flex px-2.5 py-1 text-xs rounded-full font-medium border ${p.is_active ? "bg-emerald-50 text-emerald-700 border-emerald-200" : "bg-slate-100 text-slate-600 border-slate-200"}`}>
                          {p.is_active ? t("seller.products.active") : t("seller.products.archived")}
                        </span>
                      </td>
                      <td className="px-4 py-3 text-right">
                        <div className="flex items-center justify-end gap-2 flex-wrap">
                          <Link href={`/seller/products/${p.id}/edit`} className="inline-flex px-3 py-1.5 bg-white border border-slate-200 rounded-full text-xs font-medium text-slate-700 hover:bg-slate-50 transition">{t("seller.products.edit")}</Link>
                          <button onClick={() => handleArchive(p.id)} className="inline-flex px-3 py-1.5 bg-white border border-slate-200 rounded-full text-xs font-medium text-slate-600 hover:bg-slate-50 transition">
                            {p.is_active ? t("seller.products.archive") : t("seller.products.unarchive")}
                          </button>
                          <button onClick={() => handleDelete(p.id)} className="inline-flex px-3 py-1.5 bg-white border border-red-200 rounded-full text-xs font-medium text-red-600 hover:bg-red-50 transition">{t("seller.products.delete")}</button>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}
      </main>
    </div>
  );
}
