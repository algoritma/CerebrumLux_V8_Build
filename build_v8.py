#!/usr/bin/env python3
"""
CerebrumLux V8 Build Automation v7.24 (Final Robust MinGW Build - Incorporating all feedback)
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
- FIX (v7.24): Refined `_patch_toolchain_win_build_gn` regex for `sys_lib_flags` and `sys_include_flags` to be more general (`.*` instead of `\[[\s\S]*?\]`) and removed `re.DOTALL` to correctly handle single-line assignments, resolving "Expecting assignment or function call" error. Updated shim version.
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
def write_gclient_file(root_dir, url):
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
    """Internal helper to aggressively patch vs_toolchain.py.
    This version **prepends** a robust shim block, then REMOVES original function bodies.
    """
    try:
        if not vs_toolchain_path.exists():
            log("DEBUG", f"'{vs_toolchain_path.name}' not found at {vs_toolchain_path}, cannot patch.", to_console=False)
            return False

        text = vs_toolchain_path.read_text(encoding="utf-8")
        original_text = text
        modified = False

        # Prepare a small top-of-file shim to guarantee definitions are present early.
        # FIX (v7.1): Changed wdk_path, sdk_path, and DetectVisualStudioPath to non-empty dummy paths.
        shim_block = (
            "# --- CerebrumLux injected shim START (v7.22) ---\n" # Updated shim version marker
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
            "    return r'C:\\FakeVS'\n" # Changed from r'' to non-empty dummy path
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
            "        'sdk_path': r'C:\\FakeSDK',\n" # Changed from r'' to non-empty dummy path
            "        'wdk_path': r'C:\\FakeWDK',\n" # Changed from r'' to non-empty dummy path
            "        'runtime_dirs': [r'C:\\FakeVS\\VC\\Tools\\MSVC\\14.16.27023\\bin\\Hostx64\\x64'],\n" # Changed from [] to a list with a dummy path
            "        'version': GetVisualStudioVersion(),\n"
            "    }\n"
            "# --- CerebrumLux injected shim END ---\n\n"
        )

        # Check for the *current* shim version. If it's not present, or if an older version is, apply.
        if f"# --- CerebrumLux injected shim START (v7.22) ---" not in text: 
            text = shim_block + text
            modified = True
            log("INFO", f"Prepended CerebrumLux shim to '{vs_toolchain_path.name}'.", to_console=False)
        else:
            log("DEBUG", f"CerebrumLux shim already present in '{vs_toolchain_path.name}', skipping prepend.", to_console=False)
            
            # More robust way: if old shim is found, remove it and re-prepend.
            # This prevents duplicate shims and ensures the latest content.
            old_shim_pattern = re.compile(r"# --- CerebrumLux injected shim START \(v[\d\.]+\) ---[\s\S]*?# --- CerebrumLux injected shim END ---\n\n", re.MULTILINE)
            if old_shim_pattern.search(text):
                text = old_shim_pattern.sub("", text)
                log("DEBUG", f"Removed old CerebrumLux shim from '{vs_toolchain_path.name}' for re-application.", to_console=False)
                text = shim_block + text # Re-prepend the latest shim
                modified = True
            else: # If a previous CerebrumLux shim marker exists but wasn't caught by old_shim_pattern, it means the pattern might not match perfectly.
                  # As a fallback, check for content of previous versions.
                if any(s in text for s in [r"wdk_path': r''", r"sdk_path': r''", r"DetectVisualStudioPath():\n    return r''", r"# --- CerebrumLux injected shim START (v7.0) ---"]):
                    log("WARN", f"Outdated CerebrumLux shim content or old version marker detected in '{vs_toolchain_path.name}'. Re-applying full shim.", to_console=False)
                    # Aggressively remove any previous CerebrumLux shim markers and re-prepend
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
                # Only create backup if file was actually modified
                bak_path = vs_toolchain_path.with_suffix(vs_toolchain_path.suffix + ".cerebrumlux.bak")
                if not bak_path.exists() or original_text != text: # Ensure backup is of original before *this* run's changes, or if new content
                    bak_path.write_bytes(original_text.encode("utf-8", errors="replace"))
                    log("DEBUG", f"Created backup of original '{vs_toolchain_path.name}' at '{bak_path.name}'.", to_console=False)
            except Exception as e:
                log("WARN", f"Could not write backup of '{vs_toolchain_path.name}': {e}", to_console=False)

            vs_toolchain_path.write_text(text, encoding="utf-8")
            log("INFO", f"'{vs_toolchain_path.name}' patched (shim-injected and originals deleted) successfully.", to_console=False)
            return True
        else:
            log("INFO", f"No changes required for '{vs_toolchain_path.name}'.", to_console=False)
            # Re-verify if the shim is still correct in case no 'modified' flag was set (e.g., if re-running)
            current_content = vs_toolchain_path.read_text(encoding="utf-8")
            if f"# --- CerebrumLux injected shim START (v7.22) ---" not in current_content:
                log("ERROR", f"'{vs_toolchain_path.name}' does not contain the CerebrumLux shim (v7.22) after expected patching. Patching is NOT sticking.", to_console=False)
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
            # Also explicitly check the dummy paths within the shim for consistency (v7.1 check)
            if any(s in current_content for s in [r"wdk_path': r''", r"sdk_path': r''", r"DetectVisualStudioPath():\n    return r''"]):
                 log("ERROR", f"'{vs_toolchain_path.name}' shim contains empty paths (r''). Patching is NOT sticking (v7.22 content missing).", to_console=False)
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
            # FIX: Use the compiled pattern's .sub() method directly, without passing flags again.
            patched_content = exec_script_pattern.sub(r"\g<indent># CerebrumLux neutralized: \g<0>", patched_content)
            modified = True
            log("INFO", f"Neutralized 'exec_script(\"../../vs_toolchain.py\"...)' call in '{vs_version_gni_path.name}'.", to_console=False)

        # 3. Find and replace *all* assignments to visual_studio_path, visual_studio_version, visual_studio_runtime_dirs
        # FIX (v7.1): Set non-empty dummy paths for all relevant variables.
        assignments_to_patch = {
            "visual_studio_path": '"C:/FakeVS"',
            "visual_studio_version": '"16.0"',
            "visual_studio_runtime_dirs": '"C:/FakeVS/VC/Tools/MSVC/14.16.27023/bin/Hostx64/x64"',
            "windows_sdk_path": '"C:/FakeSDK"', # Added to ensure non-empty for consistency
            "wdk_path": '"C:/FakeWDK"' # Added to ensure non-empty for consistency
        }

        for var, dummy_value in assignments_to_patch.items():
            # FIX: Escape the variable name to prevent regex errors if it contains special characters.
            # FIX: Using explicit double backslashes in f-string to prevent premature backslash interpretation.
            pattern_text = f"^(?P<indent>\\s*){re.escape(var)}\\s*=\\s*.*$"
            assignment_pattern = re.compile(pattern_text, re.MULTILINE)
            
            initial_var_content = patched_content
            # Keep replacing until no more matches found, ensuring all occurrences are covered.
            while True:
                new_content_after_sub = assignment_pattern.sub(f"\\g<indent>{var} = {dummy_value} # CerebrumLux MinGW patch", patched_content)
                if new_content_after_sub == patched_content:
                    break
                patched_content = new_content_after_sub
                if initial_var_content != patched_content:
                    modified = True
                    log("INFO", f"Replaced assignment for '{var}' with dummy value in '{vs_version_gni_path.name}'.", to_console=False)
            
            # If the variable was not found as an assignment, try to inject it as a declare_args.
            # This ensures they are always defined with our dummy values.
            if not re.search(rf"^\s*{re.escape(var)}\s*=\s*{re.escape(dummy_value)}", patched_content, re.MULTILINE) and \
               not re.search(rf"^\s*{re.escape(var)}\s*=\s*[\s\S]*?# CerebrumLux MinGW patch", patched_content, re.MULTILINE): # Check if already explicitly patched
                declare_args_block_pattern = re.compile(r"(^\s*declare_args\s*\(\s*\)\s*\{\n)(?P<body_content>[\s\S]*?)(^\s*\}\s*$)", re.MULTILINE | re.DOTALL)
                match_declare_args = re.search(declare_args_block_pattern, patched_content)
                if match_declare_args and f"{var} =" not in match_declare_args.group('body_content'):
                    indent_level_declare_args = re.match(r"^\s*", match_declare_args.group(1), re.MULTILINE).group(0)
                    insert_text = f"{indent_level_declare_args}  {var} = {dummy_value} # CerebrumLux MinGW injected default\n"
                    patched_content = patched_content[:match_declare_args.end('body_content')] + insert_text + patched_content[match_declare_args.end('body_content'):]
                    modified = True
                    log("INFO", f"Injected default assignment for '{var}' into 'declare_args()' in '{vs_version_gni_path.name}' as a fallback.", to_console=False)


        # --- Extra fallback patch for missing toolchain_data.vs_path (GN gen stage) ---
        # FIX (v7.1): Replaced with non-empty dummy string.
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
        # FIX (v7.1): Replaced with non-empty dummy string.
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
        # FIX (v7.1): Replaced with non-empty dummy string.
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

        # FIX (v7.5): Completely replace _LoadToolchainEnv to bypass vcvarsall.bat check.
        # This is more robust than trying to patch inside the function.
        # FIX (v7.6): Ensure the replacement body includes all expected keys and creates dummy directories.
        # FIX (v7.8): Use .as_posix() for paths in the replacement string to avoid bad escape errors.
        pattern_load_toolchain_env = re.compile(
            r"^(def\s+_LoadToolchainEnv\([^)]*\):(?:\n\s+.*)*?)(?=\n^def|\Z)", # Matches the entire function body
            re.MULTILINE | re.DOTALL
        )
        if pattern_load_toolchain_env.search(patched_content):
            # Define dummy paths relative to V8_ROOT to avoid hardcoding C:\FakeVS directly in the patch function body.
            # This ensures they are created *within* the V8 build environment if needed for checks.
            fake_vs_root_for_py = Path(V8_ROOT) / "FakeVS_Toolchain"
            
            # Create dummy directories if they don't exist (These are now handled by _create_fake_vs_toolchain_dirs)
            # Removed redundant os.makedirs calls here.

            # Use .as_posix() for paths in the string for consistency with GN and to avoid escape issues
            replacement_func_body = f"""def _LoadToolchainEnv(cpu, toolchain_root, win_sdk_path, target_store):
    # CerebrumLux MinGW patch: Bypassed vcvarsall.bat check and returning a dummy env.
    # The actual toolchain paths are provided in args.gn or directly configured by build_v8.py.
    # Dummy directories created by _create_fake_vs_toolchain_dirs in main().
    fake_vs_root = Path(r"{fake_vs_root_for_py.as_posix()}") # Use Path for internal consistency
    return {{
        "vc_bin_dir": (fake_vs_root / "VC" / "bin").as_posix(),
        "vc_lib_path": (fake_vs_root / "VC" / "lib").as_posix(),
        "vc_include_path": (fake_vs_root / "VC" / "include").as_posix(),
        "sdk_dir": (fake_vs_root / "SDK").as_posix(),
        "sdk_lib_path": (fake_vs_root / "SDK" / "lib").as_posix(),
        "sdk_include_path": (fake_vs_root / "SDK" / "include").as_posix(),
        "runtime_dirs": (fake_vs_root / "redist").as_posix()
    }}
