<script lang="ts">
    import { createEventDispatcher } from "svelte";
    import StoryTreeItem from "./StoryTreeItem.svelte";
    import SidebarSection from "./SidebarSection.svelte";
    import * as api from "../api";

    export let stories: any = {}; // backend returns { mainStories: [], otherStories: [] }
    export let config: any = null;

    const dispatch = createEventDispatcher();

    $: mainTree = stories.mainStories || [];
    $: otherTree = stories.otherStories || [];

    // Sort otherTree by id/name?
    // Backend returns list of Categories.

    // Filter out "Event Story", "Character Story" etc if we want specific sections?
    // VSCode has "Stories" which includes categories.
    // Here we have "ALL STORIES" (let's put 'otherTree' here) and "MAIN STORIES" (put 'mainTree' here).

    $: allTree = otherTree;

    function onSelect(e: any) {
        dispatch("select", e.detail.story);
    }

    function onReload() {
        dispatch("reload");
    }

    // Hachimi Controls
    async function reloadLocalized() {
        // zokuzoku.hachimi.reloadLocalizedData -> command
        await api.sendIpcCommand({ command: "ReloadLocalizedData" });
    }

    async function setLocalizeDir() {
        // Need file picker. Not implemented yet.
        alert("Not implemented in Web yet");
    }

    async function revertLocalizeDir() {
        // Not implemented
    }
</script>

<div class="sidebar">
    <div class="sidebar-title">EXPLORER</div>

    <SidebarSection
        title="ALL STORIES"
        expanded={true}
        actions={[{ icon: "refresh", title: "Refresh", id: "refresh" }]}
        on:action={(e) => {
            if (e.detail === "refresh") onReload();
        }}
    >
        <div class="tree-container">
            {#if !stories.otherStories || stories.otherStories.length === 0}
                {#if config?.game_path}
                    <div class="empty-msg">No stories found.</div>
                {:else}
                    <div class="empty-msg">Please configure game path.</div>
                {/if}
            {:else}
                <ul>
                    {#each allTree as node}
                        <StoryTreeItem {node} on:select={onSelect} />
                    {/each}
                </ul>
            {/if}
        </div>
    </SidebarSection>

    <SidebarSection
        title="HOME DIALOGUES"
        actions={[{ icon: "refresh", title: "Refresh", id: "refresh" }]}
    >
        <div class="tree-container">
            <div class="empty-msg">No home dialogues loaded.</div>
        </div>
    </SidebarSection>

    <SidebarSection
        title="MAIN STORIES"
        actions={[{ icon: "refresh", title: "Refresh", id: "refresh" }]}
    >
        <div class="tree-container">
            {#if !stories.mainStories || stories.mainStories.length === 0}
                <div class="empty-msg">No main stories loaded.</div>
            {:else}
                <ul>
                    {#each mainTree as node}
                        <StoryTreeItem {node} on:select={onSelect} />
                    {/each}
                </ul>
            {/if}
        </div>
    </SidebarSection>

    <SidebarSection title="LOCALIZE DICT">
        <div class="controls-container">
            <button
                class="control-btn"
                on:click={() => dispatch("openLocalizeDict")}
                >Open editor</button
            >
        </div>
    </SidebarSection>

    <SidebarSection title="MDB">
        <div class="empty-msg">Editor not implemented.</div>
    </SidebarSection>

    <SidebarSection
        title="LYRICS"
        actions={[{ icon: "refresh", title: "Refresh", id: "refresh" }]}
    >
        <div class="empty-msg">No lyrics loaded.</div>
    </SidebarSection>

    <SidebarSection title="HACHIMI CONTROLS">
        <div class="controls-container">
            <button class="control-btn" on:click={reloadLocalized}
                >Reload localized data</button
            >
            <button class="control-btn" on:click={setLocalizeDir}
                >Set translation folder</button
            >
            <button class="control-btn" on:click={revertLocalizeDir}
                >Revert translation folder</button
            >
        </div>
    </SidebarSection>

    <div class="spacer"></div>

    <SidebarSection title="SETTINGS">
        <div class="controls-container">
            <button
                class="control-btn"
                on:click={() => dispatch("openSettings")}>Open Settings</button
            >
        </div>
    </SidebarSection>

    <!-- Inactive / Timeline? MDB? -->
</div>

<style>
    .sidebar {
        width: 100%;
        height: 100%;
        background-color: var(--vscode-sideBar-background);
        color: var(--vscode-sideBar-foreground);
        display: flex;
        flex-direction: column;
        border-right: 1px solid var(--vscode-sideBar-border, #333);
        overflow-y: auto; /* Allow scrolling the whole sidebar if many sections expanded */
    }

    .sidebar-title {
        padding: 10px 15px;
        font-size: 11px;
        font-weight: normal;
        text-transform: uppercase;
        color: var(--vscode-sideBarTitle-foreground, #bbbbbb);
        display: none; /* VSCode hides the main title if using view containers? Or shows it at top? Usually "EXPLORER" is in the activity bar/header */
        /* Let's keep it hidden to mimic the "Views" list style */
    }

    .tree-container {
        padding-top: 4px;
        max-height: 50vh; /* logical limit? or flex? */
        overflow-y: auto;
    }

    ul {
        padding: 0;
        margin: 0;
    }

    .empty-msg {
        padding: 10px 20px;
        opacity: 0.5;
        font-size: 13px;
    }

    .controls-container {
        display: flex;
        flex-direction: column;
        padding: 10px;
        gap: 5px;
    }

    .control-btn {
        background-color: var(--vscode-button-background, #0e639c);
        color: var(--vscode-button-foreground, #ffffff);
        border: none;
        padding: 4px 8px;
        text-align: left;
        cursor: pointer;
    }
    .control-btn:hover {
        background-color: var(--vscode-button-hoverBackground, #1177bb);
    }

    .spacer {
        flex: 1;
    }
</style>
