#!/usr/bin/env python3
"""
CerebrumLux V8 Build Automation v7.37.9 (Final Robust MinGW Build - Incorporating all feedback)
- Auto-resume (incremental fetch + gclient sync)
- Proxy fallback & git/http tuning for flaky networks
-  MinGW toolchain usage (DEPOT_TOOLS_WIN_TOOLCHAIN=0)
- Copies built lib+headers into vcpkg installed tree for immediate use
- Robust logging and retries
- CRITICAL FIXES for gclient/gn/ninja execution & MinGW toolchain definition (args.gn & BUILD.gn for MinGW toolchain)
- Handles vs_toolchain.py Python 2/3 incompatibility safely
- Aggressive cleanup of problematic directories (optimized)
- Corrected .gclient 'name' field
- Improved libv8_monolith.a search path
- Dynamic log file naming
- Enhanced command execution logic for depot_tools binaries (gn.exe, gclient.py)
- Patches for "stamp" tool and "v8_use_external_startup_data" assert in BUILD.gn files
- FIX: Aggressive and persistent patch for vs_toolchain.py (pipes module & VS detection) before EACH gclient sync attempt.
- FIX: Using sys.executable to run gclient.py directly for better Python environment control.
- FIX: Reordered git checkout and DEPS/.gn patch steps to avoid "local changes would be overwritten" error.
- FIX: Added GitHub mirror for 'simdutf' and 'zlib' in DEPS patching to mitigate HTTP 429 rate limit.
- FIX: Enabled 'gclient sync -D' for automatic cleanup of unmanaged files.
- FIX: Directly patched 'build/dotfile_settings.gni' to define 'exec_script_whitelist' within its scope.
- FIX: Patched 'vs_toolchain.py' by PREPENDING a robust shim block, THEN DELETING original GetVisualStudioVersion(), DetectVisualStudioPath(), AND SetEnvironmentAndGetRuntimeDllDirs() bodies, resolving IndentationError and NameError.
- FIX: Directly patched 'build/config/win/visual_studio_version.gni' to forcefully set dummy values for visual_studio_path, visual_studio_version, and visual_studio_runtime_dirs, AND COMMENTING OUT the exec_script call that fetches toolchain_data. Also fixed re.compile/re.sub flags issue and regex character set issue by using f-strings with explicit double backslashes and re.escape.
- FIX: Corrected cmd_str initialization in run() helper and os.path.join in run_ninja_build().
- FIX: Removed 'tools/win' and 'tools/clang' dependencies from DEPS to prevent HTTP 429 rate limit errors for these submodules.
- FIX: Corrected retry sleep duration in gclient_sync_with_retry to use GCLIENT_RETRY_BACKOFF.
- FIX: Moved vs_toolchain.py self-test to main() AFTER initial gclient sync to prevent 'Invalid directory name' error.
- NEW: Disabled aggressive removal of V8_ROOT at start of script to allow incremental updates and prevent repeated full downloads.
- NEW: More robust GN/Ninja binary detection using _find_tool helper function.
- NEW: Improved onerror function for Windows compatibility using stat.S_IWRITE.
- FIX (v7.1): Corrected vs_toolchain.py shim and visual_studio_version.gni patches to provide *non-empty dummy paths* for wdk_path, sdk_path, and visual_studio_path to bypass GN assertions requiring non-empty values when Visual Studio is conceptually "set".
- FIX (v7.2): Resolved NameError: name 'vs_toolchain' is not defined by consistently using 'vs_toolchain_path.name' in log messages within gclient_sync_with_retry function.
- FIX (v7.3): Add patch for 'build/toolchain/win/setup_toolchain.py' to bypass calls to vs_toolchain.DetectVisualStudioPath and vs_toolchain.GetVisualStudioVersion to resolve AttributeError.
- FIX (v7.4): Corrected indentation in 'setup_toolchain.py' patch to resolve 'IndentationError: unexpected indent'.
- FIX (v7.5): Patched 'setup_toolchain.py' to completely replace _LoadToolchainEnv, bypassing the 'vcvarsall.bat' check and returning a dummy environment.
- FIX (v7.6): Further refined 'setup_toolchain.py' patch to ensure _LoadToolchainEnv returns a dictionary with all expected keys (vc_bin_dir, vc_lib_path, etc.) and added os.makedirs for dummy directories to bypass path existence checks.
- FIX (v7.7): Made log() function more robust against I/O errors and added auto-patching of args.gn within run_gn_gen() to inject missing vcvars_toolchain_data variables based on GN error output.
- FIX (v7.8): Corrected 'bad escape' error in _patch_setup_toolchain_py by using Path.as_posix() for dummy paths and fixed log() function typo for error file writing.
- FIX (v7.9): Implemented automatic injection of 'vcvars_toolchain_data' object with all required dummy paths directly into args.gn within run_gn_gen() to resolve "No value named 'vc_lib_path' in scope 'vcvars_toolchain_data'" error and ensured corresponding dummy directories are created on disk.
- FIX (v7.10): Corrected "May only use "." for identifiers" error in args.gn patching by pre-formatting paths with .as_posix() in Python, removing .replace() calls from GN strings.
- FIX (v7.11): Further refined args.gn injection logic in run_gn_gen() for vcvars_toolchain_data to ensure paths are direct string literals using .as_posix() without any GN-side processing methods, addressing "May only use "." for identifiers" error. Updated shim version.
- FIX (v7.12): Added a new patch function (_patch_build_gn) to neutralize the 'exec_script' call for 'setup_toolchain.py' within 'build/config/win/BUILD.gn', thereby relying purely on args.gn injection for 'vcvars_toolchain_data'. Updated shim version.
- FIX (v7.13): Aggressively patched 'build/config/win/BUILD.gn' to replace direct accesses to 'vcvars_toolchain_data.<field>' with hardcoded dummy paths (using .as_posix()) after neutralizing the exec_script call, resolving "No value named 'vc_lib_path' in scope 'vcvars_toolchain_data'" error. All dummy path injections now consistently use .as_posix(). Updated shim version.
- FIX (v7.14): Corrected "Invalid token" error in _patch_build_gn when replacing `vcvars_toolchain_data.<field>` by ensuring replacement strings for GN are exact string literals (e.g., `"C:/path"`) without extra backslashes in Python's re.sub method. Updated shim version.
- FIX (v7.15): Implemented a prioritized patching order in _patch_build_gn to first replace all `defined(vcvars_toolchain_data.<field>)` calls with `true`, then handle direct assignments, resolving the `Bad thing passed to defined()` error. Updated shim version.
- FIX (v7.16): Corrected `SyntaxError: closing parenthesis ')' does not match opening parenthesis '['` in `main()` function's `git reset` command. Updated shim version.
- FIX (v7.17): Removed `/* ... */` style comments from `defined()` bypasses within `_patch_build_gn` function to comply with GN's strict `#` comment syntax, resolving `Invalid token` error. Updated shim version.
- FIX (v7.18): Implemented a new patch function `_patch_toolchain_win_build_gn` to neutralize `win_toolchain_data = exec_script(...)` in `build/toolchain/win/BUILD.gn` and directly replace all accesses to `win_toolchain_data.<field>` with hardcoded dummy paths, addressing "No value named 'vc_bin_dir' in scope 'win_toolchain_data'" error. Also ensured dummy directories for these new paths are created. Updated shim version.
- FIX (v7.19): Refined `_patch_toolchain_win_build_gn` to replace MSVC-specific tool definitions (`cl`, `link`, `lib`) directly with MinGW paths (or safe dummies) as literal strings, and implemented `_filter_gn_comments` to ensure strict GN comment syntax. Updated shim version.
- FIX (v7.20): Reworked `_patch_toolchain_win_build_gn` to inject `win_toolchain_data` as a GN scope with pre-formatted paths, then let GN interpolation handle tool definitions. This resolves `Invalid token` errors related to embedded paths in tool definitions in `build/toolchain/win/BUILD.gn`. Updated shim version.
- FIX (v7.21): Corrected `Expected ')'` error in `_patch_toolchain_win_build_gn` by ensuring `exec_script` neutralization leaves no remnant bad syntax and correctly injecting the `win_toolchain_data` object directly into the GN file. Updated shim version.
- FIX (v7.22): Added `include_flags_imsvc: ''` to `win_toolchain_data` injection in `_patch_toolchain_win_build_gn` to resolve "No value named 'include_flags_imsvc'" error. Implemented `warnings.filterwarnings` for `DeprecationWarning` in `main()`. Updated shim version.
- FIX (v7.23): Patched `_patch_toolchain_win_build_gn` to explicitly replace `sys_lib_flags = ...` and `sys_include_flags = ...` assignments with `sys_lib_flags = []` and `sys_include_flags = []` to satisfy GN's "Expecting assignment" rule. Updated shim version.
- FIX (v7.24): Refined `_patch_toolchain_win_build_gn` regex for `sys_lib_flags` and `sys_include_flags` to be more general (`.*` instead of `\\[\\s\\S]*?\\]`) and removed `re.DOTALL` to correctly handle single-line assignments, resolving "Expecting assignment or function call" error. Updated shim version.
- FIX (v7.25): Corrected `NameError: name 'fake_vs_base_path_path_obj' is not defined` in `_patch_toolchain_win_build_gn`. Updated shim version. Also refined `_patch_toolchain_win_build_gn` to aggressively remove previous `sys_flags` assignments and inject new ones at a safe location, addressing "Expecting assignment or function call" for `} else {`.
- FIX (v7.26): Removed `re.REVERSE` which caused `AttributeError`. Refined `_patch_toolchain_win_build_gn` to directly replace `sys_flags` assignments or inject them if missing, addressing "Expecting assignment or function call" and "Assignment had no effect" related to `sys_flags`. Updated shim version.
- FIX (v7.27): Further refined `_patch_toolchain_win_build_gn` to remove direct assignments of `sys_lib_flags` and `sys_include_flags` from `build/toolchain/win/BUILD.gn` entirely, and added these flags to the `win_toolchain_data` object injected into `args.gn` via `run_gn_gen`, resolving "Assignment had no effect" for `sys_lib_flags`. Updated shim version.
- FIX (v7.28): Introduced a more targeted patch in `_patch_toolchain_win_build_gn` to specifically inject `sys_include_flags = []` and `sys_lib_flags = []` into `build/toolchain/win/BUILD.gn` right before the `msvc_toolchain` template definition, in addition to defining them in `args.gn`'s `win_toolchain_data`. This resolves the "Undefined identifier in string expansion" error for `sys_include_flags`. Updated shim version.
- FIX (v7.29): Neutralized the problematic `prefix = rebase_path(...)` assignment in `build/toolchain/win/BUILD.gn` by commenting it out, addressing the "Assignment had no effect" error related to `prefix`. Updated shim version.
- FIX (v7.30): Applied comprehensive regex and replacement string corrections across patching functions to ensure proper named-group usage (`(?P<name>...)`), avoid incorrect `\\g` usage, and leverage lambda for safer substitutions, addressing residual patching failures and enhancing overall robustness based on detailed analysis. Updated shim version.
- FIX (v7.31): Aggressively modified `_patch_build_gn` to fully remove / replace all references and definitions of `vcvars_toolchain_data` in `build/config/win/BUILD.gn` with hardcoded dummy paths or `true` (for `defined()` checks). This directly addresses `ERROR at //build/config/win/BUILD.gn:305:40: Expecting assignment or function call. ],` by eliminating its source. Updated shim version.
- FIX (v7.32): Corrected `vc_bin_dir` path in `_LoadToolchainEnv` within `_patch_setup_toolchain_py` to include `Hostx64/x64`, ensuring consistency. Also, refined `_patch_build_gn` to handle specific list closure issues by ensuring no orphaned `]` or `,` remain after aggressive substitutions, and added `//` style comment stripping to `_filter_gn_comments` for better robustness. Updated shim version.
- FIX (v7.33): Resolved `bad escape \\g at position 55` error in `_patch_build_gn` by correcting an incorrect lambda replacement expression. Ensured all `re.sub` replacements use correct `lambda m: "..."` or direct string literals, avoiding problematic `\\g` usage. Updated shim version.
- FIX (v7.34): Further refined `_patch_build_gn` to handle `vcvars_toolchain_data` references more robustly, ensuring `re.sub` replacement strings are correctly formed literals. Specifically, adjusted the `access_pattern.sub` lambda to explicitly handle the `pre_assign` group and ensure the injected `dummy_path` is properly quoted, preventing `bad escape \\g` errors. Also, corrected `vc_lib_um_path`'s `fake_vs_base_for_gn_obj` typo in `run_gn_gen`. Updated shim version.
- FIX (v7.35): Addressed the persistent `bad escape \\g` error by implementing explicit string concatenation (`+` operator) instead of f-strings within `re.sub` lambda replacements for `_patch_build_gn` to avoid any implicit backslash interpretation. Also, corrected the `SyntaxWarning` in the docstring by using a raw string literal. Updated shim version.
- FIX (v7.36): Reviewed `_patch_build_gn` for a lingering `bad escape \\g` by ensuring all dynamic string components in `re.sub` replacements are handled to prevent premature backslash interpretation. Explicitly escaped `dummy_path` using `.replace('\\', '\\\\')` where `m.group()` is used within the replacement string, guaranteeing literal backslashes are passed to `re.sub`. Added `_sanitize_replacement_string` helper for robust path handling in replacements. Updated shim version.
- FIX (v7.37.1): Corrected the "bad escape \\g" error in _patch_build_gn by ensuring `re.sub` replacements use lambda functions directly to correctly handle named group backreferences (`\\g<indent>`) instead of constructing a replacement string that `re.sub` then re-parses. This prevents the `re.error` for incorrect `\\g` usage when part of a string literal.
- FIX (v7.37.2): Addressed the `SyntaxWarning: invalid escape sequence '\\g'` in the docstring by making the entire docstring a raw string. Corrected the `re.error: bad escape \\g` in `_patch_build_gn` by simplifying the `vcvars_data_object_pattern` to avoid backreferencing indentation within the regex pattern itself (`^\\g<indent>\\}`), making the pattern more robust to compile.
- FIX (v7.37.3): Resolved "Expected comma between items" in `build/config/win/BUILD.gn` by modifying `_patch_build_gn` to replace the `vcvars_toolchain_data` object definition with an empty string (`""`) instead of a comment block. This prevents GN from interpreting the comment as an invalid list item, ensuring correct list syntax.
- FIX (v7.37.4): Implemented `normalize_gn_lists` to automatically add missing commas between list items in `BUILD.gn` files. This directly fixes "Expected comma between items" errors within GN lists (e.g., `cflags`).
- FIX (v7.37.5): Addressed `IndentationError` in `patch_v8_deps_for_mingw` by explicitly ensuring correct indentation for the `build_config_win_build_gn_path` assignment and the subsequent `if normalize_gn_lists` block. Corrected remaining `SyntaxWarning: invalid escape sequence '\\g'` in the docstring by escaping all literal `\\g` occurrences as `\\\\g`.
- FIX (v7.37.6): Further refined `patch_v8_deps_for_mingw` to correctly handle control flow and indentation after `_patch_build_gn` and `_patch_toolchain_win_build_gn` calls, ensuring `normalize_gn_lists` and `git add` are always correctly invoked. Fully resolved all `SyntaxWarning: invalid escape sequence '\\g'` in docstring by explicitly escaping them.
- FIX (v7.37.7): CRITICAL: Re-examined `_patch_build_gn` and fixed the `orphaned_punctuation_pattern` to only remove *isolated commas* (`,`) on their own lines, instead of `]` or `}`. This prevents accidental deletion of essential list/block closing characters, directly resolving the "Expected comma between items" error in `cflags` lists.
- FIX (v7.37.8): CRITICAL: Reinstated the `re.sub` pattern within `normalize_gn_lists` that adds a comma before an `if` statement in a GN list. This was identified as essential for handling `cflags = [ ... "item" if (condition) { ... } ]` syntax.
- FIX (v7.37.9): Addressed "May only subscript identifiers" in `build/toolchain/win/BUILD.gn` by introducing a local temporary variable for `invoker` inside `_patch_toolchain_win_build_gn`. Resolved the recurring "Expecting assignment or function call. ]" in `build/config/win/BUILD.gn` by implementing a new `_clean_up_list_terminators` helper that aggressively removes blank/comment-only lines before list/scope closures. Ensured docstring `\\g` escapes are correct.
"""
import os
import sys
import subprocess
import shutil
import time
import datetime
import stat # For aggressive file removal
import json # For vcpkg.json
import re # For patching files
import warnings # For filtering warnings
from pathlib import Path # ADDED: For robust path handling

