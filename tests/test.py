import random, pandas, time, threading, blocksmith, json, os, signal, decimal, psutil
from PyQt6.QtCore import QThread, QObject, pyqtSignal, QAbstractTableModel, Qt
from PyQt6.QtGui import QColor
from blockchain.account import Account, Test_Account
from .geth_nodes import init_geth_nodes, connect_nodes
from blockchain.network import Local_Network
from web3 import Web3, datastructures, middleware
from blockchain.contract import find_replace_split, _sign_and_send_tx

class CustomThread(threading.Thread):
    '''Custom class that saves any exception occured during thread execution and reraises it 
    when thread is joined'''
    def run(self):
        self.exc = None

        try:
            self._target(*(self._args))
        except Exception as e:
            self.exc = e

    def join(self):
        threading.Thread.join(self)

        if self.exc:
            raise self.exc


def set_miner_info(miner, test_path):
    with open(os.path.join(test_path,"key.txt"), "w") as f:
        f.write(miner.private_key)

    with open(os.path.join(test_path,"pwd.txt"), "w") as f:
        f.write("miner_password")

def send_ether_transaction(from_account, to_addr, value, nonce, w3, chain_id):
    tx = {'from' : from_account.address,'nonce' : nonce, 'to' : to_addr, 'chainId' : chain_id, 'value' : value, "gas" : 21000,"gasPrice": w3.eth.gas_price}
    tx_receipt = _sign_and_send_tx(tx, from_account, w3)

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
        self.prev_outputs = {}
        self.first_instruction = True
        self.error = False
        self.nonce_tracker = {}

    def __str__(self):
        return f"{self.instructions}"

    def _get_args(self, args):
        data = []
        
        for arg in args:

            tmp_data = arg.data
            #print("data ", tmp_data)

            if arg.name == "ether":
                print("prev temp", tmp_data)
                tmp_data = [Web3.toWei(decimal.Decimal(data), arg.type) for data in tmp_data]
                print("tmp_Data", tmp_data)

            if arg.type == "address":
                tmp_data = [self.accounts[i].address for i in tmp_data]

            if arg.__class__.__name__ == "Prev_Output":
                # Data obtained in runtime
                tmp_data = self.prev_outputs[arg.output_dict_name]

                if arg.index != None:
                    #tmp_data = self.prev_outputs[arg.output_dict_name][arg.index]
                    tmp_data = [data[arg.index] for data in tmp_data]

            data.append(tmp_data)

        return data

    def add_entry_to_results(self, node_port, contract_name, account_address, function_name, args, return_bool, ether_sent, return_value):

        if type(return_value) == datastructures.AttributeDict:
            return_value = return_value["transactionHash"].hex() 
 
        else:
            return_value = str(return_value)
            
        row = [str(node_port),contract_name, account_address, function_name, f"{args}", ether_sent, return_value]
        self.results.append(row)

    def generate_results_csv(self):
        column_names = ["Node port","Contract Name", "Account", "Function Name", "Function arguments", "Amount of ether sent", "Return value/Tx hash"]
        df = pandas.DataFrame(self.results, columns=column_names)
        df.to_csv(os.path.join(self.project_path, "tests", self.name, "results.csv"))

    def calc_total_executions(self):
        total = 0

        for inst in self.instructions:
            total += inst.number_of_executions

        return total
    
    def get_nonce(self, address):
        try:
            self.nonce_tracker[address] += 1
        except:
            self.nonce_tracker[address] = 0

        nonce = self.nonce_tracker[address]
        #print("nonce ", nonce)

        return nonce

    def create_accounts(self, acc_number):
        #self.accounts = []
        kg = blocksmith.KeyGenerator()

        for i in range(acc_number):
            priv_key = kg.generate_key()
            self.accounts.append(Test_Account(f"acccount-{i}", priv_key))

    def add_new_rol(self, name, idxs):
        self.rols[name] = Rol(name, idxs)
        
    def _divide_load(self, args, n_iter, nc):
 
        # limit number of threads to amount of iterations, if necessary
        if n_iter < nc:
            nc = n_iter

        # every thread has a list with 2 elements in it. First element is an integer that represents
        # how many iterations are assigned to that thread. Second argument is a list and its elements
        # represent the index where the thread will start reading its own arguments
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
        
    def add_to_prev_output(self, value, key):
        if key != None:
            self.prev_outputs[key].append(value)

    def _thread_send_transactions(self, time_interval, contract, function_name, prev_output_key, th_args_index, args):
        n_iter = th_args_index[0]
        return_bool, return_value = True, ""
        start_time = time.time()

        visibility, _ = contract.get_function_visibility_input_types(function_name)

        for i in range(n_iter):
            node = random.choice(self.nodes)

            if self.inst_count == 0:
                lock.acquire()
                if self.first_instruction == True:
                    node = self.nodes[0]
                    self.first_instruction = False
                lock.release()

            w3 = node.connect_to_node()
            #w3.middleware_onion.add(middleware.pythonic.pythonic_middleware)

            account, msg_value, args_row = self._extract_row(i, th_args_index[1], args)

            lock.acquire()
            if visibility == "view" or visibility == "pure":
                nonce = None
            else:
                nonce = self.get_nonce(account.address)
            lock.release()

            if contract == "":
                return_value = w3.eth.getBalance(account.address)
            else:
                if function_name == "constructor":
                    return_bool, return_value = contract.deploy(node, w3, account, args_row, msg_value, nonce)
                else:
                    return_bool, return_value = contract.contract_interaction(node, w3, account, function_name, args_row, msg_value, nonce)

            if return_bool == False:
                send_ether_transaction(account, account.address, 100, nonce, w3, node.chain_id) #praying that this works

            time.sleep(max(time_interval - ((time.time() - start_time)), 0))
            
            start_time = time.time()

            lock.acquire()
            self.add_to_prev_output(return_value, prev_output_key)
            self.add_entry_to_results(node.port, str(contract), account.address, function_name, args_row, return_bool, msg_value, return_value)
            self.inst_count += 1
            #print("nonce, inst_count, real nonce", nonce, self.inst_count, w3.eth.getTransactionCount(account.address))
            lock.release()

    def end_geth_processes(self, pids):
        for pid in pids:

            try:
                for child in psutil.Process(pid).children():
                    print("child pid: ", child.pid)
                    #child.terminate()
                    os.kill(child.pid, signal.SIGTERM)
            except:
                print("Process not found")


    def configure_evironment(self):
       
        test_path = os.path.join(self.project_path, "tests", self.name)
        try:
            os.mkdir(test_path)
        except:
            pass

        set_miner_info(self.accounts[0], test_path)

        http_ports, pids = init_geth_nodes(self.number_of_nodes, test_path, self.accounts)
        connect_nodes(http_ports)
        # syncronization time
        time.sleep(2)
        
        self.nodes = [Local_Network(f"geth-{self.name}", 1325, port) for port in http_ports]

        return pids

    def run(self, event):

        try:
            global lock
            lock = threading.Lock()

            pids = self.configure_evironment()
            start_time = time.time()

            for instruction in self.instructions:
                if event.is_set():
                    raise Exception("Execution cancelled by main thread")
                # populate data list of arg
                accounts = [self.accounts[index] for index in instruction.accounts]
                #args = [accounts] +self._get_args([instruction.msg_values], instruction.number_of_executions) +self._get_args(instruction.args, instruction.number_of_executions)
                args = [accounts] +self._get_args([instruction.msg_values]) +self._get_args(instruction.args)

                threads_args_index = self._divide_load(args, instruction.number_of_executions, self.concurrency_number)


                threads = [CustomThread(target=self._thread_send_transactions, args=(instruction.time_interval,
                            instruction.contract, instruction.function_name, instruction.prev_output_key, th_args, args,)) for th_args in threads_args_index]

                # Start threads
                for th in threads:
                    th.start()

                # Wait for all threads to finish to move onto the next transaction
                for th in threads:
                    th.join()
            
            end_time = time.time()
            exec_time = round(end_time - start_time, 3)
            self.add_entry_to_results(f"Execution time: {exec_time} seconds", "", "", "", "", "", "", "")

            self.generate_results_csv()
            self.end_geth_processes(pids)

        except Exception as e:
            self.error = True
            self.add_entry_to_results("", "", "", "", "", "","", e)
            self.generate_results_csv()

            try:
                self.end_geth_processes(pids)
            except:
                pass

