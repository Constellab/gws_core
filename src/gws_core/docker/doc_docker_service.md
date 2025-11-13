# Docker Service Developer Guide

## Overview

The `DockerService` provides a centralized way to deploy and manage custom Docker Compose configurations within the GWS Lab environment. This service allows developers to register, start, monitor, and manage multi-container Docker applications as part of their bricks.

This can be useful to deploy database services, web applications, or any other multi-container setups required by your brick.

## Key Concepts

### Brick Name and Unique Name
Every Docker Compose deployment is identified by two components:
- **brick_name**: The name of your brick (e.g., `gws_ai_toolkit`)
- **unique_name**: A unique identifier for your compose within the brick (e.g., `ragflow`)

These combine to create a fully qualified identifier: `{brick_name}/{unique_name}`

### Auto-start Behavior
The `auto_start` parameter (default: `False`) determines whether your Docker Compose should automatically start when the lab starts. Set to `True` for services that should always be available.

### Environment Variables
Environment variables can be passed to your Docker Compose configuration using the `env` parameter, which is a dictionary of key-value pairs.

## Service Methods

### 1. Register and Start Compose from String Content

```python
from gws_core import DockerService

docker_service = DockerService()
docker_service.register_and_start_compose(
    brick_name="my_brick",
    unique_name="my_service",
    compose_yaml_content="""
services:
  my_app:
    image: nginx:latest
    ports:
      - "8080:80"
networks:
  my_brick-my_service:
    driver: bridge
""",
    description="My custom NGINX service",
    env={"MY_VAR": "my_value"},
    auto_start=False
)
```

**Use case**: Quick deployments where the docker-compose content is simple or generated dynamically.

### 2. Register and Start Compose from Folder

```python
import os
from gws_core import DockerService

docker_service = DockerService()

# Get path to folder containing docker-compose.yml and related files
docker_folder_path = os.path.join(os.path.dirname(__file__), "docker")

docker_service.register_sub_compose_from_folder(
    brick_name="my_brick",
    unique_name="my_service",
    folder_path=docker_folder_path,
    description="My complex service with multiple containers",
    env={"PASSWORD": "secure_password"},
    auto_start=True
)
```

**Use case**: Complex deployments with multiple configuration files, initialization scripts, or custom configurations.

### 3. Register SQL Database Compose

```python
from gws_core import DockerService

docker_service = DockerService()

response = docker_service.register_sqldb_compose(
    brick_name="my_brick",
    unique_name="postgres_db",
    database_name="my_database",
    description="PostgreSQL database for my application",
    env={"POSTGRES_VERSION": "15"},
    auto_start=True
)

# Credentials are automatically created and returned
credentials = response.credentials
print(f"Database URL: {credentials.url}")
print(f"Username: {credentials.username}")
print(f"Password: {credentials.password}")
```

**Use case**: Quick SQL database deployment with automatic credential management.

### 4. Monitoring and Status Checking

```python
from gws_core import DockerService, DockerComposeStatus

docker_service = DockerService()

# Check current status
status = docker_service.get_compose_status(
    brick_name="my_brick",
    unique_name="my_service"
)

print(f"Status: {status.composeStatus.status.value}")
if status.composeStatus.info:
    print(f"Info: {status.composeStatus.info}")

# Wait for compose to be ready
ready_status = docker_service.wait_for_compose_status(
    brick_name="my_brick",
    unique_name="my_service",
    interval_seconds=5.0,
    max_attempts=20,
    message_dispatcher=self.message_dispatcher  # In a Task context
)

if ready_status.composeStatus.status == DockerComposeStatus.UP:
    print("Service is up and running!")
```

### 5. Stopping and Unregistering

```python
from gws_core import DockerService

docker_service = DockerService()

# Stop and unregister the compose
status = docker_service.unregister_compose(
    brick_name="my_brick",
    unique_name="my_service"
)

print(f"Final status: {status.composeStatus.status.value}")
```

### 6. List All Composes

