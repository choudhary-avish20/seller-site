"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";
import { api, Category, CategoryTreeNode, ProductListItem } from "@/lib/api";
import { Header } from "@/components/Header";
import { CategorySidebar } from "@/components/CategorySidebar";
import { ProductGrid } from "@/components/ProductCard";
import { useLanguage } from "@/context/LanguageContext";

export default function CategoryBrowsePage() {
  const params = useParams();
  const slug = params.slug as string;
  const { t } = useLanguage();
  const [tree, setTree] = useState<CategoryTreeNode[]>([]);
  const [category, setCategory] = useState<Category | null>(null);
  const [ancestors, setAncestors] = useState<Category[]>([]);
  const [products, setProducts] = useState<ProductListItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    async function load() {
      setLoading(true);
      setError("");
      try {
        const [t, pathRes] = await Promise.all([
          api.getCategoryTree(false),
          api.getCategoryByPath(slug).catch(() => api.getCategoryBySlug(slug).then((c) => ({ category: c, ancestors: [] as Category[], path: c.slug }))),
        ]);
        const cat = (pathRes as { category: Category }).category;
        const anc = (pathRes as { ancestors: Category[] }).ancestors || [];
        setTree(t);
        setCategory(cat);
        setAncestors(anc);
        const findNode = (nodes: CategoryTreeNode[], target: string): CategoryTreeNode | null => {
          for (const n of nodes) {
            if (n.slug === target) return n;
            const child = findNode(n.children, target);
            if (child) return child;
          }
          return null;
        };
        const node = findNode(t, cat.slug);
        const ids: string[] = [];
        const collect = (n: CategoryTreeNode) => {
          ids.push(n.id);
          n.children.forEach(collect);
        };
        if (node) collect(node);
        else ids.push(cat.id);

        const all = await api.listProducts({ limit: 100 });
        const filtered = all.filter((p) => ids.includes(p.category_id));
        setProducts(filtered);
      } catch (e: unknown) {
        setError(e instanceof Error ? e.message : "Failed to load category");
      } finally {
        setLoading(false);
      }
    }
    load();
  }, [slug]);

  if (loading) {
    return (
      <div className="min-h-screen bg-slate-50">
        <Header />
        <div className="max-w-7xl mx-auto px-4 py-12 flex items-center justify-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-slate-900" />
        </div>
      </div>
    );
  }

  if (error || !category) {
    return (
      <div className="min-h-screen bg-slate-50">
        <Header categories={tree} />
        <div className="max-w-7xl mx-auto px-4 py-12 text-center">
          <div className="inline-flex flex-col items-center gap-3 bg-white rounded-2xl border border-slate-200 shadow-sm p-8">
            <p className="text-red-600 text-sm">{error || t("categories.slug.categoryNotFound")}</p>
            <Link href="/categories" className="inline-flex px-5 py-2 bg-slate-900 text-white rounded-full text-sm font-medium hover:bg-slate-800 transition">
              {t("categories.slug.allCategories")}
            </Link>
          </div>
        </div>
      </div>
    );
  }

  const activeNodeInTree = (() => {
    const find = (nodes: CategoryTreeNode[], s: string): CategoryTreeNode | null => {
      for (const n of nodes) if (n.slug === s) return n;
      for (const n of nodes) {
        const r = find(n.children, s);
        if (r) return r;
      }
      return null;
    };
    return find(tree, category.slug);
  })();

  return (
    <div className="min-h-screen bg-slate-50">
      <Header categories={tree} />
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="text-sm text-slate-500 mb-4 flex flex-wrap items-center gap-1">
          <Link href="/categories" className="hover:text-slate-700 hover:underline underline-offset-4">
            {t("categories.slug.breadcrumbCategories")}
          </Link>
          {ancestors.map((a) => (
            <span key={a.id} className="inline-flex items-center gap-1">
              <span className="text-slate-300">/</span>
              <Link href={`/categories/${a.slug}`} className="hover:text-slate-700">
                {a.name}
              </Link>
            </span>
          ))}
          <span className="text-slate-300">/</span>
          <span className="text-slate-900 font-medium">{category.name}</span>
        </div>

        <div className="flex gap-6 flex-col md:flex-row">
          <CategorySidebar tree={tree} activeSlug={category.slug} />

          <main className="flex-1 min-w-0">
            <div className="flex items-start justify-between gap-4">
              <div>
                <h1 className="text-2xl font-bold tracking-tight text-slate-900">{category.name}</h1>
                <p className="text-sm text-slate-500">{t("categories.slug.packPricing")}</p>
              </div>
              <span className="inline-flex items-center px-3 py-1.5 bg-white border border-slate-200 rounded-full text-xs font-medium text-slate-700 shadow-sm shrink-0">
                {products.length} {t("categories.slug.productsCount")}
              </span>
            </div>

            {activeNodeInTree && activeNodeInTree.children.length > 0 && (
              <div className="mt-4 flex flex-wrap gap-2">
                {activeNodeInTree.children.map((sub) => (
                  <Link
                    key={sub.id}
                    href={`/categories/${sub.slug}`}
                    className="px-3.5 py-1.5 bg-white border border-slate-200 rounded-full text-sm font-medium text-slate-700 hover:border-slate-300 hover:bg-slate-50 hover:text-slate-900 transition shadow-sm"
                  >
                    {sub.name}
                  </Link>
                ))}
              </div>
            )}

            <div className="mt-6">
              <ProductGrid products={products} />
              {products.length === 0 && (
                <p className="text-sm text-slate-500 bg-white p-8 rounded-2xl border border-slate-200 shadow-sm text-center mt-4">
                  {t("categories.slug.noProducts")}
                </p>
              )}
            </div>
          </main>
        </div>
      </div>
    </div>
  );
}
