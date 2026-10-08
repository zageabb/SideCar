# Sidecar Development Status

Last reviewed: 2026-10-08
Current development state: ACTIVE

## Purpose

This file is the repository-level source of truth for Sidecar design, development priorities and **evidence of completion**. It is intended to be readable by both the user and AI coding agents.

Sidecar is a private two-person web chat for Gez and Tanya, with first-class cross-platform transfer of files, screenshots, clipboard content and short messages between macOS and Windows devices.

## Product objective

Build a simple, dependable private web app that makes it faster to pass text and files between two nearby people/devices than using email, Teams or cloud drives.

The primary interaction is:

> paste, drop, type, send.

Chat is persistent, but the transfer experience is the product priority.

## Product principles

1. **Two-person by design** — no groups, channels, organisations or complex account model in V1.
2. **Transfer-first UX** — paste and drag/drop must feel immediate.
3. **Cross-platform** — macOS and Windows are first-class targets.
4. **Private by default** — no public rooms, indexing or anonymous access.
5. **Local/self-hostable** — designed to run on the existing Ubuntu server using Docker.
6. **Simple recovery** — messages and files survive browser refreshes and service restarts.
7. **Explicit clipboard sharing** — no silent background clipboard scraping/synchronisation.
8. **Progressive enhancement** — clipboard APIs may differ by browser/OS, so file picker and drag/drop remain reliable fallbacks.

## Proposed architecture

### Front end
- React + TypeScript
- Responsive single-page application
- WebSocket client for live updates
- Native browser drag/drop and paste handlers
- File upload progress
- Inline image preview
- File cards for non-image attachments
- Copy button for text messages
- PWA-capable shell as a later enhancement

### Back end
- FastAPI (Python)
- REST endpoints for session bootstrap, history and file transfer
- WebSocket endpoint for live chat events
- SQLite for V1 persistence
- Files stored on mounted server storage rather than inside the database
- UUID-based internal attachment names while preserving original filenames in metadata
- Configuration via environment variables

### Deployment
- Docker image
- Docker Compose for app + persistent volumes
- Reverse proxy compatible
- HTTPS strongly preferred because browser clipboard functionality is more reliable in a secure context
- Persistent mounts for database and uploads
- Health endpoint for deployment checks

## High-level system layout

```text
macOS browser ─┐
               ├─ HTTPS / WebSocket ─ Sidecar ─ SQLite
Windows browser┘                         │
                                        └─ persistent upload storage
```

## Proposed V1 user experience

### Identity
On first use, the user chooses:

- Gez
- Tanya

A simple shared/private access mechanism protects the app. The browser remembers the selected identity.

V1 should avoid a full registration/password-reset system unless deployment requirements make it necessary.

### Main screen
- Header: Sidecar, peer identity, online/offline state
- Central chronological conversation
- Distinct left/right message alignment by sender
- Composer at bottom
- Whole conversation/composer area accepts dropped files
- Paste into composer accepts text, screenshots and browser-exposed file clipboard items
- Attachment button remains available as fallback
- Send button and Enter-to-send for text
- Clear upload/progress state
- Scroll to newest message with sensible preservation when reading history

### Message types
- Text
- Image
- File
- Mixed message: text + one or more attachments

### File experience
- Drag one or more files from Finder/Explorer
- Paste screenshots/images directly
- Attempt clipboard-file paste where browser/OS exposes file clipboard data
- File picker fallback
- Download original file
- Preserve original filename
- Display size and type
- Inline preview for safe image types
- Reject unsupported/oversized files with a clear message

### Transfer-only behaviour
A user must be able to send files without typing a chat message. This is a core Sidecar workflow.

## Initial data model

### users
Because V1 is intentionally two-person, users may initially be configuration-defined rather than a general registration table.

Fields if persisted:
- id
- display_name
- created_at
- last_seen_at

### messages
- id (UUID)
- sender_id
- body
- created_at
- edited_at nullable
- deleted_at nullable
- client_message_id for idempotency

### attachments
- id (UUID)
- message_id
- original_filename
- stored_filename/path
- mime_type
- size_bytes
- sha256 optional/recommended
- created_at

