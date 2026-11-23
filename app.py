"""«Тұмар: радар медленных схем»: учебный прототип.

Запуск: streamlit run app.py
Три экрана: «Клиент», «Аналитик», «Качество». Все данные вымышленные.
Правила радара лежат в radar/rules.py, здесь только показ.
"""
import random
from pathlib import Path

import altair as alt
import pandas as pd
import streamlit as st

from radar.evaluate import load_set_a
from radar.rules import scan, shared_recipients

ROOT = Path(__file__).parent
FOOTER = "Учебный прототип, данные вымышлены, не продукт БЦК"
CLIENTS_PER_STORY = 8   # в приложении меньше клиентов, чем в проверке: так быстрее
START_DAY = 95          # показ начинаем до тревоги
KNOWN_DAYS = 30         # кому платил в первые 30 дней, тот знакомый
FRESH_DAYS = 60         # «новый получатель» в радаре: первый платёж за последние 60 дней
PEOPLE = ("person", "wallet", "company")
REQUESTS = ("deposit_close", "loan")

# Истории для показа: имена вымышлены, подсказок «обман или нет» на экране нет.
DEMO = {
    "A:fraud_classic:0": "Мейрамбек, 41 год",
    "A:fraud_rotating_cards:2": "Салтанат, 52 года",
    "A:fraud_flat_amounts:1": "Жомарт, 37 лет",
    "A:honest_licensed_investor:0": "Динара, 34 года",
    "A:honest_builder:0": "Айбек, 45 лет",
    "A:honest_ordinary:0": "Зарина, 29 лет",
}
FAMILY = ("мама", "брат", "дядя", "сестра", "папа")
SIGNAL_RU = {"ladder": "лесенка", "bait": "наживка", "drain": "опустошение",
             "shared": "общий получатель", "fee": "доплата за вывод"}

