FROM node:20-alpine

WORKDIR /app

# Copy package files
COPY ./package.json ./package-lock.json* ./

# Install dependencies
RUN npm install

# Copy docs directory
COPY ./docs ./docs

# Expose VitePress dev server port
EXPOSE 5173

# Run VitePress in dev mode (with --host to bind to 0.0.0.0)
CMD ["npm", "run", "docs:dev", "--", "--host", "0.0.0.0"]
