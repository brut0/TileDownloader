# Если библиотека requests не установлена: перейти в командной строке в папку с Python
# Выполнить: pip install requests

import time as tm
import numpy as np
import requests as requests
import warnings
import logging
import concurrent.futures
from pathlib import Path

logging.basicConfig(filename='log.log')

zoom: int = 5
timeout = 1
ntiles = 1 << zoom
YOUR_CODE = ""


# Get request from 'name'
def get_request(name):
    retries = 0
    while retries < 100:
        try:
            return requests.get(name, timeout)
        except (requests.exceptions.ConnectionError, requests.exceptions.Timeout) as e:
            logging.warning(f'Error: {e}')
            logging.warning(f'Waiting {timeout} seconds and try again ...')
            # concurrent.futures.wait(timeout=timeout)
            tm.sleep(timeout)
            retries += 1
            if retries >= 100:
                print(f'Lost name {name}')
                logging.error(f'Lost name {name}')


# Download and write file
def download_tile(first_tile, last_tile, count_tiles):
    for x in range(first_tile, last_tile):
        for y in range(0, count_tiles):
            Path("out").mkdir(exist_ok=True)
            fname = 'out/z%d_x%d_y%d.png' % (zoom, x, y)
            lname = """https://maps.googleapis.com/maps/vt?pb=!1m5!1m4!1i%d!2i%d!3i%d!4i256!2m3!1e0!2sm!%s""" \
                    % (zoom, x, y, YOUR_CODE)

            request = get_request(lname)

            with open(fname, "wb") as f:
                f.write(request.content)


def main():
    nthreads = ntiles  # May be any value not greater than n_tiles

    start_time = tm.time()

    if nthreads > ntiles:
        warnings.warn("Number of threads should be greater then number of tiles", FutureWarning)
        nthreads = ntiles
    print(f'zoom: {zoom} threads: {nthreads} tiles: {ntiles ** 2}')

    # Generate list of xyz and divide it to num_threads
    array = [0] * (nthreads + 1)
    for i, j in zip(range(nthreads + 1), np.linspace(0, ntiles, (nthreads + 1))):
        array[i] = int(j)

    print("Starting ProcessPoolExecutor")
    with concurrent.futures.ProcessPoolExecutor(max_workers=nthreads) as executor:
        for i in range(nthreads):
            executor.submit(download_tile, array[i], array[i + 1], array[nthreads])

    print(f"{tm.time() - start_time:8.3f} seconds completed")


if __name__ == '__main__':
    main()
