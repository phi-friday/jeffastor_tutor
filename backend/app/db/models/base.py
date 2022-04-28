from sqlmodel import SQLModel, Table


class base_model(SQLModel):
    @classmethod
    def get_table(cls) -> Table:
        if (table := getattr(cls, "__table__", None)) is None:
            raise ValueError("not table")
        return table