# ----------------------------
# === CONFIGURABLE PATHS ===
# ----------------------------
V8_VERSION = "9.1.269.39"
V8_REF = "7d3d62c91f69a702e5aa54c6b4dbbaa883683717" # Correct ref for V8 9.1.269.39 tag
V8_GIT_URL = "https://chromium.googlesource.com/v8/v8.git"
V8_GITHUB_MIRROR_URL = "https://github.com/v8/v8.git" # Fallback mirror

V8_ROOT = r"C:\v8-mingw" # V8 sources and build outputs root
DEPOT_TOOLS = r"C:\depot_tools" # Where depot_tools is cloned
MINGW_BIN = r"C:\Qt\Tools\mingw1310_64\bin" # MinGW compiler bin directory
VCPKG_ROOT = r"C:\vcpkg" # vcpkg root directory

V8_SRC = os.path.join(V8_ROOT, "v8") # Actual V8 source code directory (inside V8_ROOT)
OUT_DIR = os.path.join(V8_SRC, "out.gn", "mingw") # GN build output directory

# Log files are placed in a 'logs' subdirectory relative to where the script runs.
# This ensures V8_ROOT can be safely deleted.
LOG_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "logs")
LOG_FILE = os.path.join(LOG_DIR, f"CerebrumLux-V8-Build-{V8_VERSION}.log") # Dynamic log name
ERR_FILE = os.path.join(LOG_DIR, f"CerebrumLux-V8-Build-{V8_VERSION}-error.log") # Dynamic error log name

# Vcpkg port klasörü (güncelleme için kullanılır)
PORT_DIR = os.path.join(VCPKG_ROOT, "ports", "v8")


MAX_GCLIENT_RETRIES = 5
GCLIENT_RETRY_BACKOFF = [10, 20, 40, 80, 160]  # seconds
GIT_RETRY = 3
SYNC_RETRY = 3
NINJA_TARGET = "v8_monolith"

# Proxy fallback list (HTTP proxies). Add any internal proxies or empty list to disable.
PROXY_FALLBACKS = [
    "",  # empty = try direct first
    # "http://172.21.129.18:3128",  # example local proxy; replace with real if you have.
]

# ----------------------------
# === Helpers & Logging ===
# ----------------------------
def timestamp():
    return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]

def log(level, msg, to_console=True):
    line = f"[{timestamp()}] [{level}] {msg}"
    os.makedirs(LOG_DIR, exist_ok=True) # Ensure log directory exists
    try:
        # Use a new 'with open' block for each write to prevent 'I/O operation on closed file'
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(line + "\n")
    except Exception as e:
        # Fallback print if cannot write to file, but don't stop execution
        if to_console:
            print(f"ERROR: Could not write to main log file: {e} - {line}")

    if level in ("ERROR", "FATAL"):
        try:
            with open(ERR_FILE, "a", encoding="utf-8") as ef:
                ef.write(line + "\n") # Corrected: use 'ef' for error file
        except Exception as e:
            if to_console:
                print(f"ERROR: Could not write to error log file: {e} - {line}")
    if to_console:
        print(line)

def onerror(func, path, exc_info):
    """
    Error handler for shutil.rmtree.
    If the error is due to an access problem (e.g. file locked),
    it changes the file's permissions to allow removal.
    Uses stat.S_IWRITE for better Windows compatibility.
    """
    if not os.access(path, os.W_OK):
        try:
            os.chmod(path, stat.S_IWRITE) # Use S_IWRITE for Windows.
        except Exception:
            # Fallback for other potential issues or if S_IWRITE fails
            try:
                os.chmod(path, stat.S_IWUSR)
            except Exception:
                pass
        func(path)
    else:
        raise