class Rol:
    def __init__(self, name, idx : list):
        self. name = name
        self.idx = idx

class Instruction:
    def __init__(self, contract, version, function_name, number_of_executions, args, msg_values, prev_output_key,time_interval=0,accounts=[], use_csv=False):
        self.contract = contract
        self.version = version
        self.function_name = function_name
        self.accounts = accounts
        self.number_of_executions = number_of_executions
        self.time_interval = time_interval
        self.use_csv = use_csv
        self.args = args
        self.msg_values = msg_values
        self.prev_output_key = prev_output_key

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
    
class Prev_Output(Argument):
    def __init__(self, output_dict_name, index = None, name = "", type = ""):
        super().__init__(name, type)

        self.output_dict_name = output_dict_name
        self.index = index

    def generate_data(self, iterations):
        return []

class File(Argument):
    def __init__(self, file_path, name="", type=""):
        super().__init__(name, type)

        self.path = file_path

    def generate_data(self, iterations):
        df = pandas.read_csv(self.path, sep=";", skipinitialspace=True)

        self.data = list(df[self.name])
        print("DATOS", self.data)
        return self.data
    
class List_Arg(Argument):
    def __init__(self, text, name = "", type = ""):
        super().__init__(name, type)

        self.text = text

    def generate_data(self, iterations):
        self.data = find_replace_split(self.text)

        return self.data
    
