"""«Тұмар: радар медленных схем»: учебный прототип.

Запуск: streamlit run app.py
Три экрана: «Клиент», «Аналитик», «Качество». Все данные вымышленные.
Правила радара лежат в radar/rules.py, здесь только показ.
"""
import html
import math
import random
from pathlib import Path

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
# Пояснения для первого знакомства: что это, как смотреть, что значит каждый экран и знак.
TEXT["ru"].update({
    "what": "Тұмар следит за переводами клиента и предупреждает, когда видит сразу два признака медленной "
            "мошеннической схемы. Здесь такую историю можно прожить день за днём.",
    "how": "Как смотреть демо",
    "s1": "Выберите историю", "s1_sub": "Клиенты вымышлены. Кого из них обманывают, не подписано.",
    "s2": "Нажмите «Проиграть» или листайте дни", "s2_sub": "Каждая точка на ленте — операция клиента.",
    "s3": "Смотрите, когда и почему радар предупредит", "s3_sub": "Один признак — молчим. Два и больше — предупреждаем.",
    "cta": "Смотреть историю Мейрамбека",
    "tab_client": "Что видит клиент в приложении банка и что в это время замечает радар.",
    "tab_analyst": "Что видит антифрод-команда банка: все предупреждения и общие получатели.",
    "tab_quality": "Честные результаты трёх слепых тестов: что поймали и что пропустили.",
    "story_hint": "Кого обманывают, не подписано: смотрите сами.",
    "consent_hint": "Если включить, банк может поставить заявку на депозит или кредит на паузу до разговора с клиентом.",
    "phone": "Приложение банка", "last_op": "Последняя операция", "radar": "Что видит радар",
    "of5": "признаков из 5", "lit": "сработал", "silent": "0–1 — тишина", "loud": "2+ — предупреждение",
    "r0": "Признаков нет — радар молчит.", "r1": "Один признак — этого мало, радар молчит.",
    "r2": "{n} признака сразу — радар предупреждает.", "r_was": "Предупреждение уже показано в день {day}.",
    "rule": "Один признак — молчим. Два и больше — предупреждаем.",
    "d_today": "День {day}: {what}", "d_more": " (и ещё {n})", "d_start": "День {day}: операций пока нет",
    "d_quiet": "День {day}: операций нет. Последняя была в день {last}: {what}",
    "to_new": "новому получателю", "to_known": "знакомому получателю", "from": "отправитель",
    "tl": "Лента операций", "tl_sub": "Каждая строка — тип операций, каждая точка — операция; чем больше точка, тем больше сумма.",
    "today": "сегодня", "warn_here": "здесь радар предупредил",
    "gloss": "Пять признаков: что они значат",
})
TEXT["kz"].update({
    "what": "Тұмар клиенттің аударымдарын бақылайды және баяу алаяқтық схеманың екі белгісін бірден көргенде "
            "ескертеді. Мұнда осындай тарихты күн артынан күн көруге болады.",
    "how": "Демоны қалай көру керек",
    "s1": "Тарихты таңдаңыз", "s1_sub": "Клиенттер ойдан шығарылған. Кімді алдап жатқаны жазылмаған.",
    "s2": "«Көрсету» батырмасын басыңыз немесе күндерді ауыстырыңыз", "s2_sub": "Лентадағы әр нүкте — клиенттің операциясы.",
    "s3": "Радар қашан және неге ескертетінін қараңыз", "s3_sub": "Бір белгі — үндемейміз. Екеу және одан көп — ескертеміз.",
    "cta": "Мейрамбектің тарихын көру",
    "tab_client": "Клиент банк қосымшасында не көреді және сол кезде радар нені байқайды.",
    "tab_analyst": "Банктің антифрод тобы не көреді: барлық ескертулер және ортақ алушылар.",
    "tab_quality": "Үш соқыр тесттің адал нәтижелері: нені ұстадық, нені өткізіп алдық.",
    "story_hint": "Кімді алдап жатқаны жазылмаған: өзіңіз қараңыз.",
    "consent_hint": "Қосылса, банк депозит не кредит өтінімін клиентпен әңгімеге дейін кідіртуі мүмкін.",
    "phone": "Банк қосымшасы", "last_op": "Соңғы операция", "radar": "Радар не көреді",
    "of5": "белгі, барлығы 5", "lit": "байқалды", "silent": "0–1 — үнсіздік", "loud": "2+ — ескерту",
    "r0": "Белгі жоқ — радар үндемейді.", "r1": "Бір белгі — бұл аз, радар үндемейді.",
    "r2": "Бірден {n} белгі — радар ескертеді.", "r_was": "Ескерту {day}-күні көрсетілді.",
    "rule": "Бір белгі — үндемейміз. Екеу және одан көп — ескертеміз.",
    "d_today": "{day}-күн: {what}", "d_more": " (тағы {n})", "d_start": "{day}-күн: әзірге операция жоқ",
    "d_quiet": "{day}-күн: операция жоқ. Соңғысы {last}-күні болды: {what}",
    "to_new": "жаңа алушыға", "to_known": "таныс алушыға", "from": "жіберуші",
    "tl": "Операциялар лентасы", "tl_sub": "Әр жол — операция түрі, әр нүкте — операция; нүкте неғұрлым үлкен болса, сома соғұрлым көп.",
    "today": "бүгін", "warn_here": "радар осы жерде ескертті",
    "gloss": "Бес белгі: нені білдіреді",
})
# Короткие имена знаков и пояснения к ним: те же слова, что на сайте (docs/index.html, docs/kz.html).
SIGN = {
    "ru": {"ladder": "Лесенка", "bait": "Наживка", "drain": "Опустошение", "shared": "Общий получатель", "fee": "Доплата"},
    "kz": {"ladder": "Баспалдақ", "bait": "Жем", "drain": "Босату", "shared": "Ортақ алушы", "fee": "Қосымша төлем"},
}
GLOSS = {
    "ru": {"ladder": "Суммы новым получателям растут от перевода к переводу.",
           "bait": "Получатель один раз вернул деньги — чтобы усыпить осторожность.",
           "drain": "Заявка на закрытие вклада или кредит рядом с такими переводами.",
           "shared": "Туда же впервые платят другие клиенты банка.",
           "fee": "После крупного перевода просят «налог» за вывод — назад ничего не приходит."},
    "kz": {"ladder": "Жаңа алушыларға сомалар аударым сайын өседі.",
           "bait": "Алушы бір рет ақша қайтарды — сақтықты ұйықтату үшін.",
           "drain": "Депозитті жабу немесе кредит өтінімі осындай аударымдармен қатар.",
           "shared": "Ол жаққа банктің басқа клиенттері де алғаш рет төлейді.",
           "fee": "Үлкен аударымнан кейін шығару үшін «салық» сұрайды — кері ештеңе келмейді."},
}
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
# История по шагам под лентой и подсказка «как читать ленту». Числа подставляются из данных.
TEXT["ru"].update({
    "key_title": "Как читать ленту",
    "key_steps": "переводы незнакомым — растут лесенкой", "key_sign": "в этот день сработал признак",
    "key_warn": "радар предупредил",
    "story": "История по шагам",
    "story_tip": "Номера на ленте — это шаги ниже. Нажмите на шаг, и лента перейдёт к этому дню.",
    "st_first": "День {day}: первый перевод незнакомому получателю — {sum} ₸",
    "st_grow": "День {day}: тому же получателю уже больше — {prev} → {sum} ₸",
    "st_ladder": "День {day}: суммы растут — признак «{sign}»",
    "st_bait": "День {day}: получатель вернул {sum} ₸ — это «{sign}», чтобы клиент поверил",
    "st_req": "День {day}: {what} на {sum} ₸",
    "st_req_sign": "День {day}: {what} на {sum} ₸ — признак «{sign}»",
    "st_sign": "День {day}: признак «{sign}». {gloss}",
    "st_tail": "Это {nth} признак — радар предупредил",
    "st_warn": "День {day}: признаков сразу {n} — радар предупредил",
    "st_pause": "День {day}: банк поставил заявку на паузу до разговора с клиентом",
    "st_stop": "День {day}: клиент остановил переводы — сохранено {sum} ₸",
    "st_go": "День {day}: клиент решил продолжить",
    "st_none": "Пока ничего заметного: переводов незнакомым не было.",
    "st_calm0": "Радар не видел ни одного признака — он молчит.",
    "st_calm": "Радар видел {n} {word} — этого мало, он молчит.",
    "fired_at": "сработал в день {day}: {what}", "step_ref": "шаг {n} на ленте",
})
TEXT["kz"].update({
    "key_title": "Лентаны қалай оқу керек",
    "key_steps": "бейтаныстарға аударымдар — баспалдақпен өседі", "key_sign": "осы күні белгі байқалды",
    "key_warn": "радар ескертті",
    "story": "Тарих қадам бойынша",
    "story_tip": "Лентадағы нөмірлер — төмендегі қадамдар. Қадамды бассаңыз, лента сол күнге өтеді.",
    "st_first": "{day}-күн: бейтаныс алушыға алғашқы аударым — {sum} ₸",
    "st_grow": "{day}-күн: сол алушыға енді көбірек — {prev} → {sum} ₸",
    "st_ladder": "{day}-күн: сомалар өсіп барады — «{sign}» белгісі",
    "st_bait": "{day}-күн: алушы {sum} ₸ қайтарды — бұл клиент сенуі үшін «{sign}»",
    "st_req": "{day}-күн: {what}, {sum} ₸",
    "st_req_sign": "{day}-күн: {what}, {sum} ₸ — «{sign}» белгісі",
    "st_sign": "{day}-күн: «{sign}» белгісі. {gloss}",
    "st_tail": "Бұл {nth} белгі — радар ескертті",
    "st_warn": "{day}-күн: бірден {n} белгі — радар ескертті",
    "st_pause": "{day}-күн: банк өтінімді клиентпен әңгімеге дейін кідіртті",
    "st_stop": "{day}-күн: клиент аударымдарды тоқтатты — {sum} ₸ сақталды",
    "st_go": "{day}-күн: клиент жалғастыруды шешті",
    "st_none": "Әзірге ештеңе байқалмады: бейтаныстарға аударым болған жоқ.",
    "st_calm0": "Радар бірде-бір белгі көрмеді — ол үндемейді.",
    "st_calm": "Радар {n} белгі көрді — бұл аз, ол үндемейді.",
    "fired_at": "{day}-күні байқалды: {what}", "step_ref": "лентадағы {n}-қадам",
})
NTH = {"ru": ("", "первый", "второй", "третий", "четвёртый", "пятый"),
       "kz": ("", "бірінші", "екінші", "үшінші", "төртінші", "бесінші")}