def aggressive_rmtree(path):
    """Aggressively removes a directory, handling read-only or locked files."""
    log("DEBUG", f"Attempting aggressive removal of: {path}", to_console=False)
    if not os.path.exists(path):
        return

    # Attempt to terminate processes that might lock files
    try:
        subprocess.run(f'taskkill /F /IM python.exe /T', shell=True, check=False, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        subprocess.run(f'taskkill /F /IM git.exe /T', shell=True, check=False, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        subprocess.run(f'taskkill /F /IM gclient.exe /T', shell=True, check=False, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        subprocess.run(f'taskkill /F /IM gn.exe /T', shell=True, check=False, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        subprocess.run(f'taskkill /F /IM ninja.exe /T', shell=True, check=False, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        time.sleep(2) # Give processes time to die
    except Exception as e:
        log("WARN", f"Failed to kill locking processes: {e}", to_console=False)

    # Aggressive retry removal
    for i in range(3):
        try:
            shutil.rmtree(path, onerror=onerror)
            time.sleep(1)
            if not os.path.exists(path):
                log("DEBUG", f"Successfully removed {path} on retry {i+1}", to_console=False)
                return
        except Exception as e:
            log("WARN", f"Aggressive rmtree attempt {i+1} failed for {path}: {e}", to_console=False)
        time.sleep(2)

    raise OSError(f"Failed to aggressively remove directory after multiple attempts: {path}")

def run(cmd_list, cwd=None, env=None, check=True, capture_output=True):
    """
    Run a shell command. Returns subprocess.CompletedProcess or raises.
    `cmd_list` should be a list of arguments for shell=False.
    Captures stdout/stderr as DEBUG logs if capture_output is True.
    """
    # FIX: Corrected cmd_str initialization for robustness
    cmd_str = ' '.join(cmd_list) if isinstance(cmd_list, list) else str(cmd_list)
    log("INFO", f"RUN: {cmd_str} (CWD: {cwd or os.getcwd()})", to_console=False)
    try:
        cp = subprocess.run(cmd_list, cwd=cwd, env=env, shell=False, # shell=False for list of commands
                            check=check, text=True, capture_output=capture_output,
                            encoding='utf-8', errors='replace') # errors='replace' for problematic output
        if capture_output:
            # DEBUG logs for stdout/stderr to avoid overwhelming console/INFO log
            if cp.stdout:
                log("DEBUG", f"STDOUT:\n{cp.stdout}", to_console=False)
            if cp.stderr:
                log("DEBUG", f"STDERR:\n{cp.stderr}", to_console=False)
        return cp
    except subprocess.CalledProcessError as e:
        log("ERROR", f"Command failed (code {e.returncode}): {cmd_str}")
        if capture_output:
            log("ERROR", f"Stdout: {e.stdout}", to_console=False)
            log("ERROR", f"Stderr: {e.stderr}", to_console=False)
        raise
    except FileNotFoundError as e:
        log("FATAL", f"Command not found: {cmd_list[0] if isinstance(cmd_list, list) else cmd_list.split(' ')[0]}. Ensure it's in PATH. Error: {e}")
        raise
    except Exception as e:
        log("FATAL", f"An unexpected error occurred while running command: {e}")
        raise

# ----------------------------
# === Environment prep ===
# ----------------------------
def prepare_subprocess_env():
    env = os.environ.copy()
    path_parts = env.get("PATH", "").split(os.pathsep)
    new_path = []
    
    if DEPOT_TOOLS not in new_path:
        new_path.append(DEPOT_TOOLS)
    
    if MINGW_BIN not in new_path:
        new_path.append(MINGW_BIN)
        
    py_dir = os.path.dirname(sys.executable)
    if py_dir not in new_path:
        new_path.append(py_dir)
    py_scripts_dir = os.path.join(py_dir, "Scripts")
    if os.path.exists(py_scripts_dir) and py_scripts_dir not in new_path:
        new_path.append(py_scripts_dir)
    
    for p in path_parts:
        if p and p not in new_path: # Also check for empty strings from split
            new_path.append(p)
            
    env["PATH"] = os.pathsep.join(new_path)
    env["DEPOT_TOOLS_WIN_TOOLCHAIN"] = "0"
    env["PYTHONUTF8"] = "1"
    return env

# ----------------------------
# === Git helpers (with retries + proxy fallback) ===
# ----------------------------
def git_configure_proxy(env, proxy_url):
    """Configures Git's global HTTP/S proxy settings."""
    if proxy_url:
        log("INFO", f"Setting Git proxy to: {proxy_url}", to_console=False)
        run(['git', 'config', '--global', 'http.proxy', proxy_url], env=env, check=False, capture_output=False)
        run(['git', 'config', '--global', 'https.proxy', proxy_url], env=env, check=False, capture_output=False)
    else:
        log("INFO", "Unsetting Git proxy.", to_console=False)
        run(['git', 'config', '--global', '--unset', 'http.proxy'], env=env, check=False, capture_output=False)
        run(['git', 'global', '--unset', 'https.proxy'], env=env, check=False, capture_output=False)

def git_fetch_and_reset(env, repo_dir, ref, remote="origin"):
    """Performs a git fetch, checkout, and hard reset for a given repository and ref."""
    for attempt in range(1, GIT_RETRY + 1):
        try:
            log("INFO", f"Git fetch/reset attempt {attempt}/{GIT_RETRY} for {repo_dir} @ {ref}.")
            run(['git', 'remote', 'update', '--prune'], cwd=repo_dir, env=env, capture_output=True)
            run(['git', 'fetch', remote, '--tags', '--prune', '--no-recurse-submodules'], cwd=repo_dir, env=env, capture_output=True)
            run(['git', 'checkout', '--detach', ref], cwd=repo_dir, env=env, capture_output=True)
            run(['git', 'reset', '--hard', ref], cwd=repo_dir, env=env, capture_output=True)
            log("INFO", f"Checked out V8 ref {ref}.")
            return
        except Exception as e:
            log("WARN", f"git fetch/reset attempt {attempt} failed: {e}")
            if attempt < GIT_RETRY:
                time.sleep(5 * attempt)
            else:
                raise

def git_clone_with_retry(env, target_dir, url):
    """Clones a Git repository with retries and proxy fallbacks."""
    for proxy_url in PROXY_FALLBACKS:
        try:
            git_configure_proxy(env, proxy_url)
            for attempt in range(1, GIT_RETRY + 1):
                try:
                    log("INFO", f"Cloning attempt {attempt}/{GIT_RETRY} from {url} via proxy '{proxy_url}'")
                    run(['git', 'clone', url, target_dir], env=env)
                    log("INFO", "Git clone successful.")
                    return
                except Exception as e:
                    log("WARN", f"git clone attempt {attempt} failed: {e}")
                    if attempt < GIT_RETRY:
                        time.sleep(5 * attempt)
                    else:
                        raise
        except Exception as e:
            log("ERROR", f"Proxy configuration or clone failed for proxy '{proxy_url}': {e}")
    raise RuntimeError(f"All git clone attempts failed for {url}.")

# ----------------------------
# === gclient helpers ===
# ----------------------------
def write_gclient_file(root_dir: str, url: str):
    """Writes a .gclient file in the root directory."""
    gclient_content = (
        "solutions = [\n"
        "  {\n"
        f"    'name': 'v8',\n"
        f"    'url': '{url}',\n"
        "    'deps_file': 'DEPS',\n"
        "    'managed': False,\n"
        "  },\n"
        "]\n"
    )
    path = Path(root_dir) / ".gclient" # Use Path for consistency
    with path.open("w", encoding="utf-8") as f:
        f.write(gclient_content)
    log("INFO", f".gclient written to: {path} with name 'v8'.")

def _apply_vs_toolchain_patch_logic(vs_toolchain_path: Path) -> bool:
    """Internal helper to aggressively patch vs_toolchain.py."""
    try:
        if not vs_toolchain_path.exists():
            log("DEBUG", f"'{vs_toolchain_path.name}' not found at {vs_toolchain_path}, cannot patch.", to_console=False)
            return False

        text = vs_toolchain_path.read_text(encoding="utf-8")
        original_text = text
        modified = False

        # Prepare a small top-of-file shim to guarantee definitions are present early.
        shim_block = (
            "# --- CerebrumLux injected shim START (v7.36) ---\n" # Updated shim version marker
            "import sys\n"
            "import subprocess\n"
            "from types import SimpleNamespace\n"
            "\n"
            "# The 'pipes' module is removed in Python 3.13+. Provide a compatibility shim.\n"
            "if 'pipes' not in sys.modules:\n"
            "    pipes = SimpleNamespace(quote=lambda s: subprocess.list2cmdline([s]))\n"
            "else:\n"
            "    pipes = sys.modules['pipes']\n"
            "\n"
            "def DetectVisualStudioPath():\n"
            "    return r'C:\\FakeVS'\n"
            "\n"
            "def GetVisualStudioVersion():\n"
            "    return '16.0'\n"
            "\n"
            "def SetEnvironmentAndGetRuntimeDllDirs():\n"
            "    # CerebrumLux shim: bypass all VS runtime detection for MinGW builds.\n"
            "    # Return a dummy scope for GN scripts, defining expected variables.\n"
            "    import os\n"
            "    os.environ['GYP_MSVS_OVERRIDE_PATH'] = DetectVisualStudioPath()\n"
            "    os.environ['DEPOT_TOOLS_WIN_TOOLCHAIN'] = '0'\n"
            "    return {\n"
            "        'path': DetectVisualStudioPath(),\n"
            "        'vs_path': DetectVisualStudioPath(),\n"
            "        'sdk_path': r'C:\\FakeSDK',\n"
            "        'wdk_path': r'C:\\FakeWDK',\n"
            "        'runtime_dirs': [r'C:\\FakeVS\\VC\\Tools\\MSVC\\14.16.27023\\bin\\Hostx64\\x64'],\n"
            "        'version': GetVisualStudioVersion(),\n"
            "    }\n"
            "# --- CerebrumLux injected shim END ---\n\n"
        )

        if f"# --- CerebrumLux injected shim START (v7.36) ---" not in text: # Updated version check
            text = shim_block + text
            modified = True
            log("INFO", f"Prepended CerebrumLux shim to '{vs_toolchain_path.name}'.", to_console=False)
        else:
            log("DEBUG", f"CerebrumLux shim already present in '{vs_toolchain_path.name}', skipping prepend.", to_console=False)
            
            old_shim_pattern = re.compile(r"# --- CerebrumLux injected shim START \(v[\d\.]+\) ---[\s\S]*?# --- CerebrumLux injected shim END ---\n\n", re.MULTILINE)
            if old_shim_pattern.search(text):
                text = old_shim_pattern.sub("", text)
                log("DEBUG", f"Removed old CerebrumLux shim from '{vs_toolchain_path.name}' for re-application.", to_console=False)
                text = shim_block + text
                modified = True
            else:
                if any(s in text for s in [r"wdk_path': r''", r"sdk_path': r''", r"DetectVisualStudioPath():\n    return r''", r"# --- CerebrumLux injected shim START (v7.0) ---"]):
                    log("WARN", f"Outdated CerebrumLux shim content or old version marker detected in '{vs_toolchain_path.name}'. Re-applying full shim.", to_console=False)
                    text = re.sub(r"# --- CerebrumLux injected shim START \(v[\d\.]+\) ---[\s\S]*?# --- CerebrumLux injected shim END ---\n\n", "", text, flags=re.MULTILINE)
                    text = shim_block + text
                    modified = True

        func_patterns_to_remove = [
            r"^(def\s+DetectVisualStudioPath\s*\([^)]*\):(?:\n\s+.*)*?\n)(?=\n?^def|\Z)",
            r"^(def\s+GetVisualStudioVersion\s*\([^)]*\):(?:\n\s+.*)*?\n)(?=\n?^def|\Z)",
            r"^(def\s+SetEnvironmentAndGetRuntimeDllDirs\s*\([^)]*\):(?:\n\s+.*)*?\n)(?=\n?^def|\Z)",
        ]

        for pattern in func_patterns_to_remove:
            initial_func_replace_text = text
            text = re.sub(pattern, r"", text, flags=re.MULTILINE | re.DOTALL)
            if initial_func_replace_text != text:
                modified = True
                log("INFO", f"Removed original function body for pattern '{pattern[:min(len(pattern), 50)]}...' in '{vs_toolchain_path.name}'.", to_console=False)

        if "import pipes" in text and not ("# import pipes (replaced by CerebrumLux shim)" in text):
            text = text.replace("import pipes", "# import pipes (replaced by CerebrumLux shim)")
            modified = True
            log("INFO", f"Replaced 'import pipes' occurrences in '{vs_toolchain_path.name}'.", to_console=False)

        exception_pattern = r"(raise\s+Exception\s*\(\s*['\"]No supported Visual Studio can be found[\s\S]*?\)\s*)"
        if re.search(exception_pattern, text):
            text = re.sub(exception_pattern, "# CerebrumLux neutralized original exception: No supported Visual Studio can be found.", text)
            modified = True
            log("INFO", f"Neutralized explicit 'No supported Visual Studio can be found' exception text in '{vs_toolchain_path.name}'.", to_console=False)

        if modified:
            try:
                bak_path = vs_toolchain_path.with_suffix(vs_toolchain_path.suffix + ".cerebrumlux.bak")
                if not bak_path.exists() or original_text != text:
                    bak_path.write_bytes(original_text.encode("utf-8", errors="replace"))
                    log("DEBUG", f"Created backup of original '{vs_toolchain_path.name}' at '{bak_path.name}'.", to_console=False)
            except Exception as e:
                log("WARN", f"Could not write backup of '{vs_toolchain_path.name}': {e}", to_console=False)

            vs_toolchain_path.write_text(text, encoding="utf-8")
            log("INFO", f"'{vs_toolchain_path.name}' patched (shim-injected and originals deleted) successfully.", to_console=False)
            return True
        else:
            log("INFO", f"No changes required for '{vs_toolchain_path.name}'.", to_console=False)
            current_content = vs_toolchain_path.read_text(encoding="utf-8")
            if f"# --- CerebrumLux injected shim START (v7.36) ---" not in current_content: # Updated version check
                log("ERROR", f"'{vs_toolchain_path.name}' does not contain the CerebrumLux shim (v7.36) after expected patching. Patching is NOT sticking.", to_console=False)
                return False
            for pattern in func_patterns_to_remove:
                if re.search(pattern, current_content, flags=re.MULTILINE | re.DOTALL):
                    log("ERROR", f"'{vs_toolchain_path.name}' still contains original function definitions (pattern: {pattern[:min(len(pattern), 50)]}) despite patching. Patch is NOT sticking.", to_console=False)
                    return False
            if "import pipes" in current_content and not ("# import pipes (replaced by CerebrumLux shim)" in current_content):
                log("ERROR", f"'{vs_toolchain_path.name}' still contains 'import pipes' but was not replaced. Patching is NOT sticking.", to_console=False)
                return False
            if "No supported Visual Studio can be found" in current_content and not ("# CerebrumLux neutralized original exception" in current_content):
                log("ERROR", f"'{vs_toolchain_path.name}' contains VS detection exception but was not neutralized. Patching is NOT sticking.", to_console=False)
                return False
            if any(s in current_content for s in [r"wdk_path': r''", r"sdk_path': r''", r"DetectVisualStudioPath():\n    return r''"]):
                 log("ERROR", f"'{vs_toolchain_path.name}' shim contains empty paths (r''). Patching is NOT sticking (v7.36 content missing).", to_console=False) # Updated version check
                 return False
            
            return True

    except Exception as e:
        log("ERROR", f"Failed to apply aggressive patch logic to '{vs_toolchain_path.name}': {e}", to_console=True)
        return False

def _patch_dotfile_settings_gni(v8_source_dir: str, env: dict) -> bool:
    """
    Patches V8_SRC/build/dotfile_settings.gni to define 'exec_script_whitelist'
    within the 'build_dotfile_settings' scope.
    """
    dotfile_settings_path = Path(v8_source_dir) / "build" / "dotfile_settings.gni"
    if not dotfile_settings_path.exists():
        log("WARN", f"'{dotfile_settings_path.name}' not found at {dotfile_settings_path}. Skipping patch.", to_console=True)
        return False

    log("INFO", f"Patching '{dotfile_settings_path.name}' for 'exec_script_whitelist' compatibility.", to_console=True)
    try:
        content = dotfile_settings_path.read_text(encoding="utf-8")
        patched_content = content
        modified = False

        match = re.search(r"^(?P<indent>\s*)build_dotfile_settings\s*=\s*\{", patched_content, re.MULTILINE)
        if match:
            indent_level = match.group("indent")
            insert_point = match.end()
            
            scope_content_after_brace = patched_content[insert_point:]
            
            if "exec_script_whitelist" not in scope_content_after_brace:
                insert_text = f"\n{indent_level}  exec_script_whitelist = []"
                patched_content = patched_content[:insert_point] + insert_text + patched_content[insert_point:]
                modified = True
                log("INFO", "Inserted 'exec_script_whitelist = []' into 'build_dotfile_settings' scope.", to_console=True)
            else:
                log("INFO", "'exec_script_whitelist' already exists in 'build_dotfile_settings' scope. Skipping insertion.", to_console=False)
        else:
            log("WARN", "Could not find 'build_dotfile_settings = {' in 'dotfile_settings.gni'. Skipping patch.", to_console=True)
            return False

        if modified:
            patched_content = _filter_gn_comments(patched_content) # Apply general comment filter
            dotfile_settings_path.write_text(patched_content, encoding="utf-8")
            log("INFO", f"'{dotfile_settings_path.name}' patched successfully.", to_console=True)
            run(["git", "add", str(dotfile_settings_path)], cwd=v8_source_dir, env=env, check=False)
            log("INFO", f"Staged '{dotfile_settings_path.name}' changes with 'git add'.", to_console=True)
            return True
        else:
            log("INFO", f"'{dotfile_settings_path.name}' already patched or no changes needed.", to_console=False)
            run(["git", "add", str(dotfile_settings_path)], cwd=v8_source_dir, env=env, check=False)
            log("INFO", f"Ensured '{dotfile_settings_path.name}' is staged with 'git add'.", to_console=True)
            return True

    except Exception as e:
        log("ERROR", f"Failed to patch '{dotfile_settings_path.name}': {e}", to_console=True)
        return False

def _patch_visual_studio_version_gni(v8_source_dir: str, env: dict) -> bool:
    """
    Patches V8_SRC/build/config/win/visual_studio_version.gni to provide dummy values
    for visual_studio_path, visual_studio_version, and visual_studio_runtime_dirs,
    bypassing dynamic toolchain data fetching and associated errors.
    """
    vs_version_gni_path = Path(v8_source_dir) / "build" / "config" / "win" / "visual_studio_version.gni"
    if not vs_version_gni_path.exists():
        log("WARN", f"'{vs_version_gni_path.name}' not found at {vs_version_gni_path}. Skipping patch.", to_console=True)
        return False

    log("INFO", f"Patching '{vs_version_gni_path.name}' to bypass Visual Studio detection (direct assignment).", to_console=True)
    try:
        content = vs_version_gni_path.read_text(encoding="utf-8")
        patched_content = content
        modified = False

        # 1. Neutralize the import line for toolchain_data.gni
        import_toolchain_data_pattern = re.compile(r"^\s*import\s*\(\"//build/toolchain/win/toolchain_data\.gni\"\)\s*\n", re.MULTILINE)
        if import_toolchain_data_pattern.search(patched_content):
            patched_content = import_toolchain_data_pattern.sub(r"# CerebrumLux neutralized: \g<0>", patched_content)
            modified = True
            log("INFO", f"Neutralized 'import(\"//build/toolchain/win/toolchain_data.gni\")' in '{vs_version_gni_path.name}'.", to_console=False)
        
        # 2. Neutralize the 'exec_script' call that populates toolchain_data.
        exec_script_pattern = re.compile(
            r"^(?P<indent>\s*)(?:toolchain_data\s*=\s*)?exec_script\s*\(\"..\s*/../vs_toolchain\.py\"[\s\S]*?\)\s*\n",
            re.MULTILINE | re.DOTALL
        )
        if exec_script_pattern.search(patched_content):
            # FIX (v7.36): Escape captured group for safety before using in replacement
            patched_content = exec_script_pattern.sub(lambda m: m.group('indent') + "# CerebrumLux neutralized: " + m.group(0).strip().replace('\\', '/') + "\n", patched_content)
            modified = True
            log("INFO", f"Neutralized 'exec_script(\"../../vs_toolchain.py\"...)' call in '{vs_version_gni_path.name}'.", to_console=False)

        # 3. Find and replace *all* assignments to visual_studio_path, visual_studio_version, visual_studio_runtime_dirs
        assignments_to_patch = {
            "visual_studio_path": '"C:/FakeVS"',
            "visual_studio_version": '"16.0"',
            "visual_studio_runtime_dirs": '"C:/FakeVS/VC/Tools/MSVC/14.16.27023/bin/Hostx64/x64"',
            "windows_sdk_path": '"C:/FakeSDK"', # Added to ensure non-empty for consistency
            "wdk_path": '"C:/FakeWDK"' # Added to ensure non-empty for consistency
        }

        for var, dummy_value in assignments_to_patch.items():
            assignment_pattern = re.compile(rf"^(?P<indent>\s*){re.escape(var)}\s*=\s*.*$", re.MULTILINE)
            
            initial_var_content = patched_content
            while True:
                new_content_after_sub = assignment_pattern.sub(rf"\g<indent>{var} = {dummy_value} # CerebrumLux MinGW patch", patched_content)
                if new_content_after_sub == patched_content:
                    break
                patched_content = new_content_after_sub
                if initial_var_content != patched_content:
                    modified = True
                    log("INFO", f"Replaced assignment for '{var}' with dummy value in '{vs_version_gni_path.name}'.", to_console=False)
            
            if not re.search(rf"^\s*{re.escape(var)}\s*=\s*{re.escape(dummy_value)}", patched_content, re.MULTILINE) and \
               not re.search(rf"^\s*{re.escape(var)}\s*=\s*[\s\S]*?# CerebrumLux MinGW patch", patched_content, re.MULTILINE):
                declare_args_block_pattern = re.compile(r"(^\s*declare_args\s*\(\s*\)\s*\{\n)(?P<body_content>[\s\S]*?)(^\s*\}\s*$)", re.MULTILINE | re.DOTALL)
                match_declare_args = re.search(declare_args_block_pattern, patched_content)
                if match_declare_args and f"{var} =" not in match_declare_args.group('body_content'):
                    indent_level_declare_args = re.match(r"^(?P<indent>\s*)", match_declare_args.group(1), re.MULTILINE).group('indent')
                    insert_text = f"{indent_level_declare_args}  {var} = {dummy_value} # CerebrumLux MinGW injected default\n"
                    patched_content = patched_content[:match_declare_args.start('body_content')] + \
                                      insert_text + \
                                      patched_content[match_declare_args.start('body_content'):]
                    modified = True
                    log("INFO", f"Injected default assignment for '{var}' into 'declare_args()' in '{vs_version_gni_path.name}' as a fallback.", to_console=False)


        # --- Extra fallback patch for missing toolchain_data.vs_path (GN gen stage) ---
        toolchain_patch_pattern = re.compile(
            r"^\s*visual_studio_path\s*=\s*toolchain_data\.vs_path.*$",
            re.MULTILINE
        )
        if toolchain_patch_pattern.search(patched_content):
            patched_content = toolchain_patch_pattern.sub(
                'visual_studio_path = "C:/FakeVS" # CerebrumLux: bypass missing toolchain_data.vs_path',
                patched_content
            )
            modified = True
            log("INFO", f"Replaced toolchain_data.vs_path with dummy string assignment.", to_console=True)

        # --- Extra fallback patch for missing toolchain_data.sdk_path (GN gen stage) ---
        sdk_patch_pattern = re.compile(
            r"^\s*windows_sdk_path\s*=\s*toolchain_data\.sdk_path.*$",
            re.MULTILINE
        )
        if sdk_patch_pattern.search(patched_content):
            patched_content = sdk_patch_pattern.sub(
                'windows_sdk_path = "C:/FakeSDK" # CerebrumLux: bypass missing toolchain_data.sdk_path',
                patched_content
            )
            modified = True
            log("INFO", f"Replaced toolchain_data.sdk_path with dummy string assignment.", to_console=True)

        # --- Extra fallback patch for missing toolchain_data.wdk_dir (GN gen stage) ---
        wdk_patch_pattern = re.compile(
            r"^\s*wdk_path\s*=\s*toolchain_data\.wdk_dir.*$",
            re.MULTILINE
        )
        if wdk_patch_pattern.search(patched_content):
            patched_content = wdk_patch_pattern.sub(
                'wdk_path = "C:/FakeWDK" # CerebrumLux: bypass missing toolchain_data.wdk_dir',
                patched_content
            )
            modified = True
            log("INFO", f"Replaced toolchain_data.wdk_dir with dummy string assignment.", to_console=True)

        if modified:
            patched_content = _filter_gn_comments(patched_content) # Apply general comment filter
            vs_version_gni_path.write_text(patched_content, encoding="utf-8")
            log("INFO", f"'{vs_version_gni_path.name}' patched successfully.", to_console=True)
            run(["git", "add", str(vs_version_gni_path)], cwd=v8_source_dir, env=env, check=False)
            log("INFO", f"Staged '{vs_version_gni_path.name}' changes with 'git add'.", to_console=True)
            return True
        else:
            log("INFO", f"'{vs_version_gni_path.name}' already patched or no changes needed.", to_console=False)
            run(["git", "add", str(vs_version_gni_path)], cwd=v8_source_dir, env=env, check=False)
            log("INFO", f"Ensured '{vs_version_gni_path.name}' is staged with 'git add'.", to_console=True)
            return True

    except Exception as e:
        log("ERROR", f"Failed to patch '{vs_version_gni_path.name}': {e}", to_console=True)
        return False

def _patch_setup_toolchain_py(v8_source_dir: str, env: dict) -> bool:
    """
    Patches V8_SRC/build/toolchain/win/setup_toolchain.py to bypass
    calls to vs_toolchain.DetectVisualStudioPath, vs_toolchain.GetVisualStudioVersion,
    and _LoadToolchainEnv to return a dummy environment for MinGW.
    """
    setup_toolchain_path = Path(v8_source_dir) / "build" / "toolchain" / "win" / "setup_toolchain.py"
    if not setup_toolchain_path.exists():
        log("WARN", f"'{setup_toolchain_path.name}' not found at {setup_toolchain_path}. Skipping patch.", to_console=True)
        return False

    log("INFO", f"Patching '{setup_toolchain_path.name}' to completely replace _LoadToolchainEnv and create dummy paths (using .as_posix()).", to_console=True)
    try:
        content = setup_toolchain_path.read_text(encoding="utf-8")
        patched_content = content
        modified = False

        pattern_load_toolchain_env = re.compile(
            r"^(?P<func_def>def\s+_LoadToolchainEnv\([^)]*\):)(?P<body>(?:\n\s+.*)*?)(?=\n^def|\Z)", # Matches the entire function body
            re.MULTILINE | re.DOTALL
        )
        if pattern_load_toolchain_env.search(patched_content):
            fake_vs_root_for_py = Path(V8_ROOT) / "FakeVS_Toolchain"
            
            replacement_func_body = f"""def _LoadToolchainEnv(cpu, toolchain_root, win_sdk_path, target_store):
    # CerebrumLux MinGW patch: Bypassed vcvarsall.bat check and returning a dummy env.
    # The actual toolchain paths are provided in args.gn or directly configured by build_v8.py.
    # Dummy directories created by _create_fake_vs_toolchain_dirs in main().
    from pathlib import Path # Ensure Path is available within the injected function
    import os # Ensure os is available for checking/creating directories
    # Ensure dummy directories are created for the paths returned
    Path(r"{fake_vs_root_for_py.as_posix()}/VC/bin").mkdir(parents=True, exist_ok=True)
    Path(r"{fake_vs_root_for_py.as_posix()}/VC/lib").mkdir(parents=True, exist_ok=True)
    Path(r"{fake_vs_root_for_py.as_posix()}/VC/include").mkdir(parents=True, exist_ok=True)
    Path(r"{fake_vs_root_for_py.as_posix()}/SDK").mkdir(parents=True, exist_ok=True)
    Path(r"{fake_vs_root_for_py.as_posix()}/SDK/lib").mkdir(parents=True, exist_ok=True)
    Path(r"{fake_vs_root_for_py.as_posix()}/SDK/include").mkdir(parents=True, exist_ok=True)
    Path(r"{fake_vs_root_for_py.as_posix()}/redist").mkdir(parents=True, exist_ok=True)
    
    return {{
        "vc_bin_dir": (Path(r"{fake_vs_root_for_py.as_posix()}") / "VC" / "Tools" / "Bin" / "Hostx64" / "x64").as_posix(),
        "vc_lib_path": (Path(r"{fake_vs_root_for_py.as_posix()}") / "VC" / "lib").as_posix(),
        "vc_include_path": (Path(r"{fake_vs_root_for_py.as_posix()}") / "VC" / "include").as_posix(),
        "sdk_dir": (Path(r"{fake_vs_root_for_py.as_posix()}") / "SDK").as_posix(),
        "sdk_lib_path": (Path(r"{fake_vs_root_for_py.as_posix()}") / "SDK" / "lib").as_posix(),
        "sdk_include_path": (Path(r"{fake_vs_root_for_py.as_posix()}") / "SDK" / "include").as_posix(),
        "runtime_dirs": (Path(r"{fake_vs_root_for_py.as_posix()}") / "redist").as_posix()
    }}
"""
            patched_content = pattern_load_toolchain_env.sub(replacement_func_body, patched_content)
            modified = True
            log("INFO", f"Replaced '_LoadToolchainEnv' function body in '{setup_toolchain_path.name}' with full dummy environment (using .as_posix()).", to_console=False)
        else:
            # Fallback for older structures (should not be hit with current _LoadToolchainEnv replacement)
            # Patch _DetectVisualStudioPath
            pattern_detect_vs_path = re.compile(r"^(?P<indent>\s*)return\s+vs_toolchain\.DetectVisualStudioPath\(\)\s*$", re.MULTILINE)
            if pattern_detect_vs_path.search(patched_content):
                patched_content = pattern_detect_vs_path.sub(
                    lambda m: f"{m.group('indent')}return 'C:/FakeVS' # CerebrumLux MinGW patch", # Use / for consistency
                    patched_content
                )
                modified = True
                log("INFO", f"Patched '_DetectVisualStudioPath' call in '{setup_toolchain_path.name}' (fallback).", to_console=False)
            
            # Patch _GetVisualStudioVersion
            pattern_get_vs_version = re.compile(r"^(?P<indent>\s*)return\s+vs_toolchain\.GetVisualStudioVersion\(\)\s*$", re.MULTILINE)
            if pattern_get_vs_version.search(patched_content):
                patched_content = pattern_get_vs_version.sub(
                    lambda m: f"{m.group('indent')}return '16.0' # CerebrumLux MinGW patch",
                    patched_content
                )
                modified = True
                log("INFO", f"Patched '_GetVisualStudioVersion' call in '{setup_toolchain_path.name}' (fallback).", to_console=False)

        if modified:
            patched_content = _filter_gn_comments(patched_content) # Apply general comment filter
            try:
                bak_path = setup_toolchain_path.with_suffix(setup_toolchain_path.suffix + ".cerebrumlux.bak")
                if not bak_path.exists():
                    bak_path.write_bytes(content.encode("utf-8", errors="replace"))
                    log("DEBUG", f"Created backup of original '{setup_toolchain_path.name}' at '{bak_path.name}'.", to_console=False)
            except Exception as e:
                log("WARN", f"Could not write backup of '{setup_toolchain_path.name}': {e}", to_console=False)

            setup_toolchain_path.write_text(patched_content, encoding="utf-8")
            log("INFO", f"'{setup_toolchain_path.name}' patched successfully.", to_console=True)
            run(["git", "add", str(setup_toolchain_path)], cwd=v8_source_dir, env=env, check=False)
            log("INFO", f"Staged '{setup_toolchain_path.name}' changes with 'git add'.", to_console=True)
            return True
        else:
            log("INFO", f"'{setup_toolchain_path.name}' already patched or no changes needed.", to_console=False)
            run(["git", "add", str(setup_toolchain_path)], cwd=v8_source_dir, env=env, check=False)
            log("INFO", f"Ensured '{setup_toolchain_path.name}' is staged with 'git add'.", to_console=True)
            return True

    except Exception as e:
        log("ERROR", f"Failed to patch '{setup_toolchain_path.name}': {e}", to_console=True)
        return False

def _patch_build_gn(v8_source_dir: str, env: dict) -> bool:
    """
    Patches V8_SRC/build/config/win/BUILD.gn to aggressively neutralize the 'exec_script' call
    that populates vcvars_toolchain_data, and replaces ALL references to vcvars_toolchain_data members
    with hardcoded dummy paths. This removes the dependency on vcvars_toolchain_data from this file
    to prevent syntax errors like "Expecting assignment or function call. ]," (from v7.30 log).
    """
    build_gn_path = Path(v8_source_dir) / "build" / "config" / "win" / "BUILD.gn"
    if not build_gn_path.exists():
        log("WARN", f"'{build_gn_path.name}' not found at {build_gn_path}. Skipping patch.", to_console=True)
        return False

    log("INFO", f"Patching '{build_gn_path.name}' to aggressively neutralize 'exec_script' and replace ALL vcvars_toolchain_data accesses with dummy paths to fix syntax errors.", to_console=True)
    try:
        content = build_gn_path.read_text(encoding="utf-8")
        patched_content = content
        modified = False

        # --- 1. Neutralize the exec_script call for vcvars_toolchain_data ---
        exec_script_vcvars_pattern = re.compile(
            r"^(?P<indent>\s*)vcvars_toolchain_data\s*=\s*exec_script\(\s*\"../../toolchain/win/setup_toolchain\.py\"[\s\S]*?\)\s*\n",
            re.MULTILINE | re.DOTALL
        )
        if exec_script_vcvars_pattern.search(patched_content):
            # FIX (v7.37.1): Use lambda to correctly apply the backreference and comment out the original line
            patched_content = exec_script_vcvars_pattern.sub(
                lambda m: m.group('indent') + "# CerebrumLux neutralized: " + m.group(0).strip().replace('\\', '/') + "\n",
                patched_content
            )
            modified = True
            log("INFO", f"Neutralized 'exec_script' call for 'vcvars_toolchain_data' in '{build_gn_path.name}'.", to_console=False)
        else:
            log("INFO", f"No 'exec_script' call for 'vcvars_toolchain_data' found in '{build_gn_path.name}' or already neutralized. Skipping.", to_console=False)

        # --- 2. Aggressively replace ALL references to vcvars_toolchain_data.<field> with hardcoded dummy paths or 'true' ---
        fake_vs_base_path_for_gn_obj = Path(V8_ROOT) / "FakeVS_Toolchain"
        dummy_vcvars_paths = {
            "vc_lib_path": (fake_vs_base_path_for_gn_obj / "VC" / "lib").as_posix(),
            "vc_lib_atlmfc_path": (fake_vs_base_path_for_gn_obj / "VC" / "atlmfc" / "lib").as_posix(),
            "vc_lib_um_path": (fake_vs_base_path_for_gn_obj / "VC" / "um" / "lib").as_posix(),
            "vc_lib_ucrt_path": (fake_vs_base_path_for_gn_obj / "VC" / "ucrt" / "lib").as_posix(),
            "vc_bin_dir": (fake_vs_base_path_for_gn_obj / "VC" / "Tools" / "Bin" / "Hostx64" / "x64").as_posix(),
            "vc_include_path": (fake_vs_base_path_for_gn_obj / "VC" / "include").as_posix(),
            "sdk_dir": (fake_vs_base_path_for_gn_obj / "SDK").as_posix(),
            "sdk_lib_path": (fake_vs_base_path_for_gn_obj / "SDK" / "lib").as_posix(),
            "sdk_include_path": (fake_vs_base_path_for_gn_obj / "SDK" / "include").as_posix(),
            "runtime_dirs": (fake_vs_base_path_for_gn_obj / "redist").as_posix(),
        }

        # First, replace defined(vcvars_toolchain_data.<field>) with 'true'
        for field in dummy_vcvars_paths.keys():
            defined_pattern = re.compile(
                r"(?P<prefix>defined\(\s*vcvars_toolchain_data\." + re.escape(field) + r"\s*\))",
                re.MULTILINE
            )
            initial_defined_replace_text = patched_content
            # Replace defined() call with 'true'.
            replacement_str = r'true'
            log("DEBUG", f"Pattern: {defined_pattern.pattern}, Replacement: {replacement_str}", to_console=False)
            patched_content = defined_pattern.sub(replacement_str, patched_content)
            if initial_defined_replace_text != patched_content:
                modified = True
                log("INFO", f"Replaced 'defined(vcvars_toolchain_data.{field})' with 'true' in '{build_gn_path.name}'.", to_console=False)

        # Then, replace all other accesses/assignments to vcvars_toolchain_data.<field> with dummy paths
        # FIX (v7.36): Explicitly handle pre_assign and ensure dummy_path is quoted correctly.
        for field, dummy_path in dummy_vcvars_paths.items():
            access_pattern = re.compile(
                r"(?P<pre_assign>\b[a-zA-Z0-9_]+\s*=\s*)?(?P<vcvars_ref>vcvars_toolchain_data\." + re.escape(field) + r")",
                re.MULTILINE
            )
            initial_access_replace_text = patched_content

            def create_replacement_string_for_vcvars(m, current_dummy_path=dummy_path):
                pre_assign_part = m.group('pre_assign') or ''
                # Sanitize current_dummy_path for safe use in regex replacement string.
                sanitized_dummy_path = current_dummy_path.replace('\\', '/')
                return pre_assign_part + '"' + sanitized_dummy_path + '"'

            log("DEBUG", f"Pattern: {access_pattern.pattern}, Replacement Logic: create_replacement_string_for_vcvars", to_console=False)
            patched_content = access_pattern.sub(create_replacement_string_for_vcvars, patched_content)

            if initial_access_replace_text != patched_content:
                modified = True
                log("INFO", f"Replaced all direct accesses/assignments for 'vcvars_toolchain_data.{field}' with hardcoded dummy path in '{build_gn_path.name}'.", to_console=False)
        
        # --- Critical: Remove any remaining `vcvars_toolchain_data` object definitions that might cause syntax errors ---
        vcvars_data_object_pattern = re.compile(
            r"^(?P<indent>\s*)vcvars_toolchain_data\s*=\s*\{[\s\S]*?^\s*\}\s*$", # Matches the entire object definition, simplified closing brace match
            re.MULTILINE | re.DOTALL
        )
        if vcvars_data_object_pattern.search(patched_content):
            # FIX (v7.37.4): Corrected to replace with an empty string to remove the block entirely.
            initial_sub_content = patched_content
            patched_content = vcvars_data_object_pattern.sub("", patched_content)
            if initial_sub_content != patched_content:
                modified = True
            log("INFO", "Neutralized direct 'vcvars_toolchain_data' object definition in 'BUILD.gn' to prevent syntax errors.", to_console=False)

        # --- Aggressively strip any orphaned commas or square brackets that might cause syntax errors (e.g., from removing items from a list) ---
        # FIX (v7.37.7): Only target isolated commas, not closing brackets. Removing ']' or '}' is almost always incorrect.
        orphaned_punctuation_pattern = re.compile(r"^\s*,\s*$", re.MULTILINE) 
        initial_orphaned_content = patched_content
        replacement_str = r""
        log("DEBUG", f"Pattern: {orphaned_punctuation_pattern.pattern}, Replacement: {replacement_str}", to_console=False)
        patched_content = orphaned_punctuation_pattern.sub(replacement_str, patched_content)
        if initial_orphaned_content != patched_content:
            modified = True
            log("INFO", "Removed orphaned commas and square/curly brackets to prevent syntax errors.", to_console=False)


        if modified:
            patched_content = _filter_gn_comments(patched_content)
            try:
                bak_path = build_gn_path.with_suffix(build_gn_path.suffix + ".cerebrumlux.bak")
                if not bak_path.exists():
                    bak_path.write_bytes(content.encode("utf-8", errors="replace"))
                    log("DEBUG", f"Created backup of original '{build_gn_path.name}' at '{bak_path.name}'.", to_console=False)
            except Exception as e:
                log("WARN", f"Could not write backup of '{build_gn_path.name}': {e}", to_console=False)

            build_gn_path.write_text(patched_content, encoding="utf-8")
            log("INFO", f"'{build_gn_path.name}' patched successfully.", to_console=True)
            run(["git", "add", str(build_gn_path)], cwd=v8_source_dir, env=env, check=False)
            log("INFO", f"Staged '{build_gn_path.name}' changes with 'git add'.", to_console=True)
            return True
        else:
            log("INFO", f"'{build_gn_path.name}' already patched or no changes needed.", to_console=False)
            run(["git", "add", str(build_gn_path)], cwd=v8_source_dir, env=env, check=False)
            log("INFO", f"Ensured '{build_gn_path.name}' is staged with 'git add'.", to_console=True)
            return True

    except Exception as e:
        log("ERROR", f"Failed to patch '{build_gn_path.name}': {e}", to_console=True)
        return False


def _patch_toolchain_win_build_gn(v8_source_dir: str, env: dict) -> bool:
    """
    Patches V8_SRC/build/toolchain/win/BUILD.gn to neutralize the 'exec_script' call
    that populates win_toolchain_data, ensures tool definitions are set for MinGW,
    and reliably defines sys_lib_flags/sys_include_flags right before msvc_toolchain() definitions,
    and also neutralizes the problematic 'prefix' assignment.
    The core win_toolchain_data object itself will be injected via args.gn.
    """
    toolchain_build_gn_path = Path(v8_source_dir) / "build" / "toolchain" / "win" / "BUILD.gn"
    if not toolchain_build_gn_path.exists():
        log("WARN", f"'{toolchain_build_gn_path.name}' not found at {toolchain_build_gn_path}. Skipping patch.", to_console=True)
        return False

    log("INFO", f"Patching '{toolchain_build_gn_path.name}' to neutralize 'exec_script', handle tool definitions/flags, define sys_flags, and neutralize 'prefix'. win_toolchain_data via args.gn.", to_console=True)
    try:
        content = toolchain_build_gn_path.read_text(encoding="utf-8")
        patched_content = content
        modified = False

        fake_vs_base_path_obj = Path(V8_ROOT) / "FakeVS_Toolchain"

        # FIX (v7.37.9): Workaround for "May only subscript identifiers. invoker.toolchain_arch"
        # Add a local _invoker_scope = invoker inside the msvc_toolchain template definition.
        invoker_patch_pattern = re.compile(
            r"^(?P<indent>\s*)(?:toolchain_arch\s*=\s*)?invoker\.toolchain_arch",
            re.MULTILINE
        )
        if invoker_patch_pattern.search(patched_content):
            # Find the template definition block to ensure we insert inside it
            template_start_pattern = re.compile(r"^(?P<indent_tmpl>\s*)template\s*\(\s*\"msvc_toolchain\"\s*\)\s*\{", re.MULTILINE)
            match_template = template_start_pattern.search(patched_content)
            if match_template:
                insert_point = match_template.end()
                indent_level_tmpl = match_template.group('indent_tmpl')
                # Inject the _invoker_scope definition right after the template opening brace
                invoker_injection_text = f"\n{indent_level_tmpl}  # CerebrumLux: Workaround for GN \"May only subscript identifiers\"\n{indent_level_tmpl}  _invoker_local = invoker\n"
                patched_content = patched_content[:insert_point] + invoker_injection_text + patched_content[insert_point:]
                modified = True
                log("INFO", "Injected '_invoker_local = invoker' into 'msvc_toolchain' template.", to_console=False)

            # Now replace all instances of invoker.toolchain_arch with _invoker_local.toolchain_arch
            patched_content = invoker_patch_pattern.sub(
                lambda m: m.group('indent') + ("_invoker_local.toolchain_arch" if not m.group(0).strip().startswith("invoker =") else m.group(0)),
                patched_content # Careful not to modify "invoker = invoker" lines if they exist, only member access
            )
            # Re-process for assignments that might have been skipped if pre_assign was present
            patched_content = re.sub(
                r"^(?P<pre_assign>\s*toolchain_arch\s*=\s*)invoker\.toolchain_arch",
                r"\g<pre_assign>_invoker_local.toolchain_arch",
                patched_content, flags=re.MULTILINE
            )
            modified = True
            log("INFO", f"Replaced 'invoker.toolchain_arch' with '_invoker_local.toolchain_arch' in '{toolchain_build_gn_path.name}'.", to_console=False)

        dummy_win_toolchain_paths = {
            "vc_bin_dir": (fake_vs_base_path_obj / "VC" / "Tools" / "Bin" / "Hostx64" / "x64").as_posix(),
            "vc_lib_path": (fake_vs_base_path_obj / "VC" / "lib").as_posix(),
            "vc_include_path": (fake_vs_base_path_obj / "VC" / "include").as_posix(),
            "sdk_dir": (fake_vs_base_path_obj / "SDK").as_posix(),
            "sdk_lib_path": (fake_vs_base_path_obj / "SDK" / "lib").as_posix(),
            "sdk_include_path": (fake_vs_base_path_obj / "SDK" / "include").as_posix(),
            "runtime_dirs": (fake_vs_base_path_obj / "redist").as_posix(),
            "include_flags_imsvc": "",
        }
        
        # --- 1. Neutralize the exec_script call for win_toolchain_data ---
        exec_script_win_toolchain_pattern = re.compile(
            r"^(?P<indent>\s*)win_toolchain_data\s*=\s*exec_script\(\"setup_toolchain\.py\"[\s\S]*?\)\s*\n",
            re.MULTILINE | re.DOTALL
        )
        if exec_script_win_toolchain_pattern.search(patched_content):
            # FIX (v7.36): Escape captured group for safety before using in replacement
            patched_content = exec_script_win_toolchain_pattern.sub(lambda m: m.group('indent') + "# CerebrumLux neutralized: " + m.group(0).strip().replace('\\', '/') + "\n", patched_content)
            modified = True
            log("INFO", f"Neutralized 'exec_script' call for 'win_toolchain_data' in '{toolchain_build_gn_path.name}'.", to_console=False)

        # --- 2. Remove any old injected direct 'win_toolchain_data' definition (CRITICAL for this fix) ---
        win_toolchain_data_block_marker = "# CerebrumLux Injected win_toolchain_data Block"
        old_injected_block_pattern = re.compile(
            r"^(?P<indent>\s*)# CerebrumLux Injected win_toolchain_data Block[\s\S]*?(?P=indent)\}\s*\n",
            re.MULTILINE | re.DOTALL
        )
        if old_injected_block_pattern.search(patched_content):
            patched_content = old_injected_block_pattern.sub("", patched_content)
            modified = True
            log("INFO", f"Removed old injected 'win_toolchain_data' definition from '{toolchain_build_gn_path.name}'.", to_console=False)

        # --- 3. Remove existing (problematic) assignments for sys_include_flags and sys_lib_flags from the original file ---
        flags_assignment_removal_pattern = re.compile(
            r"^(?P<indent>\s*)(sys_include_flags|sys_lib_flags)\s*=\s*.*?$",
            re.MULTILINE
        )
        initial_flags_content_before_removal = patched_content
        patched_content = flags_assignment_removal_pattern.sub(r'', patched_content) # Remove the line entirely
        if initial_flags_content_before_removal != patched_content:
            modified = True
            log("INFO", "Removed existing direct assignments for 'sys_include_flags' and 'sys_lib_flags' from 'BUILD.gn'.", to_console=False)


        # --- 4. Inject sys_include_flags and sys_lib_flags right before the msvc_toolchain() definitions ---
        msvc_toolchain_template_pattern = re.compile(
            r"^(?P<indent>\s*)template\s*\(\s*\"msvc_toolchain\"\s*\)\s*\{",
            re.MULTILINE
        )
        match_msvc_toolchain = msvc_toolchain_template_pattern.search(patched_content)
        
        if match_msvc_toolchain:
            insert_point = match_msvc_toolchain.start()
            indent_level = match_msvc_toolchain.group('indent')

            new_flags_injection = (
                f"\n{indent_level}# CerebrumLux injected for MinGW compatibility\n"
                f"{indent_level}sys_include_flags = []\n"
                f"{indent_level}sys_lib_flags = []\n"
            )

            if f"{indent_level}sys_include_flags = []" not in patched_content[insert_point:match_msvc_toolchain.end()] and \
               f"{indent_level}sys_lib_flags = []" not in patched_content[insert_point:match_msvc_toolchain.end()]:
                
                patched_content = patched_content[:insert_point] + new_flags_injection + patched_content[insert_point:]
                modified = True
                log("INFO", f"Injected 'sys_include_flags' and 'sys_lib_flags' before 'msvc_toolchain' template in '{toolchain_build_gn_path.name}'.", to_console=False)
            else:
                log("INFO", "'sys_include_flags' and 'sys_lib_flags' already present before 'msvc_toolchain' template. Skipping injection.", to_console=False)
        else:
            log("WARN", "Could not find 'template(\"msvc_toolchain\") {' pattern in 'BUILD.gn'. Cannot inject sys_flags before it.", to_console=True)
            # Fallback to appending at the end if msvc_toolchain template is not found (less ideal but prevents "Undefined identifier")
            if not re.search(r"sys_include_flags\s*=\s*\[\]\s*# CerebrumLux injected", patched_content) and \
               not re.search(r"sys_lib_flags\s*=\s*\[\]\s*# CerebrumLux injected", patched_content):
                
                fallback_flags_injection = (
                    "\n\n# CerebrumLux injected as fallback for MinGW compatibility\n"
                    "sys_include_flags = []\n"
                    "sys_lib_flags = []\n"
                )
                patched_content = patched_content.rstrip() + "\n" + fallback_flags_injection.strip() + "\n"
                modified = True
                log("INFO", "Injected 'sys_include_flags' and 'sys_lib_flags' at the end of 'BUILD.gn' as fallback.", to_console=False)


        # --- 5. Neutralize the problematic 'prefix' assignment to prevent "Assignment had no effect" error ---
        prefix_assignment_pattern = re.compile(
            r"^(?P<indent>\s*)prefix\s*=\s*rebase_path\(\"\$clang_base_path/bin\"[^\)]*\)\s*$",
            re.MULTILINE
        )
        initial_prefix_content = patched_content
        if prefix_assignment_pattern.search(patched_content):
            patched_content = prefix_assignment_pattern.sub(lambda m: m.group('indent') + "# [CerebrumLux-MinGW] Commented out redundant clang prefix to avoid GN fatal error", patched_content)
            modified = True
            log("INFO", "'prefix' assignment neutralized to prevent 'Assignment had no effect' error.", to_console=False)
        else:
            log("INFO", "No 'prefix = rebase_path(...clang_base_path...)' assignment found in 'BUILD.gn' or already neutralized. Skipping.", to_console=False)


        # --- 6. Replace MSVC tool definitions with MinGW tools (as direct strings) ---
        mingw_bin_posix = Path(MINGW_BIN).as_posix()
        
        tool_definitions_to_patch = {
            r'^\s*cl\s*=\s*".*?"': f'cl = "{mingw_bin_posix}/gcc.exe"',
            r'^\s*link\s*=\s*".*?"': f'link = "{mingw_bin_posix}/g++.exe"',
            r'^\s*lib\s*=\s*".*?"': f'lib = "{mingw_bin_posix}/ar.exe"',
            r'^\s*rc\s*=\s*".*?"': f'rc = "{mingw_bin_posix}/windres.exe"', 
        }
        
        for pattern_str, replacement_str in tool_definitions_to_patch.items():
            tool_assignment_pattern = re.compile(pattern_str, re.MULTILINE)
            initial_tool_content = patched_content
            patched_content = tool_assignment_pattern.sub(r'  ' + replacement_str + ' # CerebrumLux MinGW tool override', patched_content)
            if initial_tool_content != patched_content:
                modified = True
                log("INFO", f"Replaced tool assignment (pattern: {pattern_str[:min(len(pattern_str), 50)]}...) with MinGW path in '{toolchain_build_gn_path.name}'.", to_console=False)
        
        # --- 7. Generic replacement for any unhandled win_toolchain_data.<field> access ---
        for field, dummy_path in dummy_win_toolchain_paths.items():
            generic_access_pattern = re.compile(r"win_toolchain_data\." + re.escape(field), re.MULTILINE)
            initial_generic_replace_text = patched_content
            patched_content = generic_access_pattern.sub(f'"{dummy_path}"', patched_content)
            if initial_generic_replace_text != patched_content:
                modified = True
                log("INFO", f"Replaced generic access to 'win_toolchain_data.{field}' with hardcoded dummy path in '{toolchain_build_gn_path.name}' (final fallback).", to_console=False)

        if modified:
            patched_content = _filter_gn_comments(patched_content)
            try:
                bak_path = toolchain_build_gn_path.with_suffix(toolchain_build_gn_path.suffix + ".cerebrumlux.bak")
                if not bak_path.exists():
                    bak_path.write_bytes(content.encode("utf-8", errors="replace"))
                    log("DEBUG", f"Created backup of original '{toolchain_build_gn_path.name}' at '{bak_path.name}'.", to_console=False)
            except Exception as e:
                log("WARN", f"Could not write backup of '{toolchain_build_gn_path.name}': {e}", to_console=False)

            toolchain_build_gn_path.write_text(patched_content, encoding="utf-8")
            log("INFO", f"'{toolchain_build_gn_path.name}' patched successfully.", to_console=True)
            run(["git", "add", str(toolchain_build_gn_path)], cwd=v8_source_dir, env=env, check=False)
            log("INFO", f"Ensured '{toolchain_build_gn_path.name}' is staged with 'git add'.", to_console=True)
            return True
        else:
            log("INFO", f"'{toolchain_build_gn_path.name}' already patched or no changes needed.", to_console=False)
            run(["git", "add", str(toolchain_build_gn_path)], cwd=v8_source_dir, env=env, check=False)
            log("INFO", f"Ensured '{toolchain_build_gn_path.name}' is staged with 'git add'.", to_console=True)
            return True

    except Exception as e:
        log("ERROR", f"Failed to patch '{toolchain_build_gn_path.name}': {e}", to_console=True)
        return False


def normalize_gn_lists(file_path: Path):
    """
    Ensures correct GN list syntax, specifically adding missing commas between
    string elements and after string elements that are followed by comments.
    This prevents "Expected comma between items" errors.
    # FIX (v7.37.7): Removed logic to add commas before 'if' statements, as they are usually outside lists.
    """
    # FIX (v7.37.8): Reinstated the 'if' comma handling as it proved to be essential.
    # It's important to keep this patch active for lists like `cflags = [ "flag", if (condition) { ... } ]`.
    # The GN parser can interpret the 'if' block itself as an item in the list, requiring a preceding comma.
    # This was the core issue for "Expected comma between items" when 'if' statements follow list items.
    # The regex is `(?m)^(\s*"[^"]+"(?:\\s*#.*)?)\n(?=\s*if\s*\()` and it adds `,\n` before the `if`.
    # This particular pattern is tricky because of the interaction between Python's regex engine
    # and the raw string literal `r"""..."""`. Ensuring `\\s*#.*` for comments is correct.
    # The `\\g` in the docstring caused issues; direct use of `r` prefix for the overall docstring
    # and explicitly escaping backslashes within the regex is key.
    log("INFO", f"Normalizing GN list syntax in {file_path.name} to add missing commas.", to_console=False)
    text = file_path.read_text(encoding="utf-8")
    original_text = text

    # 1. Add comma between a quoted string and a subsequent quoted string on a new line
    # Example: "item1"\n"item2"  -> "item1",\n"item2"
    text = re.sub(
        r'(?m)^(\s*"[^"]+")\n(?=\s*"[^"]+")',
        r'\1,\n',
        text
    )

    # 2. Add comma between a quoted string ending with a comment and a subsequent quoted string on a new line
    # Example: "item1" # comment\n"item2" -> "item1", # comment\n"item2"
    text = re.sub(
        r'(?m)^(\s*"[^"]+"\s*#.*)\n(?=\s*"[^"]+")',
        r'\1,\n',
            text
        )

    # FIX (v7.37.8): This pattern was removed in v7.37.7 but is CRITICAL for 'if' statements within GN lists. Re-adding.
    text = re.sub(
        r'(?m)^(\s*"[^"]+"(?:\\s*#.*)?)\n(?=\s*if\s*\()', # Match quoted string + optional comment, lookahead for 'if'
        r'\1,\n', # Add comma before the 'if' line
        text
    )

    # FIX (v7.37.8): Reverted the removal of this critical patch.
    # 3. Add comma after a quoted string (optionally with a comment) that is followed by an 'if' statement on a new line
    # This is crucial for fixing the "Expected comma between items" error when 'if' statements appear directly after list items.
    text = re.sub(
        r'(?m)^(\s*"[^"]+"(?:\\s*#.*)?)\n(?=\s*if\s*\()', # Match the quoted string and optional comment, then lookahead for 'if'
        r'\1,\n',
        text
         )

    if original_text != text:
        file_path.write_text(text, encoding="utf-8")
        log("INFO", f"GN list syntax normalized in {file_path.name} successfully.", to_console=False)
        # No need to git add here, as the patching function will handle staging.
        return True
    else:
        log("INFO", f"No GN list syntax normalization needed for {file_path.name}.", to_console=False)
        return False


def _create_fake_vs_toolchain_dirs(v8_root_dir: str):
    """
    Creates dummy directories under V8_ROOT/FakeVS_Toolchain that GN
    files might reference for existence checks.
    """
    fake_vs_base_path = Path(v8_root_dir) / "FakeVS_Toolchain"
    
    # Core VS paths
    os.makedirs(fake_vs_base_path / "VC" / "bin", exist_ok=True)
    os.makedirs(fake_vs_base_path / "VC" / "lib", exist_ok=True)
    os.makedirs(fake_vs_base_path / "VC" / "include", exist_ok=True)
    
    # SDK paths
    os.makedirs(fake_vs_base_path / "SDK", exist_ok=True)
    os.makedirs(fake_vs_base_path / "SDK" / "lib", exist_ok=True)
    os.makedirs(fake_vs_base_path / "SDK" / "include", exist_ok=True)

    # Runtime and specific library paths referenced by GN
    os.makedirs(fake_vs_base_path / "redist", exist_ok=True)
    os.makedirs(fake_vs_base_path / "VC" / "Tools" / "Bin" / "Hostx64" / "x64", exist_ok=True) # For vc_bin_dir full path
    os.makedirs(fake_vs_base_path / "VC" / "atlmfc" / "lib", exist_ok=True) # For vc_lib_atlmfc_path
    os.makedirs(fake_vs_base_path / "VC" / "um" / "lib", exist_ok=True) # For vc_lib_um_path
    os.makedirs(fake_vs_base_path / "VC" / "ucrt" / "lib", exist_ok=True) # For vc_lib_ucrt_path
    
    log("DEBUG", f"Ensured all dummy Visual Studio toolchain directories exist under {fake_vs_base_path.as_posix()}.", to_console=False)

def _filter_gn_comments(content: str) -> str:
    """
    Filters GN file content to replace C-style comments (/* ... */) with #-style comments
    and ensure only # is used for line comments.
    """
    # Remove block comments /* ... */
    content = re.sub(r"/\*[\s\S]*?\*/", "", content)
    
    # Replace // line comments with #
    content = re.sub(r"^\s*//", "#", content, flags=re.MULTILINE)

    return content


def _clean_up_list_terminators(file_path: Path):
    """
    Aggressively removes blank lines or lines containing only comments immediately
    preceding a list or scope closing bracket (']' or '}'). This helps fix
    "Expecting assignment or function call" errors on closing brackets.
    """
    log("INFO", f"Cleaning up list terminators in {file_path.name}.", to_console=False)
    text = file_path.read_text(encoding="utf-8")
    original_text = text

    # Pattern to find blank lines or lines with only comments immediately before a closing bracket
    # Uses a negative lookahead to ensure we don't accidentally remove actual code.
    # Handles ']' and '}' as closing delimiters.
    pattern = re.compile(
        r"(?m)"  # Multi-line mode
        r"^\s*(?:#.*)?\n"  # Match blank line or line with only a comment
        r"(?=\s*[\}\]])"   # Positive lookahead for a closing bracket on the next line
    )
    
    cleaned_content = pattern.sub("", text)

    if original_text != cleaned_content:
        file_path.write_text(cleaned_content, encoding="utf-8")
        log("INFO", f"Cleaned up list terminators in {file_path.name} successfully.", to_console=False)
        # No need to git add here, as the calling function will handle staging.
        return True
    else:
        log("INFO", f"No list terminator cleanup needed for {file_path.name}.", to_console=False)
        return False
    

def patch_v8_deps_for_mingw(v8_source_dir: str, env: dict):
    """
    Patches the DEPS file to remove problematic dependencies for MinGW build.
    Also calls to patch all relevant .gni and .gn files.
    """
    deps_path = Path(v8_source_dir) / "DEPS" # Use Path
    if not deps_path.exists():
        log("WARN", f"DEPS file not found at {deps_path}. Skipping DEPS patch.", to_console=True)
        return

    log("INFO", f"Patching DEPS file at {deps_path} for MinGW compatibility.", to_console=True)
    
    content = deps_path.read_text(encoding='utf-8') # Use Path.read_text
    patched_content = content
    deps_modified = False
    
    log("INFO", "Removing 'buildtools/win' from DEPS.", to_console=False)
    if re.search(r"\'buildtools/win\':\s*Var\(.*?\),?\n?", patched_content, flags=re.DOTALL) or \
       re.search(r"\'buildtools/win\':\s*\'[^\n]*\',?\n?", patched_content, flags=re.DOTALL):
        patched_content = re.sub(r"\'buildtools/win\':\s*Var\(.*?\),?\n?", "", patched_content, flags=re.DOTALL)
        patched_content = re.sub(r"\'buildtools/win\':\s*\'[^\n]*\',?\n?", "", patched_content, flags=re.DOTALL)
        deps_modified = True

    log("INFO", "Removing 'third_party/llvm-build' from DEPS.", to_console=False)
    # FIX (v7.36): Refined regex to avoid 'multiple repeat' error. Use non-greedy and explicit match.
    # The original regex `Var\(.*?\),?` combined with `flags=re.DOTALL` could cause issues.
    # We explicitly look for a single-line string literal, or a Var() call.
    llvm_pattern_str = r"\'third_party/llvm-build\':\s*(?:Var\([^\)]*\)|'[^\n]*'),?\n?"
    llvm_pattern = re.compile(llvm_pattern_str, flags=re.MULTILINE) # DOTALL removed as not needed for single line.
    
    if llvm_pattern.search(patched_content):
        log("DEBUG", f"Found llvm-build pattern: {llvm_pattern_str}", to_console=False)
        patched_content = llvm_pattern.sub("", patched_content)
        deps_modified = True
    else:
        log("DEBUG", f"No llvm-build pattern found in DEPS: {llvm_pattern_str}", to_console=False)


    log("INFO", "Removing 'tools/win' from DEPS.", to_console=False)
    if re.search(r"['\"]tools/win['\"]\s*:\s*['\"][^'\"]*['\"],?\n?", patched_content):
        patched_content = re.sub(r"['\"]tools/win['\"]\s*:\s*['\"][^'\"]*['\"],?\n?", "", patched_content)
        deps_modified = True
    
    log("INFO", "Removing 'tools/clang' from DEPS.", to_console=False)
    if re.search(r"['\"]tools/clang['\"]\s*:\s*['\"][^'\"]*['\"],?\n?", patched_content):
        patched_content = re.sub(r"['\"]tools/clang['\"]\s*:\s*['\"][^'\"]*['\"],?\n?", "", patched_content)
        deps_modified = True

    log("INFO", "Removing problematic cipd packages from DEPS.", to_console=False)
    initial_cipd_content = patched_content
    # FIX (v7.36): Ensure non-greedy match to avoid "multiple repeat"
    cipd_pattern = re.compile(r"\'infra/tools/win\S*?\'[^}]*?},\n", flags=re.MULTILINE)
    if cipd_pattern.search(patched_content):
        log("DEBUG", f"Found cipd pattern: {cipd_pattern.pattern}", to_console=False)
        patched_content = cipd_pattern.sub("", patched_content)
        deps_modified = True
    else:
        log("DEBUG", f"No cipd pattern found in DEPS: {cipd_pattern.pattern}", to_console=False)


    log("INFO", "Replaced 'simdutf' source with GitHub mirror in DEPS.", to_console=True)
    if "https://chromium.googlesource.com/chromium/src/third_party/simdutf" in patched_content:
        patched_content = patched_content.replace(
            "https://chromium.googlesource.com/chromium/src/third_party/simdutf",
            "https://github.com/simdutf/simdutf.git"
        )
        deps_modified = True

    log("INFO", "Replaced 'zlib' source with GitHub mirror in DEPS.", to_console=True)
    if "https://chromium.googlesource.com/chromium/src/third_party/zlib.git" in patched_content:
        patched_content = patched_content.replace(
            "https://chromium.googlesource.com/chromium/src/third_party/zlib.git",
            "https://github.com/madler/zlib.git"
        )
        deps_modified = True

    if deps_modified:
        deps_path.write_text(patched_content, encoding="utf-8") # Use Path.write_text
        log("INFO", f"DEPS file patched successfully to remove problematic MinGW dependencies and apply mirrors.", to_console=True)
    else:
        log("INFO", f"DEPS file already patched or no problematic dependencies found.", to_console=True)

    log("INFO", "Calling patch for 'build/dotfile_settings.gni'.", to_console=True)
    if not _patch_dotfile_settings_gni(v8_source_dir, env):
        log("FATAL", "Failed to patch 'build/dotfile_settings.gni'. Aborting.", to_console=True)
        sys.exit(1)
    
    log("INFO", "Calling patch for 'build/config/win/visual_studio_version.gni'.", to_console=True)
    if not _patch_visual_studio_version_gni(v8_source_dir, env):
        log("FATAL", "Failed to patch 'build/config/win/visual_studio_version.gni'. Aborting.", to_console=True)
        sys.exit(1)

    # NEW: Call to patch setup_toolchain.py
    log("INFO", "Calling patch for 'build/toolchain/win/setup_toolchain.py'.", to_console=True)
    if not _patch_setup_toolchain_py(v8_source_dir, env):
        log("FATAL", "Failed to patch 'build/toolchain/win/setup_toolchain.py'. Aborting.", to_console=True)
        sys.exit(1)
    
    # NEW: Call to patch build/config/win/BUILD.gn
    log("INFO", "Calling patch for 'build/config/win/BUILD.gn'.", to_console=True)
    if not _patch_build_gn(v8_source_dir, env):
        log("FATAL", "Failed to patch 'build/config/win/BUILD.gn'. Aborting.", to_console=True)
        sys.exit(1)
    # FIX (v7.37.4): Normalize GN list syntax after patching BUILD.gn
    # FIX (v7.37.9): Apply _clean_up_list_terminators after normalization.
    build_config_win_build_gn_path = Path(v8_source_dir) / "build" / "config" / "win" / "BUILD.gn"
    # Run cleanup first, then normalization, as cleanup might affect lines where commas are needed.
    # No, it's safer to normalize, then cleanup any *newly created* empty lines.
    if _clean_up_list_terminators(build_config_win_build_gn_path):
        run(["git", "add", str(build_config_win_build_gn_path)], cwd=v8_source_dir, env=env, check=False)
        log("INFO", f"Staged '{build_config_win_build_gn_path.name}' changes with 'git add' after list terminator cleanup.", to_console=True)

    if normalize_gn_lists(build_config_win_build_gn_path):
        run(["git", "add", str(build_config_win_build_gn_path)], cwd=v8_source_dir, env=env, check=False)
        log("INFO", f"Staged '{build_config_win_build_gn_path.name}' changes with 'git add' after GN list normalization.", to_console=True)
    else:
        # Ensure git add is still called even if no changes, to ensure it's staged
        run(["git", "add", str(build_config_win_build_gn_path)], cwd=v8_source_dir, env=env, check=False)

    # NEW: Call to patch build/toolchain/win/BUILD.gn
    log("INFO", "Calling patch for 'build/toolchain/win/BUILD.gn'.", to_console=True)
    if not _patch_toolchain_win_build_gn(v8_source_dir, env):
        log("FATAL", "Failed to patch 'build/toolchain/win/BUILD.gn'. Aborting.", to_console=True)
        sys.exit(1)
    
    # FIX (v7.37.5): Apply normalization to build/toolchain/win/BUILD.gn as well.
    # FIX (v7.37.9): Apply _clean_up_list_terminators after normalization.
    toolchain_build_gn_path = Path(v8_source_dir) / "build" / "toolchain" / "win" / "BUILD.gn"
    if _clean_up_list_terminators(toolchain_build_gn_path):
        run(["git", "add", str(toolchain_build_gn_path)], cwd=v8_source_dir, env=env, check=False)
        log("INFO", f"Staged '{toolchain_build_gn_path.name}' changes with 'git add' after list terminator cleanup.", to_console=True)
    toolchain_build_gn_path = Path(v8_source_dir) / "build" / "toolchain" / "win" / "BUILD.gn"

    if normalize_gn_lists(toolchain_build_gn_path):
        run(["git", "add", str(toolchain_build_gn_path)], cwd=v8_source_dir, env=env, check=False)
        log("INFO", f"Staged '{toolchain_build_gn_path.name}' changes with 'git add' after GN list normalization.", to_console=True)
    else:
        # Ensure git add is still called even if no changes, to ensure it's staged
        run(["git", "add", str(toolchain_build_gn_path)], cwd=v8_source_dir, env=env, check=False)

def gclient_sync_with_retry(env: dict, root_dir: str, v8_src_dir: str, retries: int = MAX_GCLIENT_RETRIES):
    """Runs gclient sync with retries and error handling, aggressively patching vs_toolchain.py before each attempt and after if needed."""
    gclient_py_path = Path(DEPOT_TOOLS) / "gclient.py"
    # Check if gclient is in PATH as gclient.bat or gclient
    gclient_to_use = []
    if not gclient_py_path.exists():
        gclient_cmd_in_path = shutil.which("gclient") or shutil.which("gclient.bat")
        if gclient_cmd_in_path:
            log("INFO", f"Found gclient in PATH: {gclient_cmd_in_path}", to_console=False)
            gclient_to_use = [str(gclient_cmd_in_path)]
        else:
            raise RuntimeError(f"gclient.py not found at {gclient_py_path} nor in system PATH. Ensure depot_tools is correctly cloned and configured.")
    else:
        # If gclient.py exists directly, we'll use sys.executable to run it.
        gclient_to_use = [sys.executable, str(gclient_py_path)]
    
    vs_toolchain_path = Path(v8_src_dir) / "build" / "vs_toolchain.py"

    cmd_base = gclient_to_use + ["sync", "-D", "--with_branch_heads", "--with_tags", "--force"]
    
    for attempt in range(1, retries + 1):
        try:
            log("INFO", f"gclient sync attempt {attempt}/{retries}.")
            
            patch_tries = 0
            MAX_PATCH_LOOP_TRIES_INNER = 5 # User suggested 5 retries for patching loop
            
            while True:
                current_vs_toolchain_exists = vs_toolchain_path.exists()
                if not current_vs_toolchain_exists:
                    log("DEBUG", f"'{vs_toolchain_path.name}' does not exist yet. Cannot apply pre-sync patch. Continuing...", to_console=False)
                    break

                if patch_tries >= MAX_PATCH_LOOP_TRIES_INNER:
                    log("FATAL", f"'{vs_toolchain_path.name}' still contains problematic VS detection logic or missing shim after {MAX_PATCH_LOOP_TRIES_INNER} pre-sync patch attempts. Aborting.", to_console=True)
                    sys.exit(1)
                
                content_before_patch = ""
                if vs_toolchain_path.exists():
                    content_before_patch = vs_toolchain_path.read_text(encoding='utf-8')

                # Combined check for critical strings (pipes, VS exception) and v7.36 shim content
                if f"# --- CerebrumLux injected shim START (v7.36) ---" not in content_before_patch:
                    needs_patch = True
                else:
                    needs_patch = False # Assume patched if latest shim marker is present

                if not needs_patch:
                    log("INFO", f"'{vs_toolchain_path.name}' does not contain critical strings and shim (v7.36) is present and correct. Pre-sync patch skipped (already fine).", to_console=False)
                    break

                log("INFO", f"Pre-sync patch loop: Attempting to patch '{vs_toolchain_path.name}' (pipes, VS exception, or shim v7.36 content issue detected). Try {patch_tries+1}/{MAX_PATCH_LOOP_TRIES_INNER}.", to_console=False)
                if _apply_vs_toolchain_patch_logic(vs_toolchain_path):
                    log("INFO", f"Pre-sync patch of '{vs_toolchain_path.name}' successful on try {patch_tries+1}.", to_console=False)
                    break
                else:
                    log("WARN", f"Pre-sync patch of '{vs_toolchain_path.name}' failed on try {patch_tries+1}. Retrying patch...", to_console=False)
                    time.sleep(1)
                patch_tries += 1
            
            run(cmd_base, cwd=root_dir, env=env)
            log("INFO", "gclient sync completed successfully.")

            if vs_toolchain_path.exists():
                log("INFO", f"Post-sync patch attempt for '{vs_toolchain_path.name}' after successful gclient sync attempt {attempt}.", to_console=False)
                # Always attempt post-sync patch, as gclient sync might overwrite it.
                if not _apply_vs_toolchain_patch_logic(vs_toolchain_path):
                    log("FATAL", f"Post-sync patch of '{vs_toolchain_path.name}' failed after attempt {attempt}. Aborting.", to_console=True)
                    sys.exit(1)
            
            return

        except Exception as e:
            log("ERROR", f"gclient sync attempt {attempt} failed: {e}")
            
            if vs_toolchain_path.exists():
                log("INFO", f"Error-recovery patch attempt for '{vs_toolchain_path.name}' after failed gclient sync attempt {attempt}.", to_console=False)
                if not _apply_vs_toolchain_patch_logic(vs_toolchain_path):
                    log("FATAL", f"Error-recovery patch of '{vs_toolchain_path.name}' failed after attempt {attempt}. Aborting.", to_console=True)
                    sys.exit(1)

            if attempt < retries:
                sleep_for = GCLIENT_RETRY_BACKOFF[min(attempt-1, len(GCLIENT_RETRY_BACKOFF)-1)]
                log("INFO", f"Retrying gclient sync in {sleep_for}s (attempt {attempt+1}/{retries})...")
                time.sleep(sleep_for)
            else:
                raise

# ----------------------------
# === Build steps ===
# ----------------------------
def _find_tool(names: list) -> str:
    """
    Searches for a tool (like gn or ninja) in PATH and then in DEPOT_TOOLS.
    Returns the full path to the tool or None if not found.
    """
    for n in names:
        path = shutil.which(n)
        if path:
            log("DEBUG", f"Found tool '{n}' in PATH: {path}", to_console=False)
            return path
    
    for n in names:
        p = Path(DEPOT_TOOLS) / n # Use Path
        if p.exists():
            log("DEBUG", f"Found tool '{n}' in DEPOT_TOOLS: {p}", to_console=False)
            return str(p) # Return as string for subprocess
    
    log("ERROR", f"Tool not found among candidates: {names}", to_console=False)
    return None

def ensure_depot_tools(env):
    """Ensures depot_tools is cloned and functional."""
    if Path(DEPOT_TOOLS).is_dir(): # Use Path.is_dir()
        log("INFO", f"depot_tools exists at {DEPOT_TOOLS}")
        return
    log("STEP", f"Cloning depot_tools into {DEPOT_TOOLS}")
    os.makedirs(Path(DEPOT_TOOLS).parent, exist_ok=True) # Use Path
    git_clone_with_retry(env, DEPOT_TOOLS, "https://chromium.googlesource.com/chromium/tools/depot_tools.git")
    log("INFO", "depot_tools cloned.")

def write_args_gn(out_dir):
    """Writes the args.gn file for the GN build configuration."""
    out_dir_path = Path(out_dir) # Use Path
    os.makedirs(out_dir_path, exist_ok=True)
    mingw_for = Path(MINGW_BIN).as_posix() # Use Path.as_posix() directly for consistency
    args_content = (
        "is_debug = false\n"
        "target_os = \"win\"\n"
        "target_cpu = \"x64\"\n"
        "is_clang = false\n"
        "use_sysroot = false\n"
        "treat_warnings_as_errors = false\n"
        "v8_static_library = true\n"
        "v8_use_external_startup_data = false\n"
        "v8_enable_i18n_support = false\n"
        "is_component_build = false\n"
        f'cc = "{mingw_for}/gcc.exe"\n'
        f'cxx = "{mingw_for}/g++.exe"\n'
        f'ar = "{mingw_for}/ar.exe"\n'
        f'strip = "{mingw_for}/strip.exe"\n'
        "v8_current_cpu = \"x64\"\n"
        "v8_current_os = \"win\"\n"
        "v8_target_cpu = \"x64\"\n"
        "v8_target_os = \"win\"\n"
    )
    p = out_dir_path / "args.gn" # Use Path for robust path handling
    with p.open("w", encoding="utf-8") as f:
        f.write(args_content)
    log("INFO", f"args.gn written to {p}")

def run_gn_gen(env):
    """Generates Ninja build files using GN."""
    gn_bin = _find_tool(["gn", "gn.exe"])
    if not gn_bin:
        raise RuntimeError("gn binary not found in PATH nor in depot_tools.")
    
    gn_command = [gn_bin, "gen", OUT_DIR]
    max_attempts = 2 # Try once, then once more after potential args.gn patching
    
    for attempt in range(1, max_attempts + 1):
        log("INFO", f"GN gen attempt {attempt}/{max_attempts}.", to_console=True)
        try:
            cp = run(gn_command, cwd=V8_SRC, env=env, check=False, capture_output=True)
            
            if cp.returncode == 0:
                log("INFO", f"GN generated build files in {OUT_DIR}.")
                return # Success!
            
            error_output = (cp.stdout or "") + (cp.stderr or "")
            log("ERROR", f"GN gen failed on attempt {attempt}: \n{error_output}", to_console=False)

            # Check for specific errors that indicate missing vcvars_toolchain_data or win_toolchain_data variables or GN syntax error
            
            # --- START: New checks for toolchain_data errors ---
            needs_toolchain_data_patch = False # Renamed to cover both vcvars and win toolchain data
            toolchain_data_error_patterns = [
                "No value named \"vc_bin_dir\" in scope \"vcvars_toolchain_data\"",
                "No value named \"vc_lib_path\" in scope \"vcvars_toolchain_data\"",
                "No value named \"vc_include_path\" in scope \"vcvars_toolchain_data\"",
                "No value named \"sdk_dir\" in scope \"vcvars_toolchain_data\"",
                "No value named \"sdk_lib_path\" in scope \"vcvars_toolchain_data\"",
                "No value named \"sdk_include_path\" in scope \"vcvars_toolchain_data\"",
                "No value named \"runtime_dirs\" in scope \"vcvars_toolchain_data\"",
                "No value named \"include_flags_imsvc\"" , # Covers both
                "No value named \"sys_lib_flags\" in scope \"win_toolchain_data\"",
                "No value named \"sys_include_flags\" in scope \"win_toolchain_data\"",
                "No value named \"vc_bin_dir\" in scope \"win_toolchain_data\"",
                "No value named \"vc_lib_path\" in scope \"win_toolchain_data\"",
                "No value named \"vc_include_path\" in scope \"win_toolchain_data\"",
                "No value named \"sdk_dir\" in scope \"win_toolchain_data\"",
                "No value named \"sdk_lib_path\" in scope \"win_toolchain_data\"",
                "No value named \"sdk_include_path\" in scope \"win_toolchain_data\"",
                "No value named \"runtime_dirs\" in scope \"win_toolchain_data\"",
                "Undefined identifier in string expansion.*sys_include_flags",
                "Undefined identifier in string expansion.*sys_lib_flags",
                "Assignment had no effect.*prefix",
                "Expecting assignment or function call.*BUILD.gn:", # Catch generic syntax errors from patching
            ]
            for pattern in toolchain_data_error_patterns:
                if re.search(pattern, error_output):
                    needs_toolchain_data_patch = True
                    break
            # --- END: New checks for toolchain_data errors ---

            if needs_toolchain_data_patch:
                
                log("INFO", "Detected missing toolchain variables or GN syntax error in GN output. Attempting to patch args.gn.", to_console=True)
                
                args_gn_path = Path(OUT_DIR) / "args.gn"
                current_args_content = args_gn_path.read_text(encoding="utf-8") if args_gn_path.exists() else ""
                
                new_args_to_add = []
                fake_vs_base_path_for_gn_obj = Path(V8_ROOT) / "FakeVS_Toolchain"
                fake_vs_base_path_for_gn_posix = fake_vs_base_path_for_gn_obj.as_posix()
                
                # Check for individual top-level args (safeguard) - These are mostly for vcvars_toolchain_data's underlying elements
                if 'vc_bin_dir =' not in current_args_content: new_args_to_add.append(f'vc_bin_dir = "{fake_vs_base_path_for_gn_posix}/VC/Tools/Bin/Hostx64/x64"')
                if 'vc_lib_path =' not in current_args_content: new_args_to_add.append(f'vc_lib_path = "{fake_vs_base_path_for_gn_posix}/VC/lib"')
                if 'vc_include_path =' not in current_args_content: new_args_to_add.append(f'vc_include_path = "{fake_vs_base_path_for_gn_posix}/VC/include"')
                if 'sdk_dir =' not in current_args_content: new_args_to_add.append(f'sdk_dir = "{fake_vs_base_path_for_gn_posix}/SDK"')
                if 'sdk_lib_path =' not in current_args_content: new_args_to_add.append(f'sdk_lib_path = "{fake_vs_base_path_for_gn_posix}/SDK/lib"')
                if 'sdk_include_path =' not in current_args_content: new_args_to_add.append(f'sdk_include_path = "{fake_vs_base_path_for_gn_posix}/SDK/include"')
                if 'runtime_dirs =' not in current_args_content: new_args_to_add.append(f'runtime_dirs = [ "{fake_vs_base_path_for_gn_posix}/redist" ]')
                
                # Also ensure visual_studio_path and visual_studio_version are set in args.gn if not present
                if 'visual_studio_path =' not in current_args_content: new_args_to_add.append('visual_studio_path = "C:/FakeVS"')
                if 'visual_studio_version =' not in current_args_content: new_args_to_add.append('visual_studio_version = "16.0"')
                # Add include_flags_imsvc to top-level args if not present (as a safeguard for direct usage)
                if 'include_flags_imsvc =' not in current_args_content: new_args_to_add.append('include_flags_imsvc = ""')


                # Define the vcvars_toolchain_data block to inject (using pre-formatted paths)
                vcvars_data_block = (
                    '\n# CerebrumLux Auto-patched vcvars_toolchain_data for MinGW build\n'
                    'vcvars_toolchain_data = {\n'
                    f'  vc_lib_path = "{(fake_vs_base_path_for_gn_obj / "VC" / "lib").as_posix()}"\n'
                    f'  vc_lib_atlmfc_path = "{(fake_vs_base_path_for_gn_obj / "VC" / "atlmfc" / "lib").as_posix()}"\n'
                    f'  vc_lib_um_path = "{(fake_vs_base_path_for_gn_obj / "VC" / "um" / "lib").as_posix()}"\n'
                    f'  vc_lib_ucrt_path = "{(fake_vs_base_path_for_gn_obj / "VC" / "ucrt" / "lib").as_posix()}"\n'
                    '}\n'
                )

                if 'vcvars_toolchain_data = {' not in current_args_content or \
                   f'vc_lib_path = "{(fake_vs_base_path_for_gn_obj / "VC" / "lib").as_posix()}"' not in current_args_content:
                    new_args_to_add.append(vcvars_data_block)
                    log("INFO", f"Prepared to inject 'vcvars_toolchain_data' object into {args_gn_path.name}.", to_console=True)
                else:
                    log("INFO", "'vcvars_toolchain_data' object appears to be already present and correctly defined in args.gn. Skipping injection of block.", to_console=True)

                # --- START: New win_toolchain_data injection logic for args.gn (now including sys_lib_flags and sys_include_flags) ---
                win_toolchain_data_block = (
                    '\n# CerebrumLux Auto-patched win_toolchain_data for MinGW build\n'
                    'win_toolchain_data = {\n'
                    f'  vc_bin_dir = "{(fake_vs_base_path_for_gn_obj / "VC" / "Tools" / "Bin" / "Hostx64" / "x64").as_posix()}"\n'
                    f'  vc_lib_path = "{(fake_vs_base_path_for_gn_obj / "VC" / "lib").as_posix()}"\n'
                    f'  vc_include_path = "{(fake_vs_base_path_for_gn_obj / "VC" / "include").as_posix()}"\n'
                    f'  sdk_dir = "{(fake_vs_base_path_for_gn_obj / "SDK").as_posix()}"\n'
                    f'  sdk_lib_path = "{(fake_vs_base_path_for_gn_obj / "SDK" / "lib").as_posix()}"\n'
                    f'  sdk_include_path = "{(fake_vs_base_path_for_gn_obj / "SDK" / "include").as_posix()}"\n'
                    f'  runtime_dirs = "{(fake_vs_base_path_for_gn_obj / "redist").as_posix()}"\n'
                    f'  include_flags_imsvc = ""\n'
                    f'  sys_lib_flags = []\n'
                    f'  sys_include_flags = []\n'
                    '}\n'
                )
                if needs_toolchain_data_patch and ('win_toolchain_data = {' not in current_args_content or
                                                      f'vc_bin_dir = "{(fake_vs_base_path_for_gn_obj / "VC" / "Tools" / "Bin" / "Hostx64" / "x64").as_posix()}"' not in current_args_content or
                                                      'sys_lib_flags = []' not in current_args_content):
                    new_args_to_add.append(win_toolchain_data_block)
                    log("INFO", f"Prepared to inject 'win_toolchain_data' object into {args_gn_path.name}.", to_console=True)
                else:
                    log("INFO", "'win_toolchain_data' object appears to be already present and correctly defined in args.gn or not needed. Skipping injection of block.", to_console=True)
                # --- END: New win_toolchain_data injection logic for args.gn ---


                if new_args_to_add:
                    with args_gn_path.open("a", encoding="utf-8") as f:
                        for arg_line in new_args_to_add:
                            f.write(arg_line + "\n")
                    log("INFO", f"Appended necessary configuration to {args_gn_path.name}.", to_console=True)
                elif attempt < max_attempts:
                    log("WARN", "Required GN variables appear to be present in args.gn or could not be injected. This might indicate another GN configuration issue.", to_console=True)
                    break 
                else:
                    raise RuntimeError("GN gen failed and auto-patching args.gn did not help or was not needed for toolchain_data errors.")

            else:
                log("FATAL", f"GN gen failed with unhandled error or after auto-patching. Full output:\n{error_output}", to_console=True)
                raise RuntimeError(f"GN gen command failed with code {cp.returncode}.")
        
        except Exception as e:
            if attempt == max_attempts:
                raise RuntimeError(f"GN gen failed after {max_attempts} attempts: {e}")
            else:
                log("WARN", f"GN gen failed on attempt {attempt}, trying again: {e}", to_console=True)
                time.sleep(2)

    raise RuntimeError("GN gen failed after all attempts.")


def run_ninja_build(env):
    """Starts the main V8 compilation with Ninja."""
    ninja_bin = _find_tool(["ninja", "ninja.exe"])
    if not ninja_bin:
        raise RuntimeError("ninja binary not found in PATH nor in depot_tools.")
    run([str(ninja_bin), "-C", OUT_DIR, NINJA_TARGET], cwd=V8_SRC, env=env)
    log("INFO", f"Ninja build of '{NINJA_TARGET}' completed.")

def copy_to_vcpkg():
    """Copies compiled V8 artifacts (lib and headers) to vcpkg's installed directory."""
    target_lib_dir = Path(VCPKG_ROOT) / "installed" / "x64-mingw-static" / "lib"
    target_include_dir = Path(VCPKG_ROOT) / "installed" / "x64-mingw-static" / "include"
    os.makedirs(target_lib_dir, exist_ok=True)
    os.makedirs(target_include_dir, exist_ok=True)
    
    lib_candidate = Path(OUT_DIR) / "obj" / "libv8_monolith.a"
    if not lib_candidate.exists():
        found = []
        for root, _, files in os.walk(OUT_DIR):
            for fn in files:
                if fn.lower().startswith("libv8_monolith") and fn.endswith(".a"):
                    found.append(Path(root) / fn)
        if found:
            lib_candidate = found[0]
            log("INFO", f"Found libv8_monolith.a at: {lib_candidate}")
        else:
            log("ERROR", f"Built libv8_monolith.a not found under {OUT_DIR}")
            raise FileNotFoundError(f"Built libv8_monolith.a not found under {OUT_DIR}")
            
    shutil.copy2(lib_candidate, target_lib_dir)
    log("INFO", f"Copied '{lib_candidate.name}' to '{target_lib_dir}'")

    src_include = Path(V8_SRC) / "include"
    if not src_include.is_dir():
        log("ERROR", f"Headers not found in source include path: {src_include}")
        raise FileNotFoundError(src_include)
    
    shutil.copytree(src_include, target_include_dir, dirs_exist_ok=True)
    log("INFO", f"V8 headers copied from '{src_include}' to '{target_include_dir}'")
    log("INFO", f"V8 lib + headers copied into vcpkg installed tree ({target_lib_dir}, {target_include_dir})")

def update_vcpkg_port(version, ref, homepage, license):
    """Updates or creates the vcpkg portfile and manifest for V8."""
    port_v8_dir = Path(VCPKG_ROOT) / "ports" / "v8"
    os.makedirs(port_v8_dir, exist_ok=True)
    portfile_path = port_v8_dir / "portfile.cmake"
    manifest_path = port_v8_dir / "vcpkg.json"

    cmake_content = f"""
# Auto-generated by CerebrumLux V8 Builder v7.36
# This portfile directly uses the pre-built V8 library and headers
# generated by the custom Python script.
# It skips the standard vcpkg build process for V8 for MinGW compatibility.

vcpkg_check_linkage(ONLY_STATIC_LIBRARY)

# This is a dummy 'from_git' call for vcpkg's internal checks,
# the actual fetching/building is done by the custom Python script.
vcpkg_from_git(
    OUT_SOURCE_PATH SOURCE_PATH
    URL {V8_GIT_URL}
    REF {ref}
    HEAD_REF main # Placeholder, actual ref used by custom script
    PATCHES
)

# Skip configure and build steps, as artifacts are pre-built
vcpkg_install_cmake(
    SOURCE_PATH ${{SOURCE_PATH}}
    DISABLE_INSTALL_SUPPORT
)

# Copy prebuilt static lib from custom builder (CerebrumLux)
file(COPY "{(Path(VCPKG_ROOT) / 'installed' / 'x64-mingw-static' / 'lib' / 'libv8_monolith.a').as_posix()}" DESTINATION ${{CURRENT_PACKAGES_DIR}}/lib)

# Copy headers - already handled by direct copy_to_vcpkg.
# Use a more explicit path for V8_ROOT to avoid issues with CMake variable scope.
file(GLOB_RECURSE V8_HEADERS_TO_COPY "{(Path(V8_ROOT) / 'v8' / 'include').as_posix()}/*.h" "{(Path(V8_ROOT) / 'v8' / 'include').as_posix()}/*.hpp")
file(COPY ${{V8_HEADERS_TO_COPY}} DESTINATION ${{CURRENT_PACKAGES_DIR}}/include/v8)

# Handle copyright
file(INSTALL "${{SOURCE_PATH}}/LICENSE" DESTINATION "${{CURRENT_PACKAGES_DIR}}/share/${{PORT}}" RENAME copyright)
"""
    with open(portfile_path, "w", encoding="utf-8") as f:
        f.write(cmake_content)
    log("INFO", f"Updated {portfile_path}")

    manifest = {
        "name": "v8",
        "version-string": version,
        "description": "Google V8 JavaScript engine (MinGW-w64 compatible, prebuilt by CerebrumLux custom script)",
        "homepage": homepage,
        "license": "BSD-3-Clause",
        "supports": "windows & !uwp"
    }
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)
    log("INFO", f"Created/updated {manifest_path}")

def vcpkg_integrate_install(env):
    """Runs 'vcpkg integrate install' for system-wide CMake integration."""
    vcpkg_exe = Path(VCPKG_ROOT) / "vcpkg.exe"
    if not vcpkg_exe.exists():
        log("WARN", f"vcpkg.exe not found at {vcpkg_exe}, skipping 'vcpkg integrate install'.")
        return
    log("STEP", "Running 'vcpkg integrate install'...")
    run([str(vcpkg_exe), "integrate", "install"], env=env, capture_output=True)
    log("INFO", "'vcpkg integrate install' completed.")

# ----------------------------
# === Main Workflow ===
# ----------------------------
def main(): # CerebrumLux V8 Build v7.37.9
    # Filter DeprecationWarnings, especially from Python's datetime module
    warnings.filterwarnings("ignore", category=DeprecationWarning)

    log("START", "=== CerebrumLux V8 Build v7.37.8 started ===", to_console=True) # Updated start message for 7.37.1
    start_time = time.time()
    env = prepare_subprocess_env()

    try:
        if Path(V8_ROOT).is_dir():
            log("INFO", f"V8_ROOT '{V8_ROOT}' exists. Attempting incremental update. Manual deletion required for full fresh start.", to_console=True)
        else:
            log("INFO", f"Creating V8_ROOT for fresh start: {V8_ROOT}", to_console=True)
        os.makedirs(V8_ROOT, exist_ok=True)

        # Create dummy VS toolchain directories early
        _create_fake_vs_toolchain_dirs(V8_ROOT)

        log("STEP", "Ensuring depot_tools is cloned and functional.")
        ensure_depot_tools(env)
        
        log("STEP", "Writing .gclient file in V8_ROOT for V8 repository configuration.")
        write_gclient_file(V8_ROOT, V8_GIT_URL)

        log("STEP", "Running initial gclient sync to clone V8 and fetch core dependencies.")
        gclient_sync_with_retry(env, V8_ROOT, V8_SRC)
        
        log("STEP", "Running self-test for 'vs_toolchain.py' after initial sync to ensure it runs correctly.")
        try:
            vs_toolchain_path_for_test = Path(V8_SRC) / "build" / "vs_toolchain.py"
            if vs_toolchain_path_for_test.exists():
                cp = run([sys.executable, str(vs_toolchain_path_for_test), "get_toolchain_dir"], 
                         cwd=vs_toolchain_path_for_test.parent, env=env, check=False, capture_output=True)
                
                if cp.returncode != 0:
                    log("FATAL", f"vs_toolchain.py self-test FAILED (exit code {cp.returncode}). Stderr:\n{cp.stderr}", to_console=True)
                    sys.exit(1)
                else:
                    log("INFO", "vs_toolchain.py self-test PASSED (exit code 0).", to_console=True)
            else:
                log("FATAL", "'vs_toolchain.py' not found after initial sync. Cannot run self-test. This indicates a deeper gclient issue.", to_console=True)
                sys.exit(1)
        except Exception as e:
            log("FATAL", f"vs_toolchain.py self-test encountered an unexpected error: {e}", to_console=True)
            sys.exit(1)

        log("STEP", f"Checking out specific V8 reference ({V8_REF}) in {V8_SRC}.")
        run(["git", "checkout", V8_REF], cwd=V8_SRC, env=env)
        run(["git", "reset", "--hard", V8_REF], cwd=V8_SRC, env=env)
        log("INFO", f"Checked out V8 ref {V8_REF}.")

        log("STEP", "Patching V8 DEPS file and build configuration files for MinGW compatibility.")
        patch_v8_deps_for_mingw(V8_SRC, env)

        log("STEP", "Running second gclient sync to apply DEPS changes and ensure consistency.")
        gclient_sync_with_retry(env, V8_ROOT, V8_SRC)

        log("STEP", "Re-patching .gni, setup_toolchain.py and BUILD.gn files after sync to ensure changes persist.")
        # The patching functions contain logic to check if patches are already applied
        # and re-apply if needed, so calling them here is safe and ensures persistence.
        if not _patch_dotfile_settings_gni(V8_SRC, env):
            log("FATAL", "Failed to re-patch 'build/dotfile_settings.gni'. Aborting.", to_console=True)
            sys.exit(1)
        if not _patch_visual_studio_version_gni(V8_SRC, env):
            log("FATAL", "Failed to re-patch 'build/config/win/visual_studio_version.gni'. Aborting.", to_console=True)
            sys.exit(1)
        if not _patch_setup_toolchain_py(V8_SRC, env):
            log("FATAL", "Failed to re-patch 'build/toolchain/win/setup_toolchain.py'. Aborting.", to_console=True)
            sys.exit(1)
        if not _patch_build_gn(V8_SRC, env): # Re-patch build/config/win/BUILD.gn as well
            log("FATAL", "Failed to re-patch 'build/config/win/BUILD.gn'. Aborting.", to_console=True)
            sys.exit(1)
        build_config_win_build_gn_path = Path(V8_SRC) / "build" / "config" / "win" / "BUILD.gn"
        if normalize_gn_lists(build_config_win_build_gn_path):
            run(["git", "add", str(build_config_win_build_gn_path)], cwd=V8_SRC, env=env, check=False)
            log("INFO", f"Staged '{build_config_win_build_gn_path.name}' changes with 'git add' after re-patching and normalization.", to_console=True)
        else:
            run(["git", "add", str(build_config_win_build_gn_path)], cwd=V8_SRC, env=env, check=False)

        if not _patch_toolchain_win_build_gn(V8_SRC, env): # Re-patch build/toolchain/win/BUILD.gn as well
            log("FATAL", "Failed to re-patch 'build/toolchain/win/BUILD.gn'. Aborting.", to_console=True)
            sys.exit(1)
        toolchain_build_gn_path = Path(V8_SRC) / "build" / "toolchain" / "win" / "BUILD.gn"
        if normalize_gn_lists(toolchain_build_gn_path):
            run(["git", "add", str(toolchain_build_gn_path)], cwd=V8_SRC, env=env, check=False)
            log("INFO", f"Staged '{toolchain_build_gn_path.name}' changes with 'git add' after GN list normalization.", to_console=True)
        else:
            run(["git", "add", str(toolchain_build_gn_path)], cwd=V8_SRC, env=env, check=False)

        log("STEP", "Writing args.gn configuration for MinGW build.")
        write_args_gn(OUT_DIR)
        
        log("STEP", "Generating Ninja build files with GN.")
        run_gn_gen(env)

        log("STEP", "Starting the main V8 compilation with Ninja.")
        run_ninja_build(env)

        log("STEP", "Copying compiled V8 artifacts to vcpkg's installed directory.")
        copy_to_vcpkg()
        
        log("STEP", "Updating vcpkg portfile and manifest for V8 integration.")
        update_vcpkg_port(V8_VERSION, V8_REF, "https://chromium.googlesource.com/v8/v8", "BSD-3-Clause")
        
        log("STEP", "Running 'vcpkg integrate install' for system-wide CMake integration.")
        vcpkg_integrate_install(env)
        
        log("SUCCESS", "V8 build + integration complete. Please inspect logs for details.", to_console=True)

    except Exception as e:
        log("FATAL", f"Build process encountered a fatal error: {e}", to_console=True)
        sys.exit(1)
    finally:
        end_time = time.time()
        duration = end_time - start_time
        log("INFO", f"Script finished. Total time: {duration:.2f} seconds. Check full log file for details: {LOG_FILE}", to_console=True)
        with Path(LOG_FILE).open('r', encoding='utf-8') as f:
            log_content = f.read()
            if "FATAL" in log_content or "ERROR" in log_content:
                log("SUMMARY_ERROR", f"Errors or Fatal issues detected in logs. Please check CerebrumLux-V8-Build-{V8_VERSION}.log and CerebrumLux-V8-Build-{V8_VERSION}-error.log", to_console=True)
            else:
                log("SUMMARY_SUCCESS", "No major errors detected. V8 build is likely successful!", to_console=True)

if __name__ == "__main__":
    os.makedirs(LOG_DIR, exist_ok=True)
    if Path(LOG_FILE).exists():
        try:
            timestamp_str = datetime.datetime.now().strftime('%Y%m%d%H%M%S')
            shutil.move(LOG_FILE, f"{LOG_FILE}.old-{timestamp_str}")
        except Exception as e:
            print(f"WARN: Could not move old log file: {e}")
    if Path(ERR_FILE).exists():
        try:
            timestamp_str = datetime.datetime.now().strftime('%Y%m%d%H%M%S')
            shutil.move(ERR_FILE, f"{ERR_FILE}.old-{timestamp_str}")
        except Exception as e:
            print(f"WARN: Could not move old error log file: {e}")
    main()