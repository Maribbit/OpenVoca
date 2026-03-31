from sqlmodel import Field, Session, SQLModel, select

from src.services.word_store import get_engine


class SettingRecord(SQLModel, table=True):
    namespace: str = Field(primary_key=True)
    key: str = Field(primary_key=True)
    value: str = Field()


def _get_engine(engine=None):
    return engine or get_engine()


def init_settings_table(engine=None) -> None:
    """Create the settings table if it doesn't exist."""
    target = _get_engine(engine)
    SQLModel.metadata.create_all(target)


def get_setting(namespace: str, key: str, engine=None) -> str | None:
    """Return the value for a single setting, or None if not found."""
    target = _get_engine(engine)
    with Session(target) as session:
        record = session.exec(
            select(SettingRecord).where(
                SettingRecord.namespace == namespace,
                SettingRecord.key == key,
            )
        ).first()
        return record.value if record else None


def get_namespace(namespace: str, engine=None) -> dict[str, str]:
    """Return all settings in a namespace as a dict."""
    target = _get_engine(engine)
    with Session(target) as session:
        records = session.exec(
            select(SettingRecord).where(SettingRecord.namespace == namespace)
        ).all()
        return {r.key: r.value for r in records}


def get_all_settings(engine=None) -> dict[str, dict[str, str]]:
    """Return all settings grouped by namespace."""
    target = _get_engine(engine)
    with Session(target) as session:
        records = session.exec(select(SettingRecord)).all()
        result: dict[str, dict[str, str]] = {}
        for r in records:
            result.setdefault(r.namespace, {})[r.key] = r.value
        return result


def upsert_setting(namespace: str, key: str, value: str, engine=None) -> None:
    """Insert or update a single setting."""
    target = _get_engine(engine)
    with Session(target) as session:
        record = session.exec(
            select(SettingRecord).where(
                SettingRecord.namespace == namespace,
                SettingRecord.key == key,
            )
        ).first()
        if record:
            record.value = value
        else:
            session.add(SettingRecord(namespace=namespace, key=key, value=value))
        session.commit()


def upsert_namespace(namespace: str, settings: dict[str, str], engine=None) -> None:
    """Batch upsert all settings in a namespace."""
    target = _get_engine(engine)
    with Session(target) as session:
        for key, value in settings.items():
            record = session.exec(
                select(SettingRecord).where(
                    SettingRecord.namespace == namespace,
                    SettingRecord.key == key,
                )
            ).first()
            if record:
                record.value = value
            else:
                session.add(SettingRecord(namespace=namespace, key=key, value=value))
        session.commit()


def delete_namespace(namespace: str, engine=None) -> int:
    """Delete all settings in a namespace. Returns count of deleted rows."""
    target = _get_engine(engine)
    with Session(target) as session:
        records = session.exec(
            select(SettingRecord).where(SettingRecord.namespace == namespace)
        ).all()
        count = len(records)
        for record in records:
            session.delete(record)
        session.commit()
        return count
