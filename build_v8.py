#!/usr/bin/env python3
"""
CerebrumLux V8 Build Automation v7.6 (Final Robust MinGW Build - Incorporating all feedback)
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
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(line + "\n")
    if level in ("ERROR", "FATAL"):
        with open(ERR_FILE, "a", encoding="utf-8") as ef:
            f.write(line + "\n") # Typo fix: was ef.write
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
    path = os.path.join(root_dir, ".gclient")
    with open(path, "w", encoding="utf-8") as f:
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
            "# --- CerebrumLux injected shim START (v7.5) ---\n" # Updated shim version marker
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
        if f"# --- CerebrumLux injected shim START (v7.5) ---" not in text: 
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
            if f"# --- CerebrumLux injected shim START (v7.5) ---" not in current_content:
                log("ERROR", f"'{vs_toolchain_path.name}' does not contain the CerebrumLux shim (v7.5) after expected patching. Patching is NOT sticking.", to_console=False)
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
                 log("ERROR", f"'{vs_toolchain_path.name}' shim contains empty paths (r''). Patching is NOT sticking (v7.5 content missing).", to_console=False)
                 return False
            
            return True

    except Exception as e:
        log("ERROR", f"Failed to apply aggressive patch logic to '{vs_toolchain_path.name}': {e}", to_console=False)
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

    log("INFO", f"Patching '{setup_toolchain_path.name}' to completely replace _LoadToolchainEnv and create dummy paths.", to_console=True)
    try:
        content = setup_toolchain_path.read_text(encoding="utf-8")
        patched_content = content
        modified = False

        # FIX (v7.5): Completely replace _LoadToolchainEnv to bypass vcvarsall.bat check.
        # This is more robust than trying to patch inside the function.
        # FIX (v7.6): Ensure the replacement body includes all expected keys and creates dummy directories.
        pattern_load_toolchain_env = re.compile(
            r"^(def\s+_LoadToolchainEnv\([^)]*\):(?:\n\s+.*)*?)(?=\n^def|\Z)", # Matches the entire function body
            re.MULTILINE | re.DOTALL
        )
        if pattern_load_toolchain_env.search(patched_content):
            # Define dummy paths relative to V8_ROOT to avoid hardcoding C:\FakeVS directly in the patch function body.
            # This ensures they are created *within* the V8 build environment if needed for checks.
            fake_vs_root = Path(V8_ROOT) / "FakeVS_Toolchain"
            fake_vc_bin_dir = fake_vs_root / "VC" / "bin"
            fake_vc_lib_path = fake_vs_root / "VC" / "lib"
            fake_vc_include_path = fake_vs_root / "VC" / "include"
            fake_sdk_dir = fake_vs_root / "SDK"
            fake_sdk_lib_path = fake_sdk_dir / "lib"
            fake_sdk_include_path = fake_sdk_dir / "include"
            fake_runtime_dirs = fake_vs_root / "redist"

            # Create dummy directories if they don't exist
            # Note: This will be executed by the python script when it runs main().
            os.makedirs(fake_vc_bin_dir, exist_ok=True)
            os.makedirs(fake_vc_lib_path, exist_ok=True)
            os.makedirs(fake_vc_include_path, exist_ok=True)
            os.makedirs(fake_sdk_dir, exist_ok=True)
            os.makedirs(fake_sdk_lib_path, exist_ok=True)
            os.makedirs(fake_sdk_include_path, exist_ok=True)
            os.makedirs(fake_runtime_dirs, exist_ok=True)

            # Use forward slashes for paths in the string for consistency with GN
            replacement_func_body = f"""def _LoadToolchainEnv(cpu, toolchain_root, win_sdk_path, target_store):
    # CerebrumLux MinGW patch: Bypassed vcvarsall.bat check and returning a dummy env.
    # The actual toolchain paths are provided in args.gn.
    # Dummy directories created by build_v8.py if not already present.
    return {{
        "vc_bin_dir": "{str(fake_vc_bin_dir).replace('\\', '/')}",
        "vc_lib_path": "{str(fake_vc_lib_path).replace('\\', '/')}",
        "vc_include_path": "{str(fake_vc_include_path).replace('\\', '/')}",
        "sdk_dir": "{str(fake_sdk_dir).replace('\\', '/')}",
        "sdk_lib_path": "{str(fake_sdk_lib_path).replace('\\', '/')}",
        "sdk_include_path": "{str(fake_sdk_include_path).replace('\\', '/')}",
        "runtime_dirs": "{str(fake_runtime_dirs).replace('\\', '/')}"
    }}
