<script lang="ts">
    import TextSlot from "../lib/TextSlot.svelte";
    import {
        currentPath,
        currentTextSlots,
        originalTextSlots,
    } from "../stores";
    import { translatedSlotProps } from "../utils";
    import DialogueTextFrameContent from "./DialogueTextFrameContent.svelte";
    import DialogueTextFrameName from "./DialogueTextFrameName.svelte";

    export let translated: boolean = false;
</script>

<div class="text-frame">
    {#if translated}
        {#if $currentTextSlots.length >= 2}
            <TextSlot
                inner={DialogueTextFrameName}
                {...translatedSlotProps($currentTextSlots[0])}
                index={0}
                entryPath={$currentPath}
            />
            <TextSlot
                inner={DialogueTextFrameContent}
                {...translatedSlotProps($currentTextSlots[1])}
                index={1}
                entryPath={$currentPath}
            />
        {/if}
    {:else if $originalTextSlots.length >= 2}
        <TextSlot
            inner={DialogueTextFrameName}
            readonly
            {...$originalTextSlots[0]}
        />
        <TextSlot
            inner={DialogueTextFrameContent}
            readonly
            {...$originalTextSlots[1]}
        />
    {/if}
</div>

<style>
    .text-frame {
        padding: 2.22%;
        margin-top: 2%;
        position: relative;
        aspect-ratio: 43/13;
        container-type: size;
    }
</style>
