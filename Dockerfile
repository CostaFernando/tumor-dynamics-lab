FROM node:24-bookworm-slim@sha256:55fb5f5a527ea2c5c4a95f963e48ef90aa38c7b346054fdc8ee9957a2b55d205 AS node
FROM python:3.12.12-slim-bookworm

COPY --from=node /usr/local/bin/node /usr/local/bin/node
COPY --from=node /usr/local/lib/node_modules /usr/local/lib/node_modules
RUN apt-get update && apt-get install -y --no-install-recommends libstdc++6 libatomic1 \
    && rm -rf /var/lib/apt/lists/* \
    && ln -s /usr/local/lib/node_modules/npm/bin/npm-cli.js /usr/local/bin/npm \
    && npm install --global pnpm@11.25.0 \
    && pip install --no-cache-dir uv==0.9.2
WORKDIR /app
ENV NEXT_TELEMETRY_DISABLED=1 DO_NOT_TRACK=1 UV_PYTHON_DOWNLOADS=never
COPY . .
ARG TDL_API_URL=http://api:8000
ENV TDL_API_URL=$TDL_API_URL
RUN pnpm install --frozen-lockfile && uv sync --frozen && pnpm build
ENV PATH=/app/.venv/bin:$PATH TDL_DATA_DIR=/research UV_OFFLINE=1 NODE_ENV=production
CMD ["tdl", "demo"]
