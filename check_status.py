"""Quick status check for the trading bot."""
import os
from dotenv import load_dotenv

load_dotenv()

print("=" * 60)
print("IMC TRADING BOT - STATUS CHECK")
print("=" * 60)

# Check environment variables
print("\n📋 Environment Variables:")
print(f"  IMC_EXCHANGE_URL: {os.getenv('IMC_EXCHANGE_URL', 'NOT SET')}")
print(f"  IMC_USERNAME: {os.getenv('IMC_USERNAME', 'NOT SET')}")
print(f"  IMC_PASSWORD: {'***' if os.getenv('IMC_PASSWORD') else 'NOT SET'}")
print(f"  OPENWEATHER_API_KEY: {'***' if os.getenv('OPENWEATHER_API_KEY') else 'NOT SET'}")

# Check exchange connectivity
print("\n🔌 Exchange Connectivity:")
import asyncio
from src.exchange.imc_client import IMCExchangeClient

async def check_exchange():
    try:
        async with IMCExchangeClient(
            os.getenv('IMC_EXCHANGE_URL'),
            os.getenv('IMC_USERNAME'),
            os.getenv('IMC_PASSWORD')
        ) as client:
            products = await client.get_products()
            print(f"  ✅ Connected to exchange")
            print(f"  ✅ {len(products)} instruments available")
            return True
    except Exception as e:
        print(f"  ❌ Connection failed: {e}")
        return False

connected = asyncio.run(check_exchange())

# Summary
print("\n" + "=" * 60)
if connected:
    print("✅ READY TO TRADE")
    print("\nNext steps:")
    print("  1. Wait for market to open")
    print("  2. Run: python src/main.py --mode paper")
    print("  3. Monitor logs in logs/ directory")
else:
    print("❌ NOT READY - Fix connection issues")
print("=" * 60)
