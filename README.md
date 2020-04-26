# BITS F463 CRYPTOGRAPHY course project

## Installation

1. Make sure [Python 3.6+](https://www.python.org/downloads/) is installed.
2. install virtualenv
```
$ pip install virtualenv
```
3. create a virtual environment
```
$ virtualenv venv -p python3
```
4. Activate environment
```
$ deactivate &> /dev/null; source ./venv/bin/activate
```
5. Install requirements
```
$ pip install -r requirements.txt
```
6. Run the project
```
$ python blockchain.py
```
> if python2 is installed replace pip with pip3 in the second step
>
> If the port is already used replace it with a different port or use the following meathod
```
$ netstat -tupln
```
from here find the pid of the programme using port 5000, kill it using the follwng command
```
$ kill -9 (pid from the above step)
```

___

Make sure [Postman](https://www.postman.com/) is installed, postman is a tool used to make web requests

* GET: 'http://0.0.0.0:5000/mine' - creates new block with proof of work
* POST: 'http://0.0.0.0:5000/transactions/new' - create new transactions
* GET: 'http://0.0.0.0:5000/chain' - shows the full blockchain
* POST: 'http://0.0.0.0:5000/nodes/register' - will register the node for send nodes address
* GET: 'http://0.0.0.0:5000/nodes/resolve' - This will valid the longest chain in blockchain and shows the authoritized chain