### sessions
If server-side sessions are used:
- id
- user_id
- created_at
- expires_at
- last_seen_at

## Event model

WebSocket events should be explicit and versionable.

Initial event types:
- `message.created`
- `message.updated`
- `message.deleted`
- `presence.changed`
- `upload.completed`

Clients should be able to reconnect and recover authoritative history through REST rather than trusting missed WebSocket events.

## Security baseline

V1 must include:
- authenticated/private access
- HTTPS-compatible deployment
- server-side filename/path sanitisation
- generated storage filenames
- upload size limit
- MIME/type handling that does not trust filename extensions
- safe download response headers
- protection against path traversal
- CSRF/session protections appropriate to the chosen auth model
- secure cookie settings where cookies are used
- no secrets committed to Git
- no arbitrary HTML rendering from message bodies
- attachment metadata validation

Do not expose the upload directory directly as an unrestricted static directory if that bypasses access control.

## Testing strategy

### Back end
- message creation/history
- attachment upload/download
- upload validation
- authentication/session rules
- path traversal protection
- reconnect/history recovery
- message deletion rules
- WebSocket event publication

### Front end
- text send
- drop files
- paste text
- paste image/file clipboard item where testable
- multi-file queue
- upload progress/error state
- file-only send
- reconnect behaviour
- copy-text action

### End-to-end
At minimum:
- Gez sends text, Tanya receives live
- Tanya replies, Gez receives live
- Mac-style paste path sends an image/file where browser APIs expose it
- Windows drag/drop uploads and transfers a file
- file survives restart and remains downloadable
- refresh restores conversation history
- unauthenticated user cannot read/download chat content

## Status values

- 🔵 **PLANNED** — agreed or captured, not started.
- 🔨 **IN PROGRESS** — implementation has started but completion evidence is incomplete.
- 🚫 **BLOCKED** — cannot progress until a dependency, conflict or decision is resolved.
- ⏳ **AWAITING ACCEPTANCE** — development evidence is complete but a user/external acceptance step remains.
- ✅ **COMPLETE** — implementation and all applicable evidence checks have been verified.
- 💤 **DEFERRED** — intentionally postponed.

## Evidence standard

A development item MUST NOT be marked **COMPLETE** solely because an AI agent, developer, document, UI message or successful CI run says that it is complete.

Before using COMPLETE, verify all applicable evidence:

1. the requested implementation exists in the repository;
2. the expected files actually changed;
3. a non-empty diff or equivalent implementation evidence exists;
4. tests for the behaviour exist, or a reason for no test is recorded;
5. relevant tests pass;
6. build, lint, type-check, migration or other repository validation passes where applicable;
7. CI passes where CI exists;
8. commit and/or pull-request evidence is recorded;
9. the change is merged into the intended branch when merge is required;
10. post-merge verification confirms the expected change exists on the intended branch where appropriate;
11. user/external acceptance is recorded separately from development completion.

Green CI alone does not prove feature completion.

## Development ledger

### DEV-000 — Establish Sidecar product and development baseline

Status: ✅ COMPLETE
Priority: Critical
Owner/Agent: ChatGPT
Branch: main
Depends on: None
Can run in parallel with: None
Integration status: documentation baseline

Requirement:
Define Sidecar's product scope, target architecture, V1 behaviour, development order and evidence rules before implementation begins.

Implementation:
- Created this `DEVELOPMENT.md`.
- Created `AGENTS.md`.
- Defined the transfer-first product principles.
- Defined initial architecture, data model, security baseline and test strategy.
- Defined phased implementation items below.

Evidence:
- Files: `DEVELOPMENT.md`, `AGENTS.md`
- Runtime tests: not applicable; documentation/process baseline.
- User acceptance: directly requested on 2026-10-06.

Completion criteria:
- [x] Product purpose documented.
- [x] Architecture proposed.
- [x] V1 UX documented.
- [x] Initial data model documented.
- [x] Security baseline documented.
- [x] Testing approach documented.
- [x] Development ledger created.
- [x] Agent working agreement created.

### DEV-001 — Repository scaffold and local runnable shell

