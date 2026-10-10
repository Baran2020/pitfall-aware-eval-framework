"""
pragma_compatibility_checker.py

Standalone module that checks whether a Solidity contract's declared pragma
minimum version is actually the REAL minimum version its own code compiles
under. Used by ObfuscationEngine.get_verified_min_version() for the P3
(version-perturbation) dataset variant.

Root cause this fixes: ObfuscationEngine.get_version_bounds() computes the
"min" pragma by zeroing the patch number of the declared version (e.g.
"^0.4.24" -> "0.4.0"), regardless of whether the contract's own code uses
language features introduced after that floor (require/revert/assert were
added in solc 0.4.10) -- and regardless of the fact that a caret pragma's
own semantic floor is the declared version itself (^0.4.24 means
">=0.4.24 <0.5.0" in Solidity's own pragma grammar, not ">=0.4.0"). Verified
separately on the `user` dataset (2457 contracts, all pragma ^0.4.24): the
old zero-patch approach produced a P3_updated_version_min dataset where
57.5% of records (1404/2457) failed to compile at all.

Two search tiers, both ascending, stopping at the first version that
compiles:
  1. solcx's native binary archive -- fast, no extra runtime dependency,
     but solcx refuses to consider anything below 0.4.11 (its own
     MINIMAL_SOLC_VERSION constant), even though older binaries exist.
  2. A solc-js/Node.js bridge for 0.4.0-0.4.10 -- solc-js's own npm
     package is broken for exactly 0.4.0 (its published soljson.js is a
     stale GitHub-Pages 404 page, not a compiler; 0.4.1+ are fine), so the
     real compiler build for whatever version is needed is fetched from
     the project's GitHub Releases page and loaded through a working
     solc-js "shell" (installed on demand: `npm install solc@0.4.1` into a
     local cache dir). Skipped gracefully (falls back to tier 1 only) if
     Node.js/npm aren't available in this environment.

Without tier 2, every contract whose real floor is below 0.4.11 gets
reported as needing 0.4.11 regardless of how far below that its code
would actually still compile -- clustering nearly all of a dataset's
"real minimum" at the same single value (0.4.11) and losing the per-
contract variation a genuine version-sensitivity test needs.
"""
import json
import os
import re
import shutil
import subprocess

import solcx

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

PRAGMA_RE = re.compile(r"pragma\s+solidity\s+([^;]+);")
VERSION_TOKEN_RE = re.compile(r"\d+\.\d+\.\d+")

# Below solcx's own MINIMAL_SOLC_VERSION floor -- these can only be tried
# via the solc-js/Node.js bridge, never through solcx's native installer.
BRIDGE_CANDIDATES = ["0.4.0", "0.4.1", "0.4.2", "0.4.3", "0.4.4", "0.4.5",
                     "0.4.6", "0.4.7", "0.4.8", "0.4.9", "0.4.10"]

_domain_patched = False
_installable_versions_cache = None  # populated once by _get_native_candidates()
_node_wrapper_ready = None  # tri-state: None = not checked yet, True/False after

NODE_WRAPPER_DIR = os.path.join(SCRIPT_DIR, "_node_solc_wrapper")
NODE_SOLC_MODULE_DIR = os.path.join(NODE_WRAPPER_DIR, "node_modules", "solc")
SOLJSON_CACHE_DIR = os.path.join(SCRIPT_DIR, "_solcjs_cache")
BRIDGE_SCRIPT = os.path.join(SCRIPT_DIR, "solcjs_bridge.js")


def _patch_solcx_domain():
    # solc-bin.ethereum.org is decommissioned; repoint at the current host
    # (same fix as WIDENNET's Dockerfile). Idempotent/cheap -- safe to call
    # on every check_min_compatibility() invocation.
    global _domain_patched
    if _domain_patched:
        return
    import solcx.install as m
    m.BINARY_DOWNLOAD_BASE = m.BINARY_DOWNLOAD_BASE.replace(
        "solc-bin.ethereum.org", "binaries.soliditylang.org"
    )
    _domain_patched = True


def _version_tuple(v):
    return tuple(int(x) for x in str(v).split("."))


