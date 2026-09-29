"""Build a Moodle GIFT quiz file and a lecturer review page from a question YAML.

The YAML with the answer key is kept outside this public repository.
Usage: python3 scripts/build_gift.py path/to/activity.yml [out_dir]
"""
import itertools
import pathlib
import sys

import yaml

SPECIAL = "\\~=#{}:"


def esc(text):
    """Escape GIFT control characters and flatten line breaks."""
    text = " ".join(line.strip() for line in str(text).strip().splitlines())
    return "".join("\\" + c if c in SPECIAL else c for c in text)


def pct(value):
    """Format a Moodle answer weight: whole numbers without a decimal point."""
    value = round(value, 5)
    return str(int(value)) if value == int(value) else str(value)


def weights(n_correct, n_wrong):
    right = pct(100 / n_correct)
    wrong = pct(-100 / n_wrong) if n_wrong else "0"
    return right, wrong


def order_options(items):
    """Turn an ordering question into multiple choice: the right order plus three wrong ones."""
    right = list(items)
    wrong = [p for p in itertools.permutations(right) if list(p) != right]
    picks = [wrong[0], wrong[len(wrong) // 2], wrong[-1]]
    opts = [{"text": " ← ".join(right), "correct": True}]
    opts += [{"text": " ← ".join(p), "correct": False} for p in picks]
    return opts


def gift_question(q):
    head = f"::{esc(q['id'])}::[html]{esc(q['text'])}"
    opts = q.get("options") or order_options(q["items"])
    lines = []
    if q["type"] == "multi":
        n_right = sum(o["correct"] for o in opts)
        right, wrong = weights(n_right, len(opts) - n_right)
        for o in opts:
            lines.append(f"\t~%{right if o['correct'] else wrong}%{esc(o['text'])}")
    else:
        for o in opts:
            lines.append(f"\t{'=' if o['correct'] else '~'}{esc(o['text'])}")
    if q.get("feedback"):
        lines.append(f"\t####{esc(q['feedback'])}")
    return head + " {\n" + "\n".join(lines) + "\n}\n"


def review_page(a):
    out = [f"# {a['title']} – דף בדיקה למרצה", "",
           f"{a['course']} · {a['date']} · AIAS {a['aias']} · קריאה: {a['reading']}", ""]
    for i, q in enumerate(a["questions"], 1):
        out.append(f"## {i}. ({q['type']})")
        if q.get("review"):
            out.append(f"> ⚠️ לבדיקה: {q['review']}")
        out.append(q["text"].strip().replace("<br>", "  \n"))
        out.append("")
        opts = q.get("options") or order_options(q["items"])
        for o in opts:
            out.append(f"- {'✅' if o['correct'] else '▫️'} {o['text']}")
        if q.get("feedback"):
            out.append(f"\n*משוב:* {q['feedback']}")
        out.append("")
    return "\n".join(out)


def main():
    src = pathlib.Path(sys.argv[1])
    out_dir = pathlib.Path(sys.argv[2]) if len(sys.argv) > 2 else src.parent
    a = yaml.safe_load(src.read_text(encoding="utf-8"))
    gift = [f"// {a['title']} ({a['course']}, {a['date']})",
            f"$CATEGORY: $course$/top/{a['category']}", ""]
    gift += [gift_question(q) for q in a["questions"]]
    (out_dir / f"{a['id']}.gift").write_text("\n".join(gift), encoding="utf-8")
    (out_dir / f"{a['id']}-review.md").write_text(review_page(a), encoding="utf-8")
    print(f"{len(a['questions'])} questions -> {out_dir / (a['id'] + '.gift')}")


if __name__ == "__main__":
    main()
