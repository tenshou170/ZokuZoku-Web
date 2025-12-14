<script lang="ts">
    import { currentPath, currentTextSlots } from "../stores";
    import type { IPanelAction } from "../types";
    import TextSlot from "../lib/TextSlot.svelte";
    import GenericSlots from "../lib/GenericSlots.svelte";
    import StorySplitView from "./StorySplitView.svelte";
    import { originalPreview } from "./stores";
    import { postMessageToController } from "../messageBus";

    const preview = originalPreview;
    export const actions: (IPanelAction | null)[] = [
        {
            icon: "run-all",
            tooltip: "Goto block (IPC - in game)",
            onClick: () =>
                !isNaN(+$currentPath[0]) &&
                postMessageToController({
                    type: "callHachimiIpc",
                    command: {
                        type: "StoryGotoBlock",
                        block_id: +$currentPath[0] + 1,
                        incremental: true,
                    },
                }),
        },
        {
            icon: "unmute",
            tooltip: "Play voice clip",
            onClick: () => {
                postMessageToController({ type: "loadVoice" });
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
</script>

<StorySplitView preview={$preview}>
    <GenericSlots>
        {#each $currentTextSlots as slot}
            <TextSlot readonly {...slot} />
        {/each}
    </GenericSlots>
</StorySplitView>
