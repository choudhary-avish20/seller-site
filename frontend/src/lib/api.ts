const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";
export const API_BASE = API_URL.replace(/\/api\/v1\/?$/, "");
export function getImageUrl(path: string): string {
  if (!path) return "";
  if (path.startsWith("http")) return path;
  if (path.startsWith("/")) return `${API_BASE}${path}`;
  return path;
}

export interface User {
  id: string;
  email: string;
  full_name: string;
  role: "buyer" | "seller" | "admin";
  is_active: boolean;
  created_at: string;
}

export interface SellerProfile {
  id: string;
  user_id: string;
  business_name: string;
  tax_id?: string;
  business_address?: string;
  phone?: string;
  status: "pending" | "approved" | "rejected";
  rejection_reason?: string;
  created_at: string;
}

export interface TokenResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
}

export interface SellerRegistrationRequest {
  email: string;
  password: string;
  full_name: string;
  role: "seller";
  seller_profile: {
    business_name: string;
    tax_id?: string;
    business_address?: string;
    phone?: string;
  };
}

export interface SellerListResponse {
  id: string;
  email: string;
  full_name: string;
  business_name: string;
  status: "pending" | "approved" | "rejected";
  created_at: string;
}

export interface Category {
  id: string;
  name: string;
  slug: string;
  parent_id: string | null;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface CategoryTreeNode extends Category {
  children: CategoryTreeNode[];
}

export interface CategoryPathResponse {
  category: Category;
  ancestors: Category[];
  path: string;
}

export interface CategoryRequest {
  id: string;
  requester_id: string;
  name: string;
  slug: string;
  parent_id: string | null;
  description?: string | null;
  status: "pending" | "approved" | "rejected";
  rejection_reason?: string | null;
  created_category_id?: string | null;
  created_at: string;
  updated_at: string;
  requester_email?: string | null;
  parent_name?: string | null;
}

export interface ProductVariant {
  id: string;
  product_id: string;
  sku: string;
  option_name: string;
  option_value: string;
  price_net_override?: number | null;
  stock_quantity: number;
  created_at: string;
  updated_at: string;
}

export interface Product {
  id: string;
  seller_id: string;
  category_id: string;
  name: string;
  slug: string;
  description?: string | null;
  images: string[];
  pack_size: number;
  price_net: number;
  price_gross: number;
  vat_rate: number;
  stock_quantity: number;
  stock_status: "in_stock" | "out_of_stock";
  is_active: boolean;
  created_at: string;
  updated_at: string;
  category_name?: string | null;
  category_slug?: string | null;
  seller_business_name?: string | null;
  variants: ProductVariant[];
}

export interface ProductListItem {
  id: string;
  seller_id: string;
  category_id: string;
  name: string;
  slug: string;
  images: string[];
  pack_size: number;
  price_net: number;
  price_gross: number;
  vat_rate: number;
  stock_quantity: number;
  stock_status: "in_stock" | "out_of_stock";
  is_active: boolean;
  created_at: string;
  category_name?: string | null;
  category_slug?: string | null;
}

export interface OrderItem {
  id: string;
  order_id: string;
  product_id: string;
  variant_id?: string | null;
  product_name_snapshot: string;
  pack_size_snapshot: number;
  price_net_snapshot: number;
  price_gross_snapshot: number;
  pack_quantity: number;
  created_at: string;
}

export interface Order {
  id: string;
  buyer_id: string;
  status: "pending" | "confirmed" | "shipped" | "delivered" | "cancelled";
  total_net: number;
  total_gross: number;
  shipping_address: string;
  notes?: string | null;
  created_at: string;
  updated_at: string;
  items: OrderItem[];
}

class ApiClient {
  private accessToken: string | null = null;
  private refreshToken: string | null = null;

  constructor() {
    if (typeof window !== "undefined") {
      this.accessToken = localStorage.getItem("access_token");
      this.refreshToken = localStorage.getItem("refresh_token");
    }
  }

  setTokens(access: string, refresh: string) {
    this.accessToken = access;
    this.refreshToken = refresh;
    if (typeof window !== "undefined") {
      localStorage.setItem("access_token", access);
      localStorage.setItem("refresh_token", refresh);
    }
  }

  clearTokens() {
    this.accessToken = null;
    this.refreshToken = null;
    if (typeof window !== "undefined") {
      localStorage.removeItem("access_token");
      localStorage.removeItem("refresh_token");
    }
  }

  getAccessToken(): string | null {
    return this.accessToken;
  }

