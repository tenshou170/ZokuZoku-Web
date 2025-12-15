import os
import apsw
import urllib.request
import urllib.error
from pathlib import Path
from typing import Optional
import utils

# Constants from assetHelper.ts
ASSET_BASE_URL_JP = "https://prd-storage-game-umamusume.akamaized.net/dl/resources/"
ASSET_BASE_URL_GL = "https://assets-umamusume-en.akamaized.net/dl/vertical/resources/"

class AssetManager:
    def __init__(self, game_path: str):
        self.game_path = game_path
        self.meta_path = self._find_meta_path(game_path)
        self.platform: Optional[str] = None
        self.base_url: Optional[str] = None

    def _find_meta_path(self, game_path: str) -> Optional[str]:
        # Native structure
        meta = os.path.join(game_path, "meta")
        if os.path.exists(meta):
            return meta
        # Extracted structure
        meta = os.path.join(game_path, "UmamusumePrettyDerby_Jpn_Data", "Persistent", "meta")
        if os.path.exists(meta):
            return meta
        return None

    def _query_meta(self, query: str) -> list:
        if not self.meta_path:
            raise ValueError("Meta database not found")
        
        db_uri = Path(self.meta_path).as_uri()
        conn = apsw.Connection(f"{db_uri}?mode=ro", flags=apsw.SQLITE_OPEN_URI | apsw.SQLITE_OPEN_READONLY)
        cursor = conn.cursor()
        try:
            cursor.execute(query)
            return list(cursor)
        finally:
            conn.close()

    def get_platform(self) -> str:
        if self.platform:
            return self.platform
        
        # Query meta implementation from assetHelper.ts
        query = "SELECT n FROM c WHERE n = '//Android' OR n = '//Windows'"
        rows = self._query_meta(query)
        if rows and rows[0]:
            # Returns //Android or //Windows, strip //
            self.platform = rows[0][0][2:]
            return self.platform
        
        # Fallback if query fails but we are on Linux/Windows, assume Windows assets typically
        return "Windows"

    def get_base_url(self) -> str:
        if self.base_url:
            return self.base_url

        self.get_platform() # ensure platform is loaded
        
        # Simple detection based on Utils logic or just try to match Edge logic
        # Edge checks SQLite.detectedGameVersion == "GL". 
        # We can loosely infer from path or just try both?
        # For now, default to JP unless we see indications of Global.
        # Global usually has slightly different folder names or app IDs.
        
        # Let's assume JP for now as strict port of Edge default behavior
        self.base_url = ASSET_BASE_URL_JP
        # If we had a mechanism to detect GL, we'd swap here.
        return self.base_url

    def get_asset_hash(self, asset_name: str) -> Optional[str]:
        # assetHelper.ts: SELECT h FROM a WHERE n = 'name'
        # sanitize name just in case
        safe_name = asset_name.replace("'", "''")
        query = f"SELECT h FROM a WHERE n = '{safe_name}'"
        rows = self._query_meta(query)
        if rows and rows[0]:
            return rows[0][0]
        return None

    def get_asset_path(self, hash_str: str) -> tuple[str, str]:
        """Returns (asset_dir, full_asset_path)"""
        # dat/{hash[:2]}/{hash}
        # We try to use the game's dat folder first
        
        # Look for 'dat' folder
        dat_root = os.path.join(self.game_path, "dat")
        if not os.path.exists(dat_root):
             dat_root = os.path.join(self.game_path, "UmamusumePrettyDerby_Jpn_Data", "Persistent", "dat")
        
        # If still not exists, we might need to create it (if we are allowed to write)
        # Or use a local cache? Edge config has "zokuzoku.gameDataDir".
        # We assume self.game_path is the valid data dir.
        
        asset_dir = os.path.join(dat_root, hash_str[:2])
        asset_path = os.path.join(asset_dir, hash_str)
        return asset_dir, asset_path

    def ensure_asset(self, hash_str: str, is_generic: boolean = False) -> str:
        asset_dir, asset_path = self.get_asset_path(hash_str)
        
        if os.path.exists(asset_path):
            return asset_path
            
        print(f"[AssetManager] Downloading missing asset: {hash_str}")
        
        # Needs download
        base_url = self.get_base_url()
        if is_generic:
            url = f"{base_url}Generic/{hash_str[:2]}/{hash_str}"
        else:
            platform = self.get_platform()
            url = f"{base_url}{platform}/assetbundles/{hash_str[:2]}/{hash_str}"
            
        # Ensure dir exists
        os.makedirs(asset_dir, exist_ok=True)
        
        try:
            # Download to temp file then rename
            temp_path = asset_path + ".tmp"
            with urllib.request.urlopen(url) as response, open(temp_path, 'wb') as out_file:
                # Simple chunked copy
                while True:
                    chunk = response.read(1024 * 1024) # 1MB chunks
                    if not chunk:
                        break
                    out_file.write(chunk)
            
            os.rename(temp_path, asset_path)
            return asset_path
        except Exception as e:
            if os.path.exists(temp_path):
                os.remove(temp_path)
            raise RuntimeError(f"Failed to download asset {hash_str}: {e}")

    def resolve_story_id(self, story_id: str) -> Optional[dict]:
        """
        Resolves a Story ID to an asset path (downloading if necessary).
        Returns dict with path, name, hash.
        """
        # Logic ported from utils.resolve_story_path but using our query_meta
        query = f"SELECT n, h FROM a WHERE n LIKE '%storytimeline_{story_id}.%'"
        rows = self._query_meta(query)
        
        if rows and rows[0]:
            name = rows[0][0]
            hash_str = rows[0][1]
            
            # Ensure downloaded
            try:
                full_path = self.ensure_asset(hash_str)
                return {
                    "path": full_path,
                    "name": name,
                    "hash": hash_str
                }
            except Exception as e:
                print(f"[AssetManager] Failed to ensure asset {hash_str}: {e}")
                return None
                
        return None

    def resolve_voice_id(self, story_id: str) -> Optional[dict]:
        """
        Resolves a Story ID to a voice asset path (downloading if necessary).
        Voice asset name format: sound/c/snd_voi_story_{short_story_id}.awb
        """
        if len(story_id) < 6:
            return None
            
        short_id = story_id[:6]
        voice_asset_name = f"sound/c/snd_voi_story_{short_id}.awb"
        
        hash_str = self.get_asset_hash(voice_asset_name)
        if not hash_str:
            return None
            
        try:
            full_path = self.ensure_asset(hash_str)
            return {
                "path": full_path,
                "name": voice_asset_name,
                "hash": hash_str
            }
        except Exception as e:
            print(f"[AssetManager] Failed to ensure voice asset {voice_asset_name}: {e}")
            return None

