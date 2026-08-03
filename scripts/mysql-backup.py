#!/usr/bin/env python3
"""Create, verify, and restore MySQL logical backups without CLI passwords."""

from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path


DATABASE_PATTERN = re.compile(r"^[A-Za-z0-9_]+$")
SCRATCH_DATABASE_PATTERN = re.compile(r"^yuezi_restore_[A-Za-z0-9_]+$")


def env(name: str, default: str = "") -> str:
    return os.environ.get(name, default).strip()


def require_database_name(value: str) -> str:
    if not DATABASE_PATTERN.fullmatch(value):
        raise SystemExit(f"不安全的数据库名: {value!r}")
    return value


def tool_path(name: str, override_env: str) -> str:
    configured = env(override_env)
    resolved = configured or shutil.which(name)
    if not resolved:
        raise SystemExit(
            f"未找到 {name}；请安装 MySQL 客户端或设置 {override_env}。"
        )
    return resolved


def option_value(value: str) -> str:
    if "\n" in value or "\r" in value:
        raise SystemExit("MySQL 连接配置不能包含换行。")
    return '"' + value.replace("\\", "\\\\").replace('"', '\\"') + '"'


@contextmanager
def mysql_defaults_file():
    password = env("ERP_DB_PASSWORD")
    if not password:
        raise SystemExit("ERP_DB_PASSWORD is required.")
    lines = [
        "[client]",
        f"host={option_value(env('ERP_DB_HOST', '127.0.0.1'))}",
        f"port={int(env('ERP_DB_PORT', '3306'))}",
        f"user={option_value(env('ERP_DB_USER', 'yuezi_backup'))}",
        f"password={option_value(password)}",
        "default-character-set=utf8mb4",
    ]
    for variable, option in (
        ("ERP_DB_SSL_CA", "ssl-ca"),
        ("ERP_DB_SSL_CERT", "ssl-cert"),
        ("ERP_DB_SSL_KEY", "ssl-key"),
    ):
        value = env(variable)
        if value:
            lines.append(f"{option}={option_value(value)}")
    descriptor, name = tempfile.mkstemp(prefix="qdf-mysql-", suffix=".cnf")
    path = Path(name)
    try:
        os.close(descriptor)
        path.write_text("\n".join(lines) + "\n", encoding="utf-8")
        try:
            os.chmod(path, 0o600)
        except OSError:
            pass
        yield path
    finally:
        try:
            path.unlink()
        except FileNotFoundError:
            pass


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def manifest_path(backup: Path) -> Path:
    return backup.with_name(backup.name + ".manifest.json")


