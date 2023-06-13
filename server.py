    #Final Project
    #5 servers.py
    #There are 5 servers that communicate with each other
    #They all handle:
    #   userInfo
    #   user's blog
    #   log of all plog operations as blockchain

    # It will use multipaxos to reach consensus on what to append to blockchain
    # no malicious fails, but 
    # CRASHES, FAILSTOP, PARTITIONS are allowed

    #THE APPLICATION
    #WE have a blog like data structure
    #Operations on the blog DS are maintained as blockchain
    #Features: 
    #   users can make blog posts
    #   comments on user posts
    #   view posts & comments

import socket
import threading

from socket import *
from os import _exit
from sys import stdout
from time import sleep
import time
import os
from hashlib import sha256
import array as arr
import collections
import sys
import heapq

class Operation():
    op = None
    username = None
    title = None
    content = None
    def __init__(self, op, username, title, content):
        self.op = op
        self.username = username
        self.title = title
        self.content = content

    def print(self):
        return "(" + self.op + ", " + self.username + ", " + self.title + ", " + self.content + ")"
    def getOperation(self):
        return self.op + self.username + self.title + self.content
    def equals(self, op):
        if(self.print() == op.print()):
            return True
        return False

class Block():
    hash = None
    operation = None
    nonce = None
    ballot = None
    def __init__(self, ha, trans, no):
        self.hash = ha
        self.operation = trans
        self.nonce = no
    def print(self):
        return "(" + self.operation.print() + ", " + str(self.hash) + ", " + str(self.ballot) + ")"
    def getOperation(self):
        return self.operation.getOperation()
    def parse(self):
        return f"{self.hash} {self.operation.print()} {self.nonce} {self.ballot[0]} {self.ballot[1]} {self.ballot[2]}"
    def equals(self, block):
        if(self.parse() == block.parse()):
            return True
        return False
def getNonce(hashCurr, oCurr):
    nonce = 0
    while True:
        if(int(sha256((hashCurr + oCurr + str(nonce)).encode('utf-8')).hexdigest()[0], 16) <= 1):
            return nonce
        else:
            nonce += 1

class Post():
    title = None
    author = None
    content = None
    comments = None
    def __init__(self, title, author, content):
        self.title = title
        self.author = author
        self.content = content
        self.comments = []
    def printPost(self):
        #for post
        return self.title + " by " + self.author + "\n"
    def printPostsByUser(self):
        #for posts by user
        return self.title + " - " + self.content + "\n"
    def printAllComments(self):
        commentString = ""
        for comment in self.comments:
            commentString = commentString + comment.username + "\n---------\n" + comment.content + "\n\n"
        return commentString
    def printComments(self):
        #for comments on post
        return self.printPostsByUser() + "Comments:\n" + self.printAllComments()
#GLOBAL BLOG VARIABLE, FILLED WITH POSTS
Blog = []

decision = []

currLead = "P0"
users = {}
leaderPromise = {}
promiseOps = {}
promiseOp = None


blockIndex = 0
blockchain = []

opQueue = []

failLink = {}

pid = int(sys.argv[1][1])
seqId = [-1,pid]

ballotNum = [(0,0)]
acceptNum = [(0,0)]
acceptVal = [Operation("Bottom", "Bottom", "Bottom", "Bottom")]

acceptMap = {}

  
#maps ballot nums to Operations
ballots = {}

def blockParse(line):
    firstSplit = line.split('(')
    secondSplit = firstSplit[1].split(') ')
    tagHash = firstSplit[0].split()
    tag = tagHash[0]
    hash = tagHash[1]
    operationString = secondSplit[0].split(', ')
    operation = Operation(operationString[0], operationString[1], operationString[2], operationString[3])
    nonceBallot = secondSplit[1].split()
    nonce = nonceBallot[0]
    seq = int(nonceBallot[1])
    id = int(nonceBallot[2])
    depth = int(nonceBallot[3])
    block = Block(hash, operation, nonce)
    block.ballot = (int(seq), int(id), int(depth))
    return (tag, block)

def getNewBallot():
    global seqId
    global blockIndex
    seqId = (seqId[0] + 1, seqId[1])
    return (seqId[0],seqId[1],blockIndex)

