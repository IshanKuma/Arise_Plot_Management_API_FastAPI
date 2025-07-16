"""
Secret Key Management Utility
============================

This utility helps generate and verify bcrypt hashes for user secret keys.
Use this to create proper hashed secrets for your users.
"""
import bcrypt
import getpass


def hash_secret_key(secret_key: str) -> str:
    """Generate bcrypt hash for a secret key."""
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(secret_key.encode('utf-8'), salt)
    return hashed.decode('utf-8')


def verify_secret_key(secret_key: str, hashed_secret: str) -> bool:
    """Verify a secret key against its hash."""
    try:
        return bcrypt.checkpw(secret_key.encode('utf-8'), hashed_secret.encode('utf-8'))
    except Exception:
        return False


def generate_user_secrets():
    """Interactive utility to generate user secret hashes."""
    print("🔑 Secret Key Hash Generator")
    print("=" * 40)
    
    default_users = {
        "admin001": "admin-secret-key-2025",
        "zone001": "zone-admin-secret-2025", 
        "user001": "normal-user-secret-2025"
    }
    
    print("\n📋 Default User Secrets:")
    print("-" * 30)
    
    generated_hashes = {}
    
    for user_id, default_secret in default_users.items():
        print(f"\nUser: {user_id}")
        print(f"Default secret: {default_secret}")
        
        use_default = input("Use default secret? (y/n): ").strip().lower()
        
        if use_default == 'y':
            secret = default_secret
        else:
            secret = getpass.getpass(f"Enter secret for {user_id}: ")
        
        # Generate hash
        hashed = hash_secret_key(secret)
        generated_hashes[user_id] = hashed
        
        print(f"Generated hash: {hashed}")
        
        # Verify the hash works
        if verify_secret_key(secret, hashed):
            print("✅ Hash verification successful!")
        else:
            print("❌ Hash verification failed!")
    
    print("\n" + "=" * 50)
    print("📝 CODE FOR AuthService._user_secrets:")
    print("=" * 50)
    print("_user_secrets: Dict[str, str] = {")
    for user_id, hashed in generated_hashes.items():
        print(f'    "{user_id}": "{hashed}",')
    print("}")
    
    return generated_hashes


def test_secret_verification():
    """Test secret verification with known values."""
    print("\n🧪 Testing Secret Verification")
    print("=" * 40)
    
    # Test with actual hashes from your system
    test_cases = [
        ("admin001", "admin-secret-key-2025", "$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj56ZUJyTUES"),
        ("zone001", "zone-admin-secret-2025", "$2b$12$B8VHhAuB8Q7.tF6SrN8gJOGJZb0J3N5r6H8kD2VmR9Q3P7L5X1Y2Z"),
        ("user001", "normal-user-secret-2025", "$2b$12$C9WIhBvC9R8.uG7TsO9hKPHJZc1K4O6s7I9lE3WnS0R4Q8M6Y2Z3A")
    ]
    
    for user_id, secret, stored_hash in test_cases:
        result = verify_secret_key(secret, stored_hash)
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{user_id}: {status}")


def generate_new_hash():
    """Generate a hash for a new secret."""
    print("\n🆕 Generate New Secret Hash")
    print("=" * 40)
    
    user_id = input("Enter user ID: ").strip()
    secret = getpass.getpass("Enter secret key: ")
    
    if len(secret) < 8:
        print("❌ Secret must be at least 8 characters long!")
        return
    
    hashed = hash_secret_key(secret)
    print(f"\nUser ID: {user_id}")
    print(f"Secret Hash: {hashed}")
    
    # Verify
    if verify_secret_key(secret, hashed):
        print("✅ Hash verification successful!")
        print(f'\nAdd this to _user_secrets:\n"{user_id}": "{hashed}",')
    else:
        print("❌ Hash verification failed!")


if __name__ == "__main__":
    print("🔐 ARISE API - Secret Key Management Utility")
    print("=" * 60)
    
    while True:
        print("\nOptions:")
        print("1. Generate default user secret hashes")
        print("2. Test existing secret verification") 
        print("3. Generate new user secret hash")
        print("4. Exit")
        
        choice = input("\nSelect option (1-4): ").strip()
        
        if choice == "1":
            generate_user_secrets()
        elif choice == "2":
            test_secret_verification()
        elif choice == "3":
            generate_new_hash()
        elif choice == "4":
            print("👋 Goodbye!")
            break
        else:
            print("❌ Invalid option. Please choose 1-4.")
