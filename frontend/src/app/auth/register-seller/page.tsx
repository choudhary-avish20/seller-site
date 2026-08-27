"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { useAuth } from "@/context/AuthContext";
import { useLanguage } from "@/context/LanguageContext";
import { LanguageToggle } from "@/components/LanguageToggle";

export default function RegisterSellerPage() {
  const router = useRouter();
  const { registerSeller, isAuthenticated } = useAuth();
  const { t } = useLanguage();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [fullName, setFullName] = useState("");
  const [businessName, setBusinessName] = useState("");
  const [taxId, setTaxId] = useState("");
  const [businessAddress, setBusinessAddress] = useState("");
  const [phone, setPhone] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  if (isAuthenticated) {
    return null;
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    if (password !== confirmPassword) {
      setError(t("auth.registerSeller.errorMismatch"));
      return;
    }
    if (password.length < 8) {
      setError(t("auth.registerSeller.errorLength"));
      return;
    }
    if (!businessName.trim()) {
      setError(t("auth.registerSeller.errorBusinessName"));
      return;
    }
    setLoading(true);
    try {
      await registerSeller({
        email,
        password,
        full_name: fullName,
        seller_profile: {
          business_name: businessName,
          tax_id: taxId || undefined,
          business_address: businessAddress || undefined,
          phone: phone || undefined,
        },
      });
      router.push("/seller/pending");
      router.refresh();
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Registration failed");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-slate-50 flex flex-col items-center justify-center py-12 px-4 sm:px-6 lg:px-8 relative">
      <div className="absolute top-4 right-4">
        <LanguageToggle />
      </div>
      <div className="max-w-2xl w-full">
        <Link href="/" className="flex items-center justify-center gap-3 mb-8">
          <div className="w-10 h-10 rounded-xl bg-indigo-600 flex items-center justify-center text-white font-bold text-lg">W</div>
          <div className="text-left leading-none">
            <div className="font-bold tracking-tight text-slate-900">WHOLESALE</div>
            <div className="text-[10px] tracking-[0.14em] text-slate-500 font-medium">CENTRUM • WÓLKA • B2B</div>
          </div>
        </Link>

        <div className="bg-white rounded-2xl border border-slate-200 shadow-sm p-8">
          <div className="text-center mb-8">
            <h2 className="text-2xl font-bold tracking-tight text-slate-900">
              {t("auth.registerSeller.title")}
            </h2>
            <p className="mt-2 text-sm text-slate-500">
              {t("auth.registerSeller.alreadyHave")}{" "}
              <Link href="/auth/login" className="font-medium text-indigo-600 hover:text-indigo-500">
                {t("auth.registerSeller.signIn")}
              </Link>
            </p>
          </div>

          <form className="space-y-6" onSubmit={handleSubmit}>
            {error && (
              <div className="bg-red-50 text-red-600 border border-red-200 p-4 rounded-xl text-sm">
                {error}
              </div>
            )}

            <div className="bg-slate-50 p-6 rounded-xl border border-slate-200">
              <h3 className="text-sm font-semibold tracking-wide text-slate-900 mb-4">{t("auth.registerSeller.accountInfo")}</h3>
              <div className="space-y-4">
                <div>
                  <label htmlFor="full_name" className="block text-sm font-medium text-slate-700 mb-1.5">
                    {t("auth.registerSeller.fullName")}
                  </label>
                  <input
                    id="full_name"
                    type="text"
                    autoComplete="name"
                    required
                    value={fullName}
                    onChange={(e) => setFullName(e.target.value)}
                    className="block w-full bg-white border border-slate-200 rounded-xl px-4 py-3 text-sm placeholder:text-slate-400 text-slate-900 focus:outline-none focus:border-indigo-300 focus:ring-4 focus:ring-indigo-100 transition"
                    placeholder={t("auth.registerSeller.fullNamePlaceholder")}
                  />
                </div>
                <div>
                  <label htmlFor="email" className="block text-sm font-medium text-slate-700 mb-1.5">
                    {t("auth.registerSeller.email")}
                  </label>
                  <input
                    id="email"
                    type="email"
                    autoComplete="email"
                    required
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    className="block w-full bg-white border border-slate-200 rounded-xl px-4 py-3 text-sm placeholder:text-slate-400 text-slate-900 focus:outline-none focus:border-indigo-300 focus:ring-4 focus:ring-indigo-100 transition"
                    placeholder={t("auth.registerSeller.emailPlaceholder")}
                  />
                </div>
                <div>
                  <label htmlFor="password" className="block text-sm font-medium text-slate-700 mb-1.5">
                    {t("auth.registerSeller.password")}
                  </label>
                  <input
                    id="password"
                    type="password"
                    autoComplete="new-password"
                    required
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    className="block w-full bg-white border border-slate-200 rounded-xl px-4 py-3 text-sm placeholder:text-slate-400 text-slate-900 focus:outline-none focus:border-indigo-300 focus:ring-4 focus:ring-indigo-100 transition"
                    placeholder={t("auth.registerSeller.passwordPlaceholder")}
                  />
                </div>
                <div>
                  <label htmlFor="confirm_password" className="block text-sm font-medium text-slate-700 mb-1.5">
                    {t("auth.registerSeller.confirmPassword")}
                  </label>
                  <input
                    id="confirm_password"
                    type="password"
                    autoComplete="new-password"
                    required
                    value={confirmPassword}
                    onChange={(e) => setConfirmPassword(e.target.value)}
                    className="block w-full bg-white border border-slate-200 rounded-xl px-4 py-3 text-sm placeholder:text-slate-400 text-slate-900 focus:outline-none focus:border-indigo-300 focus:ring-4 focus:ring-indigo-100 transition"
                    placeholder={t("auth.registerSeller.confirmPasswordPlaceholder")}
                  />
                </div>
              </div>
            </div>

            <div className="bg-slate-50 p-6 rounded-xl border border-slate-200">
              <h3 className="text-sm font-semibold tracking-wide text-slate-900 mb-4">{t("auth.registerSeller.businessInfo")}</h3>
              <div className="space-y-4">
                <div>
                  <label htmlFor="business_name" className="block text-sm font-medium text-slate-700 mb-1.5">
                    {t("auth.registerSeller.businessName")} <span className="text-red-500">*</span>
                  </label>
                  <input
                    id="business_name"
                    type="text"
                    required
                    value={businessName}
                    onChange={(e) => setBusinessName(e.target.value)}
                    className="block w-full bg-white border border-slate-200 rounded-xl px-4 py-3 text-sm placeholder:text-slate-400 text-slate-900 focus:outline-none focus:border-indigo-300 focus:ring-4 focus:ring-indigo-100 transition"
                    placeholder={t("auth.registerSeller.businessNamePlaceholder")}
                  />
                </div>
                <div>
                  <label htmlFor="tax_id" className="block text-sm font-medium text-slate-700 mb-1.5">
                    {t("auth.registerSeller.taxId")}
                  </label>
                  <input
                    id="tax_id"
                    type="text"
                    value={taxId}
                    onChange={(e) => setTaxId(e.target.value)}
                    className="block w-full bg-white border border-slate-200 rounded-xl px-4 py-3 text-sm placeholder:text-slate-400 text-slate-900 focus:outline-none focus:border-indigo-300 focus:ring-4 focus:ring-indigo-100 transition"
                    placeholder={t("auth.registerSeller.optional")}
                  />
                </div>
                <div>
                  <label htmlFor="business_address" className="block text-sm font-medium text-slate-700 mb-1.5">
                    {t("auth.registerSeller.businessAddress")}
                  </label>
                  <textarea
                    id="business_address"
                    rows={3}
                    value={businessAddress}
                    onChange={(e) => setBusinessAddress(e.target.value)}
                    className="block w-full bg-white border border-slate-200 rounded-xl px-4 py-3 text-sm placeholder:text-slate-400 text-slate-900 focus:outline-none focus:border-indigo-300 focus:ring-4 focus:ring-indigo-100 transition resize-none"
                    placeholder={t("auth.registerSeller.optional")}
                  />
                </div>
                <div>
                  <label htmlFor="phone" className="block text-sm font-medium text-slate-700 mb-1.5">
                    {t("auth.registerSeller.phone")}
                  </label>
                  <input
                    id="phone"
                    type="tel"
                    value={phone}
                    onChange={(e) => setPhone(e.target.value)}
                    className="block w-full bg-white border border-slate-200 rounded-xl px-4 py-3 text-sm placeholder:text-slate-400 text-slate-900 focus:outline-none focus:border-indigo-300 focus:ring-4 focus:ring-indigo-100 transition"
                    placeholder={t("auth.registerSeller.optional")}
                  />
                </div>
              </div>
            </div>

            <div className="bg-amber-50 border border-amber-200 rounded-xl p-4">
              <p className="text-sm text-amber-800">
                <strong>{t("auth.registerSeller.notePrefix")}</strong> {t("auth.registerSeller.note")}
              </p>
            </div>

            <button
              type="submit"
              disabled={loading}
              className="w-full flex justify-center py-3 px-4 text-sm font-medium rounded-full text-white bg-slate-900 hover:bg-slate-800 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-slate-900 disabled:opacity-50 transition"
            >
              {loading ? t("auth.registerSeller.submitting") : t("auth.registerSeller.submit")}
            </button>
          </form>
        </div>
      </div>
    </div>
  );
}
