<script lang="ts">
    import { onMount } from "svelte";
    import Workspace from "../lib/Workspace.svelte";
    import WorkspaceInner from "./WorkspaceInner.svelte";
    import { postMessageToController } from "../messageBus";

    export let story: any;

    onMount(() => {
        // Trigger the load
        console.log("WorkspaceWrapper mounted for", story.id);
        postMessageToController({ type: "loadStory", story });
    });
</script>

<Workspace inner={WorkspaceInner} />
