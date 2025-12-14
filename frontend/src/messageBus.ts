export type MessageHandler = (message: any) => void;

const listeners: MessageHandler[] = [];

export function onMessage(callback: MessageHandler) {
    listeners.push(callback);
    return () => {
        const index = listeners.indexOf(callback);
        if (index > -1) {
            listeners.splice(index, 1);
        }
    };
}

export function postMessageToController(message: any) {
    listeners.forEach(l => l(message));
}
