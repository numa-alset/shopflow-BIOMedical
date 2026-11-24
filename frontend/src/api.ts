import axios from "axios";
import type { InventoryVariant, Order, Product, ShopifyConnection } from "./types";

export const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL ?? "/api",
  timeout: 15000,
  headers: { Accept: "application/json" },
});

export async function fetchProducts(): Promise<Product[]> {
  const { data } = await api.get<Product[]>("/products/");
  return data;
}

export async function fetchOrders(): Promise<Order[]> {
  const { data } = await api.get<Order[]>("/orders/");
  return data;
}

export async function fetchVariants(): Promise<InventoryVariant[]> {
  const { data } = await api.get<InventoryVariant[]>("/products/variants/");
  return data;
}

export async function testShopifyConnection(): Promise<ShopifyConnection> {
  const { data } = await api.post<ShopifyConnection>("/shopify/test-connection/");
  return data;
}
