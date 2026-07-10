#!/usr/bin/env bash
set -e
python3 -m py_compile scripts/*.py
bash -n bin/vibe-verify
claude plugin validate --strict .
