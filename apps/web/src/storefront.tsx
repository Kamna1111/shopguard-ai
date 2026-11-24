import { useEffect, useState } from "react";
import { AITools } from "./ai-tools";

type Product = {
  id: number;
  name: string;
  description: string;
  category: string;
  price: string;
  available_quantity: number;
};
type CartLine = { product_id: number; name: string; quantity: number; line_total: string };
type Order = {
  id: number;
  order_number: string;
  status: string;
  total: string;
  items: Array<{ product_name: string; quantity: number }>;
};
type ApiError = { detail?: string };

async function api<T>(path: string, token?: string, init: RequestInit = {}): Promise<T> {
  const response = await fetch(`/api${path}`, {
    ...init,
    headers: {
      ...(init.body ? { "Content-Type": "application/json" } : {}),
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      ...init.headers,
    },
  });
  if (!response.ok) {
    const body = (await response.json().catch(() => ({}))) as ApiError;
    throw new Error(body.detail ?? `Request failed (${response.status})`);
  }
  if (response.status === 204) return undefined as T;
  return (await response.json()) as T;
}

function money(value: string): string {
  return `$${Number(value).toFixed(2)}`;
}

export function Storefront() {
  const [products, setProducts] = useState<Product[]>([]);
  const [query, setQuery] = useState("");
  const [category, setCategory] = useState("");
  const [sort, setSort] = useState("name");
  const [token, setToken] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [cart, setCart] = useState<CartLine[]>([]);
  const [orders, setOrders] = useState<Order[]>([]);
  const [address, setAddress] = useState("123 Demo Road, Sample Town");
  const [coupon, setCoupon] = useState("WELCOME10");
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");

  async function loadProducts(search = query, categoryFilter = category, sortOrder = sort) {
    const params = new URLSearchParams();
    if (search.trim()) params.set("q", search.trim());
    if (categoryFilter) params.set("category", categoryFilter);
    if (sortOrder !== "name") params.set("sort", sortOrder);
    setProducts(await api<Product[]>(`/products${params.size ? `?${params}` : ""}`));
  }

  async function loadCart(accessToken = token) {
    const result = await api<{ items: CartLine[] }>("/cart", accessToken);
    setCart(result.items);
  }

  async function loadOrders(accessToken = token) {
    setOrders(await api<Order[]>("/orders", accessToken));
  }

  useEffect(() => {
    void loadProducts().catch((reason: Error) => setError(reason.message));
  }, []);

  async function authenticate(action: "register" | "login") {
    setError("");
    setMessage("");
    try {
      if (action === "register") {
        await api("/auth/register", undefined, {
          method: "POST",
          body: JSON.stringify({ email, password }),
        });
      }
      const result = await api<{ access_token: string }>("/auth/login", undefined, {
        method: "POST",
        body: JSON.stringify({ email, password }),
      });
      setToken(result.access_token);
      setMessage("You are signed in.");
      await Promise.all([loadCart(result.access_token), loadOrders(result.access_token)]);
    } catch (reason) {
      setError((reason as Error).message);
    }
  }

  async function addToCart(productId: number) {
    if (!token) {
      setError("Sign in before adding items to your basket.");
      return;
    }
    setError("");
    try {
      await api("/cart/items", token, {
        method: "POST",
        body: JSON.stringify({ product_id: productId, quantity: 1 }),
      });
      await loadCart();
      setMessage("Item added to your basket.");
    } catch (reason) {
      setError((reason as Error).message);
    }
  }

  async function changeCartQuantity(productId: number, quantity: number) {
    setError("");
    try {
      if (quantity < 1) {
        await api(`/cart/items/${productId}`, token, { method: "DELETE" });
      } else {
        await api(`/cart/items/${productId}`, token, {
          method: "PATCH",
          body: JSON.stringify({ quantity }),
        });
      }
      await loadCart();
    } catch (reason) {
      setError((reason as Error).message);
    }
  }

  async function checkout() {
    setError("");
    setMessage("");
    try {
      const order = await api<Order>("/orders", token, {
        method: "POST",
        body: JSON.stringify({
          shipping_address: address,
          coupon_code: coupon || null,
          idempotency_key: crypto.randomUUID(),
        }),
      });
      setMessage(`Order ${order.order_number} placed successfully.`);
      await Promise.all([loadCart(), loadOrders(), loadProducts()]);
    } catch (reason) {
      setError((reason as Error).message);
    }
  }

  async function cancelOrder(orderId: number) {
    setError("");
    try {
      await api(`/orders/${orderId}/cancel`, token, { method: "POST" });
      setMessage("Order cancelled and its items returned to stock.");
      await Promise.all([loadOrders(), loadProducts()]);
    } catch (reason) {
      setError((reason as Error).message);
    }
  }

  function signOut() {
    setToken("");
    setCart([]);
    setOrders([]);
    setMessage("You are signed out.");
  }

  return (
    <main className="page-shell">
      <header className="topbar">
        <a className="brand" href="#top" aria-label="ShopGuard Market home">
          <span className="brand-mark">S</span> ShopGuard <span>Market</span>
        </a>
        <nav aria-label="Main navigation">
          <a href="#catalog">Shop</a>
          <a href="#quality">Quality dashboard</a>
          <a href="#basket">Basket <span data-testid="basket-count">{cart.length}</span></a>
          {token ? <button className="sign-out" onClick={signOut}>Sign out</button> : <a href="#account">Sign in</a>}
        </nav>
      </header>

      <section className="hero" id="top">
        <div className="hero-copy">
          <p className="eyebrow">A little better, every day</p>
          <h1>Good things for<br /><em>everyday living.</em></h1>
          <p>Thoughtfully picked essentials, ready for your next favorite moment.</p>
          <a className="button button-dark" href="#catalog">Explore the shop <span>↗</span></a>
        </div>
        <div className="hero-art" aria-label="Colorful abstract shopping illustration">
          <div className="sun"></div><div className="art-bottle"></div><div className="art-cup"></div>
          <span className="art-note">made for<br />your everyday</span>
        </div>
        <div className="hero-foot"><span>Small joys, delivered.</span><span>Scroll to discover ↓</span></div>
      </section>

      <section className="catalog section" id="catalog">
        <div className="section-heading">
          <div><p className="eyebrow">The collection</p><h2>Find your next <em>favorite.</em></h2></div>
          <div className="catalog-controls">
          <label className="filter-control">Category <select aria-label="Filter by category" value={category} onChange={(event) => { const next = event.target.value; setCategory(next); void loadProducts(query, next, sort); }}><option value="">All categories</option><option value="Home">Home</option><option value="Outdoor">Outdoor</option></select></label>
          <label className="filter-control">Sort by <select aria-label="Sort products" value={sort} onChange={(event) => { const next = event.target.value; setSort(next); void loadProducts(query, category, next); }}><option value="name">Name</option><option value="price_asc">Price: low to high</option><option value="price_desc">Price: high to low</option></select></label>
          <form className="search" onSubmit={(event) => { event.preventDefault(); void loadProducts(); }}>
            <label className="sr-only" htmlFor="product-search">Search products</label>
            <input id="product-search" aria-label="Search products" placeholder="Search the collection" value={query} onChange={(event) => setQuery(event.target.value)} />
            <button aria-label="Search" type="submit">⌕</button>
          </form>
          </div>
        </div>
        <div className="product-grid" data-testid="product-list">
          {products.map((product, index) => (
            <article className="product-card" key={product.id}>
              <div className={`product-art art-${index % 3}`}><span>{product.category}</span><b>{product.name.slice(0, 1)}</b></div>
              <div className="product-info"><div><h3>{product.name}</h3><p>{product.description}</p></div><strong>{money(product.price)}</strong></div>
              <div className="product-footer"><span>{product.available_quantity > 0 ? `${product.available_quantity} in stock` : "Sold out"}</span><button className="add-button" aria-label={`Add ${product.name} to basket`} disabled={product.available_quantity < 1} onClick={() => void addToCart(product.id)}>Add to basket <span>+</span></button></div>
            </article>
          ))}
          {products.length === 0 && <p className="empty-state">No products found. Try another search.</p>}
        </div>
      </section>

      <section className="shop-lower section">
        <section className="account-panel panel" id="account">
          <p className="eyebrow">Your account</p><h2>{token ? "Welcome back." : "A good day to sign in."}</h2>
          {token ? <p data-testid="signed-in-state">You’re signed in and ready to shop.</p> : <form onSubmit={(event) => { event.preventDefault(); void authenticate("login"); }}>
            <label>Email address<input type="email" autoComplete="email" value={email} onChange={(event) => setEmail(event.target.value)} required /></label>
            <label>Password<input type="password" autoComplete="current-password" value={password} onChange={(event) => setPassword(event.target.value)} required /></label>
            <div className="form-actions"><button className="button button-dark" type="submit">Sign in</button><button className="text-button" type="button" onClick={() => void authenticate("register")}>Create account</button></div>
          </form>}
          <p className="microcopy">New here? Enter your email and password, then choose Create account.</p>
        </section>

        <section className="basket-panel panel" id="basket">
          <div className="panel-title"><div><p className="eyebrow">Your edit</p><h2>Your basket<span className="basket-dot">.</span></h2></div><span className="count-pill">{cart.length} items</span></div>
          {!token && <p className="muted">Sign in to save items in your basket.</p>}
          {token && cart.length === 0 && <p className="muted" data-testid="empty-basket">Your basket is empty. Find something you love above.</p>}
          {cart.map((line) => <div className="basket-line" key={line.product_id}><span>{line.name} <small>× {line.quantity}</small><span className="quantity-actions"><button aria-label={`Decrease ${line.name} quantity`} onClick={() => void changeCartQuantity(line.product_id, line.quantity - 1)}>−</button><button aria-label={`Increase ${line.name} quantity`} onClick={() => void changeCartQuantity(line.product_id, line.quantity + 1)}>+</button></span></span><strong>{money(line.line_total)}</strong></div>)}
          {cart.length > 0 && <>
            <label className="checkout-label">Delivery address<input aria-label="Delivery address" value={address} onChange={(event) => setAddress(event.target.value)} /></label>
            <label className="checkout-label">Discount code<input aria-label="Discount code" value={coupon} onChange={(event) => setCoupon(event.target.value)} /></label>
            <button className="button button-dark checkout-button" onClick={() => void checkout()}>Continue to checkout <span>→</span></button>
          </>}
        </section>
      </section>

      {token && <section className="orders-section section" id="orders"><div className="section-heading"><div><p className="eyebrow">The good things keep coming</p><h2>Your recent <em>orders.</em></h2></div></div>
        {orders.length === 0 ? <p className="muted">Your orders will appear here.</p> : orders.map((order) => <article className="order-card" key={order.id} data-testid="order-card"><div><p className="eyebrow">{order.order_number}</p><strong>{order.items.map((item) => `${item.product_name} × ${item.quantity}`).join(", ")}</strong></div><span className={`status status-${order.status}`}>{order.status}</span><strong>{money(order.total)}</strong>{order.status === "placed" && <button className="text-button" onClick={() => void cancelOrder(order.id)}>Cancel order</button>}</article>)}
      </section>}

      {token && <AITools token={token} />}

      {(error || message) && <div className={`notice ${error ? "notice-error" : "notice-success"}`} role={error ? "alert" : "status"}>{error || message}<button aria-label="Dismiss message" onClick={() => { setError(""); setMessage(""); }}>×</button></div>}
      <footer className="footer"><a className="brand" href="#top"><span className="brand-mark">S</span> ShopGuard <span>Market</span></a><span>A practice shop for quality engineering.</span><span>Payments are simulated · No card details collected</span></footer>
    </main>
  );
}
