import {getCsrfToken} from "./DjangoUtils";

export function getEntities(entityId) {
    return fetch('/entity/api/v1/get_entities');
}

export function getEntries(entityId) {
    return fetch(`/entry/api/v1/get_entries/${entityId}`);
}

export function getAdvancedSearchResults(entityIds, attributeIds, isAllEntities, hasReferral) {
    let params = new URLSearchParams();
    entityIds.forEach(id => params.append('entity', id));
    attributeIds.forEach(id => params.append('attr', id));
    params.append('is_all_entities', isAllEntities);
    params.append('has_referral', hasReferral);

    let url = new URL('/dashboard/advanced_search');
    url.searchParams = params;

    return fetch(url.toString());
}

// NOTE it calls non-API endpoint
// FIXME implement internal API then call it
export function createEntity(name, note, attrs) {
    return fetch(
        `/entity/do_create`,
        {
            method: 'POST',
            headers: {
                'X-CSRFToken': getCsrfToken(),
            },
            body: JSON.stringify({
                name: name,
                note: note,
                is_toplevel: false,
                attrs: attrs,
            }),
        }
    );
}

// NOTE it calls non-API endpoint
// FIXME implement internal API then call it
export function deleteEntity(entityId) {
    return fetch(
        `/entity/do_delete/${entityId}`,
        {
            method: 'POST',
            headers: {
                'X-CSRFToken': getCsrfToken(),
            },
            body: JSON.stringify({}),
        }
    );
}

// NOTE it calls non-API endpoint
// FIXME implement internal API then call it
export function createEntry(entityId, name, attrs) {
    return fetch(
        `/entry/do_create/${entityId}/`,
        {
            method: 'POST',
            headers: {
                'X-CSRFToken': getCsrfToken(),
            },
            body: JSON.stringify({
                entry_name: name,
                attrs: attrs,
            }),
        }
    );
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

export function getUsers() {
    return new Promise((resolve, _) => {
        resolve([
            {
                id: 1,
                name: 'test',
                email: 'test@example.com',
                created_at: '',
            },
        ]);
    })
}

export function getGroups() {
    return new Promise((resolve, _) => {
        resolve([
            {
                id: 1,
                name: 'test',
                members: [
                    {
                        name: 'user1',
                    },
                    {
                        name: 'user2',
                    },
                ],
            },
        ]);
    })
}

export function getJobs() {
    return new Promise((resolve, _) => {
        resolve([
            {
                id: 1,
                entry: 'entry1',
                operation: '作成',
                status: '完了',
                duration: '1s',
                created_at: '1st Jan 0:00pm',
                note: '',
            },
        ]);
    })
}