# Все надписи экрана «Клиент» на двух языках.
TEXT = {
    "ru": {
        "client": "Клиент", "history": "История клиента", "day": "День",
        "consent": "Режим защиты: клиент заранее согласился на паузу",
        "prev": "Назад", "next": "Следующая операция", "play": "Проиграть", "stop_play": "Остановить показ",
        "to_warn": "К предупреждению", "calm": "Пока спокойно",
        "calm_sub": "Радар не видит двух признаков сразу, поэтому молчит.",
        "warn": "Похоже на медленную схему",
        "warn_sub": "Предупреждение появилось в день {day}, до операции: {what}.",
        "why": "Почему предупреждаем", "note": "Это не приговор, а повод остановиться и проверить.",
        "held": "Заявка на паузе",
        "held_sub": "{what}, день {day}. Клиент включил режим защиты заранее, поэтому банк ждёт разговора.",
        "stopped": "Переводы остановлены", "stopped_sub": "Решение клиента в день {day}. Дальше новым получателям ушло бы {sum} ₸.",
        "go": "Клиент решил продолжить", "go_sub": "Решение в день {day}. Предупреждение осталось в деле аналитика.",
        "b_stop": "Остановить переводы", "b_cancel": "Отменить заявку", "b_go": "Продолжить",
        "b_go_held": "Продолжить после разговора", "b_lic": "Проверить получателя", "b_second": "Второе мнение",
        "b_reset": "Начать заново", "m_sent": "Ушло новым получателям", "m_sig": "Признаков сейчас", "m_saved": "Остановлено",
        "lic_yes": "Лицензия есть. Но лицензия не гарантирует честность: такой обман радар не видит.",
        "lic_no": "В учебном списке лицензий получателя нет. Если он обещает доход, это тревожный признак.",
        "who": "Получатель", "n": "переводов", "since": "первый в день", "total": "всего", "back": "вернул",
        "ladder_txt": "Суммы по порядку", "ops": "Все операции до этого дня", "warn_line": "предупреждение",
        "recipients": "Новые получатели до этого дня", "none": "Новых получателей пока нет, проверять некого.",
    },
    "kz": {
        "client": "Клиент", "history": "Клиенттің тарихы", "day": "Күн",
        "consent": "Қорғау режимі: клиент кідіртуге алдын ала келіскен",
        "prev": "Артқа", "next": "Келесі операция", "play": "Көрсету", "stop_play": "Көрсетуді тоқтату",
        "to_warn": "Ескертуге өту", "calm": "Әзірге тыныш",
        "calm_sub": "Радар бірден екі белгіні көрмейді, сондықтан үндемейді.",
        "warn": "Баяу схемаға ұқсайды",
        "warn_sub": "Ескерту {day}-күні, операцияға дейін шықты: {what}.",
        "why": "Неге ескертеміз", "note": "Бұл үкім емес, тоқтап тексеруге себеп.",
        "held": "Өтінім кідіртілді",
        "held_sub": "{what}, {day}-күн. Клиент қорғау режимін алдын ала қосқан, сондықтан банк әңгімені күтеді.",
        "stopped": "Аударымдар тоқтатылды", "stopped_sub": "Клиенттің шешімі, {day}-күн. Әрі қарай жаңа алушыларға {sum} ₸ кетер еді.",
        "go": "Клиент жалғастыруды шешті", "go_sub": "Шешім {day}-күні қабылданды. Ескерту талдаушының ісінде қалды.",
        "b_stop": "Аударымдарды тоқтату", "b_cancel": "Өтінімді болдырмау", "b_go": "Жалғастыру",
        "b_go_held": "Әңгімеден кейін жалғастыру", "b_lic": "Алушыны тексеру", "b_second": "Екінші пікір",
        "b_reset": "Басынан бастау", "m_sent": "Жаңа алушыларға кетті", "m_sig": "Қазіргі белгілер", "m_saved": "Тоқтатылды",
        "lic_yes": "Лицензиясы бар. Бірақ лицензия адалдыққа кепіл емес: мұндай алдауды радар көрмейді.",
        "lic_no": "Оқу тізімінде бұл алушының лицензиясы жоқ. Табыс уәде етсе, бұл қауіпті белгі.",
        "who": "Алушы", "n": "аударым саны", "since": "алғашқы күні", "total": "барлығы", "back": "қайтарды",
        "ladder_txt": "Сомалар ретімен", "ops": "Осы күнге дейінгі барлық операция", "warn_line": "ескерту",
        "recipients": "Осы күнге дейінгі жаңа алушылар", "none": "Жаңа алушылар әзірге жоқ.",
    },
}
LANG_LABEL = {"ru": "Русский", "kz": "Қазақша"}
REASON = {
    "ru": {
        "ladder": "Суммы новым получателям растут.",
        "bait": "Похоже, вам вернули немного денег, чтобы вызвать доверие.",
        "drain": "Депозит или кредит идёт рядом с переводами новым получателям.",
        "shared": "Тому же получателю недавно впервые заплатили другие клиенты.",
        "fee": "После крупного перевода вы платите ещё одному новому получателю.",
    },
    "kz": {
        "ladder": "Жаңа алушыларға аударымдар өсіп барады.",
        "bait": "Сенім тудыру үшін сізге аздап ақша қайтарған сияқты.",
        "drain": "Депозит немесе кредит жаңа алушыларға аударымдармен қатар жүріп жатыр.",
        "shared": "Осы алушыға жақында басқа клиенттер де алғаш рет төлеген.",
        "fee": "Үлкен аударымнан кейін тағы бір жаңа алушыға төлеп жатырсыз.",
    },
}
KIND = {
    "ru": {"out": "перевод", "in": "поступление", "purchase": "покупка", "salary": "зарплата",
           "deposit_close": "закрытие депозита", "loan": "заявка на кредит"},
    "kz": {"out": "аударым", "in": "түсім", "purchase": "сатып алу", "salary": "жалақы",
           "deposit_close": "депозитті жабу", "loan": "кредитке өтінім"},
}
GROUP = {  # группы на графике: ключ, русский, казахский, цвет
    "new": ("новым получателям", "жаңа алушыларға", "#ff6f52"),
    "known": ("знакомым", "таныстарға", "#8f9ac6"),
    "in": ("поступление", "түсім", "#45d6c8"),
    "buy": ("покупка", "сатып алу", "#4d568f"),
    "req": ("депозит или кредит", "депозит не кредит", "#ffc45c"),
    "held": ("остановлено", "тоқтатылды", "#e6ebf5"),
}

STORY_RU = {
    "fraud_classic": "Обман: классическая схема (лесенка и наживка)",
    "fraud_rotating_cards": "Обман: деньги гоняют по разным картам",
    "fraud_no_bait": "Обман: без наживки",
    "fraud_loan": "Обман: кредит под «инвестиции»",
    "fraud_pyramid": "Обман: пирамида с общим организатором",
    "fraud_fee": "Обман: «налог» за вывод",
    "fraud_fast": "Обман: быстрая схема",
    "fraud_flat_amounts": "Обман: одинаковые суммы",
    "fraud_via_licensed_exchange": "Обман: через лицензированную биржу",
    "honest_ordinary": "Честный: обычные траты",
    "honest_licensed_investor": "Честный: инвестиции через брокера",
    "honest_builder": "Честный: оплата ремонта строителям",
    "honest_student_child": "Честный: переводы ребёнку-студенту",
    "honest_entrepreneur": "Честный: закупки для бизнеса",
    "honest_friend_loan": "Честный: возврат долга другу",
    "honest_car": "Честный: покупка машины",
    "honest_toy_gifts": "Честный: подарки племяннице",
    "honest_kassa": "Честный: взносы в кассу",
    "honest_p2p_trader": "Честный: обмен криптовалюты",
    "honest_tutor": "Честный: оплата репетитора",
}


