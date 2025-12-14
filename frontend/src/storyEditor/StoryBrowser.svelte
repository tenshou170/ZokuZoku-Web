<script lang="ts">
    import { onMount } from "svelte";
    import * as api from "../api";

    export let onSelect: (story: any) => void;

    let loading = true;
    let config: any = null;
    let stories: any[] = [];
    let error: string | null = null;
    let search = "";
    let manualPath = "";

    async function loadManual() {
        if (!manualPath) return;
        loading = true;
        try {
            const res = await api.getGameStories(manualPath);
            stories = res.stories;
            if (!config) config = {};
            config.game_path = manualPath; // Update display
            error = null;
        } catch (e: any) {
            error = e.message;
        } finally {
            loading = false;
        }
    }

    async function init() {
        try {
            config = await api.getGameConfig();
            if (config.found) {
                const res = await api.getGameStories();
                stories = res.stories;
            } else {
                error = "Game path not found automatically.";
            }
        } catch (e: any) {
            error = e.message;
        } finally {
            loading = false;
        }
    }

    onMount(init);

    $: filteredStories = stories.filter(
        (s) => s.id.includes(search) || (s.group && s.group.includes(search)),
    );
</script>

<div class="browser">
    <h1>Story Browser</h1>
    {#if loading}
        <p>Loading...</p>
    {:else if error}
        <div class="error">
            <p>Error: {error}</p>
            {#if config}
                <p>Detected Path: {config.game_path || "None"}</p>
            {/if}

            <div class="manual-path">
                <p>Enter Game Directory Manualy:</p>
                <input
                    type="text"
                    bind:value={manualPath}
                    placeholder="/path/to/UmamusumePrettyDerby"
                />
                <button on:click={loadManual}>Load</button>
            </div>

            <p>Or try auto-detect again:</p>
            <button on:click={init}>Retry</button>
        </div>
    {:else}
        <div class="header">
            <p>Game Path: {config.game_path}</p>
            <input type="text" placeholder="Search ID..." bind:value={search} />
            <p>Found {filteredStories.length} stories</p>
        </div>

        <div class="list">
            {#each filteredStories as story}
                <button class="story-item" on:click={() => onSelect(story)}>
                    <span class="id">{story.id}</span>
                    <span class="meta"
                        >Cat: {story.category} | Grp: {story.group}</span
                    >
                </button>
            {/each}
        </div>
    {/if}
</div>

<style>
    .browser {
        padding: 20px;
        color: var(--vscode-foreground);
        background: var(--vscode-editor-background);
        height: 100vh;
        overflow: hidden;
        display: flex;
        flex-direction: column;
    }
    .header {
        margin-bottom: 20px;
        padding-bottom: 10px;
        border-bottom: 1px solid var(--vscode-panel-border);
    }
    .list {
        flex: 1;
        overflow-y: auto;
        display: grid;
        grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
        gap: 10px;
    }
    .story-item {
        background: var(--vscode-button-secondaryBackground);
        color: var(--vscode-button-secondaryForeground);
        border: none;
        padding: 10px;
        cursor: pointer;
        display: flex;
        flex-direction: column;
        align-items: flex-start;
        text-align: left;
    }
    .story-item:hover {
        background: var(--vscode-button-secondaryHoverBackground);
    }
    .id {
        font-weight: bold;
        font-size: 1.1em;
    }
    .meta {
        font-size: 0.9em;
        opacity: 0.8;
    }
    .error {
        color: var(--vscode-errorForeground);
        display: flex;
        flex-direction: column;
        gap: 10px;
        align-items: flex-start;
    }
    .manual-path {
        display: flex;
        flex-direction: column;
        gap: 5px;
        width: 100%;
        max-width: 400px;
    }
    .manual-path input {
        padding: 5px;
        background: var(--vscode-input-background);
        color: var(--vscode-input-foreground);
        border: 1px solid var(--vscode-input-border, transparent);
    }
</style>