```python
from gws_core import DockerService

docker_service = DockerService()

# Get all registered composes
all_composes = docker_service.get_all_composes()

for compose in all_composes.composes:
    print(f"{compose.brickName}/{compose.uniqueName}")
    print(f"  Path: {compose.composeFilePath}")
```


## Template Variables and X-GWS-Config

The Lab Manager uses a template system that automatically processes Docker Compose files and replaces custom variables before deployment. This section explains the available template variables and the `x-gws-config` metadata for advanced service configuration.

### Overview

When you register a Docker Compose configuration, the Lab Manager:
1. Processes custom template variables (e.g., `${LAB_NETWORK}`, `${CONTAINER_PREFIX}`)
2. Handles `x-gws-config` metadata for automatic routing and port mapping
3. Generates the final Docker Compose configuration
4. Deploys the processed configuration

### Template Variables Reference

#### 1. `${CONTAINER_PREFIX}`

A unique prefix for your containers, automatically generated from `brick_name`, `unique_name`, and environment. This is recommended to avoid naming collisions.

**Pattern:**
- Production/Dev: `{brick_name}-{unique_name}-{env}`
- All/None: `{brick_name}-{unique_name}`

**Example:**
```yaml
# Template (brick_name="gws_ai_toolkit", unique_name="ragflow", env="prod")
services:
  web:
    container_name: ${CONTAINER_PREFIX}-web
  api:
    container_name: ${CONTAINER_PREFIX}-api

# Result
services:
  web:
    container_name: gws_ai_toolkit-ragflow-prod-web
  api:
    container_name: gws_ai_toolkit-ragflow-prod-api
```

**Network Usage:**
```yaml
networks:
  ${CONTAINER_PREFIX}:
    driver: bridge
```

#### 2. `${LAB_NETWORK}`

Automatically replaced with the lab's Docker network name based on the environment setting.

**Replacement Rules:**

| Environment | Result |
|-------------|--------|
| `prod` | `gencovery-network-prod` |
| `dev` | `gencovery-network-dev` |

**Example:**
```yaml
# Template (env: prod)
services:
  web:
    networks:
      - ${CONTAINER_PREFIX}
      - ${LAB_NETWORK}

# Result
services:
  web:
    networks:
      - gws_ai_toolkit-ragflow-prod
      - gencovery-network-prod

networks:
  gencovery-network-prod:
    external: true
```

**Purpose:** Connect your services to the lab's network for:
- Isolate the production and development environments
- Internal communication with other lab services

#### 3. `${LAB_VOLUME_HOST}`

Replaced with either a host path (bind mount) or named volume, depending on the deployment mode.

**IMPORTANT:** You **MUST** use `${LAB_VOLUME_HOST}` for all persistent data volumes. This ensures:
- Data is stored in the correct location managed by the lab
- Your data is included in the lab's automatic backup system
- Data persistence across container restarts and updates
- Proper isolation between different environments (prod/dev)

**Bind Mount Mode** (Production/Remote):
```yaml
# Template
services:
  web:
    volumes:
      - ${LAB_VOLUME_HOST}/data:/app/data
      - ${LAB_VOLUME_HOST}/config:/etc/config

# Result (hostVolume: '/mnt/lab-storage', isNamed: false)
services:
  web:
    volumes:
      - /mnt/lab-storage/data:/app/data
      - /mnt/lab-storage/config:/etc/config
```

**Named Volume Mode** (Localhost/Development):
```yaml
# Template
services:
  web:
    volumes:
      - ${LAB_VOLUME_HOST}/data:/app/data
      - ${LAB_VOLUME_HOST}/logs:/var/log

# Result (hostVolume: 'myapp-volume', isNamed: true)
services:
  web:
    volumes:
      - myapp-volume-data:/app/data
      - myapp-volume-logs:/var/log

volumes:
  myapp-volume-data:
    name: myapp-volume-data
  myapp-volume-logs:
    name: myapp-volume-logs
```

