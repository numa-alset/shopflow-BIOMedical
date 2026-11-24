import { useMemo, useState, type ReactNode } from "react";
import { Link, NavLink, Outlet, Route, Routes, useLocation } from "react-router-dom";
import { useMutation, useQuery } from "@tanstack/react-query";
import axios from "axios";
import {
  Activity,
  ArrowDownRight,
  ArrowRight,
  ArrowUpRight,
  Bell,
  ChevronDown,
  CircleHelp,
  Command,
  LayoutDashboard,
  Menu,
  Package,
  Search,
  Settings,
  ShoppingBag,
  Sparkles,
} from "lucide-react";
import { fetchOrders, fetchProducts, fetchVariants, testShopifyConnection } from "./api";
import type { Order, Product, ProductVariant } from "./types";

const navigation = [
  { label: "Overview", to: "/", icon: LayoutDashboard },
  { label: "Products", to: "/products", icon: Package },
  { label: "Inventory", to: "/inventory", icon: Activity },
  { label: "Orders", to: "/orders", icon: ShoppingBag },
];

function usePageTitle() {
  const location = useLocation();
  if (location.pathname === "/settings") return "Settings";
  return navigation.find((item) => item.to === location.pathname)?.label ?? "Overview";
}

function AppShell() {
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const title = usePageTitle();

  return (
    <div className="app-shell">
      {sidebarOpen && <button className="mobile-backdrop" aria-label="Close menu" onClick={() => setSidebarOpen(false)} />}
      <aside className={`sidebar ${sidebarOpen ? "sidebar-open" : ""}`}>
        <Link className="brand" to="/" onClick={() => setSidebarOpen(false)}>
          <span className="brand-mark"><Activity size={20} strokeWidth={2.5} /></span>
          <span className="brand-name">shopflow<span>.</span></span>
        </Link>
        <div className="workspace-switcher">
          <span className="workspace-avatar">S</span>
          <span className="workspace-copy"><strong>Shopflow Store</strong><small>Workspace</small></span>
          <ChevronDown size={15} className="muted-icon" />
        </div>
        <p className="nav-caption">WORKSPACE</p>
        <nav className="side-nav" aria-label="Main navigation">
          {navigation.map(({ label, to, icon: Icon }) => (
            <NavLink
              key={to}
              to={to}
              end={to === "/"}
              className={({ isActive }) => `nav-link ${isActive ? "active" : ""}`}
              onClick={() => setSidebarOpen(false)}
            >
              <Icon size={18} strokeWidth={1.9} />
              <span>{label}</span>
            </NavLink>
          ))}
        </nav>
        <div className="sidebar-bottom">
          <div className="help-card">
            <span className="help-icon"><Sparkles size={16} /></span>
            <strong>Need a hand?</strong>
            <p>Manage your store connection and workspace.</p>
            <Link to="/settings">Open settings <ArrowRight size={13} /></Link>
          </div>
          <NavLink to="/settings" className={({ isActive }) => `nav-link settings-link ${isActive ? "active" : ""}`} onClick={() => setSidebarOpen(false)}>
            <Settings size={18} /><span>Settings</span>
          </NavLink>
          <div className="profile">
            <span className="profile-avatar">SA</span>
            <span className="profile-copy"><strong>Store administrator</strong><small>Workspace</small></span>
            <ChevronDown size={15} className="muted-icon" />
          </div>
        </div>
      </aside>

      <main className="main-area">
        <header className="topbar">
          <button className="mobile-menu icon-button" aria-label="Open menu" onClick={() => setSidebarOpen(true)}><Menu size={20} /></button>
          <div className="breadcrumbs"><span>Workspace</span><span className="crumb-slash">/</span><strong>{title}</strong></div>
          <div className="topbar-actions">
            <div className="search-shortcut"><Search size={16} /><span>Search anything...</span><kbd><Command size={11} /> K</kbd></div>
            <button className="icon-button notification-button" aria-label="Notifications"><Bell size={18} /><i /></button>
            <span className="topbar-divider" />
            <span className="today-label">{new Intl.DateTimeFormat("en", { weekday: "short", month: "short", day: "numeric" }).format(new Date())}</span>
          </div>
        </header>
        <div className="page-content"><Outlet /></div>
      </main>
    </div>
  );
}

function PageHeading({ eyebrow, title, description, children }: { eyebrow?: string; title: string; description: string; children?: ReactNode }) {
  return (
    <div className="page-heading">
      <div>
        {eyebrow && <div className="eyebrow">{eyebrow}</div>}
        <h1>{title}</h1>
        <p>{description}</p>
      </div>
      {children && <div className="heading-actions">{children}</div>}
    </div>
  );
}

