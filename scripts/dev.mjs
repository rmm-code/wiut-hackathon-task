import { spawn } from 'node:child_process';
import { existsSync } from 'node:fs';
import { resolve } from 'node:path';

const python = resolve(process.platform === 'win32' ? '.venv/Scripts/python.exe' : '.venv/bin/python');
if (!existsSync(python)) {
  console.error('Create .venv and install requirements.txt first. See README.md.');
  process.exit(1);
}
const children = [
  spawn(python, ['-m', 'uvicorn', 'api.main:app', '--host', '127.0.0.1', '--port', '8000'], {stdio:'inherit'}),
  spawn(process.platform === 'win32' ? 'npm.cmd' : 'npm', ['--prefix', 'web', 'run', 'dev', '--', '--host', '127.0.0.1', '--port', '5173', '--strictPort'], {stdio:'inherit'}),
];
let closing = false;
function close(code = 0) {
  if (closing) return;
  closing = true;
  for (const child of children) child.kill('SIGTERM');
  process.exitCode = code;
}
process.on('SIGINT', () => close());
process.on('SIGTERM', () => close());
for (const child of children) {
  child.on('error', error => { console.error(error.message); close(1); });
  child.on('exit', code => { if (!closing) close(code ?? 1); });
}