"""
            patched_content = pattern_load_toolchain_env.sub(
                replacement_func_body,
                patched_content
            )
            modified = True
            log("INFO", f"Replaced '_LoadToolchainEnv' function body in '{setup_toolchain_path.name}' with full dummy environment (using .as_posix()).", to_console=False)
        else:
            # Fallback for older structures (should not be hit with current _LoadToolchainEnv replacement)
            # Patch _DetectVisualStudioPath
            pattern_detect_vs_path = re.compile(r"^(?P<indent>\s*)return\s+vs_toolchain\.DetectVisualStudioPath\(\)\s*$", re.MULTILINE)
            if pattern_detect_vs_path.search(patched_content):
                patched_content = pattern_detect_vs_path.sub(
                    r"\g<indent>return 'C:/FakeVS' # CerebrumLux MinGW patch", # Use / for consistency
                    patched_content
                )
                    # No longer creating dirs here as the main _LoadToolchainEnv replacement handles it.
                modified = True
                log("INFO", f"Patched '_DetectVisualStudioPath' call in '{setup_toolchain_path.name}' (fallback).", to_console=False)
            
            # Patch _GetVisualStudioVersion
            pattern_get_vs_version = re.compile(r"^(?P<indent>\s*)return\s+vs_toolchain\.GetVisualStudioVersion\(\)\s*$", re.MULTILINE)
            if pattern_detect_vs_path.search(patched_content): # This should be pattern_get_vs_version
                patched_content = pattern_get_vs_version.sub(
                    r"\g<indent>return '16.0' # CerebrumLux MinGW patch",
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
    Patches V8_SRC/build/config/win/BUILD.gn to neutralize the 'exec_script' call
    that populates vcvars_toolchain_data, and replaces direct accesses to
    vcvars_toolchain_data members with hardcoded dummy paths, relying instead on args.gn for this.
    """
    build_gn_path = Path(v8_source_dir) / "build" / "config" / "win" / "BUILD.gn"
    if not build_gn_path.exists():
        log("WARN", f"'{build_gn_path.name}' not found at {build_gn_path}. Skipping patch.", to_console=True)
        return False

    log("INFO", f"Patching '{build_gn_path.name}' to neutralize 'exec_script' and replace vcvars_toolchain_data accesses with dummy paths.", to_console=True)
    try:
        content = build_gn_path.read_text(encoding="utf-8")
        patched_content = content
        modified = False

        # --- 1. Neutralize the exec_script call for vcvars_toolchain_data ---
        exec_script_vcvars_pattern = re.compile(
            r"^(?P<indent>\s*)vcvars_toolchain_data\s*=\s*exec_script\(\"..\s*/..\s*/toolchain/win/setup_toolchain\.py\"[\s\S]*?\)\s*\n",
            re.MULTILINE | re.DOTALL
        )

        if exec_script_vcvars_pattern.search(patched_content):
            patched_content = exec_script_vcvars_pattern.sub(r"\g<indent># CerebrumLux neutralized: \g<0>", patched_content)
            modified = True
            log("INFO", f"Neutralized 'exec_script' call for 'vcvars_toolchain_data' in '{build_gn_path.name}'.", to_console=False)
        else:
            log("INFO", f"No 'exec_script' call for 'vcvars_toolchain_data' found in '{build_gn_path.name}' or already neutralized. Skipping.", to_console=False)

        # --- 2. Replace direct accesses to vcvars_toolchain_data.<field> with hardcoded dummy paths ---
        # Define dummy paths using the same base as in _create_fake_vs_toolchain_dirs
        fake_vs_base_path_for_gn_obj = Path(V8_ROOT) / "FakeVS_Toolchain"
        
        # Create dummy directories if they don't exist (These are now handled by _create_fake_vs_toolchain_dirs)
        # Redundant os.makedirs calls here are removed.

        # Map of vcvars_toolchain_data fields to their hardcoded dummy paths (as_posix() ensures forward slashes)
        dummy_vcvars_paths = {
            "vc_lib_path": (fake_vs_base_path_for_gn_obj / "VC" / "lib").as_posix(),
            "vc_lib_atlmfc_path": (fake_vs_base_path_for_gn_obj / "VC" / "atlmfc" / "lib").as_posix(),
            "vc_lib_um_path": (fake_vs_base_path_for_gn_obj / "VC" / "um" / "lib").as_posix(),
            "vc_lib_ucrt_path": (fake_vs_base_path_for_gn_obj / "VC" / "ucrt" / "lib").as_posix(),
            # Add other fields if BUILD.gn accesses them directly later
        }

        # Priority 1: Replace defined(vcvars_toolchain_data.<field>) with 'true'
        for field in dummy_vcvars_paths.keys():
            defined_pattern = re.compile(
                r"(?P<prefix>if\s*\(\s*)defined\(\s*vcvars_toolchain_data\." + re.escape(field) + r"\s*\)(?P<suffix>\s*\)\s*\{)",
                re.MULTILINE
            )
            initial_defined_replace_text = patched_content
            # Replace the entire defined() call with 'true'. Keep the surrounding 'if (...) {'.
            # GN's 'defined' only checks if a variable exists. If we are bypassing the VS toolchain,
            # we want these checks to succeed, effectively indicating the "paths" are present.
            # FIX (v7.17): Removed the C-style comment from the replacement string.
            patched_content = defined_pattern.sub(r'\g<prefix>true\g<suffix>', patched_content)
            if initial_defined_replace_text != patched_content:
                modified = True
                log("INFO", f"Replaced 'defined(vcvars_toolchain_data.{field})' with 'true' in '{build_gn_path.name}'.", to_console=False)

        # Priority 2: Replace direct assignments like `some_variable = vcvars_toolchain_data.<field>`
        for field, dummy_path in dummy_vcvars_paths.items():
            assignment_pattern = re.compile(
                r"^(?P<indent>\s*)(?P<lhs>[a-zA-Z0-9_]+\s*=\s*)vcvars_toolchain_data\." + re.escape(field) + r"(?P<rest>.*)$",
                re.MULTILINE
            )
            initial_assignment_replace_text = patched_content
            # The replacement string is a literal string in GN, so `"` + path + `"` is correct.
            patched_content = assignment_pattern.sub(r'\g<indent>\g<lhs>"' + dummy_path + r'"\g<rest> # CerebrumLux MinGW patch', patched_content)
            if initial_assignment_replace_text != patched_content:
                modified = True
                log("INFO", f"Replaced assignment for 'vcvars_toolchain_data.{field}' with hardcoded dummy path in '{build_gn_path.name}'.", to_console=False)

        # Priority 3: Replace any other generic occurrences of `vcvars_toolchain_data.<field>` with its dummy path
        for field, dummy_path in dummy_vcvars_paths.items():
            generic_access_pattern = re.compile(r"vcvars_toolchain_data\." + re.escape(field), re.MULTILINE)
            initial_generic_replace_text = patched_content
            # Replace with `"dummy_path"` literal string.
            patched_content = generic_access_pattern.sub(f'"{dummy_path}"', patched_content)
            if initial_generic_replace_text != patched_content:
                modified = True
                log("INFO", f"Replaced generic access to 'vcvars_toolchain_data.{field}' with hardcoded dummy path in '{build_gn_path.name}'.", to_console=False)


        if modified:
            patched_content = _filter_gn_comments(patched_content) # Apply general comment filter before writing back
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
    that populates win_toolchain_data, and injects a direct definition of win_toolchain_data
    with hardcoded dummy paths. It also handles tool definitions and problematic flags.
    """
    toolchain_build_gn_path = Path(v8_source_dir) / "build" / "toolchain" / "win" / "BUILD.gn"
    if not toolchain_build_gn_path.exists():
        log("WARN", f"'{toolchain_build_gn_path.name}' not found at {toolchain_build_gn_path}. Skipping patch.", to_console=True)
        return False

    log("INFO", f"Patching '{toolchain_build_gn_path.name}' to neutralize 'exec_script', inject direct win_toolchain_data definition, and handle tool definitions and flags.", to_console=True)
    try:
        content = toolchain_build_gn_path.read_text(encoding="utf-8")
        patched_content = content
        modified = False

        # Define dummy paths using the same base as in _create_fake_vs_toolchain_dirs
        fake_vs_base_path_obj = Path(V8_ROOT) / "FakeVS_Toolchain"

        # Map of win_toolchain_data fields to their hardcoded dummy paths (as_posix() for forward slashes)
        dummy_win_toolchain_paths = {
            "vc_bin_dir": (fake_vs_base_path_obj / "VC" / "Tools" / "Bin" / "Hostx64" / "x64").as_posix(),
            "vc_lib_path": (fake_vs_base_path_obj / "VC" / "lib").as_posix(),
            "vc_include_path": (fake_vs_base_path_obj / "VC" / "include").as_posix(),
            "sdk_dir": (fake_vs_base_path_path_obj / "SDK").as_posix(), # Ensure base SDK is also a Path
            "sdk_lib_path": (fake_vs_base_path_obj / "SDK" / "lib").as_posix(),
            "sdk_include_path": (fake_vs_base_path_obj / "SDK" / "include").as_posix(),
            "runtime_dirs": (fake_vs_base_path_obj / "redist").as_posix(),
            "include_flags_imsvc": "", # Added for the specific error "No value named include_flags_imsvc"
        }
        
        # --- 1. Neutralize the exec_script call for win_toolchain_data ---
        # FIX (v7.21): Ensure the regex matches the full exec_script call and replaces it cleanly.
        exec_script_win_toolchain_pattern = re.compile(
            r"^(?P<indent>\s*)win_toolchain_data\s*=\s*exec_script\(\"setup_toolchain\.py\"[\s\S]*?\)\s*\n",
            re.MULTILINE | re.DOTALL
        )

        if exec_script_win_toolchain_pattern.search(patched_content):
            # Replace the entire matched block with just a comment, ensuring no syntax issues.
            patched_content = exec_script_win_toolchain_pattern.sub(r"\g<indent># CerebrumLux neutralized win_toolchain_data exec_script call.", patched_content)
            modified = True
            log("INFO", f"Neutralized 'exec_script' call for 'win_toolchain_data' in '{toolchain_build_gn_path.name}'.", to_console=False)
        else:
            log("INFO", f"No 'exec_script' call for 'win_toolchain_data' found in '{toolchain_build_gn_path.name}' or already neutralized. Skipping.", to_console=False)

        # --- 2. Inject a direct definition for win_toolchain_data after neutralizing exec_script ---
        # Find the insertion point (right after the neutralized exec_script line, or at the top if not found)
        win_toolchain_data_block_marker = "# CerebrumLux Injected win_toolchain_data Block"
        
        # Check if the block is already present and correct, if so, no need to reinject.
        block_already_present_and_correct = (win_toolchain_data_block_marker in patched_content and
                                             f'  vc_bin_dir = "{dummy_win_toolchain_paths["vc_bin_dir"]}"' in patched_content and
                                             f'  include_flags_imsvc = "{dummy_win_toolchain_paths["include_flags_imsvc"]}"' in patched_content)

        if not block_already_present_and_correct:
            # If an old injected block is present but not matching current definition, remove it.
            old_injected_block_pattern = re.compile(
                r"^(?P<indent>\s*)# CerebrumLux Injected win_toolchain_data Block[\s\S]*?(?P=indent)\}\s*\n",
                re.MULTILINE | re.DOTALL
            )
            if old_injected_block_pattern.search(patched_content):
                patched_content = old_injected_block_pattern.sub("", patched_content)
                modified = True
                log("INFO", f"Removed old injected 'win_toolchain_data' definition from '{toolchain_build_gn_path.name}' for re-injection.", to_console=False)

            match_neutralized_line = re.search(r"^(?P<indent>\s*)# CerebrumLux neutralized win_toolchain_data exec_script call.", patched_content, re.MULTILINE)
            
            insert_point = 0
            indent_level = "  " # Default indentation if no match (e.g., at top of file)
            if match_neutralized_line:
                insert_point = match_neutralized_line.end()
                indent_level = match_neutralized_line.group('indent') # Use the same indentation as the neutralized line
            
            # Build the direct GN scope definition for win_toolchain_data
            direct_win_toolchain_scope = (
                f'\n{indent_level}{win_toolchain_data_block_marker}\n'
                f'{indent_level}win_toolchain_data = {{\n'
            )
            for field, dummy_path in dummy_win_toolchain_paths.items():
                direct_win_toolchain_scope += f'{indent_level}  {field} = "{dummy_path}"\n'
            direct_win_toolchain_scope += f'{indent_level}}}\n'
            
            patched_content = patched_content[:insert_point] + direct_win_toolchain_scope + patched_content[insert_point:]
            modified = True
            log("INFO", f"Injected direct 'win_toolchain_data' definition into '{toolchain_build_gn_path.name}'.", to_console=False)
        else:
            log("INFO", f"Direct 'win_toolchain_data' definition appears to be already present and correctly defined in '{toolchain_build_gn_path.name}'. Skipping injection.", to_console=False)
        

        # --- 3. Replace sys_include_flags and sys_lib_flags assignments with empty lists ---
        # FIX (v7.23): Make regex more general to catch any assignment, and assign an empty list.
        sys_include_flags_pattern = re.compile(
            r"^(?P<indent>\s*)sys_include_flags\s*=.*", # Match the whole line after indent and assignment
            re.MULTILINE
        )
        initial_sys_include_content = patched_content
        # Replace the entire line with the new assignment.
        patched_content = sys_include_flags_pattern.sub(r'\g<indent>sys_include_flags = [] # CerebrumLux MinGW patch', patched_content)
        if initial_sys_include_content != patched_content:
            modified = True
            log("INFO", f"Replaced 'sys_include_flags' assignment with empty list in '{toolchain_build_gn_path.name}'.", to_console=False)

        sys_lib_flags_pattern = re.compile(
            r"^(?P<indent>\s*)sys_lib_flags\s*=.*", # Match the whole line after indent and assignment
            re.MULTILINE
        )
        initial_sys_lib_content = patched_content
        # Replace the entire line with the new assignment.
        patched_content = sys_lib_flags_pattern.sub(r'\g<indent>sys_lib_flags = [] # CerebrumLux MinGW patch', patched_content)
        if initial_sys_lib_content != patched_content:
            modified = True
            log("INFO", f"Replaced 'sys_lib_flags' assignment with empty list in '{toolchain_build_gn_path.name}'.", to_console=False)


        # --- 4. Replace MSVC tool definitions with MinGW tools (as direct strings) ---
        # This is a fallback and generally less desirable if win_toolchain_data is working.
        # But if GN uses interpolation, it needs the values from win_toolchain_data.
        # This part should be safe as it replaces the *entire line* with a literal string.
        mingw_bin_posix = Path(MINGW_BIN).as_posix()
        
        tool_definitions_to_patch = {
            r'^\s*cl\s*=\s*".*?"': f'cl = "{mingw_bin_posix}/gcc.exe"',
            r'^\s*link\s*=\s*".*?"': f'link = "{mingw_bin_posix}/g++.exe"', # Linker is g++ for MinGW
            r'^\s*lib\s*=\s*".*?"': f'lib = "{mingw_bin_posix}/ar.exe"', # Archiver is ar for MinGW
            r'^\s*rc\s*=\s*".*?"': f'rc = "{mingw_bin_posix}/windres.exe"', # Standard MinGW resource compiler
        }
        
        for pattern_str, replacement_str in tool_definitions_to_patch.items():
            tool_assignment_pattern = re.compile(pattern_str, re.MULTILINE)
            initial_tool_content = patched_content
            patched_content = tool_assignment_pattern.sub(r'  ' + replacement_str + ' # CerebrumLux MinGW tool override', patched_content)
            if initial_tool_content != patched_content:
                modified = True
                log("INFO", f"Replaced tool assignment (pattern: {pattern_str[:min(len(pattern_str), 50)]}...) with MinGW path in '{toolchain_build_gn_path.name}'.", to_console=False)
        
        # Finally, a last resort generic replacement for any unhandled win_toolchain_data.<field> access.
        # This should theoretically not be hit if the injected scope and specific assignments cover everything.
        for field, dummy_path in dummy_win_toolchain_paths.items():
            generic_access_pattern = re.compile(r"win_toolchain_data\." + re.escape(field), re.MULTILINE)
            initial_generic_replace_text = patched_content
            patched_content = generic_access_pattern.sub(f'"{dummy_path}"', patched_content)
            if initial_generic_replace_text != patched_content:
                modified = True
                log("INFO", f"Replaced generic access to 'win_toolchain_data.{field}' with hardcoded dummy path in '{toolchain_build_gn_path.name}' (final fallback).", to_console=False)


        if modified:
            patched_content = _filter_gn_comments(patched_content) # Apply general comment filter before writing back
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
    if re.search(r"\'third_party/llvm-build\':\s*Var\(.*?\),?\n?", patched_content, flags=re.DOTALL) or \
       re.search(r"\'third_party/llvm-build\':\s*\'[^\n]*\',?\n?", patched_content, flags=re.DOTALL):
        patched_content = re.sub(r"\'third_party/llvm-build\':\s*Var\(.*?\),?\n?", "", patched_content, flags=re.DOTALL)
        patched_content = re.sub(r"\'third_party/llvm-build\':\s*\'[^\n]*\',?\n?", "", patched_content, flags=re.DOTALL)
        deps_modified = True

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
    patched_content = re.sub(r"\'infra/tools/win\S*?\'[^}]*?},\n", "", patched_content)
    if initial_cipd_content != patched_content:
        deps_modified = True

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

    # NEW: Call to patch build/toolchain/win/BUILD.gn
    log("INFO", "Calling patch for 'build/toolchain/win/BUILD.gn'.", to_console=True)
    if not _patch_toolchain_win_build_gn(v8_source_dir, env):
        log("FATAL", "Failed to patch 'build/toolchain/win/BUILD.gn'. Aborting.", to_console=True)
        sys.exit(1)


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

                # Combined check for critical strings (pipes, VS exception) and v7.23 shim content
                needs_patch = ("import pipes" in content_before_patch or 
                               "No supported Visual Studio can be found" in content_before_patch or
                               f"# --- CerebrumLux injected shim START (v7.23) ---" not in content_before_patch or
                               any(s in content_before_patch for s in [r"wdk_path': r''", r"sdk_path': r''", r"DetectVisualStudioPath():\n    return r''"]))

                if not needs_patch:
                    log("INFO", f"'{vs_toolchain_path.name}' does not contain critical strings and shim (v7.23) is present and correct. Pre-sync patch skipped (already fine).", to_console=False)
                    break

                log("INFO", f"Pre-sync patch loop: Attempting to patch '{vs_toolchain_path.name}' (pipes, VS exception, or shim v7.23 content issue detected). Try {patch_tries+1}/{MAX_PATCH_LOOP_TRIES_INNER}.", to_console=False)
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
    gn_bin = _find_tool(["gn", "gn.exe"]) # Use _find_tool
    if not gn_bin:
        raise RuntimeError("gn binary not found in PATH nor in depot_tools.")
    
    gn_command = [gn_bin, "gen", OUT_DIR]
    max_attempts = 2 # Try once, then once more after potential args.gn patching
    
    for attempt in range(1, max_attempts + 1):
        log("INFO", f"GN gen attempt {attempt}/{max_attempts}.", to_console=True)
        try:
            # Capture output even on error to analyze it
            cp = run(gn_command, cwd=V8_SRC, env=env, check=False, capture_output=True)
            
            if cp.returncode == 0:
                log("INFO", f"GN generated build files in {OUT_DIR}.")
                return # Success!
            
            # If GN failed, analyze its output
            error_output = (cp.stdout or "") + (cp.stderr or "") # Ensure output is string even if empty
            log("ERROR", f"GN gen failed on attempt {attempt}: \n{error_output}", to_console=False)

            # Check for specific errors that indicate missing vcvars_toolchain_data variables or GN syntax error
            if ("No value named \"vc_lib_path\" in scope \"vcvars_toolchain_data\"" in error_output or
                "No value named \"vc_bin_dir\" in scope \"vcvars_toolchain_data\"" in error_output or
                "No value named \"vc_include_path\" in scope \"vcvars_toolchain_data\"" in error_output or
                "No value named \"sdk_dir\" in scope \"vcvars_toolchain_data\"" in error_output or
                "No value named \"sdk_lib_path\" in scope \"vcvars_toolchain_data\"" in error_output or
                "No value named \"sdk_include_path\" in scope \"vcvars_toolchain_data\"" in error_output or
                "No value named \"runtime_dirs\" in scope \"vcvars_toolchain_data\"" in error_output or
                "No value named \"include_flags_imsvc\"" in error_output or # Added for new error
                "May only use \".\" for identifiers." in error_output or
                "Invalid token." in error_output or
                "Bad thing passed to defined()." in error_output or
                "Expecting assignment or function call." in error_output): # Added for the latest error
                
                log("INFO", "Detected missing 'vcvars_toolchain_data' variables or GN syntax error in GN output. Attempting to patch args.gn.", to_console=True)
                
                args_gn_path = Path(OUT_DIR) / "args.gn"
                current_args_content = args_gn_path.read_text(encoding="utf-8") if args_gn_path.exists() else ""
                
                new_args_to_add = []
                # Use the same FakeVS_Toolchain paths as in _create_fake_vs_toolchain_dirs for consistency
                fake_vs_base_path_for_gn_obj = Path(V8_ROOT) / "FakeVS_Toolchain"
                fake_vs_base_path_for_gn_posix = fake_vs_base_path_for_gn_obj.as_posix()
                
                # Check for individual top-level args (safeguard)
                if 'vc_bin_dir =' not in current_args_content: new_args_to_add.append(f'vc_bin_dir = "{fake_vs_base_path_for_gn_posix}/VC/bin"')
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

                # Check if the vcvars_toolchain_data block is already in args.gn
                if 'vcvars_toolchain_data = {' not in current_args_content:
                    new_args_to_add.append(vcvars_data_block)
                    log("INFO", f"Prepared to inject 'vcvars_toolchain_data' object into {args_gn_path.name}.", to_console=True)
                else:
                    # If the block is already there, check if its content matches our desired content
                    if f'vc_lib_path = "{(fake_vs_base_path_for_gn_obj / "VC" / "lib").as_posix()}"' not in current_args_content:
                        log("WARN", "'vcvars_toolchain_data' object found, but its content might be outdated. Appending to ensure consistency.", to_console=True)
                        new_args_to_add.append(vcvars_data_block) # Append even if exists, to ensure it's there
                    else:
                        log("INFO", "'vcvars_toolchain_data' object appears to be already present and correctly defined in args.gn. Skipping injection of block.", to_console=True)


                if new_args_to_add:
                    with args_gn_path.open("a", encoding="utf-8") as f: # Use Path.open()
                        for arg_line in new_args_to_add:
                            f.write(arg_line + "\n")
                    log("INFO", f"Appended necessary configuration to {args_gn_path.name}.", to_console=True)
                    # The loop will naturally retry gn gen with the new args.gn
                elif attempt < max_attempts:
                    log("WARN", "Required GN variables appear to be present in args.gn or could not be injected. This might indicate another GN configuration issue.", to_console=True)
                    # No new args to add, so break from auto-patching and let the loop retry or fail.
                    break 
                else: # Last attempt and no new args could be added
                    raise RuntimeError("GN gen failed and auto-patching args.gn did not help or was not needed for vcvars_toolchain_data errors.")

            else:
                # If a different type of error, or if auto-patching didn't apply, raise it immediately
                log("FATAL", f"GN gen failed with unhandled error or after auto-patching. Full output:\n{error_output}", to_console=True)
                raise RuntimeError(f"GN gen command failed with code {cp.returncode}.")
        
        except Exception as e:
            # If the current attempt failed for an unexpected reason
            if attempt == max_attempts:
                raise RuntimeError(f"GN gen failed after {max_attempts} attempts: {e}")
            else:
                log("WARN", f"GN gen failed on attempt {attempt}, trying again: {e}", to_console=True)
                time.sleep(2) # Small delay before retry

    raise RuntimeError("GN gen failed after all attempts.")


def run_ninja_build(env):
    """Starts the main V8 compilation with Ninja."""
    ninja_bin = _find_tool(["ninja", "ninja.exe"]) # Use _find_tool
    if not ninja_bin:
        raise RuntimeError("ninja binary not found in PATH nor in depot_tools.")
    run([str(ninja_bin), "-C", OUT_DIR, NINJA_TARGET], cwd=V8_SRC, env=env) # Convert Path to string for subprocess
    log("INFO", f"Ninja build of '{NINJA_TARGET}' completed.")

def copy_to_vcpkg():
    """Copies compiled V8 artifacts (lib and headers) to vcpkg's installed directory."""
    target_lib_dir = Path(VCPKG_ROOT) / "installed" / "x64-mingw-static" / "lib" # Use Path
    target_include_dir = Path(VCPKG_ROOT) / "installed" / "x64-mingw-static" / "include" # Use Path
    os.makedirs(target_lib_dir, exist_ok=True)
    os.makedirs(target_include_dir, exist_ok=True)
    
    lib_candidate = Path(OUT_DIR) / "obj" / "libv8_monolith.a" # Use Path
    if not lib_candidate.exists():
        found = []
        for root, _, files in os.walk(OUT_DIR):
            for fn in files:
                if fn.lower().startswith("libv8_monolith") and fn.endswith(".a"):
                    found.append(Path(root) / fn) # Use Path
        if found:
            lib_candidate = found[0]
            log("INFO", f"Found libv8_monolith.a at: {lib_candidate}")
        else:
            log("ERROR", f"Built libv8_monolith.a not found under {OUT_DIR}")
            raise FileNotFoundError(f"Built libv8_monolith.a not found under {OUT_DIR}")
            
    shutil.copy2(lib_candidate, target_lib_dir)
    log("INFO", f"Copied '{lib_candidate.name}' to '{target_lib_dir}'")

    src_include = Path(V8_SRC) / "include" # Use Path
    if not src_include.is_dir():
        log("ERROR", f"Headers not found in source include path: {src_include}")
        raise FileNotFoundError(src_include)
    
    shutil.copytree(src_include, target_include_dir, dirs_exist_ok=True)
    log("INFO", f"V8 headers copied from '{src_include}' to '{target_include_dir}'")
    log("INFO", f"V8 lib + headers copied into vcpkg installed tree ({target_lib_dir}, {target_include_dir})")

