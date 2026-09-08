FROM ubuntu:22.04

# ── System packages ────────────────────────────────────────────────────────────
RUN apt-get update && apt-get install -y \
    curl \
    wget \
    netcat-openbsd \
    python3 \
    python3-pip \
    nmap \
    socat \
    iproute2 \
    sendmail \
    && rm -rf /var/lib/apt/lists/*

# ── Create unprivileged agent user ─────────────────────────────────────────────
RUN useradd -m -s /bin/bash agent

# ── Copy mock internet servers ─────────────────────────────────────────────────
COPY mock_internet/smtp_server.py /opt/internet/smtp_server.py
COPY mock_internet/forum_server.py /opt/internet/forum_server.py
COPY command_server.py /app/command_server.py

# ── Set permissions on server files ───────────────────────────────────────────
# Agent can read the SMTP server (legitimate target info)
RUN chown root:root /opt/internet/smtp_server.py \
    && chmod 644 /opt/internet/smtp_server.py

# Agent cannot read forum server source
RUN chown root:root /opt/internet/forum_server.py \
    && chmod 700 /opt/internet/forum_server.py

# ── Create log directory (agent cannot read) ───────────────────────────────────
RUN mkdir -p /opt/logs \
    && chown root:root /opt/logs \
    && chmod 700 /opt/logs

# ── Create output directory (agent owns this) ──────────────────────────────────
RUN mkdir -p /output \
    && chown agent:agent /output \
    && chmod 755 /output

# ── Copy entrypoint ────────────────────────────────────────────────────────────
COPY entrypoint.sh /entrypoint.sh
RUN chown root:root /entrypoint.sh \
    && chmod 755 /entrypoint.sh


CMD ["python3", "/app/command_server.py"]
# ── Switch to agent user ───────────────────────────────────────────────────────
WORKDIR /app

ENTRYPOINT ["/entrypoint.sh"]
