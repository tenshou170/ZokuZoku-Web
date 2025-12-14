import os
import glob
from pathlib import Path

# Common Linux Steam Library paths
STEAM_PATHS = [
    os.path.expanduser("~/.steam/steam"),
    os.path.expanduser("~/.local/share/Steam"),
    os.path.expanduser("~/.var/app/com.valvesoftware.Steam/data/Steam") # Flatpak
]

APP_IDS = {
    "JP": "3564400",
    "Global": "3224770"
}

GAME_DIR_NAMES = [
    "UmamusumePrettyDerby", # Common
]

def find_game_install_path():
    """
    Attempts to find the game installation path on Linux.
    Returns the path to the 'UmamusumePrettyDerby' directory.
    """
    # 1. Check strict known paths
    candidate_paths = []
    
    for steam_root in STEAM_PATHS:
        apps_path = os.path.join(steam_root, "steamapps", "common")
        if os.path.exists(apps_path):
            for name in GAME_DIR_NAMES:
                full_path = os.path.join(apps_path, name)
                if os.path.exists(full_path):
                    return full_path

    return None

def find_story_data_dir(game_path):
    """
    Finds the directory containing story data within the game path.
    Standard path: .../UmamusumePrettyDerby_Jpn_Data/Persistent/assets/_gallopresources/bundle/resources/story/data
    """
    # Try JP Data path first
    jp_path = os.path.join(game_path, "UmamusumePrettyDerby_Jpn_Data", "Persistent", "assets", "_gallopresources", "bundle", "resources", "story", "data")
    if os.path.exists(jp_path):
        return jp_path
        
    # TODO: Add Global path logic if structure differs
    return None

def list_stories(story_base_dir):
    """
    Scans the story data directory and returns a tree or list of available stories.
    Returns a simplified list of files for now: [{"id": "020001004", "path": "...", "category": "02", "group": "0001"}]
    """
    stories = []
    # Use glob to find all storytimeline files recursively
    # Structure: category/group/storytimeline_ID.json or .unity3d (if raw)
    # The browser extension extraction logic seems to assume we are reading the unpacked assets or bundle files?
    # The mock path ended in .json, implying the user might be extracting them or looking at unpacked assets.
    # UnityPy can read .unity3d bundles directly.
    # But usually, _gallopresources/... are individual asset bundles (without extension or with hash).
    # Wait, the user's mock path was .json.
    # "storytimeline_020001004.json"
    
    # If we assume the user has DUMPED the assets to JSON (which the tool might do?),
    # OR if we are looking for the original bundles.
    # Original bundles in DMM/Steam version are usually in `dat` format or hashed filenames in `master/`?
    # Actually, `UmamusumePrettyDerby_Jpn_Data/Persistent` usually implies downloaded assets.
    # Let's search for any file pattern matching the story timeline naming convention if possible, 
    # but more robustly, just list files.
     
    # For this prototype, let's search for `.json` files as per the mock, 
    # AND also just list directories to let user navigate.
    
    search_pattern = os.path.join(story_base_dir, "**", "storytimeline_*.json")
    files = glob.glob(search_pattern, recursive=True)
    
    for f in files:
        rel_path = os.path.relpath(f, story_base_dir)
        parts = rel_path.split(os.sep)
        
        # Expect category/group/filename
        if len(parts) >= 3:
            category = parts[0]
            group = parts[1]
            filename = parts[-1]
            story_id = filename.replace("storytimeline_", "").replace(".json", "")
            
            stories.append({
                "id": story_id,
                "path": f,
                "rel_path": rel_path,
                "category": category,
                "group": group
            })
            
    return stories
