#!/bin/bash

echo "=== Testing Scores API ==="
curl -s http://localhost:4566/restapis/$(aws --endpoint-url=http://localhost:4566 apigatewayv2 get-apis --query 'Items[0].ApiId' --output text)/stages/\$default/scores | jq

echo ""
echo "=== Testing Standings API ==="
curl -s http://localhost:4566/restapis/$(aws --endpoint-url=http://localhost:4566 apigatewayv2 get-apis --query 'Items[0].ApiId' --output text)/stages/\$default/standings | jq