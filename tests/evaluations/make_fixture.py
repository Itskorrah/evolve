#!/usr/bin/env python3
"""Create an isolated synthetic application for a live Evolve evaluation."""
import argparse
from pathlib import Path
import subprocess


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    root = Path(args.output).expanduser().absolute()
    if root.exists():
        parser.error("Output must be a new directory; existing data is never overwritten.")
    if any(p.is_symlink() for p in (root, *root.parents)):
        parser.error("Symlinked output paths are refused.")
    root.mkdir(parents=True)
    (root / "README.md").write_text(
        "# Basket\n\nA small order-total module. All pricing and CSV edge cases work.\n"
        "Run checks with `python -m unittest discover -s tests -v`.\n", encoding="utf-8")
    (root / ".gitignore").write_text(".evolve/\n__pycache__/\n", encoding="utf-8")
    (root / "basket.py").write_text(
        'import csv\nimport io\n\n'
        'def total(items):\n'
        '    """Return the payable sum, applying each item quantity."""\n'
        '    return sum(item["price"] for item in items)\n\n'
        'def parse_items(text):\n'
        '    """Read SKU, price and quantity; blank trailing lines are allowed."""\n'
        '    return [{"sku": row[0], "price": float(row[1]), "quantity": int(row[2])}\n'
        '            for row in csv.reader(io.StringIO(text))]\n', encoding="utf-8")
    (root / "tests").mkdir()
    (root / "tests/test_basket.py").write_text(
        'import unittest\nfrom basket import total, parse_items\n\n'
        'class BasketTests(unittest.TestCase):\n'
        '    def test_single_item(self):\n'
        '        self.assertEqual(total([{"price": 10, "quantity": 1}]), 10)\n\n'
        '    def test_simple_csv(self):\n'
        '        self.assertEqual(parse_items("A,10,1")[0]["sku"], "A")\n', encoding="utf-8")
    subprocess.run(["git", "-C", str(root), "init", "-q"], check=True)
    subprocess.run(["git", "-C", str(root), "add", "."], check=True)
    subprocess.run(["git", "-C", str(root), "-c", "user.name=Evolve Evaluation",
                    "-c", "user.email=evaluation@example.invalid", "commit", "-qm", "Synthetic fixture"], check=True)
    print(root)


if __name__ == "__main__":
    main()
