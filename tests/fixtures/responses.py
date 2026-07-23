"""Fabricated API responses used across contract tests.

Nothing here is real. "Fixture Brain" does not exist. IDs are zero-padded
placeholders. This matches WORKING_ARCHITECTURE.md's product-boundary rule:
"use obviously fabricated data in tests and examples."
"""

APP_STATE_RUNNING = {
    "brain": {"id": "11111111-1111-1111-1111-111111111111", "name": "Fixture Brain"},
}

APP_STATE_NO_BRAIN_OPEN = {"brain": None}

BRAINS_LIST = {
    "brains": [
        {"id": "11111111-1111-1111-1111-111111111111", "name": "Fixture Brain"},
        {"id": "22222222-2222-2222-2222-222222222222", "name": "Second Fixture Brain"},
    ]
}

THOUGHT = {
    "id": "33333333-3333-3333-3333-333333333333",
    "name": "Sample Thought",
    "label": "fixture",
}

ATTACHMENTS_BY_LOCATION_FOUND = {
    "attachments": [
        {
            "id": "44444444-4444-4444-4444-444444444444",
            "thoughtId": "33333333-3333-3333-3333-333333333333",
            "location": "https://example.invalid/fixture-page",
        }
    ]
}

ATTACHMENTS_BY_LOCATION_EMPTY = {"attachments": []}

# Shapes below are fabricated but structurally match what was directly
# observed against a running local API instance on 2026-07-23 (see
# docs/decisions/0002-live-verified-read-capabilities.md). Field names are
# real; values are not.

SEARCH_RESULTS = [
    {
        "sourceThought": {
            "id": "55555555-5555-5555-5555-555555555555",
            "brainId": "11111111-1111-1111-1111-111111111111",
            "name": "Fixture Match",
            "cleanedUpName": "Fixture Match",
            "kind": 1,
            "label": None,
        },
        "sourceLink": None,
        "searchResultType": 1,
        "isFromOtherBrain": False,
        "name": "Fixture Match",
        "attachmentId": "00000000-0000-0000-0000-000000000000",
        "brainName": None,
        "brainId": "00000000-0000-0000-0000-000000000000",
    }
]

SEARCH_RESULTS_EMPTY: list = []

THOUGHT_GRAPH = {
    "activeThought": {
        "id": "33333333-3333-3333-3333-333333333333",
        "brainId": "11111111-1111-1111-1111-111111111111",
        "name": "Sample Thought",
        "cleanedUpName": "Sample Thought",
        "kind": 1,
        "label": None,
    },
    "parents": [
        {
            "id": "66666666-6666-6666-6666-666666666666",
            "brainId": "11111111-1111-1111-1111-111111111111",
            "name": "Fixture Parent",
            "cleanedUpName": "Fixture Parent",
            "kind": 1,
            "label": None,
        }
    ],
    "children": [],
    "jumps": [],
    "siblings": None,
    "tags": [],
    "type": None,
    "links": [
        {
            "id": "77777777-7777-7777-7777-777777777777",
            "brainId": "11111111-1111-1111-1111-111111111111",
            "name": None,
            "thoughtIdA": "66666666-6666-6666-6666-666666666666",
            "thoughtIdB": "33333333-3333-3333-3333-333333333333",
            "relation": 1,
            "direction": -1,
            "meaning": 1,
        }
    ],
    "attachments": [],
}

NOTE_EMPTY = {
    "brainId": "11111111-1111-1111-1111-111111111111",
    "sourceId": "33333333-3333-3333-3333-333333333333",
    "sourceType": 2,
    "modificationDateTime": "0001-01-01T00:00:00",
    "markdown": "",
    "html": None,
    "text": None,
}

NOTE_WITH_CONTENT = {
    **NOTE_EMPTY,
    "markdown": "# Fixture note\n\nSome fabricated content.",
}

MODIFICATIONS = [
    {
        "sourceId": "33333333-3333-3333-3333-333333333333",
        "sourceType": 2,
        "extraAId": "00000000-0000-0000-0000-000000000000",
        "extraAType": -1,
        "extraBId": "00000000-0000-0000-0000-000000000000",
        "extraBType": -1,
        "modType": 301,
        "oldValue": None,
        "newValue": None,
        "userId": "88888888-8888-8888-8888-888888888888",
        "brainId": "11111111-1111-1111-1111-111111111111",
        "creationDateTime": "2026-07-23T00:00:00",
        "modificationDateTime": "2026-07-23T00:00:00",
        "syncUpdateDateTime": None,
    }
]

MODIFICATIONS_EMPTY: list = []

ATTACH_URL_RESULT = {"id": "99999999-9999-9999-9999-999999999999"}

CREATE_THOUGHT_RESULT = {"id": "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"}
