"""Генераторы историй клиентов.

Каждая история — 150 дней обычной жизни плюс сюжет, который начинается около 100-го дня.
Генератор детерминированный: make_client(kind, seed) при одном seed всегда одинаков,
а при разных seed меняются суммы, дни, число переводов и названия новых получателей.
"""
import random

from .model import Op

FRAUD = (
    "fraud_classic",
    "fraud_rotating_cards",
    "fraud_no_bait",
    "fraud_loan",
    "fraud_pyramid",
    "fraud_fee",
    "fraud_fast",
    "fraud_flat_amounts",
    "fraud_via_licensed_exchange",
)

HONEST = (
    "honest_ordinary",
    "honest_licensed_investor",
    "honest_builder",
    "honest_student_child",
    "honest_entrepreneur",
    "honest_friend_loan",
    "honest_car",
    "honest_toy_gifts",
    "honest_kassa",
    "honest_p2p_trader",
    "honest_tutor",
)


# Заявка касается своего вклада или банка-кредитора.
_REQUEST_CP = {"deposit_close": "свой вклад", "loan": "банк"}

# Короткий код сюжета: вместе с seed он делает получателей клиента уникальными.
_KIND_CODE = {kind: f"{i:02d}" for i, kind in enumerate(FRAUD + HONEST, start=1)}


def make_client(kind, seed):
    """Список операций клиента, отсортированный по дню.

    У каждого клиента (сюжет + seed) свои получатели: имена содержат метку tag.
    Общие получатели есть только там, где сюжет этого требует.
    """
    if kind not in _STORY:
        raise ValueError(f"неизвестный сюжет: {kind}")
    rnd = random.Random(f"{kind}:{seed}")
    tag = f"{seed}-{_KIND_CODE[kind]}"
    ops = _everyday(rnd, tag)
    ops += _STORY[kind](rnd, tag)
    return sorted(ops, key=lambda o: o.day)


def _jitter(rnd, value, spread=0.2):
    """Сумма меняется от seed, но остаётся в разумных пределах."""
    return float(round(value * rnd.uniform(1 - spread, 1 + spread), -2))


def _days(rnd, start, count, step):
    """Дни платежей: старт и шаг немного меняются от seed."""
    day, out = start + rnd.randrange(0, 4), []
    for _ in range(count):
        out.append(day)
        day += step + rnd.randrange(0, 4)
    return out


def _everyday(rnd, tag):
    """150 дней обычной жизни: зарплата, покупки, родные и пара мелких переводов.

    Названия получателей включают tag: у разных клиентов свои родные,
    знакомые и магазины, общих получателей нет.
    """
    ops = []
    # зарплата раз в месяц
    for day in (1, 31, 61, 91, 121):
        ops.append(Op(day, "salary", float(rnd.randrange(240, 400) * 1000),
                      f"работа {tag}", "employer"))
    # родные: первые переводы в первые 30 дней истории
    for name, ctype, start in (("мама", "person", 3), ("брат", "wallet", 11), ("дядя", "person", 24)):
        day = start + rnd.randrange(0, 4)
        while day <= 145:
            ops.append(Op(day, "out", float(rnd.randrange(10, 30) * 1000),
                          f"{name} {tag}", ctype))
            day += rnd.randrange(14, 26)
    # покупки
    for day in range(2, 150, 5):
        ops.append(Op(day, "purchase", float(rnd.randrange(1500, 18_000)),
                      f"магазин {tag}", "merchant"))
    # иногда мелкие переводы незнакомым — без роста сумм
    ops.append(Op(44 + rnd.randrange(0, 6), "out", float(rnd.randrange(3, 7) * 1000),
                  f"знакомый {tag}", "person"))
    ops.append(Op(76 + rnd.randrange(0, 6), "out", float(rnd.randrange(3, 7) * 1000),
                  f"сосед {tag}", "person"))
    return ops


# ---------- сюжеты обмана ----------

