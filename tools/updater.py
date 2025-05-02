import requests
import subprocess
import tempfile
import os
import sys
import threading

REPO_OWNER, REPO_NAME = "Overblend", "Overblend"
VERSION_LINK = "https://overblend.org/version"
VERSION_PATH = "version.txt"

# Module‐level downloader reference
global _download_manager
_download_manager = None

class DownloadManager:
    """
    Manages downloading a file with progress tracking.
    """
    def __init__(self, url, dest_path, chunk_size=8192):
        self.url = url
        self.dest_path = dest_path
        self.chunk_size = chunk_size
        self.total = 0
        self.downloaded = 0
        self.percent = 0
        self._lock = threading.Lock()

    def download(self):
        response = requests.get(self.url, stream=True)
        response.raise_for_status()
        self.total = int(response.headers.get('content-length', 0))
        self.downloaded = 0
        self.percent = 0

        with open(self.dest_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=self.chunk_size):
                if not chunk:
                    continue
                f.write(chunk)
                with self._lock:
                    self.downloaded += len(chunk)
                    if self.total:
                        self.percent = int(self.downloaded * 100 / self.total)

    def get_progress(self):
        """
        Returns the current download progress as an integer percentage (0-100).
        """
        with self._lock:
            return self.percent


def get_download_progress():
    """
    Returns the download progress of the current download, or None if no download in progress.
    """
    if _download_manager is None:
        return None
    return _download_manager.get_progress()


def get_latest_update():
    return requests.get(VERSION_LINK).text.strip()


def needs_update():
    try:
        with open(VERSION_PATH, 'r') as f:
            current_version = f.read().strip()
        latest_version = get_latest_update()
        return current_version != latest_version
    except FileNotFoundError:
        # Si le fichier de version n'existe pas, on considère qu'une mise à jour est nécessaire
        return True
    except Exception as e:
        print(f"Error checking update: {e}")
        return False


def get_latest_version(repo_owner=REPO_OWNER, repo_name=REPO_NAME):
    """
    Fetches the latest GitHub release, downloads the .exe (or fallback)
    with progress tracking, and executes it. Returns the release tag.
    """
    global _download_manager

    try:
        # Fetch release metadata
        api_url = f"https://api.github.com/repos/{repo_owner}/{repo_name}/releases/latest"
        resp = requests.get(api_url)
        resp.raise_for_status()
        release = resp.json()
        tag = release.get('tag_name')

        # Select asset
        assets = release.get('assets', [])
        download_url = None
        asset_name = None
        for asset in assets:
            if asset['name'].endswith('.exe'):
                download_url = asset['browser_download_url']
                asset_name = asset['name']
                break
        if download_url is None:
            for asset in assets:
                if asset['name'].endswith('.zip'):
                    download_url = asset['browser_download_url']
                    asset_name = asset['name']
                    break
        if download_url is None:
            download_url = release.get('zipball_url')
            asset_name = f"{repo_name}-{tag}.zip"

        # Prepare download
        tmp_dir = tempfile.mkdtemp(prefix='update_')
        dest = os.path.join(tmp_dir, asset_name)
        _download_manager = DownloadManager(download_url, dest)

        # Start download (blocking)
        print(f"Starting download of {asset_name} (release {tag})...")
        _download_manager.download()
        
        # Set progress to 100% at completion to ensure UI gets updated correctly
        _download_manager.percent = 100

        # Determine executable path
        if asset_name.endswith('.exe'):
            exec_path = dest
        else:
            extract_dir = os.path.join(tmp_dir, 'extracted')
            os.makedirs(extract_dir, exist_ok=True)
            import zipfile
            with zipfile.ZipFile(dest, 'r') as z:
                z.extractall(extract_dir)
            exec_path = None
            for root, _, files in os.walk(extract_dir):
                for f in files:
                    if f.endswith('.exe') or f in (f'{repo_name}.py', 'main.py') or f.endswith('.sh'):
                        exec_path = os.path.join(root, f)
                        break
                if exec_path:
                    break
            if not exec_path:
                raise FileNotFoundError("No executable found in extracted archive.")
            os.chmod(exec_path, 0o755)

        # Execute
        print(f"Executing {exec_path}...")
        if exec_path.endswith('.py'):
            # Lancer le nouveau programme et quitter l'actuel
            subprocess.Popen([sys.executable, exec_path], 
                            stdout=subprocess.DEVNULL, 
                            stderr=subprocess.DEVNULL,
                            creationflags=subprocess.CREATE_NEW_PROCESS_GROUP if os.name == 'nt' else 0)
        else:
            # Lancer l'exécutable
            subprocess.Popen([exec_path], 
                           stdout=subprocess.DEVNULL, 
                           stderr=subprocess.DEVNULL,
                           creationflags=subprocess.CREATE_NEW_PROCESS_GROUP if os.name == 'nt' else 0)
            

        # Clear manager after download
        _download_manager = None
        return tag
        
    except Exception as e:
        print(f"Update failed: {e}")
        _download_manager = None
        raise

if __name__ == '__main__':
    if needs_update():
        latest_tag = get_latest_version()
        print(f"Updated to {latest_tag}")
    else:
        print("Already at latest version.")