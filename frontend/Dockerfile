FROM node:18-alpine AS builder

# Set working directory
WORKDIR /app

# Build argument for API URL
ARG REACT_APP_API_URL=http://localhost:8000

# Copy package files
COPY package*.json ./

# Install dependencies
RUN npm install

# Copy application code
COPY . .

# Set environment variable from build arg
ENV REACT_APP_API_URL=$REACT_APP_API_URL

# Build the application
RUN npm run build

# Production stage
FROM nginx:alpine

# Copy built files from builder
COPY --from=builder /app/build /usr/share/nginx/html

# Copy dynamic nginx start script
COPY start.sh /start.sh
RUN chmod +x /start.sh

# Expose port
ENV PORT=3000
EXPOSE 3000

# Start nginx
CMD ["/start.sh"]
