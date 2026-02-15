FROM node:20-alpine AS builder

WORKDIR /app

# Copy package files
COPY package*.json ./

# Install all dependencies (including dev - needed for build)
RUN npm install

# Copy source code
COPY . .

# Set build-time environment variables
# Override with: docker build --build-arg VITE_API_URL=https://yourdomain.com
ARG VITE_API_URL=https://crossposter.aiengineerhelper.com
ARG VITE_TURNSTILE_SITE_KEY=0x4AAAAAACdReuv0seDqWU3U
ENV VITE_API_URL=${VITE_API_URL}
ENV VITE_TURNSTILE_SITE_KEY=${VITE_TURNSTILE_SITE_KEY}

# Build application
RUN npm run build -- --mode production

# Use nginx for serving
FROM nginx:alpine
COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=builder /app/dist /usr/share/nginx/html

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]