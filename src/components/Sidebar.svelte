<script lang="ts">
    import { invoke } from "@tauri-apps/api/core";
    import { onMount } from "svelte";
    import { fade } from "svelte/transition";
    import { MDB_TABLE_NAMES } from "../mdbController";

    import { open } from "@tauri-apps/plugin-dialog";
    import { appConfig } from "../configStore";
    import { loadLyricsList } from "../lyricsController";
    import type { LyricItem } from "../lyricsController";
    import { loadRaceStoriesList } from "../raceStoryController";
    import type { RaceStoryItem } from "../raceStoryController";

    let allStoriesExpanded = true;
    let settingsExpanded = true;
    let lyricsExpanded = false;
    let lyricsList: LyricItem[] = [];
    let raceStoriesExpanded = false;
    let raceStoriesList: RaceStoryItem[] = [];

    // Configuration
    // Dynamic from store
    $: gamePath = $appConfig.gamePath;
    $: metaPath = `${gamePath}/meta`;
    let metaKey = "532b4631e4a7b9473e7cfb"; // JP Default

    type TreeItem = {
        id: string;
        label: string;
        level: "category" | "group" | "story";
        children?: TreeItem[];
        expanded?: boolean;
        loading?: boolean;
        command?: string;
        args?: any[];
    };

    let rootItems: TreeItem[] = [];
    let errorMsg = "";
    let mdbExpanded = false;

    const categoryNames: { [key: string]: string } = {
        "01": "> Tutorials",
        "02": "> Main Story",
        "04": "> Umamusume Stories",
        "08": "> Scenario Intros",
        "09": "> Story Events",
        "10": "> Anniv. Stories",
    };

    async function queryDb(query: string) {
        if (!metaPath) return [];
        console.log("Querying", query);
        const res = await invoke<{ header: string[]; rows: any[][] }>(
            "query_db",
            {
                dbPath: metaPath,
                query,
                key: metaKey,
            },
        );
        return res.rows.map((r) => r[0]);
    }

    async function loadCategories() {
        try {
            errorMsg = "";
            const ids = await queryDb(
                "SELECT DISTINCT SUBSTR(n, 12, 2) FROM a WHERE n LIKE 'story/data/__/____/storytimeline\\__________' ESCAPE '\\'",
            );
            rootItems = ids.sort().map((id) => ({
                id,
                label: `${id} ${categoryNames[id] || ""}`,
                level: "category",
                children: [],
                expanded: false,
            }));
        } catch (e) {
            console.error(e);
            errorMsg = `Failed to load categories: ${e}`;
        }
    }

    async function loadGroups(categoryItem: TreeItem) {
        if (categoryItem.children && categoryItem.children.length > 0) return;
        categoryItem.loading = true;
        try {
            const ids = await queryDb(
                `SELECT DISTINCT SUBSTR(n, 15, 4) FROM a WHERE n LIKE 'story/data/${categoryItem.id}/____/storytimeline\\__________' ESCAPE '\\'`,
            );
            categoryItem.children = ids.sort().map((id) => ({
                id: `${categoryItem.id}/${id}`,
                label: id,
                level: "group",
                children: [],
                expanded: false,
            }));
        } catch (e) {
            console.error(e);
        } finally {
            categoryItem.loading = false;
            rootItems = rootItems; // Trigger reactivity
        }
    }

    async function loadStories(groupItem: TreeItem) {
        if (groupItem.children && groupItem.children.length > 0) return;
        groupItem.loading = true;
        try {
            const [catId, grpId] = groupItem.id.split("/");
            const ids = await queryDb(
                `SELECT SUBSTR(n, 34, 9) FROM a WHERE n LIKE 'story/data/${catId}/${grpId}/storytimeline\\__________' ESCAPE '\\'`,
            );
            groupItem.children = ids.sort().map((id) => ({
                id: `${groupItem.id}/${id}`,
                label: id.slice(6), // Display only last part
                level: "story",
                command: "openStory",
                args: [id],
            }));
        } catch (e) {
            console.error(e);
        } finally {
            groupItem.loading = false;
            rootItems = rootItems; // Trigger reactivity
        }
    }

    async function toggle(item: TreeItem) {
        item.expanded = !item.expanded;
        if (item.expanded) {
            if (item.level === "category") await loadGroups(item);
            if (item.level === "group") await loadStories(item);
        }
        rootItems = rootItems;
    }

    function openStory(id: string) {
        console.log("Opening story", id);
        // Dispatch event to parent
        const event = new CustomEvent("open-story", { detail: { id } });
        window.dispatchEvent(event);
    }

    function openMdb(tableName: string) {
        console.log("Opening MDB", tableName);
        const event = new CustomEvent("open-mdb", { detail: { tableName } });
        window.dispatchEvent(event);
    }

    function openLyrics(item: LyricItem) {
        console.log("Opening Lyrics", item);
        const event = new CustomEvent("open-lyrics", { detail: { item } });
        window.dispatchEvent(event);
    }

    function openRaceStory(item: RaceStoryItem) {
        console.log("Opening Race Story", item);
        const event = new CustomEvent("open-race-story", { detail: { item } });
        window.dispatchEvent(event);
    }

    async function selectGameFolder() {
        try {
            const selected = await open({
                directory: true,
                multiple: false,
                title: "Select Umamusume Game Folder",
            });
            if (selected && typeof selected === "string") {
                appConfig.update((c) => ({ ...c, gamePath: selected }));
                // Reload categories since path changed
                loadCategories();
            }
        } catch (e) {
            console.error(e);
            alert("Failed to select folder: " + e);
        }
    }

    async function selectTranslationFolder() {
        try {
            const selected = await open({
                directory: true,
                multiple: false,
                title: "Select Translation Folder (containing localize_dump.json)",
            });
            if (selected && typeof selected === "string") {
                appConfig.update((c) => ({ ...c, translationPath: selected }));
            }
        } catch (e) {
            console.error(e);
            alert("Failed to select folder: " + e);
        }
    }

    import { get } from "svelte/store";

    onMount(() => {
        if (get(appConfig).gamePath) {
            loadCategories();
            loadLyrics();
            loadRaceStories();
        }
    });

    async function loadLyrics() {
        lyricsList = await loadLyricsList();
    }

    async function loadRaceStories() {
        raceStoriesList = await loadRaceStoriesList();
    }

    // Watch path change
    $: if ($appConfig.gamePath) {
        // loadCategories is already called in selectGameFolder manually?
        // Let's rely on manual reload for now or add a reactive statement.
        // For lyrics, let's load it.
        loadLyrics();
        loadRaceStories();
    }