REQ = {"ru": {"deposit_close": "заявка на закрытие вклада", "loan": "заявка на кредит"},
       "kz": {"deposit_close": "салымды жабуға өтінім", "loan": "кредитке өтінім"}}

GROUP = {  # группы на графике: ключ, русский, казахский, цвет (токены DESIGN.md: сердолик, серебро, мята, янтарь)
    "new": ("новым получателям", "жаңа алушыларға", "#ff5a3c"),
    "known": ("знакомым", "таныстарға", "#aab6b1"),
    "in": ("поступление", "түсім", "#5ec8b4"),
    "buy": ("покупка", "сатып алу", "#6f7b77"),
    "req": ("депозит или кредит", "депозит не кредит", "#ffc45c"),
    "held": ("остановлено", "тоқтатылды", "#ecf3ef"),
}
FONT = '"Golos Text", system-ui, "Segoe UI", Roboto, sans-serif'

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

# Дорожки ленты сверху вниз: схема наверху и ярко, обычная жизнь внизу и приглушённо.
LANES = ("new", "back", "req", "known", "buy", "in")
BACK = ("вернули новые получатели", "жаңа алушылар қайтарды")
LOOK = {  # цвет, наименьший и наибольший радиус точки, непрозрачность
    "new": ("#ff5a3c", 5, 15, 1), "back": ("#5ec8b4", 5, 13, 1), "req": ("#ffc45c", 5, 15, 1),
    "known": ("#aab6b1", 3, 7, .6), "buy": ("#8b9792", 3, 7, .6), "in": ("#5ec8b4", 3, 7, .55),
}
HOT = ("new", "back", "req")


def lane_of(o, first):
    """Дорожка операции: те же группы, что были в легенде, плюс возвраты от новых получателей."""
    if o.kind in REQUESTS:
        return "req"
    if o.kind == "out":
        return "new" if o.cp_type in PEOPLE and first[o.cp] > KNOWN_DAYS else "known"
    if o.kind == "in":
        return "back" if KNOWN_DAYS < first.get(o.cp, 0) <= o.day else "in"
    return "buy"


@st.cache_data(show_spinner=False)
def amount_scale():
    """Общий масштаб сумм по всем клиентам: точки и высоты сравнимы между историями."""
    top, fresh = 0, []
    for _, _, ops in load_clients().values():
        first = first_paid(ops)
        for o in ops:
            if o.kind != "salary":
                top = max(top, o.amount)
                if lane_of(o, first) == "new":
                    fresh.append(o.amount)
    return top, math.log(min(fresh)), math.log(max(fresh))


def lane_name(k, lang):
    return BACK[lang != "ru"] if k == "back" else GROUP[k][lang != "ru"]


def _ticks(span, width):
    step = next((s for s in (5, 10, 20, 30, 50, 100) if span / s <= width / 56), 100)
    return list(range(0, int(span) + 1, step))


def _fits(box, taken):
    x0, x1, y0, y1 = box
    return all(x1 < a0 or x0 > a1 or y1 < b0 or y0 > b1 for a0, a1, b0, b1 in taken)


