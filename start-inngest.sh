#!/bin/bash
echo "Starting Inngest Dev Server..."
npx inngest-cli@latest dev -u http://127.0.0.1:8000/api/inngest --no-discovery
