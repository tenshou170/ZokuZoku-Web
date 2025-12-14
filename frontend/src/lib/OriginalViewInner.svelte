<script lang="ts">
    import { currentTextSlots } from "../stores";
    import type { IPanelAction } from "../types";
    import GenericSlots from "./GenericSlots.svelte";
    import TextSlot from "./TextSlot.svelte";
    import type { ControllerMessage } from "../sharedTypes";
    import { postMessageToController } from "../messageBus";

    export let actions: (IPanelAction | null)[] | undefined = undefined;

    function onMessage(e: MessageEvent<ControllerMessage>) {
        const message = e.data;
        if (message.type == "enableVoicePlayer") {
            actions = [
                {
                    icon: "unmute",
                    tooltip: "Play voice clip",
                    onClick: () => {
                        postMessageToController({ type: "loadVoice" });
                    },
                },
            ];
        }
    }
</script>

<svelte:window on:message={onMessage} />

<GenericSlots>
    {#each $currentTextSlots as slot}
        <TextSlot readonly {...slot} />
    {/each}
</GenericSlots>
