---
name: cloudflare-os-build-gadget
description: Build, package, validate, upload, and share Cloudflare OS Gadgets as .gadget Blueprint archives. Use when asked to create a Cloudflare OS app, generate server.js/client.js Gadget code, persist app state with Durable Objects, convert an externally authored app into a .gadget file, test a Gadget in Cloudflare OS, or prepare a reusable Gadget Blueprint for a team.
---

# Build Cloudflare OS Gadgets

Create a working Gadget and finish with both editable source files and a validated `.gadget` Blueprint.

## Workflow

1. Confirm the app's users, core job, stored data, and external connections. Make reasonable assumptions for a small demonstration.
2. Create a source directory containing `server.js`, `client.js`, and optionally `README.md`.
3. Implement `export class Gadget extends DurableObject` in `server.js`. Store durable state with `this.ctx.storage`; expose narrow RPC methods to `client.js`.
4. Build the interface in `client.js` using the global `gadget` RPC stub. Do not embed API keys, OAuth tokens, or privileged credentials in client code.
5. Read [references/gadget-format.md](references/gadget-format.md) before packaging or debugging an archive.
6. Package with `scripts/package-gadget.mjs`. Run it from a package that can resolve `yjs`; in the Cloudflare OS repository use:

   ```bash
   pnpm --filter @gadgets/workshop-backend exec node \
     /absolute/path/to/scripts/package-gadget.mjs \
     --source /absolute/path/to/source \
     --output /absolute/path/to/app.gadget \
     --title "App title" \
     --description "What the app does" \
     --author "Author name"
   ```

7. Upload the archive from **Blueprints → Upload .gadget**, open its landing page, and select **Create Gadget**.
8. Test the primary interaction, an invalid/empty state, and persistence after a full reload. Check browser console and Worker logs for errors.
9. Return the `.gadget` path, source path, created Workspace URL, test evidence, and any required bindings.

## Architecture Rules

- Treat `.gadget` as a Blueprint archive, not a ZIP file or direct deployment bundle.
- Keep authoritative data and validation in `server.js`; treat `client.js` as untrusted UI.
- Serialize overlapping mutations when an operation reads and then writes shared state.
- Return plain serializable objects across Gadget RPC.
- Require Gatekeepers for external systems. Never place provider credentials in a Blueprint.
- Prefer no external bindings for demonstrations so another user can instantiate immediately.
- Keep controls keyboard accessible and provide visible loading, empty, success, and error states.
- Do not claim production deployment when only `localhost` was tested. A Blueprint uploaded to a deployed Cloudflare OS runs on that deployment's Workers and Durable Objects.

## Validation Checklist

- Archive has `server.js` and `client.js`.
- `server.js` exports `Gadget` and imports `DurableObject` from `cloudflare:workers`.
- Archive metadata describes required bindings accurately.
- Upload succeeds and Blueprint metadata renders correctly.
- **Create Gadget** opens the app without runtime errors.
- At least one mutation survives a full page reload.
- No secret appears in source, logs, archive metadata, or screenshots.

## Sharing

Share the `.gadget` file for one-click import. Share this Skill folder when teammates also need to author or update Gadgets. Existing Workspace instances do not automatically update when the Blueprint changes; publish a new Blueprint version and deliberately recreate or migrate instances.
