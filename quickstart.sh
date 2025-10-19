#!/bin/bash

# HypePaper Quickstart Script
# Automatically sets up and runs the entire application

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Helper functions
print_header() {
    echo -e "\n${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${BLUE}  $1${NC}"
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}\n"
}

print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠ $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ $1${NC}"
}

# Check prerequisites
check_prerequisites() {
    print_header "Checking Prerequisites"

    # Check Docker
    if ! command -v docker &> /dev/null; then
        print_error "Docker is not installed. Please install Docker first."
        echo "Visit: https://docs.docker.com/get-docker/"
        exit 1
    fi
    print_success "Docker found: $(docker --version)"

    # Check Docker is running
    if ! docker info &> /dev/null; then
        print_error "Docker daemon is not running. Please start Docker."
        exit 1
    fi
    print_success "Docker daemon is running"

    # Check Docker Compose
    if ! docker compose version &> /dev/null; then
        print_error "Docker Compose is not installed."
        exit 1
    fi
    print_success "Docker Compose found: $(docker compose version)"

    # Check Python
    if ! command -v python3 &> /dev/null; then
        print_warning "Python 3 not found. Backend tests will be skipped."
    else
        print_success "Python found: $(python3 --version)"
    fi

    # Check Node.js
    if ! command -v node &> /dev/null; then
        print_warning "Node.js not found. Frontend development will be limited."
    else
        print_success "Node.js found: $(node --version)"
    fi
}

# Setup database
setup_database() {
    print_header "Setting Up Database"

    print_info "Starting PostgreSQL + TimescaleDB..."
    docker compose up -d postgres

    print_info "Waiting for database to be ready..."
    sleep 5

    # Wait for PostgreSQL to be healthy
    while ! docker compose exec postgres pg_isready -U hypepaper &> /dev/null; do
        print_info "Waiting for PostgreSQL..."
        sleep 2
    done

    print_success "Database is ready"
}

# Setup backend
setup_backend() {
    print_header "Setting Up Backend"

    cd backend

    # Check if venv exists
    if [ ! -d "venv" ]; then
        print_info "Creating Python virtual environment..."
        python3 -m venv venv
    fi

    print_info "Activating virtual environment..."
    source venv/bin/activate

    print_info "Installing Python dependencies..."
    pip install -q --upgrade pip
    pip install -q -r requirements.txt

    print_success "Backend dependencies installed"

    print_info "Running database migrations..."

    # Check if using Supabase (skip migrations if so)
    if grep -q "supabase.com" .env 2>/dev/null; then
        print_warning "Supabase detected - skipping migrations (database already configured)"
    else
        alembic upgrade head
        print_success "Database schema created"
    fi

    print_info "Seeding topics..."
    python scripts/seed_topics.py

    print_success "10 research topics added"

    # Ask if user wants sample data
    read -p "$(echo -e ${YELLOW}Do you want to seed sample papers for testing? \(y/N\): ${NC})" -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        print_info "Seeding sample papers..."
        python scripts/seed_sample_data.py
        print_success "~50 sample papers added with historical metrics"
    fi

    cd ..
}

# Setup frontend
setup_frontend() {
    print_header "Setting Up Frontend"

    cd frontend

    if [ ! -d "node_modules" ]; then
        print_info "Installing frontend dependencies..."
        npm install
        print_success "Frontend dependencies installed"
    else
        print_success "Frontend dependencies already installed"
    fi

    cd ..
}

# Start services
start_services() {
    print_header "Starting Services"

    # Start backend in background
    print_info "Starting FastAPI backend server..."
    cd backend
    source venv/bin/activate
    uvicorn src.main:app --host 0.0.0.0 --port 8000 > ../logs/backend.log 2>&1 &
    BACKEND_PID=$!
    cd ..
    print_success "Backend started (PID: $BACKEND_PID)"

    # Wait for backend to be ready
    print_info "Waiting for backend API..."
    sleep 3
    for i in {1..10}; do
        if curl -s http://localhost:8000/api/v1/topics > /dev/null; then
            print_success "Backend API is ready"
            break
        fi
        sleep 2
    done

    # Start frontend in background
    print_info "Starting Vite development server..."
    cd frontend
    npm run dev > ../logs/frontend.log 2>&1 &
    FRONTEND_PID=$!
    cd ..
    print_success "Frontend started (PID: $FRONTEND_PID)"

    # Save PIDs for cleanup
    echo $BACKEND_PID > /tmp/hypepaper_backend.pid
    echo $FRONTEND_PID > /tmp/hypepaper_frontend.pid
}

