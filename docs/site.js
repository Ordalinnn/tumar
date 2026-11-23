/* Общий скрипт сайта: амулет, появление секций, прогресс чтения,
   копирование команд и тренажёр правила. Строки — на двух языках. */
(() => {
  const calm = matchMedia("(prefers-reduced-motion:reduce)").matches;
  const sy = () => (document.scrollingElement || document.documentElement).scrollTop;
  const lang = document.documentElement.lang === "kk" ? "kk" : "ru";
  const T = {
    ru: {
      zero: "Сигналов нет — обычная операция, радар молчит.",
      one: "Один сигнал — молчим: слишком легко ошибиться на одном совпадении.",
      many: "Два сигнала и больше — предупреждаем и показываем, что именно заметили.",
      needCond: " Для паузы нужно опустошение вместе с наживкой или общим получателем — либо 3+ сигнала.",
      needConsent: " Условие для паузы выполнено, но режим защиты не включён: без согласия клиента паузы нет.",
      consented: " Режим защиты включён: заявка на депозит или кредит подождёт.",
      copy: "Скопировать", copied: "Скопировано", failed: "Не вышло",
    },
    kk: {
      zero: "Белгілер жоқ — қарапайым операция, радар үндемейді.",
      one: "Бір белгі — үндемейміз: бір сәйкестікке алдану оңай.",
      many: "Екі белгі және одан көп — ескертеміз және нені байқағанымызды көрсетеміз.",
      needCond: " Кідірту үшін босату белгісі наживкамен немесе ортақ алушымен бірге болуы керек — немесе 3+ белгі.",
      needConsent: " Кідірту шарты орындалды, бірақ қорғау режимі қосылмаған: клиент келісімінсіз кідірту жоқ.",
      consented: " Қорғау режимі қосылған: депозит немесе кредит өтінімі кідіртіледі.",
      copy: "Көшіру", copied: "Көшірілді", failed: "Шықпады",
    },
  }[lang];

  const AMULET = `
<svg viewBox="0 0 300 330" role="presentation">
  <defs>
    <pattern id="pd" width="7" height="7" patternUnits="userSpaceOnUse"><circle cx="3.5" cy="3.5" r="1.5" fill="#ff5a3c"/></pattern>
    <pattern id="pw" width="7" height="7" patternUnits="userSpaceOnUse"><circle cx="3.5" cy="3.5" r="1.3" fill="#e6ebf5"/></pattern>
  </defs>
  <g fill="none" stroke="#e6ebf5" stroke-width="1.9" stroke-linecap="round" stroke-dasharray="0 6.4">
    <path d="M150 0v34"/>
    <path d="M150 34 282 258H18Z"/>
    <path d="M150 62 258 246H42Z" opacity=".55"/>
  </g>
  <path d="M150 132 208 238H92Z" fill="url(#pd)" stroke="#ffc45c" stroke-width="1.6" stroke-dasharray="0 5.4" stroke-linecap="round"/>
  <g fill="none" stroke="#ffc45c" stroke-width="2.4" stroke-linecap="round" stroke-dasharray="0 4.6">
    <path d="M120 210c-16 0-22-10-18-19 4-8 16-6 15 3-1 8-13 9-17 2"/>
    <path d="M180 210c16 0 22-10 18-19-4-8-16-6-15 3 1 8 13 9 17 2"/>
  </g>
  <g fill="none" stroke="#e6ebf5" stroke-width="1.7" stroke-linecap="round" stroke-dasharray="0 6">
    <path d="M96 258v34M150 258v52M204 258v40"/>
  </g>
  <g fill="url(#pw)" stroke="#e6ebf5" stroke-width="1.6" stroke-dasharray="0 5" stroke-linecap="round">
    <circle cx="96" cy="308" r="14"/><circle cx="150" cy="326" r="14"/><circle cx="204" cy="314" r="14"/>
  </g>
  <g fill="#e6ebf5" opacity=".5">
    <circle cx="150" cy="46" r="2"/><circle cx="266" cy="246" r="2"/><circle cx="34" cy="246" r="2"/>
  </g>
</svg>`;
  document.querySelectorAll("#amulet,#amulet2").forEach(el => (el.innerHTML = AMULET));

  // страховка: если наблюдатель не сработал (печать, старый браузер) — показываем всё
  setTimeout(() => document.querySelectorAll(".rv:not(.in)").forEach(e => {
    if (e.getBoundingClientRect().top < innerHeight * 1.2) e.classList.add("in");
  }), 3000);
  addEventListener("beforeprint", () => document.querySelectorAll(".rv").forEach(e => e.classList.add("in")));

  // dots в карточках тестов: data-dots="всего:включено"
  document.querySelectorAll(".dots").forEach(box => {
    const [total, on] = box.dataset.dots.split(":").map(Number);
    box.innerHTML = Array.from({ length: total }, (_, i) => `<i class="${i < on ? "on" : ""}" aria-hidden="true"></i>`).join("");
  });

  // появление секций
  // Прячем секции только когда JS работает; через 2,5 с показываем всё, что вдруг не проявилось.
  document.documentElement.classList.add("js");
  setTimeout(() => document.querySelectorAll(".rv:not(.in)").forEach(el => {
    if (el.getBoundingClientRect().top < innerHeight) el.classList.add("in");
  }), 2500);
  const io = new IntersectionObserver(es => es.forEach(e => {
    if (e.isIntersecting) { e.target.classList.add("in"); io.unobserve(e.target); }
  }), { rootMargin: "0px 0px -12% 0px", threshold: .12 });
  document.querySelectorAll(".rv").forEach(el => io.observe(el));
  const bars = document.getElementById("bars");
  if (bars) new IntersectionObserver(es => es.forEach(e => {
    if (e.isIntersecting) bars.classList.add("in");
  }), { threshold: .3 }).observe(bars);

  // шапка и прогресс чтения
  const hd = document.getElementById("hd"), pg = document.getElementById("pg");
  const onScroll = () => {
    if (hd) hd.classList.toggle("stuck", sy() > 12);
    if (pg) {
      const h = document.documentElement.scrollHeight - innerHeight;
      pg.style.width = (h > 0 ? Math.min(1, sy() / h) * 100 : 0) + "%";
    }
  };
  onScroll(); addEventListener("scroll", onScroll, { passive: true });
  addEventListener("resize", onScroll, { passive: true });

  // мягкий параллакс карточки
  const card = document.getElementById("card");
  if (!calm && card && matchMedia("(hover:hover)").matches) {
    addEventListener("pointermove", e => {
      const x = e.clientX / innerWidth - .5, y = e.clientY / innerHeight - .5;
      card.style.transform = `translate3d(${x * 10}px,${y * 8}px,0) rotate(${x * 1.6}deg)`;
    }, { passive: true });
  }

  // копировать команды
  const copy = document.getElementById("copy");
  if (copy) copy.addEventListener("click", async () => {
    const text = "python -m pip install -r requirements.txt\nstreamlit run app.py\npytest -q";
    try { await navigator.clipboard.writeText(text); copy.textContent = T.copied; }
    catch { copy.textContent = T.failed; }
    setTimeout(() => (copy.textContent = T.copy), 1600);
  });


  // мобильное меню
  const burger = document.getElementById("burger");
  const navEl = document.getElementById("nav");
  if (burger && navEl) {
    const setMenu = open => {
      navEl.classList.toggle("open", open);
      burger.setAttribute("aria-expanded", String(open));
    };
    burger.addEventListener("click", () => setMenu(!navEl.classList.contains("open")));
    navEl.addEventListener("click", e => { if (e.target.closest("a")) setMenu(false); });
    addEventListener("keydown", e => { if (e.key === "Escape") setMenu(false); });
  }

  // кнопка «наверх»
  const up = document.getElementById("up");
  if (up) {
    const toggleUp = () => up.classList.toggle("show", sy() > innerHeight * 1.2);
    toggleUp(); addEventListener("scroll", toggleUp, { passive: true });
    up.addEventListener("click", () => scrollTo({ top: 0, behavior: calm ? "auto" : "smooth" }));
  }

  // подсветка текущего раздела в шапке
  const navLinks = [...document.querySelectorAll(".nav a")];
  if (navLinks.length) {
    const targets = navLinks.map(a => document.querySelector(a.getAttribute("href"))).filter(Boolean);
    const spy = new IntersectionObserver(es => es.forEach(e => {
      if (!e.isIntersecting) return;
      navLinks.forEach(a => a.classList.toggle("on", a.getAttribute("href") === "#" + e.target.id));
    }), { rootMargin: "-45% 0px -50% 0px" });
    targets.forEach(t => spy.observe(t));
  }

  // лайтбокс для скриншотов приложения
  const lb = document.getElementById("lb");
  const shots = [...document.querySelectorAll(".shot img")];
  if (lb && shots.length) {
    const big = lb.querySelector("img");
    const open = img => {
      big.src = img.src; big.alt = img.alt;
      if (typeof lb.showModal === "function") lb.showModal(); else lb.setAttribute("open", "");
    };
    shots.forEach(img => {
      img.tabIndex = 0; img.setAttribute("role", "button");
      img.addEventListener("click", () => open(img));
      img.addEventListener("keydown", e => {
        if (e.key === "Enter" || e.key === " ") { e.preventDefault(); open(img); }
      });
    });
    lb.addEventListener("click", e => {
      if (e.target === lb || e.target.classList.contains("lb-x")) lb.close();
    });
  }

  // тренажёр правила: 0–1 молчим, 2+ предупреждаем, пауза только по согласию
  const chips = [...document.querySelectorAll(".chip")];
  const cnt = document.getElementById("cnt");
  if (!chips.length || !cnt) return;
  const on = new Set();
  const warnv = document.getElementById("warnv");
  const pausev = document.getElementById("pausev");
  const why = document.getElementById("why");
  const prot = document.getElementById("prot");

  const paint = (el, text, cls) => { el.textContent = text; el.className = cls || ""; };

  function render() {
    const n = on.size;
    const opus = on.has("opus");
    const bait = on.has("nazh") || on.has("obsh");
    cnt.textContent = n;
    const warn = n >= 2;
    paint(warnv, warn ? (lang === "kk" ? "иә" : "да") : (lang === "kk" ? "жоқ" : "нет"), warn ? "yes" : "no");
    const cond = n >= 3 || (opus && bait);
    const pause = prot.checked && cond;
    paint(pausev, pause ? (lang === "kk" ? "иә" : "да") : (lang === "kk" ? "жоқ" : "нет"), pause ? "pz" : "no");
    let s;
    if (!n) s = T.zero;
    else if (n === 1) s = T.one;
    else s = T.many;
    if (!cond) s += T.needCond;
    else if (!prot.checked) s += T.needConsent;
    else s += T.consented;
    why.textContent = s;
  }

  chips.forEach(c => c.addEventListener("click", () => {
    const k = c.dataset.sig;
    if (on.has(k)) { on.delete(k); c.setAttribute("aria-pressed", "false"); }
    else { on.add(k); c.setAttribute("aria-pressed", "true"); }
    render();
  }));
  prot.addEventListener("change", render);
  render();
})();
