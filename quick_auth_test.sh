#!/bin/bash
# Quick Auth Endpoint Test - Copy & Paste Commands

echo "🚀 ARISE API AUTH ENDPOINT - QUICK TEST COMMANDS"
echo "=================================================="
echo ""

echo "📋 COPY & PASTE THESE COMMANDS:"
echo ""

echo "✅ 1. VALID AUTHENTICATION (Should return JWT token):"
echo "----------------------------------------------------"
echo 'curl -X POST "http://localhost:8000/api/v1/auth/token" \'
echo '  -H "Content-Type: application/json" \'
echo '  -H "Authorization: Secret arise-master-auth-secret-2025" \'
echo '  -d '"'"'{'
echo '    "userId": "admin001",'
echo '    "role": "super_admin",'
echo '    "zone": "GSEZ"'
echo '  }'"'"
echo ""

echo "❌ 2. INVALID SECRET KEY (Should return 401):"
echo "----------------------------------------------"
echo 'curl -X POST "http://localhost:8000/api/v1/auth/token" \'
echo '  -H "Content-Type: application/json" \'
echo '  -H "Authorization: Secret wrong-secret-key" \'
echo '  -d '"'"'{'
echo '    "userId": "admin001",'
echo '    "role": "super_admin",'
echo '    "zone": "GSEZ"'
echo '  }'"'"
echo ""

echo "❌ 3. MISSING AUTHORIZATION HEADER (Should return 401):"
echo "--------------------------------------------------------"
echo 'curl -X POST "http://localhost:8000/api/v1/auth/token" \'
echo '  -H "Content-Type: application/json" \'
echo '  -d '"'"'{'
echo '    "userId": "admin001",'
echo '    "role": "super_admin",'
echo '    "zone": "GSEZ"'
echo '  }'"'"
echo ""

echo "❌ 4. WRONG AUTHORIZATION FORMAT (Should return 401):"
echo "------------------------------------------------------"
echo 'curl -X POST "http://localhost:8000/api/v1/auth/token" \'
echo '  -H "Content-Type: application/json" \'
echo '  -H "Authorization: Bearer arise-master-auth-secret-2025" \'
echo '  -d '"'"'{'
echo '    "userId": "admin001",'
echo '    "role": "super_admin",'
echo '    "zone": "GSEZ"'
echo '  }'"'"
echo ""

echo "❌ 5. INVALID ZONE (Should return 400):"
echo "----------------------------------------"
echo 'curl -X POST "http://localhost:8000/api/v1/auth/token" \'
echo '  -H "Content-Type: application/json" \'
echo '  -H "Authorization: Secret arise-master-auth-secret-2025" \'
echo '  -d '"'"'{'
echo '    "userId": "admin001",'
echo '    "role": "super_admin",'
echo '    "zone": "INVALID"'
echo '  }'"'"
echo ""

echo "❌ 6. INVALID ROLE (Should return 422):"
echo "----------------------------------------"
echo 'curl -X POST "http://localhost:8000/api/v1/auth/token" \'
echo '  -H "Content-Type: application/json" \'
echo '  -H "Authorization: Secret arise-master-auth-secret-2025" \'
echo '  -d '"'"'{'
echo '    "userId": "admin001",'
echo '    "role": "invalid_role",'
echo '    "zone": "GSEZ"'
echo '  }'"'"
echo ""

echo "🎫 7. USE JWT TOKEN FOR PROTECTED ENDPOINT:"
echo "-------------------------------------------"
echo "# First get token from command #1, then:"
echo 'JWT_TOKEN="<paste_access_token_here>"'
echo 'curl -X GET "http://localhost:8000/api/v1/plots/available?country=Gabon" \'
echo '  -H "Authorization: Bearer $JWT_TOKEN"'
echo ""

echo "📚 INPUT REFERENCE:"
echo "==================="
echo "🔑 SECRET KEY:"
echo "   Valid: arise-master-auth-secret-2025"
echo "   Location: Authorization header"
echo "   Format: 'Authorization: Secret <secret>'"
echo ""
echo "👤 USER ID:"
echo "   Examples: admin001, user123, manager_gsez"
echo "   Location: Request body"
echo "   Max length: 50 characters"
echo ""
echo "🎭 ROLE:"
echo "   Valid: super_admin, zone_admin, normal_user"
echo "   Location: Request body"
echo ""
echo "🌍 ZONE:"
echo "   Valid: GSEZ, OSEZ, GABON, TEST"
echo "   Location: Request body"
echo "   Format: 4-6 uppercase letters"
echo ""

echo "🔧 TROUBLESHOOTING:"
echo "==================="
echo "• Server not running? Start with:"
echo "  uvicorn app.main:app --reload --host 0.0.0.0 --port 8000"
echo ""
echo "• Check health: curl http://localhost:8000/health"
echo "• View docs: http://localhost:8000/docs"
echo ""

echo "✨ EXPECTED RESPONSES:"
echo "======================"
echo "✅ Success (200): Returns access_token, token_type, expires_in"
echo "❌ 401: MISSING_AUTHORIZATION, INVALID_AUTHORIZATION_FORMAT, UNAUTHORIZED"
echo "❌ 400: INVALID_ZONE, INVALID_ROLE"
echo "❌ 422: Validation errors (Pydantic schema validation)"
