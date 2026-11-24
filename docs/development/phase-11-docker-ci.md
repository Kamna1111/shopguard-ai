# Phase 11: Docker and CI/CD

Phase 11 adds two helpers:

- Docker starts PostgreSQL, the FastAPI service, and the React website as a group.
- GitHub Actions automatically checks Python code, runs tests, builds the website, and checks the Docker Compose file when code is pushed or a pull request is opened.

## Start the local Docker shop

Install Docker Desktop and make sure it is running. In IntelliJ, open the project Terminal and run:

```sh
make docker-up
```

The first start builds images and can take a few minutes. When the services are ready, open `http://127.0.0.1:5173`. The API is also available at `http://127.0.0.1:8000/docs`.

Useful commands:

```sh
make docker-logs   # read messages from all services
make docker-build  # build images without starting them
make docker-down   # stop services; keep the database data
docker compose down -v  # stop services and delete the local database volume
```

The last command deletes local Docker database data. Use it only when you want to reset the practice database.

## What the main files do

- `docker-compose.yml` describes the database, API, and website and starts them in the right order.
- `apps/api/Dockerfile` packages the Python API and starts it after database migrations and demo-data setup.
- `apps/web/Dockerfile` builds the React site and serves it with Nginx.
- `apps/web/nginx.conf` sends website API calls to FastAPI.
- `.github/workflows/quality.yml` tells GitHub what automatic checks to run.
- `.dockerignore` keeps local environments, private settings, and generated files out of Docker build uploads.

## In very simple words

Docker is like a box that holds one part of the project with what it needs. Compose starts all the boxes together. CI is a helper robot on GitHub: when code changes, it checks the project before people merge the change.

The GitHub workflow uses an isolated PostgreSQL database for tests. It does not send code to a live shop or deploy the project.
