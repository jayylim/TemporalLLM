#!/bin/bash
# Reads transactions and applies rules from a config file to generate an audit report.

CONFIG_FILE="/app/config/anomaly_definitions.json"
DATA_FILE="/app/data/transactions.csv"
REPORT_FILE="/app/output/audit_report.md"

if [ ! -f "$CONFIG_FILE" ] || [ ! -f "$DATA_FILE" ]; then
    echo "Error: Missing config or data file." >&2
    exit 1
fi

THRESHOLD=$(jq -r '.high_value_threshold' "$CONFIG_FILE")
UNUSUAL_CAT=$(jq -r '.unusual_category' "$CONFIG_FILE")

echo "# Audit Report - $(date)" > "$REPORT_FILE"
echo "" >> "$REPORT_FILE"
echo "## Flagged Transactions" >> "$REPORT_FILE"
echo "" >> "$REPORT_FILE"

FLAGGED_COUNT=0
# Read CSV, skipping header
tail -n +2 "$DATA_FILE" | while IFS=, read -r timestamp amount category flagged; do
    REASON=""
    # Check for high value
    if (( $(echo "$amount > $THRESHOLD" | bc -l) )); then
        REASON="High value transaction"
    fi
    # Check for unusual category
    if [ "$category" == "$UNUSUAL_CAT" ]; then
        REASON="Transaction in unusual category"
    fi

    if [ -n "$REASON" ]; then
        echo "- **Timestamp:** ${timestamp} | **Amount:** ${amount} | **Category:** ${category} | **Reason:** ${REASON}" >> "$REPORT_FILE"
        FLAGGED_COUNT=$((FLAGGED_COUNT + 1))
    fi
done

echo "" >> "$REPORT_FILE"
echo "---" >> "$REPORT_FILE"
echo "**Total Anomalies Found:** $FLAGGED_COUNT" >> "$REPORT_FILE"

echo "Audit complete. Report generated at ${REPORT_FILE} with ${FLAGGED_COUNT} anomalies found."
exit 0