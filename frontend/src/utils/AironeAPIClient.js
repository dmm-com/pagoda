import {getCsrfToken} from "./DjangoUtils";

export function getEntities(entityId) {
    return fetch('/entity/api/v1/get_entities');
}

export function getEntries(entityId) {
    return fetch(`/entry/api/v1/get_entries/${entityId}`);
}

// NOTE it calls non-API endpoint
// FIXME implement internal API then call it
export function deleteEntry(entryId) {
    return fetch(
        `/entry/do_delete/${entryId}/`,
        {
            method: 'POST',
            headers: {
                'X-CSRFToken': getCsrfToken(),
            },
            body: JSON.stringify({}),
        }
    );
}