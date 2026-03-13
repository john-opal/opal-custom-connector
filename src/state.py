"""
In-memory state for the single-group connector.

In a real connector this would be backed by a database or external API.

Users are keyed by their remote ID (the ID your system assigns).
The single group "app-access" controls who has access to the app.
"""

# Users are empty — Opal will provision them via POST /users when access is approved
users: dict = {}

# The single group for this app
groups: dict = {
    "app-access": {
        "name": "App Access",
        "description": "Members of this group have access to the app.",
        "users": [],
    }
}
