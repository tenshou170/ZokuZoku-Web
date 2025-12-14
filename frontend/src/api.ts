const API_BASE = "http://localhost:8000";

// ... existing exports ...

export async function getGameConfig() {
    const res = await fetch(`${API_BASE}/game/config`);
    return res.json();
}

export async function getGameStories(path?: string) {
    const res = await fetch(`${API_BASE}/game/stories`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ path })
    });
    return res.json();
}

export async function checkVersion() {
    const res = await fetch(`${API_BASE}/version`);
    return res.json();
}


export async function checkApsw() {
    const res = await fetch(`${API_BASE}/check_apsw`);
    return res.json();
}

export async function queryDb(dbPath: string, query: string, key?: string) {
    const res = await fetch(`${API_BASE}/query_db`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ db_path: dbPath, query, key })
    });
    return res.json();
}

export async function extractStoryData(assetPath: string, assetName: string, useDecryption: boolean, metaPath: string, bundleHash: string, metaKey?: string) {
    const res = await fetch(`${API_BASE}/extract_story_data`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
            asset_path: assetPath,
            asset_name: assetName,
            use_decryption: useDecryption,
            meta_path: metaPath,
            bundle_hash: bundleHash,
            meta_key: metaKey
        })
    });
    return res.json();
}

export async function extractRaceStoryData(assetPath: string, assetName: string, useDecryption: boolean, metaPath: string, bundleHash: string, metaKey?: string) {
    const res = await fetch(`${API_BASE}/extract_race_story_data`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
            asset_path: assetPath,
            asset_name: assetName,
            use_decryption: useDecryption,
            meta_path: metaPath,
            bundle_hash: bundleHash,
            meta_key: metaKey
        })
    });
    return res.json();
}

export async function extractLyricsData(assetPath: string, assetName: string, useDecryption: boolean, metaPath: string, bundleHash: string, metaKey?: string) {
    const res = await fetch(`${API_BASE}/extract_lyrics_data`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
            asset_path: assetPath,
            asset_name: assetName,
            use_decryption: useDecryption,
            meta_path: metaPath,
            bundle_hash: bundleHash,
            meta_key: metaKey
        })
    });
    return res.json();
}
