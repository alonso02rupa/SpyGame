#!/bin/bash
# Example script to generate hints for a new person using the API

# Make sure the server is running first with: python app.py

# Example: Generate hints for Ada Lovelace
curl -X POST http://localhost:5000/generate_hints \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://es.wikipedia.org/wiki/Ada_Lovelace",
    "wikidata_id": "Q7259"
  }'

echo ""
echo ""

# Example: Generate hints for Isaac Newton
curl -X POST http://localhost:5000/generate_hints \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://es.wikipedia.org/wiki/Isaac_Newton"
  }'

echo ""
echo ""
echo "Hints have been generated and saved to the MongoDB 'hints' collection."
echo "You can now play the game and these persons will be available!"
