"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { useAuth } from "@/context/AuthContext";
import { api, SellerProfile } from "@/lib/api";
import { useLanguage } from "@/context/LanguageContext";
import { LanguageToggle } from "@/components/LanguageToggle";

export default function SellerPendingPage() {
  const router = useRouter();
  const { user, isAuthenticated, isSeller, refreshUser } = useAuth();
  const { t } = useLanguage();
  const [sellerProfile, setSellerProfile] = useState<SellerProfile | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!isAuthenticated || !isSeller) {
      router.push("/auth/login");
      return;
    }
    fetchProfile();
  }, [isAuthenticated, isSeller]);

  const fetchProfile = async () => {
    try {
      const profile = await api.getMySellerProfile();
      setSellerProfile(profile);
    } catch {
      // Profile not found or error
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-slate-50">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-slate-900"></div>
      </div>
    );
  }

  if (!sellerProfile) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-slate-50 py-12 px-4">
        <div className="absolute top-4 right-4">
          <LanguageToggle />
        </div>
        <div className="max-w-md w-full text-center bg-white rounded-2xl border border-slate-200 shadow-sm p-8">
          <h2 className="text-2xl font-bold tracking-tight text-slate-900 mb-2">{t("seller.pending.notFound")}</h2>
          <p className="text-sm text-slate-600 mb-6">{t("seller.pending.notFoundDesc")}</p>
          <Link
            href="/auth/register-seller"
            className="inline-flex px-5 py-2.5 bg-slate-900 text-white rounded-full text-sm font-medium hover:bg-slate-800 transition"
          >
            {t("seller.pending.registerSeller")}
          </Link>
        </div>
      </div>
    );
  }

  const statusColors = {
    pending: "bg-amber-50 text-amber-700 border-amber-200",
    approved: "bg-emerald-50 text-emerald-700 border-emerald-200",
    rejected: "bg-red-50 text-red-700 border-red-200",
  };

  const statusIcons = {
    pending: (
      <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
      </svg>
    ),
    approved: (
      <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
      </svg>
    ),
    rejected: (
      <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
      </svg>
    ),
  };

  const statusLabelMap: Record<string, string> = {
    pending: t("seller.pending.statusPending"),
    approved: t("seller.pending.statusApproved"),
    rejected: t("seller.pending.statusRejected"),
  };

  return (
    <div className="min-h-screen bg-slate-50 py-12 px-4 sm:px-6 lg:px-8">
      <div className="flex justify-end max-w-3xl mx-auto mb-4">
        <LanguageToggle />
      </div>
      <div className="max-w-3xl mx-auto">
        <div className="bg-white rounded-2xl shadow-sm border border-slate-200 p-8">
          <div className="flex items-center justify-between mb-6">
            <h1 className="text-2xl font-bold tracking-tight text-slate-900">{t("seller.pending.statusTitle")}</h1>
            <span className={`inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-medium border ${statusColors[sellerProfile.status]}`}>
              {statusIcons[sellerProfile.status]}
              <span className="capitalize">{statusLabelMap[sellerProfile.status] || sellerProfile.status}</span>
            </span>
          </div>

          <div className="space-y-6">
            <div className="border-t border-slate-200 pt-6">
              <h2 className="text-base font-semibold tracking-tight text-slate-900 mb-4">{t("seller.pending.businessInfo")}</h2>
              <dl className="grid grid-cols-1 gap-x-4 gap-y-6 sm:grid-cols-2">
                <div>
                  <dt className="text-sm font-medium text-slate-500">{t("seller.pending.businessName")}</dt>
                  <dd className="mt-1 text-sm font-medium text-slate-900">{sellerProfile.business_name}</dd>
                </div>
                {sellerProfile.tax_id && (
                  <div>
                    <dt className="text-sm font-medium text-slate-500">{t("seller.pending.taxId")}</dt>
                    <dd className="mt-1 text-sm text-slate-900">{sellerProfile.tax_id}</dd>
                  </div>
                )}
                {sellerProfile.phone && (
                  <div>
                    <dt className="text-sm font-medium text-slate-500">{t("seller.pending.phone")}</dt>
                    <dd className="mt-1 text-sm text-slate-900">{sellerProfile.phone}</dd>
                  </div>
                )}
                {sellerProfile.business_address && (
                  <div className="sm:col-span-2">
                    <dt className="text-sm font-medium text-slate-500">{t("seller.pending.businessAddress")}</dt>
                    <dd className="mt-1 text-sm text-slate-900">{sellerProfile.business_address}</dd>
                  </div>
                )}
              </dl>
            </div>

            {sellerProfile.status === "rejected" && sellerProfile.rejection_reason && (
              <div className="bg-red-50 border border-red-200 rounded-2xl p-4">
                <h3 className="text-sm font-medium text-red-800 mb-1">{t("seller.pending.rejectionReason")}</h3>
                <p className="text-sm text-red-700">{sellerProfile.rejection_reason}</p>
              </div>
            )}

            <div className="border-t border-slate-200 pt-6">
              <h2 className="text-base font-semibold tracking-tight text-slate-900 mb-4">{t("seller.pending.nextSteps")}</h2>
              {sellerProfile.status === "pending" && (
                <div className="text-sm text-slate-600 space-y-2">
                  <p>{t("seller.pending.pendingReview")}</p>
                  <p>{t("seller.pending.notify")}</p>
                  <p className="text-indigo-600 font-medium">{t("seller.pending.reviewTime")}</p>
                </div>
              )}
              {sellerProfile.status === "approved" && (
                <div className="text-sm text-slate-600 space-y-2">
                  <p className="text-emerald-600 font-medium">{t("seller.pending.approvedTitle")}</p>
                  <p>{t("seller.pending.approvedDesc")}</p>
                  <Link
                    href="/seller/dashboard"
                    className="inline-flex mt-4 px-5 py-2.5 bg-slate-900 text-white rounded-full hover:bg-slate-800 text-sm font-medium transition"
                  >
                    {t("seller.pending.goDashboard")}
                  </Link>
                </div>
              )}
              {sellerProfile.status === "rejected" && (
                <div className="text-sm text-slate-600 space-y-2">
                  <p>{t("seller.pending.rejectedDesc1")}</p>
                  <p>{t("seller.pending.rejectedDesc2")}</p>
                  <Link
                    href="/auth/register-seller"
                    className="inline-flex mt-4 px-5 py-2.5 bg-slate-900 text-white rounded-full hover:bg-slate-800 text-sm font-medium transition"
                  >
                    {t("seller.pending.submitNew")}
                  </Link>
                </div>
              )}
            </div>
          </div>
        </div>

        <div className="mt-6 text-center">
          <Link href="/" className="text-sm font-medium text-slate-600 hover:text-slate-900">
            {t("seller.pending.backHome")}
          </Link>
        </div>
      </div>
    </div>
  );
}
