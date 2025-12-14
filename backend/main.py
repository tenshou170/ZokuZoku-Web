from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List, Any, Dict
import uvicorn
import sys
import os

# Import existing logic
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
import py_bridge

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

@app.post("/extract_story_data")
def extract_story_data(req: ExtractStoryRequest):
    try:
        # Handle native path resolution
        if req.asset_path.startswith("native://"):
            story_id = req.asset_path.replace("native://", "")
            
            # Find game path again (needed for resolution)
            game_path = utils.find_game_install_path() 
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

            # Resolve
            resolved = utils.resolve_story_path(game_path, story_id)
            if not resolved:
                raise HTTPException(status_code=404, detail=f"Could not find native asset for ID {story_id}")
            
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

@app.get("/game/config")
def get_game_config():
    """
    Returns the detected game configuration.
    """
    game_path = utils.find_game_install_path()
    return {
        "game_path": game_path,
        "found": game_path is not None
    }

@app.post("/game/stories")
def get_game_stories(req: dict):
    """
    Scans for stories in the provided or detected game path.
    Payload: {"path": optional_override_path}
    """
    
    path = req.get("path")
    
    if not path:
        path = utils.find_game_install_path()
        
    if not path:
         raise HTTPException(status_code=404, detail="Game path not found")

    story_dir = utils.find_story_data_dir(path)
    if not story_dir:
        raise HTTPException(status_code=404, detail="Story data directory not found")

    stories = utils.list_stories(story_dir)
    return {"stories": stories}

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)
