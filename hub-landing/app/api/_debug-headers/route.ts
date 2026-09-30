// Decommissioned / never actually routable: Next.js treats any `_`-prefixed folder under `app/`
// as private (opted out of routing) — this was a naming mistake made while adding a one-time
// diagnostic route (see app/api/debugheaders/route.ts's own comment for what it was for and
// what it found). Left as an inert, empty module rather than deleted, since this environment has
// no git history to fall back on for this app.
export {};