def tentativeWriteBlock(block):
    file_path = f"{sys.argv[1]}.txt"
    with open(file_path, "a") as file:
        if os.path.getsize(file_path) != 0:
            file.write(f"\ntentative {block.parse()}")
        else:
            file.write(f"tentative {block.parse()}")

def decideWriteBlock(block):
    file_path = f"{sys.argv[1]}.txt"
    content = None
    with open(file_path, "r") as file:
        content = file.readlines()
    
    modified_content = []
    for line in content:
        blockTuple = blockParse(line)
        if(blockTuple[1].equals(block)):
            modified_content.append(f"decided {block.parse()}")
        else:
            modified_content.append(line)

    with open(file_path, "w") as file:
        file.writelines(modified_content)

def writeBlock(block):
    file_path = f"{sys.argv[1]}.txt"
    with open(file_path, "a") as file:
        if os.path.getsize(file_path) != 0:
            file.write(f"\ndecided {block.parse()}")
        else:
            file.write(f"decided {block.parse()}")
    
def writeBlog(op):
    #add the decided operation
    file_path = f"{sys.argv[1]}b.txt"
    with open(file_path, "a") as file:
        if os.path.getsize(file_path) != 0:
            file.write(f"\n{op.print()}")
        else:
            file.write(op.print())
def addOpLeader(op):
    global blockIndex
    if(op.op == "POST"):
        duplicate = False
        for i in Blog:
            if(i.title == op.title):
                print("DUPLICATE TITLE FOUND", flush = True)
                duplicate = True
        if not duplicate:
            post = Post(op.title, op.username, op.content)
            Blog.append(post)
            print(f"NEW POST {op.title} from {op.username}")
    if(op.op == "COMMENT"):
        commented = False
        for i in Blog:
            if(i.title == op.title):
                i.comments.append(op)
                print(f"NEW COMMENT on {op.title} from {op.username}")
                commented = True
        if not commented:
            print("CANNOT COMMENT", flush = True)
    ballotNum.append((0,0))
    acceptNum.append((0,0))
    acceptVal.append(Operation("Bottom", "Bottom", "Bottom", "Bottom"))
    blockIndex += 1
    decision.append(op)
    threading.Thread(target = writeBlog, args = (op,)).start()
    return

def addOpReceiver(op):
    global blockIndex
    if(op.op == "POST"):
        duplicate = False
        for i in Blog:
            if(i.title == op.title):
                print("DUPLICATE TITLE FOUND", flush = True)
                duplicate = True
        if not duplicate:
            post = Post(op.title, op.username, op.content)
            Blog.append(post)
            print(f"NEW POST {op.title} from {op.username}")
    if(op.op == "COMMENT"):
        for i in Blog:
            if(i.title == op.title):
                i.comments.append(op)
                print(f"NEW COMMENT on {op.title} from {op.username}")
    ballotNum.append((0,0))
    acceptNum.append((0,0))
    acceptVal.append(Operation("Bottom", "Bottom", "Bottom", "Bottom"))
    blockIndex += 1
    decision.append(op)
    threading.Thread(target = writeBlog, args = (op,)).start()
    return

def checkLeaderPromise(ballot):
    count = 0
    for i in leaderPromise[ballot]:
        count += i
    if(count >= 3):
        return True
    return False

changed = False
opUpdated = None

def becomeProposer(op):
    global currLead, promiseOp, changed, opUpdated
    ballot = getNewBallot()
    leaderPromise[ballot] = [0,0,0,0,0]
    leaderPromise[ballot][pid-1] = 1
    for i in users.keys():
        if(failLink[users[i]]):
            serverSocket.sendto(f"prepare {ballot[0]} {ballot[1]} {ballot[2]}".encode(), ('127.0.0.1', i))
            print(f"PREPARE SENT TO {users[i]} ({ballot[0]},{ballot[1]},{ballot[2]})")
    start_time = time.time()
    while not checkLeaderPromise(ballot):
        end_time = time.time()
        if(end_time - start_time > 10):
            print("COULDN'T GET PROMISES")
            for j in range(len(opQueue)):
                if opQueue[j].equals(op):
                    opQueue.pop(j)
                    break
            return
        continue
    
    max = (ballot[0],ballot[1])
    changed = max
    for i in promiseOps.keys():
        if(int(i[0]) > max[0]):
            changed = i
        elif (int(i[0]) == max[0] and int(i[1]) > max[1]):
            changed = i
    if(str(max[0]) != str(changed[0]) and str(max[1] != str(changed[1]))):
        #update the value
        print("found new val updating values...", flush= True)
        promiseOp = promiseOps[changed]
        changed = True
        opUpdated = op
    print("Became leader, propose phase done", flush = True)
    currLead = f"P{pid}" 