def timeline_svg(items, lanes, signs, span, day, warn_day, ring, t, lang, narrow, today, scale, calls=()):
    """Одна раскладка ленты. По горизонтали проценты (ширина любая), по вертикали пиксели."""
    W = 320 if narrow else 940                       # примерная ширина: только чтобы подписи не налезали

    def pct(d):
        return d / span * 100

    def px(d):
        return pct(d) * W / 100
    lab = 22 if narrow else 0
    rail = 30
    top = rail + 14 + max(1, len(signs)) * 21        # строка «предупредил» и подвески знаков
    pos, y = {}, top
    for k in lanes:
        h = (96 if narrow else 112) if k == "new" else (32 if narrow else 40)
        pos[k] = (y, y + lab, y + lab + h)            # начало дорожки, начало точек, низ
        y += lab + h
    axis = y + 4
    out = []
    add = out.append
    for k in lanes:                                   # дорожки: фон у схемы, тонкая линия у остальных
        y0, b0, b1 = pos[k]
        if k == "new":
            add(f'<rect x="0" y="{b0 + 2}" width="100%" height="{b1 - b0 - 4}" rx="12" class="tl-hotlane"/>')
        else:
            add(f'<line x1="0" x2="100%" y1="{(b0 + b1) / 2}" y2="{(b0 + b1) / 2}" class="tl-track"/>')
        if narrow:
            add(f'<text x="0" y="{y0 + 16}" class="tl-lab{" hot" if k == "new" else ""}">{lane_name(k, lang)}</text>')
    pill = len(f'{t["today"]} · {day}') * 7.6 + 18 if today else 0
    for d in _ticks(span, W):
        add(f'<line x1="{pct(d):.2f}%" x2="{pct(d):.2f}%" y1="{top - 6}" y2="{axis}" class="tl-grid"/>')
        if (0 < d or not narrow) and pct(d) < 96 and abs(px(d) - px(day)) > pill / 2 + 14:   # под «сегодня» не подписываем
            add(f'<text x="{pct(d):.2f}%" y="{axis + 20}" class="tl-tick">{d}</text>')
    add(f'<line x1="0" x2="100%" y1="{axis}" y2="{axis}" class="tl-axis"/>')
    if narrow and px(day) > pill / 2 + 50:
        add(f'<text x="0" y="{axis + 20}" class="tl-tick" text-anchor="start">{t["day"]}</text>')
    if today:                                        # будущее ещё не наступило
        add(f'<rect x="{pct(day):.2f}%" y="{top - 6}" width="{max(0, 100 - pct(day)):.2f}%" height="{axis - top + 6}" class="tl-future"/>')
    add(f'<line x1="0" x2="100%" y1="{rail}" y2="{rail}" class="tl-rail"/>')
    for i, (x, d) in enumerate(signs):               # подвески знаков: в день, когда знак загорелся впервые
        by, left = rail + 14 + i * 21, pct(d) > (55 if narrow else 75)
        add(f'<svg x="{pct(d):.2f}%" y="0" overflow="visible" class="tl-sign"><line x1="0" x2="0" y1="{rail}" y2="{by - 6}"/>'
            f'<circle cx="0" cy="{by}" r="5.5"/><text x="{-11 if left else 11}" y="{by + 4.5}" text-anchor="{"end" if left else "start"}">'
            f'{SIGN[lang][x]} · {d}</text></svg>')
    if warn_day is not None:
        left = pct(warn_day) > 40
        add(f'<svg x="{pct(warn_day):.2f}%" y="0" overflow="visible" class="tl-warn"><rect x="-8" y="22" width="16" height="{axis - 22}"/>'
            f'<line x1="0" x2="0" y1="22" y2="{axis}"/><text x="{-10 if left else 10}" y="16" text-anchor="{"end" if left else "start"}">'
            f'{t["warn_here"]}</text></svg>')
    if today:
        lbl = f'{t["today"]} · {day}'
        w = len(lbl) * 7.6 + 18
        x0 = -w / 2 if 12 < pct(day) < 88 else (-w + 8 if pct(day) >= 88 else -8)
        add(f'<svg x="{pct(day):.2f}%" y="0" overflow="visible" class="tl-today"><line x1="0" x2="0" y1="{top - 6}" y2="{axis}"/>'
            f'<rect x="{x0:.1f}" y="{axis + 6}" width="{w:.1f}" height="22" rx="11"/>'
            f'<text x="{x0 + w / 2:.1f}" y="{axis + 21.5}" text-anchor="middle">{lbl}</text></svg>')
    lo, hi = scale                                   # у схемы высота внутри дорожки растёт с суммой: видна лесенка
    for it in items:
        y0, b0, b1 = pos[it["lane"]]
        if it["lane"] != "new" or hi <= lo:
            it["y"] = (b0 + b1) / 2
        else:
            it["y"] = b1 - 16 - (it["log"] - lo) / (hi - lo) * (b1 - b0 - 16 - 30)
    steps = [it for it in items if it["lane"] == "new" and not it["held"]]
    for a, b in zip(steps, steps[1:]):               # лесенка: переводы новым получателям по порядку дней
        add(f'<line x1="{pct(a["day"]):.2f}%" x2="{pct(b["day"]):.2f}%" y1="{a["y"]:.1f}" y2="{a["y"]:.1f}" class="tl-step"/>'
            f'<line x1="{pct(b["day"]):.2f}%" x2="{pct(b["day"]):.2f}%" y1="{a["y"]:.1f}" y2="{b["y"]:.1f}" class="tl-step"/>')
    for it in sorted(items, key=lambda i: (i["lane"] in HOT, -i["r"])):   # приглушённые снизу, крупные под мелкими
        c, _, _, op = LOOK[it["lane"]]
        x, yy, r = f'{pct(it["day"]):.2f}%', f'{it["y"]:.1f}', it["r"]
        if it["held"]:
            dot = f'<circle cx="{x}" cy="{yy}" r="{r:.1f}" class="tl-held"/>'
        elif it["lane"] in HOT:
            dot = (f'<circle cx="{x}" cy="{yy}" r="{r + 5:.1f}" fill="{c}" opacity=".16"/>'
                   f'<circle cx="{x}" cy="{yy}" r="{r:.1f}" fill="{c}" class="tl-glow" style="--c:{c}"/>')
        else:
            dot = f'<circle cx="{x}" cy="{yy}" r="{r:.1f}" fill="{c}" opacity="{op}"/>'
        add(f'<g class="tl-op"><title>{it["tip"]}</title><circle cx="{x}" cy="{yy}" r="{max(r, 9):.1f}" fill="transparent"/>{dot}</g>')
        if ring is not None and it["n"] == ring:
            add(f'<circle cx="{x}" cy="{yy}" r="{r + 9:.1f}" class="tl-ring"/>')
    # занятые места: яркие точки и кольцо; сначала главные суммы, потом номера шагов вокруг них
    taken = []
    for it in items:
        if it["lane"] in HOT or it["n"] == ring:
            rr = it["r"] + (11 if it["n"] == ring else 2)
            taken.append((px(it["day"]) - rr, px(it["day"]) + rr, it["y"] - rr, it["y"] + rr))
    # суммы у лесенки: на широком экране все, если их немного; на узком только первая, самая крупная и последняя
    few = [i for i in steps if i is steps[0] or i is steps[-1] or i is max(steps, key=lambda s: s["amount"])]
    marks = steps if len(steps) <= 8 and not narrow else few
    cw = 9.0 if narrow else 8.6                       # ширина знака с запасом: подписи не касаются колец
    for it in sorted(marks, key=lambda i: (i is not steps[-1], -i["amount"])):
        txt = f'{money(it["amount"])} ₸'
        w, cx = len(txt) * cw, px(it["day"])
        anchor = "end" if pct(it["day"]) > 92 else "start" if pct(it["day"]) < 5 else "middle"
        x0 = cx - w if anchor == "end" else cx if anchor == "start" else cx - w / 2
        rr = it["r"] + (11 if it["n"] == ring else 2)
        for ty in (it["y"] - rr - 6, it["y"] + rr + 17):          # над точкой, иначе под ней
            box = (x0 - 3, x0 + w + 3, ty - 14, ty + 3)
            if _fits(box, taken):
                taken.append(box)
                add(f'<text x="{pct(it["day"]):.2f}%" y="{ty:.1f}" text-anchor="{anchor}" class="tl-amt">{txt}</text>')
                break
    byn, R = {it["n"]: it for it in items}, 11
    for num, n, cur in calls:                        # ① ② ③: те же номера, что в «Истории по шагам»
        it = byn.get(n)
        if it is None:
            continue
        cx, cy = px(it["day"]), it["y"]
        r = it["r"] + (9 if n == ring else 1)
        g = r + R + 4
        for dx, dy in ((0, -g), (-g * .8, -g * .7), (g * .8, -g * .7), (-g, 0), (g, 0), (0, g),
                       (-g * .8, g * .7), (g * .8, g * .7), (0, -g - 2 * R - 4), (0, -g - 4 * R - 8)):
            box = (cx + dx - R, cx + dx + R, cy + dy - R, cy + dy + R)
            if box[0] >= -4 and box[1] <= W + 6 and _fits(box, taken):
                break
        taken.append(box)
        k = math.hypot(dx, dy) or 1
        add(f'<svg x="{pct(it["day"]):.2f}%" y="0" overflow="visible" class="tl-call{" cur" if cur else ""}">'
            f'<line x1="{dx / k * r:.1f}" y1="{cy + dy / k * r:.1f}" x2="{dx - dx / k * R:.1f}" y2="{cy + dy - dy / k * R:.1f}"/>'
            f'<circle cx="{dx:.1f}" cy="{cy + dy:.1f}" r="{R}"/><text x="{dx:.1f}" y="{cy + dy + 4.5:.1f}">{num}</text></svg>')
    svg = f'<svg class="tl-plot" height="{axis + 34}" role="img" aria-label="{t["tl"]}">{"".join(out)}</svg>'
    if narrow:
        return f'<div class="tl tl-n">{svg}</div>'
    names = "".join(f'<span class="{"hot" if k == "new" else ""}" style="top:{(pos[k][1] + pos[k][2]) / 2}px">'
                    f'{lane_name(k, lang)}</span>' for k in lanes)
    names += f'<span class="ax" style="top:{axis + 15}px">{t["day"]}</span>'
    return f'<div class="tl tl-w"><div class="tl-names">{names}</div>{svg}</div>'


