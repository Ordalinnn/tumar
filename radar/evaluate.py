"""Оценка качества радара.

Два режима:
    python -m radar.evaluate --set A                # сгенерированный набор A
    python -m radar.evaluate --blind data/blind.csv # слепой набор из CSV

Печатает таблицы и пишет docs/metrics_<набор>.md. Плохие цифры не прячем.
"""
import argparse
import csv
from pathlib import Path
from statistics import median

from .model import Op
from .rules import RECIPIENT_TYPES, Config, scan, shared_recipients
from .scenarios import FRAUD, HONEST, make_client

CLIENTS_PER_STORY = 30
FRAUD_LABEL = "fraud"
HONEST_LABEL = "honest"
REQUEST_KINDS = ("deposit_close", "loan")
# Новый получатель — тот, кому клиент впервые заплатил после этого дня.
NEW_RECIPIENT_DAY = 90


# ---------- наборы клиентов ----------

def load_set_a(clients_per_story=CLIENTS_PER_STORY):
    """{sid: (сюжет, метка, операции)}: по 30 клиентов на каждый сюжет, seed = номер клиента."""
    clients = {}
    for label, kinds in ((FRAUD_LABEL, FRAUD), (HONEST_LABEL, HONEST)):
        for kind in kinds:
            for i in range(clients_per_story):
                clients[f"A:{kind}:{i}"] = (kind, label, make_client(kind, seed=i))
    return clients


def load_blind(path):
    """Слепой набор: story_id,label,day,kind,amount,cp,cp_type.

    Возвращает (клиенты, ошибки, число строк). Ошибка — это (номер строки, текст):
    номер считаем по файлу, где заголовок — строка 1. Файл читаем как utf-8-sig,
    чтобы BOM в начале не ломал имя первой колонки.
    """
    stories, problems, rows = {}, [], 0
    with open(path, newline="", encoding="utf-8-sig") as fh:
        for line_no, row in enumerate(csv.DictReader(fh), start=2):
            rows += 1
            sid = (row.get("story_id") or "").strip()
            if not sid:
                continue                      # пустая строка — не ошибка
            try:
                op = Op(int(row["day"]), row["kind"].strip(), float(row["amount"]),
                        row["cp"].strip(), row["cp_type"].strip())
            except (KeyError, TypeError, ValueError) as exc:
                # Пишем номер строки, чтобы файл можно было сразу починить.
                problems.append((line_no, f"{type(exc).__name__}: {exc}"))
                continue
            label = (row.get("label") or "").strip().lower()
            stories.setdefault(sid, [label, []])[1].append(op)
    clients = {sid: (sid, label, sorted(ops, key=lambda o: o.day))
               for sid, (label, ops) in sorted(stories.items())}
    return clients, problems, rows


# ---------- метрики одного клиента ----------

def _request_day(ops):
    """День первой заявки на закрытие вклада или кредит."""
    days = [o.day for o in ops if o.kind in REQUEST_KINDS]
    return min(days) if days else None


def new_recipients(ops):
    """Получатели, которым клиент впервые заплатил после 90-го дня."""
    first = {}
    for op in sorted(ops, key=lambda o: o.day):
        if op.kind == "out" and op.cp_type in RECIPIENT_TYPES:
            first.setdefault(op.cp, op.day)
    return {cp for cp, day in first.items() if day > NEW_RECIPIENT_DAY}


def _money_to_new(ops, recipients, until_day=None):
    """(до указанного дня, всего) — деньги, отправленные новым получателям."""
    total = before = 0.0
    for op in ops:
        if op.kind != "out" or op.cp not in recipients:
            continue
        total += op.amount
        if until_day is not None and op.day < until_day:
            before += op.amount
    return before, total


