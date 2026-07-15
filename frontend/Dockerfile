# syntax=docker/dockerfile:1

# -----------------------------------------------------------------------------
# Stage 1: build frontend (uses .env.production via vite build --mode production)
# -----------------------------------------------------------------------------
FROM node:24-alpine AS builder

WORKDIR /frontend

COPY package.json package-lock.json ./
RUN npm ci

COPY . .
RUN npm run build-only

# -----------------------------------------------------------------------------
# Stage 2: serve static build with nginx
# -----------------------------------------------------------------------------
FROM nginx:alpine AS production

COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=builder /frontend/dist /usr/share/nginx/html

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
