"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/context/AuthContext";
import { api, CategoryTreeNode, CategoryRequest } from "@/lib/api";
import { CategoryTree, flattenTree } from "@/components/CategoryTree";

export default function AdminCategoriesPage() {
  const router = useRouter();
  const { isAuthenticated, isAdmin, loading, user, logout } = useAuth();

  const [tree, setTree] = useState<CategoryTreeNode[]>([]);
  const [requests, setRequests] = useState<CategoryRequest[]>([]);
  const [loadingData, setLoadingData] = useState(true);
  const [error, setError] = useState("");

  // create/edit form
  const [showForm, setShowForm] = useState(false);
  const [editingId, setEditingId] = useState<string | null>(null);
  const [formName, setFormName] = useState("");
  const [formSlug, setFormSlug] = useState("");
  const [formParent, setFormParent] = useState<string>("");
  const [formActive, setFormActive] = useState(true);
  const [formError, setFormError] = useState("");

  const [selectedId, setSelectedId] = useState<string | null>(null);

  const [actionLoading, setActionLoading] = useState<string | null>(null);

  useEffect(() => {
    if (!loading && (!isAuthenticated || !isAdmin)) router.push("/auth/login");
  }, [isAuthenticated, isAdmin, loading, router]);

  const fetchAll = async () => {
    setLoadingData(true);
    setError("");
    try {
      const [t, r] = await Promise.all([api.getCategoryTree(true), api.listCategoryRequests()]);
      setTree(t);
      setRequests(r);
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "Failed to load");
    } finally {
      setLoadingData(false);
    }
  };

  useEffect(() => {
    if (isAuthenticated && isAdmin) fetchAll();
  }, [isAuthenticated, isAdmin]);

  const flat = flattenTree(tree);

  const openCreate = (parentId?: string) => {
    setEditingId(null);
    setFormName("");
    setFormSlug("");
    setFormParent(parentId || "");
    setFormActive(true);
    setFormError("");
    setShowForm(true);
  };

  const openEdit = (node: CategoryTreeNode) => {
    setEditingId(node.id);
    setFormName(node.name);
    setFormSlug(node.slug);
    setFormParent(node.parent_id || "");
    setFormActive(node.is_active);
    setFormError("");
    setShowForm(true);
    setSelectedId(node.id);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setFormError("");
    try {
      if (editingId) {
        await api.updateCategory(editingId, {
          name: formName,
          slug: formSlug || undefined,
          parent_id: formParent || null,
          is_active: formActive,
        });
      } else {
        await api.createCategory({
          name: formName,
          slug: formSlug || undefined,
          parent_id: formParent || null,
          is_active: formActive,
        });
      }
      setShowForm(false);
      await fetchAll();
    } catch (err: unknown) {
      setFormError(err instanceof Error ? err.message : "Failed");
    }
  };

  const handleDelete = async (id: string) => {
    if (!confirm("Delete this category? This cannot be undone if it has no children/products.")) return;
    try {
      await api.deleteCategory(id);
      await fetchAll();
    } catch (err: unknown) {
      alert(err instanceof Error ? err.message : "Delete failed");
    }
  };

  const handleDecision = async (id: string, action: "approve" | "reject") => {
    let reason: string | undefined;
    if (action === "reject") {
      reason = prompt("Rejection reason:") || "";
      if (!reason.trim()) return;
    }
    setActionLoading(id);
    try {
      await api.decideCategoryRequest(id, action, reason);
      await fetchAll();
    } catch (err: unknown) {
      alert(err instanceof Error ? err.message : "Action failed");
    } finally {
      setActionLoading(null);
    }
  };

  if (loading || loadingData) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-slate-50">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-slate-900" />
      </div>
    );
  }
  if (!isAuthenticated || !isAdmin) return null;

  const pending = requests.filter((r) => r.status === "pending");
  const decided = requests.filter((r) => r.status !== "pending");

  return (
    <div className="min-h-screen bg-slate-50">
      <nav className="bg-white border-b border-slate-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between h-16 items-center">
            <div className="flex items-center gap-6">
              <h1 className="text-xl font-bold tracking-tight text-slate-900">Admin Panel</h1>
              <a href="/admin/dashboard" className="text-sm text-slate-500 hover:text-slate-700">
                Sellers
              </a>
              <span className="text-sm font-medium text-slate-900 border-b-2 border-slate-900 pb-1">Categories</span>
            </div>
            <div className="flex items-center gap-3 sm:gap-4">
              <span className="text-sm font-medium text-slate-700 hidden sm:inline">{user?.full_name}</span>
              <button onClick={logout} className="text-sm text-slate-500 hover:text-slate-700">
                Sign out
              </button>
            </div>
          </div>
        </div>
      </nav>

      <main className="max-w-7xl mx-auto py-8 px-4 sm:px-6 lg:px-8">
        {error && <div className="mb-4 bg-red-50 text-red-700 p-3 rounded-xl border border-red-200 text-sm">{error}</div>}

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          {/* Tree */}
          <div className="bg-white rounded-2xl shadow-sm border border-slate-200 p-6">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-lg font-semibold tracking-tight text-slate-900">Category Tree</h2>
              <button onClick={() => openCreate()} className="px-4 py-2 bg-slate-900 text-white text-sm font-medium rounded-full hover:bg-slate-800 shadow transition">
                + Top-level
              </button>
            </div>

            <div className="border border-slate-200 rounded-xl p-3 bg-slate-50 min-h-[300px] max-h-[600px] overflow-auto">
              <CategoryTree nodes={tree} onSelect={(n) => setSelectedId(n.id)} selectedId={selectedId} showInactive />
            </div>

            {selectedId && (
              <div className="mt-4 flex flex-wrap gap-2">
                {(() => {
                  const sel = flat.find((f) => f.id === selectedId)?.node;
                  if (!sel) return null;
                  return (
                    <>
                      <button onClick={() => openEdit(sel)} className="px-4 py-2 bg-white border border-slate-200 text-sm font-medium rounded-full hover:bg-slate-50 transition">
                        Edit
                      </button>
                      <button onClick={() => openCreate(sel.id)} className="px-4 py-2 bg-white border border-slate-200 text-sm font-medium rounded-full hover:bg-slate-50 transition">
                        + Subcategory
                      </button>
                      <button onClick={() => handleDelete(sel.id)} className="px-4 py-2 bg-white border border-red-200 text-red-700 text-sm font-medium rounded-full hover:bg-red-50 transition">
                        Delete
                      </button>
                    </>
                  );
                })()}
              </div>
            )}

            {showForm && (
              <form onSubmit={handleSubmit} className="mt-6 border-t border-slate-200 pt-4 space-y-3">
                <h3 className="font-semibold tracking-tight text-slate-900">{editingId ? "Edit category" : "New category"}</h3>
                {formError && <div className="bg-red-50 text-red-600 p-2 rounded-xl border border-red-200 text-sm">{formError}</div>}
                <div>
                  <label className="block text-sm font-medium text-slate-700">Name *</label>
                  <input
                    value={formName}
                    onChange={(e) => setFormName(e.target.value)}
                    required
                    className="mt-1 w-full px-3 py-2.5 bg-slate-50 border border-slate-200 rounded-xl text-sm placeholder:text-slate-400 focus:bg-white focus:border-slate-300 focus:ring-4 focus:ring-slate-100 outline-none transition"
                    placeholder="e.g. Electronics"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-slate-700">Slug (auto if blank)</label>
                  <input
                    value={formSlug}
                    onChange={(e) => setFormSlug(e.target.value)}
                    className="mt-1 w-full px-3 py-2.5 bg-slate-50 border border-slate-200 rounded-xl text-sm placeholder:text-slate-400 focus:bg-white focus:border-slate-300 focus:ring-4 focus:ring-slate-100 outline-none transition"
                    placeholder="electronics"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-slate-700">Parent</label>
                  <select
                    value={formParent}
                    onChange={(e) => setFormParent(e.target.value)}
                    className="mt-1 w-full px-3 py-2.5 bg-slate-50 border border-slate-200 rounded-xl text-sm focus:bg-white focus:border-slate-300 focus:ring-4 focus:ring-slate-100 outline-none transition"
                  >
                    <option value="">— Top-level —</option>
                    {flat.map((f) => (
                      <option key={f.id} value={f.id} disabled={editingId === f.id}>
                        {"—".repeat(f.depth)} {f.name} (/{f.slug})
                      </option>
                    ))}
                  </select>
                </div>
                <label className="flex items-center gap-2 text-sm text-slate-700">
                  <input type="checkbox" checked={formActive} onChange={(e) => setFormActive(e.target.checked)} className="rounded border-slate-300" />
                  Active
                </label>
                <div className="flex gap-2">
                  <button type="submit" className="px-5 py-2.5 bg-slate-900 text-white text-sm font-medium rounded-full hover:bg-slate-800 shadow transition">
                    {editingId ? "Save" : "Create"}
                  </button>
                  <button type="button" onClick={() => setShowForm(false)} className="px-5 py-2.5 bg-white border border-slate-200 text-sm font-medium rounded-full hover:bg-slate-50 transition">
                    Cancel
                  </button>
                </div>
              </form>
            )}
          </div>

          {/* Requests */}
          <div className="space-y-6">
            <div className="bg-white rounded-2xl shadow-sm border border-slate-200 p-6">
              <h2 className="text-lg font-semibold tracking-tight text-slate-900 mb-1">Pending Category Requests</h2>
              <p className="text-sm text-slate-500 mb-4">Sellers request new categories/subcategories; approve to add to tree.</p>
              {pending.length === 0 ? (
                <p className="text-sm text-slate-500 bg-slate-50 p-4 rounded-xl border border-slate-200">No pending requests.</p>
              ) : (
                <div className="space-y-3">
                  {pending.map((r) => (
                    <div key={r.id} className="border border-slate-200 rounded-2xl p-4 bg-white">
                      <div className="flex justify-between gap-3">
                        <div>
                          <p className="font-medium text-slate-900">
                            {r.name} <span className="text-slate-500 font-normal">/{r.slug}</span>
                          </p>
                          <p className="text-xs text-slate-600">
                            by {r.requester_email} {r.parent_name ? `→ under ${r.parent_name}` : "(top-level)"}
                          </p>
                          {r.description && <p className="text-sm text-slate-700 mt-1">{r.description}</p>}
                          <p className="text-xs text-slate-400 mt-1">{new Date(r.created_at).toLocaleString()}</p>
                        </div>
                        <span className="h-fit px-2.5 py-0.5 bg-amber-50 text-amber-700 border border-amber-200 text-xs font-medium rounded-full">pending</span>
                      </div>
                      <div className="mt-3 flex gap-2">
                        <button
                          onClick={() => handleDecision(r.id, "approve")}
                          disabled={actionLoading === r.id}
                          className="px-4 py-1.5 bg-slate-900 text-white text-xs font-medium rounded-full hover:bg-slate-800 disabled:opacity-50 shadow transition"
                        >
                          Approve
                        </button>
                        <button
                          onClick={() => handleDecision(r.id, "reject")}
                          disabled={actionLoading === r.id}
                          className="px-4 py-1.5 bg-white border border-slate-200 text-slate-700 text-xs font-medium rounded-full hover:bg-slate-50 disabled:opacity-50 transition"
                        >
                          Reject
                        </button>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>

            {decided.length > 0 && (
              <div className="bg-white rounded-2xl shadow-sm border border-slate-200 p-6">
                <h3 className="font-semibold tracking-tight text-slate-900 mb-3">Recent decisions</h3>
                <div className="space-y-2 max-h-64 overflow-auto">
                  {decided.slice(0, 10).map((r) => (
                    <div key={r.id} className="flex justify-between items-center text-sm border-b border-slate-100 py-2 last:border-0">
                      <span className="text-slate-700">
                        {r.name} <span className="text-slate-500">/{r.slug}</span> —{" "}
                        <span className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium border ${r.status === "approved" ? "bg-emerald-50 text-emerald-700 border-emerald-200" : "bg-red-50 text-red-700 border-red-200"}`}>{r.status}</span>
                      </span>
                      <span className="text-xs text-slate-500 ml-2 truncate">{r.requester_email}</span>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>
      </main>
    </div>
  );
}