def _get_native_candidates(declared_min):
    """Every solc version solcx can install that is <= the CONTRACT'S OWN
    declared version, ascending. Built dynamically from
    solcx.get_installable_solc_versions() (fetched once and cached at
    module level) instead of a hardcoded range -- a fixed list tuned for
    one dataset's pragma (e.g. only 0.4.x) would silently return no
    candidates at all for any contract declared at 0.5.x/0.6.x/0.7.x/0.8.x."""
    global _installable_versions_cache
    _patch_solcx_domain()
    if _installable_versions_cache is None:
        _installable_versions_cache = sorted(
            (str(v) for v in solcx.get_installable_solc_versions()),
            key=_version_tuple,
        )

    if declared_min is None:
        return _installable_versions_cache

    declared_tuple = _version_tuple(declared_min)
    return [v for v in _installable_versions_cache if _version_tuple(v) <= declared_tuple]


def extract_declared_min_version(content):
    """The pragma's own literal minimum bound, e.g. "0.4.24" for
    "pragma solidity ^0.4.24;". NOT zeroed to "0.4.0": a caret pragma's
    floor is the declared version itself, and a range pragma's floor is
    its first version token (the ">=" operand, by convention)."""
    match = PRAGMA_RE.search(content)
    if not match:
        return None
    tokens = VERSION_TOKEN_RE.findall(match.group(1))
    return tokens[0] if tokens else None


def extract_contract_name(content):
    for line in content.splitlines():
        words = line.strip().split()
        if "contract" in words:
            idx = words.index("contract")
            if idx < len(words) - 1:
                return words[idx + 1].strip("{")
    return None


def _try_compile_native(source_no_pragma, contract_name, version):
    solcx.install_solc(version)
    compiled = solcx.compile_source(
        source_no_pragma, output_values=["bin-runtime"], solc_version=version
    )
    if contract_name and not any(key.endswith(":" + contract_name) for key in compiled):
        return False
    return True


def _node_available():
    return shutil.which("node") is not None and shutil.which("npm") is not None


def _ensure_node_wrapper():
    """Installs a working solc-js "shell" (npm's solc@0.4.1, the oldest
    npm publish that isn't corrupted -- see module docstring) once, into a
    local cache dir. Returns False (without raising) if Node.js/npm aren't
    on PATH, so callers can skip the bridge tier gracefully."""
    global _node_wrapper_ready
    if _node_wrapper_ready is not None:
        return _node_wrapper_ready

    if os.path.exists(NODE_SOLC_MODULE_DIR):
        _node_wrapper_ready = True
        return True

    if not _node_available():
        _node_wrapper_ready = False
        return False

    os.makedirs(NODE_WRAPPER_DIR, exist_ok=True)
    try:
        subprocess.run(
            ["npm", "install", "solc@0.4.1"],
            cwd=NODE_WRAPPER_DIR, check=True,
            capture_output=True, timeout=180,
        )
        _node_wrapper_ready = os.path.exists(NODE_SOLC_MODULE_DIR)
    except Exception:
        _node_wrapper_ready = False
    return _node_wrapper_ready


def _fetch_soljson(version):
    """Downloads and caches the real compiler build for `version` from the
    official GitHub Releases page (npm's own solc@0.4.0 package ships a
    stale 404 page instead of a compiler; the Releases asset is the only
    working source for it). Raises if that version has no release asset."""
    os.makedirs(SOLJSON_CACHE_DIR, exist_ok=True)
    cache_path = os.path.join(SOLJSON_CACHE_DIR, f"soljson-v{version}.js")
    if os.path.exists(cache_path):
        return cache_path

    import requests

    meta = requests.get(
        f"https://api.github.com/repos/ethereum/solidity/releases/tags/v{version}",
        timeout=30,
    )
    meta.raise_for_status()
    assets = [a for a in meta.json().get("assets", []) if a["name"].startswith("soljson")]
    if not assets:
        raise RuntimeError(f"no soljson release asset found for v{version}")

    data = requests.get(assets[0]["browser_download_url"], timeout=60)
    data.raise_for_status()
    with open(cache_path, "wb") as f:
        f.write(data.content)
    return cache_path


