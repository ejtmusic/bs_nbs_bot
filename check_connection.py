import asyncio
import os
from dotenv import load_dotenv

from pyinjective.async_client import AsyncClient
from pyinjective.core.network import Network
from pyinjective.wallet import PrivateKey

async def main():
    # Load environment variables from .env file
    load_dotenv()
    private_key_hex = os.getenv("INJ_PRIVATE_KEY")

    if not private_key_hex:
        print("ERROR: INJ_PRIVATE_KEY not found in .env file.")
        print("Please ensure your .env file is created and has the correct variable.")
        return

    print("--- Connection Test ---")
    try:
        # Set up the network and client for the TESTNET
        network = Network.testnet()
        client = AsyncClient(network)

        # Load private key from hex
        private_key = PrivateKey.from_hex(private_key_hex)
        pub_key = private_key.to_public_key()
        address = pub_key.to_address()
        
        print(f"Successfully loaded wallet.")
        print(f"Your derived Injective Address is: {address.to_acc_bech32()}")

        # Fetch account details from the testnet (CORRECTED METHOD)
        account = await client.fetch_account(address=address.to_acc_bech32())
        print("\nSUCCESS: Successfully connected to the Injective Testnet!")
        print("Your wallet is configured correctly.")

    except Exception as e:
        print(f"\nFAILED: An error occurred.")
        print(f"Error details: {e}")

if __name__ == "__main__":
    asyncio.run(main())