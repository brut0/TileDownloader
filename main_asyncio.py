import time as tm
import numpy as np
import requests as requests
import warnings
import logging
import asyncio
import itertools
from pathlib import Path

logging.basicConfig(filename='log.log')

zoom: int = 5
timeout = 1
ntiles = 1 << zoom
YOUR_CODE = ""


# Get request from 'name'
async def get_request(name):
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
async def download_tile(sem, first_tile, last_tile, count_tiles):
    for x in range(first_tile, last_tile):
        for y in range(0, count_tiles):
            Path("out").mkdir(exist_ok=True)
            fname = 'out/z%d_x%d_y%d.png' % (zoom, x, y)
            lname = """https://maps.googleapis.com/maps/vt?pb=!1m5!1m4!1i%d!2i%d!3i%d!4i256!2m3!1e0!2sm!%s""" \
                    % (zoom, x, y, YOUR_CODE)

            async with sem:
                request = await get_request(lname)

            with open(fname, "wb") as f:
                f.write(request.content)


async def main():
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

    tasks = set()
    sem = asyncio.Semaphore(2)
    for i in range(nthreads):
        task = asyncio.create_task(download_tile(array[i], array[i + 1], array[nthreads]))
        tasks.add(task)
    return await asyncio.gather(*tasks)

#    print("Starting ProcessPoolExecutor")
#    with concurrent.futures.ProcessPoolExecutor(max_workers=nthreads) as executor:
#        for i in range(nthreads):
#            executor.submit(download_tile, array[i], array[i + 1], array[nthreads])

    print(f"{tm.time() - start_time:8.3f} seconds completed")


if __name__ == '__main__':
    asyncio.run(main())

MAX_SIM_CONNS = 50
LAST_ID = 10**6

async def fetch(url, session):
    async with session.get(url) as response:
        return await response.read()

async def bound_fetch(sem, url, session):
    async with sem:
        await fetch(url, session)

async def fetch_all():
    url = "http://localhost:8080/?id={}"
    tasks = set()
    async with ClientSession() as session:
        sem = asyncio.Semaphore(MAX_SIM_CONNS)
        for i in range(1, LAST_ID + 1):
            task = asyncio.create_task(bound_fetch(sem, url.format(i), session))
            tasks.add(task)
        return await asyncio.gather(*tasks)

if __name__ == '__main__':
    asyncio.run(fetch_all())