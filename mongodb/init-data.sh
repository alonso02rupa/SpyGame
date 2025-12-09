#!/bin/bash
set -e

echo "Starting MongoDB temporarily to import data during build..."

# Start MongoDB in the background without authentication
mongod --dbpath /data/db --noauth --bind_ip 127.0.0.1 --fork --logpath /tmp/mongodb-build.log

# Wait for MongoDB to be ready (max 30 seconds)
echo "Waiting for MongoDB to be ready..."
for i in {1..30}; do
  if mongosh --quiet --eval "db.adminCommand('ping').ok" > /dev/null 2>&1; then
    echo "MongoDB is ready!"
    break
  fi
  echo "Waiting... ($i/30)"
  sleep 1
done

# Verify MongoDB is actually ready
if ! mongosh --quiet --eval "db.adminCommand('ping').ok" > /dev/null 2>&1; then
  echo "ERROR: MongoDB failed to start!"
  cat /tmp/mongodb-build.log
  exit 1
fi

# Import the data using mongosh
echo "Importing pistas.json into spygame.pistas collection..."
mongosh spygame --quiet --eval "
  const fs = require('fs');
  const data = JSON.parse(fs.readFileSync('/tmp/pistas.json', 'utf8'));
  const result = db.pistas.insertMany(data);
  const count = db.pistas.countDocuments({});
  print('Successfully inserted ' + count + ' documents into spygame.pistas collection');
"

# Verify the import
DOC_COUNT=$(mongosh spygame --quiet --eval "db.pistas.countDocuments({})")
echo "Verification: Found $DOC_COUNT documents in spygame.pistas"

if [ "$DOC_COUNT" -eq "0" ]; then
  echo "ERROR: No documents were imported!"
  exit 1
fi

# Shut down MongoDB gracefully
echo "Shutting down MongoDB..."
mongosh admin --quiet --eval "db.shutdownServer({ force: false, timeoutSecs: 10 })" || true

# Wait for MongoDB process to fully stop
echo "Waiting for MongoDB to stop..."
sleep 3

# Verify MongoDB has stopped
if pgrep -x mongod > /dev/null; then
  echo "WARNING: MongoDB still running, forcing shutdown..."
  pkill -TERM mongod || true
  sleep 2
fi

echo "Build-time data initialization complete!"
echo "MongoDB image now contains preloaded data in /data/db"

