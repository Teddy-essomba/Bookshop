# Bookshop API

A REST API for managing books, authors and per-user reading lists, built with
Django REST Framework. Stateless JWT authentication, row-level authorization,
and an auto-generated OpenAPI schema.

Built for CSC1040 Full Stack Development (DCU), then extended beyond the module
material with custom token claims, per-object permissions and a test suite.

**Status:** backend complete. React frontend planned — CORS and JWT are already
configured for it.

---

## Stack

| | |
|---|---|
| Framework | Django 4.2 + Django REST Framework 3.15 |
| Auth | `djangorestframework-simplejwt` 5.4 (JWT, rotating refresh tokens) |
| Docs | `drf-spectacular` 0.28 (OpenAPI 3 / Swagger UI) |
| Database | SQLite (development) |
| CORS | `django-cors-headers`, allowing `localhost:5173` |
| Python | **3.12** — see [Requirements](#requirements) |

---

## Requirements

> **Python 3.12 is required.** Django 4.2 supports Python 3.8–3.12 only.
> On Python 3.13+ the admin raises
> `AttributeError: 'super' object has no attribute 'dicts'`, caused by a change
> to `copy.copy()` behaviour that breaks Django's template context copying.

---

## Getting started

```bash
git clone https://github.com/Teddy-essomba/Bookshop.git
cd Bookshop

python3.12 -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate

pip install -r requirements.txt

# Secrets live in .env, which is gitignored. Create it from the template
# and generate a key:
cp .env.example .env
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
# paste the output as the value of DJANGO_SECRET_KEY in .env

python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

### Environment variables

| Variable | Required | Purpose |
|---|---|---|
| `DJANGO_SECRET_KEY` | yes | Signs session cookies, password-reset links and every JWT (`SIMPLE_JWT['SIGNING_KEY']` points at it). The app refuses to start without it — deliberately, so it can never boot with a default key by accident. |

Then open **http://127.0.0.1:8000/api/docs/** for the interactive API browser.

---

## API

Base URL: `http://127.0.0.1:8000`

### Authentication

| Endpoint | Method | Auth | Description |
|---|---|---|---|
| `/api/token/` | POST | — | Username + password → `access` + `refresh` tokens |
| `/api/token/refresh/` | POST | — | Refresh token → a new token pair |

### Resources

| Endpoint | Methods | Auth | Description |
|---|---|---|---|
| `/api/authors/` | GET | public | List authors |
| | POST | required | Create an author |
| `/api/authors/<id>/` | GET | public | Retrieve |
| | PUT / PATCH / DELETE | required | Update / delete |
| `/api/books/` | GET | public | List books (filterable) |
| | POST | required | Create a book |
| `/api/books/<id>/` | GET | public | Retrieve |
| | PUT / PATCH / DELETE | required | Update / delete |
| `/api/reading-list/` | GET / POST | required | The **current user's** reading list only |
| `/api/reading-list/<id>/` | GET / PUT / PATCH / DELETE | owner only | Single item |

### Documentation

| Endpoint | Description |
|---|---|
| `/api/docs/` | Swagger UI — browse and try every endpoint |
| `/api/redoc/` | The same schema, ReDoc styling |
| `/api/schema/` | Raw OpenAPI 3 YAML |
| `/admin/` | Django admin (session login, separate from the API) |

### Filtering

`GET /api/books/` accepts optional query parameters, combinable:

| Parameter | Match | Example |
|---|---|---|
| `title` | case-insensitive contains | `?title=hobbit` |
| `author` | exact author id | `?author=1` |
| `year` | exact publication year | `?year=1937` |
| `category` | exact | `?category=fantasy` |

---

## Example usage

```bash
# Public read
curl http://localhost:8000/api/books/
curl "http://localhost:8000/api/books/?title=hobbit&year=1937"

# Obtain a token
curl -X POST http://localhost:8000/api/token/ \
  -H "Content-Type: application/json" \
  -d '{"username": "alice", "password": "secret"}'
# → {"access": "eyJhbGci...", "refresh": "eyJhbGci..."}

# Authenticated write
curl -X POST http://localhost:8000/api/books/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer eyJhbGci..." \
  -d '{"title": "Dune", "year_published": 1965, "author": 1}'

# Private, per-user resource
curl http://localhost:8000/api/reading-list/ \
  -H "Authorization: Bearer eyJhbGci..."
```

---

## Data model

```
Author ──1:N──> Book <──N:1── User (added_by, SET_NULL)
                  │
                  └──1:N──> ReadingListItem ──N:1──> User
                            unique_together (user, book)
```

| Model | Fields |
|---|---|
| `Author` | `name`, `birth_year`, `country` |
| `Book` | `title`, `year_published`, `category`, → `author`, → `added_by` |
| `ReadingListItem` | → `user`, → `book`, `notes`, `priority`, `added_at` |

`Book.added_by` uses `on_delete=SET_NULL` so deleting a user does not delete
their books. `ReadingListItem` uses `CASCADE` — a deleted user's private list
should go with them — plus a `unique_together` constraint so the same book
cannot be saved twice, enforced at the database level rather than in Python.

---

## Design notes

### JWT rather than sessions

The API is consumed cross-origin by a JavaScript frontend, where cookie-based
sessions are awkward. JWT is stateless: the signature is verified in memory, so
an invalid token is rejected with **zero database queries**.

The trade-off is that a token cannot be revoked before it expires — which is why
access tokens live 15 minutes, bounding the damage window.

Access tokens carry `username`, `email` and `is_staff` as custom claims
(`CustomTokenObtainPairSerializer`), so the frontend can render the current user
without an extra request.

Refresh tokens rotate on every use and the previous one is blacklisted, so a
stolen refresh token can be used at most once before it is invalidated.

### Two layers of authorization

Model-level permissions answer *"may this user create books?"*. They cannot
answer *"may this user edit **this** book?"*, so ownership is enforced
separately:

- **`get_queryset()`** filters lists to the requesting user — without it, other
  users' rows appear in `GET /api/reading-list/`.
- **`IsOwner.has_object_permission()`** blocks fetching a single row by id —
  DRF does not run object permissions on list actions.

Both halves are required. Either one alone leaks data.

### Ownership is never taken from the request body

`perform_create()` sets the owner from the authenticated request:

```python
def perform_create(self, serializer):
    serializer.save(user=self.request.user)
```

`user` is not a serializer field at all, so a client sending `"user": 999` is
ignored rather than trusted. Covered by a test.

### Validation at two levels

Serializers mirror Django's form validation:

- `validate_year_published()` — single field, range check
- `validate()` — cross-field, rejects a book published before its author's birth

---

## Testing

```bash
python manage.py test
```

13 tests covering authentication, permissions, filtering, validation and
row-level isolation between users. Four are regression tests for bugs found
during a code audit:

| Bug | Symptom | Test |
|---|---|---|
| Filter used `year` instead of `year_published` | `FieldError` 500 on `?year=` | `test_year_filter` |
| Duplicate `api/token/` route shadowed the custom view | Custom claims silently missing | `test_token_carries_custom_claims` |
| `ReadingListViewSet` never registered on the router | Endpoint 404'd | `test_endpoint_exists` |
| `added_by` writable by the client | Users could claim authorship | `test_added_by_is_set_from_the_request` |

---

## Project structure

```
Bookshop/
├── manage.py
├── requirements.txt
├── myproject/
│   ├── settings.py        # DRF, SIMPLE_JWT, CORS, spectacular config
│   └── urls.py            # root URLconf: admin, JWT, docs
└── pages/
    ├── models.py          # Author, Book, ReadingListItem
    ├── serializers.py     # validation + custom JWT claims
    ├── views.py           # ViewSets, filtering, perform_create
    ├── permissions.py     # IsOwner
    ├── urls.py            # DRF router
    ├── forms.py           # ModelForm (server-rendered work, weeks 1-3)
    ├── tests.py
    ├── migrations/
    └── templates/         # retained from the server-rendered phase; unused
```

Every module opens with a comment explaining its role and the reasoning behind
its non-obvious decisions.

---

## Known limitations

- **SQLite** — fine for development, would move to PostgreSQL for deployment.
- **No pagination** — `GET /api/books/` returns every row.
- **N+1 queries** — `author_name` triggers one query per book; `select_related`
  would fix it.
- **`token_blacklist_outstandingtoken` grows unbounded** — needs
  `manage.py flushexpiredtokens` on a schedule.
- **Not deployment-ready** — `DEBUG=True` and an empty `ALLOWED_HOSTS`.
  (`SECRET_KEY` is already read from the environment.)
- **`/api/docs/` is public**, appropriate for development only.

---

## Roadmap

- [ ] React frontend (Vite) consuming this API
- [ ] Pagination and `select_related` on the book list
- [ ] PostgreSQL and environment-based settings
- [ ] Deployment
- [ ] CI running the test suite on every push
