import { derived, writable } from "svelte/store";
import type { ITextSlot, ITreeNode, TreeNodeId } from "./sharedTypes";
// Restore types
export interface WorkspaceState {
    currentPath: TreeNodeId[];
    explorerScrollTop: number;
    nodeStates: { [key: string]: NodeState };
    selectedNodes: { [key: string]: number }; // value is the content count
    copyingNodes: { [key: string]: number };
    userData: unknown;
}

export interface NodeState {
    open: boolean,
    childrenStart: number
}

const STORAGE_KEY = "zokuzoku_workspace_state";
let initWsState: WorkspaceState | undefined;
try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (raw) {
        initWsState = JSON.parse(raw);
    }
} catch (e) {
    console.warn("Failed to load workspace state", e);
}

export const currentPath = writable<TreeNodeId[]>(initWsState?.currentPath ?? []);
export const explorerScrollTop = writable<number>(initWsState?.explorerScrollTop ?? 0);
export const nodeStates = writable<{ [key: string]: NodeState }>(initWsState?.nodeStates ?? {});
export const selectedNodes = writable<{ [key: string]: number }>(initWsState?.selectedNodes ?? {});
export const copyingNodes = writable<{ [key: string]: number }>(initWsState?.copyingNodes ?? {});
export const userData = writable(initWsState?.userData);

const workspaceState = derived(
    [currentPath, explorerScrollTop, nodeStates, selectedNodes, copyingNodes, userData],
    ([currentPath, explorerScrollTop, nodeStates, selectedNodes, copyingNodes, userData]) => ({
        currentPath,
        explorerScrollTop,
        nodeStates,
        selectedNodes,
        copyingNodes,
        userData
    })
);
workspaceState.subscribe(state => {
    try {
        localStorage.setItem(STORAGE_KEY, JSON.stringify(state));
    } catch { }
});


/**** Session stores ****/

export const currentTextSlots = writable<ITextSlot[]>([]);
export const originalTextSlots = writable<ITextSlot[]>([]);
export const currentNav = writable<{
    next?: TreeNodeId,
    prev?: TreeNodeId
}>({});
export const currentSiblings = writable<ITreeNode[]>([]);