"""
            patched_content = pattern_load_toolchain_env.sub(
                replacement_func_body,
                patched_content
            )
            modified = True
            log("INFO", f"Replaced '_LoadToolchainEnv' function body in '{setup_toolchain_path.name}' with full dummy environment.", to_console=False)
        else:
            # Fallback for older structures (should not be hit with current _LoadToolchainEnv replacement)
            # Patch _DetectVisualStudioPath
            pattern_detect_vs_path = re.compile(r"^(?P<indent>\s*)return\s+vs_toolchain\.DetectVisualStudioPath\(\)\s*$", re.MULTILINE)
            if pattern_detect_vs_path.search(patched_content):
                patched_content = pattern_detect_vs_path.sub(
                    r"\g<indent>return r'C:\\FakeVS' # CerebrumLux MinGW patch",
                    patched_content
                )
                modified = True
                log("INFO", f"Patched '_DetectVisualStudioPath' call in '{setup_toolchain_path.name}' (fallback).", to_console=False)
            
            # Patch _GetVisualStudioVersion
            pattern_get_vs_version = re.compile(r"^(?P<indent>\s*)return\s+vs_toolchain\.GetVisualStudioVersion\(\)\s*$", re.MULTILINE)
            if pattern_get_vs_version.search(patched_content):
                patched_content = pattern_get_vs_version.sub(
                    r"\g<indent>return '16.0' # CerebrumLux MinGW patch",
                    patched_content
                )
                modified = True
                log("INFO", f"Patched '_GetVisualStudioVersion' call in '{setup_toolchain_path.name}' (fallback).", to_console=False)

        if modified:
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


def patch_v8_deps_for_mingw(v8_source_dir: str, env: dict):
    """
    Patches the DEPS file to remove problematic dependencies for MinGW build.
    Also calls to patch the 'build/dotfile_settings.gni', 'visual_studio_version.gni'
    and 'setup_toolchain.py' files.
    """
    deps_path = os.path.join(v8_source_dir, "DEPS")
    if not os.path.exists(deps_path):
        log("WARN", f"DEPS file not found at {deps_path}. Skipping DEPS patch.", to_console=True)
        return

    log("INFO", f"Patching DEPS file at {deps_path} for MinGW compatibility.", to_console=True)
    
    with open(deps_path, 'r', encoding='utf-8') as f:
        content = f.read()

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
        with open(deps_path, 'w', encoding="utf-8") as f:
            f.write(patched_content)
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

                # Combined check for critical strings (pipes, VS exception) and v7.5 shim content
                needs_patch = ("import pipes" in content_before_patch or 
                               "No supported Visual Studio can be found" in content_before_patch or
                               f"# --- CerebrumLux injected shim START (v7.5) ---" not in content_before_patch or
                               any(s in content_before_patch for s in [r"wdk_path': r''", r"sdk_path': r''", r"DetectVisualStudioPath():\n    return r''"]))

                if not needs_patch:
                    log("INFO", f"'{vs_toolchain_path.name}' does not contain critical strings and shim (v7.5) is present and correct. Pre-sync patch skipped (already fine).", to_console=False)
                    break

                log("INFO", f"Pre-sync patch loop: Attempting to patch '{vs_toolchain_path.name}' (pipes, VS exception, or shim v7.5 content issue detected). Try {patch_tries+1}/{MAX_PATCH_LOOP_TRIES_INNER}.", to_console=False)
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
        p = os.path.join(DEPOT_TOOLS, n)
        if os.path.exists(p):
            log("DEBUG", f"Found tool '{n}' in DEPOT_TOOLS: {p}", to_console=False)
            return p
    
    log("ERROR", f"Tool not found among candidates: {names}", to_console=False)
    return None

def ensure_depot_tools(env):
    """Ensures depot_tools is cloned and functional."""
    if os.path.isdir(DEPOT_TOOLS):
        log("INFO", f"depot_tools exists at {DEPOT_TOOLS}")
        return
    log("STEP", f"Cloning depot_tools into {DEPOT_TOOLS}")
    os.makedirs(os.path.dirname(DEPOT_TOOLS), exist_ok=True)
    git_clone_with_retry(env, DEPOT_TOOLS, "https://chromium.googlesource.com/chromium/tools/depot_tools.git")
    log("INFO", "depot_tools cloned.")

def write_args_gn(out_dir):
    """Writes the args.gn file for the GN build configuration."""
    os.makedirs(out_dir, exist_ok=True)
    mingw_for = MINGW_BIN.replace("\\", "/")
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
    p = os.path.join(out_dir, "args.gn")
    with open(p, "w", encoding="utf-8") as f:
        f.write(args_content)
    log("INFO", f"args.gn written to {p}")

def run_gn_gen(env):
    """Generates Ninja build files using GN."""
    gn_bin = _find_tool(["gn", "gn.exe"]) # Use _find_tool
    if not gn_bin:
        raise RuntimeError("gn binary not found in PATH nor in depot_tools.")
    
    run([gn_bin, "gen", OUT_DIR], cwd=V8_SRC, env=env)
    log("INFO", f"GN generated build files in {OUT_DIR}.")

def run_ninja_build(env):
    """Starts the main V8 compilation with Ninja."""
    ninja_bin = _find_tool(["ninja", "ninja.exe"]) # Use _find_tool
    if not ninja_bin:
        raise RuntimeError("ninja binary not found in PATH nor in depot_tools.")
    run([ninja_bin, "-C", OUT_DIR, NINJA_TARGET], cwd=V8_SRC, env=env)
    log("INFO", f"Ninja build of '{NINJA_TARGET}' completed.")

def copy_to_vcpkg():
    """Copies compiled V8 artifacts (lib and headers) to vcpkg's installed directory."""
    target_lib_dir = os.path.join(VCPKG_ROOT, "installed", "x64-mingw-static", "lib")
    target_include_dir = os.path.join(VCPKG_ROOT, "installed", "x64-mingw-static", "include")
    os.makedirs(target_lib_dir, exist_ok=True)
    os.makedirs(target_include_dir, exist_ok=True)
    
    lib_candidate = os.path.join(OUT_DIR, "obj", "libv8_monolith.a")
    if not os.path.exists(lib_candidate):
        found = []
        for root, _, files in os.walk(OUT_DIR):
            for fn in files:
                if fn.lower().startswith("libv8_monolith") and fn.endswith(".a"):
                    found.append(os.path.join(root, fn))
        if found:
            lib_candidate = found[0]
            log("INFO", f"Found libv8_monolith.a at: {lib_candidate}")
        else:
            log("ERROR", f"Built libv8_monolith.a not found under {OUT_DIR}")
            raise FileNotFoundError(f"Built libv8_monolith.a not found under {OUT_DIR}")
            
    shutil.copy2(lib_candidate, target_lib_dir)
    log("INFO", f"Copied '{os.path.basename(lib_candidate)}' to '{target_lib_dir}'")

    src_include = os.path.join(V8_SRC, "include")
    if not os.path.isdir(src_include):
        log("ERROR", f"Headers not found in source include path: {src_include}")
        raise FileNotFoundError(src_include)
    
    shutil.copytree(src_include, target_include_dir, dirs_exist_ok=True)
    log("INFO", f"V8 headers copied from '{src_include}' to '{target_include_dir}'")
    log("INFO", f"V8 lib + headers copied into vcpkg installed tree ({target_lib_dir}, {target_include_dir})")

