import os
import asyncio
from dotenv import load_dotenv

from pyinjective.core.network import Network
from pyinjective.async_client import AsyncClient
from pyinjective.wallet import PrivateKey
import grpc

async def main():
    load_dotenv()
    private_key_hex = os.getenv("INJ_PRIVATE_KEY")
    if not private_key_hex:
        print("🔴 ERROR: INJ_PRIVATE_KEY not found in .env file.")
        return

    print("Credentials loaded successfully.")
    
    network = Network.testnet()

    # Initialize client (we'll close it explicitly)
    client = AsyncClient(network)
    try:
        priv_key = PrivateKey.from_hex(private_key_hex)
        address = priv_key.to_public_key().to_address()
        subaccount_id = address.get_subaccount_id(index=0)
        
        print(f"Connecting to Injective Testnet with address: {address.to_acc_bech32()}")

        # Fetch and show on‑chain (bank) balance first
        bank_response = await client.fetch_bank_balances(address=address.to_acc_bech32())
        print("\n--- On‑chain Bank Balances ---")
        bank_inj = "0"
        for b in bank_response["balances"]:
            if b.denom == "inj":
                bank_inj = b.amount
                break
        print(f"INJ in wallet: {bank_inj}")

        # Attempt to fetch exchange (sub‑account) balances
        try:
            exchange_response = await client.fetch_subaccount_balances_list(subaccount_id=subaccount_id)

            print("\n--- Exchange (Sub‑account) Balances ---")

            inj_balance = "0"
            for balance in exchange_response["balances"]:
                if balance.denom == "inj":
                    inj_balance = balance.totalBalance
                    break

            if float(inj_balance) > 0:
                print("✅ Exchange sub‑account found!")
                print(f"Available INJ on exchange: {inj_balance}")
            else:
                print("Exchange sub‑account exists but holds zero INJ.")
        except Exception as sub_e:
            if "object not found" in str(sub_e):
                print("\n--- Exchange (Sub‑account) Balances ---")
                print("No exchange sub‑account yet (deposit once to create it).")
            else:
                raise sub_e
    finally:
        # The current AsyncClient version has no .close(); let the process exit cleanly.
        pass


if __name__ == "__main__":
    asyncio.run(main())