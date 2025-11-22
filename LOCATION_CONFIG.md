# 🌍 Location Configuration Guide

This trading bot can work with **any city in the world**! The location determines which city's data (weather, air quality, flights) is used for trading signals.

## Quick Start: Change Location in 30 Seconds

### Option 1: Edit Constants File (Recommended)

Open `src/utils/constants.py` and change line 13:

```python
ACTIVE_LOCATION = "MUNICH"  # Change this to switch locations!
```

**Available Locations:**
- `"MUNICH"` - Munich, Germany (default for IMC Challenge)
- `"LONDON"` - London, United Kingdom
- `"NEW_YORK"` - New York, United States
- `"TOKYO"` - Tokyo, Japan
- `"SINGAPORE"` - Singapore
- `"PARIS"` - Paris, France
- `"HONG_KONG"` - Hong Kong
- `"SYDNEY"` - Sydney, Australia

**Example:**
```python
ACTIVE_LOCATION = "LONDON"  # Now trading with London data!
```

### Option 2: Edit Config File

Open `config.yaml` and modify the `location` section:

```yaml
location:
  city: London
  country: UK
  coordinates:
    lat: 51.5074
    lon: -0.1278
  airport_code: LHR
  timezone: Europe/London
```

## Add Your Own Custom Location

Want to trade with data from a city not in the presets? Easy!

### Step 1: Add to Constants File

Edit `src/utils/constants.py` and add your city to the `LOCATIONS` dictionary:

```python
LOCATIONS: Dict[str, Dict[str, Any]] = {
    # ... existing locations ...
    
    "YOUR_CITY": {
        "city": "Your City Name",
        "country": "XX",  # 2-letter country code
        "coordinates": {
            "lat": 12.3456,  # Your city's latitude
            "lon": 78.9012,  # Your city's longitude
        },
        "airport_code": "ABC",  # Nearest major airport code
        "timezone": "Region/City",  # IANA timezone
    },
}
```

### Step 2: Activate Your Location

```python
ACTIVE_LOCATION = "YOUR_CITY"
```

### Step 3: Done! 🎉

The bot will automatically:
- Fetch weather data for your city
- Get air quality data for your coordinates
- Track flights around your city's airport
- Generate trading signals based on your city's data

## How to Find Coordinates

1. **Google Maps**: Right-click on your city → Click coordinates to copy
2. **OpenWeatherMap**: Search your city at https://openweathermap.org/
3. **Wikipedia**: Most city pages list coordinates

## How to Find Airport Code

Search "[Your City] airport code" or check https://www.iata.org/

## How to Find Timezone

Check https://en.wikipedia.org/wiki/List_of_tz_database_time_zones

## Testing Your Configuration

After changing the location, verify it works:

```bash
python -c "from src.utils.constants import get_active_location; print(get_active_location())"
```

You should see your city's configuration printed.

## Why Location Matters

The trading bot discovers correlations between city data and market movements:

- **Weather**: Temperature, humidity, wind → affects energy, retail, tourism
- **Air Quality**: Pollution levels → affects health, transportation, regulations
- **Flights**: Airport activity → affects travel, business, logistics

Different cities have different patterns, creating unique trading opportunities!

## Pro Tips

1. **Start with Munich** for the IMC Challenge (it's optimized for this)
2. **Test multiple cities** to find the strongest correlations
3. **Major financial hubs** (London, New York, Tokyo) often have better data quality
4. **Coastal cities** may show stronger weather correlations
5. **Hub airports** (Singapore, Dubai) provide richer flight data

## Troubleshooting

**"Location not found" error?**
- Check spelling in `ACTIVE_LOCATION`
- Make sure location exists in `LOCATIONS` dictionary

**No data being fetched?**
- Verify coordinates are correct (latitude: -90 to 90, longitude: -180 to 180)
- Check your OpenWeatherMap API key in `.env`

**Flight data empty?**
- Verify airport code is correct
- Some smaller airports may have limited data

## Need Help?

Check the main README.md or configuration documentation in `docs/`.
