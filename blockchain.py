# refernce https://hackernoon.com/learn-blockchains-by-building-one-117428612f46
import hashlib
import json
from textwrap import dedent
from time import time
from uuid import uuid4
from urllib.parse import urlparse

from flask import Flask, jsonify, request


class Blockchain(object):

    def proof_of_work(self, last_proof):
        """
         Simple Proof of Work Algorithm:
         - Find a number p' such that hash(pp') contains leading 4 zeroes, where p is the previous p'
         - p is the previous proof, and p' is the new proof
        :param last_proof: <int>
        :return: <int>
        """
        proof = 0
        while self.valid_proof(last_proof, proof) is False:
            proof += 1
        return proof

    @staticmethod
    def valid_proof(last_proof, proof):
        """
        Validates the Proof: Does hash(last_proof, proof) contain 4 leading zeroes?
        :param last_proof: <int> Previous Proof
        :param proof: <int> Current Proof
        :return: <bool> True if correct, False if not.
        """
        guess = f'{last_proof}{proof}'.encode()
        guess_hash = hashlib.sha256(guess).hexdigest()
        return guess_hash[:4] == "0000"

    # constructor
    def __init__(self):
        self.chain = []
        self.current_transaction = []
        self.nodes = set()
        # set because every node  is unique and no repeats are allowed to register

        # create the genesis block
        self.new_block(previous_hash=1, proof=100)

    def new_block(self, proof, previous_hash=None):
        """
        Create a new Block in the Blockchain
        :param proof: <int> The proof given by the Proof of Work algorithm
        :param previous_hash: (Optional) <str> Hash of previous Block
        :return: <dict> New Block
        """
        block = {
            'index': len(self.chain) + 1,
            'timestamp': time(),
            'transactions': self.current_transaction,
            'proof': proof,
            'previous_hash': previous_hash or self.hash(self.chain[-1]),
        }
        # reset current lost of transaction
        self.current_transaction = []

        self.chain.append(block)
        return block

    def new_transaction(self, product_id, recipient, location):
        # Adds a new transaction to the list of transactions
        self.current_transaction.append({
            'product_id': product_id,
            'recipient': recipient,
            'location': location,
        })
        return self.last_block['index'] + 1

    @property
    def last_block(self):
        return self.chain[-1]

    @staticmethod
    def hash(block):
        """
        Created a Sha-256 hash of a block
        :param block: <dict> Block
        :return: <str>
        """
        # We must make sure that the Dictionary is Ordered, or we'll have inconsistent hashes

        block_string = json.dumps(block, sort_keys=True).encode()
        return hashlib.sha256(block_string).hexdigest()

    def register_node(self, address):
        """
        Add a new node to the list of nodes
        :param address: <str> Address of node like: 'http://192.168.0.5:5000'
        :return: None
        """
        parsed_url = urlparse(address)
        self.nodes.add(parsed_url.netloc)

    def valid_chain(self, chain):
        """
        Determine if a given blockchain is valid or not
        :param chain: <list> a blockchain
        :return: true if valid else return false
        """
        last_block = chain[0]
        current_index = 1
        while current_index < len(chain):
            block = chain[current_index]
            print(f'{last_block}')
            print(f'{block}')
            print("\n-----------\n")
            # checking that the hash of the block is correct
            if block['pervious_hash'] != self.hash(last_block):
                return False
            # checking that the proof of work is correct
            if not self.valid_proof(last_block['proof'], block['proof']):
                return False

            last_block = block
            current_index += 1
        return True

    def resolve_conflicts(self):
        """
        Consensus Algorithm,it resloves conflicts by
        replacing our chain with longest one in the network
        :return: <bool> true if our chain was replaced,false of not
        """
        neighbours = self.nodes
        new_chain = None
        max_length = len(self.chain)

        # looking only towards longest chains
        for node in neighbours:
            response = requests.get(f'http://{node}/chain')

            if response.status_code == 200:
                length = response.json()['length']
                chain = response.json()['chain']
                if length > max_length and self.valid_chain(chain):
                    max_length = length
                    new_chain = chain
        if new_chain:
            self.chain = new_chain
            return True
        return False


# Instantiate our Node


app = Flask(__name__)

# Generate a globally unique address for this node
node_identifier = str(uuid4()).replace('-', '')

# Instantiate the Blockchain
blockchain = Blockchain()

@app.route('/')
def homeroute():
    return("This is the home route of blockchain project")
@app.route('/mine', methods=['GET'])
def mine():
    # We run the proof of work algorithm to get the next proof
    last_block = blockchain.last_block
    last_proof = last_block['proof']
    proof = blockchain.proof_of_work(last_proof)

    # We must receive a reward for finding the proof
    # The product_id is "0" to signify that this node has mined a new coin.
    blockchain.new_transaction(
        product_id="0",
        recipient=node_identifier,
        location="",
    )

    # forge the new Block by adding it to the chain
    pervious_hash = blockchain.hash(last_block)
    block = blockchain.new_block(proof, pervious_hash)

    response = {
        'message': "New block forged",
        'index': block['index'],
        'transactions': block['transactions'],
        'proof': block['proof'],
        'previous_hash': block['previous_hash'],
    }
    return jsonify(response), 200


@app.route("/transactions/new", methods=['POST'])
def new_transaction():
    values = request.get_json()

    # check that the required fields are in the POST'ed data
    required = ['product_id', 'recipient', 'location']
    if not all(k in values for k in required):
        return "Missing values", 400

    # create a new transaction
    index = blockchain.new_transaction((values['product_id'], values['recipient']), values['location'])

    response = {'message': f'Transaction will be added to block {index}'}
    return jsonify(response), 201


@app.route("/chain", methods=["GET"])
def full_chain():
    response = {
        'chain': blockchain.chain,
        'length': len(blockchain.chain),
    }
    return jsonify(response), 200


# due to consensus issue where the whole changes reflecting in one node is not decentralization..so we register nodes
# on the network


@app.route("/nodes/register", methods=["POST"])
def register_nodes():
    values = request.get_json()
    nodes = values.get('nodes')
    if nodes is None:
        return "Error :Please send a valid list of nodes", 400
    for node in nodes:
        blockchain.register_node(node)
    response = {
        'message': 'New nodes have been added to register',
        'total_nodes': list(blockchain.nodes),
    }
    return jsonify(response), 201


@app.route("/nodes/resolve", methods=["GET"])
def consensus():
    message = blockchain.resolve_conflicts()
    if message:
        response = {
            'message': 'Chain was replaced with longest length',
            'new_chain': blockchain.chain,
        }
    else:
        response = {
            'message': 'Chain is authoritative',
            'chain': blockchain.chain,
        }
    return jsonify(response), 200


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
