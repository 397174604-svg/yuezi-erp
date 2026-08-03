"""Runtime configuration, migration discovery, and data-scope helpers.

This module intentionally has no third-party dependencies so deployment and
permission checks can run before PyMySQL is installed or a database is
reachable.
"""

from __future__ import annotations

import hashlib
import os
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Mapping
from urllib.parse import urlparse


LOCAL_TOKEN_SECRET = "local-mvp-token-secret-change-before-production"
MIGRATION_PATTERN = re.compile(
    r"^(V(?P<date>\d{8})_(?P<sequence>\d{3,}))__(?P<description>[A-Za-z0-9_]+)\.sql$"
)
DATABASE_NAME_PATTERN = re.compile(r"^[A-Za-z0-9_]+$")


class RuntimeConfigError(ValueError):
    """Raised when a runtime or authorization configuration is unsafe."""


@dataclass(frozen=True)
class Migration:
    version: str
    sequence: int
    description: str
    path: Path
    checksum: str
    compatible_checksums: tuple[str, ...] = ()


def migration_checksum_matches(migration: Migration, checksum: str) -> bool:
    return checksum == migration.checksum or checksum in migration.compatible_checksums


def env_value(
    name: str,
    default: str = "",
    environ: Mapping[str, str] | None = None,
) -> str:
    source = os.environ if environ is None else environ
    return str(source.get(name, default)).strip()


def runtime_environment(environ: Mapping[str, str] | None = None) -> str:
    value = env_value(
        "ERP_RUNTIME_ENV",
        env_value("ERP_ENV", "development", environ),
        environ,
    ).lower()
    aliases = {"prod": "production", "dev": "development"}
    return aliases.get(value, value)


def is_production(environ: Mapping[str, str] | None = None) -> bool:
    return runtime_environment(environ) == "production"


def parse_bool(value: str, default: bool = False) -> bool:
    normalized = str(value or "").strip().lower()
    if not normalized:
        return default
    if normalized in {"1", "true", "yes", "on"}:
        return True
    if normalized in {"0", "false", "no", "off"}:
        return False
    raise RuntimeConfigError(f"Invalid boolean value: {value!r}")


def _cors_origins(environ: Mapping[str, str]) -> list[str]:
    return [
        item.strip()
        for item in env_value("ERP_CORS_ORIGINS", "", environ).split(",")
        if item.strip()
    ]


def _validated_int(
    name: str,
    default: str,
    source: Mapping[str, str],
    minimum: int,
    maximum: int,
) -> int:
    try:
        value = int(env_value(name, default, source))
    except ValueError as exc:
        raise RuntimeConfigError(f"{name} must be an integer.") from exc
    if value < minimum or value > maximum:
        raise RuntimeConfigError(
            f"{name} must be between {minimum} and {maximum}."
        )
    return value


def validate_runtime_config(
    environ: Mapping[str, str] | None = None,
    *,
    require_database_password: bool = True,
) -> dict:
    source = dict(os.environ if environ is None else environ)
    environment = runtime_environment(source)
    if environment not in {"development", "test", "staging", "production"}:
        raise RuntimeConfigError(
            "ERP_RUNTIME_ENV must be development, test, staging, or production."
        )

    database_name = env_value("ERP_DB_NAME", "yuezi", source)
    if not DATABASE_NAME_PATTERN.fullmatch(database_name):
        raise RuntimeConfigError("ERP_DB_NAME contains unsafe characters.")
    if require_database_password and not env_value("ERP_DB_PASSWORD", "", source):
        raise RuntimeConfigError("ERP_DB_PASSWORD is required.")
    _validated_int("ERP_DB_PORT", "3306", source, 1, 65535)
    _validated_int("ERP_API_PORT", "3000", source, 1, 65535)
    _validated_int("ERP_DB_CONNECT_TIMEOUT", "5", source, 1, 300)
    _validated_int("ERP_DB_READ_TIMEOUT", "30", source, 1, 3600)
    _validated_int("ERP_DB_WRITE_TIMEOUT", "30", source, 1, 3600)
    _validated_int(
        "ERP_MAX_REQUEST_BYTES",
        str(1024 * 1024),
        source,
        1024,
        10 * 1024 * 1024,
    )
    _validated_int("ERP_LOGIN_MAX_FAILURES", "5", source, 1, 100)
    _validated_int("ERP_LOGIN_LOCK_MINUTES", "15", source, 1, 1440)
    _validated_int("ERP_MIGRATION_LOCK_TIMEOUT", "30", source, 1, 300)

    token_secret = env_value("ERP_TOKEN_SECRET", "", source)
    origins = _cors_origins(source)
    database_user = env_value("ERP_DB_USER", "root", source)
    database_host = env_value("ERP_DB_HOST", "127.0.0.1", source).lower()
    ssl_ca = env_value("ERP_DB_SSL_CA", "", source)

    if environment == "production":
        if len(token_secret.encode("utf-8")) < 32:
            raise RuntimeConfigError(
                "ERP_TOKEN_SECRET must contain at least 32 UTF-8 bytes in production."
            )
        if token_secret == LOCAL_TOKEN_SECRET:
            raise RuntimeConfigError(
                "The local fallback ERP_TOKEN_SECRET is forbidden in production."
            )
        if database_user.lower() in {"root", "mysql.sys", "mysql.session"}:
            raise RuntimeConfigError(
                "ERP_DB_USER must be a least-privilege application account in production."
            )
        if not origins:
            raise RuntimeConfigError("ERP_CORS_ORIGINS is required in production.")
        for origin in origins:
            parsed = urlparse(origin)
            if (
                parsed.scheme != "https"
                or not parsed.netloc
                or parsed.path not in {"", "/"}
                or origin == "*"
            ):
                raise RuntimeConfigError(
                    "Production CORS origins must be explicit HTTPS origins."
                )
        if parse_bool(env_value("ERP_ALLOW_QUERY_TOKEN", "", source), False):
            raise RuntimeConfigError(
                "ERP_ALLOW_QUERY_TOKEN cannot be enabled in production."
            )
        if database_host not in {"127.0.0.1", "localhost", "::1"} and not ssl_ca:
            raise RuntimeConfigError(
                "ERP_DB_SSL_CA is required for a remote production database."
            )

    return {
        "environment": environment,
        "databaseName": database_name,
        "databaseUser": database_user,
        "corsOrigins": origins,
        "databaseTls": bool(ssl_ca),
    }


