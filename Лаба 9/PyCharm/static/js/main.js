// ===== ДАННЫЕ ТОВАРОВ =====
const PRODUCTS = [
  { id:1, name:"Royal Canin Adult для кошек 2 кг", meta:"Кошки • Royal Canin • 2 кг", price:1890, emoji:"🐱" },
  { id:2, name:"Purina One для собак 3 кг",        meta:"Собаки • Purina • 3 кг",     price:1450, emoji:"🐶" },
  { id:3, name:"Whiskas с курицей 1 кг",            meta:"Кошки • Whiskas • 1 кг",     price:490,  emoji:"🐱" },
  { id:4, name:"Pedigree для щенков 2 кг",          meta:"Собаки • Pedigree • 2 кг",   price:780,  emoji:"🐶" },
  { id:5, name:"Brit Care для грызунов 500 г",      meta:"Грызуны • Brit Care",        price:320,  emoji:"🐹" },
  { id:6, name:"Корм для попугаев Vitakraft 400 г", meta:"Птицы • Vitakraft",          price:280,  emoji:"🐦" },
  { id:7, name:"TetraMin хлопья 100 мл",            meta:"Рыбы • Tetra",               price:350,  emoji:"🐟" },
  { id:8, name:"JBL NovoBel для рыбок 250 мл",      meta:"Рыбы • JBL",                 price:620,  emoji:"🐟" },
];

// Делаем PRODUCTS доступным для product.html
window.PRODUCTS = PRODUCTS;

// ===== КОРЗИНА =====
function getCart() {
  try { return JSON.parse(localStorage.getItem("zoo_cart") || "[]"); }
  catch(e) { return []; }
}
function saveCart(cart) {
  localStorage.setItem("zoo_cart", JSON.stringify(cart));
  updateCartBadge();
}
function updateCartBadge() {
  const total = getCart().reduce((s, i) => s + i.qty, 0);
  document.querySelectorAll(".cart-badge").forEach(b => b.textContent = total);
}
function addToCart(id, btn) {
  const cart = getCart();
  const item = cart.find(i => i.id === id);
  if (item) item.qty++;
  else cart.push({ id: Number(id), qty: 1 });
  saveCart(cart);

  document.querySelectorAll(".cart-badge").forEach(b => {
    b.classList.remove("bounce");
    void b.offsetWidth;
    b.classList.add("bounce");
  });

  if (btn) {
    btn.classList.add("added");
    const old = btn.textContent;
    btn.textContent = "✓ Добавлено";
    setTimeout(() => {
      btn.classList.remove("added");
      btn.textContent = old;
    }, 1200);
  }
}
function removeFromCart(id) {
  saveCart(getCart().filter(i => i.id !== id));
  renderCartPage();
}
function changeQty(id, delta) {
  const cart = getCart();
  const item = cart.find(i => i.id === id);
  if (!item) return;
  item.qty = Math.max(1, item.qty + delta);
  saveCart(cart);
  renderCartPage();
}

// ===== РЕНДЕР ТОВАРОВ =====
function renderProducts(list, targetId = "products") {
  const root = document.getElementById(targetId);
  if (!root) return;
  if (!list.length) {
    root.innerHTML = `<p style="grid-column:1/-1;text-align:center;color:#757575;padding:40px 0;">Товары не найдены</p>`;
    return;
  }
  root.innerHTML = list.map(p => `
    <article class="product-card">
      <a href="/product?id=${p.id}">
        <div class="product-img">${p.emoji}</div>
      </a>
      <div class="product-body">
        <a href="/product?id=${p.id}">
          <div class="product-name">${p.name}</div>
        </a>
        <div class="product-meta">${p.meta}</div>
        <div class="product-price">${p.price.toLocaleString('ru-RU')} ₽</div>
        <button class="btn-cart" data-id="${p.id}">В корзину</button>
      </div>
    </article>
  `).join("");
}

