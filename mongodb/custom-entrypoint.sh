#!/bin/bash
set -e

# This is a wrapper around the official MongoDB docker-entrypoint.sh
# It handles the case where data is preloaded but auth isn't set up yet

# Check if this is the first run with auth enabled
if [ -n "$MONGO_INITDB_ROOT_USERNAME" ] && [ -n "$MONGO_INITDB_ROOT_PASSWORD" ]; then
    # Check if admin.system.users collection exists (indicates auth is set up)
    if [ ! -f /data/db/.auth_initialized ]; then
        echo "Initializing authentication for preloaded data..."
        
        # Start MongoDB temporarily without auth
        mongod --dbpath /data/db --noauth --bind_ip 127.0.0.1 --fork --logpath /tmp/mongo-init-auth.log
        
        # Wait for MongoDB to be ready
        for i in {1..30}; do
          if mongosh --quiet --eval "db.adminCommand('ping').ok" > /dev/null 2>&1; then
            break
          fi
          sleep 1
        done
        
        # Create admin user
        mongosh admin --quiet --eval "
          db.createUser({
            user: '${MONGO_INITDB_ROOT_USERNAME}',
            pwd: '${MONGO_INITDB_ROOT_PASSWORD}',
            roles: [
              { role: 'root', db: 'admin' }
            ]
          });
          print('Admin user created');
        "
        
        # Mark auth as initialized
        touch /data/db/.auth_initialized
        
        # Shut down MongoDB
        mongosh admin --quiet --eval "db.shutdownServer()" || true
        sleep 2
        
        echo "Authentication initialized successfully"
    fi
fi

# Call the original MongoDB entrypoint
exec /usr/local/bin/docker-entrypoint.sh "$@"
