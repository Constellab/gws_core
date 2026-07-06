import re
from abc import abstractmethod

from gws_core.apps import app_gateway_constants


class AppNginxServiceInfo:
    """Information about a registered nginx service"""

    service_id: str
    source_port: int
    # A single host name or a list of host names answered by this server block. Listing
    # several names lets a custom-subdomain host alias resolve to the same backend as the
    # canonical id-based host.
    server_name: str | list[str]

    def __init__(self, service_id: str, source_port: int, server_name: str | list[str]):
        self.service_id = service_id
        self.source_port = source_port
        self.server_name = server_name

    def _render_server_names(self) -> str:
        """Render the server_name(s) for the nginx 'server_name ...;' directive."""
        if isinstance(self.server_name, str):
            return self.server_name
        return " ".join(self.server_name)

    @abstractmethod
    def get_nginx_service_config(self) -> str:
        """Generate nginx configuration block for this service"""


class AppNginxRedirectServiceInfo(AppNginxServiceInfo):
    """Service to redirect requests to a backend app or dev frontend app"""

    destination_port: int
    use_localhost_host_header: bool
    allowed_origins: list[str]
    # Full URL of the core-api app-host login endpoint (…/core-api/apps/{app_id}/nginx-login).
    # When set, a `location = /gws-login` block proxies to it so the code→JWT exchange + Set-Cookie
    # happens at the app host. None disables the login location (e.g. reflex front static server).
    gws_login_url: str | None

    def __init__(
        self,
        service_id: str,
        source_port: int,
        server_name: str | list[str],
        destination_port: int,
        use_localhost_host_header: bool = False,
        allowed_origin: str | None = None,
        allowed_origins: list[str] | None = None,
        gws_login_url: str | None = None,
    ):
        super().__init__(service_id, source_port, server_name)
        self.destination_port = destination_port
        self.use_localhost_host_header = use_localhost_host_header
        self.gws_login_url = gws_login_url
        # Accept either a single origin (back-compat) or an explicit list. Both feed the same
        # allow-list; when more than one origin is allowed the request origin is echoed back
        # (Access-Control-Allow-Credentials forbids the '*' wildcard).
        origins = list(allowed_origins) if allowed_origins else []
        if allowed_origin:
            origins.append(allowed_origin)
        # de-duplicate while preserving order
        self.allowed_origins = list(dict.fromkeys(origins))

    def _build_login_location(self) -> str:
        """Build the `location = /gws-login` block that proxies to the core-api login endpoint.

        The core-api endpoint exchanges the one-time gws_code for a JWT and responds with a
        302-to-/ carrying a Set-Cookie; nginx forwards that response to the browser. Empty when
        no login URL is configured (the login is only needed on the app-serving block).
        """
        if not self.gws_login_url:
            return ""

        login_path = app_gateway_constants.GWS_LOGIN_PATH

        # Use a literal host (127.0.0.1) so nginx resolves the upstream at startup. A hostname
        # like "localhost" — or any variable in proxy_pass — would force runtime resolution and
        # require a `resolver` directive we don't configure (else: "no resolver defined").
        login_url = self._to_loopback_upstream(self.gws_login_url)

        return f"""
    location = /{login_path} {{
        # Exchange the one-time gws_code for a JWT at the core-api login endpoint, which responds
        # with a 302-to-/ + Set-Cookie (host session JWT). nginx relays that response to the
        # browser. proxy_pass carries a rewrite URI (no variables), so nginx appends the original
        # query string (?gws_code=…) automatically.
        proxy_pass {login_url};
        proxy_set_header Host $host;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_pass_request_body off;
    }}
"""

    @staticmethod
    def _to_loopback_upstream(url: str) -> str:
        """Rewrite a ``localhost`` upstream host to ``127.0.0.1``.

        The login endpoint runs in the same box as nginx (same loopback as the app process).
        Using the literal IP avoids nginx's DNS resolution path entirely, which otherwise fails
        with "no resolver defined to resolve localhost".
        """
        return url.replace("http://localhost", "http://127.0.0.1", 1)

    def _build_cors_config(self) -> str:
        """Build the CORS header block, echoing the request origin when it is allowed.

        nginx can only emit a single Access-Control-Allow-Origin value, and the '*' wildcard is
        invalid together with Access-Control-Allow-Credentials. To allow several front origins
        (e.g. the id-based host and a custom-subdomain alias), we match $http_origin against the
        allow-list and echo it back via a per-request variable.
        """
        if not self.allowed_origins:
            return ""

        # Build a regex alternation of the allowed origins (escape regex metachars in hosts).
        escaped = [re.escape(origin) for origin in self.allowed_origins]
        origin_regex = "|".join(escaped)

        return f"""# CORS headers (echo the request origin when it is in the allow-list)
        set $cors_origin "";
        if ($http_origin ~ '^({origin_regex})$') {{
            set $cors_origin $http_origin;
        }}
        add_header 'Access-Control-Allow-Origin' $cors_origin always;
        add_header 'Access-Control-Allow-Methods' '*' always;
        add_header 'Access-Control-Allow-Headers' '*' always;
        add_header 'Access-Control-Allow-Credentials' 'true' always;

        # Handle preflight OPTIONS requests
        if ($request_method = 'OPTIONS') {{
            add_header 'Access-Control-Allow-Origin' $cors_origin always;
            add_header 'Access-Control-Allow-Methods' '*' always;
            add_header 'Access-Control-Allow-Headers' '*' always;
            add_header 'Access-Control-Allow-Credentials' 'true' always;
            add_header 'Access-Control-Max-Age' 1728000;
            add_header 'Content-Type' 'text/plain; charset=utf-8';
            add_header 'Content-Length' 0;
            return 204;
        }}
"""

    def get_nginx_service_config(self) -> str:
        """Generate nginx configuration block for this service"""

        host_header = (
            f"localhost:{self.destination_port}" if self.use_localhost_host_header else "$host"
        )
        cors_config = self._build_cors_config()
        login_location = self._build_login_location()
        return f"""
server {{
    listen {self.source_port};
    server_name {self._render_server_names()};
{login_location}
    location / {{
        proxy_pass http://localhost:{self.destination_port};
        proxy_set_header Host {host_header};
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # WebSocket support (useful for applications like Streamlit)
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Origin "";
        proxy_buffering off;

        # Timeout settings
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 300s;

        {cors_config}
    }}
}}
"""


