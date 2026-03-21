"""
Single-group custom connector for Opal.

This connector exposes one group ("App Access") that controls who has
access to the app. Opal will:
  1. Call POST /users to create (provision) a user into the app when
     access is first approved.
  2. Call POST /groups/{id}/users to add the user to the group.
  3. Call DELETE /groups/{id}/users/{uid} to remove from the group
     when access is revoked.
  4. Call DELETE /users/{uid} to deprovision the user from the app
     when they are fully removed.
"""

from dotenv import load_dotenv
load_dotenv()

from fastapi import Depends, FastAPI, Request
from fastapi.responses import JSONResponse

from security import get_signature_headers
from exceptions import ErrorException
import state

app = FastAPI(
    title="Single-Group Custom Connector",
    version="1.0",
    dependencies=[Depends(get_signature_headers)],
)


@app.exception_handler(ErrorException)
async def error_exception_handler(request: Request, exc: ErrorException):
    return JSONResponse(
        status_code=exc.code,
        content={"code": exc.code, "message": exc.message},
    )


# ---------------------------------------------------------------------------
# Status
# ---------------------------------------------------------------------------

@app.get("/status")
async def get_status(app_id: str):
    if not app_id:
        raise ErrorException(code=400, message="app_id is required")
    return {}


# ---------------------------------------------------------------------------
# Users
# ---------------------------------------------------------------------------

@app.get("/users")
async def get_users(app_id: str, cursor: str = None):
    return {
        "users": [
            {"id": uid, "email": u["email"]}
            for uid, u in state.users.items()
        ]
    }


@app.post("/users")
async def create_user(body: dict):
    """
    Called by Opal to provision a user into the app for the first time.
    Opal sends the user's Opal UUID as `user_id` and their profile in
    `attributes`. We use the email as the stable remote ID so that
    re-provisioning the same user is idempotent.
    Returns {"remote_user_id": "<id>"} — Opal stores this and uses it
    as the user_id in all subsequent group membership calls.
    """
    attributes = body.get("attributes", {})
    email = attributes.get("email")
    if not email:
        raise ErrorException(code=400, message="attributes.email is required")

    # Use email as the remote ID so the connector stays idempotent
    remote_user_id = email
    state.users[remote_user_id] = {"email": email}
    return {"remote_user_id": remote_user_id}


@app.delete("/users/{user_id}")
async def delete_user(user_id: str):
    """
    Called by Opal to deprovision a user from the app entirely.
    user_id is the remote_user_id we returned from POST /users.
    """
    if user_id not in state.users:
        # Treat as idempotent — already gone is fine
        return {}
    # Remove from all groups first
    for g in state.groups.values():
        if user_id in g["users"]:
            g["users"].remove(user_id)
    del state.users[user_id]
    return {}


# ---------------------------------------------------------------------------
# Groups
# ---------------------------------------------------------------------------

@app.get("/groups")
async def get_groups(app_id: str, cursor: str = None):
    return {
        "groups": [
            {"id": gid, "name": g["name"], "description": g["description"]}
            for gid, g in state.groups.items()
        ]
    }


@app.get("/groups/{group_id}")
async def get_group(group_id: str, app_id: str):
    g = state.groups.get(group_id)
    if not g:
        raise ErrorException(code=404, message=f"Group {group_id} not found")
    return {"group": {"id": group_id, "name": g["name"], "description": g["description"]}}


@app.get("/groups/{group_id}/users")
async def get_group_users(group_id: str, app_id: str, cursor: str = None):
    g = state.groups.get(group_id)
    if not g:
        raise ErrorException(code=404, message=f"Group {group_id} not found")
    return {
        "users": [
            {"user_id": uid, "email": state.users[uid]["email"]}
            for uid in g["users"]
            if uid in state.users
        ]
    }


@app.post("/groups/{group_id}/users")
async def add_group_user(group_id: str, body: dict):
    g = state.groups.get(group_id)
    if not g:
        raise ErrorException(code=404, message=f"Group {group_id} not found")
    user_id = body.get("user_id")
    if not user_id:
        raise ErrorException(code=400, message="user_id is required")
    if user_id not in state.users:
        raise ErrorException(code=404, message=f"User {user_id} not found")
    if user_id not in g["users"]:
        g["users"].append(user_id)
    return {}


@app.delete("/groups/{group_id}/users/{user_id}")
async def remove_group_user(group_id: str, user_id: str, app_id: str):
    g = state.groups.get(group_id)
    if not g:
        raise ErrorException(code=404, message=f"Group {group_id} not found")
    if user_id not in state.users:
        raise ErrorException(code=404, message=f"User {user_id} not found")
    if user_id not in g["users"]:
        raise ErrorException(code=404, message=f"User {user_id} not in group {group_id}")
    g["users"].remove(user_id)
    return {}


@app.get("/groups/{group_id}/resources")
async def get_group_resources(group_id: str, app_id: str, cursor: str = None):
    g = state.groups.get(group_id)
    if not g:
        raise ErrorException(code=404, message=f"Group {group_id} not found")
    return {"resources": []}


# ---------------------------------------------------------------------------
# Resources (stub — this connector has no resources)
# ---------------------------------------------------------------------------

@app.get("/resources")
async def get_resources(app_id: str, cursor: str = None, parent_id: str = None):
    return {"resources": []}