# ---------- данные (считаются один раз) ----------

@st.cache_data(show_spinner=False)
def load_clients():
    """{id: (сюжет, метка, операции)}: набор клиентов для приложения."""
    return load_set_a(CLIENTS_PER_STORY)


@st.cache_data(show_spinner="Радар проверяет клиентов")
def analysis():
    """Радар по всем клиентам: с согласием на паузу и без него."""
    clients = load_clients()
    shared = shared_recipients({sid: v[2] for sid, v in clients.items()})
    found = {(sid, agree): scan(v[2], client_id=sid, shared=shared, consent=agree)
             for sid, v in clients.items() for agree in (False, True)}
    return shared, found


@st.cache_data(show_spinner=False)
def shown_order():
    """Шесть имён для показа первыми, остальные вперемешку: номер не выдаёт обман."""
    ids = list(load_clients())
    rest = sorted(sid for sid in ids if sid not in DEMO)
    random.Random(2026).shuffle(rest)
    return [sid for sid in DEMO if sid in ids] + rest


def client_name(sid):
    """Имя для экрана: без названия сюжета."""
    order = shown_order()
    return DEMO.get(sid) or (f"Клиент {order.index(sid) + 1:03d}" if sid in order else str(sid))


def cp_name(op):
    """Получатель для экрана: банк не знает, мошенник это или нет."""
    if op.cp.startswith(FAMILY):
        return op.cp.split()[0].capitalize()
    if op.cp_type == "licensed":
        return "Лицензированный брокер"
    if op.cp_type in PEOPLE:
        kind = {"person": "Карта", "wallet": "Кошелёк", "company": "Компания"}[op.cp_type]
        return f"{kind} {sum(map(ord, op.cp)) * 37 % 10000:04d}"
    return op.cp.capitalize()


def money(value):
    """Сумма с пробелами между разрядами."""
    return f"{value:,.0f}".replace(",", " ")


def first_paid(ops):
    """Когда клиент впервые заплатил каждому получателю."""
    first = {}
    for op in ops:
        if op.kind == "out" and op.cp_type in PEOPLE:
            first.setdefault(op.cp, op.day)
    return first


# ---------- что происходит с операциями после решения ----------

def is_risky(op, first, since):
    """Перевод новому получателю или заявка: то, что останавливает клиент."""
    if op.kind in REQUESTS:
        return True
    return (op.kind == "out" and op.cp_type in PEOPLE
            and first[op.cp] > KNOWN_DAYS and first[op.cp] >= since - FRESH_DAYS)


def held_operations(ops, result, decision):
    """Номера операций, которые не прошли из-за решения клиента или паузы."""
    first = first_paid(ops)
    held = set()
    stop = None                              # (день, операция, с которой начинаем)
    if decision and decision[0] == "stop":
        stop = (decision[1], result.first_warn.op)
    elif result.first_pause and not decision:
        stop = (result.first_pause.op.day, result.first_pause.op)
    if stop is None:
        return held
    day, trigger = stop
    for i, op in enumerate(ops):
        pending = op.day == day and op == trigger
        if (op.day > day or pending) and is_risky(op, first, day):
            held.add(i)
    return held


def sent_to_new(ops, held, day, first):
    """Сколько уже ушло новым получателям."""
    return sum(o.amount for i, o in enumerate(ops)
               if i not in held and o.day <= day and o.kind == "out"
               and o.cp_type in PEOPLE and first[o.cp] > KNOWN_DAYS)


# ---------- экран «Клиент» ----------

