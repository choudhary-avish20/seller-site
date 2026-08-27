"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/context/AuthContext";
import { api, CategoryTreeNode, CategoryRequest } from "@/lib/api";
import { CategoryTree, flattenTree } from "@/components/CategoryTree";

export default function SellerCategoriesPage() {
  const router = useRouter();
  const { isAuthenticated, isSeller, loading, user, logout } = useAuth();
  const [tree, setTree] = useState<CategoryTreeNode[]>([]);
  const [myRequests, setMyRequests] = useState<CategoryRequest[]>([]);
  const [loadingData, setLoadingData] = useState(true);
  const [error, setError] = useState("");

  // request form
  const [name, setName] = useState("");
  const [slug, setSlug] = useState("");
  const [parentId, setParentId] = useState("");
  const [description, setDescription] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [formError, setFormError] = useState("");
  const [formSuccess, setFormSuccess] = useState("");

  useEffect(() => {
    if (!loading && (!isAuthenticated || !isSeller)) router.push("/auth/login");
  }, [isAuthenticated, isSeller, loading, router]);

  const fetchAll = async () => {
    setLoadingData(true);
    try {
      const [t, reqs] = await Promise.all([api.getCategoryTree(false), api.listCategoryRequests({ mine: true })]);
      setTree(t);
      setMyRequests(reqs);
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "Failed to load");
    } finally {
      setLoadingData(false);
    }
  };

  useEffect(() => {
    if (isAuthenticated && isSeller) fetchAll();
  }, [isAuthenticated, isSeller]);

  const handleRequest = async (e: React.FormEvent) => {
    e.preventDefault();
    setFormError("");
    setFormSuccess("");
    if (!name.trim()) {
      setFormError("Name is required");
      return;
    }
    setSubmitting(true);
    try {
      const res = await api.createCategoryRequest({
        name: name.trim(),
        parent_id: parentId || null,
        description: description.trim() || undefined,
        slug: slug.trim() || undefined,
      });
      setFormSuccess(`Request submitted for "${res.name}" — pending admin approval.`);
      setName("");
      setSlug("");
      setParentId("");
      setDescription("");
      await fetchAll();
    } catch (err: unknown) {
      setFormError(err instanceof Error ? err.message : "Request failed");
    } finally {
      setSubmitting(false);
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

  const flat = flattenTree(tree);

  return (
    <div className="min-h-screen bg-slate-50">
      <nav className="bg-white border-b border-slate-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between h-16 items-center">
            <div className="flex items-center gap-6">
              <h1 className="text-xl font-bold tracking-tight text-slate-900">Seller Panel</h1>
              <a href="/seller/dashboard" className="text-sm text-slate-500 hover:text-slate-900 transition">
                Dashboard
              </a>
              <span className="text-sm font-semibold text-slate-900 border-b-2 border-slate-900 pb-1 -mb-1">Categories</span>
              <a href="/seller/products" className="text-sm text-slate-500 hover:text-slate-900 transition hidden sm:inline">
                Products
              </a>
            </div>
            <div className="flex items-center gap-4">
              <span className="text-sm font-medium text-slate-700 hidden sm:inline">{user?.full_name}</span>
              <button onClick={logout} className="text-sm text-slate-500 hover:text-slate-700">
                Sign out
              </button>
            </div>
          </div>
        </div>
      </nav>

      <main className="max-w-7xl mx-auto py-8 px-4 sm:px-6 lg:px-8">
        {error && <div className="mb-4 bg-red-50 border border-red-200 text-red-700 p-3 rounded-2xl text-sm">{error}</div>}

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          <div className="bg-white rounded-2xl border border-slate-200 shadow-sm p-6">
            <h2 className="text-lg font-semibold tracking-tight text-slate-900">Available Categories</h2>
            <p className="text-sm text-slate-600 mb-4">Taxonomy is centrally controlled. Pick from the tree when listing products; request additions if needed.</p>
            <div className="border border-slate-200 rounded-xl p-4 bg-slate-50 min-h-[300px] max-h-[600px] overflow-auto">
              <CategoryTree nodes={tree} />
            </div>
            <div className="mt-3 text-xs text-slate-500">
              {flat.length} categories total • inactive hidden
            </div>
          </div>

          <div className="space-y-6">
            <div className="bg-white rounded-2xl border border-slate-200 shadow-sm p-6">
              <h2 className="text-lg font-semibold tracking-tight text-slate-900">Request New Category</h2>
              <p className="text-sm text-slate-600 mb-4">Propose a new top-level category or subcategory. Admin will review.</p>

              <form onSubmit={handleRequest} className="space-y-4">
                {formError && <div className="bg-red-50 border border-red-200 text-red-700 p-3 rounded-xl text-sm">{formError}</div>}
                {formSuccess && <div className="bg-emerald-50 border border-emerald-200 text-emerald-700 p-3 rounded-xl text-sm">{formSuccess}</div>}

                <div>
                  <label className="block text-sm font-medium text-slate-700">Name *</label>
                  <input
                    value={name}
                    onChange={(e) => setName(e.target.value)}
                    className="mt-1 w-full px-3 py-2.5 bg-slate-50 border border-slate-200 rounded-xl text-sm text-slate-900 placeholder:text-slate-400 focus:outline-none focus:ring-2 focus:ring-slate-900/10 focus:border-slate-300 transition"
                    placeholder="e.g. Garden Tools"
                    required
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-slate-700">Slug (optional, auto from name)</label>
                  <input
                    value={slug}
                    onChange={(e) => setSlug(e.target.value)}
                    className="mt-1 w-full px-3 py-2.5 bg-slate-50 border border-slate-200 rounded-xl text-sm text-slate-900 placeholder:text-slate-400 focus:outline-none focus:ring-2 focus:ring-slate-900/10 focus:border-slate-300 transition"
                    placeholder="garden-tools"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-slate-700">Parent category (leave empty for top-level)</label>
                  <select
                    value={parentId}
                    onChange={(e) => setParentId(e.target.value)}
                    className="mt-1 w-full px-3 py-2.5 bg-slate-50 border border-slate-200 rounded-xl text-sm text-slate-900 focus:outline-none focus:ring-2 focus:ring-slate-900/10 focus:border-slate-300 transition"
                  >
                    <option value="">— Top-level —</option>
                    {flat.map((f) => (
                      <option key={f.id} value={f.id}>
                        {"—".repeat(f.depth)} {f.name} (/{f.slug})
                      </option>
                    ))}
                  </select>
                </div>
                <div>
                  <label className="block text-sm font-medium text-slate-700">Reason / description</label>
                  <textarea
                    value={description}
                    onChange={(e) => setDescription(e.target.value)}
                    rows={3}
                    className="mt-1 w-full px-3 py-2.5 bg-slate-50 border border-slate-200 rounded-xl text-sm text-slate-900 placeholder:text-slate-400 focus:outline-none focus:ring-2 focus:ring-slate-900/10 focus:border-slate-300 transition"
                    placeholder="Why is this category needed?"
                  />
                </div>
                <button
                  type="submit"
                  disabled={submitting}
                  className="w-full px-5 py-2.5 bg-slate-900 text-white text-sm font-medium rounded-full hover:bg-slate-800 disabled:opacity-50 transition"
                >
                  {submitting ? "Submitting..." : "Submit request"}
                </button>
              </form>
            </div>

            <div className="bg-white rounded-2xl border border-slate-200 shadow-sm p-6">
              <h3 className="font-semibold tracking-tight text-slate-900 mb-3">My Requests</h3>
              {myRequests.length === 0 ? (
                <p className="text-sm text-slate-500 bg-slate-50 border border-slate-200 rounded-xl p-4 text-center">No requests yet.</p>
              ) : (
                <div className="space-y-3 max-h-96 overflow-auto pr-1">
                  {myRequests.map((r) => (
                    <div key={r.id} className="border border-slate-200 rounded-xl p-3 bg-white hover:bg-slate-50 transition">
                      <div className="flex justify-between items-start gap-3">
                        <div className="min-w-0">
                          <p className="text-sm font-medium text-slate-900">
                            {r.name} <span className="text-slate-500 font-normal">/{r.slug}</span>
                          </p>
                          <p className="text-xs text-slate-500">
                            {r.parent_name ? `Under ${r.parent_name}` : "Top-level"} • {new Date(r.created_at).toLocaleDateString()}
                          </p>
                          {r.description && <p className="text-xs text-slate-700 mt-1">{r.description}</p>}
                          {r.rejection_reason && <p className="text-xs text-red-600 mt-1">Rejected: {r.rejection_reason}</p>}
                        </div>
                        <span
                          className={`shrink-0 px-2.5 py-1 text-xs rounded-full font-medium border ${r.status === "pending" ? "bg-amber-50 text-amber-700 border-amber-200" : r.status === "approved" ? "bg-emerald-50 text-emerald-700 border-emerald-200" : "bg-red-50 text-red-700 border-red-200"}`}
                        >
                          {r.status}
                        </span>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}
