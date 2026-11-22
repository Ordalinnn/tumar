"""Собирает слепой набор из istorii.csv.

Берём первые 5 историй с меткой fraud и первые 5 с меткой honest — в том порядке,
в каком они идут в файле. Содержание историй нигде не печатаем, только счётчики.

    python scripts/make_blind.py                       # Desktop/istorii.csv -> data/blind.csv
    python scripts/make_blind.py --source путь.csv --out data/blind.csv
"""
import argparse
import csv
from pathlib import Path

FRAUD = "fraud"
HONEST = "honest"
PER_LABEL = 5
STORY_HEADER = "story_id"
COLUMNS = ["story_id", "label", "day", "kind", "amount", "cp", "cp_type"]


def _clean(value):
    """В источнике у последней колонки бывает «\\» на конце — это опечатка формата."""
    return value.strip().rstrip("\\").strip()


def read_stories(path):
    """{story_id: (метка, [строки])} — истории в порядке появления в файле."""
    stories = {}
    with open(path, newline="", encoding="utf-8-sig") as fh:
        for row in csv.reader(fh):
            if not row or not any(cell.strip() for cell in row):
                continue
            # Повторные заголовки внутри файла пропускаем.
            if _clean(row[0]) == STORY_HEADER:
                continue
            if len(row) < len(COLUMNS):
                raise SystemExit(f"Строка короче {len(COLUMNS)} колонок: {row}")
            sid = row[0].strip()
            label = row[1].strip().lower()
            op = [sid, label] + [cell.strip() for cell in row[2:6]] + [_clean(row[6])]
            stories.setdefault(sid, (label, []))[1].append(op)
    return stories


def first_with(stories, label, count):
    """Первые count историй с нужной меткой, порядок файла сохраняем."""
    return [sid for sid, (story_label, _) in stories.items() if story_label == label][:count]


def main(argv=None):
    parser = argparse.ArgumentParser(description="Слепой набор из первых историй файла")
    parser.add_argument("--source", default=str(Path.home() / "Desktop" / "istorii.csv"),
                        help="исходный CSV с историями")
    parser.add_argument("--out", default=str(Path("data") / "blind.csv"),
                        help="куда записать слепой набор")
    parser.add_argument("--all", dest="take_all", action="store_true",
                        help="взять все истории из файла, а не первые 5 по метке")
    args = parser.parse_args(argv)

    stories = read_stories(args.source)
    if args.take_all:
        chosen = list(stories)
    else:
        chosen = first_with(stories, FRAUD, PER_LABEL) + first_with(stories, HONEST, PER_LABEL)
    if not chosen:
        raise SystemExit(f"В {args.source} не нашлось историй: файл пуст или битый")

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    with open(out, "w", newline="", encoding="utf-8") as fh:
        writer = csv.writer(fh)
        writer.writerow(COLUMNS)
        for sid in chosen:
            writer.writerows(stories[sid][1])

    ops = sum(len(stories[sid][1]) for sid in chosen)
    labels = [stories[sid][0] for sid in chosen]
    print(f"Историй в источнике: {len(stories)} "
          f"(fraud: {sum(1 for lab, _ in stories.values() if lab == FRAUD)}, "
          f"honest: {sum(1 for lab, _ in stories.values() if lab == HONEST)}).")
    print(f"В слепом наборе: {len(chosen)} историй "
          f"(fraud: {labels.count(FRAUD)}, honest: {labels.count(HONEST)}), {ops} операций.")
    print(f"Записано: {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