def read_key(t):
    """«Как читать ленту»: три приметы с маленькими рисунками, нарисованными так же, как на ленте."""
    stair = ('<svg width="38" height="20" viewBox="0 0 38 20" aria-hidden="true"><path d="M4 16H14V10H24V4H34" class="k-step"/>'
             '<circle cx="4" cy="16" r="3" class="k-dot"/><circle cx="14" cy="10" r="3.5" class="k-dot"/>'
             '<circle cx="24" cy="4" r="4" class="k-dot"/></svg>')
    pend = ('<svg width="16" height="22" viewBox="0 0 16 22" aria-hidden="true"><line x1="8" x2="8" y1="0" y2="9" class="k-str"/>'
            '<circle cx="8" cy="14" r="5" class="k-pend"/></svg>')
    warn = ('<svg width="14" height="24" viewBox="0 0 14 24" aria-hidden="true"><rect x="2" y="0" width="10" height="24" class="k-band"/>'
            '<line x1="7" x2="7" y1="1" y2="23" class="k-warn"/></svg>')
    return (f'<div class="tlkey"><span class="kt">{t["key_title"]}</span>'
            f'<span>{stair}{t["key_steps"]}</span><span>{pend}{t["key_sign"]}</span><span>{warn}{t["key_warn"]}</span></div>')


def feed_chart(ops, held, day, warn_day, lang, key="feed", today=True, verdicts=(), calls=()):
    """Лента операций дорожками. Масштабы посчитаны по всей истории, поэтому при показе ничего не прыгает."""
    first, t = first_paid(ops), TEXT[lang]
    real = [(i, o) for i, o in enumerate(ops) if o.kind != "salary"]
    span = max(o.day for o in ops) + 2
    gmax, *scale = amount_scale()
    items = []
    for i, o in real:
        if o.day > day:
            continue                                   # будущее не показываем: история раскрывается по дням
        lane = lane_of(o, first)
        _, r0, r1, _ = LOOK[lane]
        tip = (f'{t["day"]} {o.day} · {KIND[lang][o.kind]} · {lane_name(lane, lang)}'
               + (f' · {GROUP["held"][lang != "ru"]}' if i in held else "")
               + f'\n{t["who"]}: {cp_name(o)}\n{money(o.amount)} ₸')
        items.append({"n": i, "day": o.day, "amount": o.amount, "lane": lane, "held": i in held,
                      "log": math.log(max(o.amount, 1)), "r": r0 + (r1 - r0) * math.sqrt(o.amount / gmax),
                      "tip": html.escape(tip)})
    lanes = [k for k in LANES if k == "new" or any(it["lane"] == k for it in items)]
    fired = {}
    for v in verdicts:                                 # первый день каждого знака: те же знаки, что у радара справа
        if v.op.day <= day:
            for x in v.signals:
                fired.setdefault(x, v.op.day)
    signs = sorted(fired.items(), key=lambda kv: (kv[1], list(SIGNAL_RU).index(kv[0])))
    hit = [it for it in items if it["day"] == warn_day]
    ring = max(hit, key=lambda it: it["amount"])["n"] if hit else None
    body = "".join(timeline_svg([dict(it) for it in items], lanes, signs, span, day, warn_day, ring,
                                t, lang, narrow, today, scale, calls) for narrow in (False, True))
    held_pill = (f'<div class="legend"><span><i style="--c:#ecf3ef"></i>{GROUP["held"][lang != "ru"]}</span></div>'
                 if any(it["held"] for it in items) else "")
    with st.container(key=key):
        st.html(f'<div class="tlhead"><b>{t["tl"]}</b></div>{held_pill}')
        st.markdown(f'<div class="tlwrap">{read_key(t)}{body}</div>', unsafe_allow_html=True)   # st.html вырезает SVG, markdown — нет


def card(kind, title, text, extra=""):
    """Крупная карточка состояния: как экран телефона на сайте."""
    st.html(f'<div class="card {kind}" role="status"><b>{title}</b><span>{text}</span>{extra}</div>')


