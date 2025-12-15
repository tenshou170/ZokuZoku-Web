<script lang="ts">
    import { makeContentDisplayValue } from "./utils";
    import type { TreeNodeId } from "../sharedTypes";
    import { config } from "./stores";
    import ColorText from "./ColorText.svelte";

    export let readonly: boolean;
    export let multiline: boolean;
    export let link: TreeNodeId | null;
    export let active: boolean;
    export let value: string | null;
    export let placeholder: string;
    export let title: string | null;
    export const userData: any = undefined;

    // unused
    const _ = { multiline, link, active, placeholder };

    $: fontSize = 13.78 * ($config?.fontSizeMultiplier ?? 1);
    $: lineWidth = Math.round(21 / ($config?.fontSizeMultiplier ?? 1));
    $: lineHeight = 1.5 * ($config?.lineSpacingMultiplier ?? 1);

    $: displayValue = makeContentDisplayValue(
        value,
        lineWidth,
        $config,
        readonly,
    );

    import { voiceCues } from "./stores";
    import { currentPath } from "../stores";

    $: currentNodeId =
        $currentPath && $currentPath.length > 0
            ? $currentPath[$currentPath.length - 1]
            : null;
    $: voiceUrl = currentNodeId ? $voiceCues[currentNodeId] : null;

    function playVoice() {
        if (voiceUrl) {
            new Audio(voiceUrl).play();
        }
    }

    function handleKeydown(e: KeyboardEvent) {
        if (e.key === "Enter" || e.key === " ") {
            playVoice();
        }
    }
</script>

<div
    class="content"
    {title}
    on:focus
    on:blur
    on:keydown
    on:mousemove
    on:click
    style="font-size: {fontSize}cqh; line-height: {lineHeight};"
>
    <ColorText content={displayValue} translated={!readonly} />
    {#if voiceUrl}
        <div
            class="voice-btn codicon codicon-play"
            role="button"
            tabindex="0"
            on:click|stopPropagation={playVoice}
            on:keydown|stopPropagation={handleKeydown}
            title="Play Voice"
        ></div>
    {/if}
</div>

<style>
    .content {
        font-family: "CustomFont", var(--vscode-font-family);
        background-color: rgba(255, 255, 255, 0.9);
        aspect-ratio: 43/13;
        border: 1.282cqh solid #68d25d;
        box-sizing: border-box;
        border-radius: 14.34%/50%;
        overflow: visible;
        white-space: pre;
        /*font-size: 13.78cqh;*/
        padding: 22.7564cqh 7.1705cqw;
        color: #794016;
        /*line-height: 20.51cqh;*/
        letter-spacing: -0.01515152em;
        min-height: 0;
        position: relative;
    }

    .voice-btn {
        position: absolute;
        bottom: 5%;
        right: 2%;
        font-size: 20px; /* Use px or cqh? cqh might be better for scaling */
        cursor: pointer;
        color: #794016;
        opacity: 0.7;
    }
    .voice-btn:hover {
        opacity: 1;
        transform: scale(1.1);
    }
</style>