  async refreshAccessToken(): Promise<boolean> {
    if (!this.refreshToken) return false;
    try {
      const res = await fetch(`${API_URL}/auth/refresh`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ refresh_token: this.refreshToken }),
      });
      if (!res.ok) throw new Error("Refresh failed");
      const data: TokenResponse = await res.json();
      this.setTokens(data.access_token, data.refresh_token);
      return true;
    } catch {
      this.clearTokens();
      return false;
    }
  }

  async request<T>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<T> {
    const headers: Record<string, string> = {
      "Content-Type": "application/json",
      ...(options.headers as Record<string, string>),
    };

    if (this.accessToken) {
      headers["Authorization"] = `Bearer ${this.accessToken}`;
    }

    let res = await fetch(`${API_URL}${endpoint}`, {
      ...options,
      headers,
    });

    if (res.status === 401 && this.refreshToken) {
      const refreshed = await this.refreshAccessToken();
      if (refreshed) {
        headers["Authorization"] = `Bearer ${this.accessToken}`;
        res = await fetch(`${API_URL}${endpoint}`, {
          ...options,
          headers,
        });
      }
    }

    if (!res.ok) {
      const error = await res.json().catch(() => ({ detail: "Request failed" }));
      throw new Error(error.detail || `HTTP ${res.status}`);
    }

    if (res.status === 204) return {} as T;
    return res.json();
  }

  // Auth endpoints
  signup(data: { email: string; password: string; full_name: string; role?: "buyer" | "seller" }) {
    return this.request<User>("/auth/signup", {
      method: "POST",
      body: JSON.stringify(data),
    });
  }

  login(email: string, password: string) {
    return this.request<TokenResponse>("/auth/login", {
      method: "POST",
      body: JSON.stringify({ email, password }),
    });
  }

  getMe() {
    return this.request<User>("/auth/me");
  }

  // Seller endpoints
  registerSeller(data: SellerRegistrationRequest) {
    return this.request<{ user: User; seller_profile: SellerProfile }>("/sellers/register", {
      method: "POST",
      body: JSON.stringify(data),
    });
  }

  getMySellerProfile() {
    return this.request<SellerProfile>("/sellers/me/profile");
  }

  // Admin endpoints
  getPendingSellers() {
    return this.request<SellerListResponse[]>("/sellers/pending");
  }

  approveSeller(sellerId: string, status: "approved" | "rejected", rejectionReason?: string) {
    return this.request<SellerProfile>(`/sellers/${sellerId}/approve`, {
      method: "POST",
      body: JSON.stringify({ status, rejection_reason: rejectionReason }),
    });
  }

  // Category endpoints
  getCategoryTree(includeInactive = false) {
    return this.request<CategoryTreeNode[]>(`/categories/tree?include_inactive=${includeInactive}`);
  }

  listCategories(params?: { parent_id?: string; include_inactive?: boolean; search?: string }) {
    const qs = new URLSearchParams();
    if (params?.parent_id) qs.set("parent_id", params.parent_id);
    if (params?.include_inactive) qs.set("include_inactive", "true");
    if (params?.search) qs.set("search", params.search);
    const suffix = qs.toString() ? `?${qs.toString()}` : "";
    return this.request<Category[]>(`/categories${suffix}`);
  }

  getCategoryBySlug(slug: string) {
    return this.request<Category>(`/categories/by-slug/${slug}`);
  }

  getCategoryByPath(path: string) {
    return this.request<CategoryPathResponse>(`/categories/by-path/${path}`);
  }

  getCategory(id: string) {
    return this.request<Category>(`/categories/${id}`);
  }

  createCategory(data: { name: string; slug?: string; parent_id?: string | null; is_active?: boolean }) {
    return this.request<Category>(`/categories`, {
      method: "POST",
      body: JSON.stringify(data),
    });
  }

  updateCategory(id: string, data: { name?: string; slug?: string; parent_id?: string | null; is_active?: boolean }) {
    return this.request<Category>(`/categories/${id}`, {
      method: "PUT",
      body: JSON.stringify(data),
    });
  }

  deleteCategory(id: string) {
    return this.request<void>(`/categories/${id}`, {
      method: "DELETE",
    });
  }

  // Category request endpoints
  createCategoryRequest(data: { name: string; parent_id?: string | null; description?: string; slug?: string }) {
    return this.request<CategoryRequest>(`/category-requests`, {
      method: "POST",
      body: JSON.stringify(data),
    });
  }

  listCategoryRequests(params?: { status?: string; mine?: boolean }) {
    const qs = new URLSearchParams();
    if (params?.status) qs.set("status", params.status);
    if (params?.mine) qs.set("mine", "true");
    const suffix = qs.toString() ? `?${qs.toString()}` : "";
    return this.request<CategoryRequest[]>(`/category-requests${suffix}`);
  }

  getCategoryRequest(id: string) {
    return this.request<CategoryRequest>(`/category-requests/${id}`);
  }

  decideCategoryRequest(id: string, action: "approve" | "reject", rejection_reason?: string) {
    return this.request<CategoryRequest>(`/category-requests/${id}/decision`, {
      method: "POST",
      body: JSON.stringify({ action, rejection_reason }),
    });
  }

  // Product endpoints
  listProducts(params?: { category_id?: string; search?: string; seller_id?: string; page?: number; limit?: number }) {
    const qs = new URLSearchParams();
    if (params?.category_id) qs.set("category_id", params.category_id);
    if (params?.search) qs.set("search", params.search);
    if (params?.seller_id) qs.set("seller_id", params.seller_id);
    if (params?.page) qs.set("page", String(params.page));
    if (params?.limit) qs.set("limit", String(params.limit));
    const suffix = qs.toString() ? `?${qs.toString()}` : "";
    return this.request<ProductListItem[]>(`/products${suffix}`);
  }

  listMyProducts() {
    return this.request<ProductListItem[]>(`/products/my`);
  }

  getProduct(id: string) {
    return this.request<Product>(`/products/${id}`);
  }

  getProductBySlug(slug: string) {
    return this.request<Product>(`/products/slug/${slug}`);
  }

  createProduct(data: {
    name: string;
    slug?: string;
    description?: string;
    images?: string[];
    category_id: string;
    pack_size: number;
    price_net: number;
    price_gross?: number;
    vat_rate?: number;
    stock_quantity?: number;
    stock_status?: "in_stock" | "out_of_stock";
    is_active?: boolean;
    variants?: { sku: string; option_name: string; option_value: string; price_net_override?: number | null; stock_quantity?: number }[];
  }) {
    return this.request<Product>(`/products`, {
      method: "POST",
      body: JSON.stringify(data),
    });
  }

  updateProduct(
    id: string,
    data: Partial<{
      name: string;
      slug: string;
      description: string;
      images: string[];
      category_id: string;
      pack_size: number;
      price_net: number;
      price_gross: number;
      vat_rate: number;
      stock_quantity: number;
      stock_status: "in_stock" | "out_of_stock";
      is_active: boolean;
      variants: { sku: string; option_name: string; option_value: string; price_net_override?: number | null; stock_quantity?: number }[];
    }>
  ) {
    return this.request<Product>(`/products/${id}`, {
      method: "PUT",
      body: JSON.stringify(data),
    });
  }

  deleteProduct(id: string) {
    return this.request<void>(`/products/${id}`, {
      method: "DELETE",
    });
  }

  toggleStock(id: string, data: { stock_status?: "in_stock" | "out_of_stock"; stock_quantity?: number }) {
    return this.request<Product>(`/products/${id}/stock`, {
      method: "PATCH",
      body: JSON.stringify(data),
    });
  }

  archiveProduct(id: string) {
    return this.request<Product>(`/products/${id}/archive`, {
      method: "PATCH",
    });
  }

  // Uploads
  async uploadImage(file: File): Promise<{ url: string; filename: string; original_filename: string }> {
    const form = new FormData();
    form.append("file", file);
    const headers: Record<string, string> = {};
    if (this.accessToken) headers["Authorization"] = `Bearer ${this.accessToken}`;
    let res = await fetch(`${API_URL}/uploads/image`, {
      method: "POST",
      headers,
      body: form,
    });
    if (res.status === 401 && this.refreshToken) {
      const refreshed = await this.refreshAccessToken();
      if (refreshed) {
        headers["Authorization"] = `Bearer ${this.accessToken}`;
        res = await fetch(`${API_URL}/uploads/image`, {
          method: "POST",
          headers,
          body: form,
        });
      }
    }
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: "Upload failed" }));
      throw new Error(err.detail || `HTTP ${res.status}`);
    }
    return res.json();
  }

  listTestImages() {
    return this.request<string[]>(`/uploads/test-images`);
  }

  // Orders
  createOrder(data: { shipping_address: string; notes?: string; items: { product_id: string; variant_id?: string | null; pack_quantity: number }[] }) {
    return this.request<Order>(`/orders`, {
      method: "POST",
      body: JSON.stringify(data),
    });
  }

  listOrders() {
    return this.request<Order[]>(`/orders`);
  }

  getOrder(id: string) {
    return this.request<Order>(`/orders/${id}`);
  }
}

export const api = new ApiClient();