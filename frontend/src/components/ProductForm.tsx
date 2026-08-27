"use client";

import { useEffect, useState } from "react";
import { api, CategoryTreeNode, getImageUrl } from "@/lib/api";
import { flattenTree } from "@/components/CategoryTree";
import { useLanguage } from "@/context/LanguageContext";

type VariantRow = {
  sku: string;
  option_name: string;
  option_value: string;
  price_net_override?: number | null;
  stock_quantity: number;
};

export type ProductFormData = {
  name: string;
  slug?: string;
  description?: string;
  images: string[];
  category_id: string;
  pack_size: number;
  price_net: number;
  vat_rate: number;
  price_gross?: number;
  stock_quantity: number;
  stock_status: "in_stock" | "out_of_stock";
  is_active: boolean;
  variants: VariantRow[];
};

export function ProductForm({
  initial,
  onSubmit,
  submitLabel,
}: {
  initial?: Partial<ProductFormData>;
  onSubmit: (data: ProductFormData) => Promise<void>;
  submitLabel: string;
}) {
  const { t } = useLanguage();
  const [tree, setTree] = useState<CategoryTreeNode[]>([]);
  const [testImages, setTestImages] = useState<string[]>([]);
  const [form, setForm] = useState<ProductFormData>({
    name: initial?.name || "",
    slug: initial?.slug || "",
    description: initial?.description || "",
    images: initial?.images || [],
    category_id: initial?.category_id || "",
    pack_size: initial?.pack_size || 1,
    price_net: initial?.price_net ?? 0,
    vat_rate: initial?.vat_rate ?? 23,
    price_gross: initial?.price_gross,
    stock_quantity: initial?.stock_quantity ?? 0,
    stock_status: initial?.stock_status || "in_stock",
    is_active: initial?.is_active ?? true,
    variants: initial?.variants || [],
  });
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState("");
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    api.getCategoryTree(false).then(setTree).catch(() => {});
    api.listTestImages().then(setTestImages).catch(() => {});
  }, []);

  useEffect(() => {
    if (initial) setForm((prev) => ({ ...prev, ...initial, images: initial.images || prev.images, variants: initial.variants || prev.variants }));
  }, [initial]);

  const flat = flattenTree(tree);

  const handleImageUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files;
    if (!files || files.length === 0) return;
    setUploading(true);
    setError("");
    try {
      for (const file of Array.from(files)) {
        const res = await api.uploadImage(file);
        setForm((prev) => ({ ...prev, images: [...prev.images, res.url] }));
      }
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Upload failed");
    } finally {
      setUploading(false);
      e.target.value = "";
    }
  };

  const addTestImage = (name: string) => {
    const url = `/api/v1/uploads/test-images/${name}`;
    setForm((prev) => ({ ...prev, images: [...prev.images, url] }));
  };

  const computedGross = form.price_net ? (form.price_net * (1 + form.vat_rate / 100)).toFixed(2) : "0.00";

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    if (!form.name.trim()) return setError(t("productForm.errorName"));
    if (!form.category_id) return setError(t("productForm.errorCategory"));
    if (form.pack_size < 1) return setError(t("productForm.errorPack"));
    setSubmitting(true);
    try {
      await onSubmit(form);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Save failed");
    } finally {
      setSubmitting(false);
    }
  };

  const addVariant = () => {
    setForm((prev) => ({
      ...prev,
      variants: [...prev.variants, { sku: "", option_name: "size", option_value: "", stock_quantity: 0 }],
    }));
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-6 bg-white p-6 rounded-2xl shadow-sm border border-slate-200">
      {error && <div className="bg-red-50 border border-red-200 text-red-700 p-3 rounded-xl text-sm">{error}</div>}

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div>
          <label className="block text-sm font-medium text-slate-700">{t("productForm.name")}</label>
          <input
            value={form.name}
            onChange={(e) => setForm({ ...form, name: e.target.value })}
            className="mt-1 w-full px-3.5 py-2.5 border border-slate-200 rounded-xl text-sm bg-slate-50 placeholder:text-slate-400 focus:bg-white focus:border-slate-300 focus:ring-4 focus:ring-slate-100 outline-none transition"
            required
          />
        </div>
        <div>
          <label className="block text-sm font-medium text-slate-700">{t("productForm.slug")}</label>
          <input
            value={form.slug}
            onChange={(e) => setForm({ ...form, slug: e.target.value })}
            className="mt-1 w-full px-3.5 py-2.5 border border-slate-200 rounded-xl text-sm bg-slate-50 placeholder:text-slate-400 focus:bg-white focus:border-slate-300 focus:ring-4 focus:ring-slate-100 outline-none transition"
            placeholder={t("productForm.slugPlaceholder")}
          />
        </div>
      </div>

      <div>
        <label className="block text-sm font-medium text-slate-700">{t("productForm.description")}</label>
        <textarea
          value={form.description}
          onChange={(e) => setForm({ ...form, description: e.target.value })}
          rows={3}
          className="mt-1 w-full px-3.5 py-2.5 border border-slate-200 rounded-xl text-sm bg-slate-50 placeholder:text-slate-400 focus:bg-white focus:border-slate-300 focus:ring-4 focus:ring-slate-100 outline-none transition"
        />
      </div>

      <div>
        <label className="block text-sm font-medium text-slate-700">{t("productForm.category")}</label>
        <select
          value={form.category_id}
          onChange={(e) => setForm({ ...form, category_id: e.target.value })}
          className="mt-1 w-full px-3.5 py-2.5 border border-slate-200 rounded-xl text-sm bg-slate-50 focus:bg-white focus:border-slate-300 focus:ring-4 focus:ring-slate-100 outline-none transition"
          required
        >
          <option value="">{t("productForm.categoryPlaceholder")}</option>
          {flat.map((f) => (
            <option key={f.id} value={f.id}>
              {"—".repeat(f.depth)} {f.name} (/{f.slug})
            </option>
          ))}
        </select>
        <p className="text-xs text-slate-500 mt-1">{t("productForm.categoryHint")}</p>
      </div>

      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <div>
          <label className="block text-sm font-medium text-slate-700">{t("productForm.packSize")}</label>
          <input
            type="number"
            min={1}
            value={form.pack_size}
            onChange={(e) => setForm({ ...form, pack_size: parseInt(e.target.value) || 1 })}
            className="mt-1 w-full px-3.5 py-2.5 border border-slate-200 rounded-xl text-sm bg-slate-50 focus:bg-white focus:border-slate-300 focus:ring-4 focus:ring-slate-100 outline-none transition"
          />
        </div>
        <div>
          <label className="block text-sm font-medium text-slate-700">{t("productForm.priceNet")}</label>
          <input
            type="number"
            step="0.01"
            min={0}
            value={form.price_net}
            onChange={(e) => setForm({ ...form, price_net: parseFloat(e.target.value) || 0 })}
            className="mt-1 w-full px-3.5 py-2.5 border border-slate-200 rounded-xl text-sm bg-slate-50 focus:bg-white focus:border-slate-300 focus:ring-4 focus:ring-slate-100 outline-none transition"
          />
        </div>
        <div>
          <label className="block text-sm font-medium text-slate-700">{t("productForm.vat")}</label>
          <input
            type="number"
            step="0.01"
            min={0}
            max={100}
            value={form.vat_rate}
            onChange={(e) => setForm({ ...form, vat_rate: parseFloat(e.target.value) || 0 })}
            className="mt-1 w-full px-3.5 py-2.5 border border-slate-200 rounded-xl text-sm bg-slate-50 focus:bg-white focus:border-slate-300 focus:ring-4 focus:ring-slate-100 outline-none transition"
          />
          <span className="text-xs text-slate-500">{t("productForm.grossApprox")} {computedGross}</span>
        </div>
        <div>
          <label className="block text-sm font-medium text-slate-700">{t("productForm.stockQty")}</label>
          <input
            type="number"
            min={0}
            value={form.stock_quantity}
            onChange={(e) => setForm({ ...form, stock_quantity: parseInt(e.target.value) || 0 })}
            className="mt-1 w-full px-3.5 py-2.5 border border-slate-200 rounded-xl text-sm bg-slate-50 focus:bg-white focus:border-slate-300 focus:ring-4 focus:ring-slate-100 outline-none transition"
          />
        </div>
      </div>

      <div className="grid grid-cols-2 gap-4">
        <div>
          <label className="block text-sm font-medium text-slate-700">{t("productForm.stockStatus")}</label>
          <select
            value={form.stock_status}
            onChange={(e) => setForm({ ...form, stock_status: e.target.value as "in_stock" | "out_of_stock" })}
            className="mt-1 w-full px-3.5 py-2.5 border border-slate-200 rounded-xl text-sm bg-slate-50 focus:bg-white focus:border-slate-300 focus:ring-4 focus:ring-slate-100 outline-none transition"
          >
            <option value="in_stock">{t("productForm.inStock")}</option>
            <option value="out_of_stock">{t("productForm.outOfStock")}</option>
          </select>
        </div>
        <label className="flex items-center gap-2 text-sm mt-6 text-slate-700">
          <input type="checkbox" checked={form.is_active} onChange={(e) => setForm({ ...form, is_active: e.target.checked })} className="rounded border-slate-300 accent-slate-900" />
          {t("productForm.active")}
        </label>
      </div>

      <div>
        <label className="block text-sm font-medium text-slate-700">{t("productForm.images")}</label>
        <p className="text-xs text-slate-500 mb-2">
          {t("productForm.imagesHint")} <code className="bg-slate-100 px-1 py-0.5 rounded">backend/uploads/products</code> {t("productForm.imagesHint2")}{" "}
          <code className="bg-slate-100 px-1 py-0.5 rounded">assets/test-images</code> {t("productForm.imagesHint3")}
        </p>

        <div className="flex flex-wrap gap-3 mb-3">
          {form.images.map((img, idx) => (
            <div key={idx} className="relative w-24 h-24 border border-slate-200 rounded-xl overflow-hidden bg-slate-50 shadow-sm">
              {/* eslint-disable-next-line @next/next/no-img-element */}
              <img src={getImageUrl(img)} alt={`img-${idx}`} className="w-full h-full object-cover" onError={(e) => (e.currentTarget.style.display = "none")} />
              <button
                type="button"
                onClick={() => setForm({ ...form, images: form.images.filter((_, i) => i !== idx) })}
                className="absolute top-1 right-1 bg-white/90 backdrop-blur rounded-full w-6 h-6 grid place-items-center text-xs text-red-600 border border-slate-200 shadow-sm hover:bg-white"
              >
                ✕
              </button>
            </div>
          ))}
        </div>

        <div className="flex gap-2 items-center flex-wrap">
          <label className="px-4 py-2 bg-white border border-slate-200 rounded-full text-sm font-medium cursor-pointer hover:bg-slate-50 transition shadow-sm">
            {uploading ? t("productForm.uploading") : t("productForm.uploadImage")}
            <input type="file" accept=".jpg,.jpeg,.png,.webp,.gif,.avif" multiple onChange={handleImageUpload} className="hidden" disabled={uploading} />
          </label>
          <span className="text-xs text-slate-500">{t("productForm.or")}</span>
          <div className="flex gap-1.5 flex-wrap">
            {testImages.map((name) => (
              <button
                key={name}
                type="button"
                onClick={() => addTestImage(name)}
                className="px-3 py-1.5 bg-slate-50 border border-slate-200 rounded-full text-xs font-medium text-slate-700 hover:bg-white hover:border-slate-300 transition shadow-sm"
              >
                + {name}
              </button>
            ))}
            {testImages.length === 0 && <span className="text-xs text-slate-400">{t("productForm.noTestImages")}</span>}
          </div>
        </div>

        <div className="mt-3">
          <label className="block text-xs font-medium text-slate-600">{t("productForm.pasteUrl")}</label>
          <div className="flex gap-2 mt-1">
            <input id="manualUrl" placeholder={t("productForm.pastePlaceholder")} className="flex-1 px-3.5 py-2.5 border border-slate-200 rounded-xl text-sm bg-slate-50 placeholder:text-slate-400 focus:bg-white focus:border-slate-300 focus:ring-4 focus:ring-slate-100 outline-none transition" />
            <button
              type="button"
              onClick={() => {
                const el = document.getElementById("manualUrl") as HTMLInputElement;
                if (el && el.value.trim()) {
                  setForm({ ...form, images: [...form.images, el.value.trim()] });
                  el.value = "";
                }
              }}
              className="px-4 py-2.5 bg-white border border-slate-200 rounded-full text-sm font-medium hover:bg-slate-50 transition shadow-sm"
            >
              {t("productForm.addUrl")}
            </button>
          </div>
        </div>
      </div>

      <div>
        <div className="flex items-center justify-between">
          <label className="block text-sm font-medium text-slate-700">{t("productForm.variants")}</label>
          <button type="button" onClick={addVariant} className="text-xs px-3 py-1.5 bg-white border border-slate-200 rounded-full font-medium hover:bg-slate-50 transition shadow-sm">
            {t("productForm.addVariant")}
          </button>
        </div>
        {form.variants.length === 0 ? (
          <p className="text-xs text-slate-500 mt-2 bg-slate-50 border border-slate-200 rounded-xl p-3">{t("productForm.noVariants")}</p>
        ) : (
          <div className="mt-2 space-y-2">
            {form.variants.map((v, idx) => (
              <div key={idx} className="grid grid-cols-12 gap-2 items-end border border-slate-200 p-3 rounded-xl bg-slate-50">
                <div className="col-span-3">
                  <label className="block text-xs font-medium text-slate-600">{t("productForm.sku")}</label>
                  <input
                    value={v.sku}
                    onChange={(e) => setForm((prev) => ({ ...prev, variants: prev.variants.map((x, i) => (i === idx ? { ...x, sku: e.target.value } : x)) }))}
                    className="w-full px-2.5 py-2 border border-slate-200 rounded-xl text-sm bg-white focus:border-slate-300 focus:ring-2 focus:ring-slate-100 outline-none"
                    required
                  />
                </div>
                <div className="col-span-3">
                  <label className="block text-xs font-medium text-slate-600">{t("productForm.optionName")}</label>
                  <input
                    value={v.option_name}
                    onChange={(e) => setForm((prev) => ({ ...prev, variants: prev.variants.map((x, i) => (i === idx ? { ...x, option_name: e.target.value } : x)) }))}
                    className="w-full px-2.5 py-2 border border-slate-200 rounded-xl text-sm bg-white focus:border-slate-300 focus:ring-2 focus:ring-slate-100 outline-none"
                    placeholder={t("productForm.optionNamePlaceholder")}
                  />
                </div>
                <div className="col-span-3">
                  <label className="block text-xs font-medium text-slate-600">{t("productForm.optionValue")}</label>
                  <input
                    value={v.option_value}
                    onChange={(e) => setForm((prev) => ({ ...prev, variants: prev.variants.map((x, i) => (i === idx ? { ...x, option_value: e.target.value } : x)) }))}
                    className="w-full px-2.5 py-2 border border-slate-200 rounded-xl text-sm bg-white focus:border-slate-300 focus:ring-2 focus:ring-slate-100 outline-none"
                    placeholder={t("productForm.optionValuePlaceholder")}
                  />
                </div>
                <div className="col-span-2">
                  <label className="block text-xs font-medium text-slate-600">{t("productForm.priceOverride")}</label>
                  <input
                    type="number"
                    step="0.01"
                    value={v.price_net_override ?? ""}
                    onChange={(e) =>
                      setForm((prev) => ({
                        ...prev,
                        variants: prev.variants.map((x, i) => (i === idx ? { ...x, price_net_override: e.target.value ? parseFloat(e.target.value) : null } : x)),
                      }))
                    }
                    className="w-full px-2.5 py-2 border border-slate-200 rounded-xl text-sm bg-white focus:border-slate-300 focus:ring-2 focus:ring-slate-100 outline-none"
                    placeholder={t("productForm.netPlaceholder")}
                  />
                </div>
                <div className="col-span-1">
                  <button
                    type="button"
                    onClick={() => setForm((prev) => ({ ...prev, variants: prev.variants.filter((_, i) => i !== idx) }))}
                    className="w-full px-2 py-2 bg-white text-red-600 border border-red-200 rounded-full text-xs font-medium hover:bg-red-50 transition"
                  >
                    ✕
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      <button type="submit" disabled={submitting} className="w-full px-4 py-3 bg-slate-900 text-white rounded-full hover:bg-slate-800 disabled:opacity-50 transition font-medium text-sm shadow">
        {submitting ? t("productForm.saving") : submitLabel}
      </button>
    </form>
  );
}