class AppNginxReflexFrontServerServiceInfo(AppNginxServiceInfo):
    """Service to serve a built reflex front app"""

    front_folder_path: str

    def __init__(
        self,
        service_id: str,
        source_port: int,
        server_name: str | list[str],
        front_folder_path: str,
    ):
        super().__init__(service_id, source_port, server_name)
        self.front_folder_path = front_folder_path

    def get_nginx_service_config(
        self,
    ) -> str:
        """Generate nginx configuration block for serving the front-end of this service"""
        return rf"""
server {{
        listen {self.source_port};
        server_name {self._render_server_names()};

        root {self.front_folder_path};
        index index.html;

        # Handle client-side routing
        location / {{
            try_files $uri $uri/ /index.html;
        }}

        # Serve static assets with caching
        location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg)$ {{
            expires 1y;
            add_header Cache-Control "public, immutable";
        }}

        # Security headers
        add_header Content-Security-Policy "frame-ancestors *;" always;
        add_header X-Content-Type-Options "nosniff" always;
        add_header X-XSS-Protection "1; mode=block" always;

        # Gzip compression
        gzip on;
        gzip_vary on;
        gzip_min_length 1024;
        gzip_types text/plain text/css text/xml text/javascript application/javascript application/xml+rss application/json;
    }}
"""
