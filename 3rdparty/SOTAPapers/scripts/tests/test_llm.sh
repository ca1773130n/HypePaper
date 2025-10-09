#!/bin/bash
curl http://localhost:10002/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "messages": [{"role": "user", "content": "Test"}],
    "model": "mistral-7b-instruct-v0.1"
  }'
 
