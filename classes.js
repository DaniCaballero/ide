const web3 = require("web3");
//require('dotenv').config();
import path from 'path';

class Local_Account {
    constructor(address, private_key) {
        this.alias = address;
        this.address = web3.Web3.utils.toChecksumAddress(address);
        this.private_key = ["0x", private_key].join("");
    }

    async sign_transaction(node, tx) {
        const signed_tx = await node.eth.account.signTransaction(tx, this.private_key);

        return signed_tx;
    }
}

class Account {
    constructor(alias, priv_key = "", project_path = "") {
        this.alias = alias;
        this.address = "";
        this.project_path = project_path;

        if (priv_key != "") {
            if (priv_key.startsWith("0x") == False) {
                priv_key = ["0x", priv_key].join("");
            }

            this.address = web3.eth.accounts.privateKeyToAccount(priv_key);
            this.write_priv_key_to_env(priv_key, project_path);
        }
    }

    load_private_key() {
        env_path = path.join(this.project_path, ".env");
        require('dotenv').config({path : env_path});

        return process.env[`${this.alias}_PRIVATE_KEY`];
    }

    write_priv_key_to_env(priv_key, project_path) {
        
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
        const signed_tx = account.sign_transaction(w3, tx);
        const receipt = w3.eth.sendSignedTransaction(signed_tx.rawTransaction);

        return receipt;
    }

    async deploy(network, w3, account, constructor_args, msg_value = 0) {
        let contract = new w3.eth.Contract(this.abi);
        contract.options.data = this.bytecode;
        const nonce = await w3.eth.getTransactionCount(account.address, 'latest');

        // Create constructor tx
        const tx = contract.deploy({
            arguments : [...constructor_args],
        });

        const tx_receipt = this._sign_and_send_tx(tx, account, w3);

        this.address[network.chain_id] = tx_receipt.contractAddress;

        return true, tx_receipt;
    }
}