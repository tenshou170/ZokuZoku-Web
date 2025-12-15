
import os
import sqlite3
import json
import glob
from pathlib import Path
import platform
import apsw

META_KEY_JP = "9c2bab97bcf8c0c4f1a9ea7881a213f6c9ebf9d8d4c6a8e43ce5a259bde7e9fd"
META_KEY_GLOBAL = "a713a5c79dbc9497c0a88669"

def find_game_install_path():
    """
    Attempts to find the Umamusume installation path.
    """
    if platform.system() == "Windows":
        # Common DMM locations
        paths = [
            "C:\\DMMGames\\Umamusume",
            "D:\\DMMGames\\Umamusume",
            "E:\\DMMGames\\Umamusume",
            "F:\\DMMGames\\Umamusume"
        ]
        for p in paths:
            if os.path.exists(p):
                return p
    elif platform.system() == "Linux":
         # Check Steam compatdata or common wine prefixes if known?? 
         # For now, rely on user input mostly
         # Check for Flatpak/Steam default locations maybe?
         home = os.path.expanduser("~")
         steam_paths = [
             f"{home}/.steam/steam/steamapps/compatdata/3564400/pfx/drive_c/users/steamuser/AppData/LocalLow/Cygames/umamusume",
             f"{home}/.local/share/Steam/steamapps/compatdata/3564400/pfx/drive_c/users/steamuser/AppData/LocalLow/Cygames/umamusume" 
         ]
         # Wait this is data dir, not install dir. 
         # Install dir is usually .../steamapps/common/Umamusume
         pass

    return None

def find_story_data_dir(game_path):
    """
    Given game install path, find the story data directory.
    User might pass the data directory directly.
    """
    if os.path.basename(game_path) == "master":
         return os.path.dirname(game_path) # parent of master
    
    # Check standard paths
    # Data is in %AppData%/LocalLow/Cygames/umamusume on Windows
    # But usually adjacent to master.mdb
    
    candidates = [
        os.path.join(game_path, "master"), # If game_path is the Data dir
        os.path.join(game_path, "Umamusume_Data", "StreamingAssets"), # Assets?
    ]
    
    # If game_path itself has "master.mdb", it's the data root
    if os.path.exists(os.path.join(game_path, "master", "master.mdb")):
        return game_path
        
    return game_path

def get_text_data_category(mdb_path, category_id):
    """
    Fetches a dictionary {index: text} for a given text category from master.mdb
    """
    if not mdb_path or not os.path.exists(mdb_path):
        return {}
        
    conn = sqlite3.connect(mdb_path)
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT `index`, `text` FROM text_data WHERE category = ?", (category_id,))
        rows = cursor.fetchall()
        return {r[0]: r[1] for r in rows}
    except Exception as e:
        print(f"Error fetching category {category_id}: {e}")
        return {}
    finally:
        conn.close()

def query_meta(meta_path, query, key=None):
    """
    Helper to query meta database using apsw and optional key.
    """
    if not meta_path or not os.path.exists(meta_path):
        return []
        
    uri = Path(meta_path).as_uri()
    conn_str = f"{uri}?mode=ro"
    if key:
        conn_str += f"&hexkey={key}"
        
    try:
        conn = apsw.Connection(conn_str, flags=apsw.SQLITE_OPEN_URI | apsw.SQLITE_OPEN_READONLY)
        cursor = conn.cursor()
        cursor.execute(query)
        return list(cursor)
    except Exception as e:
        print(f"Meta query failed: {e}")
        return []

