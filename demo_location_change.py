#!/usr/bin/env python3
"""
Demo script showing how easy it is to change trading locations.

This demonstrates the location-agnostic design of the trading bot.
"""

from src.utils.constants import (
    LOCATIONS,
    get_active_location,
    get_location_string,
    get_coordinates,
    get_bounding_box,
)


def main():
    """Demonstrate location configuration."""
    
    print("=" * 70)
    print("🌍 IMC Trading Bot - Location Configuration Demo")
    print("=" * 70)
    print()
    
    # Show current active location
    print("📍 CURRENT ACTIVE LOCATION:")
    print("-" * 70)
    active = get_active_location()
    print(f"  City:         {active['city']}")
    print(f"  Country:      {active['country']}")
    print(f"  Coordinates:  {active['coordinates']['lat']:.4f}°N, {active['coordinates']['lon']:.4f}°E")
    print(f"  Airport:      {active['airport_code']}")
    print(f"  Timezone:     {active['timezone']}")
    print(f"  API String:   {get_location_string()}")
    print()
    
    # Show bounding box for flights
    bbox = get_bounding_box()
    print(f"  Flight Area:  [{bbox[0]:.2f}, {bbox[1]:.2f}, {bbox[2]:.2f}, {bbox[3]:.2f}]")
    print()
    
    # Show all available locations
    print("🗺️  AVAILABLE LOCATIONS:")
    print("-" * 70)
    for key, loc in LOCATIONS.items():
        marker = "✓" if key == "MUNICH" else " "
        print(f"  [{marker}] {key:15s} - {loc['city']:15s} ({loc['country']})")
    print()
    
    # Show how to change
    print("🔧 HOW TO CHANGE LOCATION:")
    print("-" * 70)
    print("  1. Open: src/utils/constants.py")
    print("  2. Find: ACTIVE_LOCATION = \"MUNICH\"")
    print("  3. Change to any location above (e.g., \"LONDON\", \"TOKYO\")")
    print("  4. Save and restart the bot")
    print()
    
    # Show how to add custom location
    print("➕ HOW TO ADD CUSTOM LOCATION:")
    print("-" * 70)
    print("  1. Open: src/utils/constants.py")
    print("  2. Add to LOCATIONS dictionary:")
    print("     \"YOUR_CITY\": {")
    print("         \"city\": \"Your City\",")
    print("         \"country\": \"XX\",")
    print("         \"coordinates\": {\"lat\": 12.34, \"lon\": 56.78},")
    print("         \"airport_code\": \"ABC\",")
    print("         \"timezone\": \"Region/City\",")
    print("     }")
    print("  3. Set: ACTIVE_LOCATION = \"YOUR_CITY\"")
    print()
    
    print("=" * 70)
    print("✨ The bot will automatically fetch data for your chosen location!")
    print("=" * 70)


if __name__ == "__main__":
    main()
