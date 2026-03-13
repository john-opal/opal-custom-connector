"""
In-memory state for the single-group connector.

In a real connector this would be backed by a database or external API.

Users are keyed by their remote ID (the ID your system assigns).
The single group "app-access" controls who has access to the app.
"""

# Users known to this connector: remote_id -> {email}
users: dict = {
    "user-1": {"email": "alice@example.com"},
    "user-2": {"email": "bob@example.com"},
}

# The single group for this app
groups: dict = {
    "app-access": {
        "name": "App Access",
        "description": "Members of this group have access to the app.",
        "users": ["user-1"],  # alice starts with access
    }
}
