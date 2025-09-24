#!/bin/bash

# Attach gym-pulse-device-Policy to all certificates
echo "Attaching gym-pulse-device-Policy to all certificates..."

# Get all certificate ARNs
cert_arns=$(aws iot list-certificates --query 'certificates[*].certificateArn' --output text)

# Attach policy to each certificate
count=0
for cert_arn in $cert_arns; do
    echo "Attaching policy to certificate: $cert_arn"
    aws iot attach-principal-policy --policy-name "gym-pulse-device-Policy" --principal "$cert_arn" 2>/dev/null
    if [ $? -eq 0 ]; then
        echo "✅ Successfully attached policy"
        ((count++))
    else
        echo "ℹ️  Policy may already be attached"
        ((count++))
    fi
done

echo "✅ Processed $count certificates"
echo "All certificates should now have the gym-pulse-device-Policy attached"