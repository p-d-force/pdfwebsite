# Admin Security Roadmap

This document describes the security path from the current local admin platform to a safer hosted admin application.

## Current State

- local admin server on `127.0.0.1:8765`
- no hosted login yet
- JSON-based writes for local workflows

## Goal State

- password-protected hosted admin
- secure session login
- role-based access
- audit trail on every meaningful change
- public site separated from internal admin data

## Recommended Security Features

### Phase 1

- password-hashed admin user records
- secure login form
- server-side session validation
- CSRF protection
- audit logging

### Phase 2

- roles: owner, reviewer, contributor, read-only
- route-level authorization
- action-level permissions for publish/redaction/delete-sensitive operations

### Phase 3

- optional IP restrictions
- login throttling
- session invalidation controls
- stronger secret isolation and environment handling

## Minimum Hosted Rules

- no raw credentials in repo or public files
- no admin APIs callable without auth
- no internal ingest JSON directly readable from public routes
- no public publish path without explicit review and audit log

## Authentication Recommendation for Current Hosting

Use PHP-native password hashing and secure session handling first.

- `password_hash()`
- `password_verify()`
- `session_regenerate_id()` after login
- secure session cookies

Avoid rolling custom crypto or token logic beyond what is necessary for the first secure phase.