def gauge(label, value, tone, extra=""):
    """Крупное светящееся число с подписью; знак тенге чуть меньше цифр."""
    value = str(value).replace(" ₸", " <small>₸</small>")
    return f'<div class="gauge {tone}"><span>{label}</span><b>{value}</b>{extra}</div>'


def dots(total, full):
    """Бусины: сколько из возможного (например, признаков из пяти)."""
    return '<div class="beads" aria-hidden="true">' + "".join(
        f'<u class="{"on" if i < full else ""}"></u>' for i in range(total)) + "</div>"


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


def describe(op, lang, first):
    """Одна операция словами: «перевод 29 800 ₸ новому получателю: Карта 1234»."""
    t = TEXT[lang]
    what = f"{KIND[lang][op.kind]} {money(op.amount)} ₸"
    if op.kind == "out" and op.cp_type in PEOPLE:
        return f"{what} {t['to_new'] if first[op.cp] > KNOWN_DAYS else t['to_known']}: {cp_name(op)}"
    if op.kind == "in":
        return f"{what}, {t['from']}: {cp_name(op)}"
    if op.kind in REQUESTS:
        return what
    return f"{what}: {cp_name(op)}"


def day_line(ops, day, lang):
    """Подпись к выбранному дню: собрана из операций по шаблону, числа берутся из данных."""
    t, first = TEXT[lang], first_paid(ops)
    past = [o for o in ops if o.day <= day and o.kind != "salary"]
    if not past:
        return t["d_start"].format(day=day), None
    today = [o for o in past if o.day == day]
    op = today[-1] if today else past[-1]
    if today:
        more = t["d_more"].format(n=len(today) - 1) if len(today) > 1 else ""
        return t["d_today"].format(day=day, what=describe(op, lang, first)) + more, op
    return t["d_quiet"].format(day=day, last=op.day, what=describe(op, lang, first)), op


def first_fired(verdicts, day):
    """Первая проверка, на которой загорелся каждый знак, не позже выбранного дня."""
    fired = {}
    for v in verdicts:
        if v.op.day <= day:
            for x in v.signals:
                fired.setdefault(x, v)
    return fired


def story_steps(ops, result, held, decision, day, lang, saved):
    """Ключевые моменты до выбранного дня: из операций и знаков радара. Все числа из данных."""
    t, first = TEXT[lang], first_paid(ops)

    def where(op):
        return next((i for i, o in enumerate(ops) if o == op), None)
    alive = [(i, o) for i, o in enumerate(ops) if o.day <= day and i not in held]
    steps = []                                         # день, порядок, текст, операция, знаки
    totals = {}
    for i, o in alive:
        if lane_of(o, first) == "new":
            totals[o.cp] = totals.get(o.cp, 0) + o.amount
    if totals:                                         # главный незнакомый получатель: кому ушло больше всего
        paid = [(i, o) for i, o in alive if lane_of(o, first) == "new" and o.cp == max(totals, key=totals.get)]
        i0, o0 = paid[0]
        steps.append([o0.day, 0, t["st_first"].format(day=o0.day, sum=money(o0.amount)), i0, ()])
        top = o0.amount
        for i, o in paid[1:]:
            if o.amount > top:
                steps.append([o.day, 1, t["st_grow"].format(day=o.day, prev=money(top), sum=money(o.amount)), i, ()])
                break
            top = max(top, o.amount)
    fired = first_fired(result.verdicts, day)
    warn = result.first_warn if result.first_warn and result.first_warn.op.day <= day else None
    for x, v in fired.items():
        sign, n, d = SIGN[lang][x], where(v.op), v.op.day
        if x == "bait":
            back = [(i, o) for i, o in alive if o.day <= d and lane_of(o, first) == "back"]
            if back:
                n, o = back[-1]
                d, text = o.day, t["st_bait"].format(day=o.day, sum=money(o.amount), sign=sign.lower())
            else:
                text = t["st_sign"].format(day=d, sign=sign, gloss=GLOSS[lang][x])
        elif x == "ladder":
            text = t["st_ladder"].format(day=d, sign=sign)
        elif x == "drain":
            reqs = [(i, o) for i, o in enumerate(ops) if o.kind in REQUESTS and o.day <= d]
            if reqs:
                n, o = reqs[-1]
                d, text = o.day, t["st_req_sign"].format(day=o.day, what=REQ[lang][o.kind], sum=money(o.amount), sign=sign)
            else:
                text = t["st_sign"].format(day=d, sign=sign, gloss=GLOSS[lang][x])
        else:
            text = t["st_sign"].format(day=d, sign=sign, gloss=GLOSS[lang][x])
        if n in held and v is not warn:
            continue                                   # операция не прошла: клиент остановил переводы
        if v is warn:
            text += ". " + t["st_tail"].format(nth=NTH[lang][min(len(v.signals), 5)])
        steps.append([d, 3 if v is warn else 2, text, n, (x,)])
    for i, o in alive:                                 # заявка без знака «Опустошение» тоже важна
        if o.kind in REQUESTS and all(s[3] != i for s in steps):
            steps.append([o.day, 2, t["st_req"].format(day=o.day, what=REQ[lang][o.kind], sum=money(o.amount)), i, ()])
    if warn and all(s[1] != 3 for s in steps):
        steps.append([warn.op.day, 3, t["st_warn"].format(day=warn.op.day, n=len(warn.signals)), where(warn.op), ()])
    pause = result.first_pause
    if pause and pause.op.day <= day and not (decision and decision[1] < pause.op.day):
        steps.append([pause.op.day, 4, t["st_pause"].format(day=pause.op.day), where(pause.op), ()])
    if decision and decision[1] <= day:
        key = "st_stop" if decision[0] == "stop" else "st_go"
        steps.append([decision[1], 5, t[key].format(day=decision[1], sum=money(saved)),
                      where(result.first_warn.op) if result.first_warn else None, ()])
    signed = {s[3] for s in steps if s[1] >= 2}
    steps = [s for s in steps if not (s[1] == 1 and s[3] in signed)]   # рост и знак на одной точке: оставляем знак
    steps.sort(key=lambda s: (s[0], s[1]))
    out = [{"num": k + 1, "day": d, "text": text, "n": n, "signs": signs, "cur": k == len(steps) - 1}
           for k, (d, _, text, n, signs) in enumerate(steps)]
    calm = None
    if not warn:
        most = max((len(v.signals) for v in result.verdicts if v.op.day <= day), default=0)
        word = "признак" if most % 10 == 1 and most % 100 != 11 else "признака" if most % 10 in (2, 3, 4) else "признаков"
        calm = t["st_calm0"] if most == 0 else t["st_calm"].format(n=most, word=word)
    return out, calm


def story_list(steps, calm, lang):
    """«История по шагам»: каждый шаг — кнопка, она переводит ленту на свой день."""
    t = TEXT[lang]
    with st.container(key="story"):
        st.html(f'<div class="sthead"><b>{t["story"]}</b><span>{t["story_tip"] if steps else t["st_none"]}</span></div>')
        for s in steps:
            st.button(s["text"], key=f'step_{s["num"]}', width="stretch",
                      type="primary" if s["cur"] else "secondary", on_click=set_state, kwargs={"day": s["day"], "playing": False})
        if calm:
            st.html(f'<p class="stcalm" role="status"><i></i>{calm}</p>')


