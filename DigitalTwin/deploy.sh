#!/bin/bash

# Cognitive-Twin Production Deployment Script
# This script deploys the complete Cognitive-Twin system to production

set -e  # Exit on any error

echo "🚀 Starting Cognitive-Twin Production Deployment"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
PROJECT_NAME="cognitive-twin"
COMPOSE_FILE="docker-compose.production.yml"
ENV_FILE=".env.production"

# Functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check prerequisites
check_prerequisites() {
    log_info "Checking prerequisites..."
    
    # Check if Docker is installed
    if ! command -v docker &> /dev/null; then
        log_error "Docker is not installed. Please install Docker first."
        exit 1
    fi
    
    # Check if Docker Compose is installed
    if ! command -v docker-compose &> /dev/null; then
        log_error "Docker Compose is not installed. Please install Docker Compose first."
        exit 1
    fi
    
    # Check if environment file exists
    if [ ! -f "$ENV_FILE" ]; then
        log_error "Environment file $ENV_FILE not found. Please create it from env.production.example"
        exit 1
    fi
    
    log_success "Prerequisites check passed"
}

# Validate environment variables
validate_environment() {
    log_info "Validating environment variables..."
    
    source "$ENV_FILE"
    
    # Check required variables
    required_vars=(
        "OPENROUTER_API_KEY"
        "POSTGRES_PASSWORD"
        "MONGODB_PASSWORD"
        "NEO4J_PASSWORD"
        "REDIS_PASSWORD"
        "GRAFANA_PASSWORD"
        "SECRET_KEY"
        "JWT_SECRET_KEY"
    )
    
    for var in "${required_vars[@]}"; do
        if [ -z "${!var}" ] || [ "${!var}" = "your_*_here" ]; then
            log_error "Environment variable $var is not set or has default value"
            exit 1
        fi
    done
    
    log_success "Environment validation passed"
}

# Create necessary directories
create_directories() {
    log_info "Creating necessary directories..."
    
    directories=(
        "logs"
        "logs/nginx"
        "backups"
        "data"
        "data/chroma"
        "monitoring/prometheus"
        "monitoring/grafana/dashboards"
        "monitoring/grafana/datasources"
        "monitoring/logstash/pipeline"
        "nginx"
        "nginx/ssl"
    )
    
    for dir in "${directories[@]}"; do
        mkdir -p "$dir"
        log_info "Created directory: $dir"
    done
    
    log_success "Directories created"
}

# Generate SSL certificates (self-signed for development)
generate_ssl_certificates() {
    log_info "Generating SSL certificates..."
    
    if [ ! -f "nginx/ssl/cert.pem" ] || [ ! -f "nginx/ssl/key.pem" ]; then
        openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
            -keyout nginx/ssl/key.pem \
            -out nginx/ssl/cert.pem \
            -subj "/C=US/ST=State/L=City/O=Organization/CN=localhost"
        
        log_success "SSL certificates generated"
    else
        log_info "SSL certificates already exist"
    fi
}

# Create Nginx configuration
create_nginx_config() {
    log_info "Creating Nginx configuration..."
    
    cat > nginx/nginx.conf << 'EOF'
events {
    worker_connections 1024;
}

http {
    upstream cognitive_twin {
        server cognitive-twin:8000;
    }
    
    upstream grafana {
        server grafana:3000;
    }
    
    upstream kibana {
        server kibana:5601;
    }
    
    upstream prometheus {
        server prometheus:9090;
    }
    
    # Rate limiting
    limit_req_zone $binary_remote_addr zone=api:10m rate=10r/s;
    limit_req_zone $binary_remote_addr zone=websocket:10m rate=5r/s;
    
    # Main server block
    server {
        listen 80;
        server_name localhost;
        
        # Redirect HTTP to HTTPS
        return 301 https://$server_name$request_uri;
    }
    
    server {
        listen 443 ssl http2;
        server_name localhost;
        
        # SSL configuration
        ssl_certificate /etc/nginx/ssl/cert.pem;
        ssl_certificate_key /etc/nginx/ssl/key.pem;
        ssl_protocols TLSv1.2 TLSv1.3;
        ssl_ciphers ECDHE-RSA-AES256-GCM-SHA512:DHE-RSA-AES256-GCM-SHA512:ECDHE-RSA-AES256-GCM-SHA384:DHE-RSA-AES256-GCM-SHA384;
        ssl_prefer_server_ciphers off;
        
        # Security headers
        add_header X-Frame-Options DENY;
        add_header X-Content-Type-Options nosniff;
        add_header X-XSS-Protection "1; mode=block";
        add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
        
        # Main application
        location / {
            limit_req zone=api burst=20 nodelay;
            proxy_pass http://cognitive_twin;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
        }
        
        # WebSocket support
        location /ws {
            limit_req zone=websocket burst=10 nodelay;
            proxy_pass http://cognitive_twin;
            proxy_http_version 1.1;
            proxy_set_header Upgrade $http_upgrade;
            proxy_set_header Connection "upgrade";
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
        }
        
        # Health check
        location /health {
            proxy_pass http://cognitive_twin;
            access_log off;
        }
        
        # Monitoring endpoints
        location /grafana/ {
            proxy_pass http://grafana/;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
        }
        
        location /kibana/ {
            proxy_pass http://kibana/;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
        }
        
        location /prometheus/ {
            proxy_pass http://prometheus/;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
        }
    }
}
EOF
    
    log_success "Nginx configuration created"
}

