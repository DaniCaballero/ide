import sys
sys.path.insert(0, r'C:\Users\Asus\Documents\Tesis\Proyecto_PyQt6')
from script_loader import loader
import random

contract, network, accounts = loader("Ballot-Voting.sol", 0, "local")

#print("Contract", contract)
#print("Network", network)
#print("Account", accounts)

w3 = network.connect_to_node()
bool_val, result = contract.deploy(network, w3, accounts[0], [["John", "Mary", "Jojito"]])

#print(bool_val, result)

# Allow addresses to vote
for i in range(1,len(accounts)):
	contract.contract_interaction(network, w3, accounts[0],"giveRightToVote", [accounts[i].address])

# Voters vote
for i in range(1, len(accounts)):
	contract.contract_interaction(network, w3, accounts[i], "vote", [random.randint(0,2)])
	
# Check winner
bool_val, result = contract.contract_interaction(network, w3, accounts[0], "winnerName", [])

print("Winner: ", result)
