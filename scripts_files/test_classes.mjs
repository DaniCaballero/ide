//const web3 = require("web3");
import Web3 from 'web3';
import fs from 'fs';
import * as dotenv from 'dotenv';
//require('dotenv').config();
import path from 'path';

class Local_Network {
    constructor(name, chain_id = 0, port = "8545") {
        this.name = name;
        this.chain_id = chain_id;
        this.port = port;
    }

    connect_to_node() {
        const w3 = new Web3(`ws://localhost:${this.port}`);

        return w3;
    }
}

class Network {
    constructor(name, chain_id, api_key = "", project_path = "") {
        this.name = name;
        this.chain_id = chain_id;
        this.project_path = project_path;

        if (api_key != "") {
            this.write_api_key_to_env(api_key, project_path);
        } 
    }

    connect_to_node() {
        const api_key = this.load_api_key();
        const url = `https://${self.name}.infura.io/v3/${api_key}`;
        const w3 = new Web3(new Web3.providers.HttpProvider(url));

        return w3;
    }

    load_api_key() {
        let env_path = path.join(this.project_path, ".env");
        dotenv.config({path : env_path})

        return process.env[`${this.name}_API_KEY`];
    }

    write_api_key_to_env(api_key, project_path) {
        let env_line = `export ${this.name}_API_KEY=${api_key}\n`;
        let env_path = path.join(project_path, ".env");

        fs.appendFile(env_path, env_line, 'utf-8', err => {
            if (err) {
                throw err;
            }
        });
    }
}

class Local_Account {
    constructor(address, private_key) {
        this.alias = address;
        let web3 = new Web3();
        this.address = web3.utils.toChecksumAddress(address);
        this.private_key = ["0x", private_key].join("");
    }

    async sign_transaction(node, tx) {
        const signed_tx = await node.eth.accounts.signTransaction(tx, this.private_key);

        return signed_tx;
    }
}

class Account {
    constructor(alias, priv_key = "", project_path = "") {
        this.alias = alias;
        this.address = "";
        this.project_path = project_path;

        if (priv_key != "") {
            if (priv_key.startsWith("0x") == false) {
                priv_key = ["0x", priv_key].join("");
            }
            let web3 = new Web3();
            this.address = web3.eth.accounts.privateKeyToAccount(priv_key);
            this.write_priv_key_to_env(priv_key, project_path);
        }
    }

    load_private_key() {
        let env_path = path.join(this.project_path, ".env");
        dotenv.config({path : env_path})

        return process.env[`${this.alias}_PRIVATE_KEY`];
    }

    write_priv_key_to_env(priv_key, project_path) {
        let env_line = `export ${this.alias}_PRIVATE_KEY=${priv_key}\n`;
        let env_path = path.join(this.project_path, ".env");

        fs.appendFile(env_path, env_line, 'utf-8', err => {
            if (err) {
                throw err;
            }
        });

    }

    async sign_transaction(node, tx) {
        let priv_key = this.load_private_key();
        const signed_tx = await node.eth.accounts.signTransaction(tx, priv_key);

        return signed_tx;
    }
}

class Contract {
    constructor(name, abi, bytecode) {
        this.name = name;
        this.abi = abi;
        this.bytecode = bytecode;
        this.address = {};
    }

    async _sign_and_send_tx(tx, account, w3) {
        const signed_tx = await account.sign_transaction(w3, tx);
        const receipt = await w3.eth.sendSignedTransaction(signed_tx.rawTransaction);
        //console.log(receipt);
        return receipt;
    }

    async deploy(network, w3, account, constructor_args, msg_value = 0) {
        let contract = new w3.eth.Contract(this.abi);
        contract.options.data = this.bytecode;
        const nonce = await w3.eth.getTransactionCount(account.address.address, 'latest');

        // Create constructor tx
        const build_tx = contract.deploy({
            arguments : [...constructor_args],
        });

        let tx = {from : account.address.address, value : msg_value, gas : await build_tx.estimateGas(), data : build_tx.encodeABI()};
        const tx_receipt = await this._sign_and_send_tx(tx, account, w3);

        this.address[network.chain_id] = tx_receipt.contractAddress;
        //this.address[5] = tx_receipt.contractAddress;
        //console.log("Contract address is:", tx_receipt.contractAddress)

        return tx_receipt;
    }

    async contract_interaction(network, w3, account, function_name, args_list, msg_value = 0) {
        const nonce = await w3.eth.getTransactionCount(account.address, 'latest');
        const visibility = this.get_visibility(function_name);
        let contract_instance = this.get_instance(w3, network);

        if (visibility === "view" || visibility === "pure") {
            let value = await contract_instance.methods[function_name](...args_list).call({from : account.address});

            return value;
        } else {
            
            let build_tx = await contract_instance.methods[function_name](...args_list);
            let tx = {from : account.address, value : msg_value, to : contract_instance.address, gas : await build_tx.estimateGas(), data : build_tx.encodeABI()};

            const tx_receipt = await this._sign_and_send_tx(tx, account, w3);

            return tx_receipt;
        }
    }

    get_instance(w3, network) {
        let address = this.address[network.chain_id];
        //let address = this.address[5];
        const contract_instance = new w3.eth.Contract(this.abi, address);

        return contract_instance;
    }

    get_visibility(function_name) {
        let visibility = null;
        const functions = this.abi.filter(item => item["type"] === "function");

        for (let i = 0; i < functions.length; i++) {
            if (functions[i]["name"] === function_name) {
                visibility = functions[i]["stateMutability"];
                break;
            }
        }

        return visibility;
    }


}

export {Local_Account, Account, Contract, Network, Local_Network};