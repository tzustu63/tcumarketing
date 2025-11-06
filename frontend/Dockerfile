FROM node:18-alpine

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

# Expose port
EXPOSE 3000

# Start application
CMD ["npm", "start"]
