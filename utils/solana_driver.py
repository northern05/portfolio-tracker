import os
import subprocess
import logging
import time

import base58
from solana.rpc.api import Client
from solana.rpc.commitment import Confirmed
from solders.keypair import Keypair
from solders.message import MessageV0

from solders.pubkey import Pubkey
from solders.signature import Signature
import struct
import re

from solders.system_program import transfer, TransferParams
from solders.transaction import VersionedTransaction
from solders.transaction_status import UiCompiledInstruction

SYSTEM_PROGRAM_ID = Pubkey.from_string("11111111111111111111111111111111")
VALUE_TO_BUY_IN_SOL = float(0.0001)
class SolanaDriver:
    def __init__(self, rpc_url: str, config_path: str, agent_keypair: str):
        self.rpc_url = rpc_url
        self.config_path = config_path
        self.client = Client(rpc_url, commitment=Confirmed)
        self.fixed_fee_in_lamports = int(0.0001 * 10 ** 9)
        self.value_to_buy_in_lamports = int(VALUE_TO_BUY_IN_SOL * 10 ** 9)

        # Typescript depends
        self.agent_keypair = Keypair.from_json(agent_keypair)
        self.node_path = os.path.expanduser("~/.nvm/versions/node/v20.18.0/bin/node")
        self.ts_dir = "raydiumSwap"
        self.parse_pattern = r"txId: ([\w\d]+),\s*computed swap ([\d\.]+)\s*(\w+)\s*to\s*([\d\.]+)\s*(\w+),\s*fee:\s*([\d\.]+)"

    def validate_payment_transaction(self, signer: str, tx_signature: str):
        time.sleep(5)  # Transaction indexing in RPC
        sig = Signature.from_string(tx_signature)
        response = self.client.get_transaction(sig, max_supported_transaction_version=1)

        if not response or not response.value:
            raise ValueError("Transaction not found or invalid signature.")
        transaction_data = response.value.transaction.transaction.message
        system_program_index = transaction_data.account_keys.index(SYSTEM_PROGRAM_ID)
        try:
            source_index = transaction_data.account_keys.index(Pubkey.from_string(signer))
        except ValueError:
            raise ValueError("Provided transaction does not contain address of signer.")
        try:
            destination_index = transaction_data.account_keys.index(self.agent_keypair.pubkey())
        except ValueError:
            raise ValueError("Provided transaction does not contain address of agent in transfer instruction.")
        transfer_instruction_data = struct.pack("<I Q", 2, self.fixed_fee_in_lamports)
        expected_transfer_instruction_data = base58.b58encode(transfer_instruction_data).decode('utf-8')
        expected_transfer_instruction = UiCompiledInstruction(
            program_id_index=system_program_index,
            accounts=[source_index, destination_index],
            data=expected_transfer_instruction_data,
            stack_height=None
        )
        if expected_transfer_instruction not in transaction_data.instructions:
            raise ValueError("Provided transaction does not contain correct transfer instruction for agent.")

    def swap_quote_token(self, pool_id: str, amount: float = VALUE_TO_BUY_IN_SOL):
        script_path = os.path.join(self.ts_dir, 'swapQuoteToken.ts')
        if not os.path.exists(script_path):
            return Exception(f"{script_path} not found.")

        env = os.environ.copy()
        env["PATH"] = f"{os.path.dirname(self.node_path)}:" + env["PATH"]
        result = subprocess.run(
            [f'scripts/swapQuoteToken.sh --config {self.config_path} --poolId {pool_id} --amountIn {amount}'],
            capture_output=True, text=True, shell=True, env=env,
        )
        if result.returncode != 0:
            logging.critical(f"Swap of quote token failed with error: {result.stderr}")
            raise Exception(f"Swap of quote token failed with error: {result.stderr}")

        match = re.search(self.parse_pattern, result.stdout)

        if match:
            tx_id = match.group(1)
            amount_in = match.group(2)
            token_in = match.group(3)
            amount_out = match.group(4)
            token_out = match.group(5)
            fee = match.group(6)

            return {
                "txId": tx_id,
                "amountIn": amount_in,
                "tokenIn": token_in,
                "amountOut": amount_out,
                "tokenOut": token_out,
                "fee": fee
            }
        else:
            logging.critical("Failed to parse tx response after running quoteTokenScript.ts script.")
            raise Exception(f"Failed to parse tx response")

    def swap_base_token(self, pool_id: str, amount: float):
        script_path = os.path.join(self.ts_dir, 'swapBaseToken.ts')
        if not os.path.exists(script_path):
            return Exception(f"{script_path} not found.")

        env = os.environ.copy()
        env["PATH"] = f"{os.path.dirname(self.node_path)}:" + env["PATH"]
        sh_script_path = os.path.abspath('scripts/swapBaseToken.sh')
        result = subprocess.run(
            [f'bash {sh_script_path} --config {self.config_path} --poolId {pool_id} --amountOut {amount}'],
            capture_output=True, text=True, shell=True, env=env
        )
        if result.returncode != 0:
            logging.critical(f"Swap of base token failed with error: {result.stderr}")
            raise Exception(f"Swap of base token failed with error: {result.stderr}")
        match = re.search(self.parse_pattern, result.stdout)
        if match:
            tx_id = match.group(1)
            amount_in = match.group(2)
            token_in = match.group(3)
            amount_out = match.group(4)
            token_out = match.group(5)
            fee = match.group(6)

            return {
                "txId": tx_id,
                "amountIn": amount_in,
                "tokenIn": token_in,
                "amountOut": amount_out,
                "tokenOut": token_out,
                "fee": fee
            }
        else:
            logging.critical("Failed to parse tx response after running swapBaseToken.ts script.")
            raise Exception(f"Failed to parse tx response")

    def transfer_share_to_user(self, user_address: str, amount: int) -> str:
        try:
            receiver = Pubkey.from_string(user_address)
            transfer_ix = transfer(
                TransferParams(from_pubkey=self.agent_keypair.pubkey(), to_pubkey=receiver, lamports=amount))
            recent_blockhash = self.client.get_latest_blockhash().value.blockhash
            msg = MessageV0.try_compile(
                payer=self.agent_keypair.pubkey(),
                instructions=[transfer_ix],
                address_lookup_table_accounts=[],
                recent_blockhash=recent_blockhash
            )
            tx = VersionedTransaction(message=msg, keypairs=[self.agent_keypair])
            return str(self.client.send_transaction(tx).value)
        except Exception as e:
            logging.critical("An error occurred during transfer: %s", str(e))
            raise

    def get_address(self):
        return self.agent_keypair.pubkey()

    def get_agent_balance(self):
        response = self.client.get_balance(self.get_address(), commitment=Confirmed)
        return response.value


if __name__ == '__main__':
    from app.core.modules_factory import solana_driver

    print(solana_driver.get_agent_balance())
