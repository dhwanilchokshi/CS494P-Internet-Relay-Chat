#Name: Dhwanil Chokshi
#Class: CS494P
#server file

import sys
import socket
import ssl
import select
import re
import time

host = ''
socket_read_list = []   #save socket objects
receive = 4096          #recv buffer
port = 2500             #connection to port
users = []              #save usernames
channels = []           #save channel names
directory = {}          #save user info

#server side function, gets the server up and ready to listen to incoming connections
def server_side():

    serv_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)   #establishes a tcp connection 
    serv_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    serv_sock.bind((host, port))

    serv_sock.listen(10)    #listens for up to 10 active connections


    socket_read_list.append(serv_sock)  #append the socket to the socket list

    print "chat server has started on port " + str(port)
    
    while 1:
        ready_read, ready_write, in_error = select.select(socket_read_list, [], [], 0)  #ready_read = sockets which are read to be read

        for element in ready_read:      #traverse through the ready to read sockets
            if element == serv_sock:    # checks if the socket is the server socket
                sockfd, addr = serv_sock.accept()   # returns (conn, address), conn = new socket object usable to send and receive data, address = address bound to the socket on other end of connection

                socket_read_list.append(sockfd) #append the new socket object to the socket list

                username = sockfd.recv(receive) #get the username first thing
                if username in users:   #checks to see if username is already existing 
                    sockfd.send("sorry username is in use")
                    sockfd.close()
                    socket_read_list.remove(sockfd)

                else:   #welcome the uesr to the chat app
                    sockfd.send("Welcome to the chat %s" % username)
                    users.append(username)
                    print "%s has connected" % username

                #add user info to dictionary based on their connection details received in sockfd
                directory[sockfd] = {"user_id": username, "in_channels": [], "current_channel": ""}

                message = "%s entered the relay chat application" % username
                broadcast_message(serv_sock, sockfd, message)   #showcase to all connected clients that a new user has received

            else:
                try:
                    client_message = element.recv(receive).strip()  #receive data from client


                    if client_message:
                        if acknowledge(serv_sock, element, client_message, addr) == 0:    #check to see if client has sent a command (1 = command, 0 = just message)
                            who_messaged = directory[element]["user_id"]
                            broadcast_to_room(serv_sock, element, '\r' + '[' + who_messaged + ']: ' + client_message, "")   #otherwise its a message 

                    else: 
                        quit(serv_sock, element, addr)  #if no client message, quit - server cant wait forever

                except: #exception - indicates something went wrong like a crash, or a server quit was called
                    mes = []
                    mes.append(client_message.split())
                    if mes[0][0] == "_squit" and mes[0][1] == "password":
                        sys.exit("server disconnected")

                    quit(serv_sock, element, addr)
                    continue

    serv_sock.close()

#shows the message to all connected clients (all who are connected to server)
def broadcast_message(serv_sock, element, message):

#traverse through sockets, send message to all clients except the one we are dealing with
    for socket in socket_read_list: 
        if socket != serv_sock and socket != element:
            try:
                socket.send(message)

            except:
                socket.close()  #if message was not sent, the client is probably not active, cut connection

                if socket in socket_read_list:
                    socket_read_list.remove(socket)


#message to the the room the user is currently in, or a specified room
def broadcast_to_room(serv_sock, element, message, specified_chan):

    users_in_channels = []  #stores the sockets 

    for socket in socket_read_list: #go through socket list, store sockets who's current channel is not empty
        if socket != serv_sock and socket != element:
            if directory[socket]["current_channel"] != "":
                users_in_channels.append(socket)

    #if no specific channel specified, send messsage to all those who's current channel is same as user sending message            
    #this way, everyone who's currently in same channel as user can see
    if specified_chan == "":
        for user in users_in_channels:
            if directory[user]["current_channel"] == directory[element]["current_channel"]:
                if user != serv_sock and user != element:
                    try:
                        user.send(message)

                    except:
                        user.close()

                        if user in socket_read_list:
                            socket_read_list.remove(socket)

    #the channel was specified, so users who's current channel matches, the specified channel will get the message
    else:
        if specified_chan not in directory[element]["in_channels"]:
            element.send("\nyou are not part of this channel")

        else:
            for user in users_in_channels:
                if directory[user]["current_channel"] == specified_chan:
                    if user != serv_sock and user != element:
                        try:
                            user.send(message)

                        except:
                            user.close()

                            if user in socket_read_list:
                                socket.read_list.remove(socket)
                            