**Exception: Relative Paths for Configuration Files**

You can skip `${LAB_VOLUME_HOST}` when using **relative paths** to mount static configuration files from your Docker folder. These are typically read-only configuration files that are part of your Docker Compose deployment.

```yaml
services:
  ragflow:
    image: infiniflow/ragflow:v0.21.1-slim
    volumes:
      # Configuration files (relative paths) - OK without LAB_VOLUME_HOST
      - ./nginx/ragflow.conf:/etc/nginx/conf.d/ragflow.conf
      - ./nginx/proxy.conf:/etc/nginx/proxy.conf
      - ./entrypoint.sh:/ragflow/entrypoint.sh

      # Persistent data (MUST use LAB_VOLUME_HOST for backup)
      - ${LAB_VOLUME_HOST}/ragflow-logs:/ragflow/logs
      - ${LAB_VOLUME_HOST}/history_data:/ragflow/history_data
```

**When to use relative paths:**
- Static configuration files (nginx configs, entrypoints, init scripts)
- Read-only files that are part of your compose deployment
- Files that don't change during runtime

**When to use `${LAB_VOLUME_HOST}`:**
- Application data that changes during runtime
- Database files
- User-generated content
- Logs and persistent state
- Any data that needs to be backed up

**Warning:** Do NOT use custom absolute paths or Docker named volumes directly for persistent data. Always use `${LAB_VOLUME_HOST}` to ensure backup coverage.

#### 4. `${LAB_DOMAIN}`

Replaced with the lab's domain name for constructing URLs.

**Example:**
```yaml
# Template
services:
  api:
    environment:
      - API_URL=https://api.${LAB_DOMAIN}
      - WEB_URL=https://app.${LAB_DOMAIN}
      - CALLBACK_URL=https://auth.${LAB_DOMAIN}/callback

# Result (labDomain: 'lab.example.com')
services:
  api:
    environment:
      - API_URL=https://api.lab.example.com
      - WEB_URL=https://app.lab.example.com
      - CALLBACK_URL=https://auth.lab.example.com/callback
```

### HTTP Configuration with X-GWS-Config

The `x-gws-config` metadata enables automatic HTTPS routing via Traefik and port management for exposing web interfaces. This is a service-level configuration.

#### Basic HTTPS Configuration

```yaml
services:
  web:
    image: nginx:latest
    container_name: ${CONTAINER_PREFIX}-web
    x-gws-config:
      - https:
          name: web-service           # Service identifier for Traefik router
          subDomain: myapp             # Subdomain 
          internalPort: 80             # Container port to route traffic to
          localhostHostPort: 8080      # Optional: port for localhost mode
```

#### Configuration Properties

| Property | Required | Type | Description |
|----------|----------|------|-------------|
| `name` | Yes | string | Unique identifier for the Traefik router |
| `subDomain` | Yes | string | Subdomain for routing (e.g., `api`, `admin`, `app`) |
| `internalPort` | Yes | number | Container port to route traffic to |
| `localhostHostPort` | No | number | Host port for localhost mode (defaults to `internalPort`) |

#### How X-GWS-Config Works

**Production/Dev Mode**:

For remote environments (not desktop data lab), the Lab Manager configures Traefik for HTTPS routing:

```yaml
# Template
services:
  api:
    image: my-api:latest
    x-gws-config:
      - https:
          name: api-service
          subDomain: api
          internalPort: 3000

# Processed Result (LAB_DOMAIN: 'lab.example.com')
services:
  api:
    image: my-api:latest
    labels:
      - traefik.enable=true
      - traefik.http.routers.api-service.rule=Host(`api.lab.example.com`)
      - traefik.http.routers.api-service.entrypoints=websecure
      - traefik.http.routers.api-service.tls.certresolver=letsencrypt
      - traefik.http.services.api-service.loadbalancer.server.port=3000
      - traefik.docker.network=gencovery-network-prod
```

The internal port `3000` of the container is exposed via Traefik at `https://api.lab.example.com` using HTTPS.

