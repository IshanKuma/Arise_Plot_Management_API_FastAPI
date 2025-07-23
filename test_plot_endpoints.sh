#!/bin/bash
# Test All Plot API Endpoints
# Usage: ./test_plot_endpoints.sh

echo "🧪 Testing All Plot API Endpoints"
echo "=================================="

# Get JWT token first
echo "🔐 Step 1: Getting JWT Token..."
AUTH_RESPONSE=$(curl -s -X POST "http://localhost:8000/api/v1/auth/token" \
  -H "Content-Type: application/json" \
  -H "Authorization: Secret arise-master-auth-secret-2025" \
  -d '{
    "userId": "admin001",
    "role": "super_admin",
    "zone": "GSEZ"
  }')

JWT_TOKEN=$(echo $AUTH_RESPONSE | jq -r '.access_token')

if [ "$JWT_TOKEN" = "null" ] || [ -z "$JWT_TOKEN" ]; then
    echo "❌ Failed to get JWT token"
    echo "Response: $AUTH_RESPONSE"
    exit 1
fi

echo "✅ JWT Token obtained: ${JWT_TOKEN:0:20}..."
echo ""

# Test 1: GET /plots/available
echo "📊 Test 2: GET /api/v1/plots/available"
echo "------------------------------------"
echo "🔍 Testing without filters:"
curl -s -X GET "http://localhost:8000/api/v1/plots/available" \
  -H "Authorization: Bearer $JWT_TOKEN" \
  -H "Content-Type: application/json" | jq '.'

echo ""
echo "🔍 Testing with country filter:"
curl -s -X GET "http://localhost:8000/api/v1/plots/available?country=Gabon" \
  -H "Authorization: Bearer $JWT_TOKEN" \
  -H "Content-Type: application/json" | jq '.'

echo ""
echo "🔍 Testing with multiple filters:"
curl -s -X GET "http://localhost:8000/api/v1/plots/available?country=Gabon&zoneCode=GSEZ&category=Industrial" \
  -H "Authorization: Bearer $JWT_TOKEN" \
  -H "Content-Type: application/json" | jq '.'

echo ""
echo "=================================================="

# Test 2: PUT /plots/update-plot
echo "📝 Test 3: PUT /api/v1/plots/update-plot"
echo "---------------------------------------"
echo "🔍 Testing plot update:"
curl -s -X PUT "http://localhost:8000/api/v1/plots/update-plot" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $JWT_TOKEN" \
  -d '{
    "plotName": "GSEZ-001",
    "zoneCode": "GSEZ",
    "country": "Gabon",
    "phase": 1,
    "plotStatus": "Allocated",
    "companyName": "Test Company Ltd",
    "sector": "Manufacturing",
    "activity": "Steel Production",
    "investmentAmount": 5000000.00,
    "employmentGenerated": 150,
    "allocatedDate": "2024-01-15",
    "expiryDate": "2029-01-15"
  }' | jq '.'

echo ""
echo "=================================================="

# Test 3: PATCH /plots/release-plot
echo "🔓 Test 4: PATCH /api/v1/plots/release-plot"
echo "------------------------------------------"
echo "🔍 Testing plot release:"
curl -s -X PATCH "http://localhost:8000/api/v1/plots/release-plot" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $JWT_TOKEN" \
  -d '{
    "plotName": "GSEZ-001",
    "zoneCode": "GSEZ",
    "country": "Gabon"
  }' | jq '.'

echo ""
echo "=================================================="

# Test 4: POST /country/zones
echo "🌍 Test 5: POST /api/v1/country/zones"
echo "------------------------------------"
echo "🔍 Testing zone creation:"
curl -s -X POST "http://localhost:8000/api/v1/country/zones" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $JWT_TOKEN" \
  -d '{
    "country": "Benin",
    "zoneCode": "GDIZ",
    "phase": 1,
    "landArea": 150.0,
    "zoneName": "Glo-Djigbé Industrial Zone",
    "zoneType": "SEZ",
    "establishedDate": "2024-07-16"
  }' | jq '.'

echo ""
echo "🏁 All endpoint tests completed!"
