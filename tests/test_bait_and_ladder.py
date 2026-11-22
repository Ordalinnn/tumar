"""Тесты на две правки правил: наживка и лесенка.

1. Наживка: «незнакомцы платили клиенту раньше» — это только те, кого клиент
   до этого поступления не знал: не платил им и от них денег не получал.
2. Лесенка: кроме общего роста нужно хотя бы два «заметных» рекорда
   (>= 1.5 обычного перевода клиента).
"""
from radar.model import Op
from radar.rules import scan


def _signals(ops, day):
    """Сигналы радара на операции указанного дня."""
    result = scan(ops)
    return next((v.signals for v in result.verdicts if v.op.day == day), ())


def test_bait_ignores_money_from_someone_the_client_knew():
    # Клиент раньше уже платил Ивану и получал от него деньги — Иван не незнакомец.
    ops = [
        Op(5, "in", 300_000.0, "зарплата", "employer"),
        Op(20, "out", 8_000.0, "Иван", "person"),
        Op(30, "in", 5_000.0, "Иван", "person"),
        Op(50, "in", 6_000.0, "Пётр", "person"),
        Op(60, "out", 10_000.0, "схема", "person"),
        Op(65, "in", 4_000.0, "схема", "person"),
    ]
    assert "bait" in _signals(ops, 65)


def test_ladder_needs_two_big_records():
    # Рекорды 10 000 -> 20 000 -> 110 000 при обычном переводе 50 000:
    # заметный только последний, поэтому лесенки нет, хотя суммы выросли.
    ops = [
        Op(5, "out", 50_000.0, "аренда", "company"),
        Op(6, "out", 50_000.0, "аренда", "company"),
        Op(7, "out", 50_000.0, "аренда", "company"),
        Op(70, "out", 10_000.0, "схема", "person"),
        Op(75, "out", 20_000.0, "схема", "person"),
        Op(80, "out", 110_000.0, "схема", "person"),
    ]
    assert "ladder" not in _signals(ops, 80)


def test_ladder_still_fires_with_two_big_records():
    # Те же суммы, но второй рекорд 80 000 — уже два заметных, лесенка есть.
    ops = [
        Op(5, "out", 50_000.0, "аренда", "company"),
        Op(6, "out", 50_000.0, "аренда", "company"),
        Op(7, "out", 50_000.0, "аренда", "company"),
        Op(70, "out", 10_000.0, "схема", "person"),
        Op(75, "out", 80_000.0, "схема", "person"),
        Op(80, "out", 110_000.0, "схема", "person"),
    ]
    assert "ladder" in _signals(ops, 80)