function LoadingState({ label = "Loading your data..." }: { label?: string }) {
  return <div className="state-card"><span className="spinner" /><span>{label}</span></div>;
}

function ErrorState({ onRetry }: { onRetry: () => void }) {
  return (
    <div className="state-card error-state">
      <span className="error-mark">!</span>
      <div><strong>We couldn’t load this data</strong><p>Check that the backend is running, then try again.</p></div>
      <button className="button button-secondary" onClick={onRetry}>Try again</button>
    </div>
  );
}

function EmptyState({ message }: { message: string }) {
  return <div className="empty-state"><Package size={22} /><p>{message}</p></div>;
}

function useDashboardData() {
  const products = useQuery({ queryKey: ["products"], queryFn: fetchProducts });
  const orders = useQuery({ queryKey: ["orders"], queryFn: fetchOrders });
  const variants = useQuery({ queryKey: ["variants"], queryFn: fetchVariants });
  return { products, orders, variants };
}

function formatCurrency(value: string | number, currency = "EUR") {
  return new Intl.NumberFormat("en", { style: "currency", currency, maximumFractionDigits: 2 }).format(Number(value) || 0);
}

function formatDate(value: string, withTime = false) {
  return new Intl.DateTimeFormat("en", withTime ? { month: "short", day: "numeric", year: "numeric", hour: "numeric", minute: "2-digit" } : { month: "short", day: "numeric", year: "numeric" }).format(new Date(value));
}

function getStockTone(variant: ProductVariant) {
  if (variant.stock_status === "out_of_stock") return "out";
  if (variant.stock_status === "low_stock") return "low";
  if (variant.stock_status === "not_configured") return "unset";
  return "healthy";
}

function StatusPill({ status }: { status: string }) {
  const normalized = status.toLowerCase().replaceAll("_", " ");
  const tone = normalized === "completed" || normalized === "active" ? "success" : normalized === "cancelled" ? "danger" : normalized === "shipped" ? "info" : "warning";
  return <span className={`status-pill ${tone}`}><i />{normalized}</span>;
}

function ProductGlyph({ name, index = 0 }: { name: string; index?: number }) {
  const palette = ["mint", "lavender", "peach", "blue", "yellow"];
  return <span className={`product-glyph ${palette[index % palette.length]}`}>{name.trim().slice(0, 1).toUpperCase() || "P"}</span>;
}

function MetricCard({ label, value, note, change, tone, icon: Icon }: {
  label: string; value: string; note: string; change?: string; tone: string;
  icon: typeof Package;
}) {
  return (
    <article className="metric-card">
      <div className="metric-top">
        <span className={`metric-icon ${tone}`}><Icon size={18} /></span>
        {change && <span className={`metric-change ${change.startsWith("-") ? "negative" : ""}`}>{change.startsWith("-") ? <ArrowDownRight size={13} /> : <ArrowUpRight size={13} />}{change}</span>}
      </div>
      <p className="metric-label">{label}</p>
      <strong className="metric-value">{value}</strong>
      <span className="metric-note">{note}</span>
    </article>
  );
}

