import random, pandas, time, threading, blocksmith, json, os, signal, decimal
from PyQt6.QtCore import QThread, QObject, pyqtSignal
from account import Account, Test_Account
from geth_nodes import init_geth_nodes, connect_nodes
from network import Local_Network
from web3 import Web3, datastructures


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
        self.rols = {}
        self.project_path = project_path
        self.inst_count = 0
        self.results = []
        self.use_prev_chain = False

    def __str__(self):
        return f"{self.instructions}"

    def _get_args(self, args):
        data = []
        
        for arg in args:
            #tmp_data = arg.generate_data(iters)
            tmp_data = arg.data
            print("data ", tmp_data)

            if arg.name == "ether denomination":
                tmp_data = [Web3.toWei(decimal.Decimal(data), arg.type) for data in tmp_data]

            data.append(tmp_data)

        return data

    def add_entry_to_results(self, node_port, contract_name, account_address, function_name, args, return_bool, return_value):
        return_str = ""

        if return_bool:
            if type(return_value) == datastructures.AttributeDict:
                return_str = return_value["transactionHash"].hex() 
            else:
                return_str = return_value
        else:
            return_str = return_value
            
        row = [str(node_port),contract_name, account_address, function_name, f"{args}", return_str]
        self.results.append(row)

    def generate_results_csv(self):
        column_names = ["Node port","Contract Name", "Account", "Function Name", "Function arguments", "Return value/Tx hash"]
        df = pandas.DataFrame(self.results, columns=column_names)
        df.to_csv(os.path.join(self.project_path, "tests", self.name, "results.csv"))

    def calc_total_executions(self):
        total = 0

        for inst in self.instructions:
            total += inst.number_of_executions

        return total

    def create_accounts(self, acc_number):
        #self.accounts = []
        kg = blocksmith.KeyGenerator()

        for i in range(acc_number):
            priv_key = kg.generate_key()
            self.accounts.append(Test_Account(f"acccount-{i}", priv_key))

    def add_new_rol(self, name, idxs):
        self.rols[name] = Rol(name, idxs)
        
    def _divide_load(self, args, n_iter, nc):
        if n_iter < nc:
            # limitamos el numero de hilos a la cantidad de iteraciones, si es necesario
            nc = n_iter

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

        if len(args) > 2:
            return row[0], row[1], row[2:]
        else:
            return row[0], row[1], []

    def _thread_send_transactions(self, time_interval, contract, function_name, th_args_index, args):
        n_iter = th_args_index[0]
        start_time = time.time()
        return_bool, return_value = False, ""

        for i in range(n_iter):
            node = random.choice(self.nodes)
            w3 = node.connect_to_node()

            account, msg_value, args_row = self._extract_row(i, th_args_index[1], args)

            if function_name == "constructor":
                node = self.nodes[0]
                w3 = node.connect_to_node()
                return_bool, return_value = contract.deploy(node, w3, account, args_row, msg_value)
            else:
                return_bool, return_value = contract.contract_interaction(node, w3, account, function_name, args_row, msg_value)

            time.sleep(max(time_interval - ((time.time() - start_time)), 0))
            
            start_time = time.time()

            lock.acquire()
            self.add_entry_to_results(node.port, contract.name, account.address, function_name, args_row, return_bool, return_value)
            self.inst_count += 1
            lock.release()

    def end_geth_processes(self, pids):
        for pid in pids:
            os.kill(pid, signal.SIGTERM)

    def configure_evironment(self):
        for i in range(3):
            print("PRIVAT KEY: ", self.accounts[i].address, self.accounts[i].private_key)
        
        test_path = os.path.join(self.project_path, "tests", self.name)
        try:
            os.mkdir(test_path)
        except:
            pass

        set_miner_info(self.accounts[0], test_path)

        http_ports, pids = init_geth_nodes(self.number_of_nodes, test_path, self.accounts, self.use_prev_chain)
        connect_nodes(http_ports)
        time.sleep(5)

        self.nodes = [Local_Network("geth", "", 1325, port) for port in http_ports]

        return pids

    def run(self):

        global lock
        lock = threading.Lock()

        pids = self.configure_evironment()

        for instruction in self.instructions:
            # populate data list of arg
            accounts = [self.accounts[index] for index in instruction.accounts]
            #args = [accounts] +self._get_args([instruction.msg_values], instruction.number_of_executions) +self._get_args(instruction.args, instruction.number_of_executions)
            args = [accounts] +self._get_args([instruction.msg_values]) +self._get_args(instruction.args)
            threads_args_index = self._divide_load(args, instruction.number_of_executions, self.concurrency_number)

            threads = [threading.Thread(target=self._thread_send_transactions, args=(instruction.time_interval,
                        instruction.contract, instruction.function_name, th_args, args,)) for th_args in threads_args_index]

            # Start threads
            for th in threads:
                th.start()

            # Wait for all threads to finish to move onto the next transaction
            for th in threads:
                th.join()

        self.generate_results_csv()
        self.end_geth_processes(pids)

class Rol:
    def __init__(self, name, idx : list):
        self. name = name
        self.idx = idx

class Instruction:
    def __init__(self, contract, version, function_name, number_of_executions, args, msg_values,time_interval=0,accounts=[], use_csv=False):
        self.contract = contract
        self.version = version
        self.function_name = function_name
        self.accounts = accounts
        self.number_of_executions = number_of_executions
        self.time_interval = time_interval
        self.use_csv = use_csv
        self.args = args
        self.msg_values = msg_values
        

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

        return self.data

class Random(Argument):
    def __init__(self, _min, _max, name = "", type = ""):
        super().__init__(name, type)

        self.min = _min
        self.max = _max
    
    # Quiza sea mejor generar una lista de tantos elementos inicializando la prueba. Problema con los hilos?
    def get_next_arg(self):
        return random.randint(self.min, self.max)

    def generate_data(self, iterations):
        self.data = [random.randint(self.min, self.max) for i in range(iterations)]
        return self.data

class File(Argument):
    def __init__(self, file_path, name="", type=""):
        super().__init__(name, type)

        self.path = file_path

    def generate_data(self, iterations):
        df = pandas.read_csv(self.path, sep=";")

        self.data = list(df[self.name])
        #print("DATOS", self.data)
        return self.data


# class for data that need to be uploaded to IPFS to obtain the identifier that will be in the contract
class IPFS_Data:
    def __init__(self, folder_path):
        self.path = folder_path

class Worker(QObject):
    progressChanged = pyqtSignal(int)
    finished = pyqtSignal()

    def __init__(self, test):
        super().__init__()
        self.test = test

    def work(self):
        count, progress = 0, 0
        total_instructions = self.test.calc_total_executions()

        while count <= total_instructions:
            count = self.test.inst_count
            progress = int(count * (100 / total_instructions))
            #print("progress",progress)
            self.progressChanged.emit(progress)

            if count == total_instructions:
                print(progress)
                self.finished.emit()
                break
