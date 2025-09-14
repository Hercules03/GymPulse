#!/usr/bin/env python3
"""
Create individual AWS IoT certificates for each gym machine
"""

import json
import subprocess
import os
from pathlib import Path

def run_aws_command(command):
    """Run AWS CLI command and return JSON result"""
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True, check=True)
        return json.loads(result.stdout) if result.stdout.strip() else None
    except subprocess.CalledProcessError as e:
        print(f"Error running command: {command}")
        print(f"Error: {e.stderr}")
        return None

def create_certificate_for_machine(machine_id):
    """Create certificate and thing for a specific machine"""
    print(f"Creating certificate for {machine_id}...")
    
    # Create certificate and key pair
    cert_response = run_aws_command("aws iot create-keys-and-certificate --set-as-active")
    if not cert_response:
        print(f"Failed to create certificate for {machine_id}")
        return False
    
    cert_arn = cert_response['certificateArn']
    cert_id = cert_response['certificateId']
    
    # Save certificate files
    cert_dir = Path("certs")
    cert_dir.mkdir(exist_ok=True)
    
    # Write certificate
    with open(cert_dir / f"{machine_id}.cert.pem", "w") as f:
        f.write(cert_response['certificatePem'])
    
    # Write private key
    with open(cert_dir / f"{machine_id}.private.key", "w") as f:
        f.write(cert_response['keyPair']['PrivateKey'])
    
    # Write public key (optional)
    with open(cert_dir / f"{machine_id}.public.key", "w") as f:
        f.write(cert_response['keyPair']['PublicKey'])
    
    # Create IoT Thing
    thing_response = run_aws_command(f'aws iot create-thing --thing-name "{machine_id}"')
    if not thing_response:
        print(f"Failed to create thing for {machine_id}")
        return False
    
    # Attach certificate to thing
    attach_response = run_aws_command(f'aws iot attach-thing-principal --thing-name "{machine_id}" --principal "{cert_arn}"')
    
    # Attach policy to certificate (assumes policy already exists)
    policy_response = run_aws_command(f'aws iot attach-principal-policy --policy-name "GymMachinePolicy" --principal "{cert_arn}"')
    
    print(f"✅ Created certificate for {machine_id} (ID: {cert_id})")
    return True

def main():
    """Main function to create certificates for all machines"""
    
    # Load machine configuration
    with open("config/machines.json", "r") as f:
        config = json.load(f)
    
    # Collect all machine IDs
    machine_ids = []
    for branch in config['branches']:
        for machine in branch['machines']:
            machine_ids.append(machine['machineId'])
    
    print(f"Creating certificates for {len(machine_ids)} machines...")
    
    # Create certificates for each machine
    success_count = 0
    for machine_id in machine_ids:
        if create_certificate_for_machine(machine_id):
            success_count += 1
        else:
            print(f"❌ Failed to create certificate for {machine_id}")
    
    print(f"\n✅ Successfully created certificates for {success_count}/{len(machine_ids)} machines")
    
    if success_count > 0:
        print("\nNext steps:")
        print("1. Update simulator to use individual certificates")
        print("2. Restart simulator with new certificates")
        print("3. Verify all machines connect successfully")

if __name__ == "__main__":
    main()