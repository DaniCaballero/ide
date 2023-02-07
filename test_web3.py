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


abi = [
                    {
                        "inputs": [
                            {
                                "internalType": "uint256",
                                "name": "_favNumber",
                                "type": "uint256"
                            }
                        ],
                        "stateMutability": "nonpayable",
                        "type": "constructor"
                    },
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

bytecode = "608060405234801561001057600080fd5b5060405161020f38038061020f83398181016040528101906100329190610054565b806000819055505061009e565b60008151905061004e81610087565b92915050565b60006020828403121561006657600080fd5b60006100748482850161003f565b91505092915050565b6000819050919050565b6100908161007d565b811461009b57600080fd5b50565b610162806100ad6000396000f3fe608060405234801561001057600080fd5b50600436106100365760003560e01c80632e64cec11461003b5780636057361d14610059575b600080fd5b610043610089565b60405161005091906100f0565b60405180910390f35b610073600480360381019061006e91906100b8565b610092565b60405161008091906100f0565b60405180910390f35b60008054905090565b600081600081905550819050919050565b6000813590506100b281610115565b92915050565b6000602082840312156100ca57600080fd5b60006100d8848285016100a3565b91505092915050565b6100ea8161010b565b82525050565b600060208201905061010560008301846100e1565b92915050565b6000819050919050565b61011e8161010b565b811461012957600080fd5b5056fea26469706673582212204e4930394c59a91aae334a238e25ce9a220baa5b6cdf564c388b47d299bf208464736f6c63430008000033"

bytecode = "608060405234801561001057600080fd5b5060e28061001f6000396000f3fe6080604052348015600f57600080fd5b506004361060325760003560e01c80632e64cec11460375780636057361d146053575b600080fd5b603d6092565b6040518082815260200191505060405180910390f35b607c60048036036020811015606757600080fd5b8101908080359060200190929190505050609b565b6040518082815260200191505060405180910390f35b60008054905090565b60008160008190555081905091905056fea264697066735822122034eb11ffc05267fc88c770fde72ef60ab0a59e65a9e29c701926a01ee8ee0c5c64736f6c63430006030033"

w3 = Web3(HTTPProvider("https://goerli.infura.io/v3/f5dbdd6dfae24f2081edfe968bfa6edf"))
print(w3.toBytes(text="256"))
#contract = w3.eth.contract(abi=abi, bytecode=bytecode)
#tx_hash=contract.deploy()
#receipt = w3.eth.getTransactionReceipt(tx_hash)
#contract_address = receipt['contractAddress']

#print(f"contract address is: {contract_address}")
