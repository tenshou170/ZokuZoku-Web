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
    Supports both native structure (Persistent/) and extracted structure.
    """
    # 1. Native Structure: Check if the path itself is the 'Persistent' folder (contains master/master.mdb)
    if os.path.exists(os.path.join(game_path, "master", "master.mdb")):
        return game_path
        
    # 2. Native Structure: Check if path is Game Root (contains UmamusumePrettyDerby_Jpn_Data/Persistent)
    persistent_check = os.path.join(game_path, "UmamusumePrettyDerby_Jpn_Data", "Persistent")
    if os.path.exists(os.path.join(persistent_check, "master", "master.mdb")):
        return persistent_check

    # 3. Extracted/Deep Structure (Legacy/Mock)
    # Standard path: .../UmamusumePrettyDerby_Jpn_Data/Persistent/assets/_gallopresources/bundle/resources/story/data
    jp_path = os.path.join(game_path, "UmamusumePrettyDerby_Jpn_Data", "Persistent", "assets", "_gallopresources", "bundle", "resources", "story", "data")
    if os.path.exists(jp_path):
        return jp_path
        
    return None

def list_stories(story_base_dir):
    """
    Scans the story data directory and returns a tree or list of available stories.
    Returns a simplified list of files for now: [{"id": "020001004", "path": "...", "category": "02", "group": "0001"}]
    """
    stories = []
    
    # Check for native Game structure
    # Expected: .../Persistent/master/master.mdb
    # 1. Native Structure: master.mdb
    # Try multiple locations for master.mdb
    master_candidates = [
        os.path.join(story_base_dir, "master", "master.mdb"),
        os.path.join(story_base_dir, "master.mdb")
    ]
    
    master_path = None
    for p in master_candidates:
        if os.path.exists(p):
            master_path = p
            break
            
    if master_path:
        import py_bridge
        
        # Helper to safely query and append
        def query_and_append(query, category_func, group_func, label_prefix=""):
            try:
                res = py_bridge.handle_query_db({
                    "db_path": master_path,
                    "query": query,
                    "key": None
                })
                if res and 'rows' in res:
                    for row in res['rows']:
                        # Expecting row[0] to be the Story ID (text_id/story_id_1)
                        story_id = str(row[0])
                        if not story_id or story_id == "0": continue
                        
                        stories.append({
                            "id": story_id,
                            "path": f"native://{story_id}", 
                            "rel_path": f"{label_prefix}{story_id}", # Display helper
                            "category": category_func(row),
                            "group": group_func(row)
                        })
            except Exception as e:
                print(f"Query failed: {query[:30]}... {e}")

        # A. Main Story
        # SELECT story_id_1, part_id, story_number, id FROM main_story_data WHERE story_id_1 > 0
        query_and_append(
            "SELECT story_id_1, part_id, story_number, id FROM main_story_data WHERE story_id_1 > 0 LIMIT 500",
            lambda r: "Main Story",
            lambda r: f"Part {r[1]}"
        )

        # B. Event Story
        # SELECT story_id_1, story_event_id, episode_index_id FROM story_event_story_data WHERE story_id_1 > 0
        query_and_append(
            "SELECT story_id_1, story_event_id, episode_index_id FROM story_event_story_data WHERE story_id_1 > 0 LIMIT 500",
            lambda r: "Event Story",
            lambda r: f"Event {r[1]}"
        )
        
        # C. Chara Story
        # SELECT story_id, chara_id, episode_index FROM chara_story_data WHERE story_id > 0
        # Note: Column names might vary, guessing standard 'chara_id' and 'episode_index' based on pattern.
        # If this fails, it just won't list chara stories.
        try:
             query_and_append(
                "SELECT story_id, chara_id, episode_index FROM chara_story_data WHERE story_id > 0 LIMIT 500",
                lambda r: "Character Story",
                lambda r: f"Chara {r[1]}"
            )
        except:
            pass

    # 2. Extracted Structure (Keep legacy support)
    search_pattern = os.path.join(story_base_dir, "**", "storytimeline_*.json")
    files = glob.glob(search_pattern, recursive=True)
    
    for f in files:
        rel_path = os.path.relpath(f, story_base_dir)
        parts = rel_path.split(os.sep)
        
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

def resolve_story_path(game_path, story_id):
    """
    Resolves a Story ID to a physical file path (hashed bundle) using the meta database.
    """
    meta_path = os.path.join(game_path, "meta")
    if not os.path.exists(meta_path):
        # Flattened/extracted structure check
        meta_path = os.path.join(game_path, "UmamusumePrettyDerby_Jpn_Data", "Persistent", "meta")
        
    if os.path.exists(meta_path):
        import py_bridge
        try:
            # We need to find the hash 'h' for the asset named '.../storytimeline_{story_id}'
            # The name 'n' in table 'a' looks like: story/data/main/01/0001/storytimeline_20002001.asset (or .unity3d?)
            # We can use LIKE to match the ID.
            query = f"SELECT n, h FROM a WHERE n LIKE '%storytimeline_{story_id}.%'"
            
            res = py_bridge.handle_query_db({
                "db_path": meta_path,
                "query": query,
                "key": None
            })
            
            if res and 'rows' in res and len(res['rows']) > 0:
                # row: [name, hash]
                asset_name = res['rows'][0][0]
                file_hash = res['rows'][0][1] # Hash string
                
                # The file is located at dat/{hash[:2]}/{hash}
                blob_path = os.path.join(game_path, "dat", file_hash[:2], file_hash)
                
                # Verify it exists
                if not os.path.exists(blob_path):
                    # Check nested structure
                    blob_path = os.path.join(game_path, "UmamusumePrettyDerby_Jpn_Data", "Persistent", "dat", file_hash[:2], file_hash)
                    
                if os.path.exists(blob_path):
                    return {
                        "path": blob_path,
                        "name": asset_name,
                        "hash": file_hash
                    }
                    
        except Exception as e:
            print(f"Failed to resolve hash for {story_id}: {e}")
            
    return None

