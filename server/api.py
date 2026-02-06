from datetime import datetime
from functools import wraps

from flask import Blueprint, abort, jsonify, request

from models import Event, Rover, db


api = Blueprint("api", __name__, url_prefix="/api")


def rover_auth(fn):
    @wraps(fn)
    def wrapper(id, *args, **kwargs):
        rover = Rover.query.filter_by(id=id, is_deleted=False).first_or_404()
        token = request.headers.get("Authorization", "").replace("Bearer ", "")
        if token != rover.api_token:
            abort(401)
        return fn(rover, *args, **kwargs)

    return wrapper


@api.get("/ui/rovers")
def ui_rovers():
    rovers = Rover.query.filter_by(is_deleted=False).all()
    return jsonify([
        {
            "id": r.id,
            "name": r.name,
            "mode_desired": r.mode_desired,
            "mode_reported": r.mode_reported,
            "pdd_state": r.pdd_state,
            "last_seen": r.last_seen.isoformat() if r.last_seen else None,
        }
        for r in rovers
    ])


@api.post("/rovers/<id>/command")
def command(id):
    rover = Rover.query.filter_by(id=id, is_deleted=False).first_or_404()
    body = request.get_json(force=True)
    rover.mode_desired = body.get("mode", rover.mode_desired)
    db.session.add(Event(rover_id=id, actor="operator", kind="command", payload=str(body)))
    db.session.commit()
    return jsonify({"ok": True, "mode_desired": rover.mode_desired, "seq_id": body.get("seq_id")})


@api.post("/rover/<id>/heartbeat")
@rover_auth
def heartbeat(rover):
    body = request.get_json(force=True)
    rover.mode_reported = body.get("mode_reported", rover.mode_reported)
    rover.pdd_state = body.get("pdd_state", rover.pdd_state)
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
def delete_rover(id):
    rover = Rover.query.filter_by(id=id).first_or_404()
    rover.is_deleted = True
    rover.api_token = "revoked"
    db.session.add(Event(rover_id=rover.id, actor="admin", kind="soft_delete", payload="{}"))
    db.session.commit()
    return jsonify({"ok": True, "is_deleted": True})
