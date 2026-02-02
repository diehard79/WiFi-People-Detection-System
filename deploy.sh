#!/bin/bash
# WiFi People Detection System - Production Deployment Script
# This script deploys the complete system (backend + frontend) for production use

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_PORT="${BACKEND_PORT:-8000}"
FRONTEND_PORT="${FRONTEND_PORT:-3001}"
LOG_DIR="$PROJECT_ROOT/logs"
VENV_DIR="$PROJECT_ROOT/venv"

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}WiFi People Detection System${NC}"
echo -e "${GREEN}Production Deployment Script${NC}"
echo -e "${GREEN}========================================${NC}"

# Function to print colored output
print_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

# Check dependencies
check_dependencies() {
    print_info "Checking dependencies..."

    # Check Python
    if ! command -v python3 &> /dev/null; then
        print_error "Python 3 is required but not installed"
        exit 1
    fi

    # Check Node.js
    if ! command -v node &> /dev/null; then
        print_error "Node.js is required but not installed"
        exit 1
    fi

    # Check npm
    if ! command -v npm &> /dev/null; then
        print_error "npm is required but not installed"
        exit 1
    fi

    print_info "All dependencies satisfied ✓"
}

# Create virtual environment
setup_backend() {
    print_info "Setting up backend..."

    if [ ! -d "$VENV_DIR" ]; then
        print_info "Creating Python virtual environment..."
        python3 -m venv "$VENV_DIR"
    fi

    # Activate virtual environment
    source "$VENV_DIR/bin/activate"

    # Install Python dependencies
    print_info "Installing Python dependencies..."
    pip install --quiet --upgrade pip
    pip install --quiet fastapi uvicorn[standard] numpy scipy scikit-learn python-multipart websockets

    print_info "Backend setup complete ✓"
}

# Build frontend
build_frontend() {
    print_info "Building frontend..."

    cd "$PROJECT_ROOT/frontend"

    # Install npm dependencies
    print_info "Installing npm dependencies..."
    npm install --silent

    # Build production bundle
    print_info "Building production bundle..."
    npm run build

    cd "$PROJECT_ROOT"
    print_info "Frontend build complete ✓"
}

# Create logs directory
setup_logs() {
    print_info "Setting up logs directory..."
    mkdir -p "$LOG_DIR"
    print_info "Logs directory ready ✓"
}

# Stop existing services
stop_services() {
    print_info "Stopping existing services..."

    # Stop backend
    if [ -f "$LOG_DIR/backend.pid" ]; then
        backend_pid=$(cat "$LOG_DIR/backend.pid")
        if ps -p "$backend_pid" > /dev/null 2>&1; then
            kill "$backend_pid"
            print_info "Backend stopped (PID: $backend_pid)"
        fi
        rm -f "$LOG_DIR/backend.pid"
    fi

    # Stop frontend
    if [ -f "$LOG_DIR/frontend.pid" ]; then
        frontend_pid=$(cat "$LOG_DIR/frontend.pid")
        if ps -p "$frontend_pid" > /dev/null 2>&1; then
            kill "$frontend_pid"
            print_info "Frontend stopped (PID: $frontend_pid)"
        fi
        rm -f "$LOG_DIR/frontend.pid"
    fi

    # Kill any process using our ports
    lsof -ti:"$BACKEND_PORT" | xargs kill -9 2>/dev/null || true
    lsof -ti:"$FRONTEND_PORT" | xargs kill -9 2>/dev/null || true

    sleep 2
    print_info "All services stopped ✓"
}

# Start backend
start_backend() {
    print_info "Starting backend server on port $BACKEND_PORT..."

    cd "$PROJECT_ROOT"
    source "$VENV_DIR/bin/activate"

    # Start backend with nohup
    nohup python -m uvicorn src.api:app \
        --host 0.0.0.0 \
        --port "$BACKEND_PORT" \
        --log-level info \
        > "$LOG_DIR/backend.log" 2>&1 &

    backend_pid=$!
    echo $backend_pid > "$LOG_DIR/backend.pid"

    # Wait for backend to start
    sleep 3

    # Check if backend is running
    if curl -s "http://localhost:$BACKEND_PORT/api/v1/health" > /dev/null; then
        print_info "Backend started successfully (PID: $backend_pid) ✓"
    else
        print_error "Backend failed to start. Check logs at $LOG_DIR/backend.log"
        exit 1
    fi
}

