FROM node:20-alpine AS builder

WORKDIR /app

# Copy package files
COPY package*.json ./

# Install all dependencies (including dev - needed for build)
RUN npm install

# Copy source code
COPY . .

# Set API URL for production (same-origin deployment)
# Override with: docker build --build-arg VITE_API_URL=https://yourdomain.com
ARG VITE_API_URL=https://crossposter.aiengineerhelper.com
ENV VITE_API_URL=${VITE_API_URL}

# Build application
RUN npm run build -- --mode production

# Use nginx for serving
FROM nginx:alpine
COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=builder /app/dist /usr/share/nginx/html

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]