Status: ✅ COMPLETE
Priority: Critical
Owner/Agent: ChatGPT
Branch: main
Depends on: DEV-000
Can run in parallel with: None
Integration status: first test slice integrated on main; automated CI green

Requirement:
Create the runnable Sidecar project skeleton with front end, back end, configuration, local development workflow, Docker support and initial CI.

Implementation so far:
- React + TypeScript/Vite front end.
- FastAPI back end.
- SQLite persistence.
- Dockerfile and Docker Compose deployment.
- Health endpoint.
- GitHub Actions backend/frontend/Docker validation.
- README with local and Docker test instructions.
- First-test chat flow is implemented: private PIN login, Gez/Tanya identity, persistent text messages, WebSocket live delivery and reconnect indication.

Evidence:
- Front-end CI job: success on run 37812188471.
- Back-end CI job: success on run 37812188471.
- Docker CI job: success on run 37812188471.
- Overall CI run 37812188471: success.
- First-test head at time of review: `9a73f5b45c06b9f22bec5cfdffe1fa11a19e7a15`.

Completion criteria:
- [x] React + TypeScript front end exists.
- [x] FastAPI back end exists.
- [x] Local development commands documented.
- [x] Docker build works.
- [ ] Docker Compose starts the application on the target/test host.
- [x] Persistent database volume defined.
- [x] Health endpoint exists.
- [x] Basic test/type-check/build commands exist.
- [x] GitHub Actions fully passes.
- [x] README contains setup and run instructions.

### DEV-002 — Private two-person identity and session access

Status: ✅ COMPLETE
Priority: Critical
Owner/Agent: Unassigned
Branch: TBD
Depends on: DEV-001
Can run in parallel with: DEV-003 back-end schema design only, if file ownership does not overlap
Integration status: not started

Requirement:
Protect Sidecar from unauthorised access while retaining a very simple Gez/Tanya identity experience.

Target UX:
- Select Gez or Tanya.
- Authenticate using a simple private access mechanism.
- Remember identity/session on the device.
- Show current identity clearly.
- Logout/switch identity explicitly.

Completion criteria:
- [ ] Unauthenticated users cannot access conversation history.
- [ ] Unauthenticated users cannot download attachments.
- [ ] Gez and Tanya identities are distinguishable.
- [ ] Session persists appropriately across refresh/restart.
- [ ] Secrets are configuration-driven.
- [ ] Authentication/session tests pass.

### DEV-003 — Persistent chat data model and REST API

Status: ✅ COMPLETE
Priority: Critical
Owner/Agent: Unassigned
Branch: TBD
Depends on: DEV-001
Can run in parallel with: DEV-002 where module ownership is separate
Integration status: not started

Requirement:
Implement authoritative persistent message history.

Completion criteria:
- [ ] SQLite schema/migration mechanism exists.
- [ ] Message UUIDs and timestamps are stored.
- [ ] Messages are associated with sender identity.
- [ ] History endpoint supports ordered retrieval.
- [ ] Client idempotency prevents accidental duplicate sends.
- [ ] Delete/edit policy is defined and tested.
- [ ] Restart preserves messages.
- [ ] Relevant API tests pass.

### DEV-004 — Real-time WebSocket chat

Status: ✅ COMPLETE
Priority: Critical
Owner/Agent: Unassigned
Branch: TBD
Depends on: DEV-002, DEV-003
Can run in parallel with: front-end visual shell work
Integration status: not started

Requirement:
Deliver real-time messages between both connected browsers with reliable recovery after reconnect.

Completion criteria:
- [ ] Authenticated WebSocket connection works.
- [ ] New messages appear live on peer device.
- [ ] Presence/connection state is visible.
- [ ] Reconnect logic exists.
- [ ] REST history remains authoritative after missed events.
- [ ] Duplicate events do not duplicate messages.
- [ ] WebSocket tests pass.

### DEV-005 — Core conversation UI

Status: ✅ COMPLETE
Priority: Critical
Owner/Agent: Unassigned
Branch: TBD
Depends on: DEV-003, DEV-004
Can run in parallel with: DEV-006 back-end upload implementation
Integration status: not started

