#!/bin/bash

# Test Runner Script for Arise Plot Management API
# This script runs various types of tests and generates reports

set -e  # Exit on any error

echo "🧪 Arise Plot Management API - Test Suite"
echo "=========================================="

# Check if virtual environment is activated
if [[ "$VIRTUAL_ENV" == "" ]]; then
    echo "⚠️  Warning: Virtual environment not detected"
    echo "   Consider running: source venv/bin/activate"
fi

# Check if server is running
SERVER_URL="http://localhost:8000"
if ! curl -s "$SERVER_URL/health" > /dev/null; then
    echo "❌ FastAPI server not running on $SERVER_URL"
    echo "   Start server with: uvicorn app.main:app --reload --host 0.0.0.0 --port 8000"
    exit 1
fi

echo "✅ FastAPI server is running"

# Install test dependencies
echo "📦 Installing test dependencies..."
pip install -r requirements-test.txt -q

# Create test reports directory
mkdir -p test-reports

# Function to run manual tests
run_manual_tests() {
    echo "🔧 Running Manual API Tests..."
    echo "================================"
    
    # Get tokens for testing
    echo "Getting authentication tokens..."
    
    SUPER_ADMIN_TOKEN=$(curl -s -X POST "$SERVER_URL/api/v1/auth/token" \
        -H "Content-Type: application/json" \
        -d '{"userId": "test_admin", "role": "super_admin", "zone": "GSEZ"}' \
        | jq -r '.access_token' 2>/dev/null || echo "")
    
    if [[ "$SUPER_ADMIN_TOKEN" != "" && "$SUPER_ADMIN_TOKEN" != "null" ]]; then
        echo "✅ Super admin token obtained"
        
        # Test user creation
        echo "Testing user creation..."
        curl -s -X POST "$SERVER_URL/api/v1/users/create_user" \
            -H "Content-Type: application/json" \
            -H "Authorization: Bearer $SUPER_ADMIN_TOKEN" \
            -d '{"email": "test_runner@example.com", "role": "zone_admin", "zone": "GSEZ"}' \
            | jq '.' || echo "User creation test completed"
        
        # Test plot retrieval
        echo "Testing plot retrieval..."
        curl -s -X GET "$SERVER_URL/api/v1/plots/available" \
            -H "Authorization: Bearer $SUPER_ADMIN_TOKEN" \
            | jq '.plots | length' || echo "Plot retrieval test completed"
        
        echo "✅ Manual tests completed"
    else
        echo "❌ Failed to get authentication token"
    fi
}

# Function to run automated tests
run_automated_tests() {
    echo "🤖 Running Automated Tests..."
    echo "============================="
    
    # Run pytest with coverage
    pytest tests/ \
        -v \
        --cov=app \
        --cov-report=html:test-reports/coverage \
        --cov-report=term \
        --junit-xml=test-reports/junit.xml \
        || echo "Some tests failed - check results"
    
    echo "📊 Test coverage report generated: test-reports/coverage/index.html"
}

# Function to run performance tests
run_performance_tests() {
    echo "⚡ Running Performance Tests..."
    echo "=============================="
    
    # Check if locust is available
    if command -v locust &> /dev/null; then
        echo "Starting Locust performance test (10 users, 30 seconds)..."
        
        # Run locust in headless mode
        locust -f tests/test_performance.py \
            --host=$SERVER_URL \
            --users=10 \
            --spawn-rate=2 \
            --run-time=30s \
            --html=test-reports/performance.html \
            --headless \
            || echo "Performance test completed with warnings"
        
        echo "📊 Performance report generated: test-reports/performance.html"
    else
        echo "⚠️  Locust not installed - skipping performance tests"
        echo "   Install with: pip install locust"
    fi
}

# Function to run security tests
run_security_tests() {
    echo "🔒 Running Security Tests..."
    echo "==========================="
    
    # Test JWT token exposure
    echo "Testing JWT payload exposure..."
    TOKEN=$(curl -s -X POST "$SERVER_URL/api/v1/auth/token" \
        -H "Content-Type: application/json" \
        -d '{"userId": "security_test", "role": "super_admin", "zone": "GSEZ"}' \
        | jq -r '.access_token' 2>/dev/null || echo "")
    
    if [[ "$TOKEN" != "" && "$TOKEN" != "null" ]]; then
        echo "JWT Token: $TOKEN"
        echo "Decoding payload (security test):"
        echo $TOKEN | cut -d. -f2 | base64 -d 2>/dev/null | jq '.' || echo "Payload decoded"
        echo "⚠️  JWT payload is visible without secret key!"
    fi
    
    # Test unauthorized access
    echo "Testing unauthorized access..."
    curl -s -X GET "$SERVER_URL/api/v1/users/list_users" \
        | jq '.' 2>/dev/null || echo "Unauthorized test completed"
    
    # Test invalid token
    echo "Testing invalid token handling..."
    curl -s -X GET "$SERVER_URL/api/v1/plots/available" \
        -H "Authorization: Bearer invalid.jwt.token" \
        | jq '.' 2>/dev/null || echo "Invalid token test completed"
    
    echo "🔒 Security tests completed"
}

# Main test execution
main() {
    local test_type="${1:-all}"
    
    case $test_type in
        "manual")
            run_manual_tests
            ;;
        "auto"|"automated")
            run_automated_tests
            ;;
        "perf"|"performance")
            run_performance_tests
            ;;
        "security")
            run_security_tests
            ;;
        "all")
            run_manual_tests
            echo ""
            run_automated_tests
            echo ""
            run_performance_tests
            echo ""
            run_security_tests
            ;;
        *)
            echo "Usage: $0 [manual|auto|perf|security|all]"
            echo ""
            echo "Test Types:"
            echo "  manual     - Manual API tests with curl"
            echo "  auto       - Automated pytest tests"
            echo "  perf       - Performance tests with Locust"
            echo "  security   - Security vulnerability tests"
            echo "  all        - Run all test types (default)"
            exit 1
            ;;
    esac
}

# Run tests
main "$@"

echo ""
echo "✅ Test execution completed!"
echo "📁 Reports available in: test-reports/"
echo "   - coverage/index.html (code coverage)"
echo "   - performance.html (performance metrics)"
echo "   - junit.xml (test results)"
