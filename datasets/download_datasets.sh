#!/usr/bin/env bash
# Descarga el dataset Sparkov de Kaggle en datasets/raw/ (carpeta ignorada por git).
# Requiere Kaggle API configurada: ~/.kaggle/kaggle.json (ver https://www.kaggle.com/docs/api).
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
RAW_DIR="${SCRIPT_DIR}/raw"
mkdir -p "${RAW_DIR}"

if ! command -v kaggle >/dev/null 2>&1; then
  echo "ERROR: la CLI 'kaggle' no está instalada. Instálala con: pip install kaggle" >&2
  exit 1
fi

echo "Descargando dataset kartik2112/fraud-detection en ${RAW_DIR} ..."
kaggle datasets download -d kartik2112/fraud-detection -p "${RAW_DIR}" --unzip

echo "Listo. Archivos en ${RAW_DIR}:"
ls -lh "${RAW_DIR}"
