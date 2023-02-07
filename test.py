import random, pandas, time, threading, blocksmith, json, os, signal
from interact import contract_interaction
from account import Account, Test_Account
from geth_nodes import init_geth_nodes, connect_nodes
from network import Local_Network

def create_genesis_block(accounts, miner, test_path):
    genesis_config = {"chainId": 1325,
            "homesteadBlock": 0,
            "eip150Block": 0,
            "eip155Block": 0,
            "eip158Block": 0,
            "byzantiumBlock": 0,
            "constantinopleBlock": 0,
            "petersburgBlock": 0,
            "istanbulBlock": 0,
            "berlinBlock": 0,
            "muirGlacierBlock": 0,
            "londonBlock" : 0,
            "clique": {
                "period": 3,
                "epoch": 30000
            }
            }
        
    genesis = {"config": genesis_config,
        "difficulty": "1",
        "gasLimit": "8000000",
        "extradata": f"0x0000000000000000000000000000000000000000000000000000000000000000{miner.address[2:]}0000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000"
        }

    default_balance = { "balance": "100000000000000000000" }

    alloc = {}
    alloc[miner.address[2:]] = default_balance
    
    for account in accounts:
        alloc[account.address[2:]] = default_balance

    genesis["alloc"] = alloc

    with open(os.path.join(test_path, 'genesis.json'), 'w') as f:
        json.dump(genesis, f)

def set_miner_info(miner, test_path):
    with open(os.path.join(test_path,"key.txt"), "w") as f:
        f.write(miner.private_key)

    with open(os.path.join(test_path,"pwd.txt"), "w") as f:
        f.write("miner_password")

class Test:
    def __init__(self, name="", number_of_nodes=1, concurrency_number=1, project_path=""):
        self.name = name
        self.number_of_nodes = number_of_nodes
        self.concurrency_number = concurrency_number
        self.instructions = []
        self.nodes = []
        self.accounts = []
        self.project_path = project_path

    def __str__(self):
        return f"{self.instructions}"

    def _get_args(self, args, iters):
        data = []
        
        for arg in args:
            data.append(arg.generate_data(iters))

        return data

    def create_accounts(self, acc_number):
        self.accounts = []
        kg = blocksmith.KeyGenerator()

        for i in range(acc_number):
            priv_key = kg.generate_key()
            self.accounts.append(Test_Account(f"acccount-{i}", priv_key))
        

    def _divide_load(self, args, n_iter, nc):
        data = [[0,[0 for j in range(len(args))]] for i in range(nc)]

        for i in range(nc):
            th_iter = n_iter // nc

            if i == nc - 1:
                th_iter += n_iter % nc

            data[i][0] = th_iter

        for j in range(len(args)):
            for i in range(1, len(data)):
                th_arg_index = (data[i-1][1][j] + data[i-1][0]) % len(args[j])
                data[i][1][j] = th_arg_index

        return data
    
    def _extract_row(self, i, args_index, args):
        row = []

        for j in range(len(args)):
            row.append(args[j][(i + args_index[j]) % len(args[j])])

        if len(args) > 1:
            return row[0], row[1:]
        else:
            return row[0], []

    def _thread_send_transactions(self, time_interval, contract, function_name, visibility, th_args_index, args, args_types):
        # loop through args length
        # pick random choice node
        # get row of args
        # send transaction trough contract interaction
        n_iter = th_args_index[0]
        start_time = time.time()

        for i in range(n_iter):
            node = random.choice(self.nodes)
            print("PUERTO DEL NODO: ", node.port)
            w3 = node.connect_to_node()

            account, args_row = self._extract_row(i, th_args_index[1], args)

            if function_name == "constructor":
                node = self.nodes[0]
                w3 = node.connect_to_node()
                print("DEPLOYMENT ARGS: ", account.address, args_types, args_row)
                contract.deploy(w3, node.chain_id, account, args_types, args_row)
            else:
                return_value = contract_interaction(node, w3, account, contract, function_name, visibility, args_types, args_row)
                print(return_value)

            #print("SLEEP TIME: ",time_interval - ((time.time() - start_time)))
            time.sleep(max(time_interval - ((time.time() - start_time)), 0))
            
            start_time = time.time()

    def end_geth_processes(self, pids):
        for pid in pids:
            os.kill(pid, signal.SIGINT)

    def configure_evironment(self):
        for i in range(3):
            print("PRIVAT KEY: ", self.accounts[i].address, self.accounts[i].private_key)
        
        test_path = os.path.join(self.project_path, "tests", self.name)
        try:
            os.mkdir(test_path)
        except:
            pass

        create_genesis_block(self.accounts, self.accounts[0], test_path)

        set_miner_info(self.accounts[0], test_path)

        http_ports, pids = init_geth_nodes(self.number_of_nodes, test_path, self.accounts[0])
        connect_nodes(http_ports)

        self.nodes = [Local_Network("geth", "", 1325, port) for port in http_ports]
        print("Si alcanzo este punto")

        return pids

    def run(self):
        # for instructions
        # initialize arguments
        # create threads
        # assign load to threads
        # for exec number / time_interval
        # extract arguments
        # pick a node
        # send transaction
        # write result to file?


        pids = self.configure_evironment()

        #self.end_geth_processes(pids)
        for instruction in self.instructions:
            # populate data list of arg
            args = [instruction.accounts] + self._get_args(instruction.args, instruction.number_of_executions)
            #print("INSTRUCTION ARGS: ", args)
            args_types = [arg.type for arg in instruction.args]

            threads_args_index = self._divide_load(args, instruction.number_of_executions, self.concurrency_number)
            #print("THREAD DIVISION: ", threads_args_index)

            # if instruction.function_name != "constructor":
            threads = [threading.Thread(target=self._thread_send_transactions, args=(instruction.time_interval,
                        instruction.contract, instruction.function_name, instruction.visibility, th_args, args, args_types,)) for th_args in threads_args_index]

            #self._thread_send_transactions(instruction.time_interval,instruction.contract, instruction.function_name, instruction.visibility, threads_args_index[0], args, args_types)

            # Start threads
            for th in threads:
                th.start()
            print("Aqui si llego no???")
            print("THREADS: ", threads)
            # Wait for all threads to finish to move onto the next transaction
            for th in threads:
                th.join()

            # else:
            #for th_args in threads_args_index:
                #print("por acaaa")
            #self._thread_send_transactions(instruction.time_interval,instruction.contract, instruction.function_name, instruction.visibility, threads_args_index[0], args, args_types)

            print("UWUUUUUU")

        self.end_geth_processes(pids)