def checkAccept(ballot):
    accepts =  acceptMap[ballot]
    count = 0
    for i in accepts:
        count += i
    if(count >= 3):
        return True
    return False

def checkReceivedDecision(userInput):
    split = userInput.split(', ')
    ty = userInput.split('(')[0]
    username = split[0].split('(')[1]
    title = split[1]
    content = split[2][:-1]
    operationToCheck = Operation(ty, username, title, content)
    for i in decision:
        if(operationToCheck.equals(i)):
            for j in range(len(opQueue)):
                if opQueue[j].equals(operationToCheck):
                    opQueue.pop(j)
                    break
            print("FOUND DECISION")
            return True
    
    return False

def findPort(user):
    for i in users.keys():
        if users[i] == user:
            return i

def handleOp(newOp, userInput):
    global currLead
    global blockIndex
    global changed
    # check if you need to send to a different person
    #if they don't respond become proposer
    if(int(currLead[1]) != pid and int(currLead[1]) != 0):
        if failLink[currLead]:
            serverSocket.sendto(userInput.encode(), ('127.0.0.1', findPort(currLead)))
            print(f"Forwarded to {users[findPort(currLead)]}", flush = True)
        start_time = time.time()
        failed = False
        while(not checkReceivedDecision(userInput)):
            end_time = time.time()
            if(end_time - start_time > 30):
                print(f"TIMEOUT")
                threading.Thread(target=becomeProposer, args=(newOp,)).start()
                failed = True
                break
        if(not failed):
            return
    elif(int(currLead[1]) == 0):
        threading.Thread(target=becomeProposer, args=(newOp,)).start()
    
    
    try:
        while(not opQueue[0].equals(newOp) or int(currLead[1]) != pid):
            continue
    except IndexError:
        return
    #This operation is at front of queue, and I am the leader
    #set a new ID (keep seqId, just update the depth)
    #put the newOP in requires lists
    ballot = (seqId[0], seqId[1], blockIndex)
    ballot = ballot
    if(changed):
        if opUpdated == None:
            ballots[ballot] = newOp
            changed = False
        else:
            ballots[ballot] = promiseOp
            changed = False
    else:
        ballots[ballot] = newOp
    ballotNum[blockIndex] = (ballot[0], ballot[1])
    print(ballot)
    print("STARTING ACCEPT PHASE..", flush = True)
    acceptMap[ballot] = [0,0,0,0,0]
    
    
    block = None
    if(blockIndex == 0):
        sfzero = ""
        for i in range(64):
            sfzero += "0"
        block = Block(sfzero, ballots[ballot], getNonce(sfzero, ballots[ballot].getOperation()))
        block.ballot = ballot
    else:
        
        lastBlock = blockchain[len(blockchain) - 1]
        lastBlockHash = str(lastBlock.hash)
        lastBlockTransaction = lastBlock.getOperation()
        lastBlockNonce = str(lastBlock.nonce)
        newHash = sha256((lastBlockHash+lastBlockTransaction+lastBlockNonce).encode('utf-8')).hexdigest()
        nonce = getNonce(str(newHash),ballots[ballot].getOperation())
        block = Block(newHash, ballots[ballot], nonce)
        block.ballot = ballot

    for i in users.keys():
        #check for failed link
        if(failLink[users[i]]):
            serverSocket.sendto(f"accept {block.parse()}".encode(), ('127.0.0.1', i))
            print(f"ACCEPT sent to {users[i]}: {ballot[0]} {ballot[1]} {ballot[2]}", flush = True)
    #set personal accept map to correct
    
    acceptMap[ballot][pid-1] = 1
    start_time = time.time()
    while not checkAccept(ballot):
        end_time = time.time()
        if(end_time - start_time > 10):
            print("DIDN'T GET ENOUGH ACCEPTS, TRY AGAIN?")
            opQueue.pop(0)
            return
        continue

    threading.Thread(target = writeBlock, args = (block,)).start()
    #received all the accepts
    #decide the value
    
    blockchain.append(block)
    addOpLeader(ballots[ballot])
    for i in users.keys():
        if(failLink[users[i]]):
            serverSocket.sendto(f"decide {block.parse()}".encode(), ('127.0.0.1', i))
            print(f"DECIDE sent to {users[i]}: {ballot[0]} {ballot[1]} {ballot[2]}")
    opQueue.pop(0)

