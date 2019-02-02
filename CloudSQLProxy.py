import sys
import requests
import pathlib
import os


def dl_url() -> str:
    if sys.platform == 'darwin':
        return 'https://dl.google.com/cloudsql/cloud_sql_proxy.darwin.amd64'

    return 'https://dl.google.com/cloudsql/cloud_sql_proxy.linux.amd64'


def download_proxy(file) -> bool:
    executable = pathlib.Path(file)

    if executable.is_file():
        return True

    with open(file, 'wb') as f:
        r = requests.get(dl_url())
        f.write(r.content)

        os.chmod(file, 0o775)

    return True


class CloudSQLProxy:
    def __init__(self, file: str, credential: str) -> None:
        self.file = file
        self.credential = credential

    def run(self):
        if False == download_proxy(self.file):
            raise RuntimeError('something is wrong')

        os.system(f'{self.file} -instances=inbep-185414:southamerica-east1:masterofpuppets=tcp:3306 -credential_file={self.credential} &')