def database_ssl_config(
    environ: Mapping[str, str] | None = None,
) -> dict | None:
    source = os.environ if environ is None else environ
    ca = env_value("ERP_DB_SSL_CA", "", source)
    cert = env_value("ERP_DB_SSL_CERT", "", source)
    key = env_value("ERP_DB_SSL_KEY", "", source)
    if not any((ca, cert, key)):
        return None
    if not ca:
        raise RuntimeConfigError(
            "ERP_DB_SSL_CA is required when database TLS is configured."
        )
    ssl = {"ca": ca, "check_hostname": True}
    if cert:
        ssl["cert"] = cert
    if key:
        ssl["key"] = key
    return ssl


def discover_migrations(
    directory: Path,
    *,
    minimum_sequence: int = 4,
) -> tuple[Migration, ...]:
    migrations: list[Migration] = []
    seen_versions: set[str] = set()
    seen_sequences: set[int] = set()
    for path in sorted(directory.glob("V*.sql")):
        match = MIGRATION_PATTERN.fullmatch(path.name)
        if not match:
            raise RuntimeConfigError(f"Invalid migration filename: {path.name}")
        sequence = int(match.group("sequence"))
        if sequence < minimum_sequence:
            continue
        version = match.group(1)
        if version in seen_versions or sequence in seen_sequences:
            raise RuntimeConfigError(
                f"Duplicate migration version or sequence: {path.name}"
            )
        seen_versions.add(version)
        seen_sequences.add(sequence)
        # Git may materialize the same tracked SQL with LF on Linux and CRLF
        # on Windows. Normalize line endings before hashing so a checkout
        # difference is not mistaken for an applied-migration mutation.
        raw_sql = path.read_bytes()
        normalized_sql = raw_sql.replace(b"\r\n", b"\n").replace(b"\r", b"\n")
        checksum = hashlib.sha256(normalized_sql).hexdigest()
        crlf_sql = normalized_sql.replace(b"\n", b"\r\n")
        compatible_checksums = tuple(
            sorted(
                {
                    hashlib.sha256(raw_sql).hexdigest(),
                    hashlib.sha256(crlf_sql).hexdigest(),
                }
                - {checksum}
            )
        )
        migrations.append(
            Migration(
                version=version,
                sequence=sequence,
                description=match.group("description").replace("_", " "),
                path=path,
                checksum=checksum,
                compatible_checksums=compatible_checksums,
            )
        )
    migrations.sort(key=lambda item: item.sequence)
    if not migrations:
        raise RuntimeConfigError(
            f"No migrations at or after sequence {minimum_sequence:03d}."
        )
    expected = list(range(minimum_sequence, migrations[-1].sequence + 1))
    actual = [item.sequence for item in migrations]
    if actual != expected:
        missing = sorted(set(expected) - set(actual))
        raise RuntimeConfigError(
            "Migration sequence has gaps: "
            + ", ".join(f"{item:03d}" for item in missing)
        )
    return tuple(migrations)


def migration_state(
    migrations: tuple[Migration, ...],
    applied: Mapping[str, str],
) -> dict:
    known = {item.version: item for item in migrations}
    checksum_mismatches = [
        version
        for version, checksum in applied.items()
        if version in known
        and not migration_checksum_matches(known[version], checksum)
    ]
    unknown_applied = sorted(version for version in applied if version not in known)
    pending = [item.version for item in migrations if item.version not in applied]
    return {
        "current": not pending and not checksum_mismatches and not unknown_applied,
        "pending": pending,
        "checksumMismatches": sorted(checksum_mismatches),
        "unknownApplied": unknown_applied,
        "latest": migrations[-1].version,
    }


def normalized_store_ids(user: Mapping) -> list[int]:
    result: list[int] = []
    for value in user.get("store_ids") or []:
        try:
            store_id = int(value)
        except (TypeError, ValueError):
            continue
        if store_id not in result:
            result.append(store_id)
    return result


def allowed_store_id(user: Mapping, store_id) -> int:
    try:
        normalized = int(store_id)
    except (TypeError, ValueError) as exc:
        raise RuntimeConfigError("请选择门店") from exc
    if normalized not in normalized_store_ids(user):
        raise RuntimeConfigError("无权访问该门店")
    return normalized


def store_scope_clause(user: Mapping, alias: str = "") -> tuple[str, list[int]]:
    store_ids = normalized_store_ids(user)
    if not store_ids:
        return "1=0", []
    column = f"{alias}.store_id" if alias else "store_id"
    placeholders = ",".join(["%s"] * len(store_ids))
    return f"{column} IN ({placeholders})", store_ids
