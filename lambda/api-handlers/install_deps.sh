#!/bin/bash
# Install Python dependencies for Lambda function

# Create a temporary directory for dependencies
DEPS_DIR="./dependencies"
rm -rf $DEPS_DIR
mkdir -p $DEPS_DIR

# Install dependencies
pip install -t $DEPS_DIR -r requirements.txt

# Copy function code
cp lambda_function.py $DEPS_DIR/
cp -r dotenv $DEPS_DIR/ 2>/dev/null || true

echo "Dependencies installed to $DEPS_DIR"
echo "Contents:"
ls -la $DEPS_DIR