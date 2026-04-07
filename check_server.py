#!/usr/bin/env python3
"""
Server diagnostics script
"""
import socket
import sys

def check_port(host, port):
    """Check if port is open"""
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(2)
    try:
        result = sock.connect_ex((host, port))
        sock.close()
        return result == 0
    except Exception as e:
        print(f"Error checking port: {e}")
        return False

def check_mongodb():
    """Check MongoDB connection"""
    try:
        from pymongo import MongoClient
        client = MongoClient("mongodb://localhost:27017", serverSelectionTimeoutMS=2000)
        client.admin.command('ping')
        print("✅ MongoDB is running")
        return True
    except Exception as e:
        print(f"❌ MongoDB error: {e}")
        return False

def check_env_file():
    """Check .env file exists"""
    import os
    env_path = ".env"
    if os.path.exists(env_path):
        print(f"✅ .env file exists")
        # Read and check required variables
        with open(env_path, 'r') as f:
            content = f.read()
            required = ['BOT_API_TOKEN', 'MONGODB_URL', 'SECRET_KEY']
            for var in required:
                if var in content:
                    print(f"  ✅ {var} found")
                else:
                    print(f"  ❌ {var} missing")
        return True
    else:
        print(f"❌ .env file not found")
        return False

def main():
    print("=" * 60)
    print("Server Diagnostics")
    print("=" * 60)
    
    # Check .env
    print("\n1. Checking .env file...")
    check_env_file()
    
    # Check MongoDB
    print("\n2. Checking MongoDB...")
    check_mongodb()
    
    # Check if server port is open
    print("\n3. Checking server port 8000...")
    if check_port('localhost', 8000):
        print("✅ Server is running on port 8000")
    else:
        print("❌ Server is NOT running on port 8000")
        print("\nTo start the server, run:")
        print("  python main.py")
    
    # Check common ports
    print("\n4. Checking other common ports...")
    ports = {
        27017: "MongoDB",
        8000: "Alternative API port",
        8080: "Alternative API port",
    }
    for port, service in ports.items():
        if check_port('localhost', port):
            print(f"✅ {service} (port {port}) is running")
        else:
            print(f"❌ {service} (port {port}) is not running")
    
    print("\n" + "=" * 60)
    print("Diagnostics complete")
    print("=" * 60)

if __name__ == "__main__":
    main()
