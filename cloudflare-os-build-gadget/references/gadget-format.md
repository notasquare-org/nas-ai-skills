# Cloudflare OS `.gadget` format

`.gadget` is an importable Blueprint archive. It contains Blueprint metadata followed by a gzip-compressed Yjs V2 snapshot whose unnamed root map stores filenames as `Y.Text` values.

Binary layout, in network byte order:

1. 8-byte magic: `0xec2e2d3a2300e317`
2. 4-byte version: `1`
3. 4-byte JSON metadata length
4. 8-byte compressed content length
5. UTF-8 Blueprint metadata JSON
6. gzip-compressed Yjs snapshot

Required Gadget files:

- `server.js`: exports `class Gadget extends DurableObject`
- `client.js`: renders in the sandboxed iframe and calls the global `gadget` RPC stub

Useful optional file:

- `README.md`: architecture and programmatic usage for future agents

Blueprint metadata normally contains `title`, `description`, `author`, `created`, `version`, `lastUpdated`, and `bindings`. Imports generate a new local Blueprint ID and ownership record. The archive does not directly deploy a standalone Worker, contain live Durable Object data, or automatically update already-created Workspaces.

Cloudflare OS rejects malformed archives and caps metadata at 64 KiB and compressed content at 32 MiB.
