"""Правила радара.

Радар на каждом шаге видит только прошлое клиента и текущую операцию:
никакие правила не заглядывают в будущее. Про обман радар не знает —
он только складывает сигналы и считает их количество.
"""
from dataclasses import dataclass
from statistics import median

from .model import Op

# Получатели, которых радар вообще рассматривает.
RECIPIENT_TYPES = ("person", "wallet", "company")
# Операции, на которых радар может поставить паузу.
REQUESTS = ("deposit_close", "loan")

# Объяснения сигналов простыми словами: только то, что видно по переводам.
REASONS = {
    "ladder": "Суммы переводов новым получателям растут — похоже, клиента раскручивают.",
    "bait": "Похоже, получатель один раз вернул деньги, чтобы усыпить осторожность.",
    "drain": "Похоже, крупная сумма уходит сразу после закрытия вклада или кредита.",
    "shared": "Похоже, этому получателю переводят деньги многие клиенты банка.",
    "fee": "Похоже, после крупного перевода клиент платит меньшую сумму новому получателю.",
}


@dataclass
class Config:
    """Все пороги радара в одном месте. Стартовые числа подбираются на наборе A."""

    fresh_window_days: int = 60        # «в последние 60 дней»
    history_quiet_days: int = 30       # «не в первые 30 дней истории»
    ladder_records: int = 3            # сколько рекордов суммы подряд нужно
    ladder_growth: float = 3.0         # последний рекорд >= 3 x первого
    ladder_vs_usual: float = 2.0       # последний рекорд >= 2 x обычного перевода
    ladder_strong: float = 1.5         # «заметный» рекорд: >= 1.5 x обычного перевода
    ladder_strong_records: int = 2     # сколько заметных рекордов нужно
    usual_default: float = 20_000      # обычный перевод, если истории нет
    bait_share: float = 0.6            # наживка <= 60% уже отправленного
    bait_strangers_before: int = 1     # сколько раз незнакомцы платили до окна F
    bait_lookback_days: int = 60
    drain_min_transfers: int = 2       # 2+ перевода новым получателям
    drain_after_days: int = 3          # перевод в течение 3 дней после заявки
    drain_after_share: float = 0.4     # ... на >= 40% суммы заявки
    shared_min_others: int = 5         # ещё >= 5 других клиентов
    shared_window_days: int = 30
    fee_min_share: float = 0.03        # доплата 3-30% отправленного за 30 дней
    fee_max_share: float = 0.30
    fee_window_days: int = 30
    warn_signals: int = 2              # 2+ сигнала — предупреждение
    pause_signals: int = 3             # 3+ сигнала — пауза (вместе с drain)


@dataclass(frozen=True)
class Verdict:
    """Что радар думает про одну операцию."""

    op: Op
    signals: tuple
    level: str   # "ok" или "warn"
    pause: bool

    def reasons(self) -> list:
        """По одной понятной фразе на каждый сработавший сигнал."""
        return [REASONS[s] for s in self.signals]


@dataclass(frozen=True)
class Result:
    """Итог прохода радара по всей истории."""

    verdicts: list
    first_warn: object   # Verdict или None
    first_pause: object  # Verdict или None


def shared_recipients(clients):
    """{client_id: [Op, ...]} -> {получатель: [(день, client_id), ...]} первых платежей."""
    first = {}
    for client_id, ops in clients.items():
        seen = {}
        for op in sorted(ops, key=lambda o: o.day):
            if op.kind == "out" and op.cp_type in RECIPIENT_TYPES and op.cp not in seen:
                seen[op.cp] = op.day
                first.setdefault(op.cp, []).append((op.day, client_id))
    return {cp: sorted(payments) for cp, payments in first.items()}


def scan(ops, client_id=None, shared=None, consent=False, cfg=Config()):
    """Проходим историю по дням и выносим вердикт по каждой проверяемой операции."""
    ops = sorted(ops, key=lambda o: o.day)
    first_day = ops[0].day if ops else 0

    verdicts = []
    for i, op in enumerate(ops):
        if not _checked(op):
            continue
        # Радар видит только прошлое и текущую операцию: операции этого же дня,
        # которые идут позже, ему ещё не известны.
        history = ops[: i + 1]
        signals = _signals(history, op, first_day, client_id, shared, cfg)
        level = "warn" if len(signals) >= cfg.warn_signals else "ok"
        verdicts.append(Verdict(op, tuple(signals), level, _pause(op, signals, consent, cfg)))

    first_warn = next((v for v in verdicts if v.level == "warn"), None)
    first_pause = next((v for v in verdicts if v.pause), None)
    return Result(verdicts, first_warn, first_pause)


def _checked(op):
    """Проверяем переводы людям и кошелькам, а также заявки на депозит и кредит."""
    if op.kind in REQUESTS:
        return True
    return op.kind in ("out", "in") and op.cp_type in RECIPIENT_TYPES


def _signals(history, op, first_day, client_id, shared, cfg):
    """Все сигналы, которые видны на этот день."""
    first = _first_payments(history)
    fresh = _fresh(first, op.day, first_day, cfg)

    signals = []
    if _ladder(history, fresh, first, cfg):
        signals.append("ladder")
    if _bait(history, fresh, first, cfg):
        signals.append("bait")
    if _drain(history, op, fresh, cfg):
        signals.append("drain")
    if _shared(fresh, op, client_id, shared, cfg):
        signals.append("shared")
    # Доплату за вывод считаем только вместе с лесенкой, наживкой или опустошением.
    if set(signals) & {"ladder", "bait", "drain"} and _fee(history, fresh, first, cfg):
        signals.append("fee")
    return signals


