from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List, Any, Dict
import uvicorn
import sys
import os
import platform
import shutil
import subprocess
import json

# Import existing logic
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
import py_bridge
from hachimi_ipc import ipc_client
from asset_manager import AssetManager
from audio_decoder import decode_service
import utils
from fastapi.responses import StreamingResponse
import io

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class QueryDbRequest(BaseModel):
    db_path: str
    query: str
    key: Optional[str] = None

class ExtractStoryRequest(BaseModel):
    asset_path: str
    asset_name: str
    use_decryption: bool = False
    meta_path: str
    bundle_hash: str
    meta_key: Optional[str] = None
    game_path: Optional[str] = None

@app.get("/")
def read_root():
    return {"status": "ok", "message": "ZokuZoku Backend Running"}

@app.get("/version")
def get_version():
    return py_bridge.handle_version({})

@app.get("/check_apsw")
def check_apsw():
    return py_bridge.handle_check_apsw({})

@app.post("/query_db")
def query_db(req: QueryDbRequest):
    try:
        params = req.dict()
        return py_bridge.handle_query_db(params)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

META_KEY_JP = "9c2bab97bcf8c0c4f1a9ea7881a213f6c9ebf9d8d4c6a8e43ce5a259bde7e9fd"
META_KEY_GLOBAL = "a713a5c79dbc9497c0a88669"

def detect_meta_key(meta_path):
    test_query = "SELECT n FROM c LIMIT 1"
    
    # Try JP
    try:
        py_bridge.handle_query_db({
            "db_path": meta_path,
            "query": test_query,
            "key": META_KEY_JP
        })
        return META_KEY_JP
    except Exception:
        pass
        
    # Try Global
    try:
        py_bridge.handle_query_db({
            "db_path": meta_path,
            "query": test_query,
            "key": META_KEY_GLOBAL
        })
        return META_KEY_GLOBAL
    except Exception:
        pass
        
    return None

@app.post("/extract_story_data")
def extract_story_data(req: ExtractStoryRequest):
    try:
        # Handle native path resolution
        if req.asset_path.startswith("native://"):
            story_id = req.asset_path.replace("native://", "")
            
            # Find game path (use provided or auto-detect)
            game_path = req.game_path if req.game_path else utils.find_game_install_path() 
            if not game_path:
                 # Try to deduce from meta_path if provided, else fail
                 if req.meta_path and os.path.exists(req.meta_path):
                     game_path = os.path.dirname(req.meta_path) # meta is in Persistent/ or root?
                     # meta path usually: .../Persistent/meta
                     if os.path.basename(game_path) == "Persistent":
                         pass # game_path is correct (Persistent dir)
                     elif os.path.exists(os.path.join(game_path, "Persistent")):
                         game_path = os.path.join(game_path, "Persistent")

            if not game_path:
                raise HTTPException(status_code=400, detail="Cannot resolve native ID without game path.")

            # Resolve using AssetManager
            mgr = AssetManager(game_path)
            resolved = mgr.resolve_story_id(story_id)
            
            if not resolved:
                raise HTTPException(status_code=404, detail=f"Could not find or download native asset for ID {story_id}")
            
            # Override request params with resolved values
            req.asset_path = resolved["path"]
            req.asset_name = resolved["name"]
            req.bundle_hash = resolved["hash"]
            req.use_decryption = True
            
            # Ensure meta_path is set (py_bridge needs it for keys)
            if not req.meta_path or not os.path.exists(req.meta_path):
                # Auto-detect meta path
                meta = os.path.join(game_path, "meta")
                if not os.path.exists(meta): 
                     # Try .../Persistent/meta if game_path was root
                     meta_alt = os.path.join(game_path, "UmamusumePrettyDerby_Jpn_Data", "Persistent", "meta")
                     if os.path.exists(meta_alt): meta = meta_alt
                
                if os.path.exists(meta):
                    req.meta_path = meta
                else:
                    raise HTTPException(status_code=500, detail="Meta file not found for decryption")
                    
            # Auto-detect meta key if needed
            if not req.meta_key:
                req.meta_key = detect_meta_key(req.meta_path)
                if not req.meta_key:
                     # Warn or default? If detection failed, it might be unencrypted or unknown key
                     pass 

        # Debug
        log_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "debug_log.txt")
        with open(log_path, "a") as f:
             f.write(f"DEBUG: Extracting with meta_path={req.meta_path}, key={req.meta_key}\n")
        params = req.dict()
        return py_bridge.handle_extract_story_data(params)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/extract_race_story_data")
def extract_race_story_data(req: ExtractStoryRequest):
    try:
        params = req.dict()
        return py_bridge.handle_extract_race_story_data(params)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/extract_lyrics_data")
