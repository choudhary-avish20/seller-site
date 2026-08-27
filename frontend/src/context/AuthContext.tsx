"use client";

import React, { createContext, useContext, useState, useEffect, ReactNode } from "react";
import { api, User } from "@/lib/api";

interface AuthContextType {
  user: User | null;
  loading: boolean;
  login: (email: string, password: string) => Promise<void>;
  signup: (data: { email: string; password: string; full_name: string; role?: "buyer" | "seller" }) => Promise<void>;
  registerSeller: (data: {
    email: string;
    password: string;
    full_name: string;
    seller_profile: {
      business_name: string;
      tax_id?: string;
      business_address?: string;
      phone?: string;
    };
  }) => Promise<void>;
  logout: () => void;
  refreshUser: () => Promise<void>;
  isAuthenticated: boolean;
  isSeller: boolean;
  isBuyer: boolean;
  isAdmin: boolean;
  isSellerApproved: boolean;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);

  const refreshUser = async () => {
    const token = api.getAccessToken();
    if (!token) {
      setUser(null);
      setLoading(false);
      return;
    }
    try {
      const userData = await api.getMe();
      setUser(userData);
    } catch {
      setUser(null);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    refreshUser();
  }, []);

  const login = async (email: string, password: string) => {
    const tokens = await api.login(email, password);
    api.setTokens(tokens.access_token, tokens.refresh_token);
    await refreshUser();
  };

  const signup = async (data: { email: string; password: string; full_name: string; role?: "buyer" | "seller" }) => {
    await api.signup(data);
    await login(data.email, data.password);
  };

  const registerSeller = async (data: {
    email: string;
    password: string;
    full_name: string;
    seller_profile: {
      business_name: string;
      tax_id?: string;
      business_address?: string;
      phone?: string;
    };
  }) => {
    await api.registerSeller({ ...data, role: "seller" });
    await login(data.email, data.password);
  };

  const logout = () => {
    api.clearTokens();
    setUser(null);
    // allow immediate re-login / sign-up with another account — clear all auth + cart state
    if (typeof window !== "undefined") {
      try {
        localStorage.removeItem("user");
        localStorage.removeItem("cart_v1");
        // also clear any legacy cart keys
        localStorage.removeItem("cart");
      } catch {}
      const target = "/auth/login";
      if (window.location.pathname !== target) {
        window.location.href = target;
      } else {
        window.location.reload();
      }
    }
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        loading,
        login,
        signup,
        registerSeller,
        logout,
        refreshUser,
        isAuthenticated: !!user,
        isSeller: user?.role === "seller",
        isBuyer: user?.role === "buyer",
        isAdmin: user?.role === "admin",
        isSellerApproved: false,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return context;
}