function RevenueChart({ orders }: { orders: Order[] }) {
  const chart = useMemo(() => {
    const days = Array.from({ length: 7 }, (_, index) => {
      const date = new Date();
      date.setDate(date.getDate() - (6 - index));
      date.setHours(0, 0, 0, 0);
      return { date, total: 0 };
    });
    orders.forEach((order) => {
      const created = new Date(order.created_at);
      created.setHours(0, 0, 0, 0);
      const day = days.find((entry) => entry.date.getTime() === created.getTime());
      if (day && order.status !== "cancelled") day.total += Number(order.total) || 0;
    });
    const max = Math.max(...days.map((day) => day.total), 1);
    const points = days.map((day, index) => `${36 + index * 157},${164 - (day.total / max) * 128}`).join(" ");
    return { days, points, max };
  }, [orders]);
  return (
    <div className="chart-wrap">
      <div className="chart-summary"><strong>{formatCurrency(chart.days.reduce((sum, day) => sum + day.total, 0))}</strong><span className="chart-up">7-day total</span></div>
      <div className="chart-area">
        <div className="chart-y-labels"><span>{formatCurrency(chart.max)}</span><span>{formatCurrency(chart.max / 2)}</span><span>{formatCurrency(0)}</span></div>
        <svg className="revenue-chart" viewBox="0 0 1000 190" preserveAspectRatio="none" role="img" aria-label="Revenue over the last seven days">
          <defs><linearGradient id="chartFill" x1="0" x2="0" y1="0" y2="1"><stop offset="0%" stopColor="#31a58a" stopOpacity=".2" /><stop offset="100%" stopColor="#31a58a" stopOpacity="0" /></linearGradient></defs>
          {[36, 100, 164].map((y) => <line key={y} x1="0" x2="1000" y1={y} y2={y} className="chart-grid" />)}
          <polygon points={`0,190 ${chart.points.split(" ").map((point) => point.split(",").join(",")).join(" ")} 978,190`} fill="url(#chartFill)" transform="scale(1 .9) translate(0 10)" />
          <polyline points={chart.points} className="chart-line" vectorEffect="non-scaling-stroke" />
          {chart.points.split(" ").map((point, index) => { const [x, y] = point.split(","); return <circle key={index} cx={x} cy={y} r="4.5" className="chart-point" vectorEffect="non-scaling-stroke" />; })}
        </svg>
      </div>
      <div className="chart-x-labels">{chart.days.map((day) => <span key={day.date.toISOString()}>{new Intl.DateTimeFormat("en", { weekday: "short" }).format(day.date)}</span>)}</div>
    </div>
  );
}

function DashboardPage() {
  const { products, orders, variants } = useDashboardData();
  const loading = products.isLoading || orders.isLoading || variants.isLoading;
  const error = products.isError || orders.isError || variants.isError;
  if (loading) return <LoadingState />;
  if (error) return <ErrorState onRetry={() => { void products.refetch(); void orders.refetch(); void variants.refetch(); }} />;

  const productRows = products.data ?? [];
  const orderRows = orders.data ?? [];
  const variantRows = variants.data ?? [];
  const inventoryCount = variantRows.reduce((total, item) => total + item.inventory_quantity, 0);
  const lowStock = variantRows.filter((item) => item.stock_status === "low_stock" || item.stock_status === "out_of_stock");
  const activeOrders = orderRows.filter((order) => order.status === "pending" || order.status === "confirmed").length;
  const recentOrders = orderRows.slice(0, 5);
  const alerts = lowStock.slice(0, 4);
  const hour = new Date().getHours();
  const greeting = hour < 12 ? "Good morning" : hour < 18 ? "Good afternoon" : "Good evening";

  return (
    <>
      <PageHeading eyebrow={`${new Intl.DateTimeFormat("en", { weekday: "long" }).format(new Date()).toUpperCase()}, YOUR STORE AT A GLANCE`} title={`${greeting}, welcome back`} description="Here’s what’s happening with your store today.">
        <Link to="/products" className="button button-primary"><Package size={16} /> View catalog</Link>
      </PageHeading>
      <section className="metrics-grid">
        <MetricCard label="Total products" value={productRows.length.toLocaleString()} note={`${variantRows.length} product variants`} icon={Package} tone="mint" />
        <MetricCard label="Inventory on hand" value={inventoryCount.toLocaleString()} note="Units across all variants" icon={Activity} tone="purple" />
        <MetricCard label="Open orders" value={activeOrders.toLocaleString()} note={`${orderRows.length} total orders`} icon={ShoppingBag} tone="peach" />
        <MetricCard label="Low stock alerts" value={lowStock.length.toLocaleString()} note="Items need attention" icon={Bell} tone="yellow" change={lowStock.length ? `${lowStock.length} items` : undefined} />
      </section>
      <div className="dashboard-grid">
        <section className="panel revenue-panel">
          <div className="panel-heading"><div><h2>Revenue overview</h2><p>Your order revenue, day by day</p></div><span className="select-chip">Last 7 days <ChevronDown size={14} /></span></div>
          <RevenueChart orders={orderRows} />
        </section>
        <section className="panel alerts-panel">
          <div className="panel-heading"><div><h2>Stock alerts</h2><p>Products that need a restock</p></div><Link to="/inventory" className="text-link">View all <ArrowRight size={14} /></Link></div>
          {alerts.length === 0 ? <EmptyState message="You're all stocked up. Nice work!" /> : (
            <div className="alert-list">{alerts.map((variant) => {
              const product = productRows.find((item) => item.variants.some((child) => child.id === variant.id));
              return <div className="alert-row" key={variant.id}><ProductGlyph name={product?.name ?? variant.title} /><div className="alert-copy"><strong>{product?.name ?? variant.title}</strong><span>{variant.sku || "No SKU"} · {variant.stock_status === "out_of_stock" ? "Out of stock" : "Below minimum"}</span></div><span className={`stock-count ${variant.inventory_quantity <= 0 ? "stock-zero" : ""}`}>{variant.inventory_quantity}<small> left</small></span></div>;
            })}</div>
          )}
        </section>
      </div>
      <section className="panel orders-panel">
        <div className="panel-heading"><div><h2>Recent orders</h2><p>Keep track of your latest activity</p></div><Link to="/orders" className="text-link">All orders <ArrowRight size={14} /></Link></div>
        <OrdersTable orders={recentOrders} />
      </section>
    </>
  );
}

