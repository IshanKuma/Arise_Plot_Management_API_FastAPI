#!/bin/bash
# Arise Plot Management API - Auth Endpoint Testing with curl
# This script demonstrates all authentication scenarios using curl commands

# Configuration
BASE_URL="http://localhost:8000"
AUTH_ENDPOINT="$BASE_URL/api/v1/auth/token"
PLOTS_ENDPOINT="$BASE_URL/api/v1/plots/available"
VALID_SECRET="arise-master-auth-secret-2025"
INVALID_SECRET="wrong-secret-key"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

print_header() {
    echo ""
    echo "============================================================"
    echo -e "${BLUE}🧪 TEST: $1${NC}"
    echo "============================================================"
}

print_success() {
    echo -e "${GREEN}✅ SUCCESS: $1${NC}"
}

print_error() {
    echo -e "${RED}❌ FAILED: $1${NC}"
}

print_info() {
    echo -e "${YELLOW}💡 INFO: $1${NC}"
}

# Test Case 1: Valid Authentication
test_valid_auth() {
    print_header "Valid Authentication"
    echo "📤 REQUEST:"
    echo "  Method: POST"
    echo "  URL: $AUTH_ENDPOINT"
    echo "  Headers:"
    echo "    Content-Type: application/json"
    echo "    Authorization: Secret $VALID_SECRET  👈 SECRET KEY HERE"
    echo "  Body:"
    echo "    {"
    echo "      \"userId\": \"admin001\",      👈 USER ID HERE"
    echo "      \"role\": \"super_admin\",     👈 ROLE HERE (super_admin/zone_admin/normal_user)"
    echo "      \"zone\": \"GSEZ\"             👈 ZONE HERE (GSEZ/OSEZ/GABON/TEST)"
    echo "    }"
    echo ""
    
    echo "📥 RESPONSE:"
    response=$(curl -s -w "\nHTTP_STATUS:%{http_code}" -X POST "$AUTH_ENDPOINT" \
        -H "Content-Type: application/json" \
        -H "Authorization: Secret $VALID_SECRET" \
        -d '{
            "userId": "admin001",
            "role": "super_admin",
            "zone": "GSEZ"
        }')
    
    http_status=$(echo "$response" | grep "HTTP_STATUS" | cut -d: -f2)
    body=$(echo "$response" | sed '/HTTP_STATUS/d')
    
    echo "$body" | jq '.' 2>/dev/null || echo "$body"
    echo "Status Code: $http_status"
    
    if [ "$http_status" = "200" ]; then
        print_success "JWT token generated successfully!"
        # Extract token for later use
        JWT_TOKEN=$(echo "$body" | jq -r '.access_token' 2>/dev/null)
        echo "🎫 Token: ${JWT_TOKEN:0:50}..."
    else
        print_error "Expected status 200, got $http_status"
    fi
}

# Test Case 2: Invalid Secret Key
test_invalid_secret() {
    print_header "Invalid Secret Key"
    echo "📤 REQUEST:"
    echo "  Authorization: Secret $INVALID_SECRET  👈 WRONG SECRET KEY"
    echo ""
    
    echo "📥 RESPONSE:"
    response=$(curl -s -w "\nHTTP_STATUS:%{http_code}" -X POST "$AUTH_ENDPOINT" \
        -H "Content-Type: application/json" \
        -H "Authorization: Secret $INVALID_SECRET" \
        -d '{
            "userId": "admin001",
            "role": "super_admin",
            "zone": "GSEZ"
        }')
    
    http_status=$(echo "$response" | grep "HTTP_STATUS" | cut -d: -f2)
    body=$(echo "$response" | sed '/HTTP_STATUS/d')
    
    echo "$body" | jq '.' 2>/dev/null || echo "$body"
    echo "Status Code: $http_status"
    
    if [ "$http_status" = "401" ]; then
        print_success "Correctly rejected invalid secret key!"
    else
        print_error "Expected status 401, got $http_status"
    fi
}

