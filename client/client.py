import sys
import requests

def print_transaction_inputs(data):
    print("\t\tinputs:")
    for dict_item in data:
        print("\n\t\t\ttransaction_input")
        for key in dict_item:
            print("\t\t\t{}: {},".format(key,dict_item[key]))

def print_transaction_outputs(data):
    print("\t\toutputs:")
    for dict_item in data:
        print("\n\t\t\ttransaction_output")
        for key in dict_item:
            print("\t\t\t{}: {},".format(key,dict_item[key]))

def print_block(data):
    print("Last validated Block:")
    print("\tindex: {},".format(data["index"]))
    print("\tprevious_hash: {},".format(data["previous_hash"]))
    print("\ttimestamp: {},".format(data["timestamp"]))
    print("\ttransactions:")
    for dict_item in data["transactions"]:
        print("\n\t\ttransaction")
        for key in dict_item:
            if key == 'inputs':
                print_transaction_inputs(dict_item[key])
            elif key == 'outputs':
                print_transaction_outputs(dict_item[key])
            else:
                print("\t\t{}: {},".format(key,dict_item[key]))
    print("\tnonce: {},".format(data["nonce"]))
    print("\tcurrent_hash: {},".format(data["current_hash"]))

def err_print(status_code):
    if not (status_code == requests.codes.ok):
        print("Some error occurred\n")
        quit()

if sys.argv[1] == 't':
    payload = {
        "dst": sys.argv[2],
        "amount": sys.argv[3]
    }
    r = requests.post("localhost:5000/transaction", json=payload)
    err_print(r.status_code)

elif sys.argv[1] == 'view':
    r =  requests.get("localhost:5000/history")
    err_print(r.status_code)
    print_block(r.json()["block"])

elif sys.argv[1] == 'balance':
    payload = {
        "walletId": "321312" # random value
    }
    r =  requests.get("localhost:5000/balance", data=payload)
    err_print(r.status_code)
    print("balance:",r.json()["balance"])

elif sys.argv[1] == 'help':
    print("t <recipient_address> <amount>: send to recipient_address the amount of NBC coins from the wallet of sender_address.\n")
    print("view: view last transactions of noobcash blockchain's last validated block.\n")
    print("balance: view wallet's balance.")