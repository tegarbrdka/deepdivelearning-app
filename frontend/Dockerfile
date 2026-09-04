# Build stage
FROM node:20-alpine as build

WORKDIR /app

# Install dependencies
COPY package*.json ./
RUN npm install

# Build the app
COPY . .
RUN npm run build

# Production stage
FROM nginx:alpine

# Copy built static files
COPY --from=build /app/dist /usr/share/nginx/html

# We will mount a custom nginx config via docker-compose
EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
