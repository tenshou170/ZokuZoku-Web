import type { ControllerMessage, ITextSlot, ITreeNode, TreeNodeId } from "./sharedTypes";
import { currentNav, currentPath, currentTextSlots, originalTextSlots, selectedNodes } from "./stores";
import { postMessageToController } from "./messageBus";

export function findNodeByPath(path: TreeNodeId[], nodes: ITreeNode[]): [ITreeNode, ITreeNode[]] | null {
    if (!path.length) return null;

    for (const node of nodes) {
        if (node.id == path[0]) {
            if (path.length == 1) {
                return [node, nodes];
            }
            else if (node.type == "category") {
                return findNodeByPath(path.slice(1), node.children)
            }
            else {
                return null;
            }
        }
    }

    return null;
}

export function getNodeTlContent(entryPath: TreeNodeId[], contentCount: number): Promise<(string | null)[]> {
    return new Promise(resolve => {
        const res: (string | null)[] = [];
        const setIndexes = new Set<number>();
        const onMessage = (e: MessageEvent) => {
            const message: ControllerMessage = e.data;
            if (message.type == "setTextSlotContent" &&
                message.entryPath.join("/") == entryPath.join("/")) {
                res[message.index] = message.content;
                setIndexes.add(message.index);
                if (setIndexes.size == contentCount) {
                    resolve(res);
                    window.removeEventListener("message", onMessage);
                }
            }
        };
        window.addEventListener("message", onMessage);
        for (let i = 0; i < contentCount; ++i) {
            postMessageToController({
                type: "getTextSlotContent",
                entryPath,
                index: i
            });
        }
    });
}

export function gotoNode(node: ITreeNode, path: TreeNodeId[]) {
    if (node.type != "entry") return;
    selectedNodes.update(() => ({ [path.join("/")]: node.content.length }));
    currentPath.update(() => path);

    // Deep copy content to originalTextSlots to prevent reference sharing
    const contentCopy = JSON.parse(JSON.stringify(node.content));
    originalTextSlots.set(contentCopy);

    currentTextSlots.update(() => node.content);
    currentNav.update(() => ({
        next: node.next,
        prev: node.prev
    }));
}

export function translatedSlotProps(slot: ITextSlot) {
    return {
        ...slot,
        content: undefined,
        postContent: true
    }
}