def feed_chart(ops, held, day, warn_day, lang):
    """Лента операций. Оси не прыгают: они посчитаны по всей истории."""
    first, rows = first_paid(ops), []
    name = {k: v[0 if lang == "ru" else 1] for k, v in GROUP.items()}
    for i, o in enumerate(ops):
        if o.day > day or o.kind == "salary":
            continue
        if i in held:
            group = "held"
        elif o.kind in REQUESTS:
            group = "req"
        elif o.kind == "out":
            group = "new" if o.cp_type in PEOPLE and first[o.cp] > KNOWN_DAYS else "known"
        else:
            group = "in" if o.kind == "in" else "buy"
        rows.append({"day": o.day, "zero": 0, "amount": o.amount, "group": name[group],
                     "kind": KIND[lang][o.kind], "cp": cp_name(o), "sum": money(o.amount) + " ₸"})
    df = pd.DataFrame(rows, columns=["day", "zero", "amount", "group", "kind", "cp", "sum"])
    top = max(o.amount for o in ops if o.kind != "salary") * 1.3
    ticks = [t for t in (10_000, 50_000, 200_000, 1_000_000, 4_000_000) if t < top]
    x = alt.X("day:Q", title=TEXT[lang]["day"], scale=alt.Scale(domain=[0, max(o.day for o in ops) + 2], nice=False),
              axis=alt.Axis(tickCount=8))
    y = alt.Y("amount:Q", title="₸", scale=alt.Scale(type="symlog", constant=20_000, domain=[0, top], nice=False),
              axis=alt.Axis(values=ticks, labelExpr="replace(format(datum.value, ','), /,/g, ' ')"))
    color = alt.Color("group:N", title=None, scale=alt.Scale(domain=list(name.values()), range=[v[2] for v in GROUP.values()]),
                      legend=alt.Legend(orient="top", labelFontSize=14, symbolType="circle", symbolSize=120, columns=6))
    tip = [alt.Tooltip("day:Q", title=TEXT[lang]["day"]), alt.Tooltip("kind:N", title=" "),
           alt.Tooltip("cp:N", title=TEXT[lang]["who"]), alt.Tooltip("sum:N", title="₸")]
    base = alt.Chart(df).encode(x=x, color=color, tooltip=tip)
    chart = base.mark_rule(strokeWidth=4, opacity=.75).encode(y=y, y2="zero:Q") + base.mark_circle(size=130, opacity=1).encode(y=y)
    if warn_day is not None:
        mark = pd.DataFrame({"day": [warn_day], "t": [TEXT[lang]["warn_line"]]})
        chart += alt.Chart(mark).mark_rule(color="#ff5a3c", strokeWidth=2, strokeDash=[4, 6]).encode(x="day:Q")
        chart += alt.Chart(mark).mark_text(color="#ff8a70", align="right", dx=-8, y=12, fontSize=15,
                                           fontWeight=600, font="Bahnschrift").encode(x="day:Q", text="t:N")
    st.altair_chart(
        chart.properties(height=340, width="container").configure(background="transparent").configure_view(stroke=None)
        .configure_axis(grid=False, labelFont="Bahnschrift", titleFont="Bahnschrift", labelFontSize=13,
                        labelColor="#aab3d6", titleColor="#aab3d6", domainColor="#8f9ac6", tickColor="#8f9ac6")
        .configure_legend(labelFont="Bahnschrift", labelColor="#e6ebf5"),
        theme=None, width="stretch")


def card(kind, title, text):
    """Крупная карточка состояния."""
    st.html(f'<div class="card {kind}" role="status"><b>{title}</b><span>{text}</span></div>')


def recipients_table(ops, held, day, lang):
    """Новые получатели: сколько ушло, сколько вернули, есть ли лицензия."""
    t, first = TEXT[lang], first_paid(ops)
    done = [o for i, o in enumerate(ops) if o.day <= day and i not in held]
    people = []
    for cp, start in first.items():
        paid = [o for o in done if o.kind == "out" and o.cp == cp]
        if start > KNOWN_DAYS and paid:
            people.append((cp, start, paid, sum(o.amount for o in done if o.kind == "in" and o.cp == cp)))
    licensed = [o for o in done if o.cp_type == "licensed" and o.kind == "out"]
    return t, sorted(people, key=lambda p: -sum(o.amount for o in p[2])), licensed


def show_check(ops, held, day, lang):
    """Кнопка «Проверить получателя»."""
    t, people, licensed = recipients_table(ops, held, day, lang)
    if licensed:
        st.success(f"**{cp_name(licensed[-1])}**. {t['lic_yes']}", icon=":material/verified:")
    if not people:
        if not licensed:
            st.info(t["none"])
        return
    st.info(f"**{cp_name(people[0][2][0])}**. {t['lic_no']}", icon=":material/search:")


def show_second(ops, held, day, lang):
    """Кнопка «Второе мнение»: простая арифметика по тем же операциям."""
    t, people, _ = recipients_table(ops, held, day, lang)
    st.write(f"**{t['recipients']}**")
    if not people:
        st.info(t["none"])
        return
    st.dataframe(pd.DataFrame([{
        t["who"]: cp_name(paid[0]), t["n"]: len(paid), t["since"]: start,
        t["total"] + ", ₸": money(sum(o.amount for o in paid)), t["back"] + ", ₸": money(back),
        t["ladder_txt"]: "  ›  ".join(money(o.amount) for o in paid),
    } for _, start, paid, back in people]), hide_index=True, width="stretch")


def reset_client():
    """Новая история начинается до тревоги и без прошлых решений."""
    sid = st.session_state["sid"]
    st.session_state["day"] = min(START_DAY, max(o.day for o in load_clients()[sid][2]))
    st.session_state["playing"] = False
    st.session_state["panel"] = None
    st.session_state.setdefault("decisions", {}).pop(sid, None)


def set_state(**values):
    """Обработчик кнопок."""
    for key, value in values.items():
        st.session_state[key] = value