function OrdersTable({ orders }: { orders: Order[] }) {
  if (!orders.length) return <EmptyState message="Orders will show here when your store receives them." />;
  return (
    <div className="table-scroll">
      <table>
        <thead><tr><th>ORDER</th><th>CUSTOMER</th><th>DATE</th><th>STATUS</th><th className="align-right">TOTAL</th></tr></thead>
        <tbody>{orders.map((order) => <tr key={order.id}>
          <td><span className="order-number">#{order.shopify_order_id.split("/").filter(Boolean).pop() || order.shopify_order_id}</span><small className="cell-subtitle">{order.items.length} {order.items.length === 1 ? "item" : "items"}</small></td>
          <td><span className="customer-email">{order.customer_email || "Guest customer"}</span></td>
          <td className="date-cell">{formatDate(order.created_at)}</td>
          <td><StatusPill status={order.status} /></td>
          <td className="align-right amount-cell">{formatCurrency(order.total, order.currency)}</td>
        </tr>)}</tbody>
      </table>
    </div>
  );
}

function ProductsPage() {
  const query = useQuery({ queryKey: ["products"], queryFn: fetchProducts });
  const [search, setSearch] = useState("");
  const products = (query.data ?? []).filter((product) => `${product.name} ${product.slug} ${product.variants.map((variant) => variant.sku).join(" ")}`.toLowerCase().includes(search.toLowerCase()));
  return (
    <>
      <PageHeading eyebrow="YOUR CATALOG" title="Products" description="A clear view of your product catalog and variant health.">
        <button className="button button-secondary" onClick={() => void query.refetch()}><Activity size={16} /> Refresh</button>
      </PageHeading>
      <section className="panel list-panel">
        <div className="list-toolbar"><div><h2>All products <span className="count-badge">{query.data?.length ?? 0}</span></h2><p>Manage and monitor your synced catalog</p></div><label className="table-search"><Search size={15} /><input value={search} onChange={(event) => setSearch(event.target.value)} placeholder="Search products..." /></label></div>
        {query.isLoading ? <LoadingState /> : query.isError ? <ErrorState onRetry={() => void query.refetch()} /> : products.length === 0 ? <EmptyState message={search ? "No products match your search." : "Your synced products will appear here."} /> : (
          <div className="table-scroll"><table><thead><tr><th>PRODUCT</th><th>STATUS</th><th>VARIANTS</th><th>INVENTORY</th><th className="align-right">PRICE FROM</th></tr></thead>
            <tbody>{products.map((product, index) => <ProductRow key={product.id} product={product} index={index} />)}</tbody></table></div>
        )}
      </section>
    </>
  );
}

function ProductRow({ product, index }: { product: Product; index: number }) {
  const count = product.variants.reduce((total, variant) => total + variant.inventory_quantity, 0);
  const price = product.variants.reduce<number | null>((lowest, variant) => {
    const amount = Number(variant.price);
    return Number.isFinite(amount) && (lowest === null || amount < lowest) ? amount : lowest;
  }, null);
  return <tr>
    <td><div className="product-cell"><ProductGlyph name={product.name} index={index} /><div><strong>{product.name}</strong><small>{product.slug}</small></div></div></td>
    <td><StatusPill status={product.status} /></td>
    <td>{product.variants.length} <span className="muted-text">{product.variants.length === 1 ? "variant" : "variants"}</span></td>
    <td><span className={count <= 0 ? "danger-text" : ""}>{count.toLocaleString()} units</span></td>
    <td className="align-right amount-cell">{price === null ? "—" : formatCurrency(price)}</td>
  </tr>;
}