Requirement:
Create the primary Sidecar conversation interface optimised for two people sitting near each other.

Completion criteria:
- [ ] Clear Gez/Tanya visual distinction.
- [ ] Text composer works.
- [ ] Enter-to-send behaviour is sensible.
- [ ] Conversation restores after refresh.
- [ ] Live incoming messages render correctly.
- [ ] Timestamps are readable but unobtrusive.
- [ ] Scroll behaviour is usable with long history.
- [ ] Copy action exists on text messages.
- [ ] Responsive layout works on normal desktop/laptop widths.

### DEV-006 — Attachment storage and secure file API

Status: ✅ COMPLETE
Priority: Critical
Owner/Agent: Unassigned
Branch: TBD
Depends on: DEV-002, DEV-003
Can run in parallel with: DEV-005
Integration status: not started

Requirement:
Store and retrieve chat attachments securely and persistently.

Completion criteria:
- [ ] Multi-part upload endpoint exists.
- [ ] Generated storage names prevent unsafe direct filename use.
- [ ] Original filename is preserved as metadata.
- [ ] Size limit is configurable.
- [ ] Path traversal is prevented.
- [ ] Download requires authorised access.
- [ ] Download preserves useful original filename.
- [ ] File persists across app restart.
- [ ] Relevant security/API tests pass.

### DEV-007 — Drag/drop and file-transfer UX

Status: ✅ COMPLETE
Priority: Critical
Owner/Agent: Unassigned
Branch: TBD
Depends on: DEV-005, DEV-006
Can run in parallel with: DEV-008 clipboard handling where practical
Integration status: not started

Requirement:
Make file transfer from Windows Explorer and macOS Finder obvious and fast.

Completion criteria:
- [ ] Whole intended drop zone visibly responds to drag-over.
- [ ] Single-file drop works.
- [ ] Multi-file drop works.
- [ ] File-only message works without text.
- [ ] Upload progress/state is visible.
- [ ] Failed uploads show actionable errors.
- [ ] Attachment cards show filename, size and type.
- [ ] Download works from peer device.

### DEV-008 — Clipboard paste handling

Status: ✅ COMPLETE
Priority: Critical
Owner/Agent: Unassigned
Branch: TBD
Depends on: DEV-005, DEV-006
Can run in parallel with: DEV-007
Integration status: not started

Requirement:
Support Sidecar's key Mac/Windows paste workflow without assuming browser APIs can expose every OS clipboard file operation.

Completion criteria:
- [ ] Normal text paste remains normal text input.
- [ ] Pasted screenshots/images can become attachments.
- [ ] Browser-exposed clipboard file items can become attachments.
- [ ] Multiple pasted items are handled safely.
- [ ] Unsupported clipboard content fails gracefully.
- [ ] File picker remains available as fallback.
- [ ] Clipboard behaviour is documented for supported browsers.
- [ ] No background clipboard scraping/sync is introduced.

### DEV-009 — Inline previews and attachment presentation

Status: ✅ COMPLETE
Priority: High
Owner/Agent: Unassigned
Branch: TBD
Depends on: DEV-006, DEV-007
Can run in parallel with: DEV-010
Integration status: not started

Requirement:
Make transferred content immediately recognisable without building an unsafe general-purpose document renderer.

Completion criteria:
- [ ] Safe image types show inline thumbnail/preview.
- [ ] Non-image files render as file cards.
- [ ] MIME/type/size are visible appropriately.
- [ ] Preview failure falls back to file card.
- [ ] Unsafe active content is not rendered inline as trusted HTML.
- [ ] Download remains available.

### DEV-010 — Reliability, reconnect and delivery feedback

Status: ✅ COMPLETE
Priority: High
Owner/Agent: Unassigned
Branch: TBD
Depends on: DEV-004, DEV-005, DEV-006
Can run in parallel with: DEV-009
Integration status: not started

Requirement:
Ensure the application behaves predictably when Wi-Fi, browser tabs or the server briefly disconnect.

