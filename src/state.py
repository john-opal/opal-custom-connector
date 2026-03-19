"""
In-memory state for the single-group connector.

In a real connector this would be backed by a database or external API.

Users are keyed by their remote ID (the ID your system assigns).
The single group "app-access" controls who has access to the app.
"""

# Users are empty — Opal will provision them via POST /users when access is approved
users: dict = {
    "54577197-387b-49e7-a203-2b0237c1ae7e": {
        "id": "54577197-387b-49e7-a203-2b0237c1ae7e",
        "email": "john@opal.dev",
    }
}

# The single group for this app
groups: dict = {
    "app-access": {
        "name": "App Access",
        "description": "Members of this group have access to the app.",
        "users": [],
    }
}
