# ============================================
# LEARNING: Multi-Stage Docker Build
# ============================================
# This Dockerfile has TWO stages:
# 1. "builder" stage: Compiles the Next.js app
# 2. "runner" stage: Runs the compiled app
#
# Why? The builder needs dev tools (TypeScript compiler, etc.)
# But the runner only needs the compiled output
# Result: Final image is MUCH smaller (500MB → 150MB)

# ============================================
# STAGE 1: Builder
# ============================================
FROM node:20-alpine AS builder

# Why alpine? It's a tiny Linux (5MB vs 100MB+)
# Perfect for Node.js apps

WORKDIR /app

# Copy package files first (for caching)
COPY package*.json ./

# Install ALL dependencies (including devDependencies)
# We need these to build the app
RUN npm ci

# Copy the rest of the code
COPY . .

# Build the Next.js application
# This compiles TypeScript, optimizes code, generates static files
RUN npm run build

# ============================================
# STAGE 2: Runner (Production)
# ============================================
FROM node:20-alpine AS runner

WORKDIR /app

# Set to production mode
ENV NODE_ENV=production

# Create a non-root user for security
# Running as root in containers is dangerous!
RUN addgroup --system --gid 1001 nodejs
RUN adduser --system --uid 1001 nextjs

# Copy package files and install ONLY production dependencies
COPY package*.json ./
RUN npm ci --only=production

# Copy the built app from the builder stage
# --from=builder: Take files from the previous stage
# This is the magic of multi-stage builds!
COPY --from=builder /app/.next ./.next
COPY --from=builder /app/public ./public
COPY --from=builder /app/next.config.ts ./

# Change ownership to our non-root user
RUN chown -R nextjs:nodejs /app

# Switch to non-root user
USER nextjs

# Expose port 3000
EXPOSE 3000

# Start the Next.js production server
CMD ["npm", "start"]
