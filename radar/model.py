"""Модель данных радара: одна операция по счёту клиента."""
from dataclasses import dataclass


@dataclass(frozen=True)
class Op:
    """Одна операция. День считается от начала истории клиента."""

    day: int
    # out, in, purchase, salary, deposit_close, loan
    kind: str
    amount: float
    # получатель или плательщик: "мама", "лже-брокер", "магазин"
    cp: str
    # person, wallet, company, licensed, merchant, employer, own
    cp_type: str
