const API_BASE = "http://localhost:8000";

// ... existing exports ...

export async function fetchPost(endpoint: string, body: any = {}) {
    const res = await fetch(`${API_BASE}${endpoint}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body)
    });
    return res.json();
}

export async function getGameConfig() {
    const res = await fetch(`${API_BASE}/game/config`);
    return res.json();
}

export async function getGameStories(path?: string) {
    // legacy endpoint was /game/stories
    return fetchPost('/api/scan_stories', { path });
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

export async function extractStoryData(assetPath: string, assetName: string, useDecryption: boolean, metaPath: string, bundleHash: string, metaKey: string = "", gamePath?: string) {
    const res = await fetchPost(`/extract_story_data`, {
        asset_path: assetPath,
        asset_name: assetName,
        use_decryption: useDecryption,
        meta_path: metaPath,
        bundle_hash: bundleHash,
        meta_key: metaKey,
        game_path: gamePath
    });
    return res;
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

export async function sendIpcCommand(command: string) {
    return fetchPost('/ipc/send', { command });
}

export interface SaveTranslationRequest {
    story_id: string;
    block_index: number;
    type: "Name" | "Content" | "Choice" | "ColorText";
    list_index: number;
    content: string;
    translation_dir: string;
}

export async function saveTranslation(req: SaveTranslationRequest) {
    return fetchPost('/story/save', req);
}

export function getAudioUrl(storyId: string, cueId: number) {
    return `${API_BASE}/audio/${storyId}/${cueId}`;
}

export async function browseFolder() {
    return fetchPost('/dialog/browse_folder', {});
}

export async function browseFile() {
    return fetchPost('/dialog/browse_file', {});
}

export async function saveConfig(config: any) {
    return fetchPost('/save_config', config);
}

export async function getLocalizeDict(translation_dir: string, dump_path: string) {
    return await fetchPost("/get_localize_dict", {
        translation_dir,
        dump_path
    });
}

export async function saveLocalizeDictEntry(translation_dir: string, key: string, value: string) {
    return fetchPost('/save_localize_dict_entry', {
        translation_dir,
        key,
        value
    });
}
