# Quick Reference - McRAE's Website Analytics

## 🚀 Application URLs

- **Frontend (Public):** http://72.61.65.163
- **Backend API:** http://72.61.65.163/api
- **API Docs:** http://72.61.65.163/api/docs

## 📋 Common Commands

```bash
# Navigate to project
cd /root/mcraes_website_analytics

# View container status
docker compose ps

# View logs
docker compose logs -f

# Restart all services
docker compose restart

# Rebuild after code changes
docker compose up -d --build

# Stop services
docker compose down

# Start services
docker compose up -d
```

## 🔒 SSL Setup (When Domain Ready)

```bash
cd /root/mcraes_website_analytics
./setup_ssl.sh yourdomain.com
```

## 🔥 Firewall

```bash
# View status
ufw status

# Close test ports (after SSL)
ufw delete allow 8000/tcp
ufw delete allow 3000/tcp
```

## 📊 Health Checks

```bash
# Backend
curl http://72.61.65.163/api/health

# Frontend
curl http://72.61.65.163/health
```