#parse the data received from client, check to see if its a command
#break down commands and call respective function to achieve what user wants
def acknowledge(serv_sock, element, client_message, addr):

    data = []   #where the data is stored, after being split
    value = 0   #value returned at end -- 1 - a command, 0 - not a command

    data.append(client_message.split())

    if data[0][0] == "_help":
        dispatch_help(element)
        value = 1

    elif data[0][0] == "_join":
        channel_name = data[0][1]
        join_channel(serv_sock, element, channel_name)
        value = 1

    elif data[0][0] == "_leave":
        channel_name = data[0][1]
        leave_channel(serv_sock, element, channel_name)
        value = 1

    elif data[0][0] == "_list":
        list_channel(element)
        value = 1

    elif data[0][0] == "_who":
        channel_name = data[0][1]
        who_channel(element, channel_name)
        value = 1

    elif data[0][0] == "_msg":
        msg_specific(serv_sock, element, client_message)
        value = 1

    elif data[0][0] == "_quit":
        quit(serv_sock, element, addr)
        value = 1
    
    elif data[0][0] == "_priv":
        user_name = data[0][1]
        msg = client_message.split("|", 1)[1]
        private_message(element, user_name, msg)
        value = 1

    elif data[0][0] == "_nick":
        old_name = data[0][1]
        new_name = data[0][2]
        nick(element, old_name, new_name)
        value = 1

    elif data[0][0] == "_squit":
        if data[0][1] == "password":
            sys.exit()

    elif data[0][0] == "_getfile":
        file_name = data[0][1]
        getfile(element, file_name)
        value = 1

    return value



#send a help message to user to showcase how commands can be used
def dispatch_help(element):
    help_message = "\nJoin/Switch to a room: <_join> <room_name>\nLeave a room: <_leave> <room_name>\nList rooms: <_list>\nList members in room: <_who> <room_name>\nMessage selected rooms: <_msg> <room_name> <room_name> |<message_to_send>\nQuit from chat: <_quit>\nPrivate message to another user: <_priv> <user_name> |<message_to_send>\nChange username: <_nick> <old_username> <new_username>\nServer Quit: <_squit> <password>\nGet file contents from server: <_getfile> <filename>"
    element.send(help_message)


#join/switch to a channel - if channel doesnt exist, its created and user is put in it - if channel exists, switch user to it
def join_channel(serv_sock, element, channel_name):

        if len(directory[element]["in_channels"]) >= 10:    #user can join up 10 channels at once
            element.send("sorry channel limit reached for %s" % directory[element]["user_id"])

        else:
            if channel_name not in channels:    #broadcast that a new channel is created
                msg = "new channel created: %s" % channel_name
                broadcast_message(serv_sock, element, msg)
                channels.append(channel_name)
            

            #append to the user's channel list
            if channel_name not in directory[element]["in_channels"]:
                directory[element]["in_channels"].append(channel_name)  #to make sure we dont add duplicates
            
            #add the channel as user's current channel
            directory[element]["current_channel"] = channel_name
            element.send("\nYou are now in channel: %s" % channel_name)

            user = directory[element]["user_id"]

            join_msg = user + " has joined %s" % channel_name
            broadcast_to_room(serv_sock, element, join_msg, "")