def _classic(rnd, tag, ctype="person", bait=True, request="deposit_close", cp=None):
    """Схема лже-брокера: лесенка, наживка, заявка и большой перевод."""
    start = 96 + rnd.randrange(0, 9)
    cp = cp or f"лже-брокер {tag}"
    ops = [
        Op(start, "out", _jitter(rnd, 10_000), cp, ctype),
        Op(start + rnd.randrange(5, 8), "out", _jitter(rnd, 30_000), cp, ctype),
    ]
    if bait:
        ops.append(Op(start + rnd.randrange(9, 12), "in", _jitter(rnd, 12_000), cp, ctype))
    ops += [
        Op(start + rnd.randrange(14, 18), "out", _jitter(rnd, 150_000), cp, ctype),
        Op(start + 20, request, _jitter(rnd, 2_000_000, 0.1), _REQUEST_CP[request], "own"),
        Op(start + 21, "out", _jitter(rnd, 1_900_000, 0.1), cp, ctype),
    ]
    return ops


def _fraud_fast(rnd, tag):
    """Та же схема, но всё укладывается в шесть дней."""
    start = 96 + rnd.randrange(0, 5)
    cp = f"лже-брокер {tag}"
    return [
        Op(start, "out", _jitter(rnd, 10_000), cp, "person"),
        Op(start + 1, "out", _jitter(rnd, 30_000), cp, "person"),
        Op(start + 2, "in", _jitter(rnd, 12_000), cp, "person"),
        Op(start + 3, "out", _jitter(rnd, 150_000), cp, "person"),
        Op(start + 4, "deposit_close", _jitter(rnd, 2_000_000, 0.1),
           _REQUEST_CP["deposit_close"], "own"),
        Op(start + 5, "out", _jitter(rnd, 1_900_000, 0.1), cp, "person"),
    ]


def _fraud_rotating_cards(rnd, tag):
    """Мошенники меняют карты на каждый перевод."""
    start = 96 + rnd.randrange(0, 9)
    cards = [f"карта {i} {tag}" for i in range(1, 6)]
    return [
        Op(start, "out", _jitter(rnd, 10_000), cards[0], "person"),
        Op(start + 6, "out", _jitter(rnd, 30_000), cards[1], "wallet"),
        Op(start + 10, "in", _jitter(rnd, 12_000), cards[2], "person"),
        Op(start + 15, "out", _jitter(rnd, 150_000), cards[3], "person"),
        Op(start + 20, "deposit_close", _jitter(rnd, 2_000_000, 0.1),
           _REQUEST_CP["deposit_close"], "own"),
        Op(start + 21, "out", _jitter(rnd, 1_900_000, 0.1), cards[4], "person"),
    ]


def _fraud_pyramid(rnd, tag):
    """Пирамида: один «организатор» на всех, деньги приходят «от участников»."""
    start = 96 + rnd.randrange(0, 7)
    member = f"участник {tag}"
    return [
        Op(start, "out", _jitter(rnd, 15_000), "организатор", "person"),
        Op(start + 4, "in", _jitter(rnd, 3_000), member, "person"),
        Op(start + 8, "out", _jitter(rnd, 40_000), "организатор", "wallet"),
        Op(start + 12, "in", _jitter(rnd, 8_000), member, "person"),
        Op(start + 16, "out", _jitter(rnd, 120_000), "организатор", "wallet"),
        Op(start + 20, "loan", _jitter(rnd, 500_000, 0.1), _REQUEST_CP["loan"], "own"),
        Op(start + 21, "out", _jitter(rnd, 500_000, 0.1), "организатор", "wallet"),
    ]


def _fraud_fee(rnd, tag):
    """Лже-брокер, а в конце просит «доплату за вывод» на новый счёт."""
    ops = _classic(rnd, tag)
    start = ops[0].day
    ops.append(Op(start + 22, "out", _jitter(rnd, 90_000),
                  f"комиссия за вывод {tag}", "wallet"))
    return ops


