#Name: Dhwanil Chokshi
#Class: CS494P
#client file

import sys
import socket
import select

#client side
def client_side(hostname, port, username):

    cli_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)    #open a tcp connection from client side


    #try connecting to the server, using hostname and port
    try:
        cli_sock.connect((hostname, port))

    except:
        sys.exit("unable to connect to host")

    print "successfully connected. You can start sending messages"

    cli_sock.send(username) #send username to server 

    while 1:
        socket_list = [sys.stdin, cli_sock]

        ready_read, ready_write, in_error = select.select(socket_list, [], [], 0)   #get socket list ready to be read

        for sock in ready_read: #go through ready socket list, if its client socket, get server message
            #incoming message from server
            if sock == cli_sock:
                server_message = sock.recv(4096).strip()

                if server_message == "_00": #disconnect client message from server
                    sys.exit("disconnected from server")

                if not server_message:
                    sys.exit("disconnected from server")

                #write the data to console
                else:
                    print server_message


            else:

                #user entered a message
                user_msg = sys.stdin.readline()
                cli_sock.send(user_msg)



if __name__ == "__main__":
    
    length_args = len(sys.argv)

    #need 4 args from command line
    if length_args < 4:
        sys.exit("too few args provided \nto run: python client.py hostname port username")

    host = sys.argv[1]
    port = int(sys.argv[2])
    user_name = sys.argv[3]
    sys.exit(client_side(host, port, user_name))
