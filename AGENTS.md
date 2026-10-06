# AGENTS.md

## Project

Repository: `zageabb/sidecar`

Sidecar is a private two-person web chat and cross-platform transfer tool for Gez and Tanya. Its primary job is to move text, screenshots and files quickly between macOS and Windows while preserving a simple persistent conversation.

This file is the persistent working agreement for ChatGPT, Codex, Olladex and other coding agents operating on this repository.

## Start here

Before changing code:

1. Read this file.
2. Read `DEVELOPMENT.md`.
3. Read `README.md` and relevant docs when they exist.
4. Inspect the current repository implementation before proposing replacement architecture.
5. Identify the current DEV item, its dependencies, branch ownership and integration state.
6. Continue the highest-priority incomplete DEV item unless the user explicitly asks for something else.
7. Update `DEVELOPMENT.md` before beginning a new development item and again after implementation/validation.

Repository state is authoritative. Do not rely on chat history when code, Git, tests, CI or `DEVELOPMENT.md` provide a more current answer.

## Product intent

Protect the core Sidecar experience:

> paste, drop, type, send.

The app is deliberately smaller than Teams, Slack, Discord or WhatsApp.

Do not introduce unnecessary enterprise collaboration concepts such as:
- workspaces;
- channels;
- organisations;
- roles/permissions matrices;
- public rooms;
- complex contact lists;
- generic multi-user registration;

unless the user explicitly changes the product scope.

The two-person Gez/Tanya workflow is a feature, not a temporary limitation.

## Development rules

- Preserve the transfer-first UX.
- Prefer the smallest coherent implementation that satisfies the active DEV item.
- Extend working modules rather than rewriting them without need.
- Keep UI, transport, persistence, file storage and authentication concerns separated.
- Keep modules focused and testable.
- Maintain backwards compatibility with stored messages/files where practical.
- Do not hard-code passwords, tokens, server addresses, ports or environment-specific paths when configuration can be used.
- Never commit production secrets.
- Clearly mark scaffolds, placeholders and unfinished features.
- Keep `README.md`, configuration docs and `DEVELOPMENT.md` accurate.
- Record unrelated ideas as future DEV items instead of silently expanding scope.
- Do not add a dependency merely because it is fashionable; justify dependencies by product need.

## Sidecar-specific UX rules

### Chat
- Conversation history must remain understandable after refresh/reconnect.
- Gez and Tanya must be visually distinguishable.
- A text-only message must be fast to send.
- A file-only message must be valid.
- Text plus attachments should be supported once the attachment flow exists.
- Avoid modal-heavy flows for ordinary sending.

### Drag/drop
- Drag/drop is a first-class input method.
- The drop target should be generous and visually obvious while dragging.
- Multi-file transfer should be supported.
- Dropping a file must not accidentally navigate the browser away from Sidecar.

### Clipboard
- Normal text paste must continue to behave like normal paste.
- Pasted screenshots/images should be attachable.
- Use browser-exposed clipboard file items when available.
- Do not promise Finder/Explorer clipboard-file support where the browser/OS does not expose it.
- Always retain drag/drop and file-picker fallbacks.
- Do not implement silent/background clipboard monitoring.
- Clipboard access should be explicit and user-driven.

### Copying
- Received text should have an explicit copy action.
- Do not attempt unrestricted remote clipboard injection.

## Architecture guidance

The planned baseline is:
- React + TypeScript front end;
- FastAPI back end;
- REST for history/uploads/bootstrap;
- WebSocket for real-time events;
- SQLite for V1 data;
- filesystem/volume storage for attachments;
- Docker deployment.

This is a preferred baseline, not permission to ignore repository evidence. If implementation has already established a different working architecture, preserve it unless there is a concrete reason to change it.

## Data integrity rules

- Use stable IDs, preferably UUIDs, for messages and attachments.
- Store original filenames only as metadata; do not trust them as storage paths.
- Generated server-side names/paths should be collision-safe.
- Message history must be authoritative on the server.
- WebSocket events are notifications, not the sole source of truth.
- Reconnecting clients must be able to recover state from persisted history.
- Use client-generated idempotency IDs or equivalent to prevent duplicate messages during retries.
- Store timestamps consistently, preferably UTC internally, and format for display at the client.

## File security rules

Treat all uploads as untrusted.

- Prevent path traversal.
- Do not construct paths directly from the submitted filename.
- Enforce configurable size limits.
- Validate metadata server-side.
- Do not trust file extension alone as MIME truth.
- Avoid rendering arbitrary uploaded HTML/SVG/active content as trusted inline content.
- Use safe download headers.
- Keep attachment downloads behind Sidecar access control.
- Do not expose a persistent upload directory publicly if doing so bypasses auth.
- Never execute uploaded content.
- Consider hashes where useful for integrity/debugging.

## Authentication/security rules

Sidecar is private even though it has only two intended users.

- Unauthenticated clients must not read conversation history.
- Unauthenticated clients must not download attachments.
- Auth must apply to WebSocket connections as well as REST requests.
- Use secure cookie/session settings when cookie sessions are chosen.
- Avoid secrets in source code.
- Keep HTTPS deployment compatible.
- Do not weaken auth merely to make local development easier; use development configuration instead.
- Avoid rendering unsanitised user-controlled HTML.

