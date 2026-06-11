from sqlalchemy import Integer, String, Float, Text
from sqlalchemy.orm import Mapped, mapped_column

from database.base import Base

class Result(Base):
    __tablename__ = "results"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    category_name: Mapped[str] = mapped_column(String(255), nullable=False)
    category_description: Mapped[str | None] = mapped_column(Text, nullable=True)
    category_image: Mapped[str | None] = mapped_column(String(255), nullable=True)

    source: Mapped[str] = mapped_column(String(255), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    url: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    score: Mapped[float | None] = mapped_column(Float, nullable=True)
    nom: Mapped[str | None] = mapped_column(String(255), nullable=True)
    rue: Mapped[str | None] = mapped_column(String(255), nullable=True)
    code_postal: Mapped[str | None] = mapped_column(String(20), nullable=True)
    ville: Mapped[str | None] = mapped_column(String(255), nullable=True)
    telephone: Mapped[str | None] = mapped_column(String(50), nullable=True)
    raw_payload: Mapped[str | None] = mapped_column(Text, nullable=True)

    def to_dict(self):
        return {
            "id": self.id,
            "category_name": self.category_name,
            "category_description": self.category_description,
            "category_image": self.category_image,
            "source": self.source,
            "title": self.title,
            "url": self.url,
            "score": self.score,
            "nom": self.nom,
            "rue": self.rue,
            "code_postal": self.code_postal,
            "ville": self.ville,
            "telephone": self.telephone,
            "raw_payload": self.raw_payload,
        }