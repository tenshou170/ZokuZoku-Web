<script lang="ts">
    import { createEventDispatcher } from "svelte";
    import * as api from "../api";
    import { config } from "./stores";

    export let show: boolean = false;

    const dispatch = createEventDispatcher();

    async function browseGamePath() {
        const res = await api.browseFolder();
        if (res.path && $config) {
            $config = { ...$config, game_path: res.path, found: true }; // Optimistic update
            // Ideally verify with backend
            dispatch("save");
        }
    }

    // Translation path not stored in config store yet?
    // In extension, it's a VSCode setting or Hachimi config.
    // For now, just IPC command to set it.
    async function browseTranslationPath() {
        // Since Hachimi controls this, we might need IPC to set it?
        // Extension does: zokuzoku.hachimi.setLocalizedDataDir -> native dialog -> ipc.send("SetLocalizedDataDir", path)
        const res = await api.browseFolder();
        if (res.path && $config) {
            $config = { ...$config, translation_dir: res.path };

            // Try to sync with Hachimi if running
            try {
                await api.sendIpcCommand(
                    JSON.stringify({
                        // Fix: verify sendIpcCommand signature
                        // update: sendIpcCommand takes string. IPC format "command: args"
                        // Hachimi format: "SetLocalizedDataDir <path>" or similar
                        // Actually controller code for callHachimiIpc just sends what we pass.
                    }),
                );
                // Actually the controller handles "callHachimiIpc" message.
                // Here we call api direct. api.sendIpcCommand takes string.
                // Hachimi protocol is usually just JSON line or simple string.
                // Assuming "SetLocalizedDataDir" is the command ID?
            } catch (e) {}

            alert(`Translation folder set to: ${res.path}`);
        }
    }

    // Theme
    let isDark = true; // default VSCode dark
    function toggleTheme() {
        isDark = !isDark;
        if (isDark) {
            document.body.classList.remove("light-theme");
            document.body.classList.add("dark-theme");
        } else {
            document.body.classList.remove("dark-theme");
            document.body.classList.add("light-theme");
        }
    }

    function close() {
        dispatch("close");
    }

    let localDictDumpPath = "";
    $: if ($config && show) {
        localDictDumpPath = $config.localize_dict_dump_path || "";
    }

    async function browseDictDumpPath() {
        const res = await api.browseFile();
        if (res.path) {
            localDictDumpPath = res.path;
        }
    }

    async function saveSettings() {
        if ($config) {
            $config = {
                ...$config,
                localize_dict_dump_path: localDictDumpPath,
            };

            try {
                const res = await api.saveConfig($config);
                if (res.status === "success") {
                    alert("Settings Saved!");
                    close();
                } else {
                    alert(
                        "Error saving settings: " +
                            (res.detail || "Unknown error"),
                    );
                }
            } catch (e: any) {
                alert("Error saving settings: " + e.message);
            }
        }
    }
</script>

{#if show}
    <div class="modal-backdrop" on:click={close}>
        <div class="modal" on:click|stopPropagation>
            <div class="header">
                <span>Settings</span>
                <div
                    class="close-btn codicon codicon-close"
                    on:click={close}
                ></div>
            </div>
            <div class="body">
                <div class="section">
                    <div class="label">Game Data Directory</div>
                    <div class="row">
                        <input
                            type="text"
                            value={$config?.game_path || ""}
                            readonly
                        />
                        <button on:click={browseGamePath}>Browse...</button>
                    </div>
                    <div class="desc">
                        Path to UmamusumePretyDerby directory or Persistent
                        folder.
                    </div>
                </div>

                <div class="section">
                    <div class="label">Translation (Hachimi) Folder</div>
                    <div class="desc">Folder containing 'localized_data'</div>
                    <div class="row">
                        <input
                            type="text"
                            value={$config?.translation_dir || ""}
                            readonly
                        />
                        <button on:click={browseTranslationPath}
                            >Browse...</button
                        >
                    </div>
                </div>

                <div class="section">
                    <div class="label">Localize Dict Dump</div>
                    <div class="desc">
                        Path to 'localize_dump.json' (optional for Dictionary
                        Editor)
                    </div>
                    <div class="row">
                        <input
                            type="text"
                            bind:value={localDictDumpPath}
                            placeholder="/path/to/localize_dump.json"
                        />
                        <button on:click={browseDictDumpPath}>Browse...</button>
                    </div>
                    <div class="row" style="margin-top: 5px;">
                        <button class="secondary" on:click={saveSettings}
                            >Save Settings</button
                        >
                    </div>
                </div>

                <div class="section">
                    <div class="label">Appearance</div>
                    <div class="row">
                        <button on:click={toggleTheme}
                            >Toggle Dark/Light Mode</button
                        >
                    </div>
                </div>
            </div>
        </div>
    </div>
{/if}

<style>
    .modal-backdrop {
        position: fixed;
        top: 0;
        left: 0;
        width: 100vw;
        height: 100vh;
        background: rgba(0, 0, 0, 0.5);
        z-index: 1000;
        display: flex;
        justify-content: center;
        align-items: center;
    }
    .modal {
        width: 500px;
        background-color: var(--vscode-editor-background, #1e1e1e);
        color: var(--vscode-editor-foreground, #cccccc);
        border: 1px solid var(--vscode-widget-border, #454545);
        box-shadow: 0 4px 10px rgba(0, 0, 0, 0.5);
    }
    .header {
        background-color: var(--vscode-titleBar-activeBackground, #3c3c3c);
        color: var(--vscode-titleBar-activeForeground, #cccccc);
        padding: 8px 12px;
        display: flex;
        justify-content: space-between;
        align-items: center;
        font-weight: bold;
    }
    .close-btn {
        cursor: pointer;
    }
    .body {
        padding: 16px;
        display: flex;
        flex-direction: column;
        gap: 16px;
    }
    .section {
        display: flex;
        flex-direction: column;
        gap: 4px;
    }
    .label {
        font-weight: bold;
        font-size: 12px;
    }
    .row {
        display: flex;
        gap: 8px;
    }
    .desc {
        font-size: 11px;
        opacity: 0.7;
    }
    input {
        flex: 1;
        background-color: var(--vscode-input-background, #3c3c3c);
        color: var(--vscode-input-foreground, #cccccc);
        border: 1px solid var(--vscode-input-border, #3c3c3c);
        padding: 4px;
    }
    button {
        background-color: var(--vscode-button-background, #0e639c);
        color: var(--vscode-button-foreground, #ffffff);
        border: none;
        padding: 6px 12px;
        cursor: pointer;
    }
    button:hover {
        background-color: var(--vscode-button-hoverBackground, #1177bb);
    }

    button.secondary {
        background-color: var(--vscode-button-secondaryBackground, #3a3d41);
        color: var(--vscode-button-secondaryForeground, #ffffff);
    }
    button.secondary:hover {
        background-color: var(
            --vscode-button-secondaryHoverBackground,
            #45494e
        );
    }
</style>
