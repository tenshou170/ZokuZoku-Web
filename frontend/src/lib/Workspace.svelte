<script lang="ts">
    import { onMount } from "svelte";
    import type { ControllerMessage } from "../sharedTypes";
    import { postMessageToController } from "../messageBus";

    export let inner;

    onMount(() => postMessageToController({ type: "init" }));

    function onMessage(e: MessageEvent<ControllerMessage>) {
        const message = e.data;
        switch (message.type) {
            case "undo": {
                document.execCommand("undo");
                break;
            }
            case "redo": {
                document.execCommand("redo");
                break;
            }
        }
    }
</script>

<svelte:window on:message={onMessage} />

<svelte:component this={inner} />
