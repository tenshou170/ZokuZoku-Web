<script lang="ts">
    import Workspace from "../lib/Workspace.svelte";
    import { onMount } from "svelte";
    import type { StoryEditorControllerMessage } from "../sharedTypes";
    import { config, originalPreview, translatedPreview } from "./stores";
    import WorkspaceInner from "./WorkspaceInner.svelte";
    import StoryBrowser from "./StoryBrowser.svelte";
    import { postMessageToController } from "../messageBus"; // Import for signaling

    let view: "browser" | "editor" = "browser";

    function onMessage(e: MessageEvent<StoryEditorControllerMessage>) {
        const message = e.data;
        switch (message.type) {
            case "setConfig":
                $config = message.config;
                const defaultPreview = message.config.isStoryView ? "story" : "dialogue";
                if ($originalPreview === undefined) {
                    $originalPreview = defaultPreview;
                }
                if ($translatedPreview === undefined) {
                    $translatedPreview = defaultPreview;
                }
                break;
        };
    }

    function handleStorySelect(story: any) {
        console.log("Selected story:", story);
        view = "editor";
        // Notify controller to load this story
        // We use a custom message type or just 'init' with params?
        // Existing controller listens to 'init'.
        // We can define a new message type "loadStory" on the bus.
        postMessageToController({ type: "loadStory", story });
    }
</script>

<svelte:window on:message={onMessage} />

{#if view === "browser"}
    <StoryBrowser onSelect={handleStorySelect} />
{:else}
    <Workspace inner={WorkspaceInner} />
{/if}