import web3
import re


def get_substrings(string):
    '''This function extracts susbtrings that are lists and assigns them a placeholder text
    so they can be subsituted in a string and then reassigned back after a split by ',' is done'''
    substrings, sublist = [], []
    bracket_count = 0

    for char in string:
        if char == "[":
            bracket_count += 1
            sublist.append(char)
        else:
            if bracket_count > 0:
                sublist.append(char)
                if char == "]":
                    bracket_count -= 1
                    if bracket_count == 0:
                        substrings.append("".join(sublist))
                        sublist = []

    return {f"placeholder{i}" : sublist for i, sublist in enumerate(substrings)}

def find_replace_split(string):
    '''This function is used for splitting the argument string by ',' ensuring
    that a list's content is not splitted as well.'''

    if string == "":
        return []

    sublist_dict = get_substrings(string)

    for key, sublist in sublist_dict.items():
        string = string.replace(sublist, key)

    string_list = string.split(",")

    string_list = [item.strip() for item in string_list]

    for key, sublist in sublist_dict.items():
        index = string_list.index(key)
        string_list[index] = sublist

    return string_list
    

TYPE_CAST = {"uint" : web3.Web3.toInt, "bytes" : web3.Web3.toBytes, "address" : web3.Web3.toChecksumAddress}

def cast_web3_helper(arg_type, args, list_bool, temp):
    '''This function extracts base argument type and converts the arguments to their appropiate solidity type.
    In case an argument is a list, all of its elements are converted. '''
    arg_type_tmp = re.sub('\d', '', arg_type)

    if arg_type_tmp in TYPE_CAST.keys():
        if list_bool:
            if arg_type_tmp == "address":
                args = [TYPE_CAST[arg_type_tmp](i) for i in args]
                temp.append(args)
            elif arg_type_tmp == "bytes":
                try:
                    args = [arg.hex() for arg in args]
                except:
                    pass
                args = [TYPE_CAST[arg_type_tmp](hexstr=i) for i in args]
                temp.append(args)
            else:
                args = [TYPE_CAST[arg_type_tmp](text=i) for i in args]
                temp.append(args)
        else:
            if arg_type_tmp == "address":
                temp.append(TYPE_CAST[arg_type_tmp](args))
            elif arg_type_tmp == "bytes":
                try:
                    args = args.hex()
                except:
                    pass
                temp.append(TYPE_CAST[arg_type_tmp](hexstr=args))
            else:
                temp.append(TYPE_CAST[arg_type_tmp](text=args))
    else:
        temp.append(args)

def cast_web3_types(type_list, args_list):
    '''This function splits argument type in case is a list and splits its respective
    argument list by ',' so all elements can be converted to the corresponding type'''
    temp = []
    print("TYPES:", type_list, args_list)

    for arg_type, arg in zip(type_list, args_list):
        if arg_type.endswith("[]"):
            arg_type_tmp = arg_type.split("[]")[0]
            arg_list = arg.strip("][").split(',')

            cast_web3_helper(arg_type_tmp, arg_list, True, temp)
        else:
            cast_web3_helper(arg_type, arg, False, temp)

    return temp

class Contract: 
    def __init__(self, name, abi, bytecode):
        self.name = name
        self.abi = abi
        self.bytecode = bytecode
        self.address = {}

    def __str__(self):
        return f"{self.name}"

    def _sign_and_send_tx(self, tx, account, w3):
        signed_tx = account.sign_transaction(w3, tx)
        tx_hash = w3.eth.send_raw_transaction(signed_tx.rawTransaction)  
        tx_receipt = w3.eth.wait_for_transaction_receipt(tx_hash)

        return tx_receipt

    def deploy(self, network, w3, account, constructor_args, msg_value = 0):
        _, type_list = self.get_function_visibility_input_types("constructor")
        casted_args = cast_web3_types(type_list, constructor_args)
        contract = w3.eth.contract(abi=self.abi, bytecode=self.bytecode)
        nonce = w3.eth.getTransactionCount(account.address)

        tx = contract.constructor(*casted_args).build_transaction(
            {"gasPrice": w3.eth.gas_price,"from" : account.address, "chainId" : network.chain_id, "nonce" : nonce, "value" : msg_value})
        
        tx_receipt = self._sign_and_send_tx(tx, account, w3)
        self.address[network.chain_id] = tx_receipt.contractAddress

        #return f"Contract deployed at: {tx_receipt.contractAddress}\n"
        return True, tx_receipt

    def contract_interaction(self, network, w3, account, function_name, args_list, msg_value = 0):
        visibility, type_list = self.get_function_visibility_input_types(function_name)
        casted_args = cast_web3_types(type_list, args_list)
        nonce = w3.eth.getTransactionCount(account.address)
        contract_instance = self.get_instance(w3, network)

        tx = {"chainId" : network.chain_id, "from" : account.address, "nonce" : nonce, "gasPrice" : w3.eth.gas_price, "value" : msg_value}

        try:
            if visibility == "view" or visibility == "pure":
                value = contract_instance.functions[function_name](*casted_args).call({"from" : account.address})
                return True, value

            else:
                tx = contract_instance.functions[function_name](*casted_args).build_transaction(tx)
                tx_receipt = self._sign_and_send_tx(tx, account, w3)

                return True, tx_receipt
                
        except Exception as e:
            return False, e

    def get_instance(self, w3, network):
        address = self.address[network.chain_id]
        print(address)
        contract_instance = w3.eth.contract(address=address, abi=self.abi)

        return contract_instance

    def get_functions(self):
        function_list = [item for item in self.abi if item["type"]=="function"]

        return function_list

    def get_function_visibility_input_types(self, function_name):
        visibility, input_types = None, []

        if function_name == "constructor":
            constructor = self.get_constructor()
            if constructor != []:
                visibility = constructor["stateMutability"]
                input_types = [input["type"] for input in constructor["inputs"]]
        else:
            for function in self.get_functions():
                if function["name"] == function_name:
                    visibility = function["stateMutability"]
                    input_types = [input["type"] for input in function["inputs"]]
                    break

        return visibility, input_types


    def get_constructor(self):
        try:
            constructor = [item for item in self.abi if item["type"]=="constructor"]
            #input_types = [input["type"] for input in constructor["inputs"]]
            #input = [item for item in constructor[0]["inputs"]]
            #print("iput types",input_types)
            return constructor[0]
        except:
            return []