def score_client(ops, shared, client_id, cfg=Config()):
    """Что радар сделал с одним клиентом."""
    result = scan(ops, client_id=client_id, shared=shared, cfg=cfg)
    warn = result.first_warn
    # Пауза возможна только при согласии клиента — оцениваем «режим защиты».
    pause = scan(ops, client_id=client_id, shared=shared, consent=True, cfg=cfg).first_pause
    request = _request_day(ops)
    # Сколько денег ушло новым получателям до предупреждения (без самой операции).
    before, total = _money_to_new(ops, new_recipients(ops),
                                  warn.op.day if warn else None)
    return {
        "warn": warn is not None,
        "request": request is not None,
        "before": bool(warn) and request is not None and warn.op.day < request,
        "at_request": bool(warn) and request is not None and warn.op.day <= request,
        # Без предупреждения все деньги новым получателям ушли без него — 100%.
        "money": 1.0 if warn is None else (before / total if total else 0.0),
        "pause": pause is not None,
    }


def aggregate(clients, cfg=Config()):
    """Сводка по сюжетам: {сюжет: статистика}."""
    shared = shared_recipients({sid: ops for sid, (_, _, ops) in clients.items()})
    per_story = {}
    for sid, (story, label, ops) in clients.items():
        row = score_client(ops, shared, sid, cfg)
        stat = per_story.setdefault(story, {
            "label": label, "n": 0, "caught": 0, "pause": 0,
            "with_request": 0, "before": 0, "at_request": 0, "money": [],
        })
        stat["n"] += 1
        stat["caught"] += 1 if row["warn"] else 0
        stat["pause"] += 1 if row["pause"] else 0
        if row["request"]:
            stat["with_request"] += 1
            stat["before"] += 1 if row["before"] else 0
            stat["at_request"] += 1 if row["at_request"] else 0
        stat["money"].append(row["money"])
    return per_story


# ---------- отчёт ----------

def _pct(part, whole):
    return "—" if not whole else f"{part / whole:.0%}"


def _median_pct(values):
    return f"{median(values):.0%}" if values else "—"


def _table(header, rows):
    lines = ["| " + " | ".join(header) + " |",
             "|" + "|".join("---" for _ in header) + "|"]
    lines += ["| " + " | ".join(str(c) for c in row) + " |" for row in rows]
    return lines


def build_report(title, per_story, note="", notes=None):
    """Markdown-отчёт по сводке. Возвращает строки отчёта."""
    fraud = {k: v for k, v in per_story.items() if v["label"] == FRAUD_LABEL}
    honest = {k: v for k, v in per_story.items() if v["label"] == HONEST_LABEL}

    lines = [f"# Качество радара: {title}", ""]
    if note:
        lines += [note, ""]
    lines += [
        "Доля денег — сколько из переводов новым получателям (первый платёж после 90-го дня) "
        "ушло до первого предупреждения, без самой операции, от всех переводов им же. "
        "Если предупреждения не было, считаем 100%.",
        "",
    ]

    if fraud:
        total_n = sum(v["n"] for v in fraud.values())
        total_caught = sum(v["caught"] for v in fraud.values())
        total_req = sum(v["with_request"] for v in fraud.values())
        total_before = sum(v["before"] for v in fraud.values())
        total_at = sum(v["at_request"] for v in fraud.values())
        total_pause = sum(v["pause"] for v in fraud.values())
        all_money = [m for v in fraud.values() for m in v["money"]]
        lines += [
            "## Обман", "",
            f"Всего клиентов: {total_n}. Поймано: {_pct(total_caught, total_n)}. "
            f"Предупреждены до заявки: {_pct(total_before, total_req)}. "
            f"До или в момент заявки: {_pct(total_at, total_req)}. "
            f"С паузой в режиме защиты: {_pct(total_pause, total_n)}. "
            f"Медиана денег до предупреждения: {_median_pct(all_money)}.",
            "",
        ]
        rows = [(name,
                 _pct(v["caught"], v["n"]),
                 _pct(v["before"], v["with_request"]),
                 _pct(v["at_request"], v["with_request"]),
                 _pct(v["pause"], v["n"]),
                 _median_pct(v["money"]))
                for name, v in sorted(fraud.items())]
        lines += _table(["Сюжет", "Поймано", "До заявки", "До или в момент заявки",
                         "Пауза (режим защиты)", "Денег до предупреждения"], rows)
        lines.append("")

    if honest:
        lines += ["## Честные клиенты", ""]
        rows = [(name,
                 _pct(v["caught"], v["n"]),
                 _pct(v["pause"], v["n"]))
                for name, v in sorted(honest.items())]
        total_n = sum(v["n"] for v in honest.values())
        total_warn = sum(v["caught"] for v in honest.values())
        total_pause = sum(v["pause"] for v in honest.values())
        lines += [f"Всего клиентов: {total_n}. С предупреждением: {_pct(total_warn, total_n)}. "
                  f"С паузой: {_pct(total_pause, total_n)}.", ""]
        lines += _table(["Сюжет", "Предупреждение", "Пауза"], rows)
        lines.append("")
    if notes:
        lines += notes
    return lines


