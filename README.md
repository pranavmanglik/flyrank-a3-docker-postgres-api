# W3 A3 — Containerize the Task API and Postgres

This standalone FastAPI project preserves the A1 task routes and stores rows in Postgres. Docker Compose starts the API and database together. The Postgres volume keeps tasks after `docker compose down` and `docker compose up`.

## Run the whole stack

Requires Docker or a compatible Compose implementation:

```bash
cp .env.example .env
# Replace the password placeholder with a local development password.
docker compose up --build
```

The API is at <http://localhost:8000> and Swagger UI is at <http://localhost:8000/docs>. The database is available on localhost port 5432 for a local SQL client. Compose builds `DATABASE_URL` from the three settings in `.env`; `.env` is ignored by Git and the committed `.env.example` contains only placeholders.

Stop the stack with `docker compose down`, then start it again with `docker compose up`; the named `taskdata` volume preserves data. To remove the database data too, use `docker compose down -v`.

## Endpoints

`GET /`, `GET /health`, `GET /tasks`, `GET /tasks/{id}`, `POST /tasks`, `PUT /tasks/{id}`, and `DELETE /tasks/{id}`. The CRUD routes use parameterized SQL. `GET /health` also runs `SELECT 1` and reports database availability.

## Checkpoints

```bash
curl -i http://localhost:8000/tasks
curl -i -X POST http://localhost:8000/tasks -H 'Content-Type: application/json' -d '{"title":"Persistent task"}'
docker compose exec db psql -U postgres -d tasks -c 'SELECT * FROM tasks;'
```

Capture genuine `curl -i` output and a screenshot of the rows in Postgres after running the stack. Check the persistence by restarting Compose and querying the API and database again. Add those observed results before submitting.

## Assignment steps

Suggested commits: start Postgres with a volume and `.gitignore`; connect with `.env` and create/seed the table; read; implement full CRUD; compose the stack; document and publish. The optional AI rematch belongs in its own folder or branch. A public GitHub repo and honest stage commits remain submission steps.
