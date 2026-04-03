#!/usr/bin/env python3

import re
import sys
import os


override = "override-clash.txt"


def load_manual_rules(path):
    rules = {}
    if not os.path.exists(path):
        return rules

    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if "=>" in line:
                k, v = line.split("=>", 1)
                k = k.strip()
                v = [x.strip() for x in v.split(" | ") if x.strip()]
                rules.setdefault(k, []).extend(v)
    return rules


def parse_line(raw, manual_map):
    original = raw
    raw = raw.strip()

    if not raw or raw.startswith("!"):
        return None

    is_whitelist = raw.startswith("@@")
    if is_whitelist:
        raw = raw[2:]
    target = "DIRECT" if is_whitelist else "PROXY"

    # override first
    if raw in manual_map:
        return [rule + f",{target}" for rule in manual_map[raw]]

    # regex
    if raw.startswith("/") and raw.endswith("/"):
        return f"# [UNSUPPORTED] {original}"

    # ^
    if "^" in raw:
        if raw.endswith("^"):
            raw = raw[:-1]
        else:
            return f"# [UNSUPPORTED] {original}"

    # path
    if "/" in raw:
        m = re.match(r"^(\|*)(.+)", raw)
        pre = m.group(1)
        raw = m.group(2)
        if "://" in raw:
            raw = raw.split("://")[1]
        if "/" in raw:
            raw = raw.split("/")[0]
        raw = f"{pre}{raw}"
        if not raw:
            return f"# [UNSUPPORTED] {original}"

    # ||
    if raw.startswith("||"):
        raw = raw[2:]
        if "*" not in raw:
            return f"DOMAIN-SUFFIX,{raw},{target}"

    # |
    if raw.startswith("|"):
        raw = raw[1:]
        if "*" not in raw:
            return f"DOMAIN,{raw},{target}"

    # wildcard
    if "*" in raw:
        if raw.startswith("*"):
            # *.example.com → suffix
            if raw.startswith("*."):
                value = raw[2:]
                if "*" not in value and "." in value:
                    return f"DOMAIN-SUFFIX,{value},{target}"

            # *example* → keyword
            if raw.endswith("*"):
                keyword = raw[1:-1]
                if "*" not in keyword:
                    return f"DOMAIN-KEYWORD,{keyword},{target}"

        return f"DOMAIN-WILDCARD,{raw},{target}"

    return f"DOMAIN-KEYWORD,{raw},{target}"


def convert(fin, manual_map):
    header = []
    unsupported = []
    direct = []
    proxy = []

    # collect header
    in_header = True
    for line in fin:
        raw = line.rstrip("\n")
        if in_header:
            if raw.startswith("!"):
                if raw != "!":
                  header.append("# " + raw.lstrip("! "))
                else:
                  header.append("#")
                continue
            if raw.startswith("["):
                header.append("# " + raw)
                continue
            header.append("")
        in_header = False

        parsed = parse_line(raw, manual_map)
        if not parsed:
            continue

        if isinstance(parsed, list):
            for p in parsed:
                if p.startswith("# [UNSUPPORTED]"):
                    unsupported.append(p)
                elif p.endswith(",DIRECT"):
                    direct.append(p)
                else:
                    proxy.append(p)
            continue

        if parsed.startswith("# [UNSUPPORTED]"):
            unsupported.append(parsed)
        elif parsed.endswith(",DIRECT"):
            direct.append(parsed)
        else:
            proxy.append(parsed)

    return header, unsupported, direct, proxy


def resolve_manual(infile):
    if infile:
        path = os.path.join(os.path.dirname(infile), override)
        if os.path.exists(path):
            return path
    return override


def main():
    argc = len(sys.argv)

    if argc == 1:
        manual = load_manual_rules(override)
        header, unsupported, direct, proxy = convert(sys.stdin, manual)

        for x in header + unsupported + direct + proxy:
            print(x)
        return

    infile = sys.argv[1]
    manual = load_manual_rules(resolve_manual(infile))

    with open(infile, "r", encoding="utf-8") as fin:
        header, unsupported, direct, proxy = convert(fin, manual)

    output = header + unsupported + direct + proxy

    if argc == 2:
        for x in output:
            print(x)
        return

    outfile = sys.argv[2]

    if not outfile:
        for x in output:
            print(x)
        return

    with open(outfile, "w", encoding="utf-8") as fout:
        for x in output:
            fout.write(x + "\n")

    # warning
    if unsupported:
        print(f"[WARNING] {len(unsupported)} unsupported rules", file=sys.stdout)


if __name__ == "__main__":
    main()
