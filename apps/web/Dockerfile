# syntax=docker/dockerfile:1.8

FROM node:24-alpine AS dependencies
WORKDIR /workspace
COPY package.json package-lock.json ./
COPY apps/web/package.json ./apps/web/package.json
COPY packages/api-client/package.json ./packages/api-client/package.json
RUN npm ci

FROM dependencies AS development
COPY apps/web ./apps/web
COPY packages/api-client ./packages/api-client
EXPOSE 5173
CMD ["npm", "run", "dev", "--workspace", "@agentic-rag/web", "--", "--host", "0.0.0.0"]

FROM dependencies AS build
COPY apps/web ./apps/web
COPY packages/api-client ./packages/api-client
RUN npm run build --workspace @agentic-rag/web

FROM nginx:1.28-alpine AS production
COPY apps/web/nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=build /workspace/apps/web/dist /usr/share/nginx/html
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]

