#!/usr/bin/env node
import { createRequire } from "node:module";
import { readFile, readdir, writeFile, mkdir } from "node:fs/promises";
import { dirname, resolve } from "node:path";
import { gzipSync, gunzipSync } from "node:zlib";

const argv = process.argv.slice(2);
const option = (name) => {
  const index = argv.indexOf(`--${name}`);
  return index === -1 ? undefined : argv[index + 1];
};
const sourceDir = option("source") && resolve(option("source"));
const outputPath = option("output") && resolve(option("output"));
const title = option("title");
const description = option("description") ?? "Reusable Cloudflare OS Gadget Blueprint.";
const authorName = option("author") ?? "Cloudflare OS Gadget Builder";

if (!sourceDir || !outputPath || !title) {
  console.error("usage: package-gadget.mjs --source DIR --output FILE.gadget --title TITLE [--description TEXT] [--author NAME]");
  process.exit(2);
}

const requireFromCwd = createRequire(resolve(process.cwd(), "package.json"));
let Y;
try {
  Y = requireFromCwd("yjs");
} catch {
  throw new Error("Cannot resolve yjs. Run through `pnpm --filter @gadgets/workshop-backend exec node ...` from a Cloudflare OS repository.");
}

const names = (await readdir(sourceDir)).filter((name) => !name.startsWith(".")).sort();
for (const required of ["server.js", "client.js"]) {
  if (!names.includes(required)) throw new Error(`Missing required file: ${required}`);
}
const server = await readFile(resolve(sourceDir, "server.js"), "utf8");
if (!/export\s+class\s+Gadget\s+extends\s+DurableObject/.test(server)) {
  throw new Error("server.js must export `class Gadget extends DurableObject`.");
}

const doc = new Y.Doc();
const files = doc.getMap("");
for (const name of names) {
  const path = resolve(sourceDir, name);
  const text = await readFile(path, "utf8");
  files.set(name, new Y.Text(text));
}
const compressed = gzipSync(Y.encodeStateAsUpdateV2(doc));
const now = new Date().toISOString();
const metadata = {
  title,
  description,
  author: { type: "user", name: authorName, id: authorName.toLowerCase().replace(/[^a-z0-9]+/g, "-") },
  created: now,
  version: 1,
  lastUpdated: now,
  bindings: {},
};
const metadataBytes = Buffer.from(JSON.stringify(metadata));
const prefix = Buffer.alloc(24);
prefix.writeBigUInt64BE(0xec2e2d3a2300e317n, 0);
prefix.writeUInt32BE(1, 8);
prefix.writeUInt32BE(metadataBytes.length, 12);
prefix.writeBigUInt64BE(BigInt(compressed.length), 16);
const archive = Buffer.concat([prefix, metadataBytes, compressed]);

// Decode once before writing so packaging bugs fail locally instead of at upload time.
const metadataLength = archive.readUInt32BE(12);
const contentLength = Number(archive.readBigUInt64BE(16));
if (archive.readBigUInt64BE(0) !== 0xec2e2d3a2300e317n || archive.readUInt32BE(8) !== 1) {
  throw new Error("Archive prefix validation failed.");
}
const tail = archive.subarray(24 + metadataLength);
if (tail.length !== contentLength) throw new Error("Archive length validation failed.");
const verifyDoc = new Y.Doc();
Y.applyUpdateV2(verifyDoc, gunzipSync(tail));
for (const required of ["server.js", "client.js"]) {
  if (!verifyDoc.getMap("").has(required)) throw new Error(`Snapshot validation lost ${required}.`);
}

await mkdir(dirname(outputPath), { recursive: true });
await writeFile(outputPath, archive);
console.log(`${outputPath} (${archive.length} bytes, ${names.length} files)`);