def decide(sid, what, day):
    st.session_state.setdefault("decisions", {})[sid] = (what, day)
    st.session_state["panel"] = None
    st.session_state["playing"] = False


def screen_client():
    """Экран клиента. Работает как отдельный кусок страницы, поэтому отвечает быстро."""
    s = st.session_state
    s.setdefault("decisions", {})
    s.setdefault("playing", False)
    s.setdefault("panel", None)

    left, right = st.columns([3, 1], vertical_alignment="bottom")
    lang = right.segmented_control("Тіл / Язык", list(LANG_LABEL), default="ru", key="lang",
                                   format_func=LANG_LABEL.get, label_visibility="collapsed") or "ru"
    t = TEXT[lang]
    sid = left.selectbox(t["history"], shown_order(), format_func=client_name, key="sid", on_change=reset_client)
    ops = load_clients()[sid][2]
    last = max(o.day for o in ops)
    s.setdefault("day", min(START_DAY, last))

    consent = st.toggle(t["consent"], key="consent")
    result = analysis()[1][(sid, consent)]
    decision = s["decisions"].get(sid)
    held = held_operations(ops, result, decision)
    warn_day = result.first_warn.op.day if result.first_warn else None
    pause_day = result.first_pause.op.day if result.first_pause else None

    if s["playing"]:                       # показ сам доходит до тревоги и останавливается
        ahead = [o.day for o in ops if o.day > s["day"] and o.kind != "salary"]
        stops = [d for d in (warn_day, pause_day) if d and d > s["day"] and not decision]
        s["day"] = min(ahead) if ahead else last
        if not ahead or s["day"] in stops:
            s["playing"] = False
            st.rerun()

    day = st.slider(t["day"], 0, last, key="day")
    b = st.columns([1, 1.5, 1.3, 1.5])
    days = sorted({o.day for o in ops if o.kind != "salary"})
    before, after = [d for d in days if d < day], [d for d in days if d > day]
    b[0].button(t["prev"], icon=":material/arrow_back:", key="b_prev", width="stretch", disabled=not before, on_click=set_state,
                kwargs={"day": before[-1] if before else 0, "playing": False})
    b[1].button(t["next"], icon=":material/arrow_forward:", key="b_next", width="stretch", disabled=not after, on_click=set_state,
                kwargs={"day": after[0] if after else last, "playing": False})
    if b[2].button(t["stop_play"] if s["playing"] else t["play"], key="b_play", width="stretch", disabled=not after and not s["playing"],
                   icon=":material/stop:" if s["playing"] else ":material/play_arrow:",
                   on_click=set_state, kwargs={"playing": not s["playing"]}):
        st.rerun()                         # перезапуск страницы включает или выключает таймер
    b[3].button(t["to_warn"], icon=":material/notifications_active:", key="b_warn", width="stretch", disabled=warn_day is None or warn_day == day,
                on_click=set_state, kwargs={"day": warn_day or day, "playing": False})

    warned = warn_day is not None and day >= warn_day
    feed_chart(ops, held, day, warn_day if warned else None, lang)

    first = first_paid(ops)
    seen = [v for v in result.verdicts if v.op.day <= day]
    now = seen[-1].signals if seen else ()
    # В день предупреждения операция ещё ждёт решения клиента, поэтому не считаем её ушедшей.
    waits = {i for i, o in enumerate(ops) if o == result.first_warn.op} if day == warn_day and not decision else set()
    sent = sent_to_new(ops, held | waits, day, first)
    saved = sum(ops[i].amount for i in held if ops[i].kind == "out")
    main, side = st.columns([2.1, 1], gap="large")
    with side:
        st.metric(t["m_sent"], f"{money(sent)} ₸")
        st.metric(t["m_sig"], len(now))
        if decision and decision[0] == "stop":
            st.metric(t["m_saved"], f"{money(saved)} ₸")

    waiting = bool(consent and pause_day and day >= pause_day and not decision)
    with main:
        def what(op):
            return f"{KIND[lang][op.kind]}, {money(op.amount)} ₸"
        if decision and day >= decision[1]:
            key = "stopped" if decision[0] == "stop" else "go"
            card("ok" if key == "stopped" else "go", t[key], t[key + "_sub"].format(day=decision[1], sum=money(saved)))
        elif waiting:
            card("hold", t["held"], t["held_sub"].format(what=what(result.first_pause.op).capitalize(), day=pause_day))
        elif warned:
            card("warn", t["warn"], t["warn_sub"].format(day=warn_day, what=what(result.first_warn.op)))
        else:
            card("calm", t["calm"], t["calm_sub"])
        if warned:
            reasons = list(dict.fromkeys(result.first_warn.signals + (result.first_pause.signals if waiting else ())))
            st.write(f"**{t['why']}**")
            for r in reasons:
                st.html(f'<div class="why"><i></i>{REASON[lang][r]}</div>')
            st.caption(t["note"])

    c = st.columns(4)
    active = warned and not decision
    c[0].button(t["b_cancel"] if waiting else t["b_stop"], key="b_stop", width="stretch", type="primary", disabled=not active,
                on_click=decide, args=(sid, "stop", pause_day if waiting else day))
    c[1].button(t["b_lic"], key="b_lic", width="stretch", on_click=set_state, kwargs={"panel": None if s["panel"] == "lic" else "lic"})
    c[2].button(t["b_second"], key="b_second", width="stretch", on_click=set_state, kwargs={"panel": None if s["panel"] == "second" else "second"})
    if decision:
        c[3].button(t["b_reset"], key="b_reset", width="stretch", icon=":material/restart_alt:", on_click=reset_client)
    else:
        c[3].button(t["b_go_held"] if waiting else t["b_go"], key="b_go", width="stretch", disabled=not active,
                    on_click=decide, args=(sid, "go", day))
    if s["panel"] == "lic":
        show_check(ops, held, day, lang)
    if s["panel"] == "second":
        show_second(ops, held, day, lang)

    with st.expander(t["ops"]):
        st.dataframe(pd.DataFrame([{
            t["day"]: o.day, " ": ("⏸ " if i in held else "") + KIND[lang][o.kind], t["who"]: cp_name(o), "₸": money(o.amount),
        } for i, o in enumerate(ops) if o.day <= day][::-1]), hide_index=True, width="stretch")
    footer()


