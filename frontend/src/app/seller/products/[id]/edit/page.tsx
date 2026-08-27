"use client";

import { useEffect, useState } from "react";
import { useRouter, useParams } from "next/navigation";
import Link from "next/link";
import { useAuth } from "@/context/AuthContext";
import { api, Product } from "@/lib/api";
import { ProductForm, ProductFormData } from "@/components/ProductForm";

export default function EditProductPage() {
  const router = useRouter();
  const params = useParams();
  const id = params.id as string;
  const { isAuthenticated, isSeller, loading } = useAuth();
  const [product, setProduct] = useState<Product | null>(null);
  const [loadingProd, setLoadingProd] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    if (!loading && (!isAuthenticated || !isSeller)) router.push("/auth/login");
  }, [isAuthenticated, isSeller, loading, router]);

  useEffect(() => {
    if (isAuthenticated && isSeller && id) {
      api.getProduct(id).then((p) => {
        setProduct(p);
        setLoadingProd(false);
      }).catch((e: unknown) => {
        setError(e instanceof Error ? e.message : "Failed to load");
        setLoadingProd(false);
      });
    }
  }, [isAuthenticated, isSeller, id]);

  if (loading || loadingProd) {
    return <div className="min-h-screen flex items-center justify-center bg-slate-50"><div className="animate-spin rounded-full h-12 w-12 border-b-2 border-slate-900" /></div>;
  }
  if (!isAuthenticated || !isSeller) return null;
  if (error) return <div className="min-h-screen flex items-center justify-center bg-slate-50 text-red-600"><div className="bg-white rounded-2xl border border-red-200 p-6 text-sm">{error}</div></div>;
  if (!product) return <div className="min-h-screen flex items-center justify-center bg-slate-50 text-slate-600">Not found</div>;

  const initial: ProductFormData = {
    name: product.name,
    slug: product.slug,
    description: product.description || "",
    images: product.images,
    category_id: product.category_id,
    pack_size: product.pack_size,
    price_net: product.price_net,
    vat_rate: product.vat_rate,
    price_gross: product.price_gross,
    stock_quantity: product.stock_quantity,
    stock_status: product.stock_status,
    is_active: product.is_active,
    variants: product.variants.map((v) => ({
      sku: v.sku,
      option_name: v.option_name,
      option_value: v.option_value,
      price_net_override: v.price_net_override,
      stock_quantity: v.stock_quantity,
    })),
  };

  const handleUpdate = async (data: ProductFormData) => {
    await api.updateProduct(id, {
      name: data.name,
      slug: data.slug || undefined,
      description: data.description,
      images: data.images,
      category_id: data.category_id,
      pack_size: data.pack_size,
      price_net: data.price_net,
      vat_rate: data.vat_rate,
      price_gross: data.price_gross,
      stock_quantity: data.stock_quantity,
      stock_status: data.stock_status,
      is_active: data.is_active,
      variants: data.variants,
    });
    router.push("/seller/products");
  };

  return (
    <div className="min-h-screen bg-slate-50">
      <nav className="bg-white border-b border-slate-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between h-16 items-center">
            <h1 className="text-xl font-bold tracking-tight text-slate-900">Edit Product</h1>
            <div className="flex items-center gap-4">
              <Link href="/seller/products" className="text-sm font-medium text-slate-600 hover:text-slate-900">Products</Link>
              <Link href="/seller/dashboard" className="text-sm text-slate-500 hover:text-slate-900 hidden sm:inline">Dashboard</Link>
            </div>
          </div>
        </div>
      </nav>

      <main className="max-w-3xl mx-auto py-8 px-4 sm:px-6 lg:px-8">
        <Link href="/seller/products" className="inline-flex items-center gap-1 text-sm font-medium text-slate-600 hover:text-slate-900 transition">← Back</Link>
        <div className="mt-3 mb-6">
          <h2 className="text-2xl font-bold tracking-tight text-slate-900">{product.name}</h2>
          <p className="text-sm text-slate-500">/{product.slug}</p>
        </div>
        <div className="bg-white rounded-2xl border border-slate-200 shadow-sm overflow-hidden">
          <div className="p-6 sm:p-8">
            <ProductForm initial={initial} onSubmit={handleUpdate} submitLabel="Save changes" />
          </div>
        </div>
      </main>
    </div>
  );
}