def _fraud_flat_amounts(rnd, tag):
    """Одинаковые суммы: лесенки нет, схема держится на частых переводах."""
    start = 96 + rnd.randrange(0, 9)
    cp = f"лже-брокер {tag}"
    amount = float(rnd.randrange(40, 61) * 1000)
    return [
        Op(start, "out", amount, cp, "person"),
        Op(start + 6, "out", amount, cp, "person"),
        Op(start + 12, "out", amount, cp, "person"),
        Op(start + 18, "deposit_close", _jitter(rnd, 2_000_000, 0.1),
           _REQUEST_CP["deposit_close"], "own"),
        Op(start + 19, "out", _jitter(rnd, 1_900_000, 0.1), cp, "person"),
    ]


# ---------- честные сюжеты ----------
# Трудные истории: снаружи они похожи на схему, но человек делает обычные дела.

def _honest_builder(rnd, tag):
    """Строитель платит новому поставщику растущими суммами и закрывает вклад."""
    new = f"новый поставщик {tag}"
    days = _days(rnd, 96, 4, 8)
    return [
        Op(10, "out", 120_000, f"поставщик {tag}", "company"),
        Op(days[0], "out", _jitter(rnd, 50_000, 0.1), new, "company"),
        Op(days[1], "out", _jitter(rnd, 110_000, 0.1), new, "company"),
        Op(days[2], "out", _jitter(rnd, 200_000, 0.1), new, "company"),
        Op(days[3], "out", _jitter(rnd, 300_000, 0.1), new, "company"),
        Op(days[3] + rnd.randrange(6, 11), "deposit_close", _jitter(rnd, 3_000_000, 0.1),
           _REQUEST_CP["deposit_close"], "own"),
    ]


def _honest_friend_loan(rnd, tag):
    """Одолжил другу три растущих суммы на новую карту, часть вернулась."""
    card = f"друг карта {tag}"
    days = _days(rnd, 96, 3, 12)
    return [
        Op(18, "out", 20_000, f"друг {tag}", "person"),
        Op(days[0], "out", _jitter(rnd, 40_000, 0.1), card, "person"),
        Op(days[1], "out", _jitter(rnd, 90_000, 0.1), card, "person"),
        Op(days[2], "out", _jitter(rnd, 160_000, 0.1), card, "person"),
        Op(days[2] + rnd.randrange(10, 16), "in", _jitter(rnd, 70_000, 0.1), card, "person"),
    ]


def _honest_p2p_trader(rnd, tag):
    """P2P-трейдер: растущие переводы новым обменникам, деньги возвращаются."""
    names = [f"обменник {i} {tag}" for i in ("А", "Б", "В")]
    days = _days(rnd, 96, 3, 10)
    return [
        Op(days[0], "out", _jitter(rnd, 30_000, 0.1), names[0], "wallet"),
        Op(days[0] + 2, "in", _jitter(rnd, 29_000, 0.1), names[0], "wallet"),
        Op(days[1], "out", _jitter(rnd, 50_000, 0.1), names[1], "wallet"),
        Op(days[1] + 2, "in", _jitter(rnd, 48_000, 0.1), names[1], "wallet"),
        Op(days[2], "out", _jitter(rnd, 90_000, 0.1), names[2], "wallet"),
        Op(days[2] + 2, "in", _jitter(rnd, 88_000, 0.1), names[2], "wallet"),
    ]


def _honest_student_child(rnd, tag):
    """Отец платит за учёбу сыну: новая карта и растущие суммы."""
    card = f"карта сына {tag}"
    days = _days(rnd, 96, 3, 14)
    return [
        Op(6, "out", 40_000, f"сын {tag}", "person"),
        Op(36, "out", 40_000, f"сын {tag}", "person"),
        Op(66, "out", 45_000, f"сын {tag}", "person"),
        Op(days[0], "out", _jitter(rnd, 45_000, 0.1), card, "person"),
        Op(days[1], "out", _jitter(rnd, 90_000, 0.1), card, "person"),
        Op(days[2], "out", _jitter(rnd, 180_000, 0.1), card, "person"),
    ]


def _honest_toy_gifts(rnd, tag):
    """Игрушки внукам: мелкие переводы племяннице, которой платят многие."""
    count = rnd.randrange(4, 6)
    return [Op(day + rnd.randrange(0, 4), "out", float(rnd.randrange(5, 8) * 1000),
               "племянница", "person")
            for day in _days(rnd, 10, count, 28)]


