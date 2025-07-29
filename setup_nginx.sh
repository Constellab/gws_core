#!/bin/bash

# Setup script for nginx in container
set -e

echo "Setting up nginx for dynamic Reflex app routing..."

# Install nginx
apt-get update
apt-get install -y nginx

# Create nginx configuration
cat > /etc/nginx/nginx.conf << 'EOF'
user www-data;
worker_processes auto;
pid /run/nginx.pid;
include /etc/nginx/modules-enabled/*.conf;

events {
    worker_connections 1024;
}

http {
    include /etc/nginx/mime.types;
    default_type application/octet-stream;

    # Logging
    access_log /var/log/nginx/access.log;
    error_log /var/log/nginx/error.log;

    # Gzip compression
    gzip on;
    gzip_types text/plain text/css application/json application/javascript text/xml application/xml application/xml+rss text/javascript;

    # Default server block for unmatched requests
    server {
        listen 80 default_server;
        server_name _;
        return 444;
    }

    # Include dynamically generated service configurations
    include /etc/nginx/conf.d/dynamic_services.conf;
}
EOF

# Create nginx conf.d directory
mkdir -p /etc/nginx/conf.d

# Create initial empty dynamic services config
cat > /etc/nginx/conf.d/dynamic_services.conf << 'EOF'
# No services registered yet
EOF

# Test nginx configuration
nginx -t

echo "Nginx setup complete!"
echo ""
echo "To use:"
echo "1. Run this script in your container"
echo "2. Start your Reflex apps - nginx will start automatically"
echo "3. External proxy should redirect app*.myhost.com to container:80"