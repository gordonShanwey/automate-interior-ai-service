#!/bin/bash

# Simple test script for the /test endpoint
# This sends the Polish form data directly without Pub/Sub wrapping

echo "🧪 Testing simple webhook endpoint with Polish client form data..."

# Send the request to the test endpoint
echo "📤 Sending request to http://localhost:8000/webhooks/test..."
echo ""

# Use curl with a properly escaped JSON payload
RESPONSE=$(curl -s -w "\nHTTP_STATUS:%{http_code}" \
  -X POST \
  -H "Content-Type: application/json" \
  -d '{"values":["2025-03-19T21:12:56.064Z","magdalenagrzesik1991@gmail.com","Tak","Magdalena wolak","magdalenagrzesik1991@gmail.com",730730314,"Ul. Goszczyńskiego","Mieszkanie w bloku","W stanie deweloperskim",97,"zamawiający","2026 lipiec",3,"5-38","Praca w domu","Miejsce do czytania, Miejsca do oglądania TV, projektor w sypialni","Nie","Nie","Tak","Św","Terrarium","Jesion i Dąb","Jodełka francuska","Minimalistyczny, Modern Classic/Klasyczny, Wabi sabi/ Japandi","Nie","Maksymalne wykorzystanie przestrzeni, Otwarta przestrzeń, Duża ilość do przechowywania, Wydzielenie stref, Minimalistyczne rozwiązania","Tak, projektujemy wszystkie pomieszczenia","Tak","Nie","Tak","Panel winylowy układany w jodełkę","W palecie białej","Zależy nam na kolorach neutralnych, ziemi, drewna","Nie","Tak, w salonie, centrala na dachu budynku","Nie","Za mała kuchnia","W sypialni musi znaleźć się miejsce do pracy","W zależności od pomieszczenia podobają nam się firany i zasłony z maskownice, rolety oraz żaluzje","Drewno naturalne","Neutralne światło",5,"Tak","L, Z wyspą","Szuflady z pełnym wysuwem, Wysokie szafki do sufitu, Ukryte gniazdka w blacie","Tak","Nie, tylko blat roboczy i hokery","Płyta indukcyjna","Piekarnik, Mikrofalówka, Lodówka na wino, Zmywarka, Ekspres wolnostojący, Lodówka, Dodatkowo przewidzieć miejsce na toster, robot kuchenny, sokowirówka itp.","Wszystkie sprzęty będziemy kupować nowe, oprócz ekspresu do kawy","Tak, ekspres chodź może on być w zabudowie wysuwanej","przeważnie 1, sporadycznie 2","Wolnostojąca szklany front albo w zabudowie","W słupku","Jednokomorowy bez ociekacza","spiek lub kamień","Stół dla 8 osób","Zabudowany","powyżej 90 cm","Nie","Nie","85\"","soundbar","Nie","kominek elektryczny z parą wodną","Nie","Nie","Szafa wolnostojąca w holu","Szafa na pełną wysokość pomieszczenia, Siedzisko wolnostojące, Duże lustro, Konsola na klucze","Skrzydłowe","Półki, Drążki, Szuflady, Wysuwane organizery na dodatki","Torebki, Ubrania, Ubrania o niestandardowej długości (np. bardzo długie płaszcze), Płaszcze","","Część większej łazienki","Wanna wolnostojąca, Prysznic Walk-In, Prysznic z odpływem liniowym","Tak","Grzejnik","Tak","Tak","Prysznic z odpływem liniowym, Prysznic walk-in, WC, Umywalka, Kosze na pranie, Pralka, Suszarka","Grzejnik","Tak","Tak","Nie",8,"Nie","","","","","","","","","","","","","","","","","","","","","","","","","","","","","","Tak",6,"Nie","Miejsce do nauki/biurko, Łóżko, Szafa, Wyznaczona strefa do zabawy, Miejsce na zabawki","Łóżko zwykłe/pojedyncze","90x200","Nie","","","","","","Nie","","","","","Nie","","","Nie","","","","","","","","Nie","","","","","","250 000 na wszystko","","","Drzewo oliwne w salonie","","","","","","","",""]}' \
  http://localhost:8000/webhooks/test)

# Extract HTTP status and response body
HTTP_STATUS=$(echo "$RESPONSE" | grep "HTTP_STATUS:" | cut -d: -f2)
RESPONSE_BODY=$(echo "$RESPONSE" | sed '/HTTP_STATUS:/d')

echo "📥 Response Status: $HTTP_STATUS"
echo "📄 Response Body:"
echo "$RESPONSE_BODY" | python -m json.tool 2>/dev/null || echo "$RESPONSE_BODY"
echo ""

if [ "$HTTP_STATUS" = "200" ]; then
    echo "✅ Success! Test data was received and queued for processing."
    echo "🔍 Check the server logs to see the processing progress."
else
    echo "❌ Error! HTTP status: $HTTP_STATUS"
fi 