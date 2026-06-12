# scrapper_spain

> Web scraper asynchrone pour l'agrégation de données commerciales depuis paginasamarillas.es (pages jaunes espagnoles)

[![Status](https://img.shields.io/badge/status-MVP-orange)](README.md)
[![Python](https://img.shields.io/badge/python-3.11%2B-blue)](https://www.python.org)
[![License](https://img.shields.io/badge/license-MIT-green)](LICENSE)

---

## 📋 Tableau de contenu

- [Vue d'ensemble](#vue-densemble)
- [Démarrage rapide](#démarrage-rapide)
- [Architecture](#architecture)
- [Configuration](#configuration)
- [Utilisation](#utilisation)
- [Développement](#développement)
- [Dépannage](#dépannage)
- [Documentation](#documentation)
- [Contribution](#contribution)
- [License](#license)

---

## 🎯 Vue d'ensemble

**scrapper_spain** est un outil de scraping web conçu pour collecter systématiquement des informations sur les entreprises espagnoles (Gym, dépôts, garages, etc.) depuis le portail paginasamarillas.es.

### Caractéristiques principales

✅ **Asynchrone** — Utilise asyncio + Playwright pour scraping hautement performant  
✅ **Persistance** — Sauvegarde les données dans PostgreSQL avec schéma structuré  
✅ **Configurable** — Catégories & paramètres via `config.yml`  
✅ **Containerisé** — Dockerfile + docker-compose pour déploiement simple  
✅ **Antidetection** — Playwright Stealth Mode pour éviter les blocages  
✅ **Logging structuré** — Traces complètes pour débogage & monitoring  

### Cas d'usage

- Agrégation de données d'annuaires commerciaux
- Monitoring de prix/services par catégorie
- Enrichissement de bases de données de leads
- Analyse comparative de marchés régionaux

### Stack technique

| Composant | Technologie | Version |
|-----------|-------------|---------|
| **Runtime** | Python | 3.11+ |
| **Web Scraping** | Playwright | 1.60.0+ |
| **Framework API** | Flask | 3.1.3 |
| **ORM Database** | SQLAlchemy + Flask-SQLAlchemy | 2.0.50 + 3.1.1 |
| **Database** | PostgreSQL | 13+ |
| **Async** | asyncio + pyee | Built-in + 13.0.1 |
| **Config** | YAML | PyYAML 6.0.3 |
| **Containerization** | Docker & docker-compose | Latest |

---

## 🚀 Démarrage rapide

### Prérequis

- **Python 3.11+** ([Download](https://www.python.org/downloads/))
- **PostgreSQL 13+** ([Download](https://www.postgresql.org/download/))
- **Docker & docker-compose** (optionnel, pour environnement isolé)

### Installation locale

#### 1. Cloner le repository
```bash
git clone https://github.com/yourusername/scrapper_spain.git
cd scrapper_spain
```

#### 2. Créer environnement virtuel
```bash
python -m venv .venv

# Windows
.venv\Scripts\activate

# macOS / Linux
source .venv/bin/activate
```

#### 3. Installer dépendances
```bash
pip install -r requirements.txt
playwright install
```

#### 4. Configurer base de données

Créer `.env` avec vos identifiants PostgreSQL :
```env
DATABASE_URL=postgresql://scrapper:password@localhost:5432/scrapper_db
LOG_LEVEL=INFO
```

Ou éditer `config.yml` :
```yaml
database:
  url: "postgresql://scrapper:password@localhost:5432/scrapper_db"
```

#### 5. Initialiser la base de données
```bash
python -c "from database.session import init_db; init_db()"
```

#### 6. Exécuter le scraper
```bash
python run_scrapper.py
```

Résultat attendu :
```
[2026-06-12 10:15:30] root [INFO] 4 catégorie(s) chargée(s) depuis config.yml
[2026-06-12 10:15:30] root [INFO] Scraping catégorie=Gym...
[2026-06-12 10:15:45] root [INFO] [OK] Scraping terminé pour Gym
...
```

---

### Avec Docker (Recommandé pour production)

#### 1. Démarrer les services
```bash
docker-compose up --build
```

Ou en arrière-plan :
```bash
docker-compose up -d
```

#### 2. Vérifier les logs
```bash
docker-compose logs -f scraper
```

#### 3. Arrêter les services
```bash
docker-compose down
```

**Notes** :
- Les identifiants DB par défaut sont : `myuser:mypassword`
- Modifier `.env` pour production (voir section [Configuration](#configuration))
- Données persistées dans `db_data/` volume Docker

---

## 🏗️ Architecture

### Flux d'exécution

```
run_scrapper.py (point d'entrée)
    ↓
[1] Charger catégories depuis config.yml
    ↓
[2] Initialiser DB (database/session.py → init_db())
    ↓
[3] Créer ScraperRunner instance
    ↓
[4] Pour chaque catégorie :
    ├─ Lancer navigateur Playwright
    ├─ Naviguer vers base_url + query
    ├─ Paginer résultats (max_pages=3)
    ├─ Parser HTML → extraire données entreprises
    ├─ Insérer en BD via SQLAlchemy ORM
    └─ Logger succès/erreur
```

### Structure modulaire

```
scrapper_spain/
├── run_scrapper.py              # Point d'entrée principal
├── config.yml                   # Configuration (catégories, paramètres)
├── requirements.txt             # Dépendances Python
├── Dockerfile                   # Image conteneur
├── docker-compose.yml           # Orchestration locale
├── .env.example                 # Template variables d'environnement
│
├── database/                    # Couche données
│   ├── __init__.py
│   ├── models.py               # ORM models (Business, Contact, Category)
│   └── session.py              # SQLAlchemy engine & init_db()
│
├── scraper/                     # Logique extraction
│   ├── __init__.py
│   ├── scraper_runner.py       # Orchestrateur async (ScraperRunner)
│   ├── browser_manager.py      # Gestion navigateur Playwright
│   └── parsers.py              # HTML parsing (BeautifulSoup)
│
├── utils/                       # Utilitaires
│   ├── __init__.py
│   └── logger.py               # Logging structuré
│
├── tests/                       # Suite de tests (pytest)
│   ├── conftest.py             # Fixtures
│   ├── test_config.py
│   ├── test_database.py
│   ├── test_scraper.py
│   └── test_logger.py
│
├── CLAUDE.md                    # Guide développeur Claude Code
├── AUDIT_REPORT.md             # Rapport d'audit technique détaillé
├── DEPLOYMENT.md               # Checklist déploiement production
└── LICENSE                      # MIT
```

### Modèles de données

#### Business (Entreprises scrapées)
```python
class Business(db.Model):
    id: int                    # Primary key
    name: str                  # Nom entreprise
    address: str               # Adresse
    phone: str                 # Téléphone
    email: str                 # Email
    website: str               # Site web
    category: str              # Catégorie (Gym, dépôt, etc.)
    created_at: datetime       # Timestamp création
```

#### Contact (Informations supplémentaires)
```python
class Contact(db.Model):
    id: int                    # Primary key
    business_id: int           # Foreign key → Business
    contact_type: str          # Type (phone, email, mobile, etc.)
    value: str                 # Valeur
    created_at: datetime
```

#### Category (Catégories)
```python
class Category(db.Model):
    name: str                  # PK (Gym, dépôt, etc.)
    description: str
    image_url: str
```

---

## ⚙️ Configuration

### config.yml

Fichier principal de configuration :

```yaml
# Connexion base de données
database:
  url: "postgresql://user:password@host:5432/dbname"
  
# Paramètres scraper
scraper:
  base_url: "https://www.paginasamarillas.es/search/"
  user_agent: "Mozilla/5.0..."  # Optionnel
  timeout_seconds: 30
  rate_limit_delay: 2            # Délai entre requêtes (sec)
  
# Catégories à scraper (liste)
categorie:
  - name: "Gym"
    description: "Salles de fitness et entraînement"
    image: "gym.jpg"
    
  - name: "depósito"
    description: "Services d'entreposage"
    image: "deposito.jpg"
    
  - name: "cochera"
    description: "Garages et parkings"
    image: "cochera.jpg"
    
  - name: "almacenar"
    description: "Solutions de stockage"
    image: "almacenar.jpg"
```

### Variables d'environnement

Créer `.env` pour override config.yml :

```bash
# Base de données
DATABASE_URL=postgresql://scrapper:secure_password@localhost:5432/scrapper_db

# Logging
LOG_LEVEL=INFO                    # DEBUG, INFO, WARNING, ERROR

# Scraper
SCRAPER_HEADLESS=true             # Headless mode (true recommandé)
SCRAPER_MAX_PAGES=3               # Pages max par catégorie
SCRAPER_RATE_LIMIT_DELAY=2        # Délai entre requêtes (sec)

# Optional: Proxy (si scraping depuis proxy)
HTTP_PROXY=http://proxy:port
HTTPS_PROXY=http://proxy:port
```

### Docker .env

Pour docker-compose, créer `.env` à la racine :

```bash
DB_USER=scrapper
DB_PASSWORD=secure_password
DB_NAME=scrapper_db
```

---

## 💻 Utilisation

### Exécution simple

```bash
# Mode développement avec logs verbeux
LOG_LEVEL=DEBUG python run_scrapper.py
```

### Exécution avec paramètres

```bash
# Override via env vars
SCRAPER_MAX_PAGES=10 python run_scrapper.py
```

### Scraper une seule catégorie (Développement)

Éditer `run_scrapper.py` temporairement :
```python
# Filtrer catégories
categories = load_categories_from_config("config.yml")
categories = [c for c in categories if c["name"] == "Gym"]  # Gym only
```

### Vérifier les données scrapées

```bash
# Connexion PostgreSQL
psql postgresql://scrapper:password@localhost:5432/scrapper_db

# Requêtes utiles
SELECT COUNT(*) FROM business;
SELECT COUNT(*) FROM business WHERE category = 'Gym';
SELECT name, phone FROM business WHERE category = 'Gym' LIMIT 5;
```

---

## 🛠️ Développement

### Installation mode édition

```bash
# Installer dépendances + dev tools
pip install -r requirements.txt
pip install pytest pytest-asyncio black flake8 isort

# Installer pre-commit hooks (optionnel)
pre-commit install
```

### Linting & formatting

```bash
# Format code
black .
isort .

# Lint Python
flake8 . --max-line-length=100

# Type checking (optionnel)
mypy database/ scraper/ utils/
```

### Tests

```bash
# Lancer tous les tests
pytest tests/ -v

# Tests avec couverture
pytest tests/ --cov=. --cov-report=html

# Ouvrir rapport couverture
open htmlcov/index.html  # macOS
# or
start htmlcov/index.html  # Windows
```

### Ajouter une nouvelle catégorie

1. Éditer `config.yml` :
```yaml
categorie:
  - name: "nouvelle_categorie"
    description: "Description"
    image: "icon.jpg"
```

2. Relancer le scraper :
```bash
python run_scrapper.py
```

---

## 🐛 Dépannage

### Erreur: "ModuleNotFoundError: No module named 'database'"

**Cause** : Modules non implémentés (MVP phase)  
**Solution** : Voir [AUDIT_REPORT.md](AUDIT_REPORT.md) section "Plan d'implémentation" pour installer les modules

### Erreur: "psycopg2: FATAL: Ident authentication failed"

**Cause** : Identifiants PostgreSQL incorrects  
**Solution** :
```bash
# Vérifier .env
cat .env

# Ou vérifier config.yml
grep database config.yml

# Ou tester connexion
psql postgresql://user:password@localhost:5432/dbname
```

### Erreur: "TimeoutError: Target page, context or browser has been closed"

**Cause** : Timeout Playwright, site peut être slow/down  
**Solution** :
```bash
# Augmenter timeout
# Dans run_scrapper.py:
runner = ScraperRunner(headless=True, max_pages=3, timeout=60)

# Ou réduire max_pages
runner = ScraperRunner(headless=True, max_pages=1)
```

### Docker: "Cannot connect to database"

**Cause** : Service PostgreSQL non lancé ou réseau Docker  
**Solution** :
```bash
# Vérifier services
docker-compose ps

# Redémarrer
docker-compose down && docker-compose up --build

# Vérifier logs
docker-compose logs db
```

### IP bloquée par le site

**Cause** : Trop de requêtes simultanées  
**Solution** :
```yaml
# Augmenter délai en config.yml
scraper:
  rate_limit_delay: 5  # De 2 à 5 sec entre requêtes
```

Ou utiliser proxy :
```bash
HTTP_PROXY=http://proxy_ip:port python run_scrapper.py
```

---

## 📚 Documentation

| Document | Contenu |
|----------|---------|
| **[CLAUDE.md](CLAUDE.md)** | Guide architecture & développement pour Claude Code |
| **[AUDIT_REPORT.md](AUDIT_REPORT.md)** | Rapport technique complet (sécurité, performance, gaps) |
| **[DEPLOYMENT.md](DEPLOYMENT.md)** | Checklist & guide déploiement production *(à créer)* |
| **[DATABASE.md](DATABASE.md)** | Schéma ER & requêtes SQL fréquentes *(à créer)* |

### Générer documentation API (si routes Flask ajoutées)

```bash
pip install flask-restx
# Swagger auto-généré à /api/docs
```

---

## 🚨 État & Feuille de route

### ✅ MVP Actuel
- [x] Point d'entrée `run_scrapper.py`
- [x] Configuration via `config.yml`
- [x] Docker & docker-compose
- [x] Dépendances définies

### 🟡 Phase 1 (En cours)
- [ ] Implémenter `database/models.py` & `session.py`
- [ ] Implémenter `utils/logger.py`
- [ ] Implémenter `scraper/` (runner, browser_manager, parsers)
- [ ] Ajouter tests (pytest)

### 🔴 Phase 2 (Planifié)
- [ ] Migrations DB (Flask-Migrate)
- [ ] Rate limiting & retry logic
- [ ] Validation config (Pydantic)
- [ ] Sécurité: env vars, user non-root Docker
- [ ] API Flask endpoints (optionnel)
- [ ] Monitoring & alerting

### Contribution

Les contributions sont bienvenues ! Voir [CONTRIBUTING.md](CONTRIBUTING.md) *(à créer)*.

**Pour signaler un bug** : [GitHub Issues](https://github.com/yourusername/scrapper_spain/issues)

---

## 📄 License

MIT License — Voir [LICENSE](LICENSE) pour détails.

---

## 📞 Support

- **Issues** : [GitHub Issues](https://github.com/yourusername/scrapper_spain/issues)
- **Discussions** : [GitHub Discussions](https://github.com/yourusername/scrapper_spain/discussions)
- **Email** : [support@example.com](mailto:support@example.com)

---

## 🙏 Remerciements

- [Playwright](https://playwright.dev/) — Web scraping
- [Flask](https://flask.palletsprojects.com/) — Framework web
- [SQLAlchemy](https://www.sqlalchemy.org/) — ORM
- [PostgreSQL](https://www.postgresql.org/) — Base de données

---

**Dernière mise à jour** : 12 juin 2026  
**Mainteneur** : [@yourusername](https://github.com/yourusername)
