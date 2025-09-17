#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# pre requisites: pip install boto3

import argparse
import sys
import boto3
from botocore.exceptions import ClientError
import re

TAG_KEY = "S3-Bucket-Name"

def normalize_region(loc):
    # S3 retorna None para us-east-1 e, em casos antigos, "EU" para eu-west-1
    if loc in (None, "None", ""):
        return "us-east-1"
    if loc == "EU":
        return "eu-west-1"
    return loc

def upsert_tag(tagset, key, value):
    """Adiciona ou atualiza a tag (preserva as demais)."""
    found = False
    new = []
    for t in tagset:
        k = t.get("Key")
        v = t.get("Value")
        if k == key:
            new.append({"Key": key, "Value": value})
            found = True
        else:
            new.append({"Key": k, "Value": v})
    if not found:
        if len(new) >= 50:
            raise RuntimeError("Bucket já possui 50 tags; não é possível adicionar outra.")
        new.append({"Key": key, "Value": value})
    return new

def main():
    parser = argparse.ArgumentParser(
        description="Adiciona a tag S3-Bucket-Name com o próprio nome do bucket em todos os buckets da conta."
    )
    parser.add_argument("--profile", default=None, help="Perfil AWS a usar (opcional).")
    parser.add_argument("--dry-run", action="store_true", help="Não aplica, apenas mostra o que faria.")
    parser.add_argument("--bucket-filter", default=None, help="Regex para filtrar buckets por nome (opcional).")
    parser.add_argument("--yes", action="store_true", help="Pula confirmação interativa.")
    args = parser.parse_args()

    session = boto3.Session(profile_name=args.profile) if args.profile else boto3.Session()
    s3_global = session.client("s3")

    try:
        buckets = s3_global.list_buckets().get("Buckets", [])
    except ClientError as e:
        print(f"ERRO ao listar buckets: {e}", file=sys.stderr)
        return 1

    # Filtrar buckets se especificado
    if args.bucket_filter:
        pattern = re.compile(args.bucket_filter)
        buckets = [b for b in buckets if pattern.search(b["Name"])]
        print(f"Filtro aplicado: {len(buckets)} buckets selecionados")

    # Confirmação de segurança
    if not args.dry_run and not args.yes:
        print(f"\n⚠️  ATENÇÃO: Este script irá modificar tags em {len(buckets)} bucket(s).")
        print("Tags existentes serão preservadas, mas a tag 'S3-Bucket-Name' será adicionada/atualizada.")
        confirm = input("Deseja continuar? (digite 'sim' para confirmar): ")
        if confirm.lower() != 'sim':
            print("Operação cancelada.")
            return 0

    updated = skipped = errors = 0

    for b in buckets:
        name = b["Name"]
        try:
            loc_resp = s3_global.get_bucket_location(Bucket=name)
            region = normalize_region(loc_resp.get("LocationConstraint"))
        except ClientError as e:
            print(f"[{name}] ERRO ao obter região: {e}", file=sys.stderr)
            errors += 1
            continue

        s3_regional = session.client("s3", region_name=region)

        # Lê tags atuais (ou vazio se não existir)
        current = []
        try:
            resp = s3_regional.get_bucket_tagging(Bucket=name)
            current = resp.get("TagSet", [])
        except ClientError as e:
            code = e.response["Error"].get("Code")
            if code in ("NoSuchTagSet", "NoSuchTagSetError"):
                current = []
            elif code in ("AccessDenied", "AuthorizationHeaderMalformed"):
                print(f"[{name}] Sem permissão para ler tags: {e}")
                skipped += 1
                continue
            else:
                print(f"[{name}] ERRO ao ler tags: {e}", file=sys.stderr)
                errors += 1
                continue

        # Calcula novo TagSet (merge + upsert)
        try:
            new = upsert_tag(current, TAG_KEY, name)
        except RuntimeError as e:
            print(f"[{name}] {e}")
            skipped += 1
            continue

        if new == current:
            print(f"[{name}] já possui a tag correta. (região {region})")
            continue

        if args.dry_run:
            print(f"[{name}] DRY-RUN: aplicaria TagSet={new} (região {region})")
            continue

        try:
            s3_regional.put_bucket_tagging(Bucket=name, Tagging={"TagSet": new})
            print(f"[{name}] tag aplicada com sucesso. (região {region})")
            updated += 1
        except ClientError as e:
            print(f"[{name}] ERRO ao aplicar tag: {e}", file=sys.stderr)
            errors += 1

    print(f"\nResumo: atualizados={updated}, pulados={skipped}, erros={errors}")
    return 0

if __name__ == "__main__":
    sys.exit(main())
