# Bloxos
A project that displays the multi-Paxos protocol.
Supports 5 clients that can post and comment on a distributed blog. 

### Description
----------
This blog post application consists of a blog data structure for storage and a blockchain that acts as the log for blog operations. The application’s main features allow users to make blog posts, comment on other users’ posts, and view posts and comments.
Each node manages its own copy of the blog and can **post** and **comment** (given a username, title, content), and has these *reading* operations:
- View All Posts
- View All Posts made by a user
- View All Comments on a post

## Blockchain
The blockchain acts as a log for all *writing* operations that have been applied to the blog. Each block consists of 3 fields:
- Hash Pointer
- Writing Operation
- Nonce (Pattern of 3 leading zero bits at the beginning of SHA256 hash)
  *provides trustworthiness

## Paxos
Consists of 3 phases for adding blocks to the blockchain (updating the blog)
#### Election Phase
------
- Used for electing a leader that users will send requests to
- Responsible for sending accept messages and deciding messages
#### Replication Phase
------
- Leader maintains a queue of pending operations waiting for consensus
- Broadcasts ACCEPT messages for next pending operatioon
- Acceptors (other nodes) do not accept if blockchain is deeper than the depth of the ballot_number
#### Decision Phase
------
- Append the proposed block to the blockchain
- Apply operation to blog
- Remote the operation from the queue
- Send DECIDE message to all nodes

 Upon receiving the DECIDE message from the leader, an acceptor will similarly append the proposed block to its blockchain, and apply the corresponding operation to its local blog
 The leader should start a new normal/replication phase for the next pending operation in its queue with an updated ballot number

## Recovery
Every node has a save-file that saves when the blog is changed (tentative and decided operations)
When reconnecting to the network the app reads from the save file and updates the blockchain and blog accordingly

## Inputs
##### Protocol-Related Input Interface 
- crash: terminate the process
- failLink(dest): fail the connection between the issuing process and the dest node. Links
are assumed to be bidirectional, i.e. once P1 runs failLink(P2), P1 can neither send to
or receive from P2
- fixLink(dest): fix the connection between the issuing process and the dest node
- blockchain: print all content of every block in the blockchain
- queue: print all pending operations in the queue

##### Application-Related Input Interface
- post(username, title, content): issue a Post operation for creating a new blog post
authored under username with the given title and content
- comment(username, title, content): issue a Comment operation for creating a new comment authored under username with content for the blog post with title
- blog: print a list of the title of all blog posts in chronological order. If there are no blog
posts, print “BLOG EMPTY” instead
- view(username): print a list of the title and content of all blog posts authored under
the username in chronological order. If there are no posts authored under a username, print “NO
POST” instead
- read(title): print the content of the blog post with the title, and the list of comments for the
post with their respective authors in chronological order. If a post with a title doesn’t exist,
print “POST NOT FOUND” instead





