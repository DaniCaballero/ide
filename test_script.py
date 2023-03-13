import sys
sys.path.insert(0, r'C:\Users\Asus\Documents\Tesis\Proyecto_PyQt6')
from script_loader import loader

contract = loader("Coin-Coin.sol", 0)

print(contract)