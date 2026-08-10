import os
import re
import subprocess
import shutil
import zipfile

PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_DIR = os.path.dirname(PROJECT_DIR)  # C:\Users\magictwin\Documents\Projects
DESKTOP_DIR = os.path.expanduser(r"~\Desktop")

MANIFEST_PATH = os.path.join(PROJECT_DIR, "blender_manifest.toml")
INIT_PATH = os.path.join(PROJECT_DIR, "__init__.py")

BLENDER_PATH = r"C:\Program Files\Blender Foundation\Blender 4.3\blender.exe"

def get_current_version():
    with open(MANIFEST_PATH, "r", encoding="utf-8") as f:
        content = f.read()
    match = re.search(r'^version\s*=\s*"([^"]+)"', content, re.MULTILINE)
    if match:
        return match.group(1)
    return "5.2.5"

def increment_version(version_str):
    parts = version_str.split(".")
    if len(parts) == 3:
        parts[2] = str(int(parts[2]) + 1)
    elif len(parts) > 3:
        parts[-1] = str(int(parts[-1]) + 1)
    else:
        parts.append("1")
    return ".".join(parts)

def update_manifest_and_init(new_version):
    # Update blender_manifest.toml
    with open(MANIFEST_PATH, "r", encoding="utf-8") as f:
        manifest = f.read()
    manifest = re.sub(r'^version\s*=\s*"[^"]+"', f'version = "{new_version}"', manifest, flags=re.MULTILINE)
    with open(MANIFEST_PATH, "w", encoding="utf-8") as f:
        f.write(manifest)
    print(f"Updated blender_manifest.toml version to: {new_version}")

    # Update __init__.py CATS_VERSION
    if os.path.exists(INIT_PATH):
        with open(INIT_PATH, "r", encoding="utf-8") as f:
            init_code = f.read()
        init_code = re.sub(r'CATS_VERSION\s*=\s*"[^"]+"', f'CATS_VERSION = "{new_version}.0"', init_code)
        with open(INIT_PATH, "w", encoding="utf-8") as f:
            f.write(init_code)
        print(f"Updated __init__.py version to: {new_version}.0")

def build_extension(version_str):
    zip_name = f"Toasters-Blender-Plugin-{version_str}.zip"
    target_path = os.path.join(OUTPUT_DIR, zip_name)
    desktop_path = os.path.join(DESKTOP_DIR, zip_name)

    if os.path.exists(BLENDER_PATH):
        cmd = [
            BLENDER_PATH,
            "--background",
            "--factory-startup",
            "--command", "extension", "build",
            "--source-dir", PROJECT_DIR,
            "--output-filepath", target_path
        ]
        print(f"Building extension package via Blender CLI...")
        res = subprocess.run(cmd, capture_output=True, text=True)
        if res.returncode == 0:
            print(f"Blender extension build succeeded: {target_path}")
        else:
            print(f"Blender CLI failed, falling back to python zip: {res.stderr}")
            fallback_zip(target_path)
    else:
        fallback_zip(target_path)

    if os.path.exists(target_path):
        try:
            shutil.copy2(target_path, desktop_path)
            print(f"Copied package to Desktop: {desktop_path}")
        except Exception as e:
            print(f"Could not copy to Desktop: {e}")

    return target_path

def fallback_zip(target_path):
    exclude_dirs = {".venv", ".git", ".idea", "__pycache__", "build", "dist"}
    exclude_extensions = {".pyc", ".zip", ".tmp"}

    with zipfile.ZipFile(target_path, "w", zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk(PROJECT_DIR):
            dirs[:] = [d for d in dirs if d not in exclude_dirs]
            for file in files:
                if any(file.endswith(ext) for ext in exclude_extensions):
                    continue
                if file == "build_plugin.py":
                    continue
                full_path = os.path.join(root, file)
                rel_path = os.path.relpath(full_path, PROJECT_DIR)
                zipf.write(full_path, rel_path)

if __name__ == "__main__":
    current = get_current_version()
    new_ver = increment_version(current)
    update_manifest_and_init(new_ver)
    build_extension(new_ver)
