"""
JWT Security Analysis - What happens when someone gets your token?
================================================================

This demonstrates what an attacker can do with a stolen JWT token.
"""
import base64
import json
import hmac
import hashlib
from datetime import datetime


def decode_jwt_payload(jwt_token: str) -> dict:
    """
    Decode JWT payload without needing the secret key.
    This is what ANY attacker can do!
    """
    try:
        # Split JWT into parts
        header, payload, signature = jwt_token.split('.')
        
        # Add padding if needed (base64 requirement)
        payload += '=' * (4 - len(payload) % 4)
        
        # Decode payload (no secret needed!)
        decoded_bytes = base64.urlsafe_b64decode(payload)
        payload_data = json.loads(decoded_bytes)
        
        return payload_data
    except Exception as e:
        return {"error": str(e)}


def analyze_jwt_security(jwt_token: str):
    """Analyze what information is exposed in a JWT token."""
    
    print("🔍 JWT Security Analysis")
    print("=" * 50)
    
    # 1. Decode payload (no secret needed)
    payload = decode_jwt_payload(jwt_token)
    
    print("📋 EXPOSED INFORMATION (visible to anyone):")
    print("-" * 40)
    for key, value in payload.items():
        if key == "exp":
            # Convert timestamp to readable date
            exp_date = datetime.fromtimestamp(value)
            print(f"  {key}: {value} ({exp_date})")
        else:
            print(f"  {key}: {value}")
    
    print("\n🚨 WHAT AN ATTACKER CAN DO:")
    print("-" * 40)
    print("1. ✅ See user role:", payload.get('role'))
    print("2. ✅ See user zone:", payload.get('zone'))
    print("3. ✅ See permissions:", payload.get('permissions'))
    print("4. ✅ See token expiry:", datetime.fromtimestamp(payload.get('exp', 0)))
    print("5. ✅ Make API requests until expiry")
    print("6. ❌ Cannot modify token (signature verification)")
    print("7. ❌ Cannot extend expiry (signature verification)")
    
    print("\n⚠️  ATTACK SCENARIOS:")
    print("-" * 40)
    print("• Use stolen token for API access")
    print("• Enumerate system capabilities")
    print("• Understand permission structure")
    print("• Time attacks around token expiry")
    print("• Social engineering with role information")


def simulate_token_tampering(jwt_token: str):
    """Demonstrate what happens when someone tries to modify a JWT."""
    
    print("\n🔧 TOKEN TAMPERING SIMULATION")
    print("=" * 50)
    
    # Split token
    header, payload, signature = jwt_token.split('.')
    
    # Decode current payload
    original_payload = decode_jwt_payload(jwt_token)
    print("Original Role:", original_payload.get('role'))
    
    # Try to modify payload
    try:
        # Add padding and decode
        payload += '=' * (4 - len(payload) % 4)
        payload_bytes = base64.urlsafe_b64decode(payload)
        payload_dict = json.loads(payload_bytes)
        
        # Modify role (attacker's goal)
        payload_dict['role'] = 'super_admin'
        payload_dict['permissions'] = {
            "read": ["plots", "zones", "users"],
            "write": ["plots", "zones", "users"]
        }
        
        # Re-encode payload
        new_payload_bytes = json.dumps(payload_dict).encode()
        new_payload = base64.urlsafe_b64encode(new_payload_bytes).decode().rstrip('=')
        
        # Create tampered token (with original signature)
        tampered_token = f"{header}.{new_payload}.{signature}"
        
        print("Tampered Role:", payload_dict.get('role'))
        print("Tampered Token:", tampered_token[:50] + "...")
        
        print("\n❌ RESULT: Token signature verification will FAIL")
        print("   Server will reject this token as invalid")
        
    except Exception as e:
        print(f"Tampering failed: {e}")


def demonstrate_signature_importance():
    """Show why JWT signature is critical for security."""
    
    print("\n🛡️  SIGNATURE SECURITY IMPORTANCE")
    print("=" * 50)
    
    # Example: Create two tokens with same payload but different signatures
    header = '{"alg":"HS256","typ":"JWT"}'
    payload = '{"userId":"attacker","role":"super_admin","zone":"GSEZ"}'
    
    # Encode without signature
    header_b64 = base64.urlsafe_b64encode(header.encode()).decode().rstrip('=')
    payload_b64 = base64.urlsafe_b64encode(payload.encode()).decode().rstrip('=')
    
    print("Header:", header)
    print("Payload:", payload)
    print("\nWithout signature:")
    print(f"  {header_b64}.{payload_b64}.<NO_SIGNATURE>")
    
    print("\n❌ This token would be REJECTED because:")
    print("  1. Missing signature")
    print("  2. Cannot verify authenticity")
    print("  3. Anyone could create fake tokens")
    
    print("\n✅ Valid signature proves:")
    print("  1. Token was created by server with secret key")
    print("  2. Payload hasn't been tampered with")
    print("  3. Token is authentic and trusted")


def show_attack_mitigation():
    """Show how to mitigate JWT token theft."""
    
    print("\n🛡️  ATTACK MITIGATION STRATEGIES")
    print("=" * 50)
    
    print("🔒 PREVENT TOKEN THEFT:")
    print("  • Use HTTPS only (prevent network sniffing)")
    print("  • Store tokens securely (httpOnly cookies, not localStorage)")
    print("  • Implement CSP headers (prevent XSS)")
    print("  • Short token expiry (limit damage window)")
    print("  • Rotate tokens regularly")
    
    print("\n🚨 DETECT TOKEN ABUSE:")
    print("  • Monitor unusual API usage patterns")
    print("  • Track IP addresses per token")
    print("  • Log all authentication events")
    print("  • Alert on privilege escalation attempts")
    
    print("\n⚡ IMMEDIATE RESPONSE:")
    print("  • Token blacklisting/revocation")
    print("  • Force user re-authentication")
    print("  • Disable compromised accounts")
    print("  • Audit trail analysis")
    
    print("\n🔄 BETTER ALTERNATIVES:")
    print("  • Opaque tokens (no payload exposure)")
    print("  • Refresh token rotation")
    print("  • Multi-factor authentication")
    print("  • Session binding (IP, device fingerprinting)")


if __name__ == "__main__":
    # Example JWT from your system (this would be a real token)
    sample_jwt = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VySWQiOiJhZG1pbjAwMSIsInJvbGUiOiJzdXBlcl9hZG1pbiIsInpvbmUiOiJHU0VaIiwicGVybWlzc2lvbnMiOnsicmVhZCI6WyJwbG90cyIsInpvbmVzIiwidXNlcnMiXSwid3JpdGUiOlsicGxvdHMiLCJ6b25lcyIsInVzZXJzIl19LCJpYXQiOjE3MjA5NzI4MDAsImV4cCI6MTcyMTA1OTIwMH0.signature_placeholder"
    
    print("🎯 ARISE API JWT SECURITY ANALYSIS")
    print("=" * 60)
    print(f"Analyzing token: {sample_jwt[:50]}...")
    print()
    
    # Run analysis
    analyze_jwt_security(sample_jwt)
    simulate_token_tampering(sample_jwt)
    demonstrate_signature_importance()
    show_attack_mitigation()
    
    print("\n" + "=" * 60)
    print("🚨 CRITICAL FINDING: Your JWT payload is FULLY VISIBLE!")
    print("   Anyone with the token can see role, permissions, zone")
    print("   Consider implementing opaque tokens for better security")
    print("=" * 60)
