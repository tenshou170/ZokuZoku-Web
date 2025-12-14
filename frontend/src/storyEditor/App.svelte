<script lang="ts">
    import Workspace from "../lib/Workspace.svelte";
    import { onMount } from "svelte";
    import type { StoryEditorControllerMessage } from "../sharedTypes";
    import { config, originalPreview, translatedPreview } from "./stores";
    import WorkspaceInner from "./WorkspaceInner.svelte";
    import Sidebar from "./Sidebar.svelte";
    import Welcome from "./Welcome.svelte";
    import WorkspaceWrapper from "./WorkspaceWrapper.svelte";
    import * as api from "../api";

    // Application State
    let stories: any[] = [];
    let loading = true;
    let error: string | null = null;

    // Tab State
    interface Tab {
        id: string; // story id
        title: string;
        story: any;
    }
    let tabs: Tab[] = [];
    let activeTabIndex = -1;

    // Load initial data
    async function loadData(manualPath?: string) {
        loading = true;
        error = null;
        try {
            // 1. Get Config (or use manual path)
            if (manualPath) {
                // Temporary override logic, ideally backend persists
                const res = await api.getGameStories(manualPath);
                stories = res.stories;
                const defaultConfig = { noWrap: false, isStoryView: false };
                $config = {
                    ...defaultConfig,
                    ...($config || {}),
                    game_path: manualPath,
                };
            } else {
                const defaultConfig = { noWrap: false, isStoryView: false };
                const apiConfig = await api.getGameConfig();
                $config = {
                    ...defaultConfig,
                    ...($config || {}),
                    ...apiConfig,
                };

                if ($config?.found) {
                    const res = await api.getGameStories();
                    stories = res.stories;
                } else {
                    // Stay in "Welcome" state to ask for path
                }
            }
        } catch (e: any) {
            error = e.message;
        } finally {
            loading = false;
        }
    }

    onMount(() => loadData());

    function onMessage(e: MessageEvent<StoryEditorControllerMessage>) {
        const message = e.data;
        switch (message.type) {
            case "setConfig":
                $config = message.config;
                const defaultPreview = message.config.isStoryView
                    ? "story"
                    : "dialogue";
                if ($originalPreview === undefined) {
                    $originalPreview = defaultPreview;
                }
                if ($translatedPreview === undefined) {
                    $translatedPreview = defaultPreview;
                }
                break;
            case "loadStory":
                // Handle request to load story (e.g. from internal link?)
                const s = stories.find((st) => st.id === message.story.id);
                if (s) openStory(s);
                break;
            case "setTextSlotContent":
                break;
        }
    }

    function openStory(story: any) {
        // Check if already open
        const existingIdx = tabs.findIndex((t) => t.id === story.id);
        if (existingIdx >= 0) {
            activeTabIndex = existingIdx;
        } else {
            tabs = [
                ...tabs,
                {
                    id: story.id,
                    title: story.id, // Or use name if available
                    story: story,
                },
            ];
            activeTabIndex = tabs.length - 1;
        }
    }

    function closeTab(index: number, e: MouseEvent) {
        e.stopPropagation();
        tabs = tabs.filter((_, i) => i !== index);
        if (activeTabIndex >= tabs.length) {
            activeTabIndex = tabs.length - 1;
        }
    }

    function selectTab(index: number) {
        activeTabIndex = index;
    }

    // Sidebar Events
    function onSidebarSelect(e: any) {
        openStory(e.detail);
    }

    function onReload() {
        loadData($config?.game_path);
    }
</script>

<svelte:window on:message={onMessage} />