## Testing and quality

For meaningful code changes:

- add/update tests for material behaviour;
- run relevant unit/integration tests;
- run front-end build/type-check/lint where configured;
- run back-end test/lint/type-check where configured;
- test failure/retry paths, not only the happy path;
- test restart/reconnect behaviour for persistence and WebSocket work;
- test unauthorised access for auth/file features;
- verify drag/drop does not trigger browser navigation;
- verify file-only transfer works;
- record validation evidence in `DEVELOPMENT.md`.

Do not claim completion if only a scaffold exists.

## Cross-platform validation

Sidecar specifically exists to bridge macOS and Windows.

Where behaviour is OS/browser-sensitive, document the tested combination.

Important flows include:
- macOS: text paste, screenshot/image paste, Finder drag/drop, browser-exposed clipboard file paste where available;
- Windows: text paste, screenshot paste, Explorer drag/drop, browser-exposed clipboard file paste where available;
- download/open behaviour on both platforms.

Do not invent browser support. If an API is not reliably exposed, keep a fallback and document the limitation.

## Git workflow

- Default branch is normally `main`; verify before acting.
- Do not force-push the default branch.
- Do not rewrite published history unless explicitly requested.
- Keep commits focused and clearly named.
- Do not push code known to fail relevant validation unless the user explicitly requests a WIP commit.
- For parallel work, use separate branches/worktrees where practical.
- Record active branch/agent ownership in `DEVELOPMENT.md`.
- Verify integration on the intended target branch after merge.

## Parallel development

Before starting parallel work:

1. split only genuinely independent DEV items;
2. record Owner/Agent, Branch, Depends on, Can run in parallel with and Integration status;
3. avoid concurrent edits to the same files/modules where possible;
4. do not misrepresent sequential dependencies as parallel work;
5. validate each child task independently;
6. identify who owns integration;
7. verify the integrated result.

For Sidecar, likely safe parallel boundaries include:
- UI shell vs back-end storage/auth;
- attachment API vs conversation visual styling;
- preview presentation vs reconnect hardening;

but only after shared contracts are stable.

## Reuse before duplication

Before implementing generic infrastructure, inspect the user's existing repositories for proven patterns where this is efficient and legally/technically appropriate.

Potential reuse areas:
- Docker/reverse-proxy configuration;
- FastAPI application structure;
- WebSocket patterns;
- SQLite migration/testing patterns;
- GitHub Actions;
- common front-end layout components.

Do not copy large unrelated architectures into Sidecar. The app should remain intentionally small.

## Deployment

Sidecar is expected to be self-hostable on the Ubuntu server.

- Inspect actual deployment files before changing deployment.
- Preserve defined ports/volumes/environment variables once established unless change is required.
- Keep database and upload storage persistent.
- Document backup/restore locations.
- Provide a health endpoint.
- Keep reverse-proxy/HTTPS compatibility.
- Do not bake production credentials or local IP assumptions into the image.
- Keep local development possible without requiring the production server.

## Agent behaviour

Continue autonomously until one of these happens:

1. the current objective is complete and verified;
2. a genuinely ambiguous product decision is required;
3. progress is blocked by something outside the repository;
4. continuing would risk destructive changes.

Do not stop merely because one implementation step has completed.

Also:
- use repository evidence as the source of truth;
- prefer implementation over speculative redesign;
- investigate root cause rather than stacking repeated patches;
- do not invent files, CI results, commits, test outcomes or runtime behaviour;
- preserve enough state/documentation for another agent to resume safely;
- if two attempted fixes fail for the same issue, perform root-cause analysis before another patch.

## Development completion evidence

For every meaningful feature, bug fix or development idea:

- create/update the relevant `DEVELOPMENT.md` entry;
- keep PLANNED / IN PROGRESS / BLOCKED / AWAITING ACCEPTANCE / COMPLETE / DEFERRED truthful;
- record owner, branch, dependencies and integration status;
- record implementation files;
- record tests and validation;
- record CI evidence where applicable;
- record commit/PR/merge evidence where applicable;
- keep user acceptance separate from engineering completion.

Never mark a coding item COMPLETE merely because an agent says it is complete.

Before marking COMPLETE, verify all applicable evidence:
- requested behaviour exists;
- expected files changed;
- meaningful diff exists;
- relevant tests exist or a no-test reason is recorded;
- tests pass;
- build/lint/type-check pass where applicable;
- CI passes where available;
- branch/commit evidence is correct;
- merge/integration is correct;
- post-merge verification is complete where applicable;
- acceptance criteria have been checked.

An empty result, no write/edit operation, unchanged branch HEAD, empty diff, missing requested validation or budget exhaustion before criteria are satisfied means the task is not complete.

Green CI alone does not prove feature completion.

## Recovery and interrupted work

If work is interrupted or blocked, update `DEVELOPMENT.md` with:
- what was completed;
- what remains;
- the blocker;
- validation already performed;
- the safest continuation point;
- the next recommended action.

When documentation conflicts with code, tests, Git history or CI, repository evidence wins and documentation must be reconciled.