#leave a channel
def leave_channel(serv_sock, element, channel_name):

    if channel_name not in channels:    #channel doesnt exist at all
        element.send("%s channel does not exist" % channel_name)

    else:
        if channel_name not in directory[element]["in_channels"]:   #channel doesn't exist in user's channel list
            element.send("cannot leave channel you are not part of")

        else:   #remove channel from user's list
            if channel_name in directory[element]["in_channels"]:
                directory[element]["in_channels"].remove(channel_name)
                    
                leave_msg = "%s has left the room" % directory[element]["user_id"]
                broadcast_to_room(serv_sock, element, leave_msg, "")

                element.send("\nyou have been removed from %s" % channel_name)

                if not directory[element]["in_channels"]:   #if no channels left, user's current channel left empty
                    element.send("\ncannot add you in any channels since your channel list is empty")
                    directory[element]["current_channel"] = ""

                else:   #sets user's current channel to first channel in list
                    directory[element]["current_channel"] = directory[element]["in_channels"][0]
                    msg = directory[element]["user_id"] + " has joined %s" % directory[element]["in_channels"][0]
                    broadcast_to_room(serv_sock, element, msg, "")


#list the channels
def list_channel(element):

    element.send("Here are a list of active rooms")
    for channel in channels:
        element.send('\n' + channel)

#list the users in specific channel
def who_channel(element, channel_name):
    
    element.send("\nList of users in %s" % channel_name)
    
    if len(channels) == 0 or channel_name not in channels:
        element.send("\nNo users to show in channel")

    usernames = []

    for key in directory:
        if channel_name in directory[key]["in_channels"]:
            if directory[key]["user_id"] not in usernames:
                usernames.append(directory[key]["user_id"])



    for key in usernames:
        element.send('\n' + key)


#message specific selected channels 
def msg_specific(serv_sock, element, message):

    data = []
    channels_tomsg = []
    data.append(message.split("|")[0].split())  #get the channel names
    msg = message.split("|", 1)[1]  #get the message to send


    for i in range(0, len(data[0]) - 1):    #add channels to list to know which to send message to
        channels_tomsg.append(data[0][i+1])

    who_messaged = directory[element]["user_id"]
    currently_in = "currently in %s" % directory[element]["current_channel"]    #get the current channel user is in

    for chan in channels_tomsg: #send the messages to the channels specified
        broadcast_to_room(serv_sock, element, '\r' + '[' + who_messaged + " (" + currently_in + ")" + ']: ' + msg, chan)
        
    
#quit the client from server
def quit(serv_sock, element, addr):


    #broadcast that client has left
    current_user = directory[element]["user_id"]
    msg = "%s has left the room" % current_user
    broadcast_to_room(serv_sock, element, msg, "")


    #set current channel to none and remove user from users list
    directory[element]["current_channel"] = ""
    users.remove(directory[element]["user_id"])
    
    #delete the dictionary element
    del directory[element]

    time.sleep(0.00001)
    element.send("_00") #message tells client to exit 
    
    #broadcast that client is inactive
    print "Client %s is offline" % current_user
    broadcast_message(serv_sock, element, "Client %s is offline" % current_user)

    element.close()

    if element in socket_read_list:
        socket_read_list.remove(element)

#send private message to specified user
def private_message(element, user, message): 

    try:
        for active in directory:    #loop through dict element, send message to user matching username
            if directory[active]["user_id"] == user:
                active.send("\nPrivate Message from %s: " % user + message)
    except:
        element.send("\nUsername not recognized")


#change the user's username to something new
def nick(element, old, new):

    if old not in users:
        element.send("\ncurrent user name does not exist")

    else:
        if new not in users:
            users.remove(old)
            directory[element]["user_id"] = new

            users.append(new)
            element.send("\nyour user name has been changed to %s" %new)

        else:
            element.send("'\nusername already exists")


#get the file contents, and send to client
def getfile(element, filename):

    try:
        f = open(filename, "rb")
        read_limit = f.read(receive)
        while read_limit:
            element.send('\n' + read_limit)
            read_limit = f.read(receive)

        f.close()
        print "file sent to %s" %directory[element]["user_id"]

    except:
        element.send('\n' + "filename not recognized")


if __name__ == "__main__":
    sys.exit(server_side())
