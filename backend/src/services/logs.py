from sqlalchemy.orm import Session
from ..models.system_log import SystemLog


def log_event(db: Session, level: str, event_type: str, message: str, actor_user_id=None, ip=None, user_agent=None):
    db.add(SystemLog(
        level=level,
        event_type=event_type,
        message=message,
        actor_user_id=actor_user_id,
        ip=ip,
        user_agent=user_agent
    ))