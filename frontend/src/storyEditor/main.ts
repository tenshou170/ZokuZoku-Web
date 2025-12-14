import '../app.css'
import "@vscode/codicons/dist/codicon.css"
import App from './App.svelte'
import initSync from "hachimi_lib";
import { initController } from '../controller';

initSync();
initController();

const app = new App({
    target: document.getElementById('app')!,
})

export default app
