from datetime import datetime, timedelta
from functools import wraps

from flask import Blueprint, abort, jsonify, request, session
from werkzeug.security import generate_password_hash

from models import Event, Rover, User, db


api = Blueprint("api", __name__, url_prefix="/api")
ONLINE_TIMEOUT_S = 10


def require_ui_roles(*roles):
    def dec(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            role = session.get("role")
            if role is None:
                abort(401)
            if roles and role not in roles:
                abort(403)
            return fn(*args, **kwargs)

        return wrapper

    return dec


def rover_auth(fn):
    @wraps(fn)
    def wrapper(id, *args, **kwargs):
        rover = Rover.query.filter_by(id=id, is_deleted=False).first_or_404()
        token = request.headers.get("Authorization", "").replace("Bearer ", "")
        if token != rover.api_token:
            abort(401)
        return fn(rover, *args, **kwargs)

    return wrapper


def _is_online(rover: Rover) -> bool:
    if not rover.last_seen:
        return False
    return rover.last_seen >= datetime.utcnow() - timedelta(seconds=ONLINE_TIMEOUT_S)


@api.get("/ui/rovers")
@require_ui_roles("admin", "operator", "moder", "viewer")
def ui_rovers():
    rovers = Rover.query.filter_by(is_deleted=False).all()
    return jsonify([
        {
            "id": r.id,
            "name": r.name,
            "ip_address": r.ip_address,
            "mode_desired": r.mode_desired,
            "mode_reported": r.mode_reported,
            "pdd_state": r.pdd_state,
            "last_seen": r.last_seen.isoformat() if r.last_seen else None,
            "online": _is_online(r),
            "location": {"lat": r.last_lat, "lon": r.last_lon},
        }
        for r in rovers
    ])


@api.get("/admin/users")
@require_ui_roles("admin")
def list_users():
    users = User.query.order_by(User.username.asc()).all()
    return jsonify([
        {
            "id": u.id,
            "username": u.username,
            "role": u.role,
        }
        for u in users
    ])


@api.post("/admin/users")
@require_ui_roles("admin")
def add_user():
    body = request.get_json(force=True)
    username = (body.get("username") or "").strip()
    password = body.get("password") or ""
    role = (body.get("role") or "viewer").strip().lower()

    if not username or len(password) < 6:
        abort(422)
    if role not in {"admin", "moder", "operator", "viewer"}:
        abort(422)
    if User.query.filter_by(username=username).first():
        return jsonify({"ok": False, "error": "user_exists"}), 409

    user = User(username=username, password_hash=generate_password_hash(password), role=role)
    db.session.add(user)
    db.session.add(Event(rover_id="rover-001", actor=session.get("username", "admin"), kind="user_add", payload=str({"username": username, "role": role})))
    db.session.commit()
    return jsonify({"ok": True, "user": {"username": username, "role": role}})


@api.post("/admin/rovers")
@require_ui_roles("admin")
def add_rover():
    body = request.get_json(force=True)
    rover_id = (body.get("id") or "").strip()
    ip_address = (body.get("ip_address") or "").strip()
    name = (body.get("name") or rover_id).strip()
    token = (body.get("api_token") or "CHANGE_ME").strip()

    if not rover_id or not ip_address:
        abort(422)
    existing = Rover.query.filter_by(id=rover_id).first()
    if existing:
        return jsonify({
            "ok": False,
            "error": "rover_exists",
            "message": f"Rover with id '{rover_id}' already exists",
            "existing": {"id": existing.id, "name": existing.name, "ip_address": existing.ip_address, "is_deleted": existing.is_deleted},
        }), 409

    rover = Rover(id=rover_id, name=name, ip_address=ip_address, api_token=token)
    db.session.add(rover)
    db.session.add(Event(rover_id=rover_id, actor=session.get("username", "admin"), kind="rover_add", payload=str(body)))
    db.session.commit()
    return jsonify({"ok": True, "rover": {"id": rover.id, "ip_address": rover.ip_address}})


@api.post("/rovers/<id>/command")
@require_ui_roles("admin", "operator", "moder")
def command(id):
    rover = Rover.query.filter_by(id=id, is_deleted=False).first_or_404()
    body = request.get_json(force=True)
    rover.mode_desired = body.get("mode", rover.mode_desired)
    action = body.get("action")
    event_kind = "lid_open" if action == "open_lid" else "command"
    db.session.add(Event(rover_id=id, actor=session.get("username", "operator"), kind=event_kind, payload=str(body)))
    db.session.commit()
    return jsonify({"ok": True, "mode_desired": rover.mode_desired, "seq_id": body.get("seq_id"), "action": action})


@api.post("/rovers/<id>/connectivity-check")
@require_ui_roles("admin", "operator", "moder", "viewer")
def connectivity_check(id):
    rover = Rover.query.filter_by(id=id, is_deleted=False).first_or_404()
    return jsonify({"ok": True, "online": _is_online(rover), "last_seen": rover.last_seen.isoformat() if rover.last_seen else None})


@api.post("/rover/<id>/heartbeat")
@rover_auth
def heartbeat(rover):
    body = request.get_json(force=True)
    rover.mode_reported = body.get("mode_reported", rover.mode_reported)
    rover.pdd_state = body.get("pdd_state", rover.pdd_state)
    gps = body.get("gps") or {}
    rover.last_lat = gps.get("lat", rover.last_lat)
    rover.last_lon = gps.get("lon", rover.last_lon)
    rover.last_seen = datetime.utcnow()
    db.session.add(Event(rover_id=rover.id, actor=rover.id, kind="heartbeat", payload=str(body)))
    db.session.commit()
    return jsonify({"ok": True, "mode_desired": rover.mode_desired})


@api.post("/rover/<id>/ack")
@rover_auth
def ack(rover):
    body = request.get_json(force=True)
    db.session.add(Event(rover_id=rover.id, actor=rover.id, kind="ack", payload=str(body)))
    db.session.commit()
    return jsonify({"ok": True})


@api.delete("/admin/rovers/<id>")
@require_ui_roles("admin")
def delete_rover(id):
    rover = Rover.query.filter_by(id=id).first_or_404()
    rover.is_deleted = True
    rover.api_token = "revoked"
    db.session.add(Event(rover_id=rover.id, actor=session.get("username", "admin"), kind="soft_delete", payload="{}"))
    db.session.commit()
    return jsonify({"ok": True, "is_deleted": True})
