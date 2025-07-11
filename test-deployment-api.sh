#!/bin/bash

# Test Deployment API endpoints

API_URL="http://localhost:8000/api/v1"
TOKEN="your-auth-token-here"  # Replace with actual token

echo "Testing Deployment API..."

# 1. Get trained models
echo -e "\n1. Getting trained models:"
curl -X GET "$API_URL/deployment/models/trained" \
  -H "Authorization: Bearer $TOKEN" | jq '.'

# 2. Get all deployments
echo -e "\n2. Getting all deployments:"
curl -X GET "$API_URL/deployment/" \
  -H "Authorization: Bearer $TOKEN" | jq '.'

# 3. Deploy a model (example)
echo -e "\n3. Deploying a model:"
curl -X POST "$API_URL/deployment/deploy" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "model_id": "model-1",
    "type": "api",
    "config": {}
  }' | jq '.'

# 4. Test a deployment (example deployment ID)
echo -e "\n4. Testing a deployment:"
DEPLOYMENT_ID="your-deployment-id"  # Replace with actual deployment ID
curl -X POST "$API_URL/deployment/$DEPLOYMENT_ID/test" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "test_input": {
      "text": "I had a terrible experience with your product"
    }
  }' | jq '.'

echo -e "\nDeployment API test complete!" 