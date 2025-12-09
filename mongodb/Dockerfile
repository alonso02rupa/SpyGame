FROM mongo:7.0

# Copy the data file and initialization script  
COPY pistas.json /tmp/pistas.json
COPY init-data.sh /tmp/init-data.sh
COPY custom-entrypoint.sh /usr/local/bin/custom-entrypoint.sh

# Make the scripts executable
RUN chmod +x /tmp/init-data.sh /usr/local/bin/custom-entrypoint.sh

# Create data directory
RUN mkdir -p /data/db

# Run the initialization script during build
# This starts MongoDB temporarily, imports data, and stops it
RUN /tmp/init-data.sh

# Clean up temporary files
RUN rm /tmp/init-data.sh /tmp/pistas.json

# Use custom entrypoint that handles auth initialization
ENTRYPOINT ["/usr/local/bin/custom-entrypoint.sh"]
CMD ["mongod"]