def _try_compile_bridge(source_no_pragma, contract_name, version):
    if not _ensure_node_wrapper():
        return False
    soljson_path = _fetch_soljson(version)
    # Overwrites the shell package's active soljson.js in place -- not safe
    # under concurrent compiles of two different versions at once; fine
    # here since candidates are tried sequentially.
    shutil.copyfile(soljson_path, os.path.join(NODE_SOLC_MODULE_DIR, "soljson.js"))

    proc = subprocess.run(
        ["node", BRIDGE_SCRIPT, NODE_SOLC_MODULE_DIR, contract_name or ""],
        input=source_no_pragma, capture_output=True, text=True, timeout=120,
    )
    if proc.returncode != 0:
        return False
    try:
        result = json.loads(proc.stdout)
    except Exception:
        return False
    return bool(result.get("runtimeBytecode")) and not result.get("errors")


def find_real_min_compatible_version(content, declared_min=None):
    """Strips the pragma line (so the source only gets a compiler-version
    WARNING, never a hard error, letting genuine syntax/feature
    incompatibilities surface cleanly) and returns the minimum version that
    actually compiles it, or None if nothing does.

    Runs the (cheap, no subprocess) native tier FIRST, then only spends time
    on the (expensive, one Node.js subprocess per candidate) bridge tier
    when it can actually change the answer:
      - If native's search had to go ABOVE its own lowest candidate to find
        a match (e.g. `pure` needs 0.4.16, so 0.4.11-0.4.15 all fail), the
        bridge tier (0.4.0-0.4.10, strictly older/less-featured) is
        guaranteed to fail too -- skipped entirely.
      - Otherwise (native's lowest candidate itself already compiles, e.g.
        a contract using `require`, present since 0.4.10, compiles fine at
        native's floor of 0.4.11), there's a real chance an even older
        version works. A single cheap probe at the bridge tier's highest
        candidate (closest to native's floor) decides whether the full
        11-candidate bridge search is worth running at all: if even that
        closest version fails, everything older will too.
    This turns the common case (majority of a dataset needs >=0.4.10
    features) from ~11 wasted Node.js subprocess calls into 1.
    """
    _patch_solcx_domain()
    no_pragma = PRAGMA_RE.sub("", content, count=1)
    contract_name = extract_contract_name(content)

    native_candidates = _get_native_candidates(declared_min)
    native_min = None
    for version in native_candidates:
        try:
            if _try_compile_native(no_pragma, contract_name, version):
                native_min = version
                break
        except Exception:
            continue

    at_native_floor = bool(
        native_min and native_candidates and native_min == native_candidates[0]
    )
    if not at_native_floor:
        # Either nothing compiled natively, or the match was strictly above
        # native's own lowest candidate -- the bridge tier is entirely
        # older/less-featured than that lowest candidate, so it cannot help.
        return native_min

    if declared_min is not None:
        declared_tuple = _version_tuple(declared_min)
        bridge_candidates = [v for v in BRIDGE_CANDIDATES if _version_tuple(v) <= declared_tuple]
    else:
        bridge_candidates = list(BRIDGE_CANDIDATES)

    if not bridge_candidates:
        return native_min

    probe_version = bridge_candidates[-1]
    try:
        probe_ok = _try_compile_bridge(no_pragma, contract_name, probe_version)
    except Exception:
        probe_ok = False

    if not probe_ok:
        return native_min

    for version in bridge_candidates:
        try:
            if _try_compile_bridge(no_pragma, contract_name, version):
                return version
        except Exception:
            continue

    return native_min


def check_min_compatibility(content):
    """
    Returns a dict:
        declared_min   -- the pragma's own literal minimum version, or None
        real_min       -- the actual minimum solc version the code compiles
                           under (bridge tier 0.4.0-0.4.10, then solcx
                           native tier, both capped at declared_min), or
                           None if no candidate worked
        is_real_change -- True only if real_min is strictly lower than
                           declared_min, i.e. rewriting the pragma to
                           real_min is a genuine downgrade. False when
                           they're equal (or real_min couldn't be
                           determined) -- in that case the P3 "min" variant
                           would be byte-for-byte identical to the original
                           for this contract, so it must not be counted as
                           a real perturbation.
    """
    declared_min = extract_declared_min_version(content)
    real_min = find_real_min_compatible_version(content, declared_min=declared_min)
    is_real_change = bool(
        declared_min and real_min and
        _version_tuple(real_min) < _version_tuple(declared_min)
    )
    return {
        "declared_min": declared_min,
        "real_min": real_min,
        "is_real_change": is_real_change,
    }