def extract_lyrics_data(req: ExtractStoryRequest):
    try:
        params = req.dict()
        return py_bridge.handle_extract_lyrics_data(params)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

import utils

# ... existing imports ...

CONFIG_FILE = "config.json"

def load_config_file():
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            pass
    return {}

def save_config_file(config):
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=4)

@app.get("/game/config")
def get_game_config():
    """
    Returns the detected game configuration, merged with persistent config.
    """
    game_path_detected = utils.find_game_install_path()
    persistent_config = load_config_file()
    
    # Persistent overrides detected? Or persistent saves detected?
    # Let's say persistent config stores user preferences.
    # We always return persistent + detected game_path if not in persistent.
    
    config = persistent_config.copy()
    if "game_path" not in config or not config["game_path"]:
         config["game_path"] = game_path_detected
         
    config["found"] = config.get("game_path") is not None
    return config

class SaveConfigRequest(BaseModel):
    game_path: Optional[str] = None
    translation_dir: Optional[str] = None
    localize_dict_dump_path: Optional[str] = None
    # Add other fields as needed

@app.post("/save_config")
def save_config(req: SaveConfigRequest):
    try:
        current = load_config_file()
        
        # Merge updates
        updates = req.dict(exclude_unset=True)
        current.update(updates)
        
        save_config_file(current)
        return {"status": "success", "config": current}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

class GetGameStoriesRequest(BaseModel):
    path: Optional[str] = None

@app.get("/test_stories")
def test_stories():
    return {"status": "ok"}

@app.post("/test_post")
def test_post(req: Dict[str, Any]):
    return {"status": "ok", "req": req}

@app.post("/api/scan_stories")
def scan_stories_endpoint(req: Dict[str, Any]):
    """
    Scans for stories.
    req: { "path": "..." }
    """
    path = req.get("path")
    if not path:
        # Check config.json
        cfg = load_config_file()
        path = cfg.get("game_path")

    if not path:
        path = utils.find_game_install_path()
        
    if not path:
         raise HTTPException(status_code=404, detail="Game path not found")

    tree = utils.list_stories_tree(path)
    return tree

@app.get("/audio/{story_id}/{cue_id}")
def get_audio(story_id: str, cue_id: int):
    """
    Decodes and streams the voice line for the given story and cue ID.
    """
    # 1. Find Game Path (required for AssetManager)
    game_path = utils.find_game_install_path()
    if not game_path:
        raise HTTPException(status_code=404, detail="Game path not found")
        
    # 2. Resolve Voice Asset
    mgr = AssetManager(game_path)
    voice_info = mgr.resolve_voice_id(story_id)
    
    if not voice_info:
        raise HTTPException(status_code=404, detail="Voice asset not found for this story")
        
    # 3. Decode
    try:
        wav_data = decode_service.decode_cue(voice_info["path"], cue_id)
        return StreamingResponse(io.BytesIO(wav_data), media_type="audio/wav")
    except RuntimeError as e:
        # Check if it was missing tool
        if "not found" in str(e):
             raise HTTPException(status_code=500, detail="vgmstream-cli not found on server. Please install it.")
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/ipc/send")
def send_ipc_command(command: Dict[str, Any]):
    """
    Forwards a JSON command to the running game via Hachimi IPC.
    """
    response = ipc_client.send_command(command)
    if response.get("type") == "Error":
         # Return ok=True even on error so frontend can handle it gracefully? 
         # Or raising exception?
         # The extension uses reject(error).
         # Let's return the response as is.
         pass
    return response



def open_native_file_dialog(title="Open File", filetypes=[], directory=False):
    """
    Attempts to use native Linux tools (zenity, kdialog) before falling back to Tkinter.
    """
    system = platform.system()
    
    if system == "Linux":
        # Try Zenity (GNOME / GTK / Generic)
        if shutil.which("zenity"):
            cmd = ["zenity", "--file-selection", f"--title={title}"]
            if directory:
                cmd.append("--directory")
            
            # File filters for zenity
            # --file-filter="Name | *.json *.txt"
            if not directory and filetypes:
                for name, pattern in filetypes:
                    # simplistic mapping
                    cmd.append(f"--file-filter={name} | {pattern}")

            try:
                result = subprocess.run(cmd, capture_output=True, text=True)
                if result.returncode == 0:
                    return result.stdout.strip()
                return None
            except:
                pass # Fallback

        # Try Kdialog (KDE)
        if shutil.which("kdialog"):
            cmd = ["kdialog"]
            if directory:
                cmd.append("--getexistingdirectory")
            else:
                cmd.append("--getopenfilename")
                
            # Filter for kdialog: "application/json text/plain" or "*.json *.txt"
            if not directory and filetypes:
                 # kdialog uses "space separated patterns" usually or mime
                 # simpler to just pass pattern if possible or skip filter for simplicity in fallback
                 # cmd.append(" ".join([p for n, p in filetypes]))
                 pass

            try:
                result = subprocess.run(cmd, capture_output=True, text=True)
                if result.returncode == 0:
                    return result.stdout.strip()
                return None
            except:
                pass

    # Fallback to Tkinter (Windows, MacOS, or Linux without utils)
    try:
        import tkinter as tk
        from tkinter import filedialog
        
        root = tk.Tk()
        root.withdraw()
        root.attributes('-topmost', True)
        
        path = None
        if directory:
             path = filedialog.askdirectory(title=title)
        else:
             path = filedialog.askopenfilename(title=title, filetypes=filetypes)
             
        root.destroy()
        return path
    except Exception as e:
        print(f"Tkinter dialog failed: {e}")
        return None