# Create monitoring configurations
create_monitoring_configs() {
    log_info "Creating monitoring configurations..."
    
    # Prometheus configuration
    cat > monitoring/prometheus.yml << 'EOF'
global:
  scrape_interval: 15s
  evaluation_interval: 15s

rule_files:
  # - "first_rules.yml"
  # - "second_rules.yml"

scrape_configs:
  - job_name: 'prometheus'
    static_configs:
      - targets: ['localhost:9090']

  - job_name: 'cognitive-twin'
    static_configs:
      - targets: ['cognitive-twin:8000']
    metrics_path: '/metrics'
    scrape_interval: 30s

  - job_name: 'postgres'
    static_configs:
      - targets: ['postgres:5432']

  - job_name: 'redis'
    static_configs:
      - targets: ['redis:6379']

  - job_name: 'mongodb'
    static_configs:
      - targets: ['mongodb:27017']

  - job_name: 'neo4j'
    static_configs:
      - targets: ['neo4j:7474']
EOF
    
    # Grafana datasource configuration
    mkdir -p monitoring/grafana/datasources
    cat > monitoring/grafana/datasources/prometheus.yml << 'EOF'
apiVersion: 1

datasources:
  - name: Prometheus
    type: prometheus
    access: proxy
    url: http://prometheus:9090
    isDefault: true
    editable: true
EOF
    
    # Grafana dashboard configuration
    mkdir -p monitoring/grafana/dashboards
    cat > monitoring/grafana/dashboards/dashboard.yml << 'EOF'
apiVersion: 1

providers:
  - name: 'default'
    orgId: 1
    folder: ''
    type: file
    disableDeletion: false
    updateIntervalSeconds: 10
    allowUiUpdates: true
    options:
      path: /etc/grafana/provisioning/dashboards
EOF
    
    # Logstash pipeline configuration
    mkdir -p monitoring/logstash/pipeline
    cat > monitoring/logstash/pipeline/logstash.conf << 'EOF'
input {
  file {
    path => "/usr/share/logstash/logs/*.log"
    start_position => "beginning"
    codec => "json"
  }
}

filter {
  if [fields][service] == "cognitive-twin" {
    mutate {
      add_tag => ["cognitive-twin"]
    }
  }
}

output {
  elasticsearch {
    hosts => ["elasticsearch:9200"]
    index => "cognitive-twin-logs-%{+YYYY.MM.dd}"
  }
}
EOF
    
    log_success "Monitoring configurations created"
}

