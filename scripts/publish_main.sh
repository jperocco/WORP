#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

if [[ "$(git branch --show-current)" != "main" ]]; then
  echo "PUBLICACAO BLOQUEADA: use a branch main antes de publicar." >&2
  exit 1
fi

if [[ -n "$(git status --porcelain)" ]]; then
  echo "PUBLICACAO BLOQUEADA: ha arquivos alterados; revise e salve/commite antes." >&2
  exit 1
fi

git fetch origin main
if ! git merge-base --is-ancestor origin/main HEAD; then
  echo "PUBLICACAO BLOQUEADA: o GitHub tem uma versao mais nova. Atualize antes." >&2
  exit 1
fi

python3 scripts/verify_release.py
git push origin main
echo "Publicacao concluida."