# Display status
show_status() {
    print_header "HypePaper is Running!"

    echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${GREEN}  🎉 Application successfully started!${NC}"
    echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}\n"

    echo -e "${BLUE}Access Points:${NC}"
    echo -e "  • Frontend:       ${GREEN}http://localhost:5173${NC}"
    echo -e "  • Backend API:    ${GREEN}http://localhost:8000${NC}"
    echo -e "  • API Docs:       ${GREEN}http://localhost:8000/docs${NC}"
    echo -e "  • Database:       ${GREEN}localhost:5432${NC}"

    echo -e "\n${BLUE}Logs:${NC}"
    echo -e "  • Backend:        ${YELLOW}tail -f logs/backend.log${NC}"
    echo -e "  • Frontend:       ${YELLOW}tail -f logs/frontend.log${NC}"
    echo -e "  • Database:       ${YELLOW}docker compose logs -f postgres${NC}"

    echo -e "\n${BLUE}Useful Commands:${NC}"
    echo -e "  • Stop services:  ${YELLOW}./quickstart.sh stop${NC}"
    echo -e "  • View logs:      ${YELLOW}./quickstart.sh logs${NC}"
    echo -e "  • Run tests:      ${YELLOW}./scripts/run_tests.sh${NC}"
    echo -e "  • Background jobs:${YELLOW}cd backend && python -m src.jobs.scheduler${NC}"

    echo -e "\n${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${GREEN}  📖 For more info, see README.md${NC}"
    echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}\n"
}

# Stop services
stop_services() {
    print_header "Stopping Services"

    # Kill backend
    if [ -f /tmp/hypepaper_backend.pid ]; then
        BACKEND_PID=$(cat /tmp/hypepaper_backend.pid)
        if kill -0 $BACKEND_PID 2>/dev/null; then
            kill $BACKEND_PID
            print_success "Backend stopped"
        fi
        rm /tmp/hypepaper_backend.pid
    fi

    # Kill frontend
    if [ -f /tmp/hypepaper_frontend.pid ]; then
        FRONTEND_PID=$(cat /tmp/hypepaper_frontend.pid)
        if kill -0 $FRONTEND_PID 2>/dev/null; then
            kill $FRONTEND_PID
            print_success "Frontend stopped"
        fi
        rm /tmp/hypepaper_frontend.pid
    fi

    # Stop database
    docker compose down
    print_success "Database stopped"
}

# Show logs
show_logs() {
    print_header "Application Logs"

    echo -e "${BLUE}Backend logs:${NC}"
    tail -20 logs/backend.log

    echo -e "\n${BLUE}Frontend logs:${NC}"
    tail -20 logs/frontend.log

    echo -e "\n${BLUE}Database logs:${NC}"
    docker compose logs --tail=20 postgres
}

# Main function
main() {
    # Create logs directory
    mkdir -p logs

    case "${1:-start}" in
        start)
            echo -e "${GREEN}"
            echo "╔═══════════════════════════════════════════════════════╗"
            echo "║                                                       ║"
            echo "║              HypePaper Quickstart                     ║"
            echo "║      Trending Research Paper Tracker                 ║"
            echo "║                                                       ║"
            echo "╚═══════════════════════════════════════════════════════╝"
            echo -e "${NC}"

            check_prerequisites
            setup_database
            setup_backend
            setup_frontend
            start_services
            show_status

            # Keep script running
            echo -e "\n${YELLOW}Press Ctrl+C to stop all services${NC}"
            trap stop_services EXIT
            wait
            ;;

        stop)
            stop_services
            ;;

        logs)
            show_logs
            ;;

        clean)
            print_header "Cleaning Up"
            stop_services
            docker compose down -v
            rm -rf backend/venv
            rm -rf frontend/node_modules
            rm -rf logs
            print_success "Cleanup complete"
            ;;

        *)
            echo "Usage: $0 {start|stop|logs|clean}"
            echo ""
            echo "Commands:"
            echo "  start  - Start all services (default)"
            echo "  stop   - Stop all services"
            echo "  logs   - Show application logs"
            echo "  clean  - Remove all generated files and stop services"
            exit 1
            ;;
    esac
}

# Run main function
main "$@"