# Create backup script
create_backup_script() {
    log_info "Creating backup script..."
    
    cat > scripts/backup.sh << 'EOF'
#!/bin/bash

# Backup script for Cognitive-Twin
BACKUP_DIR="/backups"
DATE=$(date +%Y%m%d_%H%M%S)

# Create backup directory
mkdir -p "$BACKUP_DIR/$DATE"

# Backup PostgreSQL
pg_dump -h postgres -U cognitive_twin cognitive_twin > "$BACKUP_DIR/$DATE/postgres_backup.sql"

# Backup MongoDB
mongodump --host mongodb:27017 --username cognitive_twin --password $MONGODB_PASSWORD --db cognitive_twin --out "$BACKUP_DIR/$DATE/mongodb_backup"

# Backup Neo4j
neo4j-admin dump --database=neo4j --to="$BACKUP_DIR/$DATE/neo4j_backup.dump"

# Backup application data
cp -r /app/data "$BACKUP_DIR/$DATE/app_data"

# Create compressed archive
cd "$BACKUP_DIR"
tar -czf "cognitive_twin_backup_$DATE.tar.gz" "$DATE"
rm -rf "$DATE"

# Clean up old backups (keep last 30 days)
find "$BACKUP_DIR" -name "cognitive_twin_backup_*.tar.gz" -mtime +30 -delete

echo "Backup completed: cognitive_twin_backup_$DATE.tar.gz"
EOF
    
    chmod +x scripts/backup.sh
    log_success "Backup script created"
}

# Deploy the application
deploy_application() {
    log_info "Deploying Cognitive-Twin application..."
    
    # Stop existing containers
    docker-compose -f "$COMPOSE_FILE" down --remove-orphans
    
    # Build and start services
    docker-compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" up -d --build
    
    log_success "Application deployed"
}

# Wait for services to be ready
wait_for_services() {
    log_info "Waiting for services to be ready..."
    
    services=(
        "postgres:5432"
        "mongodb:27017"
        "redis:6379"
        "neo4j:7474"
        "cognitive-twin:8000"
    )
    
    for service in "${services[@]}"; do
        IFS=':' read -r host port <<< "$service"
        log_info "Waiting for $host:$port..."
        
        while ! nc -z "$host" "$port"; do
            sleep 2
        done
        
        log_success "$host:$port is ready"
    done
}

# Run health checks
run_health_checks() {
    log_info "Running health checks..."
    
    # Check main application
    if curl -f http://localhost:8000/health > /dev/null 2>&1; then
        log_success "Main application is healthy"
    else
        log_error "Main application health check failed"
        exit 1
    fi
    
    # Check monitoring services
    if curl -f http://localhost:3000 > /dev/null 2>&1; then
        log_success "Grafana is accessible"
    else
        log_warning "Grafana is not accessible"
    fi
    
    if curl -f http://localhost:9090 > /dev/null 2>&1; then
        log_success "Prometheus is accessible"
    else
        log_warning "Prometheus is not accessible"
    fi
    
    log_success "Health checks completed"
}

# Display deployment information
display_deployment_info() {
    log_success "🎉 Cognitive-Twin deployment completed successfully!"
    
    echo ""
    echo "📋 Deployment Information:"
    echo "=========================="
    echo "Main Application: https://localhost"
    echo "Grafana Dashboard: https://localhost/grafana"
    echo "Prometheus: https://localhost/prometheus"
    echo "Kibana: https://localhost/kibana"
    echo ""
    echo "🔐 Default Credentials:"
    echo "Grafana: admin / $GRAFANA_PASSWORD"
    echo ""
    echo "📊 Monitoring:"
    echo "- Application metrics: https://localhost/prometheus"
    echo "- Dashboards: https://localhost/grafana"
    echo "- Logs: https://localhost/kibana"
    echo ""
    echo "🛠️  Management Commands:"
    echo "- View logs: docker-compose -f $COMPOSE_FILE logs -f"
    echo "- Stop services: docker-compose -f $COMPOSE_FILE down"
    echo "- Restart services: docker-compose -f $COMPOSE_FILE restart"
    echo "- Scale services: docker-compose -f $COMPOSE_FILE up -d --scale cognitive-twin=3"
    echo ""
    echo "📁 Important Directories:"
    echo "- Logs: ./logs/"
    echo "- Backups: ./backups/"
    echo "- Data: ./data/"
    echo ""
    echo "⚠️  Security Notes:"
    echo "- Change default passwords in $ENV_FILE"
    echo "- Configure proper SSL certificates for production"
    echo "- Set up firewall rules"
    echo "- Enable log monitoring and alerting"
}

# Main deployment function
main() {
    log_info "Starting Cognitive-Twin production deployment..."
    
    check_prerequisites
    validate_environment
    create_directories
    generate_ssl_certificates
    create_nginx_config
    create_monitoring_configs
    create_backup_script
    deploy_application
    wait_for_services
    run_health_checks
    display_deployment_info
    
    log_success "🚀 Deployment completed successfully!"
}

# Run main function
main "$@"
