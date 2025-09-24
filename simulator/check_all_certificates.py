#!/usr/bin/env python3
"""
Check all certificates for IoT policy attachments
"""
import os
import subprocess
import json

def get_certificate_id_from_file(cert_file):
    """Extract certificate ID from PEM file using fingerprint"""
    try:
        cmd = f"openssl x509 -in {cert_file} -fingerprint -sha256 -noout"
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        if result.returncode == 0:
            fingerprint = result.stdout.strip().split('=')[1]
            # Remove colons and convert to lowercase to match AWS format
            cert_id = fingerprint.replace(':', '').lower()
            return cert_id
        return None
    except Exception as e:
        print(f"Error processing {cert_file}: {e}")
        return None

def check_certificate_policies(cert_id):
    """Check if certificate has IoT policies attached"""
    try:
        cmd = f"aws iot list-principal-policies --principal arn:aws:iot:ap-east-1:168860953292:cert/{cert_id}"
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        if result.returncode == 0:
            policies = json.loads(result.stdout)
            return policies.get('policies', [])
        return []
    except Exception as e:
        print(f"Error checking policies for {cert_id}: {e}")
        return []

def main():
    cert_dir = "certs"
    print("Checking all certificates for IoT policy attachments...\n")

    # Find all .cert.pem files
    cert_files = []
    for file in os.listdir(cert_dir):
        if file.endswith('.cert.pem'):
            cert_files.append(os.path.join(cert_dir, file))

    cert_files.sort()

    certificates_with_policy = []
    certificates_without_policy = []

    for cert_file in cert_files:
        print(f"Checking {cert_file}...")
        cert_id = get_certificate_id_from_file(cert_file)

        if cert_id:
            policies = check_certificate_policies(cert_id)
            if policies:
                print(f"  ✅ Has policies: {[p['policyName'] for p in policies]}")
                certificates_with_policy.append((cert_file, cert_id, policies))
            else:
                print(f"  ❌ No policies attached")
                certificates_without_policy.append((cert_file, cert_id))
        else:
            print(f"  ⚠️  Could not extract certificate ID")

        print()

    print("=" * 60)
    print("SUMMARY:")
    print(f"Certificates WITH policy: {len(certificates_with_policy)}")
    for cert_file, cert_id, policies in certificates_with_policy:
        print(f"  - {cert_file}: {cert_id}")

    print(f"\nCertificates WITHOUT policy: {len(certificates_without_policy)}")
    for cert_file, cert_id in certificates_without_policy:
        print(f"  - {cert_file}: {cert_id}")

if __name__ == "__main__":
    main()