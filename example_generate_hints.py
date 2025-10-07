#!/usr/bin/env python3
"""
Example script to generate hints for new persons using the SpyGame API.

Usage:
    python example_generate_hints.py

Make sure the Flask app is running first: python app.py
"""

import requests
import json

# API endpoint (adjust if running on a different host/port)
API_URL = "http://localhost:5000/generate_hints"

# List of Wikipedia URLs to process
persons_to_add = [
    {
        "url": "https://es.wikipedia.org/wiki/Ada_Lovelace",
        "wikidata_id": "Q7259"
    },
    {
        "url": "https://es.wikipedia.org/wiki/Isaac_Newton",
        "wikidata_id": "Q8000"
    },
    {
        "url": "https://es.wikipedia.org/wiki/Frida_Kahlo",
        "wikidata_id": "Q5588"
    }
]

def generate_hints(url, wikidata_id=None):
    """
    Call the /generate_hints endpoint to create hints for a person.
    
    Args:
        url: Wikipedia URL of the person
        wikidata_id: Optional Wikidata ID
        
    Returns:
        dict: Response from the API
    """
    payload = {"url": url}
    if wikidata_id:
        payload["wikidata_id"] = wikidata_id
    
    try:
        response = requests.post(API_URL, json=payload)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        return {"status": "error", "message": str(e)}

if __name__ == "__main__":
    print("SpyGame Hint Generator")
    print("=" * 60)
    print(f"\nGenerating hints for {len(persons_to_add)} persons...\n")
    
    for person_data in persons_to_add:
        url = person_data["url"]
        wikidata_id = person_data.get("wikidata_id")
        
        print(f"Processing: {url}")
        result = generate_hints(url, wikidata_id)
        
        if result.get("status") == "success":
            print(f"  ✓ Success: {result.get('message')}")
            print(f"  - Person: {result.get('person')}")
            print(f"  - Hints generated: {result.get('hints_count')}")
        else:
            print(f"  ✗ Error: {result.get('message')}")
        
        print()
    
    print("=" * 60)
    print("\nDone! The persons are now available in the game.")
    print("Start a new game to play with the newly added persons!")
