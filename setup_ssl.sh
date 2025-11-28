#!/bin/bash
# SSL Setup Script for McRAE's Website Analytics
# Run this script when you have a domain name ready

set -e

if [ -z "$1" ]; then
    echo "Usage: $0 <your-domain.com>"
    echo "Example: $0 example.com"
    exit 1
fi

DOMAIN=$1

echo "Setting up SSL certificate for domain: $DOMAIN"

# Update Nginx configuration with domain name
sed -i "s/server_name.*;/server_name $DOMAIN;/" /etc/nginx/sites-available/mcraes

# Test Nginx configuration
nginx -t

# Obtain SSL certificate
certbot --nginx -d $DOMAIN --non-interactive --agree-tos --email admin@$DOMAIN --redirect

# Reload Nginx
systemctl reload nginx

echo "SSL certificate has been installed for $DOMAIN"
echo "Your application is now available at: https://$DOMAIN"

