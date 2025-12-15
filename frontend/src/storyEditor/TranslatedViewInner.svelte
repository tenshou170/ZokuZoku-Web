<script lang="ts">
    import { currentPath, currentTextSlots, currentNav } from "../stores";
    import type { IPanelAction } from "../types";
    import { translatedSlotProps } from "../utils";
    import TextSlot from "../lib/TextSlot.svelte";
    import GenericSlots from "../lib/GenericSlots.svelte";
    import StorySplitView from "./StorySplitView.svelte";
    import { translatedPreview } from "./stores";

    const preview = translatedPreview;

    // Reactive actions to update disabled state
    // We export actions so the parent (TranslatedView) can bind to it and display them in the header.
    export let actions: (IPanelAction | null)[] = [];

    $: actions = [
        {
            icon: "arrow-up",
            tooltip: "Previous",
            disabled: !$currentNav.prev,
            onClick: () => {
                if ($currentNav.prev) $currentPath = [$currentNav.prev];
            },
        },
        {
            icon: "arrow-down",
            tooltip: "Next",
            disabled: !$currentNav.next,
            onClick: () => {
                if ($currentNav.next) $currentPath = [$currentNav.next];
            },
        },
        null,
        {
            icon: "comment",
            tooltip: "Dialogue preview",
            onClick: () =>
                ($preview = $preview == "dialogue" ? null : "dialogue"),
        },
        {
            icon: "book",
            tooltip: "Story preview",
            onClick: () => ($preview = $preview == "story" ? null : "story"),
        },
    ];

    const placeholder = "Type your translation here...";
</script>

<StorySplitView preview={$preview} translated>
    <GenericSlots>
        {#each $currentTextSlots as slot, index}
            <TextSlot
                {...translatedSlotProps(slot)}
                {index}
                entryPath={$currentPath}
                {placeholder}
            />
        {/each}
    </GenericSlots>
</StorySplitView>