def radar_panel(now, day, warn_day, lang, fired=None):
    """Пять подвесок тұмара: горит та, чей признак сработал на последней проверенной операции."""
    t, n = TEXT[lang], len(now)
    pend = ""
    for x, h in zip(SIGNAL_RU, (14, 40, 26, 48, 18)):
        on = x in now
        tick = '<em aria-hidden="true">✓</em>' if on else ""
        pend += (f'<li class="pd{" on" if on else ""}" style="--h:{h}px" title="{SIGN[lang][x]}: {GLOSS[lang][x]}">'
                 f'<i class="str" aria-hidden="true"></i><span class="bead"><i class="ic ic-{x}" aria-hidden="true"></i>{tick}</span>'
                 f'<b>{SIGN[lang][x]}</b><small>{t["lit"] if on else "—"}</small></li>')
    state = t["r0"] if n == 0 else t["r1"] if n == 1 else t["r2"].format(n=n)
    if n < 2 and warn_day is not None and day >= warn_day:
        state += " " + t["r_was"].format(day=warn_day)
    fired = fired or {}

    def at(x):                                         # где на ленте точка, из-за которой знак загорелся
        if x not in fired:
            return ""
        d, what, num = fired[x]
        ref = f' · {t["step_ref"].format(n=num)}' if num else ""
        return f'<small class="at">{t["fired_at"].format(day=d, what=what)}{ref}</small>'
    lit = "".join(f'<li><b>{SIGN[lang][x]}</b><span>{GLOSS[lang][x]}{at(x)}</span></li>' for x in now)
    return (f'<div class="radar lv{min(n, 2)}"><div class="rhead"><span>{t["radar"]}</span><em>{t["day"]} {day}</em></div>'
            f'<div class="amulet" aria-hidden="true"><i class="roof"></i></div><ul class="pends">{pend}</ul>'
            f'<div class="meter"><div class="count"><b>{n}</b><span>{t["of5"]}</span></div>'
            f'<div class="scale"><span class="{"" if n >= 2 else "on"}">{t["silent"]}</span>'
            f'<span class="{"on hot" if n >= 2 else ""}">{t["loud"]}</span></div></div>'
            f'<p class="rstate" role="status">{state}</p>' + (f'<ul class="litlist">{lit}</ul>' if lit else "") + "</div>")


