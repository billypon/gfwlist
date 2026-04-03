#!/usr/bin/env python3

import sys
import re


ipv4 = re.compile(r"^(\d{1,3}\.){3}\d{1,3}$")


def convert_line(line: str, target):
    line = line.strip()

    if not line or line.startswith("#"):
        return None

    parts = line.split(",")
    if len(parts) < 2:
        return None

    rule_type = parts[0].strip().upper()
    value = parts[1].strip()
    policy = parts[2].strip().upper()

    if not value or policy != target:
        return None

    if rule_type == "DOMAIN":
        if not ipv4.match(value):
            return value

    if rule_type == "DOMAIN-SUFFIX":
        return f"+.{value}"

    return None


def process(fin, fout, target):
    seen = set()
    result = []

    for line in fin:
        v = convert_line(line, target)
        if v and v not in seen:
            seen.add(v)
            result.append(v)

    fout.write("payload:\n")
    for item in result:
        fout.write(f"  - '{item}'\n")


def main():
    args = sys.argv[1:]

    target = (args[0] or "proxy").upper()
    fin = open(args[1], "r", encoding="utf-8") if len(args) >= 2 else sys.stdin
    fout = open(args[2], "w", encoding="utf-8") if len(args) >= 3 else sys.stdout

    process(fin, fout, target)

    if fin is not sys.stdin:
        fin.close()
    if fout is not sys.stdout:
        fout.close()


if __name__ == "__main__":
    main()
