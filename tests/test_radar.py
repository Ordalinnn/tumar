"""Тесты написаны до кода: каждая история короткая и понятная вручную."""
import pytest

from radar.model import Op
from radar.rules import REASONS, scan, shared_recipients
from radar.scenarios import FRAUD, HONEST, make_client


def base():
    """Обычная жизнь: зарплата, покупки и переводы знакомому человеку."""
    ops = [Op(d, "salary", 300_000, "employer", "employer") for d in (1, 31, 61, 91)]
    ops += [Op(d, "out", 20_000, "sister", "person") for d in (3, 15, 27, 45, 60, 75, 90)]
    ops += [Op(d, "purchase", 8_000, "shop", "merchant") for d in range(2, 110, 6)]
    return ops


def classic():
    """Лже-брокер: лесенка, наживка, потом закрытие депозита."""
    return base() + [
        Op(100, "out", 10_000, "x", "person"),
        Op(106, "out", 30_000, "x", "person"),
        Op(110, "in", 12_000, "x", "person"),
        Op(115, "out", 150_000, "x", "person"),
        Op(120, "deposit_close", 2_000_000, "own", "own"),
        Op(121, "out", 1_900_000, "x", "person"),
    ]


def test_ordinary_life_is_silent():
    assert scan(base()).first_warn is None


def test_fake_broker_is_warned_before_the_deposit_is_closed():
    result = scan(classic())
    assert result.first_warn.op.day == 115
    assert {"ladder", "bait"} <= set(result.first_warn.signals)


def test_deposit_is_paused_only_with_consent_given_in_advance():
    assert scan(classic(), consent=True).first_pause.op.day == 120
    assert scan(classic(), consent=False).first_pause is None


def test_new_card_for_every_transfer_does_not_hide_the_scheme():
    ops = base() + [
        Op(100, "out", 10_000, "card1", "person"),
        Op(106, "out", 30_000, "card2", "wallet"),
        Op(110, "in", 12_000, "card3", "person"),
        Op(115, "out", 150_000, "card4", "person"),
    ]
    assert scan(ops).first_warn.op.day == 115


def test_licensed_investor_is_silent():
    ops = base() + [
        Op(100, "out", 50_000, "broker", "licensed"),
        Op(106, "out", 150_000, "broker", "licensed"),
        Op(110, "in", 20_000, "broker", "licensed"),
        Op(115, "deposit_close", 2_000_000, "own", "own"),
        Op(116, "out", 1_900_000, "broker", "licensed"),
    ]
    assert scan(ops).first_warn is None


def test_buying_a_car_is_silent():
    ops = base() + [
        Op(110, "deposit_close", 3_000_000, "own", "own"),
        Op(111, "out", 3_000_000, "seller", "person"),
    ]
    assert scan(ops).first_warn is None


def test_radar_never_looks_into_the_future():
    full = {v.op.day: v.signals for v in scan(classic()).verdicts}
    cut = {v.op.day: v.signals for v in scan([o for o in classic() if o.day <= 115]).verdicts}
    assert all(full[day] == signals for day, signals in cut.items())


def test_shared_recipient_counts_other_clients_only():
    clients = {f"c{i}": base() + [Op(100 + i % 3, "out", 10_000, "org", "person")] for i in range(6)}
    shared = shared_recipients(clients)
    assert "shared" in scan(clients["c5"], client_id="c5", shared=shared).verdicts[-1].signals
    lonely = shared_recipients({"c5": clients["c5"]})
    assert "shared" not in scan(clients["c5"], client_id="c5", shared=lonely).verdicts[-1].signals


def test_every_signal_has_an_explanation_in_plain_words():
    for v in scan(classic(), consent=True).verdicts:
        assert len(v.reasons()) == len(v.signals)
    assert all(REASONS.values())


@pytest.mark.parametrize("kind", [*FRAUD, *HONEST])
def test_generator_is_repeatable_and_ordered(kind):
    a, b = make_client(kind, seed=7), make_client(kind, seed=7)
    assert a == b and a
    assert [o.day for o in a] == sorted(o.day for o in a)
    assert all(o.amount > 0 for o in a)


def test_known_blind_spot_is_documented():
    """Если деньги идут через лицензированную биржу, радар обмана не видит."""
    assert scan(make_client("fraud_via_licensed_exchange", seed=3)).first_warn is None
