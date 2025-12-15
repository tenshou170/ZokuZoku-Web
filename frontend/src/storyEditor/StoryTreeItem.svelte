<script lang="ts">
    import { createEventDispatcher } from "svelte";

    export let node: any;

    // Internal state for expansion
    let open = false;

    const dispatch = createEventDispatcher();

    function toggle() {
        open = !open;
    }

    function select() {
        dispatch("select", { story: node });
    }

    // Bubble up events
    function forward(e: any) {
        dispatch("select", e.detail);
    }
</script>

<li class="tree-item">
    {#if node.type === "category"}
        <div class="row category" on:click={toggle}>
            <div
                class="codicon codicon-{open
                    ? 'chevron-down'
                    : 'chevron-right'}"
            ></div>
            <span class="icon codicon codicon-{node.icon || 'folder'}"></span>
            <span class="label">{node.name}</span>
        </div>
        {#if open}
            <ul class="children">
                {#each node.children as child}
                    <svelte:self node={child} on:select={forward} />
                {/each}
            </ul>
        {/if}
    {:else}
        <!-- Entry -->
        <div class="row entry" on:click={select}>
            <span class="indent"></span>
            <span class="icon codicon codicon-file-code"></span>
            <span class="label">{node.name}</span>
        </div>
    {/if}
</li>

<style>
    ul,
    li {
        list-style: none;
        padding: 0;
        margin: 0;
    }

    .children {
        padding-left: 12px;
        border-left: 1px solid var(--vscode-tree-inactiveIndentGuidesStroke);
        margin-left: 10px;
    }

    .row {
        display: flex;
        align-items: center;
        cursor: pointer;
        padding: 2px 4px;
        color: var(--vscode-sideBar-foreground);
        font-size: 13px;
        height: 22px;
    }

    .row:hover {
        background-color: var(--vscode-list-hoverBackground);
    }

    .icon {
        margin-right: 6px;
    }

    .codicon {
        font-family: "codicon";
        font-size: 14px;
    }

    .indent {
        width: 16px; /* spacing for no chevron */
    }

    .label {
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
    }

    .category {
        font-weight: bold;
    }
</style>