**Localhost Mode** :

In localhost mode (like a desktop data lab), instead of Traefik labels, port mappings are added:

```yaml
# Template
services:
  api:
    image: my-api:latest
    x-gws-config:
      - https:
          name: api-service
          subDomain: api
          internalPort: 3000
          localhostHostPort: 3001

# Processed Result (LAB_DOMAIN: 'localhost')
services:
  api:
    image: my-api:latest
    ports:
      - '3001:3000'
```

If `localhostHostPort` is not specified, it defaults to `internalPort`:

```yaml
# Without localhostHostPort
x-gws-config:
  - https:
      name: web
      subDomain: app
      internalPort: 8080

# Result in localhost mode
ports:
  - '8080:8080'
```

#### Multiple Service Exposure

You can expose multiple services or ports from the same compose:

```yaml
services:
  app:
    image: myapp:latest
    container_name: ${CONTAINER_PREFIX}-app
    x-gws-config:
      - https:
          name: app-web
          subDomain: app
          internalPort: 80
      - https:
          name: app-api
          subDomain: api
          internalPort: 3000
          localhostHostPort: 3001

  admin:
    image: myapp-admin:latest
    container_name: ${CONTAINER_PREFIX}-admin
    x-gws-config:
      - https:
          name: admin-panel
          subDomain: admin
          internalPort: 8080
```

**Result:** Your services will be available at:
- `https://app.{LAB_DOMAIN}` (port 80 of app container)
- `https://api.{LAB_DOMAIN}` (port 3000 of app container)
- `https://admin.{LAB_DOMAIN}` (port 8080 of admin container)

#### Real-World Example from RagFlow

```yaml
services:
  ragflow:
    depends_on:
      mysql:
        condition: service_healthy
    image: infiniflow/ragflow:v0.21.1-slim
    container_name: ${CONTAINER_PREFIX}-server
    volumes:
      - ./nginx/ragflow.conf:/etc/nginx/conf.d/ragflow.conf
      - ${LAB_VOLUME_HOST}/ragflow-logs:/ragflow/logs
    environment:
      - MYSQL_PASSWORD=${PASSWORD}
    networks:
      - ${CONTAINER_PREFIX}
      - ${LAB_NETWORK}
    extra_hosts:
      - "host.docker.internal:host-gateway"
    x-gws-config:
      - https:
          name: ragflow-web
          internalPort: 80
          subDomain: ragflow
```

This configuration:
- Exposes RagFlow's web interface on port 80
- Makes it accessible at `https://ragflow.{LAB_DOMAIN}` in production
- Opens port 80 for localhost development
- Automatically configures Traefik for HTTPS with Let's Encrypt certificates

### Complete Template Example

Here's a comprehensive example combining all template variables:

```yaml
services:
  web:
    image: nginx:alpine
    container_name: ${CONTAINER_PREFIX}-web
    volumes:
      - ${LAB_VOLUME_HOST}/web_data:/usr/share/nginx/html
      - ${LAB_VOLUME_HOST}/web_logs:/var/log/nginx
    environment:
      - BACKEND_URL=https://api.${LAB_DOMAIN}
    networks:
      - ${CONTAINER_PREFIX}
      - ${LAB_NETWORK}
    x-gws-config:
      - https:
          name: frontend
          subDomain: app
          internalPort: 80
          localhostHostPort: 8080

  api:
    image: node:18-alpine
    container_name: ${CONTAINER_PREFIX}-api
    volumes:
      - ${LAB_VOLUME_HOST}/api_data:/app/data
    environment:
      - DATABASE_URL=postgresql://${DB_USER}:${DB_PASSWORD}@${CONTAINER_PREFIX}-db:5432/mydb
      - APP_URL=https://app.${LAB_DOMAIN}
    networks:
      - ${CONTAINER_PREFIX}
      - ${LAB_NETWORK}
    depends_on:
      - db
    x-gws-config:
      - https:
          name: backend-api
          subDomain: api
          internalPort: 3000
          localhostHostPort: 3001

  db:
    image: postgres:15
    container_name: ${CONTAINER_PREFIX}-db
    volumes:
      - ${LAB_VOLUME_HOST}/postgres_data:/var/lib/postgresql/data
    environment:
      - POSTGRES_USER=${DB_USER}
      - POSTGRES_PASSWORD=${DB_PASSWORD}
      - POSTGRES_DB=mydb
    networks:
      - ${CONTAINER_PREFIX}
    healthcheck:
      test: ["CMD", "pg_isready", "-U", "${DB_USER}"]
      interval: 5s
      timeout: 5s
      retries: 5

networks:
  ${CONTAINER_PREFIX}:
    driver: bridge
```

