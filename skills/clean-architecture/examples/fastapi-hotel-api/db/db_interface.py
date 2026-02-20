from typing import Any

from sqlalchemy.orm import Session

DataObject = dict[str, Any]


def to_dict(obj) -> DataObject:
    return {col.name: getattr(obj, col.name) for col in obj.__table__.columns}


class DBInterface:
    def __init__(self, db_session: Session, db_class: type):
        self.db_session = db_session
        self.db_class = db_class

    def read_by_id(self, id: str) -> DataObject:
        obj = self.db_session.query(self.db_class).get(id)
        if obj is None:
            raise KeyError(f"Not found: {id}")
        return to_dict(obj)

    def read_all(self) -> list[DataObject]:
        objects = self.db_session.query(self.db_class).all()
        return [to_dict(obj) for obj in objects]

    def create(self, data: DataObject) -> DataObject:
        obj = self.db_class(**data)
        self.db_session.add(obj)
        self.db_session.commit()
        return to_dict(obj)

    def update(self, id: str, data: DataObject) -> DataObject:
        obj = self.db_session.query(self.db_class).get(id)
        if obj is None:
            raise KeyError(f"Not found: {id}")
        for key, value in data.items():
            setattr(obj, key, value)
        self.db_session.commit()
        return to_dict(obj)

    def delete(self, id: str) -> None:
        obj = self.db_session.query(self.db_class).get(id)
        if obj is None:
            raise KeyError(f"Not found: {id}")
        self.db_session.delete(obj)
        self.db_session.commit()