# ---------- экран «Аналитик» ----------

def case_text(sid, result):
    """Справка по делу: её можно скачать."""
    ops = load_clients()[sid][2]
    warn, pause, first = result.first_warn, result.first_pause, first_paid(ops)
    lines = ["ТҰМАР. Справка по клиенту (учебные данные)", f"Клиент: {client_name(sid)}",
             f"Предупреждение: день {warn.op.day}, перед операцией «{KIND['ru'][warn.op.kind]}» на {money(warn.op.amount)} ₸",
             "Пауза в режиме защиты: " + (f"день {pause.op.day}" if pause else "не потребовалась"), "", "Причины:"]
    lines += [f"  {SIGNAL_RU[x]}: {REASON['ru'][x]}" for x in warn.signals]
    lines += ["", "Переводы новым получателям:"]
    lines += [f"  день {o.day}: {cp_name(o)}, {money(o.amount)} ₸" for o in ops
              if o.kind == "out" and o.cp_type in PEOPLE and first[o.cp] > KNOWN_DAYS]
    return "\n".join(lines + ["", "Решение принимает человек. " + FOOTER]).replace(" ", " ")


def shared_dot(shared):
    """Схема общих получателей: то же правило, что в радаре (6 и больше клиентов за 30 дней)."""
    lines = ["digraph g {", 'rankdir=LR; bgcolor=transparent; node [shape=box, style="rounded,filled", fontname="Bahnschrift", '
             'fontsize=12, color="#8f9ac6", fillcolor="#1f2358", fontcolor="#e6ebf5"];',
             'edge [color="#8f9ac6", fontname="Bahnschrift", fontsize=10, fontcolor="#aab3d6"];']
    n = 0
    for cp, pays in shared.items():
        fresh = [(d, c) for d, c in pays if d > KNOWN_DAYS and d - pays[0][0] <= 30]
        if len({c for _, c in fresh}) < 6:
            continue
        n += 1
        lines.append(f'"r{n}" [label="Получатель {n}\\nклиентов: {len(fresh)}", fillcolor="#d8452d", color="#d8452d", fontcolor=white];')
        lines += [f'"{c}" [label="{client_name(c)}"]; "{c}" -> "r{n}" [label="день {d}"];' for d, c in fresh]
    return "\n".join(lines + ["}"]), n