def get_user_input():
    global seqId
    while True:
        try:
            userInput = input()
            # close all sockets before exiting

            if(userInput[0:4] == "wait"):
                sleep(int(userInput[5:]))
            
            
            # flush console output buffer in case there are remaining prints
            # that haven't actually been printed to console
            if(userInput == "print"):
                print(users)
            if(userInput == "leader"):
                print(currLead)
            if(userInput == "blockindex"):
                print(blockIndex)
            if(userInput == "acceptVal"):
                for i in acceptVal:
                    print(i.print())
            if(userInput == "crash"):
                
                # print("exiting program", flush=True)
                serverSocket.close()

                stdout.flush() # imported from sys library
                # exit program with status 0
                _exit(0) # imported from os library
                            
            if(userInput == "blockchain"):
                stringChain = "["
                if len(blockchain) != 0:
                    for i in blockchain:
                        stringChain += i.print() + ", "
                    print(stringChain[:-2] + "]")
                else:
                    print("[]")

            if(userInput[:8]== "failLink"):
                split = userInput.split('(')
                username = split[1][:-1]
                failLink[username] = False
            
            if(userInput[:7]== "fixLink"):
                split = userInput.split('(')
                username = split[1][:-1]
                failLink[username] = True
            
            if(userInput[:8] == "increase"):
                seqId = (seqId[0] + 1, seqId[1])
            
            if(userInput == "queue"):
                stringChain = ""
                for i in opQueue:
                    stringChain += i.print()
                print(stringChain, flush= True)

            if(userInput[0:4] == "POST"):
                #todo\
                split = userInput.split(', ')
                username = split[0].split('(')[1]
                title = split[1]
                content = split[2][:-1]
                newOp = Operation("POST", username, title, content)
                opQueue.append(newOp)
                threading.Thread(target=handleOp, args=(newOp, userInput,)).start()

                
            if(userInput[0:7] == "COMMENT"):
                #todo\
                split = userInput.split(', ')
                username = split[0].split('(')[1]
                title = split[1]
                content = split[2][:-1]
                newOp = Operation("COMMENT", username, title, content)
                opQueue.append(newOp)
                threading.Thread(target=handleOp, args=(newOp, userInput,)).start()

            if(userInput == "blog"):
                stringChain = "Printing Blog:\n"
                if len(Blog) == 0:
                    print("BLOG EMPTY", flush = True)
                    continue
                for i in Blog:
                    stringChain += i.printPost()
                print(stringChain, flush=True)
            
            if(userInput[:4] == "view"):
                split = userInput.split('(')
                username = split[1][:-1]
                stringChain = f"Printing posts by {username}:\n"
                count = 0
                for i in Blog:
                    if i.author == username:
                        stringChain += i.printPostsByUser()
                        count += 1
                if (count == 0):
                    print(f"{username} NO POST")
                    continue
                print(stringChain, flush= True)
            
            if(userInput[:4] == "read"):
                split = userInput.split('(')
                title = split[1][:-1]
                stringChain = f"Printing post {title}:\n"
                exists = False
                for i in Blog:
                    if i.title == title:
                        stringChain += i.printComments()
                        exists = True
                        break
                if exists:
                    print(stringChain, flush= True)
                    continue
                
                print("POST NOT FOUND", flush = True)
            
            if(userInput[:7] == "connect"):
                split = userInput.split()
                port = split[1]
                serverSocket.sendto(f"Hi {sys.argv[1]}".encode(), ('127.0.0.1', int(port)))
        except EOFError or AttributeError or IndexError:
            continue


