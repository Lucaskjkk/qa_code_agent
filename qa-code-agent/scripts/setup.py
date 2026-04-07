#!/usr/bin/env python3
import os
import shutil
import sys
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

def ensure_outputs_dir():
    out = ROOT / "outputs"
    out.mkdir(exist_ok=True, parents=True)
    print(f"[setup] outputs/ pronto em {out}")

def copy_env_if_missing():
    src = ROOT / ".env.example"
    dst = ROOT / ".env"
    if src.exists() and not dst.exists():
        shutil.copyfile(src, dst)
        print("[setup] .env criado a partir de .env.example (lembre-se de preencher as chaves)")

def install_requirements_if_requested():
    if os.getenv("INSTALL_DEPS", "0") not in ("1", "true", "True"):
        print("[setup] INSTALL_DEPS não definido. Pulando instalação de deps.")
        return
    req = ROOT / "requirements.txt"
    if req.exists():
        print("[setup] Instalando dependências via requirements.txt ...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", str(req)])
    else:
        pyproj = ROOT / "pyproject.toml"
        if pyproj.exists():
            print("[setup] Encontrado pyproject.toml. Instalando projeto (editable) ...")
            subprocess.check_call([sys.executable, "-m", "pip", "install", "-e", str(ROOT)])
        else:
            print("[setup] Nenhum requirements.txt ou pyproject.toml encontrado. Nada a instalar.")

def main():
    ensure_outputs_dir()
    copy_env_if_missing()
    install_requirements_if_requested()
    print("[setup] Concluído.")

if __name__ == "__main__":
    main()
