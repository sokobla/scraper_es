import json
from extensions import db
from models.result_model import Result
from persistence.result_repository import ResultRepository

class ResultService:
    def __init__(self, repository=None):
        self.repository = repository or ResultRepository()

    def save_many(self, items: list[dict]):
        saved = []

        for item in items:
            if not item.get("source") or not item.get("title"):
                continue

            entity = Result(
                source=item["source"],
                title=item["title"],
                url=item.get("url"),
                score=item.get("score"),
                raw_payload=json.dumps(item.get("raw_payload"), ensure_ascii=False)
                if item.get("raw_payload") is not None else None
            )

            self.repository.add(entity)
            saved.append(entity)

        db.session.commit()
        return saved