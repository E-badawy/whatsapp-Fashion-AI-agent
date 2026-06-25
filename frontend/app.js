const money = (amount, currency = "NGN") =>
  `${currency} ${Number(amount || 0).toLocaleString()}`;

const qs = (selector) => document.querySelector(selector);

async function api(path, options = {}) {
  const response = await fetch(path, {
    headers: { "Content-Type": "application/json", ...(options.headers || {}) },
    ...options,
  });
  const data = await response.json().catch(() => ({}));
  if (!response.ok) {
    throw new Error(data.error || "Request failed");
  }
  return data;
}

function csv(value) {
  return String(value || "")
    .split(",")
    .map((item) => item.trim())
    .filter(Boolean);
}

function formData(form) {
  return Object.fromEntries(new FormData(form).entries());
}

function addBubble(role, text) {
  const bubble = document.createElement("div");
  bubble.className = `bubble ${role}`;
  bubble.textContent = text;
  qs("#chatLog").appendChild(bubble);
  qs("#chatLog").scrollTop = qs("#chatLog").scrollHeight;
}

async function loadHealth() {
  try {
    await api("/health");
    qs("#healthStatus").textContent = "API connected";
    qs("#healthStatus").classList.add("ok");
  } catch {
    qs("#healthStatus").textContent = "API offline";
  }
}

async function loadProducts() {
  const products = await api("/api/products");
  qs("#productList").innerHTML = products
    .map(
      (product) => `
        <article class="item">
          <div class="item-title">
            <span>${product.name}</span>
            <span class="pill">${product.sku}</span>
          </div>
          <div class="item-meta">
            ${product.category} · ${money(product.price, product.currency)} · Stock ${product.stock}<br>
            Sizes: ${(product.sizes || []).join(", ") || "None"} · Colors: ${(product.colors || []).join(", ") || "None"}<br>
            ${product.description || ""}
          </div>
        </article>
      `
    )
    .join("");
}

async function loadStories() {
  const stories = await api("/api/stories");
  qs("#storyList").innerHTML = stories
    .map(
      (story) => `
        <article class="item">
          <div class="item-title">
            <span>${story.title}</span>
            <span class="pill">${story.product_sku || "unlinked"}</span>
          </div>
          <div class="item-meta">
            ${story.caption || "No caption"}<br>
            ${story.product_name ? `Linked product: ${story.product_name}` : ""}
          </div>
        </article>
      `
    )
    .join("");
}

async function loadOrders() {
  const orders = await api("/api/orders");
  qs("#orderList").innerHTML =
    orders
      .map(
        (order) => `
          <article class="item">
            <div class="item-title">
              <span>Order #${order.id}</span>
              <span class="pill">${order.status}</span>
            </div>
            <div class="item-meta">
              ${order.customer_name || order.customer_phone} · ${money(order.total)} · ${order.payment_status}<br>
              ${(order.items || []).map((item) => `${item.quantity || 1}x ${item.name || item.sku}`).join(", ")}
            </div>
          </article>
        `
      )
      .join("") || `<div class="item"><div class="item-meta">No orders yet.</div></div>`;
}

async function boot() {
  await loadHealth();
  await Promise.all([loadProducts(), loadStories(), loadOrders()]);

  qs("#refreshProducts").addEventListener("click", loadProducts);
  qs("#refreshOrders").addEventListener("click", loadOrders);

  qs("#productForm").addEventListener("submit", async (event) => {
    event.preventDefault();
    const form = event.currentTarget;
    const data = formData(form);
    await api("/api/products", {
      method: "POST",
      body: JSON.stringify({
        ...data,
        price: Number(data.price),
        stock: Number(data.stock || 0),
        sizes: csv(data.sizes),
        colors: csv(data.colors),
        image_urls: csv(data.image_urls),
      }),
    });
    form.reset();
    await loadProducts();
  });

  qs("#storyForm").addEventListener("submit", async (event) => {
    event.preventDefault();
    const form = event.currentTarget;
    await api("/api/stories", { method: "POST", body: JSON.stringify(formData(form)) });
    form.reset();
    await loadStories();
  });

  qs("#chatForm").addEventListener("submit", async (event) => {
    event.preventDefault();
    const form = event.currentTarget;
    const data = formData(form);
    const message = data.message.trim();
    if (!message) return;
    addBubble("customer", message);
    form.reset();
    try {
      const result = await api("/api/simulate-chat", {
        method: "POST",
        body: JSON.stringify({ phone: "2348000000000", message }),
      });
      addBubble("assistant", result.reply);
    } catch (error) {
      addBubble("assistant", error.message);
    }
  });
}

boot();
