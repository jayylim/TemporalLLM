#!/bin/bash
echo "=== ENVIRONMENT DEBUG ==="
echo "Current directory: $(pwd)"
echo "Available files:"
ls -la
echo "=== CHECKING FOR LOG FILES ==="
if [ -f "run.log" ]; then
    echo "Found run.log:"
    cat run.log
else
    echo "No run.log found"
fi
echo "=== CSV FILE CHECK ==="
if [ -f "recipients.csv" ]; then
    echo "Recipients CSV exists:"
    head -3 recipients.csv
else
    echo "Recipients CSV missing"
fi
echo "=== BASH VERSION ==="
bash --version
echo "=== END DEBUG ==="