# Docker Setup for QtRVSim Web Evaluator

## Configuration

### Environment Variables

Copy `variables.env` to a new file (e.g., `.env.local`) and configure the following variables:

#### Database Configuration
- `POSTGRES_DB`, `DB_NAME`, `DB_DATABASE`: Database name (should be the same)
- `POSTGRES_USER`: PostgreSQL root username
- `POSTGRES_PASSWORD`: PostgreSQL root password
- `DB_HOST`: Database host (use `db` for docker-compose)
- `DB_PORT`: Database port (default: 5432)
- `DB_USER`: Application database user
- `DB_PASSWORD`: Application database password

#### Flask Application
- `SECRET_KEY`: Flask secret key for sessions

#### Mail Configuration
- `MAIL_SERVER`: SMTP server hostname
- `MAIL_PORT`: SMTP server port
- `MAIL_USE_TLS`: Use TLS (True/False)
- `MAIL_USE_SSL`: Use SSL (True/False)
- `MAIL_USERNAME`: SMTP username
- `MAIL_PASSWORD`: SMTP password
- `MAIL_DEFAULT_SENDER`: Default sender email address

#### Application URL
- `BASE_URL`: Base URL for email links and API documentation (e.g., `https://eval.comparch.edu.cvut.cz`)

#### File Directories (NEW)
- `TEMPLATES_DIR`: Path to code templates directory (default: `./.docker/S_templates`)
- `TASKS_DIR`: Path to task description files directory (default: `./.docker/tasks`)

### Setting up Template and Task Directories

Before running docker-compose, create the local directories and copy your files:

```bash
# From the project root directory
mkdir -p .docker/S_templates .docker/tasks

# Copy template files
cp web/S_templates/* .docker/S_templates/

# Copy task description files
cp web/tasks/* .docker/tasks/
```

These directories will be mounted as read-only volumes in the Docker containers.

### Running with Docker Compose

```bash
# Using the default variables.env file
docker-compose up -d

# Or using a custom env file
docker-compose --env-file .env.local up -d
```

### Directory Structure

The Docker setup mounts the following directories:
- `TEMPLATES_DIR` → `/app/S_templates` (in web container)
- `TASKS_DIR` → `/app/tasks` (in both web and evaluator containers)

This allows you to manage templates and tasks outside of the containers and update them without rebuilding Docker images.

### Notes

- The web container runs on port 8000
- The database container runs on port 5432
- Templates and tasks are mounted as read-only volumes
- Make sure to update your `.toml` task files to reference templates by their filename only (e.g., `template = "addition.S"` instead of `template = "S_templates/addition.S"`)