def screen_analyst():
    shared, found = analysis()
    rows = []
    for sid in shown_order():
        r = found[(sid, True)]
        w = r.first_warn
        rows.append({"sid": sid, "Клиент": client_name(sid), "Предупреждение, день": w.op.day if w else None,
                     "Признаки": ", ".join(SIGNAL_RU[x] for x in w.signals) if w else "",
                     "Пауза, день": r.first_pause.op.day if r.first_pause else None})
    df = pd.DataFrame(rows)
    warned = int(df["Предупреждение, день"].notna().sum())
    m = st.columns(3)
    m[0].metric("Клиентов", len(df))
    m[1].metric("С предупреждением", warned)
    m[2].metric("С паузой при согласии", int(df["Пауза, день"].notna().sum()))

    a, b = st.columns([2, 1], vertical_alignment="bottom")
    wanted = a.multiselect("Показать с признаками", list(SIGNAL_RU.values()), placeholder="Любые признаки")
    only = b.toggle("Только с предупреждением", value=True)
    view = df[df["Предупреждение, день"].notna()] if only else df
    for x in wanted:
        view = view[view["Признаки"].str.contains(x)]
    view = view.sort_values("Предупреждение, день", na_position="last").reset_index(drop=True)
    st.caption(f"Найдено: {len(view)}. Выберите строку, чтобы открыть дело.")
    pick = st.dataframe(view.drop(columns="sid"), hide_index=True, width="stretch", height=330, key="cases",
                        on_select="rerun", selection_mode="single-row")
    chosen = [i for i in pick.selection.rows if i < len(view)]
    if chosen:
        sid = view.loc[chosen[0], "sid"]
        r = found[(sid, True)]
        st.subheader(client_name(sid))
        if r.first_warn:
            ops = load_clients()[sid][2]
            for x in r.first_warn.signals:
                st.html(f'<div class="why"><i></i><b>{SIGNAL_RU[x].capitalize()}.</b>&nbsp;{REASON["ru"][x]}</div>')
            feed_chart(ops, set(), max(o.day for o in ops), r.first_warn.op.day, "ru")
            st.download_button("Скачать справку по делу", case_text(sid, r), file_name="spravka.txt", icon=":material/download:")
        else:
            st.info("Предупреждений нет: двух признаков сразу не было.")

    st.subheader("Общие получатели")
    dot, n = shared_dot(shared)
    if n:
        st.caption("Сюда за 30 дней впервые заплатили 6 и больше клиентов. Честный получатель тоже может оказаться здесь, "
                   "поэтому одного этого признака мало.")
        st.graphviz_chart(dot, width="content")
    else:
        st.info("Таких получателей нет.")
    footer()


# ---------- экран «Качество» ----------

TESTS = [("Тест 1", 5, 0, 5, 0, "В историях обмана не было депозита и кредита."),
         ("Тест 2", 10, 8, 10, 9, "До него исправили «общего получателя». Пауза: 0 из 5."),
         ("Тест 3", 10, 10, 10, 0, "До него исправили лесенку и наживку. До депозита или кредита: 0 из 4, пауза: 0 из 4.")]


def beads(total, full, css):
    return "".join(f'<u class="{css if i < full else ""}"></u>' for i in range(total))


def russian_names(text):
    for key in sorted(STORY_RU, key=len, reverse=True):
        text = text.replace(key, STORY_RU[key])
    return text


def screen_quality():
    st.subheader("Три слепых теста")
    st.caption("Одна бусина это одна история. Истории придуманы ИИ. Правила после третьего теста не менялись.")
    st.html("".join(
        f'<div class="test"><b>{name}</b><div><p>{beads(n, hit, "f")}</p>{hit} из {n} обманов заметили</div>'
        f'<div><p>{beads(m, false, "h")}</p>{false} из {m} честных предупредили зря</div><span>{note}</span></div>'
        for name, n, hit, m, false, note in TESTS))
    st.subheader("Подробные отчёты")
    files = {"Учебный набор A": "A", "Тест 1": "blind1", "Тест 2": "blind2", "Тест 3": "blind3"}
    choice = st.segmented_control("Отчёт", list(files), default="Тест 3", label_visibility="collapsed") or "Тест 3"
    if choice == "Учебный набор A":
        st.caption("На этом наборе радар настраивали, поэтому для вывода о качестве он не годится.")
    path = ROOT / "docs" / f"metrics_{files[choice]}.md"
    if path.exists():
        body = russian_names(path.read_text(encoding="utf-8")).split("\n", 1)[-1]
        st.markdown(body.replace("\n## ", "\n#### "))
    else:
        st.info(f"Отчёта {path.name} нет. Соберите его командой: python -m radar.evaluate --set A")
    footer()


def footer():
    st.divider()
    st.caption(FOOTER)