class Time_Arg(Argument):
    def __init__(self, seconds, random_bool = False, name = "", type = ""):
        super().__init__(name, type)
        self.seconds = seconds
        self.random_bool = random_bool

    def generate_data(self, iterations):
        current_time = time.time()

        if self.random_bool == False:
            self.data = [current_time + self.seconds]
        else:
            self.data = [current_time + random.randint(self.seconds) for i in iterations]

        return self.data


# class for data that need to be uploaded to IPFS to obtain the identifier that will be in the contract
class IPFS_Data:
    def __init__(self, folder_path):
        self.path = folder_path

class ResultsModel(QAbstractTableModel):
    def __init__(self, data):
        super().__init__()
        self._data = data
        self.hheaders = ["Node port","Contract Name", "Account", "Function Name", "Function arguments", "Amount of ether sent", "Return value/Tx hash"]

        colors = [QColor("#d9f6ff"), QColor("#d9ffed"), QColor("#ffd9f9"), QColor("#ffecd9"), QColor("#dcd9ff")]
        self.nameColumn = 3

        third_column = [row[self.nameColumn] for row in self._data]
        unique_function_names = list(dict.fromkeys(third_column))
        self.colors_dict = {}
        index = 0

        for function_name in unique_function_names:
            color = colors[index % len(colors)]
            self.colors_dict[function_name] = color
            index += 1
        
        print("colors dict: ", self.colors_dict)

    def data(self, index, role):
        if role == Qt.ItemDataRole.DisplayRole:
            return self._data[index.row()][index.column()]
        if role == Qt.ItemDataRole.BackgroundRole:
            row = index.row()
            try:
                color = self.colors_dict[self._data[row][self.nameColumn]]
                return color
            except Exception as e:
                print(e)
                return QColor("white")
        
    def rowCount(self, index):
        return len(self._data)
    
    def columnCount(self, index):
        return len(self._data[0])   
    
    def headerData(self, section, orientation, role=Qt.ItemDataRole.DisplayRole):
        if orientation == Qt.Orientation.Horizontal and role == Qt.ItemDataRole.DisplayRole:
            return self.hheaders[section]
        
        return super().headerData(section, orientation, role)

class Worker(QObject):
    progressChanged = pyqtSignal(int)
    errorFound = pyqtSignal()
    finished = pyqtSignal()

    def __init__(self, test):
        super().__init__()
        self.test = test

    def work(self):
        count, progress = 0, 0
        total_instructions = self.test.calc_total_executions()

        while count <= total_instructions and self.test.error == False:
            count = self.test.inst_count
            progress = int(count * (100 / total_instructions))
            #print("progress",progress)
            self.progressChanged.emit(progress)

            if count == total_instructions:
                print(progress)
                self.finished.emit()
                break

        if self.test.error == True:
            self.errorFound.emit()
            self.finished.emit()
