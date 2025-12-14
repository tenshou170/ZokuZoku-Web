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
                    const data = await api.extractStoryData(
                        story.path, // asset_path
                        story.id, // asset_name
                        false, // use_decryption
                        "", // meta_path (Not used yet/Auto-detect in backend?)
                        "", // bundle_hash
                        "" // meta_key
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
                    type: "setExplorerTitle",
                    title: "Story (Loading...)"
                }, "*");

                try {
                    // TODO: Get these from UI or Config
                    // For now, we stub with a fake call to see if API works
                    const version = await api.checkVersion();
                    console.log("Backend Version:", version);

                    if (version.status === "error") {
                        window.postMessage({ type: "showMessage", content: "Backend Error: " + version.message }, "*");
                        return;
                    }

                    // We cannot easily load a story without path resolution.
                    // For the "Port Feasibility" check, getting the UI up and talking to backend is enough.
                    // But to show *nodes*, we need data.

                    // Let's create dummy nodes to prove it works
                    const dummyNodes = [
                        {
                            type: "entry",
                            id: 0,
                            name: "Mock Block 1",
                            content: [{ content: "This is a mock data from Controller" }]
                        },
                        {
                            type: "entry",
                            id: 1,
                            name: "Mock Block 2",
                            content: [{ content: "It proves the frontend is receiving data!" }]
                        }
                    ];

                    window.postMessage({ type: "setNodes", nodes: dummyNodes }, "*");
                    window.postMessage({ type: "setExplorerTitle", title: "Mock Story" }, "*");

                } catch (e) {
                    console.error(e);
                    window.postMessage({ type: "showMessage", content: "Failed to connect to backend" }, "*");
                }
                break;
        }
    });
}