def read_manifest(backup: Path) -> dict:
    path = manifest_path(backup)
    if not path.is_file():
        raise SystemExit(f"缺少备份清单: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def tool_version(executable: str) -> str:
    completed = subprocess.run(
        [executable, "--version"],
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )
    return completed.stdout.strip()


def backup(args) -> dict:
    database = require_database_name(args.database)
    output = args.output.resolve()
    if output.suffix != ".gz" or not output.name.endswith(".sql.gz"):
        raise SystemExit("备份文件名必须以 .sql.gz 结尾。")
    output.parent.mkdir(parents=True, exist_ok=True)
    if output.exists() and not args.overwrite:
        raise SystemExit(f"备份文件已存在: {output}")

    mysqldump = tool_path("mysqldump", "ERP_MYSQLDUMP")
    temporary = output.with_name(output.name + ".partial")
    stderr_path = output.with_name(output.name + ".stderr.partial")
    for stale in (temporary, stderr_path):
        if stale.exists():
            stale.unlink()

    with mysql_defaults_file() as defaults, stderr_path.open("wb") as error_file:
        command = [
            mysqldump,
            f"--defaults-extra-file={defaults}",
            "--single-transaction",
            "--quick",
            "--routines",
            "--events",
            "--triggers",
            "--hex-blob",
            "--default-character-set=utf8mb4",
            "--skip-comments",
            database,
        ]
        process = subprocess.Popen(
            command,
            stdout=subprocess.PIPE,
            stderr=error_file,
        )
        assert process.stdout is not None
        try:
            with gzip.open(temporary, "wb", compresslevel=6) as destination:
                shutil.copyfileobj(process.stdout, destination, 1024 * 1024)
        finally:
            process.stdout.close()
        return_code = process.wait()
    error_text = stderr_path.read_text(encoding="utf-8", errors="replace").strip()
    stderr_path.unlink(missing_ok=True)
    if return_code:
        temporary.unlink(missing_ok=True)
        raise SystemExit(f"mysqldump 失败（{return_code}）: {error_text}")

    temporary.replace(output)
    manifest = {
        "format": "qdf-erp-mysql-logical-backup-v1",
        "database": database,
        "createdAt": datetime.now(timezone.utc).isoformat(),
        "sha256": sha256_file(output),
        "compressedBytes": output.stat().st_size,
        "tool": tool_version(mysqldump),
        "transactional": True,
        "includes": ["schema", "data", "routines", "events", "triggers"],
    }
    manifest_path(output).write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    verify_backup(output)
    return {"backup": str(output), "manifest": str(manifest_path(output)), **manifest}


def verify_backup(backup_file: Path) -> dict:
    backup_file = backup_file.resolve()
    if not backup_file.is_file():
        raise SystemExit(f"备份文件不存在: {backup_file}")
    manifest = read_manifest(backup_file)
    checksum = sha256_file(backup_file)
    if checksum != manifest.get("sha256"):
        raise SystemExit("备份 SHA-256 与清单不一致。")
    try:
        with gzip.open(backup_file, "rt", encoding="utf-8", errors="strict") as source:
            prefix = source.read(1024 * 1024)
    except (OSError, UnicodeError) as exc:
        raise SystemExit(f"备份 gzip/UTF-8 校验失败: {exc}") from exc
    if "CREATE TABLE" not in prefix and "CREATE DATABASE" not in prefix:
        raise SystemExit("备份内容未发现建表语句。")
    return {
        "status": "verified",
        "backup": str(backup_file),
        "database": manifest.get("database"),
        "sha256": checksum,
        "compressedBytes": backup_file.stat().st_size,
    }


def restore(args) -> dict:
    backup_file = args.backup.resolve()
    verification = verify_backup(backup_file)
    target = require_database_name(args.database)
    if args.confirm_database != target:
        raise SystemExit("--confirm-database 必须与 --database 完全一致。")
    if not SCRATCH_DATABASE_PATTERN.fullmatch(target):
        if not args.allow_non_scratch_target:
            raise SystemExit(
                "默认只允许恢复到 yuezi_restore_*；非演练库须显式添加 "
                "--allow-non-scratch-target。"
            )
        if env("ERP_ALLOW_LIVE_RESTORE") != f"YES:{target}":
            raise SystemExit(
                f"非演练库恢复还需设置 ERP_ALLOW_LIVE_RESTORE=YES:{target}。"
            )

    mysql = tool_path("mysql", "ERP_MYSQL")
    stderr_path = backup_file.with_name(backup_file.name + ".restore.stderr.partial")
    with mysql_defaults_file() as defaults, stderr_path.open("wb") as error_file:
        command = [
            mysql,
            f"--defaults-extra-file={defaults}",
            "--default-character-set=utf8mb4",
            target,
        ]
        process = subprocess.Popen(
            command,
            stdin=subprocess.PIPE,
            stdout=subprocess.DEVNULL,
            stderr=error_file,
        )
        assert process.stdin is not None
        try:
            with gzip.open(backup_file, "rb") as source:
                shutil.copyfileobj(source, process.stdin, 1024 * 1024)
        finally:
            process.stdin.close()
        return_code = process.wait()
    error_text = stderr_path.read_text(encoding="utf-8", errors="replace").strip()
    stderr_path.unlink(missing_ok=True)
    if return_code:
        raise SystemExit(f"mysql 恢复失败（{return_code}）: {error_text}")
    return {
        "status": "restored",
        "targetDatabase": target,
        "backup": str(backup_file),
        "backupSha256": verification["sha256"],
        "next": "运行 migrate、verify 和 RBAC 测试；演练库验收后再销毁。",
    }


def tools() -> dict:
    result = {}
    for name, variable in (("mysqldump", "ERP_MYSQLDUMP"), ("mysql", "ERP_MYSQL")):
        try:
            executable = tool_path(name, variable)
            result[name] = {
                "available": True,
                "path": executable,
                "version": tool_version(executable),
            }
        except (SystemExit, subprocess.SubprocessError) as exc:
            result[name] = {"available": False, "error": str(exc)}
    return result


def main():
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="command", required=True)

    backup_parser = subparsers.add_parser("backup")
    backup_parser.add_argument(
        "--database", default=env("ERP_DB_NAME", "yuezi")
    )
    backup_parser.add_argument("--output", required=True, type=Path)
    backup_parser.add_argument("--overwrite", action="store_true")

    verify_parser = subparsers.add_parser("verify")
    verify_parser.add_argument("--backup", required=True, type=Path)

    restore_parser = subparsers.add_parser("restore")
    restore_parser.add_argument("--backup", required=True, type=Path)
    restore_parser.add_argument("--database", required=True)
    restore_parser.add_argument("--confirm-database", required=True)
    restore_parser.add_argument("--allow-non-scratch-target", action="store_true")

    subparsers.add_parser("check-tools")
    args = parser.parse_args()
    if args.command == "backup":
        result = backup(args)
    elif args.command == "verify":
        result = verify_backup(args.backup)
    elif args.command == "restore":
        result = restore(args)
    else:
        result = tools()
    print(json.dumps(result, ensure_ascii=False, indent=2))
    if args.command == "check-tools" and not all(
        item.get("available") for item in result.values()
    ):
        raise SystemExit(2)


if __name__ == "__main__":
    main()