def get_main_story_tree(mdb_path):
    """
    Constructs the Main Story tree: Act -> Chapter -> Episode -> Parts
    """
    tree = []
    if not mdb_path or not os.path.exists(mdb_path):
        return tree

    conn = sqlite3.connect(mdb_path)
    cursor = conn.cursor()

    try:
        # Pre-fetch text data
        chapter_names = get_text_data_category(mdb_path, 93)
        episode_names = get_text_data_category(mdb_path, 94)

        # 1. Get all parts (Chapters)
        cursor.execute("SELECT DISTINCT part_id FROM main_story_data ORDER BY part_id")
        all_part_ids = [r[0] for r in cursor.fetchall()]
        if not all_part_ids:
            return tree

        last_chapter = all_part_ids[-1]
        act_count = max(1, last_chapter // 10)

        for i in range(1, act_count + 1):
            act_node = {
                "type": "category",
                "name": f"Act {i}",
                "id": f"act_{i}",
                "children": []
            }

            # Chapters in this act
            min_part = (i) * 10 if i == 1 else i * 10
            if i == 1: min_part = 0 # Act 1 starts at 0? Extension says: actNum === 1 ? 0 : actNum * 10
            
            # Re-read extension logic:
            # actNum=1 -> > 0 AND < 20. So 1..19.
            # actNum=2 -> > 20 AND < 30.
            
            start = 0 if i == 1 else i * 10
            end = (i + 1) * 10
            
            # Find chapters in range
            chapters_in_act = [p for p in all_part_ids if p > start and p < end]
            
            for chap_id in chapters_in_act:
                chap_name = chapter_names.get(chap_id, f"Chapter {chap_id}")
                chap_node = {
                    "type": "category",
                    "name": chap_name,
                    "id": f"chap_{chap_id}",
                    "children": []
                }
                
                # Episodes
                cursor.execute("SELECT id, episode_index FROM main_story_data WHERE part_id = ? ORDER BY episode_index", (chap_id,))
                episodes = cursor.fetchall()
                
                for ep_id, ep_idx in episodes:
                    ep_name_text = episode_names.get(ep_id, "Unknown")
                    ep_node = {
                        "type": "category",
                        "name": f"E{ep_idx} - {ep_name_text}",
                        "id": f"ep_{ep_id}",
                        "children": []
                    }
                    
                    # Stories (Parts)
                    cursor.execute("""
                        SELECT story_type_1, story_id_1, story_type_2, story_id_2, 
                               story_type_3, story_id_3, story_type_4, story_id_4, 
                               story_type_5, story_id_5
                        FROM main_story_data WHERE id = ?
                    """, (ep_id,))
                    row = cursor.fetchone()
                    if row:
                        for k in range(0, 10, 2):
                            sType = row[k]
                            sId = row[k+1]
                            if sType == 0: break
                            
                            # sId might differ from story_id if formatted? 
                            # Extension uses utils.normalizeStoryId(storyId) -> ensures 9 digits?
                            # For main story usually just ID.
                            
                            story_ref = {
                                "type": "entry",
                                "name": f"Part {k//2 + 1}",
                                "id": str(sId),
                                "path": f"native://{sId}",
                                "category": "Main Story"
                            }
                            ep_node["children"].append(story_ref)
                            
                    if ep_node["children"]:
                        chap_node["children"].append(ep_node)
                
                if chap_node["children"]:
                    act_node["children"].append(chap_node)
            
            if act_node["children"]:
                tree.append(act_node)
                
    except Exception as e:
        print(f"Error building main story tree: {e}")
    finally:
        conn.close()

    return tree


category_names = {
    "00": "Short Episodes",
    "01": "Tutorials",
    "02": "Main Story",
    "04": "Umamusume Stories",
    "08": "Scenario Intros",
    "09": "Story Events",
    "10": "Anniv. Stories",
    "11": "G1 Outfit Episodes",
    "12": "New Year Short Episodes",
    "13": "Kirari Magic Show",
    "14": "The White Era",
    "40": "Scenario Career Events",
    "50": "Umamusume Career Events",
    "80": "Support Card Events (R)",
    "82": "Support Card Events (SR)",
    "83": "Support Card Events (SSR)"
}

def query_meta_conn(conn, query):
    """
    Helper to query using an existing open connection.
    """
    try:
        cursor = conn.cursor()
        cursor.execute(query)
        return list(cursor)
    except Exception as e:
        print(f"Meta query failed: {e}")
        return []

def get_meta_story_tree(meta_path, mdb_path, key):
    """
    Generic tree builder for stories in meta db (Events, Chara, etc)
    """
    tree = []
    if not meta_path or not os.path.exists(meta_path):
        return tree

    # Open Connection ONCE
    uri = Path(meta_path).as_uri()
    conn_str = f"{uri}?mode=ro"
    if key:
        conn_str += f"&hexkey={key}"
        
    conn = None
    try:
        conn = apsw.Connection(conn_str, flags=apsw.SQLITE_OPEN_URI | apsw.SQLITE_OPEN_READONLY)
    except Exception as e:
        print(f"Failed to open meta db: {e}")
        return tree
        
    try:
        # Get Categories
        query = r"SELECT DISTINCT SUBSTR(n, 12, 2) FROM a WHERE n LIKE 'story/data/__/____/storytimeline\__________' ESCAPE '\\'"
        rows = query_meta_conn(conn, query)
        
        # Cache names if needed
        # 4 (Chara) & 50 -> category 6
        # 40 -> category 119
        # Story Names: 4 -> cat 92, others -> cat 181
        
        char_names = get_text_data_category(mdb_path, 6)
        scenario_names = get_text_data_category(mdb_path, 119)
        chara_story_titles = get_text_data_category(mdb_path, 92)
        training_story_titles = get_text_data_category(mdb_path, 181)
    
        for r in rows:
            cat_id = r[0]
            if cat_id == "02": continue # Main story handled separately
    
            cat_real_name = category_names.get(cat_id, f"Category {cat_id}")
            
            cat_node = {
                "type": "category",
                "name": cat_real_name,
                "id": f"meta_cat_{cat_id}",
                "children": []
            }
            
            # Groups
            g_query = rf"SELECT DISTINCT SUBSTR(n, 15, 4) FROM a WHERE n LIKE 'story/data/{cat_id}/____/storytimeline\__________' ESCAPE '\\'"
            g_rows = query_meta_conn(conn, g_query)
            
            for gr in g_rows:
                grp_id = gr[0]
                grp_name = grp_id
                
                # Resolve Group Name
                if int(cat_id) in [4, 50]:
                    grp_name = char_names.get(int(grp_id), grp_id)
                elif int(cat_id) == 40:
                    grp_name = scenario_names.get(int(grp_id), grp_id).replace("\\n", " ")
                
                grp_node = {
                    "type": "category",
                    "name": grp_name,
                    "id": f"meta_grp_{cat_id}_{grp_id}",
                    "children": []
                }
                
                # Stories
                s_query = rf"SELECT SUBSTR(n, 34, 9) FROM a WHERE n LIKE 'story/data/{cat_id}/{grp_id}/storytimeline\__________' ESCAPE '\\'"
                s_rows = query_meta_conn(conn, s_query)
                
                for sr in s_rows:
                    s_id = sr[0]
                    s_label = s_id[6:] # Slice last 3 digits usually? Extension: storyId.slice(6)
                    
                    # Resolve Story Name
                    s_title = ""
                    if int(cat_id) == 4:
                        s_title = chara_story_titles.get(int(s_id), "")
                    else:
                        s_title = training_story_titles.get(int(s_id), "")
                    
                    full_label = s_label
                    if s_title:
                       full_label += f" {s_title}"
                       
                    story_node = {
                        "type": "entry",
                        "name": full_label,
                        "id": str(s_id),
                        "path": f"native://{s_id}",
                        "category": cat_real_name
                    }
                    grp_node["children"].append(story_node)
                    
                if grp_node["children"]:
                    cat_node["children"].append(grp_node)
            
            if cat_node["children"]:
                tree.append(cat_node)
                
    except Exception as e:
        print(f"Error walking meta tree: {e}")
    finally:
        conn.close()
            
    return tree

def list_stories_tree(game_path):
    """
    Returns the full story tree.
    """
    if not game_path: return {}
    
    print(f"Scanning stories in {game_path}...")
    
    mdb_path = os.path.join(game_path, "master", "master.mdb")
    meta_path = os.path.join(game_path, "meta")
    if not os.path.exists(meta_path):
         meta_alt = os.path.join(game_path, "UmamusumePrettyDerby_Jpn_Data", "Persistent", "meta")
         if os.path.exists(meta_alt): meta_path = meta_alt

    # Detect Key for meta
    print("Detecting meta key...")
    key = None
    # Try JP
    try:
        query_meta(meta_path, "SELECT 1", META_KEY_JP)
        key = META_KEY_JP
        print("Meta key detected: JP")
    except:
        pass
    
    if not key:
        try:
             query_meta(meta_path, "SELECT 1", META_KEY_GLOBAL)
             key = META_KEY_GLOBAL
             print("Meta key detected: Global")
        except:
             pass
    
    if not key:
        print("Meta key detection failed or unencrypted.")

    print("Building scan trees...")
    main_tree = get_main_story_tree(mdb_path)
    print(f"Main Tree built with {len(main_tree)} acts.")
    
    meta_tree = get_meta_story_tree(meta_path, mdb_path, key)
    print(f"Meta Tree built with {len(meta_tree)} categories.")
    
    return {
        "mainStories": main_tree,
        "otherStories": meta_tree
    }

def get_localize_dict_nodes(dump_path, local_dict_path):
    """
    Builds the tree nodes for the Localize Dict editor.
    """
    import json
    
    nodes = []
    
    # Read Dump (Originals)
    dump_data = {}
    if dump_path and os.path.exists(dump_path):
        try:
            with open(dump_path, 'r', encoding='utf-8') as f:
                dump_data = json.load(f)
        except Exception as e:
            print(f"Error reading dump: {e}")
            
    # Read Local (Translations)
    local_data = {}
    if local_dict_path and os.path.exists(local_dict_path):
        try:
            with open(local_dict_path, 'r', encoding='utf-8') as f:
                local_data = json.load(f)
        except Exception as e:
            print(f"Error reading local dict: {e}")
            
    category_map = {} # name -> child list
    
    # We iterate over DUMP keys as the source of truth for the tree structure
    # If local has extra keys not in dump, they might be lost in this view? 
    # The extension iterates the validated dict (dump).
    
    sorted_keys = sorted(dump_data.keys())
    
    for key in sorted_keys:
        original_value = dump_data[key]
        translated_value = local_data.get(key, None) # None means not translated yet (or use empty string?)
        
        # Determine Category
        category_name = ""
        for char in key:
            if char.isdigit(): break
            category_name += char
            
        if not category_name: category_name = "Misc"
        
        # Get/Create Category Node
        if category_name not in category_map:
             cat_node = {
                 "type": "category",
                 "id": category_name,
                 "name": category_name,
                 "children": []
             }
             nodes.append(cat_node)
             category_map[category_name] = cat_node["children"]
             
        # Create Entry Node
        # We store the Key as the ID.
        entry_node = {
            "type": "entry",
            "id": key,
            "name": key,
            "content": [
                {
                    "content": translated_value, # Can be null
                    "originalText": original_value,
                    "type": "text",
                    "userData": { "type": "LocalizeDict", "key": key },
                    "multiline": True
                }
            ]
        }
        category_map[category_name].append(entry_node)
        
    return nodes

def save_localize_dict_entry(path, key, value):
    import json
    if not path: return
    
    data = {}
    if os.path.exists(path):
        try:
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except Exception as e:
            print(f"Error reading dict for save: {e}")
            
    data[key] = value
    
    try:
        # Sort keys to keep it tidy
        # sorted_data = dict(sorted(data.items())) # Maybe too slow for huge dicts?
        # Let's just dump.
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
    except Exception as e:
        print(f"Error saving dict: {e}")
        raise e
