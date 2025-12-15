<script lang="ts">
    import { createEventDispatcher } from "svelte";

    export let error: string | null = null;
    export let loading = false;
    export let config: any = null;

    const dispatch = createEventDispatcher();
    let manualPath = "";

    import { onMount } from "svelte";

    function load() {
        if (manualPath) dispatch("load", manualPath);
    }

    function retry() {
        dispatch("retry");
    }

    let isLightMode = false;

    onMount(() => {
        isLightMode = document.body.classList.contains("light-theme");
    });

    function toggleTheme() {
        isLightMode = !isLightMode;
        if (isLightMode) {
            document.body.classList.add("light-theme");
        } else {
            document.body.classList.remove("light-theme");
        }
    }
</script>

<div class="welcome-container">
    <div class="banner">
        ⚠️ This is an experimental web version. Some features may not work as
        expected.
    </div>

    <button class="theme-toggle" on:click={toggleTheme} title="Toggle Theme">
        {#if isLightMode}
            🌙
        {:else}
            ☀️
        {/if}
    </button>

    <img src="/icon.png" alt="ZokuZoku" class="logo" />
    <h1>ZokuZoku Web</h1>
    <p class="subtitle">Select a story from the sidebar to begin editing.</p>

    {#if loading}
        <p>Loading...</p>
    {:else if error}
        <div class="error-box">
            <p class="error-msg">Error: {error}</p>

            <div class="manual-input">
                <p>Use Manual Game Path:</p>
                <div class="input-row">
                    <input
                        type="text"
                        bind:value={manualPath}
                        placeholder="/path/to/data"
                    />
                    <button on:click={load}>Load</button>
                </div>
            </div>

            <div class="retry-section">
                <button class="secondary" on:click={retry}
                    >Try Auto-Detect Again</button
                >
            </div>
        </div>
    {:else if !config || !config.game_path}
        <div class="manual-input center-text">
            <p>Game path not detected. Please configure it in settings.</p>
            <div class="row">
                <button on:click={() => dispatch("openSettings")}
                    >Open Settings</button
                >
            </div>
        </div>
    {/if}
</div>

<style>
    .welcome-container {
        position: relative;
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        height: 100%;
        color: var(--vscode-foreground);
    }

    .banner {
        width: fit-content;
        max-width: 80%;
        background-color: #ef5350; /* Soft, eye-catching red */
        border: 1px solid #e53935;
        color: white;
        text-align: center;
        padding: 8px 16px;
        position: absolute;
        top: 20px;
        left: 0;
        right: 0;
        margin: 0 auto;
        font-weight: 500;
        border-radius: 4px;
        z-index: 10;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.2);
    }

    .theme-toggle {
        position: absolute;
        top: 20px;
        right: 20px;
        z-index: 11;
        background: transparent;
        border: none;
        cursor: pointer;
        font-size: 20px;
        padding: 5px;
        border-radius: 50%;
        width: 36px;
        height: 36px;
        display: flex;
        align-items: center;
        justify-content: center;
        transition: background 0.2s;
    }

    .theme-toggle:hover {
        background: rgba(128, 128, 128, 0.2);
    }

    h1 {
        font-weight: normal;
        margin-bottom: 10px;
    }

    .logo {
        width: 128px;
        height: 128px;
        margin-bottom: 20px;
        /* Optional: Drop shadow for better visibility on dark bg */
        filter: drop-shadow(0 4px 6px rgba(0, 0, 0, 0.3));
    }

    .subtitle {
        opacity: 0.7;
        margin-bottom: 40px;
    }

    .error-box {
        background-color: var(--vscode-inputValidation-errorBackground);
        border: 1px solid var(--vscode-inputValidation-errorBorder);
        padding: 20px;
        border-radius: 4px;
        max-width: 500px;
    }

    .input-row {
        display: flex;
        gap: 10px;
        margin-top: 10px;
    }

    input {
        background: var(--vscode-input-background);
        color: var(--vscode-input-foreground);
        border: 1px solid var(--vscode-input-border, transparent);
        padding: 6px;
        flex: 1;
        width: 300px;
    }

    button {
        background: var(--vscode-button-background);
        color: var(--vscode-button-foreground);
        border: none;
        padding: 6px 12px;
        cursor: pointer;
    }

    button:hover {
        background: var(--vscode-button-hoverBackground);
    }

    button.secondary {
        background: var(--vscode-button-secondaryBackground);
        color: var(--vscode-button-secondaryForeground);
        margin-top: 10px;
        width: 100%;
    }
</style>