def handle_msg(data, port):
    global seqId
    data = data.decode()
    if(data[:3] == "Hai"):
        user = data.split()[1]
        users[port] = user
        failLink[user] = True
    sleep(3)
    

    if(users.get(port)):
        if(not failLink[users.get(port)]):
            return

    if(data[:2] == "Hi"):
        user = data.split()[1]
        users[port] = user
        failLink[user] = True
        print("connected with " + str(port))
        serverSocket.sendto(f"Hai {sys.argv[1]}".encode(), ('127.0.0.1', int(port)))

    

    if(data[:7] == "prepare"):
        global ballotNum, acceptNum, acceptVal, blockIndex
        split = data.split()
        seq = int(split[1])
        id = int(split[2])
        depth = int(split[3])
        print(f"PREPARE RECEIVED FROM {users[port]}: ({seq},{id},{depth})", flush=True)
        if(depth > blockIndex):
            missing = depth - blockIndex
            for i in range(missing):
                ballotNum.append((0,0))
                acceptNum.append((0,0))
                acceptVal.append(acceptVal.append(Operation("Bottom", "Bottom", "Bottom", "Bottom")))
            blockIndex = depth
        if(blockIndex > depth):
            return
        currBall = ballotNum[depth]
        #if it is bigger than the current Ballot send PROMISE you won't accept
        if(seq > currBall[0] or (seq == currBall[0] and id > currBall[1])):
            ballotNum[depth] = (seq, id)
            serverSocket.sendto(f"promise {seq} {id} {depth} {acceptNum[depth][0]} {acceptNum[depth][1]} {acceptVal[depth].print()}".encode(), ('127.0.0.1', int(port)))
            print(f"PROMISE SENT TO {users[port]}: ({seq},{id},{depth})", flush=True)
        else:
            #don't send promise, ignore
            return

    
    if(data[:7] == "promise"):
        #you will only get this if you send a prepare
        split = data.split('(')
        first = split[0]
        second = split[1]
        ballotNumB = first.split(' ')
        operation = second.split(')')[0].split(', ')
        ballot = (int(ballotNumB[1]), int(ballotNumB[2]), int(ballotNumB[3]))
        print(f"PROMISE RECEIVED FROM {users[port]}: ({ballot[0]},{ballot[1]},{ballot[2]})", flush=True)
        accept = (ballotNumB[4], ballotNumB[5])
        if(operation[0] == "Bottom"):
            #it never see no other ballot
            pass
        else:
            #it did go put in map
            promiseOps[accept] = Operation(operation[0], operation[1], operation[2], operation[3])
        #mark that this user sent you promise (index weird)
        leaderPromise[ballot][int(users[port][1])-1] = 1

    if(data[:7] == "accept "):
        split = data.split('(')
        first = split[0]
        second = split[1]
        hash = first.split()[1]
        secondSplit = second.split(') ')
        ballotString = secondSplit[0].split(', ')
        nonceBallot = secondSplit[1].split()

        nonce = nonceBallot[0]
        seq = int(nonceBallot[1])
        id =int(nonceBallot[2])
        depth = int(nonceBallot[3])
        ballot = (seq, id, depth)
        newOperation = Operation(ballotString[0], ballotString[1], ballotString[2], ballotString[3])
        block = Block(hash, newOperation, nonce)
        block.ballot = ballot
        if(seq > seqId[0]):
            seqId = (seq, seqId[1])
        print(f"ACCEPT RECEIVED FROM {users[port]}: ({seq},{id},{depth})", flush=True)
        if(depth > blockIndex):
            missing = depth - blockIndex
            for i in range(missing):
                ballotNum.append((0,0))
                acceptNum.append((0,0))
                acceptVal.append(acceptVal.append(Operation("Bottom", "Bottom", "Bottom", "Bottom")))
            blockIndex = depth
        if(blockIndex > depth):
            return
        threading.Thread(target= tentativeWriteBlock, args = (block,)).start()
        currBall = ballotNum[depth]
        if(seq > currBall[0] or (seq == currBall[0] and id >= currBall[1])):
            acceptNum[depth] = (seq, id)
            acceptVal[depth] = newOperation
            serverSocket.sendto(f"accepted {seq} {id} {depth}".encode(), ('127.0.0.1', int(port)))
            print(f"ACCEPTED ({seq},{id},{depth}) sent to {users[int(port)]}")
    
    if(data[:8] == "accepted"):
        split = data.split()
        seq = int(split[1])
        id = int(split[2])
        depth = int(split[3])
        print(f"ACCEPTED received from {users[port]}: ({seq},{id},{depth})", flush=True)
        acceptMap[(seq,id,depth)][int(users[port][1]) - 1] = 1

    if(data[:6] == "decide"):
        split = data.split('(')
        first = split[0]
        second = split[1]
        hash = first.split()[1]
        secondSplit = second.split(') ')
        ballotString = secondSplit[0].split(', ')
        nonceBallot = secondSplit[1].split()
        seq = int(nonceBallot[1])
        id =int(nonceBallot[2])
        depth = int(nonceBallot[3])
        nonce = nonceBallot[0]
        ballot = (nonceBallot[1], nonceBallot[2], nonceBallot[3])
        print(f"DECIDE received from {users[port]}: ({ballot[0]},{ballot[1]},{ballot[2]})", flush=True)
        newOperation = Operation(ballotString[0], ballotString[1], ballotString[2], ballotString[3])
        block = Block(hash, newOperation, nonce)
        block.ballot = (seq, id, depth)
        global currLead
        currLead = users[port]
        if(blockIndex > depth):
            return
        threading.Thread(target = decideWriteBlock, args = (block,)).start()
        blockchain.append(block)
        addOpReceiver(newOperation)
        
        
    if(data[0:4] == "POST"):
            #todo\
        split = data.split(', ')
        username = split[0].split('(')[1]
        title = split[1]
        content = split[2][:-1]
        newOp = Operation("POST", username, title, content)  
        opQueue.append(newOp)
        threading.Thread(target=handleOp, args=(newOp, data,)).start()

            
    if(data[0:7] == "COMMENT"):
        #todo\
        split = data.split(', ')
        username = split[0].split('(')[1]
        title = split[1]
        content = split[2][:-1]
        newOp = Operation("COMMENT", username, title, content)
        opQueue.append(newOp)
        threading.Thread(target=handleOp, args=(newOp, data,)).start()
   

    
