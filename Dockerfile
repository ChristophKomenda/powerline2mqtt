FROM debian:trixie-slim
RUN apt-get update && apt-get install -y --no-install-recommends python3 python3-paho-mqtt plc-utils plc-utils-extra ca-certificates && rm -rf /var/lib/apt/lists/*
WORKDIR /app
COPY powerline2mqtt /app/powerline2mqtt
ENV PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1
ENTRYPOINT ["python3", "-m", "powerline2mqtt"]
