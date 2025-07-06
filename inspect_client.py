import asyncio
from pyinjective.async_client import AsyncClient
from pyinjective.constant import Network

async def main():
    """
    This script inspects the AsyncClient object and prints all of its
    available methods to solve our function name mystery.
    """
    print("--- Inspecting the pyinjective.async_client.AsyncClient object ---")
    
    network = Network.mainnet()
    client = AsyncClient(network, insecure=False) # Use the older insecure flag just in case

    print("\nAvailable methods:")
    
    # Get all attributes and methods, filter out the private ones (starting with '_')
    available_methods = [method for method in dir(client) if not method.startswith('_')]
    
    for method in sorted(available_methods):
        print(f"- {method}")
        
    print("\n--- Inspection Complete ---")

if __name__ == "__main__":
    asyncio.run(main())