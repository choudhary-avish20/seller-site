"use client";

import React, { createContext, useContext, useEffect, useState, ReactNode } from "react";
import { Product, ProductListItem } from "@/lib/api";

export type CartItem = {
  product: Product | ProductListItem;
  packQuantity: number;
  variantId?: string | null;
  variantLabel?: string | null;
  variantPriceNet?: number | null;
};

type CartContextType = {
  items: CartItem[];
  addToCart: (product: Product | ProductListItem, packQuantity?: number, variantId?: string | null, variantLabel?: string | null, variantPriceNet?: number | null) => void;
  updateQuantity: (productId: string, variantId: string | null | undefined, packQuantity: number) => void;
  removeFromCart: (productId: string, variantId?: string | null) => void;
  clearCart: () => void;
  count: number;
  totalNet: number;
  totalGross: number;
};

const CartContext = createContext<CartContextType | undefined>(undefined);

const STORAGE_KEY = "cart_v1";

export function CartProvider({ children }: { children: ReactNode }) {
  const [items, setItems] = useState<CartItem[]>([]);

  useEffect(() => {
    try {
      const raw = localStorage.getItem(STORAGE_KEY);
      if (raw) setItems(JSON.parse(raw));
    } catch {}
  }, []);

  useEffect(() => {
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(items));
    } catch {}
  }, [items]);

  const addToCart = (product: Product | ProductListItem, packQuantity = 1, variantId?: string | null, variantLabel?: string | null, variantPriceNet?: number | null) => {
    setItems((prev) => {
      const idx = prev.findIndex((it) => it.product.id === product.id && (it.variantId || null) === (variantId || null));
      if (idx >= 0) {
        const copy = [...prev];
        copy[idx] = { ...copy[idx], packQuantity: copy[idx].packQuantity + packQuantity };
        return copy;
      }
      return [...prev, { product, packQuantity, variantId: variantId || null, variantLabel: variantLabel || null, variantPriceNet: variantPriceNet ?? null }];
    });
  };

  const updateQuantity = (productId: string, variantId: string | null | undefined, packQuantity: number) => {
    if (packQuantity < 1) return removeFromCart(productId, variantId);
    setItems((prev) => prev.map((it) => (it.product.id === productId && (it.variantId || null) === (variantId || null) ? { ...it, packQuantity } : it)));
  };

  const removeFromCart = (productId: string, variantId?: string | null) => {
    setItems((prev) => prev.filter((it) => !(it.product.id === productId && (it.variantId || null) === (variantId || null))));
  };

  const clearCart = () => setItems([]);

  const count = items.reduce((sum, it) => sum + it.packQuantity, 0);

  const getNet = (it: CartItem) => {
    if (it.variantPriceNet != null) return it.variantPriceNet;
    return (it.product as Product).price_net ?? (it.product as ProductListItem).price_net;
  };
  const getGross = (it: CartItem) => {
    // if variant override, gross recomputed with same VAT? Use product vat
    const vat = (it.product as Product).vat_rate ?? (it.product as ProductListItem).vat_rate ?? 23;
    const net = getNet(it);
    // if original gross for variant not stored, compute
    if (it.variantPriceNet != null) return +(net * (1 + vat / 100)).toFixed(2);
    return (it.product as Product).price_gross ?? (it.product as ProductListItem).price_gross;
  };
  const totalNet = items.reduce((sum, it) => sum + getNet(it) * it.packQuantity, 0);
  const totalGross = items.reduce((sum, it) => sum + getGross(it) * it.packQuantity, 0);

  return (
    <CartContext.Provider value={{ items, addToCart, updateQuantity, removeFromCart, clearCart, count, totalNet, totalGross }}>
      {children}
    </CartContext.Provider>
  );
}

export function useCart() {
  const ctx = useContext(CartContext);
  if (!ctx) throw new Error("useCart must be used within CartProvider");
  return ctx;
}