function InventoryPage() {
  const query = useQuery({ queryKey: ["variants"], queryFn: fetchVariants });
  const products = useQuery({ queryKey: ["products"], queryFn: fetchProducts });
  const [filter, setFilter] = useState("all");
  const [search, setSearch] = useState("");
  const productByVariant = new Map<number, Product>();
  (products.data ?? []).forEach((product) => product.variants.forEach((variant) => productByVariant.set(variant.id, product)));
  const variants = (query.data ?? []).filter((variant) => {
    const matchesFilter = filter === "all" || (filter === "attention" ? variant.stock_status === "low_stock" || variant.stock_status === "out_of_stock" : variant.stock_status === filter);
    const productName = productByVariant.get(variant.id)?.name ?? "";
    return matchesFilter && `${productName} ${variant.title} ${variant.sku}`.toLowerCase().includes(search.toLowerCase());
  });
  return (
    <>
      <PageHeading eyebrow="STOCK CONTROL" title="Inventory" description="Monitor stock levels across your product variants.">
        <button className="button button-secondary" onClick={() => { void query.refetch(); void products.refetch(); }}><Activity size={16} /> Refresh</button>
      </PageHeading>
      <section className="inventory-summary">
        <div className="inventory-stat"><span className="inventory-stat-icon mint"><Package size={17} /></span><div><small>Total units</small><strong>{(query.data ?? []).reduce((total, item) => total + item.inventory_quantity, 0).toLocaleString()}</strong></div></div>
        <div className="inventory-stat"><span className="inventory-stat-icon yellow"><Bell size={17} /></span><div><small>Low stock</small><strong>{(query.data ?? []).filter((item) => item.stock_status === "low_stock").length}</strong></div></div>
        <div className="inventory-stat"><span className="inventory-stat-icon peach"><Package size={17} /></span><div><small>Out of stock</small><strong>{(query.data ?? []).filter((item) => item.stock_status === "out_of_stock").length}</strong></div></div>
      </section>
      <section className="panel list-panel">
        <div className="list-toolbar inventory-toolbar"><div><h2>Stock levels <span className="count-badge">{query.data?.length ?? 0}</span></h2><p>Inventory updates automatically from Shopify</p></div><label className="table-search"><Search size={15} /><input value={search} onChange={(event) => setSearch(event.target.value)} placeholder="Search SKU or product..." /></label></div>
        <div className="filter-tabs" role="tablist" aria-label="Inventory filter">
          {[["all", "All stock"], ["attention", "Needs attention"], ["normal", "Healthy"], ["not_configured", "Not configured"]].map(([value, label]) => <button key={value} className={filter === value ? "filter-tab selected" : "filter-tab"} onClick={() => setFilter(value)}>{label}</button>)}
        </div>
        {query.isLoading || products.isLoading ? <LoadingState /> : query.isError || products.isError ? <ErrorState onRetry={() => { void query.refetch(); void products.refetch(); }} /> : variants.length === 0 ? <EmptyState message="No inventory items match this view." /> : (
          <div className="table-scroll"><table><thead><tr><th>PRODUCT / VARIANT</th><th>SKU</th><th>STOCK STATUS</th><th>ON HAND</th><th className="align-right">MIN. STOCK</th></tr></thead>
            <tbody>{variants.map((variant, index) => {
              const product = productByVariant.get(variant.id);
              return <tr key={variant.id}>
                <td><div className="product-cell"><ProductGlyph name={product?.name ?? variant.title} index={index} /><div><strong>{product?.name ?? "Product"}</strong><small>{variant.title}</small></div></div></td>
                <td className="sku-cell">{variant.sku || "—"}</td>
                <td><span className={`stock-status ${getStockTone(variant)}`}><i />{variant.stock_status.replaceAll("_", " ")}</span></td>
                <td><span className={`inventory-number ${variant.inventory_quantity <= 0 ? "danger-text" : ""}`}>{variant.inventory_quantity.toLocaleString()} <small>units</small></span></td>
                <td className="align-right">{variant.minimum_stock ?? <span className="muted-text">Not set</span>}</td>
              </tr>;
            })}</tbody></table></div>
        )}
      </section>
    </>
  );
}

