"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/context/AuthContext";
import { api, SellerListResponse, SellerProfile } from "@/lib/api";

export default function AdminDashboardPage() {
  const router = useRouter();
  const { user, isAuthenticated, isAdmin, loading, logout } = useAuth();
  const [pendingSellers, setPendingSellers] = useState<SellerListResponse[]>([]);
  const [loadingSellers, setLoadingSellers] = useState(true);
  const [actionLoading, setActionLoading] = useState<string | null>(null);

  useEffect(() => {
    if (!loading && (!isAuthenticated || !isAdmin)) {
      router.push("/auth/login");
    }
  }, [isAuthenticated, isAdmin, loading]);

  useEffect(() => {
    if (isAuthenticated && isAdmin) {
      fetchPendingSellers();
    }
  }, [isAuthenticated, isAdmin]);

  const fetchPendingSellers = async () => {
    try {
      const sellers = await api.getPendingSellers();
      setPendingSellers(sellers);
    } catch (err) {
      console.error("Failed to fetch pending sellers:", err);
    } finally {
      setLoadingSellers(false);
    }
  };

  const handleApprove = async (sellerId: string) => {
    setActionLoading(sellerId);
    try {
      await api.approveSeller(sellerId, "approved");
      await fetchPendingSellers();
    } catch (err) {
      alert("Failed to approve seller: " + (err instanceof Error ? err.message : "Unknown error"));
    } finally {
      setActionLoading(null);
    }
  };

  const handleReject = async (sellerId: string) => {
    const reason = prompt("Please provide a rejection reason:");
    if (!reason) return;
    setActionLoading(sellerId);
    try {
      await api.approveSeller(sellerId, "rejected", reason);
      await fetchPendingSellers();
    } catch (err) {
      alert("Failed to reject seller: " + (err instanceof Error ? err.message : "Unknown error"));
    } finally {
      setActionLoading(null);
    }
  };

  if (loading || loadingSellers) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-slate-50">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-slate-900"></div>
      </div>
    );
  }

  if (!isAuthenticated || !isAdmin) {
    return null;
  }

  const statusColors: Record<string, string> = {
    pending: "bg-amber-50 text-amber-700 border border-amber-200",
    approved: "bg-emerald-50 text-emerald-700 border border-emerald-200",
    rejected: "bg-red-50 text-red-700 border border-red-200",
  };

  return (
    <div className="min-h-screen bg-slate-50">
      <nav className="bg-white border-b border-slate-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between h-16 items-center">
            <div className="flex items-center gap-6">
              <h1 className="text-xl font-bold tracking-tight text-slate-900">Admin Panel</h1>
              <span className="hidden sm:inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-slate-900 text-white">
                Seller approvals
              </span>
            </div>
            <div className="flex items-center gap-3 sm:gap-4">
              <span className="text-sm font-medium text-slate-700 hidden sm:inline">{user?.full_name}</span>
              <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-purple-50 text-purple-700 border border-purple-200">
                Admin
              </span>
              <button onClick={logout} className="text-sm text-slate-500 hover:text-slate-700">
                Sign out
              </button>
            </div>
          </div>
        </div>
      </nav>

      <main className="max-w-7xl mx-auto py-8 sm:py-12 px-4 sm:px-6 lg:px-8">
        <div className="mb-8 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div>
            <h2 className="text-3xl font-bold tracking-tight text-slate-900">Seller Approvals</h2>
            <p className="mt-2 text-slate-600 text-sm sm:text-base">Review and approve/reject pending seller applications</p>
          </div>
          <a href="/admin/categories" className="inline-flex items-center justify-center px-5 py-2.5 bg-slate-900 text-white text-sm font-medium rounded-full hover:bg-slate-800 shadow transition">
            Manage Categories →
          </a>
        </div>

        {pendingSellers.length === 0 ? (
          <div className="bg-white rounded-2xl shadow-sm border border-slate-200 p-12 text-center">
            <div className="mx-auto w-12 h-12 rounded-full bg-slate-50 border border-slate-200 grid place-items-center">
              <svg className="h-6 w-6 text-slate-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
            </div>
            <h3 className="mt-4 text-sm font-semibold text-slate-900">No pending sellers</h3>
            <p className="mt-1 text-sm text-slate-500">All seller applications have been reviewed.</p>
          </div>
        ) : (
          <div className="bg-white shadow-sm border border-slate-200 rounded-2xl overflow-hidden">
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-slate-200">
                <thead className="bg-slate-50">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium text-slate-500 uppercase tracking-wider">Business Name</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-slate-500 uppercase tracking-wider">Applicant</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-slate-500 uppercase tracking-wider">Email</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-slate-500 uppercase tracking-wider">Applied</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-slate-500 uppercase tracking-wider">Status</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-slate-500 uppercase tracking-wider">Actions</th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-slate-200">
                  {pendingSellers.map((seller) => (
                    <tr key={seller.id} className="hover:bg-slate-50">
                      <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-slate-900">{seller.business_name}</td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-slate-900">{seller.full_name}</td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-slate-500">{seller.email}</td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-slate-500">{new Date(seller.created_at).toLocaleDateString()}</td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${statusColors[seller.status] ?? "bg-slate-50 text-slate-700 border border-slate-200"}`}>
                          {seller.status.charAt(0).toUpperCase() + seller.status.slice(1)}
                        </span>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                        {seller.status === "pending" && (
                          <div className="flex items-center gap-2">
                            <button
                              onClick={() => handleApprove(seller.id)}
                              disabled={actionLoading === seller.id}
                              className="inline-flex items-center px-3 py-1.5 bg-slate-900 text-white text-xs font-medium rounded-full hover:bg-slate-800 disabled:opacity-50 transition"
                            >
                              {actionLoading === seller.id ? "Approving..." : "Approve"}
                            </button>
                            <button
                              onClick={() => handleReject(seller.id)}
                              disabled={actionLoading === seller.id}
                              className="inline-flex items-center px-3 py-1.5 bg-white border border-slate-200 text-slate-700 text-xs font-medium rounded-full hover:bg-slate-50 disabled:opacity-50 transition"
                            >
                              {actionLoading === seller.id ? "Rejecting..." : "Reject"}
                            </button>
                          </div>
                        )}
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