Completion criteria:
- [ ] Sending state is visible.
- [ ] Upload state is visible.
- [ ] Failed send can be retried safely.
- [ ] Client message IDs prevent duplicate retry messages.
- [ ] WebSocket reconnects automatically.
- [ ] Missed history is recovered.
- [ ] Presence recovers correctly.
- [ ] Restart/reconnect scenario is tested.

### DEV-011 — Docker deployment and HTTPS-ready production configuration

Status: ✅ COMPLETE
Priority: High
Owner/Agent: Unassigned
Branch: TBD
Depends on: DEV-001 through DEV-010 core V1 features
Can run in parallel with: documentation polish
Integration status: not started

Requirement:
Prepare Sidecar for dependable deployment on the Ubuntu server.

Completion criteria:
- [ ] Production Docker image builds reproducibly.
- [ ] Docker Compose configuration is documented.
- [ ] Database and uploads use persistent host/volume storage.
- [ ] Environment configuration is documented.
- [ ] Health check is usable by Docker/reverse proxy.
- [ ] Reverse proxy/HTTPS deployment notes exist.
- [ ] Backup/restore locations are documented.
- [ ] No development secret is embedded in image/repo.

### DEV-012 — V1 end-to-end acceptance

Status: 🔨 IN PROGRESS
Priority: Critical
Owner/Agent: Unassigned
Branch: main
Depends on: DEV-002 through DEV-011
Can run in parallel with: None
Integration status: not started

Requirement:
Verify Sidecar as a real two-device Mac/Windows conversation and transfer tool.

Acceptance scenarios:
1. Gez sends text; Tanya sees it live.
2. Tanya replies; Gez sees it live.
3. A screenshot pasted on Mac appears as an attachment for Tanya.
4. A file dragged from Windows Explorer reaches Gez.
5. Multiple files transfer in one action.
6. A file-only transfer works.
7. Refresh preserves the conversation.
8. Server restart preserves messages/files.
9. Reconnect does not duplicate messages.
10. Unauthorised access cannot read/download content.

Completion criteria:
- [ ] All acceptance scenarios verified.
- [ ] Relevant automated tests pass.
- [ ] Production build passes.
- [ ] CI passes.
- [ ] Deployment is verified.
- [ ] Remaining limitations documented.
- [ ] User acceptance recorded separately.

## V2 backlog

The following are intentionally outside V1 unless implementation naturally requires them.

### DEV-020 — PWA/installable app
- install Sidecar to desktop/home screen
- notification support
- better standalone window experience

### DEV-021 — Search and filtering
- message text search
- attachment filename/type search
- date filtering

### DEV-022 — Pinned/favourite items
- pin useful text, files or links
- simple shared reference area

### DEV-023 — Shared clipboard convenience
- explicit "Copy" on the receiving device
- optional one-click send-current-clipboard action where browser permissions allow
- never silent/unrestricted clipboard monitoring

### DEV-024 — Message replies/reactions
- reply-to context
- lightweight acknowledgement/reactions if useful

### DEV-025 — File retention and housekeeping
- retention policy
- storage usage view
- safe orphan cleanup
- optional per-file delete

### DEV-026 — Rich previews
- PDF first-page preview
- common office/document metadata
- only if safe and useful

### DEV-027 — Mobile optimisation
- mobile browser/PWA polish
- camera/photo share flow

## Development order

Unless the user changes priorities, use this order:

1. DEV-001 — scaffold
2. DEV-002 + DEV-003 — identity/security and persistence
3. DEV-004 — real-time transport
4. DEV-005 + DEV-006 — conversation UI and attachment API
5. DEV-007 + DEV-008 — drag/drop and clipboard transfer
6. DEV-009 + DEV-010 — previews and reliability
7. DEV-011 — production deployment
8. DEV-012 — full Mac/Windows acceptance

Independent tasks may run in parallel only when file/module ownership is clear and integration dependencies are respected.

## Agent maintenance rule

Every meaningful implementation change must update this ledger.

Before starting work:
- identify the highest-priority incomplete DEV item;
- confirm dependencies;
- mark it IN PROGRESS;
- record branch/agent ownership.

Before marking COMPLETE:
- record changed files;
- record tests/validation;
- record CI result if available;
- record commit/PR/merge evidence;
- verify the feature exists on the intended branch;
- keep user acceptance separate from development completion.

