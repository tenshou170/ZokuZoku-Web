<script lang="ts">
    import { createEventDispatcher } from "svelte";

    export let title: string;
    export let expanded: boolean = false;
    export let actions: { icon: string; title: string; id: string }[] = [];

    const dispatch = createEventDispatcher();

    let isOpen = expanded;
    $: isOpen = expanded; // If prop changes externally, update local
    // Allow local toggle to diverge if user interacts?
    // Actually, if we do `isOpen = expanded`, then local toggle `isOpen = !isOpen` might be overwritten if parent updates.
    // Better: Helper function that updates local, and maybe notifies?

    // For this simple sidebar, just let local take precedence after init?
    // Svelte 3: `let isOpen = expanded` only runs once.
    // If we want to support parent strictly controlling it, we shouldn't have local state.
    // But parent passes generic `true` for "ALL STORIES".

    function toggle() {
        // We want to toggle local state.
        // But if we have `$: isOpen = expanded;`, then on next cycle if `expanded` is still true, does it overwrite?
        // Yes, reactive declarations run when dependencies change.
        // If `expanded` prop doesn't change, the line doesn't re-run.
        // So `isOpen = !isOpen` is safe.
        isOpen = !isOpen;
    }

    function onAction(id: string, e: MouseEvent) {
        e.stopPropagation();
        dispatch("action", id);
    }
</script>

<div class="sidebar-section">
    <div class="header" on:click={toggle}>
        <div class="title-container">
            <span
                class="codicon codicon-chevron-right chevron"
                class:expanded={isOpen}
            ></span>
            <span class="title">{title}</span>
        </div>
        <div class="actions">
            {#each actions as action}
                <div
                    class="action-btn codicon codicon-{action.icon}"
                    title={action.title}
                    on:click={(e) => onAction(action.id, e)}
                ></div>
            {/each}
        </div>
    </div>
    {#if isOpen}
        <div class="content">
            <slot />
        </div>
    {/if}
</div>

<style>
    .sidebar-section {
        border-bottom: 1px solid var(--vscode-sideBarSectionHeader-border, #333);
        display: flex;
        flex-direction: column;
    }

    .header {
        display: flex;
        align-items: center;
        justify-content: space-between;
        padding: 4px 4px 4px 8px;
        cursor: pointer;
        background-color: var(
            --vscode-sideBarSectionHeader-background,
            #252526
        );
        color: var(--vscode-sideBarSectionHeader-foreground, #ccc);
        font-size: 11px;
        font-weight: bold;
        text-transform: uppercase;
    }

    .header:hover {
        background-color: var(--vscode-list-hoverBackground, #2a2d2e);
    }

    .title-container {
        display: flex;
        align-items: center;
        overflow: hidden;
    }

    .chevron {
        margin-right: 4px;
        transition: transform 0.1s ease;
        font-size: 12px;
    }

    .chevron.expanded {
        transform: rotate(90deg);
    }

    .title {
        white-space: nowrap;
        text-overflow: ellipsis;
        overflow: hidden;
    }

    .actions {
        display: flex;
        align-items: center;
        opacity: 0; /* Only show on hover usually, but VSCode keeps them visible often? */
        /* VSCode shows them on hover of the header */
    }

    .header:hover .actions {
        opacity: 1;
    }

    .action-btn {
        margin-left: 4px;
        padding: 2px;
        cursor: pointer;
        border-radius: 3px;
    }

    .action-btn:hover {
        background-color: var(
            --vscode-toolbar-hoverBackground,
            rgba(90, 93, 94, 0.31)
        );
    }

    .content {
        /* No fixed height, let it grow? VSCode sections usually are flex or fixed */
        /* For simple mimic, just flow */
        padding-bottom: 5px;
        flex: 1; /* If we want it to take space? */
    }
</style>
