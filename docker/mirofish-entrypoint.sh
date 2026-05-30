#!/bin/sh
set -e

if [ -z "${LLM_API_KEY}" ]; then
  export LLM_API_KEY=demo-placeholder
fi
if [ -z "${ZEP_API_KEY}" ]; then
  export ZEP_API_KEY=demo-placeholder
fi

exec uv run python run.py
