# My task API with Postgres and Docker Compose

For this assignment, I moved my task API data from an in-memory list to Postgres. I used Docker Compose to run the API and database together. The named `taskdata` volume lets me keep tasks when I stop and start the containers.

## What I built

- A FastAPI task API with create, read, update, and delete routes
- A Postgres database that stores the task records
- A health check that also checks whether Postgres can answer a query
- A Docker Compose setup for starting the API and database together
- A named database volume for keeping data between container restarts
- Parameterized SQL for the task queries

## How I run it

I need Docker Compose or a compatible implementation. From this project folder, I copy the example environment file, set a local password, and start the stack:

```bash
cp .env.example .env
```

I edit `.env` so it contains the three required settings, keeping the password local:

```env
POSTGRES_USER=postgres
POSTGRES_PASSWORD=my-local-password
POSTGRES_DB=tasks
```

Then I build and start the services:

```bash
docker compose up --build
```

The API is available at <http://localhost:8000>, and I can explore it at <http://localhost:8000/docs>. Compose uses the `.env` values to connect the API to Postgres. I keep `.env` out of Git and only commit the placeholder `.env.example`.

## Routes

| Method | Path | What I use it for |
| --- | --- | --- |
| GET | `/` | Check the API name and version |
| GET | `/health` | Check that the API and database are available |
| GET | `/tasks` | List tasks, optionally filtering by `done` or `search` |
| GET | `/tasks/{id}` | Get one task |
| POST | `/tasks` | Create a task |
| PUT | `/tasks/{id}` | Update a task's title, done value, or both |
| DELETE | `/tasks/{id}` | Delete a task |

## What I tested

I checked the health endpoint and got `200 OK` with `{"status":"ok","db":"ok"}`. I created “Postgres persistence test” and got `201 Created` with task ID 4. Listing tasks returned `200 OK` and included the new task alongside the three starter tasks.

I also checked the `tasks` table in Postgres with this query:

```bash
docker compose exec db psql -U postgres -d tasks \
  -c 'SELECT id, title, done FROM tasks;'
```

I ran that command from this project folder, where `compose.yaml` is located. After stopping the stack with `docker compose down` and starting it again with `docker compose up`, I checked the task list and confirmed the Postgres-backed task was still there.

## Test screenshot

I’ll add my terminal and Postgres test screenshot here.

<!-- Add the screenshot here as assets/a3-postgres-test.png when it is available in this project folder. -->

## What I learned

This project helped me connect an API to a separate database service and keep the data in a Docker volume. In my next project, I’ll build on these backend skills for a different kind of application.