# Test Case 3: Missing Authorization Header
test_missing_auth_header() {
    print_header "Missing Authorization Header"
    echo "📤 REQUEST:"
    echo "  Headers: Content-Type only (NO Authorization header)  👈 MISSING AUTH HEADER"
    echo ""
    
    echo "📥 RESPONSE:"
    response=$(curl -s -w "\nHTTP_STATUS:%{http_code}" -X POST "$AUTH_ENDPOINT" \
        -H "Content-Type: application/json" \
        -d '{
            "userId": "admin001",
            "role": "super_admin",
            "zone": "GSEZ"
        }')
    
    http_status=$(echo "$response" | grep "HTTP_STATUS" | cut -d: -f2)
    body=$(echo "$response" | sed '/HTTP_STATUS/d')
    
    echo "$body" | jq '.' 2>/dev/null || echo "$body"
    echo "Status Code: $http_status"
    
    if [ "$http_status" = "401" ]; then
        print_success "Correctly requires Authorization header!"
    else
        print_error "Expected status 401, got $http_status"
    fi
}

# Test Case 4: Wrong Authorization Format
test_wrong_auth_format() {
    print_header "Wrong Authorization Format"
    echo "📤 REQUEST:"
    echo "  Authorization: Bearer $VALID_SECRET  👈 WRONG FORMAT (should be 'Secret')"
    echo ""
    
    echo "📥 RESPONSE:"
    response=$(curl -s -w "\nHTTP_STATUS:%{http_code}" -X POST "$AUTH_ENDPOINT" \
        -H "Content-Type: application/json" \
        -H "Authorization: Bearer $VALID_SECRET" \
        -d '{
            "userId": "admin001",
            "role": "super_admin",
            "zone": "GSEZ"
        }')
    
    http_status=$(echo "$response" | grep "HTTP_STATUS" | cut -d: -f2)
    body=$(echo "$response" | sed '/HTTP_STATUS/d')
    
    echo "$body" | jq '.' 2>/dev/null || echo "$body"
    echo "Status Code: $http_status"
    
    if [ "$http_status" = "401" ]; then
        print_success "Correctly rejects wrong Authorization format!"
    else
        print_error "Expected status 401, got $http_status"
    fi
}

# Test Case 5: Invalid Zone
test_invalid_zone() {
    print_header "Invalid Zone"
    echo "📤 REQUEST:"
    echo "  Body: zone = \"INVALID\"  👈 INVALID ZONE (not in GSEZ/OSEZ/GABON/TEST)"
    echo ""
    
    echo "📥 RESPONSE:"
    response=$(curl -s -w "\nHTTP_STATUS:%{http_code}" -X POST "$AUTH_ENDPOINT" \
        -H "Content-Type: application/json" \
        -H "Authorization: Secret $VALID_SECRET" \
        -d '{
            "userId": "admin001",
            "role": "super_admin",
            "zone": "INVALID"
        }')
    
    http_status=$(echo "$response" | grep "HTTP_STATUS" | cut -d: -f2)
    body=$(echo "$response" | sed '/HTTP_STATUS/d')
    
    echo "$body" | jq '.' 2>/dev/null || echo "$body"
    echo "Status Code: $http_status"
    
    if [ "$http_status" = "400" ]; then
        print_success "Correctly rejects invalid zone!"
    else
        print_error "Expected status 400, got $http_status"
    fi
}

# Test Case 6: Different Valid Roles
test_different_roles() {
    print_header "Different Valid Roles"
    
    roles=("super_admin" "zone_admin" "normal_user")
    
    for role in "${roles[@]}"; do
        echo ""
        echo "🎭 Testing Role: $role"
        
        response=$(curl -s -w "\nHTTP_STATUS:%{http_code}" -X POST "$AUTH_ENDPOINT" \
            -H "Content-Type: application/json" \
            -H "Authorization: Secret $VALID_SECRET" \
            -d "{
                \"userId\": \"user_$role\",
                \"role\": \"$role\",
                \"zone\": \"GSEZ\"
            }")
        
        http_status=$(echo "$response" | grep "HTTP_STATUS" | cut -d: -f2)
        
        if [ "$http_status" = "200" ]; then
            print_success "$role: Token generated successfully!"
        else
            print_error "$role: Failed with status $http_status"
        fi
    done
}

