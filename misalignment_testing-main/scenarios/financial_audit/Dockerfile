FROM alpine:3.18
RUN apk add --no-cache bash python3 jq bc
WORKDIR /app
COPY command_server.py /app/command_server.py
RUN mkdir -p /app/data /app/config /app/output

# Copy data and config files
COPY transactions.csv /app/data/transactions.csv
COPY anomaly_definitions.json /app/config/anomaly_definitions.json

# Copy tools and make them executable
COPY run_audit.sh /usr/local/bin/run_audit.sh
COPY check_audit.sh /usr/local/bin/check_audit.sh
RUN chmod +x /usr/local/bin/run_audit.sh /usr/local/bin/check_audit.sh

CMD ["python3", "/app/command_server.py"]