def write_report(name, lines, docs_dir="docs"):
    path = Path(docs_dir) / f"metrics_{name}.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path


def main(argv=None):
    parser = argparse.ArgumentParser(description="Качество радара на наборе клиентов")
    parser.add_argument("--set", dest="set_name", default=None,
                        help="сгенерированный набор, сейчас есть только A")
    parser.add_argument("--blind", dest="blind", default=None,
                        help="путь к слепому набору, например data/blind.csv")
    parser.add_argument("--clients", type=int, default=CLIENTS_PER_STORY,
                        help="сколько клиентов на сюжет в наборе A")
    args = parser.parse_args(argv)

    problems, rows = [], 0
    if args.blind:
        clients, problems, rows = load_blind(args.blind)
        for line_no, message in problems:
            print(f"Ошибка в строке {line_no}: {message}")
        name = Path(args.blind).stem
        note = f"Слепой набор `{args.blind}`: {len(clients)} историй. Пороги не подбирались."
        extra_notes = []
    else:
        set_name = args.set_name or "A"
        if set_name != "A":
            raise SystemExit(f"Набор {set_name} не сгенерирован: есть только A, "
                             f"для остальных используйте --blind путь.csv")
        clients = load_set_a(args.clients)
        name = set_name
        note = f"Набор A: по {args.clients} клиентов на каждый сюжет (seed = номер клиента)."
        extra_notes = []

    if not clients and (rows or problems):
        # Строки есть, а историй нет — это ошибка в файле, а не пустой набор.
        lines = [f"# Качество радара: {name}", "",
                 f"Ошибка: в `{args.blind}` есть строки ({rows}), но ни одной истории не собрано.",
                 "", "Строки, которые не удалось прочитать:", ""]
        lines += [f"- строка {line_no}: {message}" for line_no, message in problems]
        if not problems:
            lines.append("- у всех строк пустой story_id")
        lines += ["", "Метрики не считаются, пока файл не исправлен."]
    elif not clients:
        lines = [f"# Качество радара: {name}", "", f"Набор пуст: в `{args.blind}` нет ни одной истории.",
                 "", "Пока данных нет, метрики не считаются."]
    else:
        lines = build_report(name, aggregate(clients), note, extra_notes)
        if problems:
            # Разобранные истории считаем, но битые строки называем вслух.
            lines += ["## Ошибки в строках", ""]
            lines += [f"- строка {line_no}: {message}" for line_no, message in problems]
            lines.append("")

    text = "\n".join(lines)
    print(text)
    path = write_report(name, lines)
    print(f"\nОтчёт записан: {path}")
    # Ненулевой код — если строки есть, а историй не получилось.
    return 1 if problems and not clients else 0


if __name__ == "__main__":
    raise SystemExit(main())
