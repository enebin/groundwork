// Test data tools. Usage: DATA_DIR=./data node tools.js reset | save <name> | restore <name>
const fs = require('fs');
const path = require('path');

const DATA_DIR = process.env.DATA_DIR || path.join(__dirname, 'data');
const DB_FILE = path.join(DATA_DIR, 'db.json');
const CHECKPOINTS = path.join(DATA_DIR, 'checkpoints');
const [command, name] = process.argv.slice(2);

if (command === 'reset') {
  fs.rmSync(DB_FILE, { force: true });
  console.log('Data reset');
} else if (command === 'save' && name) {
  fs.mkdirSync(CHECKPOINTS, { recursive: true });
  fs.copyFileSync(DB_FILE, path.join(CHECKPOINTS, `${name}.json`));
  console.log(`Saved checkpoint ${name}`);
} else if (command === 'restore' && name) {
  fs.mkdirSync(DATA_DIR, { recursive: true });
  fs.copyFileSync(path.join(CHECKPOINTS, `${name}.json`), DB_FILE);
  console.log(`Restored checkpoint ${name}`);
} else {
  console.error('Usage: node tools.js reset | save <name> | restore <name>');
  process.exit(1);
}
