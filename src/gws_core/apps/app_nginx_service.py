from abc import abstractmethod


class AppNginxServiceInfo:
    """Information about a registered nginx service"""

    service_id: str
    source_port: int
    server_name: str

    def __init__(self, service_id: str, source_port: int, server_name: str):
        self.service_id = service_id
        self.source_port = source_port
        self.server_name = server_name

    @abstractmethod
    def get_nginx_service_config(self) -> str:
        """Generate nginx configuration block for this service"""


class AppNginxRedirectServiceInfo(AppNginxServiceInfo):
    """Service to redirect requests to a backend app or dev frontend app"""

    destination_port: int
    use_localhost_host_header: bool

    def __init__(
        self,
        service_id: str,
        source_port: int,
        server_name: str,
        destination_port: int,
        use_localhost_host_header: bool = False,
    ):
        super().__init__(service_id, source_port, server_name)
        self.destination_port = destination_port
        self.use_localhost_host_header = use_localhost_host_header

    def get_nginx_service_config(self) -> str:
        """Generate nginx configuration block for this service"""

        host_header = (
            f"localhost:{self.destination_port}" if self.use_localhost_host_header else "$host"
        )
        return f"""
server {{
    listen {self.source_port};
    server_name {self.server_name};

    location / {{
        proxy_pass http://localhost:{self.destination_port};
        # Use localhost as new host to avoid error on frontend apps when
        # running in dev mode
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
    }}
}}
"""


class AppNginxReflexFrontServerServiceInfo(AppNginxServiceInfo):
    """Service to serve a built reflex front app"""

    front_folder_path: str

    def __init__(self, service_id: str, source_port: int, server_name: str, front_folder_path: str):
        super().__init__(service_id, source_port, server_name)
        self.front_folder_path = front_folder_path

    def get_nginx_service_config(
        self,
    ) -> str:
        """Generate nginx configuration block for serving the front-end of this service"""
        return rf"""
server {{
        listen {self.source_port};
        server_name {self.server_name};

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
