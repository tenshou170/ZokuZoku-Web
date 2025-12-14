<script lang="ts">
    import { createEventDispatcher } from "svelte";
    import StoryTreeItem from "./StoryTreeItem.svelte";

    export let stories: any[] = [];
    export let config: any = null;

    const dispatch = createEventDispatcher();

    let treeNodes: any[] = [];

    $: treeNodes = buildTree(stories);

    function buildTree(flatStories: any[]): any[] {
        const root: any[] = [];
        const categoryMap = new Map<string, any>();

        for (const story of flatStories) {
            // Level 1: Category
            let catName = story.category || "Uncategorized";
            let catNode = categoryMap.get(catName);
            if (!catNode) {
                catNode = {
                    type: "category",
                    id: `cat_${catName}`,
                    name: catName,
                    children: [],
                    icon: "library",
                };
                categoryMap.set(catName, catNode);
                root.push(catNode);
            }

            // Level 2: Group (Optional)
            let parentChildren = catNode.children;
            if (story.group) {
                let grpName = story.group;
                let groupNode = parentChildren.find(
                    (c: any) => c.id === `grp_${catName}_${grpName}`,
                );
                if (!groupNode) {
                    groupNode = {
                        type: "category",
                        id: `grp_${catName}_${grpName}`,
                        name: grpName,
                        children: [],
                        icon: "folder",
                    };
                    parentChildren.push(groupNode);
                }
                parentChildren = groupNode.children;
            }

            // Level 3: Leaf
            parentChildren.push({
                type: "entry",
                id: story.id,
                name: story.id,
                path: story.path,
                // store full story object data if needed
                story: story,
            });
        }

        return root;
    }

    function onSelect(e: any) {
        dispatch("select", e.detail.story);
    }

    function onReload() {
        dispatch("reload");
    }
</script>

<div class="sidebar">
    <div class="header">
        <span class="title">EXPLORER</span>
        <div class="actions">
            <button
                class="icon-btn codicon codicon-refresh"
                title="Reload Stories"
                on:click={onReload}
            ></button>
        </div>
    </div>

    {#if config && config.game_path}
        <div class="path-info">
            <span class="codicon codicon-link"></span>
            <span class="path-text" title={config.game_path}
                >{config.game_path}</span
            >
        </div>
    {/if}

    <div class="tree-container">
        <ul>
            {#each treeNodes as node}
                <StoryTreeItem {node} on:select={onSelect} />
            {/each}
        </ul>

        {#if stories.length === 0}
            <div class="empty-msg">No stories loaded.</div>
        {/if}
    </div>
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
    }

    .header {
        padding: 10px 15px;
        font-size: 11px;
        font-weight: bold;
        display: flex;
        justify-content: space-between;
        align-items: center;
        background-color: var(--vscode-sideBarSectionHeader-background);
    }

    .path-info {
        padding: 4px 10px;
        font-size: 11px;
        opacity: 0.7;
        display: flex;
        align-items: center;
        border-bottom: 1px solid #333;
    }

    .path-text {
        margin-left: 5px;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
    }

    .tree-container {
        flex: 1;
        overflow-y: auto;
        padding-top: 4px;
    }

    ul {
        padding: 0;
        margin: 0;
    }

    .empty-msg {
        padding: 20px;
        opacity: 0.5;
        text-align: center;
    }

    .icon-btn {
        background: none;
        border: none;
        color: inherit;
        cursor: pointer;
    }
    .icon-btn:hover {
        color: var(--vscode-foreground);
    }
</style>
