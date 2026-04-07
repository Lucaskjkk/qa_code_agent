#!/usr/bin/env python3
import argparse
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

def sh(cmd: list):
    print("$", " ".join(cmd))
    subprocess.check_call(cmd)

def main():
    parser = argparse.ArgumentParser(description="Deploy helper")
    parser.add_argument("--image", default="qa-code-agent", help="Nome da imagem (sem tag)")
    parser.add_argument("--tag", default="latest", help="Tag da imagem")
    parser.add_argument("--registry", default="", help="Registro (ex: ghcr.io/user) - opcional")
    parser.add_argument("--push", action="store_true", help="Fazer push após build")
    parser.add_argument("--k8s-apply", action="store_true", help="Aplicar manifests em infrastructure/kubernetes")
    args = parser.parse_args()

    ref = f"{args.image}:{args.tag}" if not args.registry else f"{args.registry}/{args.image}:{args.tag}"

    # docker build
    sh(["docker", "build", "-t", ref, str(ROOT)])

    if args.push:
        sh(["docker", "push", ref])

    if args.k8s_apply:
        k8s_path = ROOT / "infrastructure" / "kubernetes"
        sh(["kubectl", "apply", "-f", str(k8s_path)])

    print(f"[deploy] Concluído. Imagem: {ref}")

if __name__ == "__main__":
    main()