def _pause(op, signals, consent, cfg):
    """Пауза — только на заявке, только по согласию клиента."""
    if not consent or op.kind not in REQUESTS:
        return False
    found = set(signals)
    if "drain" in found and ({"bait", "shared"} & found):
        return True
    return len(found) >= cfg.pause_signals


def _first_payments(history):
    """Когда клиент впервые заплатил каждому получателю."""
    first = {}
    for op in history:
        if op.kind == "out" and op.cp_type in RECIPIENT_TYPES:
            first.setdefault(op.cp, op.day)
    return first


def _out_to(history, recipients):
    """Переводы этим получателям."""
    return [op for op in history
            if op.kind == "out" and op.cp_type in RECIPIENT_TYPES and op.cp in recipients]


def _fresh(first, day, first_day, cfg):
    """Новые получатели F: первый платёж в последние 60 дней и не в первые 30 дней."""
    return {cp for cp, paid in first.items()
            if paid <= day
            and day - paid <= cfg.fresh_window_days
            and paid - first_day >= cfg.history_quiet_days}


def _ladder(history, fresh, first, cfg):
    """Лесенка: три рекорда суммы подряд, последний сильно больше первого."""
    transfers = _out_to(history, fresh)
    if not transfers:
        return False

    records, best = [], 0.0
    for op in transfers:
        if op.amount > best:      # каждый новый рекорд суммы
            records.append(op)
            best = op.amount
    if len(records) < cfg.ladder_records:
        return False

    start = min(first[cp] for cp in fresh)
    before = [op.amount for op in history if op.kind == "out" and op.day < start]
    usual = median(before) if before else cfg.usual_default
    # Заметных рекордов должно быть хотя бы два: иначе лесенка — это один выброс.
    strong = [op for op in records if op.amount >= cfg.ladder_strong * usual]
    last, first_record = records[-1].amount, records[0].amount
    return (len(strong) >= cfg.ladder_strong_records
            and last >= cfg.ladder_growth * first_record
            and last >= cfg.ladder_vs_usual * usual)


def _bait(history, fresh, first, cfg):
    """Наживка: после первого перевода в F деньги один раз вернулись."""
    if not fresh:
        return False
    start = min(first[cp] for cp in fresh)

    strangers = _strangers_before(history, start, cfg)
    if len(strangers) > cfg.bait_strangers_before:
        return False

    sent, seen_in, found = 0.0, set(), False
    known = set(first)          # кому клиент уже платил — это не незнакомцы
    for op in history:
        if op.kind == "out" and op.cp in fresh:
            sent += op.amount
        elif op.kind == "in" and op.cp_type in RECIPIENT_TYPES:
            stranger = op.cp not in seen_in and op.cp not in known
            seen_in.add(op.cp)
            if op.day > start and (op.cp in fresh or stranger) and op.amount <= cfg.bait_share * sent:
                found = True
    return found


def _strangers_before(history, start, cfg):
    """Входящие до схемы только от незнакомцев.

    Незнакомец — тот, с кем у клиента до этого поступления не было операций
    ни в одну сторону: он ему не платил и от него денег не получал.
    """
    strangers = []
    for i, op in enumerate(history):
        if op.kind != "in" or op.cp_type not in RECIPIENT_TYPES:
            continue
        if not start - cfg.bait_lookback_days <= op.day < start:
            continue
        known = any(prev.cp == op.cp and prev.kind in ("out", "in") for prev in history[:i])
        if not known:
            strangers.append(op)
    return strangers


def _drain(history, op, fresh, cfg):
    """Опустошение: заявка при 2+ переводах в F или перевод сразу после заявки."""
    transfers = _out_to(history, fresh)
    if op.kind in REQUESTS:
        if len(transfers) >= cfg.drain_min_transfers and transfers:
            if op.amount >= max(t.amount for t in transfers):
                return True
    if op.kind == "out" and op.cp in fresh:
        for req in history:
            if req.kind in REQUESTS and 0 <= op.day - req.day <= cfg.drain_after_days:
                if op.amount >= cfg.drain_after_share * req.amount:
                    return True
    return False


def _shared(fresh, op, client_id, shared, cfg):
    """Общий получатель: в последний месяц ему впервые платили ещё 5+ клиентов.

    Получателя, которому любой клиент впервые заплатил больше 60 дней назад,
    не считаем: это давнее знакомство, а не свежий сбор денег у многих.
    """
    if not shared or not client_id:
        return False
    for cp in fresh:
        payments = shared.get(cp, ())
        if not payments:
            continue
        # payments отсортированы, первый — самый ранний первый платёж всех клиентов.
        if op.day - payments[0][0] > cfg.fresh_window_days:
            continue
        others = {cid for day, cid in payments
                  if cid != client_id and 0 <= op.day - day <= cfg.shared_window_days}
        if len(others) >= cfg.shared_min_others:
            return True
    return False


def _fee(history, fresh, first, cfg):
    """Доплата за вывод: новый получатель, 3-30% отправленного за 30 дней, возврата нет."""
    transfers = _out_to(history, fresh)
    if not transfers:
        return False
    biggest = max(transfers, key=lambda o: (o.amount, o.day))

    for op in history:
        if op.kind != "out" or op.day <= biggest.day:
            continue
        if first.get(op.cp) != op.day:       # только новый получатель
            continue
        # Долю считаем только от переводов новым получателям (F).
        sent = sum(o.amount for o in history
                   if o.kind == "out" and o.cp in fresh
                   and o.day >= op.day - cfg.fee_window_days)
        if sent <= 0:
            continue
        if cfg.fee_min_share <= op.amount / sent <= cfg.fee_max_share:
            # Возврат от нового получателя или от незнакомца после крупного перевода.
            back = any(o.kind == "in" and o.day >= biggest.day
                       and (o.cp in fresh or o.cp not in first)
                       for o in history)
            if not back:
                return True
    return False