def page_style():
    """Оформление: ночная степь и тұмар из точек, как на слайдах."""
    st.html("""<style>
    html, body, .stApp, .stApp button, .stApp input, .stApp p, .stApp h1, .stApp h2, .stApp h3,
    .stApp label {font-family: Bahnschrift, "Segoe UI", sans-serif}
    .stApp {background: linear-gradient(180deg, #0f1338 0, #1a1b52 70%, #2a2060 100%) fixed}
    .stApp h2 {font-size: 46px; font-stretch: 75%; letter-spacing: -.6px}
    .stApp h3 {font-stretch: 80%}
    .block-container, .stMainBlockContainer {padding-top: 1.2rem; max-width: 1180px}
    header[data-testid="stHeader"] {background: transparent}
    .stTabs [data-baseweb="tab"] p {font-size: 20px; font-weight: 600}
    .stButton button {border: 2px solid #8f9ac6; border-radius: 14px; width: 100%; min-height: 50px;
                      font-weight: 600; background: rgba(255,255,255,.04); transition: background .18s, color .18s}
    .stButton button:hover {background: #e6ebf5; color: #151a45; border-color: #e6ebf5}
    .stButton button:focus-visible {outline: 3px solid #45d6c8; outline-offset: 2px}
    .card {padding: 26px 30px; border-radius: 24px 24px 24px 6px; animation: alarm .6s cubic-bezier(.16,1,.3,1)}
    .card b {display: block; font-size: 38px; font-stretch: 78%; line-height: 1.05; margin-bottom: 8px}
    .card span {font-size: 19px; line-height: 1.35}
    .card.warn {background: linear-gradient(150deg, #e2492f, #a8212d); color: #fff}
    .card.hold {background: #ffc45c; color: #2a1c05}
    .card.ok {background: #0f5f5c; color: #fff; border: 2px solid #45d6c8}
    .card.go {background: #2a2e68; color: #e6ebf5; border: 2px solid #8f9ac6}
    .card.calm {background: rgba(255,255,255,.05); color: #e6ebf5}
    .why {display: flex; align-items: center; font-size: 19px; padding: 5px 0; flex-wrap: wrap}
    .why i {width: 13px; height: 13px; border-radius: 50%; background: #ff5a3c; margin-right: 14px; flex: none}
    .test {display: grid; grid-template-columns: 90px 1fr 1fr 1fr; gap: 20px; align-items: center; padding: 20px 0;
           border-top: 1px solid rgba(230,235,245,.2); font-size: 17px}
    .test > b {font-size: 30px; font-stretch: 78%} .test p {display: flex; gap: 5px; margin: 0 0 8px}
    .test u {flex: none; width: 20px; height: 20px; border-radius: 50%; border: 3px solid #8f9ac6; box-sizing: border-box}
    .test u.f {background: #ff5a3c; border-color: #ff5a3c} .test u.h {background: #ffc45c; border-color: #ffc45c}
    @media (max-width: 760px) {.test {grid-template-columns: 1fr}}
    .stButton button[kind="primary"] {background: #ff5a3c; border-color: #ff5a3c; color: #1a0703}
    .stButton button:disabled {opacity: .4}
    [data-testid="stMetricValue"] {font-size: 42px; font-stretch: 75%; font-weight: 700; line-height: 1}
    @keyframes alarm {from {transform: translateY(24px) scale(.97); opacity: 0}}
    /* метрики-карточки, вкладки-пилюли, мягче тени */
    .stApp {background: radial-gradient(900px 420px at 78% -6%, rgba(109,42,92,.55), transparent 62%),
                              radial-gradient(700px 360px at 8% 2%, rgba(35,32,110,.6), transparent 60%),
                              linear-gradient(180deg, #0b0e2a 0, #10143a 46%, #161544 100%) fixed}
    [data-testid="stMetric"] {background: rgba(255,255,255,.045); border: 1px solid rgba(230,235,245,.1);
                              border-radius: 16px; padding: 14px 16px}
    [data-testid="stMetricLabel"] p {font-size: 13px; letter-spacing: .05em; text-transform: uppercase; color: #aab3d6}
    [data-testid="stMetricValue"] {font-size: 38px}
    .stTabs [data-baseweb="tab-list"] {gap: 4px; background: rgba(255,255,255,.045); padding: 5px;
                                       border-radius: 999px; width: max-content; border: 1px solid rgba(230,235,245,.09)}
    .stTabs [data-baseweb="tab"] {border-radius: 999px; padding: 4px 20px; height: auto}
    .stTabs [aria-selected="true"] {background: rgba(255,90,60,.18)}
    .stTabs [data-baseweb="tab-highlight"], .stTabs [data-baseweb="tab-border"] {display: none}
    .card {box-shadow: 0 26px 60px -38px #000, inset 0 1px 0 rgba(255,255,255,.09)}
    .why {border-bottom: 1px dashed rgba(230,235,245,.1); padding: 9px 0}
    .why:last-of-type {border-bottom: 0}
    .stButton button {min-height: 52px}
    .stButton button:hover {transform: translateY(-1px)}
    .stButton button[kind="primary"] {box-shadow: 0 14px 28px -16px rgba(255,90,60,.85)}
    @media (prefers-reduced-motion: reduce) {* {animation: none !important}}
    </style>""")
    st.iframe(ROOT / "assets" / "hero.html", height=256)



def main():
    st.set_page_config(page_title="Тұмар: радар медленных схем", page_icon="🔺", layout="wide")
    page_style()
    tabs = st.tabs(["Клиент", "Аналитик", "Качество"])
    with tabs[0]:
        playing = st.session_state.get("playing", False)
        st.fragment(screen_client, run_every=0.45 if playing else None)()
    with tabs[1]:
        st.fragment(screen_analyst)()
    with tabs[2]:
        st.fragment(screen_quality)()


main()
