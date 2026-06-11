import json

from database.session import SessionLocal
from models.result_model import Result
from persistence.result_repository import ResultRepository

class ResultService:
    def __init__(self, repository=None):
        self.repository = repository or ResultRepository()

    def save_many(self, category: dict, items: list[dict]):
        # 1. Filtrer les éléments valides et extraire leurs identifiants
        valid_items = [
            item for item in items
            if item.get("source") and item.get("title") and item.get("url")
        ]
        if not valid_items:
            return []

        item_identifiers = [(item["title"], item["url"]) for item in valid_items]

        with SessionLocal() as session:
            # 2. Récupérer tous les éléments existants en une seule requête
            #    Ceci nécessite une nouvelle méthode dans le repository.
            existing_tuples = self.repository.find_existing_by_title_and_url(
                session, identifiers=item_identifiers
            )
            existing_set = set(existing_tuples)

            # 3. Déterminer les nouveaux éléments et créer les entités
            new_entities = []
            for item in valid_items:
                if (item["title"], item["url"]) in existing_set:
                    continue  # Ignorer si l'élément existe déjà

                entity = Result(
                    category_name=category.get("name"),
                    category_description=category.get("description"),
                    category_image=category.get("image"),
                    source=item.get("source"),
                    title=item.get("title"),
                    url=item.get("url"),
                    score=item.get("score"),
                    nom=item.get("nom"),
                    rue=item.get("rue"),
                    code_postal=item.get("code_postal"),
                    ville=item.get("ville"),
                    telephone=item.get("telephone"),
                    raw_payload=(
                        json.dumps(item.get("raw_payload"), ensure_ascii=False)
                        if item.get("raw_payload") is not None
                        else None
                    ),
                )
                new_entities.append(entity)

            # 4. Insérer en masse les nouvelles entités et valider la transaction
            if new_entities:
                session.add_all(new_entities)
                session.commit()

        return new_entities

    def list_results(self):
        with SessionLocal() as session:
            return self.repository.list_all(session)