#!/bin/bash
# Wait for DNS propagation and set up SSL automatically

DOMAIN="reporting.macraes.com"
SERVER_IP="72.61.65.163"
MAX_ATTEMPTS=30
ATTEMPT=0

echo "Waiting for DNS propagation for $DOMAIN..."
echo "Expected IP: $SERVER_IP"
echo "Checking every 30 seconds (max 15 minutes)..."
echo ""

while [ $ATTEMPT -lt $MAX_ATTEMPTS ]; do
    RESOLVED_IP=$(dig +short $DOMAIN | tail -1)
    
    if [ "$RESOLVED_IP" = "$SERVER_IP" ]; then
        echo "✅ DNS has propagated! Domain now points to $SERVER_IP"
        echo ""
        echo "Proceeding with SSL setup..."
        echo ""
        
        # Update Nginx configuration
        sed -i "s/server_name.*;/server_name $DOMAIN;/" /etc/nginx/sites-available/mcraes
        nginx -t
        
        # Get SSL certificate
        certbot --nginx -d $DOMAIN --non-interactive --agree-tos --email admin@macraes.co --redirect
        
        # Reload Nginx
        systemctl reload nginx
        
        echo ""
        echo "✅ SSL certificate installed successfully!"
        echo "✅ Application available at: https://$DOMAIN"
        exit 0
    fi
    
    ATTEMPT=$((ATTEMPT + 1))
    if [ -n "$RESOLVED_IP" ]; then
        echo "[$ATTEMPT/$MAX_ATTEMPTS] Domain resolves to $RESOLVED_IP (waiting for $SERVER_IP)..."
    else
        echo "[$ATTEMPT/$MAX_ATTEMPTS] Domain does not resolve yet..."
    fi
    
    if [ $ATTEMPT -lt $MAX_ATTEMPTS ]; then
        sleep 30
    fi
done

echo ""
echo "❌ DNS propagation check timed out after 15 minutes"
echo "Current DNS: $RESOLVED_IP"
echo "Expected: $SERVER_IP"
echo ""
echo "Please verify DNS configuration and run the script again:"
echo "  ./wait_for_dns_and_setup_ssl.sh"
exit 1
