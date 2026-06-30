const money = (amount, currency = "NGN") =>
  `${currency} ${Number(amount || 0).toLocaleString()}`;

const qs = (selector) => document.querySelector(selector);
let selectedPhone = "";
let editingSku = null;
let uploadedImages = [];

function escapeHtml(value) {
  return String(value || "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

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

    qs("#productList").innerHTML = products.map(product => `

        <article class="item">
        ${product.image_urls && product.image_urls.length
        ? `
        <img
          src="${product.image_urls[0]}"
          style="
          width:100%;
          height:220px;
          object-fit:cover;
          border-radius:8px;
          margin-bottom:12px;
          ">
            `
          : ""
        }
            <div class="item-title">

                <span>${escapeHtml(product.name)}</span>

                <span class="pill">${escapeHtml(product.sku)}</span>

            </div>

            <div class="item-meta">

                ${escapeHtml(product.category)}

                •

                ${money(product.price,product.currency)}

                •

                Stock ${product.stock}

                <br>

                Sizes:

                ${escapeHtml((product.sizes||[]).join(", "))}

                <br>

                Colors:

                ${escapeHtml((product.colors||[]).join(", "))}

                <br>

                ${escapeHtml(product.description||"")}

            </div>

            <div style="margin-top:10px;display:flex;gap:10px;">

                <button
                    class="editProduct"
                    data-sku="${product.sku}">
                    Edit
                </button>

                <button
                    class="deleteProduct"
                    data-sku="${product.sku}">
                    Delete
                </button>

            </div>

        </article>

    `).join("");



    document.querySelectorAll(".editProduct").forEach(button=>{

        button.onclick=()=>editProduct(button.dataset.sku);

    });



    document.querySelectorAll(".deleteProduct").forEach(button=>{

        button.onclick=()=>deleteProduct(button.dataset.sku);

    });

}

async function editProduct(sku){

    const products=await api("/api/products");

    const product=products.find(p=>p.sku===sku);

    if(!product) return;

    editingSku=sku;

    const form=qs("#productForm");

    form.sku.value=product.sku;

    form.sku.disabled=true;

    form.name.value=product.name;

    form.category.value=product.category;

    form.price.value=product.price;

    form.stock.value=product.stock;

    form.sizes.value=(product.sizes||[]).join(",");

    form.colors.value=(product.colors||[]).join(",");

    form.image_urls.value=(product.image_urls||[]).join(",");

    form.description.value=product.description||"";

    qs("#productSubmit").textContent="Update Product";

    qs("#cancelEdit").style.display="inline-block";

}

async function deleteProduct(sku){

    if(!confirm(`Delete ${sku}?`)) return;

    await api(`/api/products/${sku}`,{

        method:"DELETE"

    });

    loadProducts();

}

async function loadStories() {
  const stories = await api("/api/stories");
  qs("#storyList").innerHTML = stories
    .map(
      (story) => `
        <article class="item">
          <div class="item-title">
            <span>${escapeHtml(story.title)}</span>
            <span class="pill">${escapeHtml(story.product_sku || "unlinked")}</span>
          </div>
          <div class="item-meta">
            ${escapeHtml(story.caption || "No caption")}<br>
            ${story.product_name ? `Linked product: ${escapeHtml(story.product_name)}` : ""}
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
              <span class="pill">${escapeHtml(order.status)}</span>
            </div>
            <div class="item-meta">
              ${escapeHtml(order.customer_name || order.customer_phone)} - ${money(order.total)} - ${escapeHtml(order.payment_status)}<br>
              ${escapeHtml((order.items || []).map((item) => `${item.quantity || 1}x ${item.name || item.sku}`).join(", "))}
            </div>
          </article>
        `
      )
      .join("") || `<div class="item"><div class="item-meta">No orders yet.</div></div>`;
}

async function loadConversations() {
  const conversations = await api("/api/conversations");
  qs("#conversationList").innerHTML =
    conversations
      .map(
        (thread) => `
          <article class="item conversation-item" data-phone="${thread.phone}">
            <div class="item-title">
            <span>${escapeHtml(thread.name || thread.phone)}</span>
              <span class="pill">${thread.ai_paused ? "human" : "ai"}</span>
            </div>
            <div class="item-meta">
              ${escapeHtml(thread.last_role)}: ${escapeHtml(thread.last_message || "")}<br>
              ${thread.message_count || 0} messages
            </div>
          </article>
        `
      )
      .join("") || `<div class="item"><div class="item-meta">No conversations yet.</div></div>`;

  document.querySelectorAll(".conversation-item").forEach((item) => {
    item.addEventListener("click", () => selectConversation(item.dataset.phone));
  });
}

async function selectConversation(phone) {
  selectedPhone = phone;
  const messages = await api(`/api/conversations/${encodeURIComponent(phone)}`);
  const thread = (await api("/api/conversations")).find((item) => item.phone === phone);
  qs("#conversationDetail").innerHTML = `
    <div class="staff-toolbar">
    <strong>${escapeHtml(phone)}</strong>
      <button type="button" id="pauseAi">${thread && thread.ai_paused ? "AI Paused" : "Pause AI"}</button>
      <button type="button" id="resumeAi">Resume AI</button>
    </div>
    <div class="chat-log staff-log">
      ${messages
        .map(
          (message) => `
            <div class="bubble ${message.role === "customer" ? "customer" : "assistant"}">
              ${escapeHtml(message.role)}: ${escapeHtml(message.message)}
            </div>
          `
        )
        .join("")}
    </div>
  `;
  qs("#pauseAi").addEventListener("click", async () => {
    await api(`/api/conversations/${encodeURIComponent(phone)}/pause`, { method: "POST" });
    await loadConversations();
    await selectConversation(phone);
  });
  qs("#resumeAi").addEventListener("click", async () => {
    await api(`/api/conversations/${encodeURIComponent(phone)}/resume`, { method: "POST" });
    await loadConversations();
    await selectConversation(phone);
  });
}

async function boot() {
  await loadHealth();
  await Promise.all([loadProducts(), loadStories(), loadOrders(), loadConversations()]);

  qs("#refreshProducts").addEventListener("click", loadProducts);
  qs("#refreshOrders").addEventListener("click", loadOrders);
  qs("#refreshConversations").addEventListener("click", loadConversations);
  qs("#productImage").addEventListener(

"change",

async(event)=>{

const file=event.target.files[0];

if(!file) return;

const form=new FormData();

form.append("image",file);

const response=await fetch(

"/api/upload/product",

{

method:"POST",

body:form

}

);

const result=await response.json();

uploadedImages=[result.url];
console.log("Uploaded image:", result.url);
const preview=qs("#imagePreview");

preview.src=result.url;

preview.style.display="block";

}

);
  qs("#productForm").addEventListener("submit", async (event) => {
    event.preventDefault();

const form=event.currentTarget;

const data=formData(form);

const payload={

    ...data,

    price:Number(data.price),

    stock:Number(data.stock),

    sizes:csv(data.sizes),

    colors:csv(data.colors),

    image_urls: uploadedImages

};

if(editingSku){

    await api(

        `/api/products/${editingSku}`,

        {

            method:"PUT",

            body:JSON.stringify(payload)

        }

    );

}else{

    await api(

        "/api/products",

        {

            method:"POST",

            body:JSON.stringify(payload)

        }

    );

}

editingSku=null;

form.reset();

form.sku.disabled=false;

qs("#productSubmit").textContent="Add Product";

qs("#cancelEdit").style.display="none";

loadProducts();
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
      await loadConversations();
    } catch (error) {
      addBubble("assistant", error.message);
    }
  });

  qs("#manualReplyForm").addEventListener("submit", async (event) => {
    event.preventDefault();
    if (!selectedPhone) return;
    const form = event.currentTarget;
    const data = formData(form);
    const message = data.message.trim();
    if (!message) return;
    await api(`/api/conversations/${encodeURIComponent(selectedPhone)}/reply`, {
      method: "POST",
      body: JSON.stringify({ message }),
    });
    form.reset();
    await loadConversations();
    await selectConversation(selectedPhone);
  });
}

boot();