def connect():
    sleep(3)
    users = [9001,9002,9003,9004,9005]
    for i in users:
        if i != SERVER_PORT:
            serverSocket.sendto(f"Hi {sys.argv[1]}".encode(), ('127.0.0.1', i))


def initializeOp(op):
    global Blog, ballotNum, acceptNum, acceptVal
    if(op.op == "POST"):
        duplicate = False
        for i in Blog:
            if(i.title == op.title):
                duplicate = True
        if not duplicate:
            post = Post(op.title, op.username, op.content)
            Blog.append(post)
    if(op.op == "COMMENT"):
        for i in Blog:
            if(i.title == op.title):
                i.comments.append(op)     
    decision.append(op)
    return

def parseOp(op):
    split = op.split('(')
    second = split[1]
    operationString = second.split(')')[0].split(', ')
    operation = Operation(operationString[0], operationString[1], operationString[2], operationString[3])
    return operation

def initialize():
    global Blog, blockchain, blockIndex
    file_path = f"{sys.argv[1]}.txt"
    if os.path.getsize(file_path) != 0:
        with open(file_path, "r") as file:
            for line in file:
                block = blockParse(line)
                if(block[0] == "decided"):
                    blockchain.append(block[1])
                    ballotNum.append((0,0))
                    acceptNum.append((0,0))
                    acceptVal.append(Operation("Bottom", "Bottom", "Bottom", "Bottom"))
                    blockIndex += 1
            
            ballotNum.append((0,0))
            acceptNum.append((0,0))
            acceptVal.append(Operation("Bottom", "Bottom", "Bottom", "Bottom"))

    file_path = f"{sys.argv[1]}b.txt"
    if os.path.getsize(file_path) != 0:
        with open(file_path, "r") as file:
            for line in file:
                op = parseOp(line)
                initializeOp(op)

#SHALL BE USING UDP INSTEAD OF TCP
if __name__ == "__main__":
    SERVER_IP = gethostname()
    SERVER_PORT = int(sys.argv[2])
    threading.Thread(target=initialize).start()
    serverSocket = socket(AF_INET, SOCK_DGRAM)
    serverSocket.bind(('', SERVER_PORT))
    print("Server is up and running")
    serverSocket.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
    threading.Thread(target=get_user_input).start()
    threading.Thread(target=connect).start()
    while True:
        try:
            message, clientAddress = serverSocket.recvfrom(2048)
            threading.Thread(target=handle_msg, args = (message, clientAddress[1])).start()
        except ConnectionResetError:
            continue
