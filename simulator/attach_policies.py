#!/usr/bin/env python3
"""
Attach the correct IoT policy to all machine certificates
"""

import json
import subprocess

def run_aws_command(command):
    """Run AWS CLI command and return result"""
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True, check=True)
        return result.stdout if result.stdout.strip() else ""
    except subprocess.CalledProcessError as e:
        print(f"Error running command: {command}")
        print(f"Error: {e.stderr}")
        return None

def get_certificate_arn_for_machine(machine_id):
    """Get certificate ARN for a specific machine from AWS IoT"""
    try:
        # List all certificates and find the one for this machine
        certs_response = run_aws_command("aws iot list-certificates")
        if not certs_response:
            return None
            
        certs_data = json.loads(certs_response)
        
        for cert in certs_data['certificates']:
            # Get certificate details to find the one for this machine
            cert_id = cert['certificateId']
            cert_details = run_aws_command(f"aws iot describe-certificate --certificate-id {cert_id}")
            if cert_details:
                cert_detail_data = json.loads(cert_details)
                # Check if this certificate is attached to the machine thing
                principals_response = run_aws_command(f"aws iot list-thing-principals --thing-name {machine_id}")
                if principals_response:
                    principals_data = json.loads(principals_response)
                    if cert['certificateArn'] in principals_data.get('principals', []):
                        return cert['certificateArn']
        
        return None
    except Exception as e:
        print(f"Error getting certificate ARN for {machine_id}: {e}")
        return None

def attach_policy_to_certificate(cert_arn, machine_id):
    """Attach the IoT policy to a certificate"""
    policy_name = "gym-pulse-device-Policy"
    command = f'aws iot attach-principal-policy --policy-name "{policy_name}" --principal "{cert_arn}"'
    
    result = run_aws_command(command)
    if result is not None:
        print(f"✅ Attached policy to certificate for {machine_id}")
        return True
    else:
        print(f"❌ Failed to attach policy to certificate for {machine_id}")
        return False

def main():
    """Main function to attach policies to all machine certificates"""
    
    # Load machine configuration
    with open("config/machines.json", "r") as f:
        config = json.load(f)
    
    # Collect all machine IDs
    machine_ids = []
    for branch in config['branches']:
        for machine in branch['machines']:
            machine_ids.append(machine['machineId'])
    
    print(f"Attaching policies for {len(machine_ids)} machines...")
    
    # Attach policy to each machine certificate
    success_count = 0
    for machine_id in machine_ids:
        print(f"Processing {machine_id}...")
        cert_arn = get_certificate_arn_for_machine(machine_id)
        
        if cert_arn:
            if attach_policy_to_certificate(cert_arn, machine_id):
                success_count += 1
        else:
            print(f"❌ Could not find certificate ARN for {machine_id}")
    
    print(f"\n✅ Successfully attached policies for {success_count}/{len(machine_ids)} machines")

if __name__ == "__main__":
    main()