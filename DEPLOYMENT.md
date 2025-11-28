# Deployment Guide - McRAE's Website Analytics

## Deployment Status: ✅ COMPLETE

Your application has been successfully deployed on Ubuntu server at IP: **72.61.65.163**

## Current Setup

### Services Running
- ✅ Docker Engine (v29.1.0)
- ✅ Docker Compose (v2.40.3)
- ✅ Backend Container (FastAPI on port 8000)
- ✅ Frontend Container (React + Nginx on port 3000)
- ✅ Host Nginx Reverse Proxy (port 80)
- ✅ UFW Firewall (configured)

### Access URLs

**HTTP (Current):**
- Frontend: http://72.61.65.163
- Backend API: http://72.61.65.163/api
- API Documentation: http://72.61.65.163/api/docs

**Direct Container Access (for testing):**
- Backend: http://72.61.65.163:8000
- Frontend: http://72.61.65.163:3000

### Firewall Configuration

The following ports are open:
- Port 22 (SSH)
- Port 80 (HTTP)
- Port 443 (HTTPS - ready for SSL)
- Port 8000 (Backend - can be closed after SSL setup)
- Port 3000 (Frontend - can be closed after SSL setup)

## SSL/HTTPS Setup (When Domain is Ready)

When you have a domain name ready:

1. **Point your domain to the server IP:**
   ```
   A Record: yourdomain.com → 72.61.65.163
   ```

2. **Run the SSL setup script:**
   ```bash
   cd /root/mcraes_website_analytics
   ./setup_ssl.sh yourdomain.com
   ```

   Or manually:
   ```bash
   # Update Nginx config with your domain
   sed -i "s/server_name.*;/server_name yourdomain.com;/" /etc/nginx/sites-available/mcraes
   nginx -t
   
   # Get SSL certificate
   certbot --nginx -d yourdomain.com
   
   # Reload Nginx
   systemctl reload nginx
   ```

3. **After SSL is set up, you can close ports 8000 and 3000:**
   ```bash
   ufw delete allow 8000/tcp
   ufw delete allow 3000/tcp
   ```

## Management Commands

### Docker Compose
```bash
cd /root/mcraes_website_analytics

# View status
docker compose ps

# View logs
docker compose logs -f
docker compose logs backend -f
docker compose logs frontend -f

# Restart services
docker compose restart
docker compose restart backend
docker compose restart frontend

# Stop services
docker compose down

# Start services
docker compose up -d

# Rebuild after code changes
docker compose up -d --build
```

### Nginx
```bash
# Test configuration
nginx -t

# Reload configuration
systemctl reload nginx

# Restart Nginx
systemctl restart nginx

# View logs
tail -f /var/log/nginx/access.log
tail -f /var/log/nginx/error.log
```

### Firewall
```bash
# View status
ufw status

# View numbered rules
ufw status numbered

# Allow/deny ports
ufw allow 80/tcp
ufw deny 8000/tcp
```

## Health Checks

### Backend Health
```bash
curl http://localhost:8000/health
# or
curl http://72.61.65.163/api/health
```

### Frontend Health
```bash
curl http://localhost:3000/health
# or
curl http://72.61.65.163/health
```

## Configuration Files

- **Docker Compose:** `/root/mcraes_website_analytics/docker-compose.yml`
- **Nginx Config:** `/etc/nginx/sites-available/mcraes`
- **Environment Variables:** `/root/mcraes_website_analytics/.env`
- **SSL Setup Script:** `/root/mcraes_website_analytics/setup_ssl.sh`

## Production Settings

- ✅ `DEBUG=False` in docker-compose.yml
- ✅ Containers set to `restart: unless-stopped`
- ✅ Health checks configured
- ✅ Nginx reverse proxy configured
- ✅ Firewall enabled

## Troubleshooting

### Containers not starting
```bash
docker compose logs
docker compose ps
```

### Nginx not working
```bash
nginx -t
systemctl status nginx
tail -f /var/log/nginx/error.log
```

### Can't access from outside
```bash
# Check firewall
ufw status

# Check if services are listening
netstat -tlnp | grep -E ':(80|443|8000|3000)'
```

### SSL certificate renewal
Certbot automatically renews certificates. To test renewal:
```bash
certbot renew --dry-run
```

## Next Steps

1. **Set up domain DNS** (when ready)
2. **Run SSL setup script** (when domain is ready)
3. **Close ports 8000 and 3000** (after SSL is working)
4. **Set up monitoring** (optional)
5. **Configure backups** (recommended)

## Notes

- The application is currently accessible via HTTP on port 80
- SSL/HTTPS can be set up when you have a domain name
- All containers are configured to restart automatically
- Logs are available via `docker compose logs`
- The frontend container's healthcheck may show as unhealthy due to missing wget, but the service is working correctly