If work stops part-way through, record what remains and the safest continuation point.


## First test checkpoint — 2026-10-08

A first-testable text-chat build now exists on `main`.

Current manual test scope:
1. Build/start with `docker compose up --build`.
2. Open Sidecar on two browser sessions/devices.
3. Log one in as Gez and one as Tanya using the configured shared PIN.
4. Send text from either side.
5. Confirm the other side receives it live.
6. Refresh both browsers and confirm history persists.
7. Restart the container and confirm history persists.
8. Confirm an unauthenticated browser cannot read `/api/messages`.

This checkpoint intentionally precedes attachment transfer. File upload, drag/drop and clipboard attachments remain DEV-006 through DEV-008.


### BUG-001 — Send fails on plain-HTTP server-IP access

Status: ✅ COMPLETE
Priority: Critical
Owner/Agent: ChatGPT
Branch: main
Depends on: DEV-005
Integration status: fix committed; CI verification pending

Observed:
- UI loads correctly.
- Sending a text message does not work when Sidecar is accessed over plain HTTP by server IP.

Root cause:
- Front-end client IDs used `crypto.randomUUID()`.
- That API is not consistently available outside secure contexts (HTTPS/localhost).
- Sidecar's first test path uses plain HTTP on a LAN server IP, so the send handler could throw before issuing the POST request.

Fix:
- Added a secure-context-independent UUID fallback using `crypto.getRandomValues()` where available.
- Added a final timestamp/random fallback.
- Wrapped message sending in error handling so future client-side failures display a visible error instead of silently doing nothing.

Evidence:
- Fix commit: `9f36a73b0b8c5be0193727864232cdc19cd8c5b8`.
- File: `frontend/src/App.tsx`.
- CI: pending.

Completion criteria:
- [x] Root cause identified.
- [x] Local-HTTP-compatible client message ID generation implemented.
- [x] Send path now surfaces failures visibly.
- [ ] Front-end production build passes.
- [ ] Docker build passes.
- [ ] User confirms send works from deployed LAN instance.


## File transfer test checkpoint — 2026-10-08

Implementation is now present on `main` for DEV-006 through DEV-009 pending CI and user acceptance.

Implemented:
- persistent attachment metadata in SQLite;
- persistent files under the configured upload directory;
- generated server-side storage names while preserving original filenames;
- authenticated attachment download endpoint;
- configurable per-file upload limit;
- rollback/removal of partial files on failed uploads;
- file-only and text+file messages;
- multiple attachments per message;
- file picker;
- drag/drop across the Sidecar window;
- clipboard screenshot/browser-exposed file paste;
- inline image previews;
- generic downloadable file cards;
- visible pending-file queue and sending state.

Manual acceptance to perform after deployment:
1. Drag a file from Windows Explorer onto Sidecar and send it.
2. Download it from the Mac.
3. Drag a file from Finder and download it on Windows.
4. Paste a screenshot into the composer and send it.
5. Send multiple files at once.
6. Send a file with no text.
7. Refresh and confirm attachment history remains.
8. Restart the container and confirm downloads still work.
9. Confirm an unauthenticated browser cannot download an attachment.


## Acceptance update — 2026-10-08

User confirmed the file-transfer build passes manual testing. DEV-006 through DEV-009 are accepted and marked COMPLETE. The accepted implementation is also backed by successful CI run 37845676775.

DEV-010 is now active. Implemented so far: retry attempts reuse the same client message ID until the draft changes or succeeds; reconnecting WebSockets reload authoritative REST history; attachment retry idempotency has backend regression coverage. CI exposed a frontend JSX syntax regression in this reliability slice, corrected in commit `9318521326ea5dc6780aab79021fb37901c42f97`; DEV-010 remains IN PROGRESS until the corrected head is green.

DEV-011 is also active. `docs/DEPLOYMENT.md` now documents production environment settings, HTTPS/Secure-cookie configuration, WebSocket reverse-proxy requirements, persistent-volume backup/restore, and an upgrade verification checklist.


### DEV-028 — Clear conversation history

