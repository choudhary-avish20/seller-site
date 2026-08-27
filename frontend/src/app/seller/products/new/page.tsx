"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/context/AuthContext";
import { api } from "@/lib/api";
import { ProductForm } from "@/components/ProductForm";
import Link from "next/link";

export default function NewProductPage() {
  const router = useRouter();
  const { isAuthenticated, isSeller, loading } = useAuth();

  useEffect(() => {
    if (!loading && (!isAuthenticated || !isSeller)) router.push("/auth/login");
  }, [isAuthenticated, isSeller, loading, router]);

  if (loading) return <div className="min-h-screen flex items-center justify-center bg-slate-50"><div className="animate-spin rounded-full h-12 w-12 border-b-2 border-slate-900" /></div>;
  if (!isAuthenticated || !isSeller) return null;

  const handleCreate = async (data: Parameters<typeof api.createProduct>[0]) => {
    const res = await api.createProduct(data);
    router.push("/seller/products");
  };

  return (
    <div className="min-h-screen bg-slate-50">
      <nav className="bg-white border-b border-slate-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between h-16 items-center">
            <div className="flex items-center gap-6">
              <h1 className="text-xl font-bold tracking-tight text-slate-900">Seller Panel</h1>
              <Link href="/seller/products" className="text-sm text-slate-500 hover:text-slate-900 transition">Products</Link>
              <span className="text-sm font-semibold text-slate-900 border-b-2 border-slate-900 pb-1 -mb-1 hidden sm:inline">New</span>
            </div>
            <Link href="/seller/dashboard" className="text-sm text-slate-500 hover:text-slate-900 hidden sm:inline">Dashboard</Link>
          </div>
        </div>
      </nav>

      <main className="max-w-3xl mx-auto py-8 px-4 sm:px-6 lg:px-8">
        <div className="mb-6">
          <Link href="/seller/products" className="inline-flex items-center gap-1 text-sm font-medium text-slate-600 hover:text-slate-900 transition">← Back to products</Link>
          <h2 className="mt-3 text-2xl font-bold tracking-tight text-slate-900">Add Product</h2>
          <p className="text-sm text-slate-600 mt-1">Pack pricing, category, stock and images. Seller must be approved.</p>
        </div>

        <div className="bg-white rounded-2xl border border-slate-200 shadow-sm overflow-hidden">
          <div className="p-6 sm:p-8">
            {/* eslint-disable-next-line @typescript-eslint/no-explicit-any */}
            <ProductForm onSubmit={handleCreate as any} submitLabel="Create product" />
          </div>
        </div>
      </main>
    </div>
  );
}
