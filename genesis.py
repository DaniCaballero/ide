def create_genesis_block(accounts, miner, project_path):
    genesis_config = {"chainId": 10,
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
                "period": 5,
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

    with open(os.path.join(project_path, 'tests', 'genesis.json'), 'w') as f:
        json.dump(genesis, f)