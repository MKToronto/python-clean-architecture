from typing import Any, Protocol

DataObject = dict[str, Any]


class DataInterface(Protocol):
    def read_by_id(self, id: str) -> DataObject: ...
    def read_all(self) -> list[DataObject]: ...
    def create(self, data: DataObject) -> DataObject: ...
    def update(self, id: str, data: DataObject) -> DataObject: ...
    def delete(self, id: str) -> None: ...


class DataInterfaceStub:
    def __init__(self):
        self.data: dict[str, DataObject] = {}

    def read_by_id(self, id: str) -> DataObject:
        if id not in self.data:
            raise KeyError(f"Not found: {id}")
        return self.data[id]

    def read_all(self) -> list[DataObject]:
        return list(self.data.values())

    def create(self, data: DataObject) -> DataObject:
        self.data[data["id"]] = data
        return data

    def update(self, id: str, data: DataObject) -> DataObject:
        if id not in self.data:
            raise KeyError(f"Not found: {id}")
        self.data[id].update(data)
        return self.data[id]

    def delete(self, id: str) -> None:
        if id not in self.data:
            raise KeyError(f"Not found: {id}")
        del self.data[id]
