# Security Documentation - SpyGame

This document describes the security features implemented in SpyGame and best practices for secure deployment.

## 🔐 Security Features

### 1. MongoDB Authentication

SpyGame uses authenticated MongoDB connections. The database requires username and password for access.

**Configuration in `.env`:**
```env
MONGO_INITDB_ROOT_USERNAME=spygame
MONGO_INITDB_ROOT_PASSWORD=your_secure_password_here
```

**Important:** 
- Always change the default password in production
- Use strong, unique passwords (at least 16 characters with mixed case, numbers, and symbols)
- Never commit `.env` files to version control

### 2. MongoDB Network Security

MongoDB is only accessible internally within the Docker network:
- MongoDB ports are NOT exposed to the host machine
- Only the web service container can connect to MongoDB
- This prevents direct external access to the database

**Accessing MongoDB for Administration:**

To access MongoDB for backups, restores, or other admin tasks, use `docker exec`:

```bash
# Access MongoDB shell
docker-compose exec mongodb mongosh -u $MONGO_INITDB_ROOT_USERNAME -p $MONGO_INITDB_ROOT_PASSWORD --authenticationDatabase admin spygame

# Backup the database
docker-compose exec mongodb mongodump -u $MONGO_INITDB_ROOT_USERNAME -p $MONGO_INITDB_ROOT_PASSWORD --authenticationDatabase admin --db spygame --out /data/db/backup

# Copy backup to host
docker cp $(docker-compose ps -q mongodb):/data/db/backup ./backup

# Restore from backup
docker cp ./backup $(docker-compose ps -q mongodb):/data/db/backup
docker-compose exec mongodb mongorestore -u $MONGO_INITDB_ROOT_USERNAME -p $MONGO_INITDB_ROOT_PASSWORD --authenticationDatabase admin --db spygame /data/db/backup/spygame
```

**Note:** If you need temporary external access to MongoDB for development tools like MongoDB Compass, you can add the ports back temporarily by creating a `docker-compose.override.yml`:

```yaml
# docker-compose.override.yml (DO NOT use in production)
services:
  mongodb:
    ports:
      - "27017:27017"
```

### 3. Password Validation

User passwords must meet the following requirements:
- Minimum 12 characters
- At least one uppercase letter (A-Z)
- At least one lowercase letter (a-z)
- At least one number (0-9)
- At least one special character (!@#$%^&*()_+=-)

### 4. Input Validation (NoSQL Injection Prevention)

Usernames are validated with strict rules:
- Only alphanumeric characters and underscores allowed
- Length between 3 and 20 characters
- Regex pattern: `^[a-zA-Z0-9_]{3,20}$`

This prevents NoSQL injection attacks by ensuring only safe characters are used in database queries.

### 5. Rate Limiting

To prevent brute-force attacks, the following rate limits are enforced:

| Endpoint | Limit |
|----------|-------|
| Global | 200 requests/day, 50 requests/hour |
| `/login` | 5 attempts per minute |
| `/register` | 3 attempts per minute |
| `/make_guess` | 20 attempts per minute |

### 6. CSRF Protection

Cross-Site Request Forgery (CSRF) protection is enabled via Flask-WTF:
- All POST endpoints are protected
- API endpoints using JSON are exempt (they use session-based auth)
- CSRF tokens are automatically available in templates

### 7. Secure Session Management

- Flask sessions are signed with a secret key
- Session data is encrypted and cannot be tampered with
- Game sessions are cleared on logout

### 8. Docker Volume Security

In development mode, only specific subdirectories are mounted:
- `./static` - Static assets (CSS, JS, images)
- `./templates` - HTML templates
- `./datatreatment` - Data processing scripts

**For production:** Do not use bind mounts. Build the application into the Docker image using `COPY` in the Dockerfile.

## 🚀 Deployment Best Practices

### Environment Configuration

1. **Generate a strong secret key:**
   ```bash
   python -c "import secrets; print(secrets.token_hex(32))"
   ```

2. **Set production environment variables:**
   ```env
   FLASK_SECRET_KEY=<your-generated-secret-key>
   FLASK_ENV=production
   FLASK_DEBUG=False
   MONGO_INITDB_ROOT_USERNAME=<secure-username>
   MONGO_INITDB_ROOT_PASSWORD=<secure-password>
   ```

3. **Never use default credentials in production**

### MongoDB Setup

1. Create `.env` file from template:
   ```bash
   cp .env.example .env
   ```

2. Set secure MongoDB credentials:
   ```env
   MONGO_INITDB_ROOT_USERNAME=spygame_admin
   MONGO_INITDB_ROOT_PASSWORD=Your-Super-Secure-Password-123!
   ```

3. Start the services:
   ```bash
   docker-compose up -d
   ```

### HTTPS/SSL (Recommended for Production)

For production deployments, you should:
1. Use a reverse proxy (nginx, Traefik) with SSL termination
2. Obtain SSL certificates (Let's Encrypt)
3. Redirect HTTP to HTTPS

Example nginx configuration:
```nginx
server {
    listen 80;
    server_name yourdomain.com;
    return 301 https://$host$request_uri;
}

server {
    listen 443 ssl;
    server_name yourdomain.com;
    
    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;
    
    location / {
        proxy_pass http://localhost:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

## ⚠️ Security Checklist

Before deploying to production:

- [ ] Changed `FLASK_SECRET_KEY` to a strong, unique value
- [ ] Changed MongoDB username and password
- [ ] Set `FLASK_DEBUG=False`
- [ ] Set `FLASK_ENV=production`
- [ ] Verified MongoDB ports are not exposed externally
- [ ] Configured HTTPS/SSL
- [ ] Reviewed and tested rate limiting
- [ ] Removed or secured any development endpoints
- [ ] Updated all dependencies to latest secure versions

## 📝 Logging

The application uses Python's logging module:
- **INFO**: General application events
- **WARNING**: Potential issues (e.g., failed login attempts)
- **ERROR**: Errors and exceptions

Logs are output to stdout by default. For production, configure a proper logging backend.

## 🐛 Reporting Security Issues

If you discover a security vulnerability, please:
1. **Do not** open a public issue
2. Contact the maintainers privately
3. Provide details about the vulnerability
4. Allow time for the issue to be fixed before public disclosure

## 📚 Additional Resources

- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [Flask Security Best Practices](https://flask.palletsprojects.com/en/2.3.x/security/)
- [MongoDB Security Checklist](https://www.mongodb.com/docs/manual/administration/security-checklist/)
