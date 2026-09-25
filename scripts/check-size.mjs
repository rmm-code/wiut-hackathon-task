import { readdir, readFile } from 'node:fs/promises';
import { extname, join } from 'node:path';

const extensions = new Set(['.ts', '.tsx', '.js', '.jsx', '.mjs', '.py', '.css']);
const violations = [];
let largest = { path: '', lines: 0 };

async function inspect(directory) {
  for (const entry of await readdir(directory, { withFileTypes: true })) {
    const path = join(directory, entry.name);
    if (entry.isDirectory()) await inspect(path);
    else if (extensions.has(extname(path))) {
      const lines = (await readFile(path, 'utf8')).trimEnd().split('\n').length;
      if (lines > largest.lines) largest = { path, lines };
      if (lines > 700) violations.push(`${path}: ${lines} lines`);
    }
  }
}

await inspect('web/src');
await inspect('web/tests');
await inspect('scripts');
await inspect('vision');
await inspect('api');
await inspect('tests');
if (violations.length) {
  console.error(violations.join('\n'));
  process.exitCode = 1;
} else {
  console.log(`All authored source files are within 700 lines. Largest: ${largest.path} (${largest.lines}).`);
}
