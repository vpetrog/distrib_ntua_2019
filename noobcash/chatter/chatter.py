from multiprocessing.pool import ThreadPool
import itertools
import requests
from noobcash.blockchain.util import get_ip, bintos


def send_post_request(node_id, payload, arg):
    requests.post("http://" + get_ip(node_id)["ipAddr"] + ":" + get_ip(node_id)["port"] + \
                      "/" + arg, json=payload)


def send_get_request(node_id, payload, arg):
    requests.get("http://" + get_ip(node_id)["ipAddr"] + ":" + get_ip(node_id)["port"] + \
                     "/" + arg, json=payload)


def broadcast_transaction(trans_data, node_ids, blocking=False):
    payload = {"transData": trans_data.dumps()}
    p = ThreadPool(len(node_ids))
    if blocking:
        p.starmap(send_post_request,
                  (node_ids, itertools.repeat(payload), itertools.repeat("transaction")))
    else:
        p.starmap_async(send_post_request,
                        zip(node_ids, itertools.repeat(payload), itertools.repeat("transaction")))


def broadcast_block(block_data, node_ids, blocking=False):
    payload = {"blockData": block_data.dumps()}
    p = ThreadPool(len(node_ids))
    if blocking:
        p.starmap(send_post_request,
                  zip(node_ids, itertools.repeat(payload), itertools.repeat("block")))
    else:
        p.starmap_async(send_post_request,
                        zip(node_ids, itertools.repeat(payload), itertools.repeat("block")))


def get_blockid(blockId, node_ids, blocking=False):
    payload = {"block": bintos(blockId)}
    p = ThreadPool(len(node_ids))
    if blocking:
        p.starmap(send_get_request,
                  (node_ids, itertools.repeat(payload), itertools.repeat("block")))
    else:
        p.starmap_async(send_get_request,
                        zip(node_ids, itertools.repeat(payload), itertools.repeat("block")))