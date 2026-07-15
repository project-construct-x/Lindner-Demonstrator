# Production image — bakes in .env.production at build time (vite build --mode production)
FROM node:24-alpine AS build

WORKDIR /frontend

COPY package.json package-lock.json* ./
RUN npm ci

COPY . .
RUN npm run build-only

FROM nginx:alpine

COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=build /frontend/dist /usr/share/nginx/html

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
