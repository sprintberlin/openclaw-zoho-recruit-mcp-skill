#!/usr/bin/env python3
"""Portable endpoint resolution for the Zoho Recruit helper CLIs.

Resolution order for the MCP URL:
1. --mcp-url
2. --profile (or an app-specific/generic profile environment variable)
3. the app-specific endpoint environment variable(s)

Profile files are local configuration and must never be committed with real URLs.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
import re
from urllib.parse import urlsplit


DEFAULT_PROFILES_FILE = "~/.config/zoho-mcp/profiles.json"
_PROFILE_ENV = "ZOHO_MCP_PROFILE"
_PROFILES_FILE_ENV = "ZOHO_MCP_PROFILES_FILE"
_ENV_NAME = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")
_ORG_ID = re.compile(r"^[A-Za-z0-9_-]+$")


class EndpointResolutionError(RuntimeError):
    """Raised when an MCP endpoint cannot be resolved safely."""


def _validate_organization_id(value, source):
    value = str(value or "").strip()
    if not value:
        raise EndpointResolutionError(f"{source} is empty")
    if not _ORG_ID.fullmatch(value):
        raise EndpointResolutionError(f"{source} is not a valid organization ID")
    return value


def add_endpoint_arguments(parser):
    """Add shared multi-account endpoint options to an argparse parser."""
    group = parser.add_argument_group("MCP endpoint selection")
    group.add_argument(
        "--mcp-url",
        metavar="URL",
        help="use this endpoint for this invocation (highest priority; credential may be visible in process listings)",
    )
    group.add_argument(
        "--profile",
        metavar="NAME",
        help="select a named account from the Zoho MCP profiles file",
    )
    group.add_argument(
        "--profiles-file",
        metavar="PATH",
        help=f"profiles JSON path (default: {_PROFILES_FILE_ENV} or {DEFAULT_PROFILES_FILE})",
    )
    group.add_argument(
        "--organization-id",
        metavar="ID",
        help="Zoho Recruit organization ID for this invocation",
    )
    return parser


def _option(args, name):
    return getattr(args, name, None) if args is not None else None


def _validate_url(value, source):
    value = str(value or "").strip()
    if not value:
        raise EndpointResolutionError(f"{source} is empty")
    if any(char.isspace() for char in value):
        raise EndpointResolutionError(f"{source} contains whitespace")
    parsed = urlsplit(value)
    if parsed.scheme not in {"https", "http"} or not parsed.netloc:
        raise EndpointResolutionError(f"{source} must be an absolute HTTP(S) URL")
    return value


def _profile_name(args, service, environ):
    explicit = _option(args, "profile")
    if explicit:
        return explicit
    app_env = f"ZOHO_{service.upper()}_MCP_PROFILE"
    return environ.get(app_env) or environ.get(_PROFILE_ENV)


def _profiles_path(args, environ):
    raw = _option(args, "profiles_file") or environ.get(_PROFILES_FILE_ENV) or DEFAULT_PROFILES_FILE
    return Path(raw).expanduser()


def _load_profiles(path):
    try:
        document = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise EndpointResolutionError(f"profiles file not found: {path}") from exc
    except OSError as exc:
        raise EndpointResolutionError(f"profiles file cannot be read: {path}") from exc
    except json.JSONDecodeError as exc:
        raise EndpointResolutionError(
            f"profiles file is invalid JSON at line {exc.lineno}, column {exc.colno}: {path}"
        ) from exc

    if not isinstance(document, dict):
        raise EndpointResolutionError(f"profiles file must contain a JSON object: {path}")
    profiles = document.get("profiles")
    if not isinstance(profiles, dict):
        raise EndpointResolutionError(f"profiles file has no 'profiles' object: {path}")
    return profiles


def _service_entry(profile, service):
    services = profile.get("services")
    if not isinstance(services, dict):
        return None
    entry = services.get(service)
    return entry if isinstance(entry, dict) else None


def _url_from_entry(entry, environ):
    """Resolve a service entry to a URL without ever echoing the secret."""
    url = entry.get("url")
    if isinstance(url, str) and url.strip():
        return _validate_url(url, "profile url")

    env_name = entry.get("env")
    if isinstance(env_name, str) and env_name.strip():
        if not _ENV_NAME.fullmatch(env_name.strip()):
            raise EndpointResolutionError(f"profile env name is not a valid variable name: {env_name}")
        value = environ.get(env_name.strip())
        if value:
            return _validate_url(value, f"environment variable {env_name.strip()}")
        raise EndpointResolutionError(f"environment variable {env_name.strip()} is not set")

    url_file = entry.get("url_file")
    if isinstance(url_file, str) and url_file.strip():
        path = Path(url_file.strip()).expanduser()
        try:
            value = path.read_text(encoding="utf-8").strip()
        except OSError as exc:
            raise EndpointResolutionError(f"url_file cannot be read: {path}") from exc
        if not value:
            raise EndpointResolutionError(f"url_file is empty: {path}")
        return _validate_url(value, f"url_file {path}")

    return None


def resolve_mcp_url(args, service="recruit", env_vars=("ZOHO_RECRUIT_MCP_URL",), environ=None):
    """Resolve the MCP endpoint URL from args, profiles, or environment."""
    environ = os.environ if environ is None else environ
    direct = _option(args, "mcp_url")
    if direct:
        return _validate_url(direct, "--mcp-url")

    profile_name = _profile_name(args, service, environ)
    if profile_name:
        path = _profiles_path(args, environ)
        profiles = _load_profiles(path)
        profile = profiles.get(profile_name)
        if not isinstance(profile, dict):
            raise EndpointResolutionError(f"profile not found in {path}: {profile_name}")
        entry = _service_entry(profile, service)
        if entry is None:
            raise EndpointResolutionError(
                f"profile '{profile_name}' has no services.{service} entry in {path}"
            )
        url = _url_from_entry(entry, environ)
        if url:
            return url
        raise EndpointResolutionError(
            f"profile '{profile_name}' services.{service} has no 'url', 'env', or 'url_file'"
        )

    for name in env_vars:
        value = environ.get(name)
        if value:
            return _validate_url(value, f"environment variable {name}")

    raise EndpointResolutionError(
        "no MCP endpoint configured: set ZOHO_RECRUIT_MCP_URL, use --profile, or pass --mcp-url"
    )


def resolve_organization_id(args, service="recruit", environ=None):
    """Resolve an optional organization ID.

    Recruit is usually account-scoped, so a missing organization ID is not an
    error here: callers that need one must ask for it explicitly.
    """
    environ = os.environ if environ is None else environ

    direct = _option(args, "organization_id")
    if direct:
        return _validate_organization_id(direct, "--organization-id")

    profile_name = _profile_name(args, service, environ)
    if profile_name:
        path = _profiles_path(args, environ)
        profiles = _load_profiles(path)
        profile = profiles.get(profile_name)
        if isinstance(profile, dict):
            entry = _service_entry(profile, service)
            if isinstance(entry, dict):
                value = entry.get("organization_id")
                if value:
                    return _validate_organization_id(value, f"profile '{profile_name}' organization_id")

    for name in (f"ZOHO_{service.upper()}_ORGANIZATION_ID", "ZOHO_ORGANIZATION_ID"):
        value = environ.get(name)
        if value:
            return _validate_organization_id(value, f"environment variable {name}")

    return None


def redact(text, secret):
    """Replace the endpoint with a placeholder in any message."""
    if not secret:
        return str(text or "")
    return str(text or "").replace(secret, "<MCP_URL>")