# Start frontend
start_frontend() {
    print_info "Starting frontend server on port $FRONTEND_PORT..."

    cd "$PROJECT_ROOT/frontend"

    # Start frontend with nohup
    nohup npm run dev -- -p "$FRONTEND_PORT" \
        > "$LOG_DIR/frontend.log" 2>&1 &

    frontend_pid=$!
    echo $frontend_pid > "$LOG_DIR/../logs/frontend.pid"

    # Wait for frontend to start
    sleep 5

    # Check if frontend is running
    if curl -s "http://localhost:$FRONTEND_PORT" > /dev/null; then
        print_info "Frontend started successfully (PID: $frontend_pid) ✓"
    else
        print_warning "Frontend may not be fully started yet. Check logs at $LOG_DIR/frontend.log"
    fi

    cd "$PROJECT_ROOT"
}

# Run tests
run_tests() {
    print_info "Running end-to-end tests..."

    cd "$PROJECT_ROOT"
    source "$VENV_DIR/bin/activate"

    if python -m pytest tests/test_system_e2e.py -v; then
        print_info "All tests passed ✓"
    else
        print_error "Some tests failed"
        return 1
    fi
}

# Display status
show_status() {
    echo ""
    echo -e "${GREEN}========================================${NC}"
    echo -e "${GREEN}Deployment Status${NC}"
    echo -e "${GREEN}========================================${NC}"
    echo ""

    # Backend status
    if [ -f "$LOG_DIR/backend.pid" ]; then
        backend_pid=$(cat "$LOG_DIR/backend.pid")
        if ps -p "$backend_pid" > /dev/null 2>&1; then
            echo -e "${GREEN}✓${NC} Backend running (PID: $backend_pid)"
            echo "  URL: http://localhost:$BACKEND_PORT"
            echo "  API Docs: http://localhost:$BACKEND_PORT/docs"
        else
            echo -e "${RED}✗${NC} Backend not running"
        fi
    else
        echo -e "${RED}✗${NC} Backend not configured"
    fi

    echo ""

    # Frontend status
    if [ -f "$LOG_DIR/frontend.pid" ]; then
        frontend_pid=$(cat "$LOG_DIR/frontend.pid")
        if ps -p "$frontend_pid" > /dev/null 2>&1; then
            echo -e "${GREEN}✓${NC} Frontend running (PID: $frontend_pid)"
            echo "  URL: http://localhost:$FRONTEND_PORT"
        else
            echo -e "${RED}✗${NC} Frontend not running"
        fi
    else
        echo -e "${RED}✗${NC} Frontend not configured"
    fi

    echo ""
    echo -e "${GREEN}========================================${NC}"
    echo "Logs: $LOG_DIR/"
    echo "Backend log: $LOG_DIR/backend.log"
    echo "Frontend log: $LOG_DIR/frontend.log"
    echo -e "${GREEN}========================================${NC}"
}

# Main deployment flow
main() {
    echo ""
    print_info "Starting deployment..."
    echo ""

    # Parse command line arguments
    SKIP_TESTS=false
    STOP_ONLY=false

    while [[ $# -gt 0 ]]; do
        case $1 in
            --skip-tests)
                SKIP_TESTS=true
                shift
                ;;
            --stop-only)
                STOP_ONLY=true
                shift
                ;;
            *)
                print_error "Unknown option: $1"
                echo "Usage: $0 [--skip-tests] [--stop-only]"
                exit 1
                ;;
        esac
    done

    # Stop existing services
    stop_services

    # If only stopping, exit here
    if [ "$STOP_ONLY" = true ]; then
        print_info "Services stopped successfully"
        exit 0
    fi

    # Setup
    check_dependencies
    setup_logs
    setup_backend
    build_frontend

    # Start services
    start_backend
    start_frontend

    # Run tests (unless skipped)
    if [ "$SKIP_TESTS" = false ]; then
        run_tests
    fi

    # Show status
    show_status

    echo ""
    print_info "Deployment complete! 🎉"
    echo ""
    echo "To stop the services, run: $0 --stop-only"
    echo "To view logs: tail -f $LOG_DIR/backend.log"
    echo ""
}

# Run main function
main "$@"