### Usage in Python Code

When registering a compose, pass custom environment variables via the `env` parameter:

```python
from gws_core import DockerService

docker_service = DockerService()

# Get credentials
credentials = docker_service.get_or_create_basic_credentials(
    brick_name="my_brick",
    unique_name="my_app"
)

# Register compose with custom environment variables
docker_service.register_sub_compose_from_folder(
    brick_name="my_brick",
    unique_name="my_app",
    folder_path="/path/to/docker/folder",
    description="My application stack",
    env={
        "PASSWORD": credentials.password,
        "DB_USER": credentials.username,
        "DB_PASSWORD": credentials.password,
        "API_KEY": "your-api-key",
        "CUSTOM_VAR": "custom-value"
    },
    auto_start=True
)
```

### Best Practices for Templates

1. **Always use `${LAB_VOLUME_HOST}` for persistent data:**
   ```yaml
   volumes:
     - ${LAB_VOLUME_HOST}/app_data:/var/lib/app
   ```

2. **Connect to both networks for lab integration:**
   ```yaml
   networks:
     - ${CONTAINER_PREFIX}      # Internal network
     - ${LAB_NETWORK}            # Lab network
   ```

3. **Use `${CONTAINER_PREFIX}` for unique container names:**
   ```yaml
   container_name: ${CONTAINER_PREFIX}-service-name
   ```

4. **Leverage `x-gws-config` for web interfaces:**
   ```yaml
   x-gws-config:
     - https:
         name: service-web
         subDomain: myservice
         internalPort: 8080
   ```

5. **Pass sensitive data via env parameters, not hardcoded:**
   ```yaml
   environment:
     - DB_PASSWORD=${PASSWORD}  # Passed via env parameter
   ```

6. **Use `${LAB_DOMAIN}` for callback URLs and service discovery:**
   ```yaml
   environment:
     - AUTH_CALLBACK=https://auth.${LAB_DOMAIN}/callback
   ```

## Credentials Management

The Docker Service integrates with the GWS credentials system for secure credential management.

### Automatic Credential Generation

```python
from gws_core import DockerService

docker_service = DockerService()

# Get or create credentials (auto-generates password if not exists)
credentials = docker_service.get_or_create_basic_credentials(
    brick_name="my_brick",
    unique_name="my_service",
    username="custom_user",  # Optional, defaults to "{brick_name}_{unique_name}"
    password=None,  # Optional, auto-generated if None
    url="http://localhost:5432"  # Optional
)

print(f"Username: {credentials.username}")
print(f"Password: {credentials.password}")
print(f"URL: {credentials.url}")
```

### Credential Naming Convention

Credentials are automatically named using the pattern: `docker_{brick_name}_{unique_name}`

### Retrieving Existing Credentials

```python
from gws_core import DockerService

docker_service = DockerService()

credentials = docker_service.get_basic_credentials(
    brick_name="my_brick",
    unique_name="my_service"
)

if credentials:
    print("Credentials found!")
else:
    print("No credentials exist for this compose")
```


## Real-World Example: RagFlow Deployment

This example demonstrates deploying RagFlow, a complete RAG (Retrieval-Augmented Generation) system with multiple services.

### Directory Structure

