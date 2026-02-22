#!/bin/bash

# Test script for simulating Pub/Sub push notification
# This script sends the Polish client form data to the webhook endpoint

echo "🚀 Testing Pub/Sub webhook with Polish client form data..."

# Create the client form data in the new flat format
POLISH_FORM_DATA='{"data":{"name":"Anna Kowalska","email":"anna@example.com","phone":"+48 600 123 456","timeline":"6months","answers":{"podstawowe_0":"Nie","podstawowe_1":"Tak, potrzebne pozwolenie na budowe","podstawowe_20":"ok. 800 zl/m2","podstawowe_21":"Japandi, minimalizm","salon_0":"Naroznik rozkladany","salon_2":"65 cali","jadalnia_0":"6 osob, rozkladany","kuchnia_0":"Otwarta z wyspa","kuchnia_5":"Indukcja, okap wyspowy, lodowka side-by-side","lazienka_0":"Prysznic walk-in","lazienka_3":"Dwie umywalki nablatowe","hol_0":"Gres wielkogabarytowy","sypialnia_0":"180x200, z pojemnikiem","garderoba_0":"Otwarta z oswietleniem LED","gabinet_0":"Biurko 160cm, jedna osoba","pokoj_dziecka_0":"8 lat, lego i rysowanie"}},"source":"nextjs","timestamp":"2026-02-22T10:30:00.000Z","version":"1.0"}'

# Write to a temp file to avoid shell encoding issues
TMPFILE=$(mktemp /tmp/pubsub_msg_XXXXXX.json)
echo "$POLISH_FORM_DATA" > "$TMPFILE"

echo "📤 Publishing to Pub/Sub topic: form-submissions-topic"
echo ""

OUTPUT=$(gcloud pubsub topics publish form-submissions-topic \
  --project=alicja-kobialka \
  --message="$(cat $TMPFILE)" 2>&1)

rm -f "$TMPFILE"

if echo "$OUTPUT" | grep -q "messageIds"; then
    MSG_ID=$(echo "$OUTPUT" | grep -oE '[0-9]{10,}')
    echo "✅ Message published successfully!"
    echo "📊 Message ID: $MSG_ID"
    echo "🔍 Check Cloud Run logs to see the processing progress:"
    echo "   gcloud logging tail 'resource.type=cloud_run_revision AND resource.labels.service_name=interior-ai-service' --project=alicja-kobialka --format='value(textPayload)'"
else
    echo "❌ Failed to publish message:"
    echo "$OUTPUT"
fi 