"""Ошибки, найденные при проверке первой версии. Файл не менять."""
import ast
from pathlib import Path

import pytest

from radar.evaluate import score_client
from radar.model import Op
from radar.rules import scan
from radar.scenarios import make_client
from tests.test_radar import base, classic


def test_rules_import_op_so_code_works_on_older_python():
    tree = ast.parse(Path("radar/rules.py").read_text(encoding="utf-8"))
    names = {a.name for n in ast.walk(tree) if isinstance(n, ast.ImportFrom) for a in n.names}
    assert "Op" in names


def test_money_back_from_a_known_relative_is_not_bait():
    ops = base() + [Op(100, "out", 50_000, "tutor", "person"), Op(104, "in", 10_000, "sister", "person")]
    assert "bait" not in scan(ops).verdicts[-1].signals


def test_radar_does_not_see_later_operations_of_the_same_day():
    ops = base() + [
        Op(100, "out", 10_000, "x", "person"),
        Op(106, "out", 30_000, "x", "person"),
        Op(106, "in", 12_000, "x", "person"),
    ]
    out = [v for v in scan(ops).verdicts if v.op.day == 106 and v.op.kind == "out"][0]
    assert "bait" not in out.signals


def test_no_fee_signal_when_money_came_back_after_the_biggest_transfer():
    ops = base() + [
        Op(100, "out", 10_000, "x", "person"), Op(106, "out", 30_000, "x", "person"),
        Op(110, "out", 150_000, "x", "person"), Op(112, "in", 140_000, "x", "person"),
        Op(115, "out", 20_000, "y", "person"),
    ]
    assert "fee" not in scan(ops).verdicts[-1].signals


def new_recipients(kind, seed):
    first = {}
    for o in make_client(kind, seed=seed):
        if o.kind == "out" and o.cp_type in ("person", "wallet", "company"):
            first.setdefault(o.cp, o.day)
    return {cp for cp, day in first.items() if day > 90}


@pytest.mark.parametrize("kind", ["fraud_classic", "fraud_no_bait", "honest_car", "honest_builder"])
def test_different_clients_do_not_share_recipients(kind):
    assert not new_recipients(kind, 1) & new_recipients(kind, 2)


def test_pyramid_members_do_share_a_recipient():
    assert new_recipients("fraud_pyramid", 1) & new_recipients("fraud_pyramid", 2)


def test_money_metric_counts_only_suspicious_recipients_before_the_warning():
    """40 000 из 2 090 000 ушло до предупреждения на 115-й день."""
    assert score_client(classic(), {}, "c")["money"] == pytest.approx(40_000 / 2_090_000)
