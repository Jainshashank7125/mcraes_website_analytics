#!/bin/bash
# Check DNS propagation and set up SSL when ready

set -e

DOMAIN="reporting.macraes.com"
SERVER_IP="72.61.65.163"

echo "Checking DNS propagation for $DOMAIN..."
echo "Expected IP: $SERVER_IP"
echo ""

# Check if domain resolves
RESOLVED_IP=$(dig +short $DOMAIN | tail -1)

if [ -z "$RESOLVED_IP" ]; then
    echo "❌ DNS not propagated yet - domain does not resolve"
    echo "Please wait for DNS propagation and try again later"
    echo ""
    echo "You can check DNS propagation with:"
    echo "  dig $DOMAIN"
    echo "  nslookup $DOMAIN"
    exit 1
fi

echo "Domain resolves to: $RESOLVED_IP"

if [ "$RESOLVED_IP" != "$SERVER_IP" ]; then
    echo "⚠️  Warning: Domain resolves to $RESOLVED_IP, but server IP is $SERVER_IP"
    echo "DNS may still be propagating, or the wrong IP is configured"
    read -p "Continue with SSL setup anyway? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Aborted. Please verify DNS configuration."
        exit 1
    fi
else
    echo "✅ DNS is correctly pointing to this server!"
fi

echo ""
echo "Proceeding with SSL certificate setup..."
echo ""

# Update Nginx configuration with domain name
echo "Updating Nginx configuration..."
sed -i "s/server_name.*;/server_name $DOMAIN;/" /etc/nginx/sites-available/mcraes

# Test Nginx configuration
echo "Testing Nginx configuration..."
nginx -t

# Obtain SSL certificate
echo ""
echo "Obtaining SSL certificate from Let's Encrypt..."
echo "This may take a minute..."
certbot --nginx -d $DOMAIN --non-interactive --agree-tos --email admin@macraes.co --redirect

# Reload Nginx
echo "Reloading Nginx..."
systemctl reload nginx

echo ""
echo "✅ SSL certificate has been installed for $DOMAIN"
echo "✅ Your application is now available at: https://$DOMAIN"
echo ""
echo "HTTP requests will automatically redirect to HTTPS"
