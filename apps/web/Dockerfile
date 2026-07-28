FROM node:22-alpine AS build
WORKDIR /app
COPY apps/web/package*.json ./
RUN npm install
COPY apps/web .
ARG NEXT_PUBLIC_API_URL
ENV NEXT_PUBLIC_API_URL=$NEXT_PUBLIC_API_URL
RUN npm run build

FROM node:22-alpine
WORKDIR /app
ENV NODE_ENV=production
RUN addgroup -S -g 10001 app && adduser -S -u 10001 -G app app
COPY --chown=app:app --from=build /app/.next/standalone ./
COPY --chown=app:app --from=build /app/.next/static ./.next/static
RUN mkdir -p /app/.next/cache && chown -R app:app /app/.next
USER app
EXPOSE 3000
CMD ["node", "server.js"]