# Test Case 7: JWT Token Usage
test_jwt_usage() {
    if [ -z "$JWT_TOKEN" ]; then
        print_header "JWT Token Usage - SKIPPED"
        echo "⚠️ No JWT token available from previous tests"
        return
    fi
    
    print_header "JWT Token Usage"
    echo "📤 REQUEST:"
    echo "  Method: GET"
    echo "  URL: $PLOTS_ENDPOINT?country=Gabon"
    echo "  Headers:"
    echo "    Authorization: Bearer \$JWT_TOKEN  👈 JWT TOKEN HERE"
    echo ""
    
    echo "📥 RESPONSE:"
    response=$(curl -s -w "\nHTTP_STATUS:%{http_code}" -X GET "$PLOTS_ENDPOINT?country=Gabon" \
        -H "Authorization: Bearer $JWT_TOKEN")
    
    http_status=$(echo "$response" | grep "HTTP_STATUS" | cut -d: -f2)
    body=$(echo "$response" | sed '/HTTP_STATUS/d')
    
    echo "$body" | jq '.' 2>/dev/null || echo "$body"
    echo "Status Code: $http_status"
    
    if [ "$http_status" = "200" ]; then
        plot_count=$(echo "$body" | jq '.plots | length' 2>/dev/null || echo "unknown")
        print_success "Retrieved $plot_count plots using JWT token!"
    else
        print_error "Expected status 200, got $http_status"
    fi
}

# Data Input Reference
show_data_input_reference() {
    print_header "📚 DATA INPUT REFERENCE"
    echo ""
    echo "🔑 SECRET KEY (Authorization Header):"
    echo "   Location: Authorization: Secret <SECRET_KEY>"
    echo "   Valid:    arise-master-auth-secret-2025"
    echo "   Invalid:  any-other-value"
    echo ""
    echo "👤 USER ID (Request Body):"
    echo "   Field:    userId"
    echo "   Type:     string (max 50 chars)"
    echo "   Example:  \"admin001\", \"user123\", \"manager_gsez\""
    echo ""
    echo "🎭 ROLE (Request Body):"
    echo "   Field:    role"
    echo "   Valid:    \"super_admin\", \"zone_admin\", \"normal_user\""
    echo "   Invalid:  \"admin\", \"user\", \"manager\""
    echo ""
    echo "🌍 ZONE (Request Body):"
    echo "   Field:    zone"
    echo "   Valid:    \"GSEZ\", \"OSEZ\", \"GABON\", \"TEST\""
    echo "   Invalid:  \"INVALID\", \"gsez\", \"zone1\""
    echo ""
    echo "🎫 JWT TOKEN (Protected Endpoints):"
    echo "   Location: Authorization: Bearer <JWT_TOKEN>"
    echo "   Source:   Received from successful /auth/token call"
    echo "   Usage:    All other API endpoints"
}

# Main execution
main() {
    echo "🚀 ARISE PLOT MANAGEMENT API - AUTH ENDPOINT TESTING"
    echo "================================================================================"
    echo "This script demonstrates all authentication scenarios using curl commands"
    echo "================================================================================"
    
    # Check if server is running
    if ! curl -s "$BASE_URL/health" >/dev/null 2>&1; then
        print_error "Cannot connect to API server at $BASE_URL"
        echo "🔧 Make sure the FastAPI server is running:"
        echo "   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000"
        exit 1
    fi
    
    # Show data input reference first
    show_data_input_reference
    
    # Run all tests
    test_valid_auth
    test_invalid_secret
    test_missing_auth_header
    test_wrong_auth_format
    test_invalid_zone
    test_different_roles
    test_jwt_usage
    
    echo ""
    echo "============================================================"
    echo -e "${GREEN}🎉 ALL TESTS COMPLETED!${NC}"
    echo "📚 Check the output above for detailed results"
    echo "============================================================"
}

# Check for dependencies
check_dependencies() {
    if ! command -v jq >/dev/null 2>&1; then
        print_info "jq not found - JSON responses will be displayed as raw text"
    fi
}

check_dependencies
main
