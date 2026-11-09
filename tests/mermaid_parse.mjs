// Parses every ```mermaid block of a markdown file with the real mermaid parser under jsdom.
// Setup once, outside the repo: mkdir -p ~/.cache/mm && cd ~/.cache/mm && npm i mermaid jsdom
// Run: NODE_PATH=~/.cache/mm/node_modules node tests/mermaid_parse.mjs docs/ARCHITECTURE.md
import { createRequire } from 'module';
import fs from 'fs';
const require = createRequire((process.env.NODE_PATH || '.') + '/');   // ESM imports ignore NODE_PATH
const { JSDOM } = require('jsdom');
const dom = new JSDOM('<!DOCTYPE html><body></body>', { pretendToBeVisual: true });
globalThis.window = dom.window; globalThis.document = dom.window.document;
Object.defineProperty(globalThis, "navigator", { value: dom.window.navigator, configurable: true });
const mermaid = (await import(require.resolve('mermaid'))).default;
mermaid.initialize({ startOnLoad: false });
const md = fs.readFileSync(process.argv[2], 'utf8').split('\n');
let blocks = [], cur = null, start = 0;
md.forEach((l, i) => { if (l.trim().startsWith('```mermaid')) { cur = []; start = i + 2; } else if (cur && l.trim() === '```') { blocks.push({ start, text: cur.join('\n') }); cur = null; } else if (cur) cur.push(l); });
let bad = 0;
for (const b of blocks) { try { await mermaid.parse(b.text); console.log(`ok   block at line ${b.start}`); } catch (e) { bad++; console.log(`FAIL block at line ${b.start}: ${String(e.message).split('\n').slice(0, 3).join(' | ')}`); } }
process.exit(bad ? 1 : 0);