<div class="app-shell">
    <div class="sidebar-pane">
        <Sidebar
            {stories}
            config={$config}
            on:select={onSidebarSelect}
            on:reload={onReload}
        />
    </div>

    <div class="main-pane">
        {#if tabs.length > 0}
            <div class="tab-bar">
                {#each tabs as tab, i}
                    <div
                        class="tab"
                        class:active={i === activeTabIndex}
                        on:click={() => selectTab(i)}
                    >
                        <span class="tab-title">{tab.title}</span>
                        <div
                            class="tab-close codicon codicon-close"
                            on:click={(e) => closeTab(i, e)}
                        ></div>
                    </div>
                {/each}
            </div>
            <div class="tab-content">
                <!-- We only render the ACTIVE workspace to save resources? 
                     Or keep all alive with display:none? 
                     Svelte key blocks re-render. 
                     For simplicity, re-render on switch. 
                     Ideally keep state. workspaceState store handles state per generic workspace, 
                     but we need per-story state.
                     The current store architecture is SINGLETON (currentPath etc).
                     This means switching tabs will CLOBBER the state if we don't save/restore it.
                     State saving is handled via 'localStorage' based on... single session?
                     
                     Major Refactor Risk: The 'stores.ts' are global singletons intended for VSCode (one editor).
                     Supporting multiple tabs with state persistence is HARD without refactoring all stores to be contexts.
                     
                     Compromise: Only ONE tab active at a time in terms of "Workspace" component mounted.
                     Switching tabs re-mounts workspace. State might be lost if not saved.
                     The store saves to 'zokuzoku_workspace_state'. It doesn't key by story ID.
                     So switching tabs will show the state of the PREVIOUS story applied to the NEW story if not careful,
                     or just reset.
                     
                     Let's accept that switching tabs resets the view for now (scroll position etc), 
                     OR we force a save/load per story ID.
                     
                     Update 2: existing Workspace logic initializes from store.
                     We should probably clear the store or update it when switching.
                     For now, straight switch.
                -->
                {#key tabs[activeTabIndex].id}
                    <!-- We need to pass the story to the Workspace/Controller somehow.
                          Currently Controller listens to 'loadStory'. 
                          We need to tell the controller "Hey, the active story changed".
                          But wait, WorkspaceInner mounts Editor which uses stores.
                          Where is 'controller.ts' used? It's global.
                          
                          We need to trigger 'loadStory' on mount of the tab content.
                     -->
                    <WorkspaceWrapper story={tabs[activeTabIndex].story} />
                {/key}
            </div>
        {:else}
            <!-- Welcome / Empty State -->
            <Welcome
                {loading}
                {error}
                config={$config}
                on:load={(e) => loadData(e.detail)}
                on:retry={() => loadData()}
            />
        {/if}
    </div>
</div>

<style>
    .app-shell {
        display: flex;
        width: 100%;
        height: 100vh;
        overflow: hidden;
    }

    .sidebar-pane {
        width: 250px;
        flex-shrink: 0;
        display: flex;
    }

    .main-pane {
        flex: 1;
        display: flex;
        flex-direction: column;
        background-color: var(--vscode-editor-background);
        min-width: 0; /* Prevent flex overflow */
    }

    .tab-bar {
        display: flex;
        background-color: var(
            --vscode-editorGroupHeader-tabsBackground,
            #252526
        );
        height: 35px;
        overflow-x: auto;
    }

    .tab {
        display: flex;
        align-items: center;
        padding: 0 10px;
        background-color: var(--vscode-tab-inactiveBackground, #2d2d2d);
        color: var(--vscode-tab-inactiveForeground, #969696);
        border-right: 1px solid var(--vscode-tab-border, #1e1e1e);
        cursor: pointer;
        min-width: 120px;
        max-width: 200px;
        user-select: none;
    }

    .tab.active {
        background-color: var(--vscode-tab-activeBackground, #1e1e1e);
        color: var(--vscode-tab-activeForeground, #ffffff);
        border-top: 1px solid var(--vscode-tab-activeBorderTop, #007fd4);
    }

    .tab-title {
        flex: 1;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
        margin-right: 5px;
        font-size: 13px;
    }

    .tab-close {
        font-size: 14px;
        border-radius: 4px;
        padding: 2px;
    }

    .tab-close:hover {
        background-color: rgba(255, 255, 255, 0.2);
        color: white;
    }

    .tab-content {
        flex: 1;
        position: relative;
        overflow: hidden;
    }
</style>
