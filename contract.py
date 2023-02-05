import web3
from interact import cast_web3_types

class Contract: 
    def __init__(self, name, abi, bytecode):
        self.name = name
        self.abi = abi
        self.bytecode = bytecode
        self.address = {}

    def deploy(self, w3, chain_id, account, args_types, constructor_args):
        casted_args = cast_web3_types(args_types, constructor_args)
        contract = w3.eth.contract(abi=self.abi, bytecode=self.bytecode)
        nonce = w3.eth.getTransactionCount(account.address)

        tx = contract.constructor(*casted_args).build_transaction(
            {"gasPrice": w3.eth.gas_price,"from" : account.address, "chainId" : chain_id, "nonce" : nonce})
        
        signed_tx = account.sign_transaction(w3 ,tx)
        tx_hash = w3.eth.send_raw_transaction(signed_tx.rawTransaction)
        tx_receipt = w3.eth.wait_for_transaction_receipt(tx_hash)

        self.address[chain_id] = tx_receipt.contractAddress
        #state.output.append(f"Contract deployed at: {tx_receipt.contractAddress}\n")
        return f"Contract deployed at: {tx_receipt.contractAddress}\n"

    def get_instance(self, w3, network):
        print(f"type of chain_ñid : {type(network.chain_id)}")
        contract_instance = w3.eth.contract(address=self.address[network.chain_id], abi=self.abi)
        return contract_instance

    def get_functions(self):
        function_list = [item for item in self.abi if item["type"]=="function"]

        return function_list

    def get_constructor(self):
        try:
            constructor = [item for item in self.abi if item["type"]=="constructor"]
            #input_types = [input["type"] for input in constructor["inputs"]]
            #input = [item for item in constructor[0]["inputs"]]
            #print("iput types",input_types)
            return constructor[0]
        except:
            return []