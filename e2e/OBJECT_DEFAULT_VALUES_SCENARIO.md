# Object Default Values Acceptance Scenario

## Contract

- `OBJECT.default_value` is either `null` or one positive active Entry ID.
- `ARRAY_OBJECT.default_value` is either `null` or an ordered list of unique positive active Entry IDs.
- Every default Entry must belong to one of the attribute's referred Entities.
- An explicit Entry value, including `null` or `[]`, suppresses the schema default.
- Changing a schema default affects only Entries created afterward.

## Automated browser path

1. Open the Server Entity editor.
2. Confirm that `primary_switch` restores `switch-core-01` as its OBJECT default.
3. Confirm that `backup_switches` restores `switch-backup-01`, then `switch-core-01`, as its ARRAY_OBJECT default.
4. Open the new Entry page and confirm the same prefilled controls.
5. Create an Entry without changing either control.
6. Confirm that Entry detail renders the single reference and both ordered array references as links.
7. Run the browser quality checks for console errors, failed requests, accessibility, overflow, and off-screen controls.

The mock-browser implementation is in `e2e/pagoda-smoke.spec.ts`. It writes screenshots and a Markdown report under `e2e/test-results/report/`.

## Live ad hoc path

1. Create a referred Entity and three active Entries named `default-a`, `default-b`, and `default-c`.
2. Create or edit a consumer Entity with:
   - OBJECT default: `default-b`
   - ARRAY_OBJECT default: `default-c`, `default-a`
3. Reload the Entity editor and verify both defaults by display name.
4. Create `consumer-one` without touching the reference controls and verify its detail page contains `default-b`, `default-c`, and `default-a` in that order.
5. Change the defaults to `default-a` and `default-b`, then create `consumer-two`.
6. Verify `consumer-one` is unchanged and `consumer-two` uses the new defaults.
7. Create `consumer-three`, explicitly clear OBJECT and ARRAY_OBJECT, save, and verify neither reference was applied.
8. Attempt each invalid schema update and expect HTTP 400 with no schema mutation:
   - an Entry from an unreferred Entity;
   - an inactive or missing Entry;
   - a string, boolean, or object instead of an integer ID;
   - duplicate ARRAY_OBJECT IDs;
   - removing a referred Entity while its Entry remains a default.

## Release evidence

- Focused backend tests cover storage shape, referral integrity, create/retrieve round trips, Entry materialization, ordering, and Trigger input.
- Frontend tests cover single/multiple selection, ID submission, ID-to-label restoration, and new-Entry prefilling.
- The production frontend build must pass against a client generated from the current OpenAPI schema.
- Browser acceptance must produce both configuration and persisted-Entry screenshots.