```
my_brick/
└── rag/
    └── ragflow/
        ├── ragflow_start_docker_compose.py
        └── docker/
            ├── docker-compose.yml
            ├── init.sql
            ├── entrypoint.sh
            └── nginx/
                ├── ragflow.conf
                ├── proxy.conf
                └── nginx.conf
```

### Docker Compose Configuration


```yaml
services:
  es01:
    container_name: ${CONTAINER_PREFIX}-es-01
    image: elasticsearch:8.11.3
    volumes:
      - ${LAB_VOLUME_HOST}/esdata01:/usr/share/elasticsearch/data
    environment:
      - node.name=es01
      - ELASTIC_PASSWORD=${PASSWORD}
      - bootstrap.memory_lock=false
      - discovery.type=single-node
      - xpack.security.enabled=true
      - xpack.security.http.ssl.enabled=false
    mem_limit: 8073741824
    healthcheck:
      test: ["CMD-SHELL", "curl http://localhost:9200"]
      interval: 10s
      timeout: 10s
      retries: 120
    networks:
      - ${CONTAINER_PREFIX}

  mysql:
    image: mysql:8.0.39
    container_name: ${CONTAINER_PREFIX}-mysql
    environment:
      - MYSQL_ROOT_PASSWORD=${PASSWORD}
    command:
      --max_connections=1000
      --character-set-server=utf8mb4
      --collation-server=utf8mb4_unicode_ci
      --default-authentication-plugin=mysql_native_password
    volumes:
      - ${LAB_VOLUME_HOST}/mysql_data:/var/lib/mysql
      - ./init.sql:/data/application/init.sql
    networks:
      - ${CONTAINER_PREFIX}
    healthcheck:
      test: ["CMD", "mysqladmin", "ping", "-uroot", "-p${PASSWORD}"]
      interval: 10s
      timeout: 10s
      retries: 3
    restart: on-failure

  ragflow:
    depends_on:
      mysql:
        condition: service_healthy
    image: infiniflow/ragflow:v0.21.1-slim
    container_name: ${CONTAINER_PREFIX}-server
    volumes:
      - ./nginx/ragflow.conf:/etc/nginx/conf.d/ragflow.conf
      - ${LAB_VOLUME_HOST}/ragflow-logs:/ragflow/logs
    environment:
      - MYSQL_PASSWORD=${PASSWORD}
      - REDIS_PASSWORD=${PASSWORD}
    networks:
      - ${CONTAINER_PREFIX}
      - ${LAB_NETWORK}
    extra_hosts:
      - "host.docker.internal:host-gateway"
    x-gws-config:
      - https:
          name: ragflow-web
          internalPort: 80
          subDomain: ragflow

networks:
  ${CONTAINER_PREFIX}:
    driver: bridge
```

### Task Implementation

This task registers and starts the RagFlow Docker Compose services.