@app.post("/dialog/browse_folder")
def browse_folder():
    path = open_native_file_dialog(title="Select Folder", directory=True)
    return {"path": path}

@app.post("/dialog/browse_file")
def browse_file():
    path = open_native_file_dialog(title="Select File", filetypes=[("JSON files", "*.json"), ("All files", "*.*")])
    return {"path": path}
class GetLocalizeDictRequest(BaseModel):
    translation_dir: str
    dump_path: str

@app.post("/get_localize_dict")
def get_localize_dict(req: GetLocalizeDictRequest):
    try:
        if not req.translation_dir or not req.dump_path:
             raise HTTPException(status_code=400, detail="Missing translation_dir or dump_path")
             
        local_path = os.path.join(req.translation_dir, "localized_data", "localize_dict.json")
        nodes = utils.get_localize_dict_nodes(req.dump_path, local_path)
        return {"nodes": nodes}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

class SaveLocalizeDictEntryRequest(BaseModel):
    translation_dir: str
    key: str
    value: str

@app.post("/save_localize_dict_entry")
def save_localize_dict_entry(req: SaveLocalizeDictEntryRequest):
    try:
        local_path = os.path.join(req.translation_dir, "localized_data", "localize_dict.json")
        utils.save_localize_dict_entry(local_path, req.key, req.value)
        return {"status": "success"}
    except Exception as e:
        return {"status": "error", "message": str(e)}

class SaveStoryRequest(BaseModel):
    story_id: str
    block_index: int
    type: str # "Name", "Content", "Choice", "ColorText"
    list_index: int
    content: str
    translation_dir: str

@app.post("/story/save")
async def save_story(req: SaveStoryRequest):
    try:
        # 1. Resolve path
        # Assuming flattened structure: translation_dir/storytimeline_{id}.json
        filename = f"storytimeline_{req.story_id}.json"
        
        # Check recursion?
        import glob
        existing_files = glob.glob(os.path.join(req.translation_dir, "**", filename), recursive=True)
        
        if existing_files:
            file_path = existing_files[0]
        else:
            # Default to flat in root of translation dir
            file_path = os.path.join(req.translation_dir, filename)
            
        # 2. Load or Init JSON
        data = {}
        if os.path.exists(file_path):
            with open(file_path, "r", encoding="utf-8") as f:
                try:
                    data = json.load(f)
                except json.JSONDecodeError:
                    pass # Corrupt or empty, start fresh
                    
        if "text_block_list" not in data:
            data["text_block_list"] = []
            
        # 3. Ensure Block Exists
        # Extend list if needed
        while len(data["text_block_list"]) <= req.block_index:
            data["text_block_list"].append({})
            
        block = data["text_block_list"][req.block_index]
        
        # 4. Update Field
        if req.type == "Name":
            block["name"] = req.content
        elif req.type == "Content":
            block["text"] = req.content
        elif req.type == "Choice":
            if "choice_data_list" not in block:
                block["choice_data_list"] = []
            # Extend list
            while len(block["choice_data_list"]) <= req.list_index:
                block["choice_data_list"].append("") 
            block["choice_data_list"][req.list_index] = req.content
        elif req.type == "ColorText":
            if "color_text_info_list" not in block:
                block["color_text_info_list"] = []
            while len(block["color_text_info_list"]) <= req.list_index:
                block["color_text_info_list"].append("")
            block["color_text_info_list"][req.list_index] = req.content
            
        # 5. Save
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
            
        print(f"Saved translation to {file_path}")
        return {"status": "ok", "path": file_path}
        
    except Exception as e:
        print(f"Error saving story: {e}")
        return {"status": "error", "message": str(e)}

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)