def _honest_tutor(rnd, tag):
    """Репетитору платят многие ученики — это не общий получатель-мошенник."""
    start = 96 + rnd.randrange(0, 8)
    return [Op(start + rnd.randrange(0, 8), "in", float(rnd.randrange(18, 23) * 1000),
               f"ученик {i} {tag}", "person")
            for i in range(1, rnd.randrange(5, 9))]


def _honest_car(rnd, tag):
    """Покупка машины: закрыл вклад и сразу заплатил продавцу."""
    day = 106 + rnd.randrange(0, 9)
    return [
        Op(day, "deposit_close", _jitter(rnd, 3_000_000, 0.1),
           _REQUEST_CP["deposit_close"], "own"),
        Op(day + 1, "out", _jitter(rnd, 3_000_000, 0.1), f"продавец авто {tag}", "person"),
    ]


def _honest_licensed_investor(rnd, tag):
    """Инвестор работает через лицензированного брокера."""
    days = _days(rnd, 96, 3, 7)
    return [
        Op(days[0], "out", _jitter(rnd, 50_000), "брокер", "licensed"),
        Op(days[1], "out", _jitter(rnd, 150_000), "брокер", "licensed"),
        Op(days[2], "in", _jitter(rnd, 20_000), "брокер", "licensed"),
        Op(days[2] + 5, "deposit_close", _jitter(rnd, 2_000_000, 0.1),
           _REQUEST_CP["deposit_close"], "own"),
        Op(days[2] + 6, "out", _jitter(rnd, 1_900_000, 0.1), "брокер", "licensed"),
    ]


def _honest_entrepreneur(rnd, tag):
    """Предприниматель платит трём поставщикам, все — давние контрагенты."""
    ops = []
    for name in ("А", "Б", "В"):
        ops.append(Op(10 + rnd.randrange(0, 15), "out", _jitter(rnd, 70_000),
                      f"поставщик {name} {tag}", "company"))
    for day, name in ((52, "А"), (82, "Б"), (112, "В")):
        ops.append(Op(day + rnd.randrange(0, 5), "out", _jitter(rnd, 80_000),
                      f"поставщик {name} {tag}", "company"))
    return ops


def _honest_kassa(rnd, tag):
    """Снял деньги в кассе: закрытие вклада и выдача наличных."""
    day = 110 + rnd.randrange(0, 6)
    amount = _jitter(rnd, 500_000, 0.1)
    return [
        Op(day, "deposit_close", amount, _REQUEST_CP["deposit_close"], "own"),
        Op(day, "out", amount, "касса", "own"),
    ]


_STORY = {
    "fraud_classic": lambda rnd, tag: _classic(rnd, tag),
    "fraud_rotating_cards": _fraud_rotating_cards,
    "fraud_no_bait": lambda rnd, tag: _classic(rnd, tag, bait=False),
    # Кредит вместо вклада: схема та же, только заявка на кредит.
    "fraud_loan": lambda rnd, tag: _classic(rnd, tag, request="loan"),
    "fraud_pyramid": _fraud_pyramid,
    "fraud_fee": _fraud_fee,
    # Всё быстро: сюжет укладывается в несколько дней.
    "fraud_fast": _fraud_fast,
    "fraud_flat_amounts": _fraud_flat_amounts,
    # Слепое пятно: весь обман идёт через лицензированную биржу.
    "fraud_via_licensed_exchange": lambda rnd, tag: _classic(rnd, tag, ctype="licensed"),
    "honest_ordinary": lambda rnd, tag: [],
    "honest_licensed_investor": _honest_licensed_investor,
    "honest_builder": _honest_builder,
    "honest_student_child": _honest_student_child,
    "honest_entrepreneur": _honest_entrepreneur,
    "honest_friend_loan": _honest_friend_loan,
    "honest_car": _honest_car,
    "honest_toy_gifts": _honest_toy_gifts,
    "honest_kassa": _honest_kassa,
    "honest_p2p_trader": _honest_p2p_trader,
    "honest_tutor": _honest_tutor,
}
