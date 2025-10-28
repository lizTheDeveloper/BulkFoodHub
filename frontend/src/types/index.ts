export interface User {
  id: number;
  email: string;
  first_name: string;
  last_name: string;
  role: 'customer' | 'wholesale_buyer' | 'supplier' | 'admin';
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface Product {
  id: number;
  name: string;
  description: string;
  price_per_unit: number;
  unit: string;
  available_quantity: number;
  category: string;
  ingredients?: string;
  nutritional_info?: string;
  is_active: boolean;
  is_approved: boolean;
  supplier_id: number;
  supplier_name?: string;
  supplier_business_name?: string;
  created_at: string;
  updated_at: string;
  images?: ProductImage[];
}

export interface ProductImage {
  id: number;
  product_id: number;
  image_url: string;
  alt_text?: string;
  is_primary: boolean;
  created_at: string;
}

export interface Category {
  name: string;
  value: string;
  description: string;
  product_count: number;
}

export interface ProductSearchParams {
  query?: string;
  category?: string;
  supplier_id?: number;
  min_price?: number;
  max_price?: number;
  min_quantity?: number;
  is_active?: boolean;
  is_approved?: boolean;
  sort_by?: string;
  sort_order?: 'asc' | 'desc';
  page?: number;
  size?: number;
  offset?: number;
}

export interface PaginationParams {
  page: number;
  size: number;
  offset: number;
}

export interface ProductListResponse {
  page: number;
  size: number;
  total: number;
  products: Product[];
}

export interface ApiResponse<T> {
  success: boolean;
  message: string;
  data?: T;
}

export interface LoginRequest {
  email: string;
  password: string;
}

export interface LoginResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
  user: User;
}

export interface RegisterRequest {
  email: string;
  password: string;
  first_name: string;
  last_name: string;
  role: 'customer' | 'wholesale_buyer' | 'supplier' | 'admin';
}

export interface Address {
  id: number;
  user_id: number;
  street_address: string;
  city: string;
  state: string;
  postal_code: string;
  country: string;
  is_default: boolean;
  created_at: string;
  updated_at: string;
}

export interface CartItem {
  id: string;
  product: Product;
  quantity: number;
  unit_price: number;
  total_price: number;
  added_at: string;
}

export interface Cart {
  items: CartItem[];
  total_items: number;
  total_price: number;
  created_at: string;
  updated_at: string;
}

export interface ShippingAddress {
  first_name: string;
  last_name: string;
  company?: string;
  street_address: string;
  apartment?: string;
  city: string;
  state: string;
  postal_code: string;
  country: string;
  phone?: string;
}

export interface BillingAddress extends ShippingAddress {}

export interface CheckoutRequest {
  shipping_address: ShippingAddress;
  billing_address: BillingAddress;
  payment_method: 'credit_card' | 'paypal';
  notes?: string;
}

export interface OrderCalculation {
  subtotal: number;
  tax_amount: number;
  shipping_cost: number;
  total_amount: number;
  currency: string;
}