</script>

<div class="sidebar">
    <div class="header">
        <h3>ZOKUZOKU</h3>
        <button on:click={loadCategories} title="Refresh">
            <span class="codicon codicon-refresh"></span>
        </button>
    </div>

    <!-- ALL STORIES Section -->
    <div
        class="header section-header"
        role="button"
        tabindex="0"
        on:click={() => (allStoriesExpanded = !allStoriesExpanded)}
        on:keydown={(e) =>
            (e.key === "Enter" || e.key === " ") &&
            (allStoriesExpanded = !allStoriesExpanded)}
        style="cursor: pointer;"
    >
        <h3 style="display: flex; align-items: center;">
            <span
                class="codicon codicon-{allStoriesExpanded
                    ? 'chevron-down'
                    : 'chevron-right'}"
                style="margin-right: 5px;"
            ></span>
            ALL STORIES
        </h3>
    </div>

    {#if allStoriesExpanded}
        {#if errorMsg}
            <div class="error">{errorMsg}</div>
        {/if}

        <ul class="tree">
            {#each rootItems as cat}
                <!-- Category -->
                <li>
                    <div
                        class="tree-item"
                        role="button"
                        tabindex="0"
                        on:click={() => toggle(cat)}
                        on:keydown={(e) =>
                            (e.key === "Enter" || e.key === " ") && toggle(cat)}
                    >
                        <span
                            class="codicon codicon-{cat.expanded
                                ? 'chevron-down'
                                : 'chevron-right'}"
                        ></span>
                        <span>{cat.label}</span>
                    </div>
                    {#if cat.expanded}
                        <ul
                            class="sub-tree"
                            transition:fade={{ duration: 100 }}
                        >
                            {#if cat.loading}<li>Loading...</li>{/if}
                            {#each cat.children || [] as grp}
                                <!-- Group -->
                                <li>
                                    <div
                                        class="tree-item group-item"
                                        role="button"
                                        tabindex="0"
                                        on:click={() => toggle(grp)}
                                        on:keydown={(e) =>
                                            (e.key === "Enter" ||
                                                e.key === " ") &&
                                            toggle(grp)}
                                    >
                                        <span
                                            class="codicon codicon-{grp.expanded
                                                ? 'chevron-down'
                                                : 'chevron-right'}"
                                        ></span>
                                        <span>{grp.label}</span>
                                    </div>
                                    {#if grp.expanded}
                                        <ul class="sub-tree">
                                            {#if grp.loading}<li>
                                                    Loading...
                                                </li>{/if}
                                            {#each grp.children || [] as story}
                                                <!-- Story -->
                                                <li>
                                                    <div
                                                        class="tree-item story-item"
                                                        role="button"
                                                        tabindex="0"
                                                        on:click={() =>
                                                            openStory(story.id)}
                                                        on:keydown={(e) =>
                                                            (e.key ===
                                                                "Enter" ||
                                                                e.key ===
                                                                    " ") &&
                                                            openStory(story.id)}
                                                    >
                                                        <span
                                                            class="codicon codicon-file"
                                                        ></span>
                                                        <span
                                                            >{story.label}</span
                                                        >
                                                    </div>
                                                </li>
                                            {/each}
                                        </ul>
                                    {/if}
                                </li>
                            {/each}
                        </ul>
                    {/if}
                </li>
            {/each}
        </ul>
    {/if}

    <div
        class="header section-header"
        role="button"
        tabindex="0"
        on:click={() => (mdbExpanded = !mdbExpanded)}
        on:keydown={(e) =>
            (e.key === "Enter" || e.key === " ") &&
            (mdbExpanded = !mdbExpanded)}
        style="cursor: pointer;"
    >
        <h3 style="display: flex; align-items: center;">
            <span
                class="codicon codicon-{mdbExpanded
                    ? 'chevron-down'
                    : 'chevron-right'}"
                style="margin-right: 5px;"
            ></span>
            MDB
        </h3>
    </div>
    {#if mdbExpanded}
        <ul
            class="tree mdb-tree"
            style="flex: 0 0 auto; max-height: 300px; border-top: 1px solid var(--vscode-editorGroup-border);"
        >
            {#each MDB_TABLE_NAMES as table}
                <li>
                    <div
                        class="tree-item"
                        role="button"
                        tabindex="0"
                        on:click={() => openMdb(table)}
                        on:keydown={(e) =>
                            (e.key === "Enter" || e.key === " ") &&
                            openMdb(table)}
                    >
                        <span class="codicon codicon-database"></span>
                        <span>{table}</span>
                    </div>
                </li>
            {/each}
        </ul>
    {/if}

    <div
        class="header section-header"
        role="button"
        tabindex="0"
        on:click={() => (lyricsExpanded = !lyricsExpanded)}
        on:keydown={(e) =>
            (e.key === "Enter" || e.key === " ") &&
            (lyricsExpanded = !lyricsExpanded)}
        style="cursor: pointer; border-top: 1px solid var(--vscode-editorGroup-border);"
    >
        <h3 style="display: flex; align-items: center;">
            <span
                class="codicon codicon-{lyricsExpanded
                    ? 'chevron-down'
                    : 'chevron-right'}"
                style="margin-right: 5px;"
            ></span>
            LYRICS
        </h3>
    </div>
    {#if lyricsExpanded}
        <ul
            class="tree lyrics-tree"
            style="flex: 0 0 auto; max-height: 300px; border-top: 1px solid var(--vscode-editorGroup-border);"
        >
            {#if lyricsList.length === 0}
                <li style="padding: 5px 10px; color: #888;">
                    No lyrics found or loading...
                </li>
            {/if}
            {#each lyricsList as item}
                <li>
                    <div
                        class="tree-item"
                        role="button"
                        tabindex="0"
                        on:click={() => openLyrics(item)}
                        on:keydown={(e) =>
                            (e.key === "Enter" || e.key === " ") &&
                            openLyrics(item)}
                    >
                        <span class="codicon codicon-music"></span>
                        <span>{item.label}</span>
                    </div>
                </li>
            {/each}
        </ul>
    {/if}

    <div
        class="header section-header"
        role="button"
        tabindex="0"
        on:click={() => (raceStoriesExpanded = !raceStoriesExpanded)}
        on:keydown={(e) =>
            (e.key === "Enter" || e.key === " ") &&
            (raceStoriesExpanded = !raceStoriesExpanded)}
        style="cursor: pointer; border-top: 1px solid var(--vscode-editorGroup-border);"
    >
        <h3 style="display: flex; align-items: center;">
            <span
                class="codicon codicon-{raceStoriesExpanded
                    ? 'chevron-down'
                    : 'chevron-right'}"
                style="margin-right: 5px;"
            ></span>
            RACE STORIES
        </h3>
    </div>
    {#if raceStoriesExpanded}
        <ul
            class="tree race-tree"
            style="flex: 0 0 auto; max-height: 300px; border-top: 1px solid var(--vscode-editorGroup-border);"
        >
            {#if raceStoriesList.length === 0}
                <li style="padding: 5px 10px; color: #888;">
                    No race stories found or loading...
                </li>
            {/if}
            {#each raceStoriesList as item}
                <li>
                    <div
                        class="tree-item"
                        role="button"
                        tabindex="0"
                        on:click={() => openRaceStory(item)}
                        on:keydown={(e) =>
                            (e.key === "Enter" || e.key === " ") &&
                            openRaceStory(item)}
                    >
                        <span class="codicon codicon-run"></span>
                        <span>{item.label}</span>
                    </div>
                </li>
            {/each}
        </ul>
    {/if}

    <div
        class="header section-header"
        role="button"
        tabindex="0"
        on:click={() => (settingsExpanded = !settingsExpanded)}
        on:keydown={(e) =>
            (e.key === "Enter" || e.key === " ") &&
            (settingsExpanded = !settingsExpanded)}
        style="cursor: pointer; border-top: 1px solid var(--vscode-editorGroup-border);"
    >
        <h3 style="display: flex; align-items: center;">
            <span
                class="codicon codicon-{settingsExpanded
                    ? 'chevron-down'
                    : 'chevron-right'}"
                style="margin-right: 5px;"
            ></span>
            HACHIMI CONTROLS
        </h3>
    </div>
    {#if settingsExpanded}
        <div
            style="padding: 10px; display: flex; flex-direction: column; gap: 4px;"
        >
            <button
                class="settings-btn"
                on:click={() => {
                    loadCategories();
                    loadLyrics();
                    loadRaceStories();
                }}
            >
                Reload localized data
            </button>

            <button class="settings-btn" on:click={selectTranslationFolder}>
                {#if $appConfig.translationPath}
                    Change translation folder
                {:else}
                    Set translation folder
                {/if}
            </button>

            <button
                class="settings-btn"
                on:click={() =>
                    appConfig.update((c) => ({ ...c, translationPath: "" }))}
            >
                Revert translation folder
            </button>

            <div style="margin-top: 10px; opacity: 0.6; font-size: 10px;">
                Game Data: {$appConfig.gamePath || "Not set"}
                <button
                    on:click={selectGameFolder}
                    style="text-decoration: underline; padding: 0; margin-left: 5px; color: var(--vscode-textLink-foreground);"
                >
                    Change
                </button>
            </div>
        </div>
    {/if}
</div>

<style>
    .sidebar {
        width: 300px;
        height: 100%;
        background-color: var(--vscode-sideBar-background);
        border-right: 1px solid var(--vscode-editorGroup-border);
        display: flex;
        flex-direction: column;
        font-size: 13px;
        user-select: none;
    }
    .header {
        padding: 10px;
        display: flex;
        justify-content: space-between;
        align-items: center;
        border-bottom: 1px solid var(--vscode-editorGroup-border);
    }
    h3 {
        margin: 0;
        font-size: 11px;
        font-weight: bold;
        color: var(--vscode-sideBarTitle-foreground, #bbb);
    }
    button {
        background: none;
        border: none;
        color: var(--vscode-icon-foreground);
        cursor: pointer;
    }
    .tree {
        list-style: none;
        padding: 0;
        margin: 0;
        overflow-y: auto;
        flex: 1;
    }
    .tree-item {
        display: flex;
        align-items: center;
        padding: 3px 10px;
        cursor: pointer;
        color: var(--vscode-sideBar-foreground);
    }
    .tree-item:hover {
        background-color: var(--vscode-list-hoverBackground);
    }
    .codicon {
        margin-right: 5px;
        font-size: 14px;
    }
    .sub-tree {
        list-style: none;
        padding-left: 15px;
    }
    .group-item {
        color: var(--vscode-foreground);
    }
    .story-item {
        color: var(--vscode-foreground);
    }
    .error {
        color: red;
        padding: 10px;
        font-size: 11px;
    }
    .settings-btn {
        display: block;
        width: 100%;
        padding: 6px 12px;
        background-color: var(--vscode-button-background);
        color: var(--vscode-button-foreground);
        border: none;
        border-radius: 2px;
        cursor: pointer;
        font-size: 11px;
        text-align: center;
        margin-bottom: 2px;
    }
    .settings-btn:hover {
        background-color: var(--vscode-button-hoverBackground);
    }
</style>
