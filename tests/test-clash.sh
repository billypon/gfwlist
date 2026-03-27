#!/bin/bash

scripts/autoproxy2clash.py tests/clash-input.txt > tests/clash-output.txt
diff -u --color=always tests/clash-expect.txt tests/clash-output.txt
