"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { useAuth } from "@/context/AuthContext";
import { useLanguage } from "@/context/LanguageContext";
import { LanguageToggle } from "@/components/LanguageToggle";

export default function SignupPage() {
  const router = useRouter();
  const { signup, isAuthenticated } = useAuth();
  const { t } = useLanguage();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [fullName, setFullName] = useState("");
  const [role, setRole] = useState<"buyer" | "seller">("buyer");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  if (isAuthenticated) {
    return null;
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    if (password !== confirmPassword) {
      setError(t("auth.signup.errorMismatch"));
      return;
    }
    if (password.length < 8) {
      setError(t("auth.signup.errorLength"));
      return;
    }
    setLoading(true);
    try {
      await signup({ email, password, full_name: fullName, role });
      router.push("/");
      router.refresh();
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Signup failed");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-slate-50 flex flex-col items-center justify-center py-12 px-4 sm:px-6 lg:px-8 relative">
      <div className="absolute top-4 right-4">
        <LanguageToggle />
      </div>
      <div className="max-w-md w-full">
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
              {t("auth.signup.title")}
            </h2>
            <p className="mt-2 text-sm text-slate-500">
              {t("auth.signup.alreadyHave")}{" "}
              <Link href="/auth/login" className="font-medium text-indigo-600 hover:text-indigo-500">
                {t("auth.signup.signIn")}
              </Link>
            </p>
          </div>

          <form className="space-y-5" onSubmit={handleSubmit}>
            {error && (
              <div className="bg-red-50 text-red-600 border border-red-200 p-4 rounded-xl text-sm">
                {error}
              </div>
            )}
            <div className="space-y-4">
              <div>
                <label htmlFor="full_name" className="block text-sm font-medium text-slate-700 mb-1.5">
                  {t("auth.signup.fullNameLabel")}
                </label>
                <input
                  id="full_name"
                  name="full_name"
                  type="text"
                  autoComplete="name"
                  required
                  value={fullName}
                  onChange={(e) => setFullName(e.target.value)}
                  className="block w-full bg-slate-50 border border-slate-200 rounded-xl px-4 py-3 text-sm placeholder:text-slate-400 text-slate-900 focus:outline-none focus:border-indigo-300 focus:ring-4 focus:ring-indigo-100 transition"
                  placeholder={t("auth.signup.fullNamePlaceholder")}
                />
              </div>
              <div>
                <label htmlFor="email" className="block text-sm font-medium text-slate-700 mb-1.5">
                  {t("auth.signup.emailLabel")}
                </label>
                <input
                  id="email"
                  name="email"
                  type="email"
                  autoComplete="email"
                  required
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  className="block w-full bg-slate-50 border border-slate-200 rounded-xl px-4 py-3 text-sm placeholder:text-slate-400 text-slate-900 focus:outline-none focus:border-indigo-300 focus:ring-4 focus:ring-indigo-100 transition"
                  placeholder={t("auth.signup.emailPlaceholder")}
                />
              </div>
              <div>
                <label htmlFor="password" className="block text-sm font-medium text-slate-700 mb-1.5">
                  {t("auth.signup.passwordLabel")}
                </label>
                <input
                  id="password"
                  name="password"
                  type="password"
                  autoComplete="new-password"
                  required
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  className="block w-full bg-slate-50 border border-slate-200 rounded-xl px-4 py-3 text-sm placeholder:text-slate-400 text-slate-900 focus:outline-none focus:border-indigo-300 focus:ring-4 focus:ring-indigo-100 transition"
                  placeholder={t("auth.signup.passwordPlaceholder")}
                />
              </div>
              <div>
                <label htmlFor="confirm_password" className="block text-sm font-medium text-slate-700 mb-1.5">
                  {t("auth.signup.confirmPasswordLabel")}
                </label>
                <input
                  id="confirm_password"
                  name="confirm_password"
                  type="password"
                  autoComplete="new-password"
                  required
                  value={confirmPassword}
                  onChange={(e) => setConfirmPassword(e.target.value)}
                  className="block w-full bg-slate-50 border border-slate-200 rounded-xl px-4 py-3 text-sm placeholder:text-slate-400 text-slate-900 focus:outline-none focus:border-indigo-300 focus:ring-4 focus:ring-indigo-100 transition"
                  placeholder={t("auth.signup.confirmPasswordPlaceholder")}
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-2">{t("auth.signup.registerAs")}</label>
                <div className="flex gap-3">
                  <label className={`flex-1 flex items-center justify-center gap-2 px-4 py-3 rounded-xl border cursor-pointer transition ${role === "buyer" ? "bg-slate-900 border-slate-900 text-white" : "bg-slate-50 border-slate-200 text-slate-700 hover:bg-white"}`}>
                    <input
                      type="radio"
                      name="role"
                      value="buyer"
                      checked={role === "buyer"}
                      onChange={() => setRole("buyer")}
                      className="sr-only"
                    />
                    <span className="text-sm font-medium">{t("auth.signup.buyer")}</span>
                  </label>
                  <label className={`flex-1 flex items-center justify-center gap-2 px-4 py-3 rounded-xl border cursor-pointer transition ${role === "seller" ? "bg-slate-900 border-slate-900 text-white" : "bg-slate-50 border-slate-200 text-slate-700 hover:bg-white"}`}>
                    <input
                      type="radio"
                      name="role"
                      value="seller"
                      checked={role === "seller"}
                      onChange={() => setRole("seller")}
                      className="sr-only"
                    />
                    <span className="text-sm font-medium">{t("auth.signup.seller")}</span>
                  </label>
                </div>
                {role === "seller" && (
                  <p className="mt-2 text-xs text-slate-500">
                    {t("auth.signup.sellerNote")}
                  </p>
                )}
              </div>
            </div>

            <button
              type="submit"
              disabled={loading}
              className="w-full flex justify-center py-3 px-4 text-sm font-medium rounded-full text-white bg-slate-900 hover:bg-slate-800 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-slate-900 disabled:opacity-50 transition"
            >
              {loading ? t("auth.signup.creating") : t("auth.signup.create")}
            </button>
          </form>
        </div>
      </div>
    </div>
  );
}