def update_vcpkg_port(version, ref, homepage, license):
    """Updates or creates the vcpkg portfile and manifest for V8."""
    port_v8_dir = os.path.join(VCPKG_ROOT, "ports", "v8")
    os.makedirs(port_v8_dir, exist_ok=True)
    portfile_path = os.path.join(port_v8_dir, "portfile.cmake")
    manifest_path = os.path.join(port_v8_dir, "vcpkg.json")

    cmake_content = f"""
# Auto-generated by CerebrumLux V8 Builder v7.6
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
file(COPY "{os.path.join(VCPKG_ROOT, 'installed', 'x64-mingw-static', 'lib', 'libv8_monolith.a').replace('\\', '/')}" DESTINATION ${{CURRENT_PACKAGES_DIR}}/lib)

# Copy headers - already handled by direct copy_to_vcpkg.
# Use a more explicit path for V8_ROOT to avoid issues with CMake variable scope.
file(GLOB_RECURSE V8_HEADERS_TO_COPY "{V8_ROOT.replace('\\', '/')}/v8/include/*.h" "{V8_ROOT.replace('\\', '/')}/v8/include/*.hpp")
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
    vcpkg_exe = os.path.join(VCPKG_ROOT, "vcpkg.exe")
    if not os.path.exists(vcpkg_exe):
        log("WARN", f"vcpkg.exe not found at {vcpkg_exe}, skipping 'vcpkg integrate install'.")
        return
    log("STEP", "Running 'vcpkg integrate install'...")
    run([vcpkg_exe, "integrate", "install"], env=env, capture_output=True)
    log("INFO", "'vcpkg integrate install' completed.")

# ----------------------------
# === Main Workflow ===
# ----------------------------
def main():
    log("START", "=== CerebrumLux V8 Build v7.6 started ===", to_console=True)
    start_time = time.time()
    env = prepare_subprocess_env()

    try:
        if os.path.isdir(V8_ROOT):
            log("INFO", f"V8_ROOT '{V8_ROOT}' exists. Attempting incremental update. Manual deletion required for full fresh start.", to_console=True)
        else:
            log("INFO", f"Creating V8_ROOT for fresh start: {V8_ROOT}", to_console=True)
        os.makedirs(V8_ROOT, exist_ok=True)

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

        log("STEP", "Re-patching .gni and setup_toolchain.py files after sync to ensure changes persist.")
        # The patching functions contain logic to check if patches are already applied
        # and re-apply if needed, so calling them here is safe and ensures persistence.
        if not _patch_dotfile_settings_gni(V8_SRC, env):
            log("FATAL", "Failed to re-patch 'build/dotfile_settings.gni' after sync. Aborting.", to_console=True)
            sys.exit(1)
        if not _patch_visual_studio_version_gni(V8_SRC, env):
            log("FATAL", "Failed to re-patch 'build/config/win/visual_studio_version.gni'. Aborting.", to_console=True)
            sys.exit(1)
        if not _patch_setup_toolchain_py(V8_SRC, env):
            log("FATAL", "Failed to re-patch 'build/toolchain/win/setup_toolchain.py' after sync. Aborting.", to_console=True)
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
        with open(LOG_FILE, 'r', encoding='utf-8') as f:
            log_content = f.read()
            if "FATAL" in log_content or "ERROR" in log_content:
                log("SUMMARY_ERROR", f"Errors or Fatal issues detected in logs. Please check CerebrumLux-V8-Build-{V8_VERSION}.log and CerebrumLux-V8-Build-{V8_VERSION}-error.log", to_console=True)
            else:
                log("SUMMARY_SUCCESS", "No major errors detected. V8 build is likely successful!", to_console=True)

if __name__ == "__main__":
    os.makedirs(LOG_DIR, exist_ok=True)
    if os.path.exists(LOG_FILE):
        try:
            timestamp_str = datetime.datetime.now().strftime('%Y%m%d%H%M%S')
            shutil.move(LOG_FILE, f"{LOG_FILE}.old-{timestamp_str}")
        except Exception as e:
            print(f"WARN: Could not move old log file: {e}")
    if os.path.exists(ERR_FILE):
        try:
            timestamp_str = datetime.datetime.now().strftime('%Y%m%d%H%M%S')
            shutil.move(ERR_FILE, f"{ERR_FILE}.old-{timestamp_str}")
        except Exception as e:
            print(f"WARN: Could not move old error log file: {e}")
    main()