class Instruction:
    def __init__(self, contract, function_name, number_of_executions, args, visibility, time_interval=0,accounts=[], use_csv=False):
        self.contract = contract
        self.function_name = function_name
        self.accounts = accounts
        self.number_of_executions = number_of_executions
        self.time_interval = time_interval
        self.use_csv = use_csv
        self.args = args
        self.visibility = visibility

    def __str__(self):
        return f"{self.function_name}, {self.number_of_executions}"

    def __repr__(self):
        return self.__str__()

# Base class for arguments of a contract function. 
class Argument:
    def __init__(self, name, type):
        self.name = name
        self.type = type
        self.data = []

    def generate_data(self, iterations):
        pass

    def __str__(self):
        return f"{self.__class__.__name__} : {self.data}"

    def __repr__(self):
        return self.__str__()


class Sequence(Argument):
    def __init__(self, _min, _max, name = "", type = "", step = 1):
        super().__init__(name, type)

        self.min = _min
        self.max = _max
        self.step = step

    def generate_data(self, iterations):
        self.data = list(range(self.min, self.max, self.step))

class Random(Argument):
    def __init__(self, _min, _max, name = "", type = ""):
        super().__init__(name, type)

        self.min = _min
        self.max = _max
    
    # Quiza sea mejor generar una lista de tantos elementos inicializando la prueba. Problema con los hilos?
    def get_next_arg(self):
        return random.randint(self.min, self.max)

    def generate_data(self, iterations):
        return [random.randint(self.min, self.max) for i in range(iterations)]

class File(Argument):
    def __init__(self, file_path, name="", type=""):
        super().__init__(name, type)

        self.path = file_path

    def generate_data(self, iterations):
        try:
            df = pandas.read_csv(self.path)
            self.data = list(df[self.name])
        except:
            raise Exception

# class for data that need to be uploaded to IPFS to obtain the identifier that will be in the contract
class IPFS_Data:
    def __init__(self, folder_path):
        self.path = folder_path
