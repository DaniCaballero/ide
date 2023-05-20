import {Local_Account, Account, Contract, Network, Local_Network} from './test_classes.mjs';
import fs from 'fs';
import path from 'path';

function load_project_data() {
    //const project_path = fs.readFileSync("./current_project_path.txt", {encoding : "utf8", flag : "r"});
    //console.log(process.cwd())
    const data_path = "./project_data.json";

    let raw_data = fs.readFileSync(data_path);
    let data_json = JSON.parse(raw_data);

    return data_json;
}

function instantiate_contract(data_json, contract_name, contract_version) {
    const contract_tmp = data_json["contracts"][contract_name][contract_version];
    let contract = new Contract(contract_tmp["name"], contract_tmp["abi"], contract_tmp["bytecode"]);

    let address = contract_tmp["address"];
    contract.address = address;

    return contract;
}

function get_network(network_name, data_json) {
    const network_json = data_json["networks"][network_name];
    let network = null;

    if (network_name === "local") {
        network = new Local_Network(network_json["name"], network_json["chain_id"], network_json["port"]);
    } else {
        network = new Network(network_json["name"], network_json["chain_id"]);
        network.project_path = network_json["project_path"];
    }

    return network;
}

function loader(contract_name, contract_version, network_name = "local") {
    let accounts = [];
    let data_json = load_project_data();
    let contract = instantiate_contract(data_json, contract_name, contract_version);
    let network = get_network(network_name, data_json);

    if (network_name === "local") {
        let accounts_tmp = data_json["accounts"]["local"];
        accounts = accounts_tmp.map(function(acc) {
            return new Local_Account(acc["address"], acc["private_key"].slice(2));
        })
    } else {
        let accounts_tmp = data_json["accounts"]["persistent"];
        accounts = accounts_tmp.map(function(acc) {
            return new Account(acc["alias"]);
        })

        for (let i = 0; accounts.length; i++) {
            accounts[i].address = accounts_tmp[i]["address"];
            accounts[i].project_path = accounts_tmp[i]["project_path"];
        }
    }

    return [contract, network, accounts];
}

export {loader};