from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """Base declarativa do SQLAlchemy. Os modelos das próximas fases herdam daqui."""
