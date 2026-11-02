# ── Stage 1: Build the React app ──────────────────────────────────────────
FROM node:20-alpine AS build

WORKDIR /app

# Install dependencies
COPY package.json package-lock.json* ./
RUN npm ci

# Build for production
COPY . .
RUN npm run build

# ── Stage 2: Serve with nginx ────────────────────────────────────────────
FROM nginx:alpine

# Remove default nginx config
RUN rm /etc/nginx/conf.d/default.conf

# Copy nginx template — nginx:alpine auto-runs envsubst on files in /etc/nginx/templates/
# This substitutes ${PORT} and ${BACKEND_URL} at container startup
COPY default.conf.template /etc/nginx/templates/default.conf.template

# Copy built assets
COPY --from=build /app/dist /usr/share/nginx/html

# Railway injects PORT dynamically; default to 3000 for local Docker
ENV PORT=3000
ENV BACKEND_URL=http://localhost:8000

EXPOSE ${PORT}

# nginx:alpine's default entrypoint handles the template + start
CMD ["nginx", "-g", "daemon off;"]
