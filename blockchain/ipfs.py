import w3storage
from pathlib import Path
import os

class IPFS:
    def __init__(self, token_id):
        self.token_id = token_id

    def add_file(self, file_path):
        w3 = w3storage.API(token=self.token_id)
        cid = ""

        with open(file_path, "rb") as file:
            cid = w3.post_upload((Path(file_path).name, file))

        return cid

    def add_files(self, dir_path):
        files = os.listdir(dir_path)
        only_files = [os.path.join(dir_path, f) for f in files if os.path.isfile(os.path.join(dir_path, f))]
        cids = []

        for file in only_files:
            cid = self.add_file(file)
            cids.append(cid)

        return cids

    def upload_to_ipfs(self, path, name, multiple_files, project_path):
        cids = []
        results_path = os.path.join(project_path, "IPFS", f"{name}.txt")

        if multiple_files:
            cids = self.add_files(path)
        else:
            cids.append(self.add_file(path))

        with open(results_path, "w") as f:
            for cid in cids:
                f.write("%s\n" % cid)

            