// ===== РЕНДЕР КОРЗИНЫ =====
function renderCartPage() {
  const root = document.getElementById("cart-list");
  if (!root) return;
  const cart = getCart();

  if (!cart.length) {
    root.innerHTML = `
      <div style="text-align:center;padding:60px 20px;">
        <div style="font-size:64px;">🛒</div>
        <h2 style="margin:16px 0;">Корзина пуста</h2>
        <p style="color:#757575;margin-bottom:20px;">Добавьте товары из каталога</p>
        <a href="/catalog" class="btn btn-primary">Перейти в каталог</a>
      </div>`;
    updateSummary(0, 0);
    return;
  }

  root.innerHTML = cart.map(item => {
    const p = PRODUCTS.find(x => x.id === item.id) || { name:"Товар", meta:"", price:0, emoji:"📦" };
    const sum = p.price * item.qty;
    return `
      <div class="cart-item">
        <div class="cart-item-img">${p.emoji}</div>
        <div class="cart-item-info">
          <h3>${p.name}</h3>
          <p>${p.meta}</p>
        </div>
        <div class="qty">
          <button onclick="changeQty(${item.id}, -1)">−</button>
          <input type="text" value="${item.qty}" readonly>
          <button onclick="changeQty(${item.id}, 1)">+</button>
        </div>
        <div class="cart-item-price">${sum.toLocaleString('ru-RU')} ₽</div>
        <button class="remove-btn" onclick="removeFromCart(${item.id})" title="Удалить">🗑</button>
      </div>
    `;
  }).join("");

  const total = cart.reduce((s, i) => {
    const p = PRODUCTS.find(x => x.id === i.id);
    return s + (p ? p.price * i.qty : 0);
  }, 0);
  updateSummary(cart.reduce((s, i) => s + i.qty, 0), total);
}
function updateSummary(count, total) {
  const c = document.getElementById("summary-count");
  const t = document.getElementById("summary-total");
  const t2 = document.getElementById("summary-total-2");
  if (c) c.textContent = count + " шт.";
  if (t) t.textContent = total.toLocaleString('ru-RU') + " ₽";
  if (t2) t2.textContent = total.toLocaleString('ru-RU') + " ₽";
}

// ===== ФОРМА ВХОДА =====
function initLoginForm() {
  const form = document.getElementById("loginForm");
  if (!form) return;
  form.addEventListener("submit", e => {
    e.preventDefault();
    const email = form.email.value.trim();
    const password = form.password.value;
    if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) {
      alert("Введите корректный email");
      return;
    }
    if (password.length < 6) {
      alert("Пароль должен быть не менее 6 символов");
      return;
    }
    alert("Успешный вход! (демо)");
  });
}

// ===== ФОРМА ЗАКАЗА =====
function initCheckoutForm() {
  const form = document.getElementById("checkoutForm");
  if (!form) return;
  form.addEventListener("submit", e => {
    e.preventDefault();
    alert("Заказ оформлен! (демо)");
    localStorage.removeItem("zoo_cart");
    updateCartBadge();
    window.location.href = "/";
  });
}

// ===== СТРАНИЦА ТОВАРА =====
function initProductPage() {
  const btn = document.getElementById("add-to-cart");
  if (!btn) return;
  btn.addEventListener("click", () => {
    const id = Number(btn.dataset.id);
    addToCart(id, btn);
  });
}

// ===== ЗАПУСК =====
document.addEventListener("DOMContentLoaded", () => {
  updateCartBadge();

  // Товары только на главной/каталоге
  if (document.getElementById("products")) {
    renderProducts(PRODUCTS);
  }

  renderCartPage();
  initLoginForm();
  initCheckoutForm();
  initProductPage();

  document.addEventListener("click", e => {
    if (e.target.classList && e.target.classList.contains("btn-cart")) {
      addToCart(Number(e.target.dataset.id), e.target);
    }
  });
});