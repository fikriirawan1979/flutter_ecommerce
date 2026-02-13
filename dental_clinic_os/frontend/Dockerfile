# Flutter Frontend Dockerfile
FROM ghcr.io/cirruslabs/flutter:stable

# Set working directory
WORKDIR /app

# Copy pubspec files
COPY pubspec.yaml pubspec.lock ./

# Get dependencies
RUN flutter pub get

# Copy project
COPY . .

# Build the app for web
RUN flutter build web --release

# Production stage
FROM nginx:alpine
COPY --from=0 /app/build/web /usr/share/nginx/html
COPY docker/nginx/nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]