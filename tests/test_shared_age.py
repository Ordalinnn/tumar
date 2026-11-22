"""Общий получатель не должен считаться общим, если он «старый».

Правило: если любому клиенту банка этот получатель впервые встретился больше
60 дней назад, сигнал `shared` не ставим — это давнее знакомство, а не сбор.
"""
from radar.model import Op
from radar.rules import scan, shared_recipients


def _clients(first_days):
    """Клиенты, которые впервые платят одному и тому же получателю в указанные дни."""
    clients = {}
    for client_id, day in first_days.items():
        clients[client_id] = [
            Op(day - 30, "purchase", 5_000.0, "магазин", "merchant"),
            Op(day, "out", 30_000.0, "общий", "person"),
        ]
    return clients


def _has_shared(clients, client_id):
    shared = shared_recipients(clients)
    result = scan(clients[client_id], client_id=client_id, shared=shared)
    return any("shared" in verdict.signals for verdict in result.verdicts)


def test_old_recipient_is_not_shared():
    # Первый платёж был на 95-й день, проверяем 160-й: 65 дней назад — больше 60.
    clients = _clients({"A": 95, "B": 155, "C": 155, "D": 156, "E": 156, "F": 157, "G": 160})
    assert _has_shared(clients, "G") is False


def test_recent_recipient_is_still_shared():
    # Тот же расклад, но первый платёж на 130-й день: 30 дней назад — считаем.
    clients = _clients({"A": 130, "B": 155, "C": 155, "D": 156, "E": 156, "F": 157, "G": 160})
    assert _has_shared(clients, "G") is True
