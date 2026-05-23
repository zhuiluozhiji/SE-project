#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
SRC_DIR="$ROOT/docs/设计模式报告/figures/src"
OUT_DIR="$ROOT/docs/设计模式报告/figures/exported"
JAR_PATH="$ROOT/docs/设计模式报告/tools/plantuml.jar"
JAVA_BIN="${JAVA_BIN:-/opt/homebrew/opt/openjdk/bin/java}"

if [[ ! -x "$JAVA_BIN" ]]; then
  echo "Java runtime not found at $JAVA_BIN" >&2
  exit 1
fi

if [[ ! -f "$JAR_PATH" ]]; then
  echo "PlantUML jar not found at $JAR_PATH" >&2
  exit 1
fi

mkdir -p "$OUT_DIR"

for file in "$SRC_DIR"/*.puml; do
  [[ -f "$file" ]] || continue
  [[ "$(basename "$file")" == "common-theme.puml" ]] && continue
  "$JAVA_BIN" -Djava.awt.headless=true -jar "$JAR_PATH" -tpng -o ../exported "$file"
done

echo "Rendered figures into $OUT_DIR"
