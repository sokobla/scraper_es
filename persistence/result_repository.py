from typing import Optional

from sqlalchemy import select, tuple_
from sqlalchemy.orm import Session

from models.result_model import Result

class ResultRepository:
    def add(self, session: Session, result: Result) -> Result:
        session.add(result)
        return result

    def list_all(self, session: Session) -> list[Result]:
        stmt = select(Result).order_by(Result.id.desc())
        return list(session.scalars(stmt).all())

    def exists_by_title_and_url(self, session: Session, title: str, url: Optional[str]) -> bool:
        stmt = select(Result).where(Result.title == title, Result.url == url)
        return session.execute(stmt).scalar_one_or_none() is not None

    def find_existing_by_title_and_url(
        self, session: Session, identifiers: list[tuple[str, str]]
    ) -> set[tuple[str, str]]:
        """
        Trouve les résultats existants à partir d'une liste de tuples (title, url).
        Retourne un set de tuples (title, url) qui existent déjà en base de données.
        """
        if not identifiers:
            return set()

        stmt = select(Result.title, Result.url).where(
            tuple_(Result.title, Result.url).in_(identifiers)
        )
        return set(session.execute(stmt).all())