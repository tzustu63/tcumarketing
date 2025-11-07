#!/bin/sh

set -eu

PORT_VALUE="${PORT:-3000}"

cat <<NGINX_CONF >/etc/nginx/conf.d/default.conf
server {
    listen ${PORT_VALUE};
    server_name _;
    root /usr/share/nginx/html;
    index index.html;

    location / {
        try_files \$uri \$uri/ /index.html;
    }

    location /static {
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
}
NGINX_CONF

exec nginx -g "daemon off;"




