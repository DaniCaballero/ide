import sys
sys.path.insert(0, r'C:\Users\Asus\Documents\Tesis\Proyecto_PyQt6')
from script_loader import loader

contract, network, accounts = loader("Coin-Coin.sol", 0, "local")

print("Contract", contract)
print("Network", network)
print("Account", accounts)

w3 = network.connect_to_node()
bool_val, result = contract.deploy(network, w3, accounts[0], [])

print(bool_val, result)

