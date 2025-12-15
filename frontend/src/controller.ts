import { onMessage } from "./messageBus";
import * as api from "./api";
import { formatStoryData } from "./formatters";
import { config } from "./storyEditor/stores";
import { get } from "svelte/store";
import type { ITreeNode, IEntryTreeNode } from "./sharedTypes";
import { StoryTextSlotType } from "./sharedTypes";

let isInitialized = false;
let currentNodes: ITreeNode[] = [];
let currentStoryId = "";

export function initController() {
    if (isInitialized) return;
    isInitialized = true;

    console.log("[Controller] Initialized");

    onMessage(async (message) => {
        console.log("[Controller] Received:", message);
        switch (message.type) {
            case "loadStory":
                // Message from App.svelte -> Controller
                // We need to fetch and render the story
                const story = message.story;
                console.log("[Controller] Loading story:", story);

                if (story.id === "localize_dict") {
                    // Divert to loadLocalizeDict logic
                    // We can just self-dispatch or copy logic. 
                    // Since we are in a message handler, we can recurse by posting message?
                    // Or better, just emit the event so the switch case catches it?
                    // But we are inside the handler... 
                    // Let's just postMessage to self.
                    window.postMessage({ type: "loadLocalizeDict" }, "*");
                    break;
                }

                currentStoryId = story.id;

                window.postMessage({
                    type: "setExplorerTitle",
                    title: `Story ${story.id} (Loading...)`
                }, "*");

                try {
                    // Send default config first
                    window.postMessage({
                        type: "setConfig",
                        config: {
                            isStoryView: false, // Default to dialogue view
                            fontSizeMultiplier: 1.0,
                            lineSpacingMultiplier: 1.0,
                            game_path: "", // Will be updated by UI
                            use_decryption: false
                        }
                    }, "*");

                    const currentConfig = get(config);
                    const gamePath = currentConfig?.game_path || "";

                    const data = await api.extractStoryData(
                        story.path,
                        story.id,
                        false,
                        "",
                        "",
                        "",
                        gamePath
                    );

                    // Check for FastAPI error (detail) or bridge error (status="error")
                    if (data.detail) {
                        throw new Error("Backend Error: " + data.detail);
                    }
                    if (data.status === "error") {
                        throw new Error(data.message);
                    }
                    if (!data.blockList) {
                        throw new Error("Invalid story data: missing blockList");
                    }

                    const formatted = formatStoryData(data);
                    currentNodes = formatted.nodes; // Store for saving

                    // Update UI
                    window.postMessage({ type: "setNodes", nodes: formatted.nodes }, "*");
                    window.postMessage({ type: "setExplorerTitle", title: story.id }, "*");

                    // Send voice cues
                    const uris: Record<string, string> = {};
                    if (formatted.voiceCues) {
                        for (const [id, cue] of formatted.voiceCues) {
                            uris[id] = api.getAudioUrl(story.id, cue);
                        }
                    }
                    window.postMessage({ type: "loadVoice", uris }, "*");

                } catch (e: any) {
                    console.error("Failed to load story:", e);
                    window.postMessage({
                        type: "showMessage",
                        content: "Error loading story: " + e.message
                    }, "*");

                    // Clear nodes on error
                    window.postMessage({ type: "setNodes", nodes: [] }, "*");
                    window.postMessage({ type: "setExplorerTitle", title: "Error: " + e.message }, "*");
                }
                break;

            case "init":
                // Send initial config
                window.postMessage({
                    type: "setConfig",
                    config: {
                        isStoryView: false,
                        fontSizeMultiplier: 1.0,
                        lineSpacingMultiplier: 1.0,
                        game_path: "",
                        use_decryption: false
                    }
                }, "*");

                window.postMessage({
                    type: "setExplorerTitle",
                    title: "Story (Loading...)"
                }, "*");

                try {
                    const version = await api.checkVersion();
                    console.log("Backend Version:", version);

                    if (version.status === "error") {
                        window.postMessage({ type: "showMessage", content: "Backend Error: " + version.message }, "*");
                        return;
                    }

                    // Clear nodes/title on init
                    window.postMessage({ type: "setNodes", nodes: [] }, "*");
                    window.postMessage({ type: "setExplorerTitle", title: "" }, "*");

                    // Let's debug by ensuring we have valid mock data structure matching what utils expects.
                    // utils.gotoNode uses `node.content`.
                    // The dummyNodes have `content: [{content: "System"}, ...]`.
                    // This seems correct.


                } catch (e) {
                    console.error(e);
                    window.postMessage({ type: "showMessage", content: "Failed to connect to backend" }, "*");
                }
                break;
            case "loadLocalizeDict":
                const ldConfig = get(config);
                if (!ldConfig?.translation_dir || !ldConfig?.localize_dict_dump_path) {
                    window.postMessage({ type: "showMessage", content: "Please configure Translation Folder and Dict Dump Path in settings." }, "*");
                    return;
                }

                window.postMessage({ type: "setExplorerTitle", title: "Localize Dict (Loading...)" }, "*");

                try {
                    const data = await api.getLocalizeDict(ldConfig.translation_dir, ldConfig.localize_dict_dump_path);
                    if (data.detail) throw new Error(data.detail);

                    currentNodes = data.nodes;
                    currentStoryId = "localize_dict"; // Special ID

                    window.postMessage({ type: "setNodes", nodes: currentNodes }, "*");
                    window.postMessage({ type: "setExplorerTitle", title: "Localize Dict" }, "*");
                } catch (e: any) {
                    console.error("Failed to load localize dict:", e);
                    window.postMessage({ type: "showMessage", content: "Error: " + e.message }, "*");
                    window.postMessage({ type: "setExplorerTitle", title: "Error" }, "*");
                }
                break;

            case "getTextSlotContent":
                // Handle request for content
                // entryPath is [id] (string) for dict, or [blockIndex] (number) for story.
                // For Dict: key is entryPath[0] (string ID)
                // For Dict, the "content" is loaded into node.content[0].content initially?
                // Wait, utils.py sets content: translated_value.
                // So initial render has content.
                // BUT currentTextSlots (in utils.ts) implementation of gotoNode might copy content.
                // However, TextSlot logic: if (content === null) calls getTextSlotContent.
                // If content is NOT null, it doesn't call it.
                // For dict, I populated content. So it should be fine?

                // EXCEPT: If TranslatedViewInner calls translatedSlotProps -> sets content=undefined.
                // Then TextSlot calls getTextSlotContent.
                // So I MUST handle it here.

                if (currentStoryId === "localize_dict") {
                    const key = message.entryPath[0];
                    // Find node
                    // How to find node in tree structure from flat ID?
                    // Flat ID? No, entryPath corresponds to tree path? 
                    // Extension uses flat/nested IDs.
                    // For Dict, entryPath is [key] if it's flat?
                    // But I constructed a tree: Category -> Entry.
                    // So path is [Category, EntryID].

                    // Actually, TranslatedView traverses.
                    // If I select a node in Explorer, `gotoNode` sets `currentPath` to node path.
                    // And `currentTextSlots` to `node.content`.
                    // `TextSlot` uses `entryPath`... wait.
                    // `TextSlot` in `TranslatedViewInner` uses `entryPath={$currentPath}`.
                    // `$currentPath` is the path to the current entry node. [Category, Key].

                    // TextSlot receives `index`.

                    // So I just need to return `node.content[index].content`.
                    // But I need to find the node from `currentNodes` using `entryPath`.
                    // `utils.findNodeByPath` exists but I don't have access to it directly here?
                    // I can replicate find logic or import it.
                    // `currentNodes` is the root array.

                    // But wait, `getTextSlotContent` message only has `entryPath` and `index`.
                    // I need to traverse `currentNodes` (which is the tree root) using `entryPath`.

                    let target: ITreeNode | undefined;
                    let list = currentNodes;

                    for (const part of message.entryPath) {
                        const found = list.find(n => n.id === part);
                        if (!found) break;
                        target = found;
                        if (found.children) list = found.children;
                    }

                    if (target && target.content && target.content[message.index]) {
                        window.postMessage({
                            type: "setTextSlotContent",
                            entryPath: message.entryPath,
                            index: message.index,
                            content: target.content[message.index].content
                        }, "*");
                    }
                }
                // For Story, we didn't implement it yet but it seems fine without it?
                break;

            case "setTextSlotContent":
                // Echo back to update frontend stores
                window.postMessage({
                    type: "setTextSlotContent",
                    entryPath: message.entryPath,
                    index: message.index,
                    content: message.content
                }, "*");

                // Perform Save
                const currentConfig = get(config);
                if (!currentConfig || !currentConfig.translation_dir) {
                    return;
                }

                if (currentStoryId === "localize_dict") {
                    // Localize Dict Saving
                    // entryPath: [Category, Key]
                    // But wait, message.entryPath comes from TextSlot.
                    // TextSlot receives entryPath prop.
                    // In TranslatedViewInner: entryPath={$currentPath}.
                    // So it is indeed the full path to the node.

                    const key = message.entryPath[message.entryPath.length - 1]; // Last part is ID (Key)

                    // Call API
                    api.saveLocalizeDictEntry(currentConfig.translation_dir, key, message.content || "")
                        .then(res => {
                            if (res.status === "error")
                                window.postMessage({ type: "showMessage", content: "Save Failed: " + res.message }, "*");
                        })
                        .catch(e => window.postMessage({ type: "showMessage", content: "Save Failed: " + e.message }, "*"));

                    return;
                }

                // Story Saving
                // 1. Find Node
                const blockIndex = Number(message.entryPath[0]);
                const node = currentNodes.find(n => n.id === blockIndex);
                if (!node || node.type !== "entry") return;

                // ... existing logic ...
                // 2. Find Slot
                const slot = node.content[message.index];
                if (!slot || !slot.userData) return;

                const userData = slot.userData as { type: StoryTextSlotType, gender?: string };
                let listIndex = 0;

                const siblings = node.content.slice(0, message.index).filter(s => {
                    const u = s.userData as { type: StoryTextSlotType };
                    return u.type === userData.type;
                });
                listIndex = siblings.length;

                const saveReq: api.SaveTranslationRequest = {
                    story_id: currentStoryId,
                    block_index: blockIndex,
                    type: userData.type === StoryTextSlotType.Name ? "Name" :
                        userData.type === StoryTextSlotType.Content ? "Content" :
                            userData.type === StoryTextSlotType.Choice ? "Choice" : "ColorText",
                    list_index: listIndex,
                    content: message.content || "",
                    translation_dir: currentConfig.translation_dir
                };

                api.saveTranslation(saveReq)
                    .then(res => {
                        if (res.status === "error") {
                            window.postMessage({ type: "showMessage", content: "Save Failed: " + res.message }, "*");
                        } else {
                            console.log("Saved translation", res);
                        }
                    })
                    .catch(e => window.postMessage({ type: "showMessage", content: "Save Failed: " + e.message }, "*"));

                break;
            case "callHachimiIpc":
                try {
                    console.log("[Controller] Sending IPC command:", message.command);
                    const res = await api.sendIpcCommand(message.command);
                    if (res.type === "Error") {
                        window.postMessage({ type: "showMessage", content: "IPC Error: " + res.message }, "*");
                    } else {
                        console.log("[Controller] IPC Response:", res);
                    }
                } catch (e: any) {
                    console.error("[Controller] IPC Failed:", e);
                    window.postMessage({ type: "showMessage", content: "Failed to send IPC command" }, "*");
                }
                break;
        }
    });
}
