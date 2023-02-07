import web3, re

TYPE_CAST = {"uint" : web3.Web3.toInt, "bytes" : web3.Web3.toBytes}

def cast_web3_helper(arg_type, args, list_bool, temp):
    arg_type_tmp = re.sub('\d', '', arg_type)

    if arg_type_tmp in TYPE_CAST.keys():
        if list_bool:
            args = [TYPE_CAST[arg_type_tmp](text=i) for i in args]
            temp.append(args)
        else:
            temp.append(TYPE_CAST[arg_type_tmp](text=args))
    else:
        temp.append(args)


def cast_web3_types(type_list, args_list):
    temp = []

    for arg_type, arg in zip(type_list, args_list):
        if arg_type.endswith("[]"):
            arg_type_tmp = arg_type.split("[]")[0]
            arg_list = arg.strip("][").split(',')

            cast_web3_helper(arg_type_tmp, arg_list, True, temp)
        else:
            cast_web3_helper(arg_type, arg, False, temp)

    return temp

def contract_interaction(network, w3, account, contract, function_name, visibility, type_list, args_list):
    casted_args = cast_web3_types(type_list, args_list)
    nonce = w3.eth.getTransactionCount(account.address)
    contract_instance = contract.get_instance(w3, network)
    tx = {"chainId" : network.chain_id, "from" : account.address, "nonce" : nonce, "gasPrice" : w3.eth.gas_price}

    if visibility == "view":
        value = contract_instance.functions[function_name](*casted_args).call({"from" : account.address})
        return f"{function_name} output: {value}\n"

    else:
        function_tx = contract_instance.functions[function_name](*casted_args).build_transaction(tx)
        signed_tx = account.sign_transaction(w3, function_tx)
        tx_hash = w3.eth.send_raw_transaction(signed_tx.rawTransaction)
        
        tx_receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
        return f"Transaction hash: {tx_hash.hex()}\n"

        #state.output.append(f"Transaction receipt: {tx_receipt}\n")
    

    