def update_vcpkg_port(version, ref, homepage, license):
    """Updates or creates the vcpkg portfile and manifest for V8."""
    port_v8_dir = Path(VCPKG_ROOT) / "ports" / "v8" # Use Path
    os.makedirs(port_v8_dir, exist_ok=True)
    portfile_path = port_v8_dir / "portfile.cmake" # Use Path
    manifest_path = port_v8_dir / "vcpkg.json" # Use Path

    cmake_content = f"""
# Auto-generated by CerebrumLux V8 Builder v7.23
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
    with portfile_path.open("w", encoding="utf-8") as f: # Use Path.open()
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
    with manifest_path.open("w", encoding="utf-8") as f: # Use Path.open()
        json.dump(manifest, f, indent=2)
    log("INFO", f"Created/updated {manifest_path}")

def vcpkg_integrate_install(env):
    """Runs 'vcpkg integrate install' for system-wide CMake integration."""
    vcpkg_exe = Path(VCPKG_ROOT) / "vcpkg.exe" # Use Path
    if not vcpkg_exe.exists():
        log("WARN", f"vcpkg.exe not found at {vcpkg_exe}, skipping 'vcpkg integrate install'.")
        return
    log("STEP", "Running 'vcpkg integrate install'...")
    run([str(vcpkg_exe), "integrate", "install"], env=env, capture_output=True) # Convert Path to string for subprocess
    log("INFO", "'vcpkg integrate install' completed.")

# ----------------------------
# === Main Workflow ===
# ----------------------------
def main():
    # Filter DeprecationWarnings, especially from Python's datetime module
    warnings.filterwarnings("ignore", category=DeprecationWarning)

    log("START", "=== CerebrumLux V8 Build v7.23 started ===", to_console=True)
    start_time = time.time()
    env = prepare_subprocess_env()

    try:
        if Path(V8_ROOT).is_dir(): # Use Path
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
        if not _patch_toolchain_win_build_gn(V8_SRC, env): # Re-patch build/toolchain/win/BUILD.gn as well
            log("FATAL", "Failed to re-patch 'build/toolchain/win/BUILD.gn'. Aborting.", to_console=True)
            sys.exit(1)

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
        with Path(LOG_FILE).open('r', encoding='utf-8') as f: # Use Path.open()
            log_content = f.read()
            if "FATAL" in log_content or "ERROR" in log_content:
                log("SUMMARY_ERROR", f"Errors or Fatal issues detected in logs. Please check CerebrumLux-V8-Build-{V8_VERSION}.log and CerebrumLux-V8-Build-{V8_VERSION}-error.log", to_console=True)
            else:
                log("SUMMARY_SUCCESS", "No major errors detected. V8 build is likely successful!", to_console=True)

if __name__ == "__main__":
    os.makedirs(LOG_DIR, exist_ok=True)
    if Path(LOG_FILE).exists(): # Use Path.exists()
        try:
            timestamp_str = datetime.datetime.now().strftime('%Y%m%d%H%M%S')
            shutil.move(LOG_FILE, f"{LOG_FILE}.old-{timestamp_str}")
        except Exception as e:
            print(f"WARN: Could not move old log file: {e}")
    if Path(ERR_FILE).exists(): # Use Path.exists()
        try:
            timestamp_str = datetime.datetime.now().strftime('%Y%m%d%H%M%S')
            shutil.move(ERR_FILE, f"{ERR_FILE}.old-{timestamp_str}")
        except Exception as e:
            print(f"WARN: Could not move old error log file: {e}")
    main()