def screen_client():
    """Экран клиента. Работает как отдельный кусок страницы, поэтому отвечает быстро."""
    s = st.session_state
    s.setdefault("decisions", {})
    s.setdefault("playing", False)
    s.setdefault("panel", None)
    lang = s.get("lang") or "ru"
    t = TEXT[lang]

    with st.container(key="setup"):
        left, right = st.columns([1.25, 1], gap="large", vertical_alignment="top")
        sid = left.selectbox(t["history"], shown_order(), format_func=client_name, key="sid", on_change=reset_client)
        left.caption(t["story_hint"])
        with right:
            consent = st.toggle(t["consent"], key="consent")
            st.caption(t["consent_hint"])
    ops = load_clients()[sid][2]
    last = max(o.day for o in ops)
    s.setdefault("day", min(START_DAY, last))

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

    with st.container(key="player"):
        day = st.slider(t["day"], 0, last, key="day")
        with st.container(key="controls"):        # на телефоне четыре кнопки встают сеткой 2 × 2
            b = st.columns([1, 1.5, 1.3, 1.5])
            days = sorted({o.day for o in ops if o.kind != "salary"})
            before, after = [d for d in days if d < day], [d for d in days if d > day]
            b[0].button(t["prev"], icon=":material/arrow_back:", key="b_prev", width="stretch", disabled=not before, on_click=set_state,
                        kwargs={"day": before[-1] if before else 0, "playing": False})
            b[1].button(t["next"], icon=":material/arrow_forward:", key="b_next", width="stretch", disabled=not after, on_click=set_state,
                        kwargs={"day": after[0] if after else last, "playing": False})
            if b[2].button(t["stop_play"] if s["playing"] else t["play"], key="b_play", width="stretch", disabled=not after and not s["playing"],
                           icon=":material/stop:" if s["playing"] else ":material/play_arrow:", type="primary",
                           on_click=set_state, kwargs={"playing": not s["playing"]}):
                st.rerun()                         # перезапуск страницы включает или выключает таймер
            b[3].button(t["to_warn"], icon=":material/notifications_active:", key="b_warn", width="stretch", disabled=warn_day is None or warn_day == day,
                        on_click=set_state, kwargs={"day": warn_day or day, "playing": False})

    warned = warn_day is not None and day >= warn_day
    first = first_paid(ops)
    seen = [v for v in result.verdicts if v.op.day <= day]
    now = seen[-1].signals if seen else ()
    line, cur = day_line(ops, day, lang)
    st.html(f'<div class="now{" hot" if len(now) >= 2 else ""}" role="status" aria-live="polite"><i></i><span>{line}</span></div>')

    # В день предупреждения операция ещё ждёт решения клиента, поэтому не считаем её ушедшей.
    waits = {i for i, o in enumerate(ops) if o == result.first_warn.op} if day == warn_day and not decision else set()
    sent = sent_to_new(ops, held | waits, day, first)
    saved = sum(ops[i].amount for i in held if ops[i].kind == "out")
    waiting = bool(consent and pause_day and day >= pause_day and not decision)
    steps, calm = story_steps(ops, result, held, decision, day, lang, saved)
    num_of = {x: s["num"] for s in steps for x in s["signs"]}
    fired = {x: (v.op.day, f"{KIND[lang][v.op.kind]} {money(v.op.amount)} ₸", num_of.get(x))
             for x, v in first_fired(result.verdicts, day).items()}

    phone_col, radar_col = st.columns([1, 1.3], gap="large")
    with radar_col:
        st.html(radar_panel(now, day, warn_day, lang, fired))
        st.html(f'<div class="gauges{" two" if decision and decision[0] == "stop" else ""}">' + gauge(t["m_sent"], f"{money(sent)} ₸", "carn")
                + (gauge(t["m_saved"], f"{money(saved)} ₸", "turq") if decision and decision[0] == "stop" else "")
                + "</div>")
    with phone_col:
        def what(op):
            return f"{KIND[lang][op.kind]}, {money(op.amount)} ₸"
        if decision and day >= decision[1]:
            key = "stopped" if decision[0] == "stop" else "go"
            state = ("ok" if key == "stopped" else "go", t[key], t[key + "_sub"].format(day=decision[1], sum=money(saved)))
        elif waiting:
            state = ("hold", t["held"], t["held_sub"].format(what=what(result.first_pause.op).capitalize(), day=pause_day))
        elif warned:
            state = ("warn", t["warn"], t["warn_sub"].format(day=warn_day, what=what(result.first_warn.op)))
        else:
            state = ("calm", t["calm"], t["calm_sub"])
        focus = (result.first_pause.op if waiting else result.first_warn.op) if warned and not decision else cur
        with st.container(key="phone_" + state[0]):   # экран телефона, как на сайте: операция, карточка, причины, кнопки
            head = f'<div class="ph-top"><span>{t["phone"]}</span><em>{t["day"]} {day}</em></div>'
            if focus is not None:
                label = t["last_op"] if focus is cur else KIND[lang][focus.kind].capitalize()
                head += (f'<div class="ph-op"><span>{label} · {t["day"].lower()} {focus.day}</span>'
                         f'<b>{money(focus.amount)}<small>₸</small></b><p>{describe(focus, lang, first)}</p></div>')
            st.html(head)
            if warned:
                reasons = list(dict.fromkeys(result.first_warn.signals + (result.first_pause.signals if waiting else ())))
                tags = "".join(f"<i>{SIGN[lang][r]}</i>" for r in reasons)
                card(*state, extra=f'<div class="tags">{tags}</div>')
                st.html(f'<div class="whyhead">{t["why"]}</div>'
                        + "".join(f'<div class="why"><i></i><span><b>{SIGN[lang][r]}.</b> {REASON[lang][r]}</span></div>' for r in reasons)
                        + f'<p class="note">{t["note"]}</p>')
            else:
                card(*state)
            with st.container(key="acts"):
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

    feed_chart(ops, held, day, warn_day if warned else None, lang, key="feed_client", verdicts=result.verdicts,
               calls=[(s["num"], s["n"], s["cur"]) for s in steps if s["n"] is not None])
    story_list(steps, calm, lang)

    with st.expander(t["gloss"], icon=":material/help:"):
        st.html('<ul class="gloss">' + "".join(
            f'<li><span class="bead sm"><i class="ic ic-{x}" aria-hidden="true"></i></span>'
            f'<b>{SIGN[lang][x]}</b><span>{GLOSS[lang][x]}</span></li>' for x in SIGNAL_RU)
            + f'</ul><p class="note">{t["rule"]}</p>')
    with st.expander(t["ops"], icon=":material/list:"):
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
    lines = ["digraph g {", 'rankdir=LR; bgcolor=transparent; node [shape=box, style="rounded,filled", fontname="Golos Text", '
             'fontsize=12, color="#2a3438", fillcolor="#10171a", fontcolor="#ecf3ef", penwidth=1.2, margin="0.18,0.08"];',
             'edge [color="#aab6b166", arrowsize=.6, penwidth=1.1, fontname="Golos Text", fontsize=10, fontcolor="#8b9792"];']
    n = 0
    for cp, pays in shared.items():
        fresh = [(d, c) for d, c in pays if d > KNOWN_DAYS and d - pays[0][0] <= 30]
        if len({c for _, c in fresh}) < 6:
            continue
        n += 1
        lines.append(f'"r{n}" [label="Получатель {n}\\nклиентов: {len(fresh)}", fillcolor="#ff5a3c", color="#ff8a70", fontcolor="#1f0503", penwidth=2];')
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
    paused = int(df["Пауза, день"].notna().sum())
    rail = lambda n, c: f'<div class="rail" aria-hidden="true"><i style="--w:{100 * n / max(len(df), 1):.1f}%;--c:{c}"></i></div>'
    hint = lambda text: f'<p class="hint">{text}</p>'
    st.html('<div class="figs">'
            + gauge("Клиентов", len(df), "silver", rail(len(df), "rgba(233,242,238,.7)")
                    + hint("Все вымышленные истории учебного набора: и честные, и с обманом."))
            + gauge("С предупреждением", warned, "carn", rail(warned, "#ff5a3c")
                    + hint("Радар хотя бы раз увидел два признака сразу и предупредил клиента."))
            + gauge("С паузой при согласии", paused, "amber", rail(paused, "#ffc45c")
                    + hint("Столько заявок на депозит или кредит встало бы на паузу, если бы клиент заранее включил режим защиты."))
            + "</div>")

    st.subheader("Дела")
    st.caption("Каждая карточка — клиент, которого радар предупредил: когда, по каким признакам и что было бы с паузой.")
    a, b = st.columns([2, 1], vertical_alignment="bottom")
    wanted = a.multiselect("Показать с признаками", list(SIGNAL_RU.values()), placeholder="Любые признаки")
    only = b.toggle("Только с предупреждением", value=True)
    view = df[df["Предупреждение, день"].notna()] if only else df
    for x in wanted:
        view = view[view["Признаки"].str.contains(x)]
    view = view.sort_values("Предупреждение, день", na_position="last").reset_index(drop=True)
    s = st.session_state
    shown = view.head(6)
    with st.container(key="cases_grid"):
        cols = st.columns(3)
        for i, row in shown.iterrows():
            with cols[i % 3], st.container(key=f"case_{i}"):
                w, p = row["Предупреждение, день"], row["Пауза, день"]
                chips = "".join(f"<i>{x}</i>" for x in row["Признаки"].split(", ") if x)
                did = (f"Предупредил в день {int(w)}. " + (f"С согласием — пауза в день {int(p)}." if pd.notna(p) else "Пауза не понадобилась.")
                       if pd.notna(w) else "Предупреждений нет: двух признаков сразу не было.")
                st.html(f'<div class="case{" quiet" if pd.isna(w) else ""}"><div class="ch"><b>{row["Клиент"]}</b>'
                        + (f'<em>{t_day(w)}</em>' if pd.notna(w) else "") + f'</div><div class="chips">{chips}</div><p>{did}</p></div>')
                st.button("Открыть дело", key=f"open_{row['sid']}", icon=":material/folder_open:", width="stretch",
                          on_click=set_state, kwargs={"case": row["sid"]})
    st.caption(f"Найдено: {len(view)}. Сверху — первые {len(shown)} по дню предупреждения; остальные в таблице ниже.")
    with st.expander(f"Все дела таблицей ({len(view)})", icon=":material/table_rows:"):
        st.caption("Выберите строку, чтобы открыть дело.")
        pick = st.dataframe(view.drop(columns="sid"), hide_index=True, width="stretch", height=330, key="cases",
                            on_select="rerun", selection_mode="single-row")
    chosen = [i for i in pick.selection.rows if i < len(view)]
    sid = view.loc[chosen[0], "sid"] if chosen else s.get("case")
    if sid in found_ids(found):
        r = found[(sid, True)]
        with st.container(key="casefile"):
            st.subheader(client_name(sid))
            if r.first_warn:
                ops = load_clients()[sid][2]
                st.caption("Почему радар предупредил:")
                for x in r.first_warn.signals:
                    st.html(f'<div class="why"><i></i><span><b>{SIGNAL_RU[x].capitalize()}.</b>&nbsp;{REASON["ru"][x]}</span></div>')
                feed_chart(ops, set(), max(o.day for o in ops), r.first_warn.op.day, "ru", key="feed_case", today=False, verdicts=r.verdicts)
                st.download_button("Скачать справку по делу", case_text(sid, r), file_name="spravka.txt", icon=":material/download:")
            else:
                st.info("Предупреждений нет: двух признаков сразу не было.")

    st.subheader("Общие получатели")
    dot, n = shared_dot(shared)
    if n:
        st.caption("Сюда за 30 дней впервые заплатили 6 и больше клиентов. Честный получатель тоже может оказаться здесь, "
                   "поэтому одного этого признака мало.")
        st.caption("Как читать схему: слева клиенты, справа получатель; на стрелке — день первого платежа.")
        st.graphviz_chart(dot, width="content")
    else:
        st.info("Таких получателей нет.")
    footer()