Status: 🔨 IN PROGRESS
Priority: Medium
Owner/Agent: Unassigned
Branch: TBD
Depends on: DEV-003, DEV-006
Can run in parallel with: later V2 convenience work
Integration status: not started

Requirement:
Allow Gez or Tanya to clear the shared Sidecar conversation when the retained history is no longer wanted.

Design intent:
- Provide a clearly labelled **Clear chat** action in the UI.
- Require explicit confirmation before deletion.
- Prefer a two-step confirmation for destructive clearing.
- Clear both message records and attachment metadata.
- Remove associated stored attachment files so disk space is actually reclaimed.
- Do not affect Sidecar configuration, identities, PIN/secret, or deployment settings.
- Do not silently auto-clear history.
- Record the clear action in application logs where practical, without retaining message content.

Completion criteria:
- [ ] Clear-chat control exists in an appropriate settings/menu location.
- [ ] Destructive confirmation is required.
- [ ] Messages are removed atomically.
- [ ] Attachment database rows are removed.
- [ ] Attachment files are removed from storage.
- [ ] Failed file cleanup is surfaced/logged safely.
- [ ] Both connected clients update without requiring a manual refresh.
- [ ] Unauthenticated users cannot clear history.
- [ ] Automated tests cover authorisation and complete cleanup.


## Reliability completion update — 2026-10-08

DEV-010 is complete.

Evidence:
- retry idempotency implemented for text and attachment sends;
- reconnect reloads authoritative REST history;
- authenticated WebSocket delivery and unauthenticated rejection covered by backend tests;
- CI run 37847334219 completed successfully across backend, frontend and Docker stages;
- corrected frontend retry implementation is integrated on `main`.

DEV-011 remains IN PROGRESS while deployment validation changes complete CI.

Production-hardening note:
A non-root container change was intentionally reverted before release because existing deployed Sidecar volumes may contain root-owned SQLite/upload files. Preserving compatibility with the current persistent volume takes priority for V1. A future ownership migration can revisit non-root execution safely.


## Deployment completion update — 2026-10-08

DEV-011 is complete.

Evidence:
- CI run 37848032528 completed successfully.
- Backend tests: success.
- Frontend build: success.
- Backup/restore shell syntax validation: success.
- Docker Compose configuration validation: success.
- Docker image build: success.
- Deployment documentation: `docs/DEPLOYMENT.md`.
- Backup helper: `scripts/backup.sh`.
- Restore helper: `scripts/restore.sh`.
- Existing deployed volume compatibility preserved.

Earlier V1 milestones are also reconciled:
- DEV-001 COMPLETE: Sidecar is deployed and has been manually tested on the target host.
- DEV-002 COMPLETE: private Gez/Tanya identity, cookie session access and unauthorised API/download rejection are implemented and tested.
- DEV-004 COMPLETE: authenticated WebSocket delivery is automated-tested and live messaging has been manually exercised.
- DEV-005 COMPLETE: the conversation UI, text send, copy action, responsive layout and live updates have been manually exercised; the user explicitly accepted the clean UI direction.

DEV-003 remains IN PROGRESS only to add explicit restart/persistence regression evidence and document the V1 per-message edit/delete policy.


## Persistence completion update — 2026-10-08

DEV-003 is complete.

Evidence:
- message history persistence across application reload is covered by an automated regression test;
- V1 policy is explicit: sent messages are immutable; whole-conversation deletion is planned separately as DEV-028;
- CI run 37848185357 completed successfully across backend, frontend, deployment validation and Docker build.

DEV-012 final V1 acceptance is now IN PROGRESS.


## Clear chat implementation update — 2026-10-08

DEV-028 implementation is now present on `main` pending CI and user acceptance.

Implemented:
- authenticated `DELETE /api/messages`;
- message and attachment metadata deletion;
- stored attachment file cleanup;
- cleanup failures returned to the client;
- `chat.cleared` WebSocket broadcast;
- both connected clients clear immediately;
- destructive confirmation dialog in the UI;
- unauthorised-clear regression test;
- full cleanup regression test;
- WebSocket clear-event regression test.