function OrdersPage() {
  const query = useQuery({ queryKey: ["orders"], queryFn: fetchOrders });
  const [search, setSearch] = useState("");
  const orders = (query.data ?? []).filter((order) => `${order.shopify_order_id} ${order.customer_email} ${order.status}`.toLowerCase().includes(search.toLowerCase()));
  const total = (query.data ?? []).filter((order) => order.status !== "cancelled").reduce((sum, order) => sum + (Number(order.total) || 0), 0);
  const pending = (query.data ?? []).filter((order) => order.status === "pending" || order.status === "confirmed").length;
  return (
    <>
      <PageHeading eyebrow="SALES ACTIVITY" title="Orders" description="Your Shopify orders, synced and organized in one place.">
        <button className="button button-secondary" onClick={() => void query.refetch()}><Activity size={16} /> Refresh</button>
      </PageHeading>
      <section className="orders-overview">
        <div className="orders-overview-card"><small>Total orders</small><strong>{query.data?.length ?? "—"}</strong><span>Synced from Shopify</span></div>
        <div className="orders-overview-card"><small>Awaiting fulfillment</small><strong>{query.isLoading ? "—" : pending}</strong><span>Pending or confirmed</span></div>
        <div className="orders-overview-card"><small>Order value</small><strong>{query.isLoading ? "—" : formatCurrency(total)}</strong><span>Excluding cancelled orders</span></div>
      </section>
      <section className="panel list-panel">
        <div className="list-toolbar"><div><h2>All orders <span className="count-badge">{query.data?.length ?? 0}</span></h2><p>Latest first</p></div><label className="table-search"><Search size={15} /><input value={search} onChange={(event) => setSearch(event.target.value)} placeholder="Search orders..." /></label></div>
        {query.isLoading ? <LoadingState /> : query.isError ? <ErrorState onRetry={() => void query.refetch()} /> : orders.length === 0 ? <EmptyState message={search ? "No orders match your search." : "Your orders will appear here once they sync."} /> : <OrdersTable orders={orders} />}
      </section>
    </>
  );
}

function connectionErrorMessage(error: unknown) {
  if (axios.isAxiosError(error)) {
    const data: unknown = error.response?.data;
    if (data && typeof data === "object" && "error" in data && typeof data.error === "string") return data.error;
    if (!error.response) return "The backend could not be reached. Check that the server is running.";
  }
  return error instanceof Error ? error.message : "The connection test failed.";
}

function SettingsPage() {
  const connection = useMutation({ mutationFn: testShopifyConnection });
  const connectionFailed = connection.isError || connection.data?.connected === false;
  return (
    <>
      <PageHeading eyebrow="PREFERENCES" title="Settings" description="Manage your store connection and workspace preferences." />
      <section className="panel settings-panel">
        <div className="settings-title"><span className="shopify-mark">S</span><div><h2>Shopify connection</h2><p>Check that Shopflow can reach your Shopify store.</p></div></div>
        <div className="settings-connection">
          <span className={`connection-indicator ${connection.data?.connected ? "connected" : connectionFailed ? "disconnected" : ""}`} />
          <div><strong>{connection.isPending ? "Checking connection..." : connection.data?.connected ? "Connected" : connectionFailed ? "Connection failed" : "Not checked yet"}</strong><p>{connection.data?.connected ? "Your Shopify credentials are working." : connection.isError ? connectionErrorMessage(connection.error) : connection.data?.error ?? "Run a connection test to verify your Shopify credentials."}</p></div>
          <button className="button button-primary" disabled={connection.isPending} onClick={() => connection.mutate()}>{connection.isPending ? <span className="button-spinner" /> : <Activity size={16} />}{connection.isPending ? "Testing..." : "Test connection"}</button>
        </div>
        <div className="settings-footnote"><CircleHelp size={15} /><span>Connection credentials are configured on the backend and are never shown here.</span></div>
      </section>
      <section className="panel settings-info"><div className="settings-title"><span className="settings-info-icon"><Command size={17} /></span><div><h2>About your workspace</h2><p>Shopflow medical commerce operations</p></div></div><div className="info-row"><span>Application</span><strong>Shopflow Dashboard</strong></div><div className="info-row"><span>API</span><strong>Connected through your Django backend</strong></div><div className="info-row"><span>Inventory source</span><strong>Shopify sync</strong></div></section>
    </>
  );
}

function NotFoundPage() {
  return <div className="not-found"><span>404</span><h1>Page not found</h1><p>The page you’re looking for doesn’t exist.</p><Link className="button button-primary" to="/">Back to overview</Link></div>;
}

export default function App() {
  return (
    <Routes>
      <Route element={<AppShell />}>
        <Route index element={<DashboardPage />} />
        <Route path="products" element={<ProductsPage />} />
        <Route path="inventory" element={<InventoryPage />} />
        <Route path="orders" element={<OrdersPage />} />
        <Route path="settings" element={<SettingsPage />} />
        <Route path="*" element={<NotFoundPage />} />
      </Route>
    </Routes>
  );
}