```python
import os
from typing import cast
from gws_core import (
    ConfigParams, ConfigSpecs, CredentialsDataBasic,
    CredentialsService, DockerComposeStatus, DockerService,
    InputSpecs, OutputSpecs, Task, TaskInputs, TaskOutputs,
    TypingStyle, task_decorator
)

@task_decorator(
    "RagflowStartDockerCompose",
    human_name="Start RagFlow Docker Compose",
    short_description="Start the RagFlow docker compose services",
    style=TypingStyle.community_image("ragflow", "#4A90E2")
)
class RagflowStartDockerCompose(Task):
    """Start the RagFlow docker compose services."""

    input_specs = InputSpecs()
    output_specs = OutputSpecs()
    config_specs = ConfigSpecs()

    def run(self, params: ConfigParams, inputs: TaskInputs) -> TaskOutputs:
        # Get the path to the docker folder
        docker_folder_path = os.path.join(os.path.dirname(__file__), "docker")

        self.log_info_message("Retrieving credentials...")
        credentials = CredentialsService.get_or_create_basic_credential(
            name="gws_ai_toolkit-ragflow-docker",
            username='user',
            description="Basic credentials for Docker compose gws_ai_toolkit/ragflow"
        )

        credentials_data = cast(CredentialsDataBasic, credentials.get_data_object())

        self.log_info_message("Registering RagFlow docker compose services...")

        # Register the docker compose with the Docker service
        docker_service = DockerService()
        docker_service.register_sub_compose_from_folder(
            brick_name="gws_ai_toolkit",
            unique_name="ragflow",
            folder_path=docker_folder_path,
            description="RagFlow docker compose services",
            env={
                "PASSWORD": credentials_data.password
            }
        )

        self.log_info_message("Docker Compose started, waiting for ready status...")

        # Wait for the compose to be ready
        response = docker_service.wait_for_compose_status(
            brick_name="gws_ai_toolkit",
            unique_name="ragflow",
            interval_seconds=10,
            max_attempts=20,
            message_dispatcher=self.message_dispatcher
        )

        if response.composeStatus.status != DockerComposeStatus.UP:
            text = f"Docker Compose did not start successfully, status: {response.composeStatus.status.value}."
            if response.composeStatus.info:
                text += f" Info: {response.composeStatus.info}."
            raise Exception(text)

        self.log_success_message("RagFlow docker compose services started successfully!")

        return {}
```



## Error Handling

```python
from gws_core import DockerService, BaseHTTPException

docker_service = DockerService()

try:
    docker_service.register_and_start_compose(
        brick_name="my_brick",
        unique_name="my_service",
        compose_yaml_content=compose_content,
        description="My service"
    )
except BaseHTTPException as e:
    print(f"Failed to start compose: {e.detail}")
except Exception as e:
    print(f"Unexpected error: {str(e)}")
```

## Troubleshooting

### Check Compose Status

```python
status = docker_service.get_compose_status(
    brick_name="my_brick",
    unique_name="my_service"
)

print(f"Compose Status: {status.composeStatus.status.value}")
if status.composeStatus.info:
    print(f"Additional Info: {status.composeStatus.info}")

if status.subComposeProcess:
    print(f"Process Type: {status.subComposeProcess.processType.value}")
    print(f"Process Status: {status.subComposeProcess.status.value}")
    print(f"Message: {status.subComposeProcess.message}")
```

### List All Running Composes

```python
all_composes = docker_service.get_all_composes()
for compose in all_composes.composes:
    print(f"Brick: {compose.brickName}, Name: {compose.uniqueName}")
    print(f"Path: {compose.composeFilePath}")
```

### Force Unregister

If a compose is stuck, you can force unregister it:

```python
docker_service.unregister_compose(
    brick_name="my_brick",
    unique_name="my_service"
)
```

## API Reference Summary

| Method | Description | Returns |
|--------|-------------|---------|
| `register_and_start_compose()` | Register compose from string content | None |
| `register_sub_compose_from_folder()` | Register compose from folder | None |
| `register_sqldb_compose()` | Register SQL database with auto-credentials | `RegisterSQLDBComposeResponseDTO` |
| `unregister_compose()` | Stop and unregister compose | `SubComposeStatusDTO` |
| `get_compose_status()` | Get current compose status | `SubComposeStatusDTO` |
| `wait_for_compose_status()` | Wait for compose to stabilize | `SubComposeStatusDTO` |
| `get_all_composes()` | List all registered composes | `SubComposeListDTO` |
| `get_or_create_basic_credentials()` | Get/create credentials | `CredentialsDataBasic` |
| `get_basic_credentials()` | Get existing credentials | `Optional[Credentials]` |

## Additional Resources

- Docker Compose Documentation: https://docs.docker.com/compose/
- Docker Compose File Reference: https://docs.docker.com/compose/compose-file/
- GWS Core Credentials Service: [credentials_service.py](bricks/gws_core/src/gws_core/credentials/credentials_service.py)
- Docker Service Implementation: [docker_service.py](bricks/gws_core/src/gws_core/docker/docker_service.py)