def t_day(value):
    return f"день {int(value)}"


def found_ids(found):
    return {sid for sid, _ in found}


# ---------- экран «Качество» ----------

TESTS = [("Тест 1", 5, 0, 5, 0, "В историях обмана не было депозита и кредита."),
         ("Тест 2", 10, 8, 10, 9, "До него исправили «общего получателя». Пауза: 0 из 5."),
         ("Тест 3", 10, 10, 10, 0, "До него исправили лесенку и наживку. До депозита или кредита: 0 из 4, пауза: 0 из 4.")]
# Вывод по каждому тесту и «до заявки»: те же слова и числа, что на сайте (docs/index.html, раздел о проверке).
TAKE = {"Тест 1": ("Ни одного предупреждения", "Радар промолчал во всех историях.", "—", None),
        "Тест 2": ("Рано — но с тревогами", "Во втором тесте успевали до заявки, зато беспокоили 9 честных клиентов из 10.", "100%", None),
        "Тест 3": ("Ловим — но поздно", "В третьем тесте предупреждение приходило уже после заявки: "
                   "19% денег к этому моменту успевало уйти.", "0 из 4", (4, 0))}


def beads(total, full, css):
    return "".join(f'<u class="{css if i < full else ""}"></u>' for i in range(total))


def russian_names(text):
    for key in sorted(STORY_RU, key=len, reverse=True):
        text = text.replace(key, STORY_RU[key])
    return text


def screen_quality():
    st.subheader("Три слепых теста")
    st.caption("Одна бусина это одна история. Истории придуманы ИИ. Правила после третьего теста не менялись.")
    head = ('<div class="qhead" aria-hidden="true"><span></span><span>Заметили обман</span><span>Ложные тревоги</span>'
            '<span>До заявки</span><span>Вывод</span></div>')
    body = ""
    for name, n, hit, m, false, note in TESTS:
        title, line, before, bb = TAKE[name]
        body += (f'<div class="test{" last" if name == TESTS[-1][0] else ""}"><b>{name}</b>'
                 f'<div class="f-n"><small class="lab">Заметили обман</small><p>{beads(n, hit, "f")}</p><em>{hit}</em> из {n} обманов заметили</div>'
                 f'<div class="h-n"><small class="lab">Ложные тревоги</small><p>{beads(m, false, "h")}</p><em>{false}</em> из {m} честных предупредили зря</div>'
                 f'<div class="b-n"><small class="lab">До заявки</small>' + (f'<p>{beads(bb[0], bb[1], "f")}</p>' if bb else "")
                 + f'<em>{before}</em></div>'
                 f'<div class="tk"><strong>{title}</strong>{line}<span>{note}</span></div></div>')
    st.html(f'<div class="tests">{head}{body}<div class="qlegend"><span><u class="f"></u>Обман: закрашено, если заметили</span>'
            '<span><u class="h"></u>Честные: закрашено, если зря</span><span><u></u>Пустая бусина — не заметили или не тревожили</span></div></div>'
            '<div class="verdict"><b>Значит, порог 2 — компромисс</b><span>Не победа. Чтобы двигаться дальше, нужны обезличенные данные банка, '
            'а не новые подгонки под свои же примеры.</span></div>')
    st.subheader("Подробные отчёты")
    st.caption("Полные таблицы по каждому набору — те же файлы, что в репозитории.")
    files = {"Учебный набор A": "A", "Тест 1": "blind1", "Тест 2": "blind2", "Тест 3": "blind3"}
    choice = st.segmented_control("Отчёт", list(files), default="Тест 3", label_visibility="collapsed") or "Тест 3"
    if choice == "Учебный набор A":
        st.caption("На этом наборе радар настраивали, поэтому для вывода о качестве он не годится.")
    path = ROOT / "docs" / f"metrics_{files[choice]}.md"
    if path.exists():
        body = russian_names(path.read_text(encoding="utf-8")).split("\n", 1)[-1]
        with st.container(key="report"):
            st.markdown(body.replace("\n## ", "\n#### "))
    else:
        st.info(f"Отчёта {path.name} нет. Соберите его командой: python -m radar.evaluate --set A")
    footer()


def footer():
    st.divider()
    st.caption(FOOTER)


def page_style():
    """Оформление: ночная степь и тұмар из точек, как на слайдах."""
    st.html(f"<style>{(ROOT / 'assets' / 'app.css').read_text(encoding='utf-8')}</style>")
    hero = (ROOT / "assets" / "hero.html").read_text(encoding="utf-8")
    if st.session_state.get("lang") == "kz":   # переключатель ниже, но его значение уже в session_state
        hero = (hero.replace('<html lang="ru">', '<html lang="kk">', 1)
                    .replace("Радар медленных мошеннических схем", "Баяу схемалар радары", 1))
    st.iframe(hero, height=270)


def start_demo():
    """Большая кнопка: история Мейрамбека с начала и сразу показ."""
    st.session_state["sid"] = next(iter(DEMO))
    reset_client()
    st.session_state["playing"] = True


def intro(lang):
    """Что это и как смотреть: три шага и одна главная кнопка."""
    t = TEXT[lang]
    steps = "".join(f'<li><span class="n">{i}</span><div><b>{t[f"s{i}"]}</b><small>{t[f"s{i}_sub"]}</small></div></li>'
                    for i in (1, 2, 3))
    with st.container(key="intro"):
        st.html(f'<p class="what">{t["what"]}</p><div class="howto"><span class="hw">{t["how"]}</span><ol class="steps">{steps}</ol></div>')
        st.button(t["cta"], key="cta", type="primary", icon=":material/play_circle:", on_click=start_demo)


def main():
    st.set_page_config(page_title="Тұмар: радар медленных схем", page_icon="🔺", layout="wide")
    page_style()
    with st.container(key="langbar"):
        lang = st.segmented_control("Тіл / Язык", list(LANG_LABEL), default="ru", key="lang",
                                    format_func=LANG_LABEL.get, label_visibility="collapsed") or "ru"
    intro(lang)
    t = TEXT[lang]
    tabs = st.tabs(["Клиент", "Аналитик", "Качество"])
    with tabs[0]:
        st.html(f'<p class="tabcap">{t["tab_client"]}</p>')
        playing = st.session_state.get("playing", False)
        st.fragment(screen_client, run_every=0.45 if playing else None)()
    with tabs[1]:
        st.html(f'<p class="tabcap">{t["tab_analyst"]}</p>')
        st.fragment(screen_analyst)()
    with tabs[2]:
        st.html(f'<p class="tabcap">{t["tab_quality"]}</p>')
        st.fragment(screen_quality)()


main()
