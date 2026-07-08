FROM node:20-alpine

WORKDIR /app

# Copy package descriptors
COPY package*.json ./

# Install dependencies
RUN npm install

# Copy source code
COPY . .

EXPOSE 3000

# Run Vite dev server in host mode so it is accessible from outside container
CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0", "--port", "3000"]
