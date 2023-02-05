import w3storage
from pathlib import Path

class IPFS:
    def __init__(self, token_id):
        self.token_id = token_id

    def add_file(self, state, file_path):
        w3 = w3storage.API(token=self.token_id)

        with open(file_path, "rb") as file:
            cid = w3.post_upload((Path(file_path).name, file))
            state.output.append(f"File content identifier is: {cid}")