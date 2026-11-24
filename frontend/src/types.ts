export interface ProductVariant {
  id: number;
  title: string;
  sku: string;
  price: string;
  inventory_quantity: number;
  minimum_stock: number | null;
  stock_status: "out_of_stock" | "low_stock" | "not_configured" | "normal";
}

export interface Product {
  id: number;
  name: string;
  slug: string;
  description: string;
  status: string;
  variants: ProductVariant[];
  created_at: string;
  updated_at: string;
}

export interface OrderItem {
  id: number;
  sku_snapshot: string;
  product_title_snapshot: string;
  product_name: string;
  quantity: number;
  unit_price: string;
  subtotal: string;
}

export interface Order {
  id: number;
  shopify_order_id: string;
  customer_email: string;
  currency: string;
  status: "pending" | "confirmed" | "shipped" | "completed" | "cancelled";
  total: string;
  items: OrderItem[];
  created_at: string;
}

export interface InventoryVariant extends ProductVariant {
  product: number;
}

export interface ShopifyConnection {
  connected: boolean;
  shop?: Record<string, string>;
  error?: string;
}
