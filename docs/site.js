/* Общий скрипт сайта: амулет из точек, прогресс чтения,
   копирование команд и тренажёр правила. Строки — на двух языках. */
(() => {
  const motion = matchMedia("(prefers-reduced-motion:reduce)");
  let calm = motion.matches;
  motion.addEventListener?.("change", e => (calm = e.matches));
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

  /* ---------- амулет из точек: та же техника, что в slides.html ----------
     Это украшение: любая ошибка здесь не должна ломать меню, копирование и тренажёр. */
  try {
  const COL = ["230,235,245", "255,90,60", "69,214,200", "255,196,92", "150,160,205"]; // серебро, сердолик, бирюза, янтарь, пыль
  let seed = 7;
  const R = () => ((seed = (seed * 1664525 + 1013904223) >>> 0) / 4294967296);
  const P = (x, y, c = 0, r = 2.2, a = 1) => ({ x, y, c, r, a });
  const line = (x1, y1, x2, y2, n, c, r) => Array.from({ length: n }, (_, i) => { const t = n > 1 ? i / (n - 1) : 0; return P(x1 + (x2 - x1) * t, y1 + (y2 - y1) * t, c, r); });
  const disc = (x, y, rad, n, c, r) => Array.from({ length: n }, (_, i) => { const q = Math.sqrt((i + .5) / n) * rad, t = i * 2.39996; return P(x + Math.cos(t) * q, y + Math.sin(t) * q, c, r); });
  function tri(ax, ay, bx, by, cx, cy, n, c, r) { const o = []; for (let i = 0; i < n; i++) { let u = (.5 + i * .7548776662) % 1, v = (.5 + i * .569840291) % 1; if (u + v > 1) { u = 1 - u; v = 1 - v; } o.push(P(ax + (bx - ax) * u + (cx - ax) * v, ay + (by - ay) * u + (cy - ay) * v, c, r)); } return o; }
  // точки вдоль SVG-пути; путь временно кладём в скрытый <svg> в документе — так измерение работает во всех браузерах
  const svgNS = "http://www.w3.org/2000/svg";
  const CURL = (() => {
    const host = document.createElementNS(svgNS, "svg"), e = document.createElementNS(svgNS, "path");
    host.setAttribute("aria-hidden", "true"); host.setAttribute("width", "0"); host.setAttribute("height", "0");
    host.style.cssText = "position:absolute;left:-9999px;top:0;width:0;height:0;overflow:hidden";
    e.setAttribute("d", "M0 0 c-30 40 -96 32 -92 -16 c4 -36 56 -34 50 2 c-3 16 -24 14 -22 0");
    host.append(e); document.body.append(host);
    const L = e.getTotalLength(), n = 100;
    const pts = Array.from({ length: n }, (_, i) => { const p = e.getPointAtLength(L * i / (n - 1)); return { x: p.x, y: p.y }; });
    host.remove(); return pts;
  })();
  // amulet() перенесён из слайдов: треугольник, сердоликовое ядро, завитки и пять подвесок
  function amulet(cx, top, k) {
    const X = x => cx + (x - 350) * k, Y = y => top + y * k; let o = [];
    for (const g of [0, 9]) { o.push(...line(X(350), Y(92 + g * 1.6), X(684 - g * 1.9), Y(560 - g), 150, 0, 2.3), ...line(X(350), Y(92 + g * 1.6), X(16 + g * 1.9), Y(560 - g), 150, 0, 2.3), ...line(X(16 + g * 1.9), Y(560 - g), X(684 - g * 1.9), Y(560 - g), 170, 0, 2.3)); }
    for (let i = 1; i < 20; i++) { const a = i / 20; o.push(...disc(X(350 - 304 * a), Y(160 + 366 * a), 5.5 * k, 6, 0, 2), ...disc(X(350 + 304 * a), Y(160 + 366 * a), 5.5 * k, 6, 0, 2), ...disc(X(46 + 608 * a), Y(526), 5.5 * k, 6, 0, 2)); }
    o.push(...line(X(350), Y(226), X(452), Y(412), 60, 3, 2.4), ...line(X(350), Y(226), X(248), Y(412), 60, 3, 2.4), ...line(X(248), Y(412), X(452), Y(412), 60, 3, 2.4), ...tri(X(350), Y(244), X(438), Y(402), X(262), Y(402), 330, 1, 2.8));
    for (const m of [1, -1]) o.push(...CURL.map(p => P(X(350 + p.x * m), Y(486 + p.y), 3, 2.2)));
    o.push(...line(X(350), Y(-10), X(350), Y(88), 22, 0, 2.2));
    [[70, 120], [210, 150], [350, 184], [490, 150], [630, 120]].forEach(([x, l]) => {
      o.push(...line(X(x), Y(566), X(x), Y(560 + l), Math.round(l / 7), 0, 1.9)); const y = 560 + l;
      o.push(...line(X(x), Y(y), X(x - 25), Y(y + 44), 9, 0, 2.2), ...line(X(x), Y(y), X(x + 25), Y(y + 44), 9, 0, 2.2), ...tri(X(x), Y(y + 8), X(x - 19), Y(y + 42), X(x + 19), Y(y + 42), 16, 0, 2.2), ...disc(X(x), Y(y + 58), 30 * k, 96, 0, 2.2));
    });
    return o;
  }
  // рассыпающийся амулет со слайда «Чего Тұмар пока не умеет»
  const fray = (cx, top, k) => amulet(cx, top, k).map(p => {
    const d = (p.x - cx) * .62 + (p.y - top - 400 * k) * .78; if (d < 60 * k) return p;
    const q = (d - 60 * k) / (300 * k);
    return { ...p, x: p.x + q * (R() * 300 - 60) * k, y: p.y + q * (R() * 300 - 40) * k, a: Math.max(.25, 1 - q * .6) };
  });
  // точка — радиальный спрайт, как в слайдах
  const SP = COL.map(c => {
    const k = document.createElement("canvas"); k.width = k.height = 48; const g = k.getContext("2d"), q = g.createRadialGradient(24, 24, 0, 24, 24, 24);
    q.addColorStop(0, `rgba(${c},1)`); q.addColorStop(.3, `rgba(${c},.95)`); q.addColorStop(.42, `rgba(${c},.28)`); q.addColorStop(1, `rgba(${c},0)`);
    g.fillStyle = q; g.fillRect(0, 0, 48, 48); return k;
  });
  const dot = (g, x, y, c, r, a) => { g.globalAlpha = a; const z = r * 5.2; g.drawImage(SP[c], x - z / 2, y - z / 2, z, z); };
  const AW = 700, AH = 860; // поле амулета в его собственных координатах
  const fit = (w, h) => Math.min(w / AW, h / AH);
  const sizeCanvas = (cv, w, h) => { const q = Math.min(2, devicePixelRatio || 1); cv.width = Math.round(w * q); cv.height = Math.round(h * q); const g = cv.getContext("2d"); g.setTransform(q, 0, 0, q, 0, 0); return g; };
  // радиусы точек растут вместе с амулетом, но не мельче читаемого
  const scaleR = (pts, k) => { const m = Math.max(.42, Math.min(1, k * 1.05)); pts.forEach(p => (p.r *= m)); return pts; };
  // перестраиваем только когда размер действительно изменился (скрытие адресной строки — не повод)
  const onResize = (fn, key) => { let rt, was = key(); addEventListener("resize", () => { clearTimeout(rt); rt = setTimeout(() => { const now = key(); if (now !== was) { was = now; fn(); } }, 150); }, { passive: true }); };

  // статичные амулеты: в финале — целый, в «ограничениях» — рассыпающийся
  function still(box, make) {
    if (!box) return;
    const cv = document.createElement("canvas"); box.append(cv);
    const size = () => box.clientWidth + "x" + box.clientHeight;
    const draw = () => {
      const w = box.clientWidth, h = box.clientHeight; if (!w || !h) return;
      const g = sizeCanvas(cv, w, h); seed = 11; g.clearRect(0, 0, w, h);
      make(w, h).forEach(p => dot(g, p.x, p.y, p.c, p.r, p.a));
    };
    draw(); onResize(draw, size);
  }
  still(document.getElementById("amulet2"), (w, h) => { const k = fit(w, h); return scaleR(amulet(w / 2, (h - AH * k) / 2 + 10 * k, k), k); });
  still(document.getElementById("fray"), (w, h) => { const k = Math.min(fit(w * 1.2, h), .62); return scaleR(fray(w * .47, 10, k), k); });

  // первый экран: точки слетаются в амулет, вокруг — звёзды ночной степи
  const sky = document.getElementById("sky"), art = document.getElementById("art");
  if (sky && art) {
    const hero = sky.parentElement;
    const LIFE = 20000, FADE = 3000; // через 20 с покачивание и мерцание плавно затихают, цикл останавливается
    let W = 0, H = 0, g, halo, hx = 0, hy = 0, hr = 0, pts = [], from = [], dl = [], sw = [], ph = [], cx = 0, top = 0, t0 = 0, raf = 0, last = 0, seen = true, intro = !calm;
    // положение рамки амулета без учёта transform (анимация появления сдвигает .stage на 28px)
    const box = () => { let x = 0, y = 0, e = art; while (e && e !== hero) { x += e.offsetLeft; y += e.offsetTop; e = e.offsetParent; } return { x, y, w: art.offsetWidth, h: art.offsetHeight }; };
    const key = () => { const b = box(); return [hero.clientWidth, hero.clientHeight, b.x, b.y, b.w, b.h].join(); };
    const layout = () => {
      W = hero.clientWidth; H = hero.clientHeight; g = sizeCanvas(sky, W, H);
      const b = box(), k = fit(b.w, b.h); cx = b.x + b.w / 2; top = b.y + (b.h - AH * k) / 2 + 10 * k;
      hx = cx; hy = top + 330 * k; hr = 430 * k; halo = g.createRadialGradient(hx, hy, 0, hx, hy, hr);
      halo.addColorStop(0, "rgba(255,90,60,.46)"); halo.addColorStop(.42, "rgba(255,90,60,.16)"); halo.addColorStop(1, "rgba(255,90,60,0)");
      seed = 7;
      const shape = scaleR(amulet(cx, top, k), k);
      const dust = Array.from({ length: Math.round(W * H / 2400) }, () => P(R() * W, Math.pow(R(), .7) * H, 4, .7 + R() * 1.1, .12 + R() * .34));
      pts = shape.concat(dust);
      from = pts.map(p => ({ x: p.x + (R() - .5) * W * 1.1, y: p.y + (R() - .5) * H * 1.2 }));
      dl = pts.map(() => R() * .42); sw = pts.map(() => (R() - .5) * 220); ph = pts.map(() => R() * 6.28);
    };
    const ez = t => t < .5 ? 4 * t * t * t : 1 - Math.pow(-2 * t + 2, 3) / 2;
    const amp = now => calm ? 0 : Math.max(0, Math.min(1, (t0 + LIFE - now) / FADE));
    const paint = now => {
      g.clearRect(0, 0, W, H);
      const el = intro ? (now - t0) / 1650 : 9, A = amp(now), sway = Math.sin(now / 1900) * .013 * A;
      const hA = Math.max(0, Math.min(1, (el - .3) / .9)) * (.86 + .14 * Math.sin(now / 1700) * A);
      if (hA > 0) { g.globalAlpha = hA; g.fillStyle = halo; g.fillRect(hx - hr, hy - hr, hr * 2, hr * 2); }
      for (let j = 0; j < pts.length; j++) {
        const b = pts[j]; let x = b.x, y = b.y, a = b.a;
        const u = Math.max(0, Math.min(1, (el - dl[j]) / .95));
        if (u < 1) { const f = from[j], e = ez(u), w = Math.sin(u * 3.1416); x = f.x + (b.x - f.x) * e + w * sw[j]; y = f.y + (b.y - f.y) * e - w * Math.abs(sw[j]) * .7; a = b.a * e; }
        else if (b.c === 4) { x += Math.sin(now / 5200 + ph[j]) * 4 * A; y += Math.cos(now / 6100 + ph[j]) * 3 * A; }
        else if (sway) { const ox = x - cx, oy = y - top; x = cx + ox - sway * oy; y = top + oy + sway * ox; }
        const tw = b.c === 4 ? 1 : 1 - A * (.14 - .14 * Math.sin(now / 640 + ph[j] + x * .012));
        dot(g, x, y, b.c, b.r, a * tw);
      }
      if (intro && el > 1.5) intro = false;
    };
    const loop = now => {
      raf = 0;
      if (calm || !seen || document.hidden) return;
      if (intro || now - last > 40) { last = now; paint(now); } // после сборки — не чаще 25 кадров в секунду
      if (intro || amp(now) > 0) raf = requestAnimationFrame(loop);
    };
    const kick = () => { if (!calm && !raf && seen && !document.hidden && (intro || amp(performance.now()) > 0)) raf = requestAnimationFrame(loop); };
    layout();
    if (calm) paint(0); else { t0 = performance.now(); kick(); }
    // при смене размера сборка не прерывается: точки просто летят к новому месту
    onResize(() => { layout(); if (!raf) paint(performance.now()); kick(); }, key);
    if ("IntersectionObserver" in window) new IntersectionObserver(es => { seen = es[0].isIntersecting; kick(); }).observe(hero);
    document.addEventListener("visibilitychange", kick);
    // пользователь включил или выключил «уменьшить движение» на ходу
    motion.addEventListener?.("change", () => {
      if (calm) { if (raf) cancelAnimationFrame(raf); raf = 0; intro = false; paint(performance.now()); }
      else { t0 = performance.now(); kick(); }
    });
  }

  // радар в «признаках»: луч обходит круг и по очереди зажигает цепочку переводов
  const rbox = document.getElementById("radar");
  if (rbox) {
    const cv = document.createElement("canvas"), st = document.createElement("canvas"); rbox.append(cv); rbox.classList.add("live");
    const CH = [[22, .56], [33, .64], [45, .69], [57, .71], [69, .7], [80, .66]]; // угол от севера по часовой, доля радиуса
    let S = 0, g, sg, c = 0, RM = 0, dust = [], beads = [], raf = 0, last = 0, seen = false;
    const t0 = performance.now(), TURN = 4600, TAU = Math.PI * 2;
    const pol = (a, r) => ({ x: c + Math.sin(a) * r, y: c - Math.cos(a) * r });
    const layout = () => {
      S = rbox.clientWidth; if (!S) return; g = sizeCanvas(cv, S, S); sg = sizeCanvas(st, S, S);
      c = S / 2; RM = c - 6; const s = S / 420; seed = 23;
      sg.clearRect(0, 0, S, S);
      [.25, .5, .75, 1].forEach(f => { const r = RM * f, n = Math.round(TAU * r / 7); for (let i = 0; i < n; i++) { const p = pol(i / n * TAU, r); dot(sg, p.x, p.y, 0, 1.05 * Math.max(.8, s), f === 1 ? .5 : .32); } });
      for (let i = -RM; i <= RM; i += 9) { dot(sg, c + i, c, 0, .9, .16); dot(sg, c, c + i, 0, .9, .16); }
      dust = Array.from({ length: Math.round(70 * s * s) + 30 }, () => { const a = R() * TAU, r = Math.sqrt(R()) * RM * .97; return { a, ...pol(a, r), r: .8 + R() * .9 }; });
      dust.forEach(d => dot(sg, d.x, d.y, 4, d.r, .32));
      beads = CH.map(([deg, f], i) => { const a = deg / 180 * Math.PI, p = pol(a, RM * f), end = i === CH.length - 1; return { a, x: p.x, y: p.y, c: end ? 3 : 1, pts: disc(0, 0, (end ? 14 : 10) * s, end ? 26 : 16, end ? 3 : 1, 1.5 * Math.max(.8, s)) }; });
    };
    const since = (th, a) => ((th - a) % TAU + TAU) % TAU; // сколько луч прошёл после точки
    const paint = th => {
      g.clearRect(0, 0, S, S); g.globalAlpha = 1; g.drawImage(st, 0, 0, S, S);
      for (let k = 0; k < 16; k++) { // луч и затухающий след из точек
        const a = th - k * .07, al = .6 * Math.pow(1 - k / 16, 2);
        for (let r = 8 + (k % 2) * 5; r <= RM; r += 10) { const p = pol(a, r); dot(g, p.x, p.y, 1, k ? 1 : 1.25, al); }
      }
      dust.forEach(d => { const q = since(th, d.a); if (q < .7) dot(g, d.x, d.y, 0, d.r * 1.3, (1 - q / .7) * .85); });
      const lit = beads.map(b => .34 + .66 * Math.exp(-since(th, b.a) / 2.4));
      for (let i = 1; i < beads.length; i++) { const A = beads[i - 1], B = beads[i], al = Math.min(lit[i - 1], lit[i]) * .7; line(A.x, A.y, B.x, B.y, 6, 1, 1).forEach((p, j) => j && j < 5 && dot(g, p.x, p.y, 1, 1, al)); }
      beads.forEach((b, i) => b.pts.forEach(p => dot(g, b.x + p.x, b.y + p.y, b.c, p.r, lit[i])));
    };
    const loop = now => {
      raf = 0; if (calm || !seen || document.hidden) return;
      if (now - last > 33) { last = now; paint(((now - t0) / TURN) * TAU); } // ≈30 кадров в секунду
      raf = requestAnimationFrame(loop);
    };
    const kick = () => { if (!calm && !raf && seen && !document.hidden) raf = requestAnimationFrame(loop); };
    const rest = () => paint(CH[CH.length - 1][0] / 180 * Math.PI + .35); // без движения — цепочка уже горит
    layout(); rest();
    onResize(() => { layout(); rest(); }, () => rbox.clientWidth);
    if ("IntersectionObserver" in window) new IntersectionObserver(es => { seen = es[0].isIntersecting; kick(); }).observe(rbox);
    document.addEventListener("visibilitychange", kick);
    motion.addEventListener?.("change", () => { if (calm) { if (raf) cancelAnimationFrame(raf); raf = 0; rest(); } else kick(); });
  }
  } catch (err) { /* украшение не нарисовалось — остальное работает */ }


  // большие цифры демо досчитывают до итога при появлении; итог уже стоит в разметке
  if (!calm && "IntersectionObserver" in window) {
    document.querySelectorAll("#demo .stat .v").forEach(v => {
      const tn = v.firstChild; if (!tn || tn.nodeType !== 3) return;
      const fin = tn.nodeValue, n = +fin.replace(/\D/g, ""), sep = (fin.match(/\d(\D)\d/) || [, " "])[1];
      if (!n) return;
      const io = new IntersectionObserver(es => {
        if (!es[0].isIntersecting) return; io.disconnect();
        v.style.minWidth = v.offsetWidth + "px"; // ширина не прыгает, пока цифры растут
        const s0 = performance.now(), D = 1500;
        const step = now => {
          const u = Math.min(1, (now - s0) / D), e = 1 - Math.pow(1 - u, 4);
          tn.nodeValue = u < 1 ? String(Math.round(n * e / 100) * 100).replace(/\B(?=(\d{3})+(?!\d))/g, sep) : fin;
          if (u < 1 && !calm) requestAnimationFrame(step); else { tn.nodeValue = fin; v.style.minWidth = ""; }
        };
        requestAnimationFrame(step);
      }, { threshold: .5 });
      io.observe(v);
    });
  }

  // точки в строках тестов уже в разметке; на случай пустых — дорисовываем
  document.querySelectorAll(".dots[data-dots]").forEach(box => {
    if (box.children.length) return;
    const [total, on] = box.dataset.dots.split(":").map(Number);
    box.innerHTML = Array.from({ length: total }, (_, i) => `<i class="${i < on ? "on" : ""}"></i>`).join("");
  });

  // появление секций делает CSS (animation-timeline: view()), JS для этого не нужен

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
  if (card && matchMedia("(hover:hover)").matches) {
    addEventListener("pointermove", e => {
      if (calm) { card.style.transform = ""; return; }
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
  const chips = [...document.querySelectorAll(".chips .chip")];
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
