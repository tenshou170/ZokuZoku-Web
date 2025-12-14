import { onMessage } from "./messageBus";
import * as api from "./api";
import { formatStoryData } from "./formatters";

// Hardcoded for testing - needs a file picker later
const DEFAULT_ASSET_PATH = "/home/tenshou170/.local/share/Steam/steamapps/common/UmamusumePrettyDerby/UmamusumePrettyDerby_Jpn_Data/Persistent/assets/_gallopresources/bundle/resources/story/data/02/0001/storytimeline_020001004.json"; // Example path
// We actually need the Asset Bundle Path, not the JSON path inside it?
// The extractStoryData API expects: asset_path, asset_name, meta_path...
// This is tricky without the path resolution logic.
// Let's rely on the user to provide a path or implement the detector in Python.

let isInitialized = false;

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

                    const data = await api.extractStoryData(
                        story.path,
                        story.id,
                        false,
                        "",
                        "",
                        ""
                    );

                    if (data.status === "error") {
                        throw new Error(data.message);
                    }

                    const formatted = formatStoryData(data);

                    window.postMessage({ type: "setNodes", nodes: formatted.nodes }, "*");
                    window.postMessage({ type: "setExplorerTitle", title: story.id }, "*");

                } catch (e: any) {
                    window.postMessage({ type: "showMessage", content: "Failed to load story: " + e.message }, "*");
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

                    const dummyNodes = [
                        {
                            type: "entry",
                            id: 0,
                            name: "Mock Block 1",
                            content: [
                                { content: "System" },
                                { content: "This is a mock data from Controller" }
                            ]
                        },
                        {
                            type: "entry",
                            id: 1,
                            name: "Mock Block 2",
                            content: [
                                { content: "Tazuna" },
                                { content: "It proves the frontend is receiving data!" }
                            ]
                        }
                    ];


                    // Send setNodes
                    window.postMessage({ type: "setNodes", nodes: dummyNodes }, "*");
                    window.postMessage({ type: "setExplorerTitle", title: "Mock Story" }, "*");

                    // Force select the first node to populate panels? 
                    // Actually the Sidebar handles selection and triggers logic in utils.gotoNode
                    // But for initial load we might want to auto-select?
                    // Let's just trust user will click.
                    // However, the issue is that if the user clicks, utils.gotoNode IS called.
                    // Why is originalTextSlots empty?
                    // Ah, the mocked data flow might be different.
                    // In real app, `extractStoryData` returns nodes. user clicks node -> `gotoNode` -> sets stores.
                    // If user clicked "Mock Block 1", `gotoNode` runs.

                    // Let's debug by ensuring we have valid mock data structure matching what utils expects.
                    // utils.gotoNode uses `node.content`.
                    // The dummyNodes have `content: [{content: "System"}, ...]`.
                    // This seems correct.


                } catch (e) {
                    console.error(e);
                    window.postMessage({ type: "showMessage", content: "Failed to connect to backend" }, "*");
                }
                break;
            case "setTextSlotContent":
                // Echo back to update frontend stores (and other TextSlots)
                window.postMessage({
                    type: "setTextSlotContent",
                    entryPath: message.entryPath,
                    index: message.index,
                    content: message.content
                }, "*");
                break;
        }
    });
}
