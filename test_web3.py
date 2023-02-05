from web3 import Web3, EthereumTesterProvider, HTTPProvider

abi = [
                    {
                        "inputs": [],
                        "name": "retrieve",
                        "outputs": [
                            {
                                "internalType": "uint256",
                                "name": "",
                                "type": "uint256"
                            }
                        ],
                        "stateMutability": "view",
                        "type": "function"
                    },
                    {
                        "inputs": [
                            {
                                "internalType": "uint256",
                                "name": "_favoriteNumber",
                                "type": "uint256"
                            }
                        ],
                        "name": "store",
                        "outputs": [
                            {
                                "internalType": "uint256",
                                "name": "",
                                "type": "uint256"
                            }
                        ],
                        "stateMutability": "nonpayable",
                        "type": "function"
                    }
                ]

bytecode = "608060405234801561001057600080fd5b5060e28061001f6000396000f3fe6080604052348015600f57600080fd5b506004361060325760003560e01c80632e64cec11460375780636057361d146053575b600080fd5b603d6092565b6040518082815260200191505060405180910390f35b607c60048036036020811015606757600080fd5b8101908080359060200190929190505050609b565b6040518082815260200191505060405180910390f35b60008054905090565b60008160008190555081905091905056fea264697066735822122034eb11ffc05267fc88c770fde72ef60ab0a59e65a9e29c701926a01ee8ee0c5c64736f6c63430006030033"

w3 = Web3(HTTPProvider("https://goerli.infura.io/v3/f5dbdd6dfae24f2081edfe968bfa6edf"))
print(w3.toBytes(text="256"))
#contract = w3.eth.contract(abi=abi, bytecode=bytecode)
#tx_hash=contract.deploy()
#receipt = w3.eth.getTransactionReceipt(tx_hash)
#contract_address = receipt['contractAddress']

#print(f"contract address is: {contract_address}")
