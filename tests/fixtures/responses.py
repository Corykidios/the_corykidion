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
