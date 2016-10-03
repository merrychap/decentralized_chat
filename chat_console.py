#!/usr/bin/env python3

import logging
import optparse
import logging.config
import signal

from network.client import ChatClient
from network.client import PORT

from database.chat_dbhelper import ChatDBHelper

from chats.console.main_chat import MainChat

<<<<<<< HEAD

LOG_FILE = 'logging_config.ini'
=======
LOG_FILE = 'logging_config.ini'
EMPTY = ' '
INDENT = 38 * '='
INF = 1000
lock = threading.Lock()


user_pattern = re.compile(r'^@user "([a-zA-Z_.]+)"$')
username_pattern = re.compile(r'@username "([a-zA-Z_.]+)"$')
room_pattern = re.compile(r'^@room "([a-zA-Z_.]+)"$')
create_room_pattern = re.compile(r'^@create_room "([a-zA-Z_.]+)"$')
remove_room_pattern = re.compile(r'^@remove_room "([a-zA-Z_]+)"$')
add_user_patter = re.compile(r'^@add_user "([a-zA-Z_]+)" "([a-zA-Z_]+)"$')
add_patter = re.compile(r'^@add_user "([a-zA-Z_]+)"$')


class BreakLoopException(Exception):
    pass

class BaseChat():
    def __init__(self, client):
        self.db_helper = ChatDBHelper()
        self.db_helper.specify_username(client)

        self.client = client
        self.commands = self.create_command_descrypt()
        self.stop_printing = True

    def print_help(self, commands, message=None):
        print('\n' + INDENT)
        print(('Type commands with @ on the left side of command.'
               '\nList of commands:\n'))
        for command, descr in commands.items():
            print('+ %s : %s' % (command, descr))
        print(INDENT + '\n')

    def print_mode_help(self, mode):
        print(('\n[*] Switched to %s mode\n'
               'Type "enter" to start typing message\n'
               'You can type @help for list of available '
               'commands\n' + INDENT + '\n') % mode)

    def specify_username(self):
        username = input('[*] Please, specify your username(a-zA-Z_.):> ')
        self.client.specify_username(username)

    def send_room_message(self, room_name, text, room_user = '',
                          remove_room='No'):
        '''
        Sends message to the certain room

        Args:
            room_name (str) Passed name of the room
        '''

        users = []
        room_id = self.db_helper.get_room_id(room_name)
        for user in self.db_helper.get_users_by_room(room_name, room_id):
            users.append(user)
        for user in users:
            if remove_room == 'Yes' and user == self.client.user_id:
                continue
            self.send_message(user_id=user, room=room_name, text=text,
                              remove_room=remove_room, room_user=room_user,
                              users_in_room=users)

    def send_message(self, room="", user_id=None, username=None,
                     text=None, remove_room='No', room_user = '',
                     room_creator='', users_in_room=[]):
        '''
        Sends message to destination host

        Args:
            username (str) Username of user that should recieve message
            text (str) Text of message
            message (data) Formated data of message
        '''

        if (user_id is None and username is None):
           logger.info('[-] Invalid data for sending message')
           return
        # Destination user id
        if user_id is None:
            user_id = self.db_helper.get_user_id(username)
        if room != '':
            room_creator = self.db_helper.get_room_creator(room)
        message = self.client.create_data(msg=text,
                                          username=self.client.username,
                                          user_id=self.client.user_id,
                                          room_name=room, remove_room=remove_room,
                                          room_creator=room_creator,
                                          new_room_user=room_user,
                                          users_in_room=users_in_room)
        # Destination host
        host = self.client.user_id2host[user_id]
        if user_id != self.client.user_id:
            self.db_helper.save_message(user_id, text)
        self.client.send_msg(host=host, msg=message)

    def get_last_message(self, user_id=None, room_name=''):
        # Invalid arguments
        if (user_id is None and room_name == '') or \
           (user_id is not None and room_name != ''):
            return
        dst = user_id if user_id is not None else room_name
        for message in self.db_helper.get_history(dst, 1, room_name != ''):
            return message
            # if message != None and message[2] == user_id:
            #    return message
        return ('', 0, -1)

    def cur_user_exists(self):
        return self.client.username != ''

    def change_username(self, username):
        self.db_helper.change_username(username)
        print('\n[+] Username changed, %s!\n' % username)

    def print_last_messages(self, dst, room=False):
        for message in list(self.db_helper.get_history(dst, 10, room))[::-1]:
            if message == None or message[1] == -1:
                continue
            print('{0} : {1}:> {2}'.format(message[3],
                                    self.db_helper.get_username(message[2]),
                                    message[0]))

    def print_recv_message(self, user_id=None, room_name=''):
        dst = user_id if user_id is not None else room_name

        last_msg = self.get_last_message(user_id=user_id, room_name=room_name)
        while not self.stop_printing:
            cur_msg = self.get_last_message(user_id=user_id, room_name=room_name)
            if last_msg[1] != cur_msg[1]:
                messages = self.db_helper.get_history(dst,
                                                      cur_msg[1] - last_msg[1],
                                                      room_name != '')
                for message in messages:
                    if message[2] != self.client.user_id:
                        print('{0} : {1}:> {2}'
                              .format(message[3],
                                      self.db_helper.get_username(message[2]),
                                      message[0]))
                last_msg = cur_msg

    def remove_room(self, room_name):
        self.stop_printing = True
        self.send_room_message(room_name, "Room was deleted",
                               remove_room='Yes')
        self.db_helper.remove_room(room_name)
        print('\nRoom "{0}" was deleted\n'.format(room_name))

    def add_user2room(self, username, room_name):
        if not self.db_helper.user_exists(username):
            print('[-] No such user in the chat\n')
            return False
        self.db_helper.add_user2room(username=username,
                                     room_name=room_name)
        # Invites user to the room by sending
        # empty message
        self.send_room_message(room_name, EMPTY,
                               room_user=username)
        print('\n[+] You have invited "{0}" to the "{1}" room\n'.
              format(username, room_name))
        return True

    def exit(self):
        self.client.disconnect()
        print ('\nBye!')
        time.sleep(1)
        os._exit(1)


class MainChat(BaseChat):
    def __init__(self, client):
        super().__init__(client)
        self.client = client
        self.commands = self.create_command_descrypt()

    def run(self):
        if not self.cur_user_exists():
            self.specify_username()
        else:
            print('Hello again, %s!' % self.client.username)
        self.db_helper.specify_username(self.client)
        self.client.start()
        self.command_mode()

    def create_command_descrypt(self):
        return {
            'help': 'Shows this output',
            'username "username"': 'Changes current username. ',
            'rooms': 'Shows available rooms.',
            'users': 'Shows online users.',
            'user "username"': 'Switches to user message mode. ',
            'room "room_name"': 'Switches to room message mode. ',
            'remove_room "roomname"': 'Removes created room.',
            'add_user': '"username" "room_name"',
            'create_room "roomname"': 'Creates new room. ',
            'exit': 'Closes chat.'
        }

    def handle_command(self, command):
        user_parse = user_pattern.match(command)
        room_parse = room_pattern.match(command)
        username_parse = username_pattern.match(command)
        create_room_parse = create_room_pattern.match(command)
        remove_room_parse = remove_room_pattern.match(command)
        add_user_parse = add_user_patter.match(command)

        if command == '@help':
            self.print_help(commands=self.commands)
        elif command == '@users':
            print('\n' + INDENT)
            for user_id in self.client.host2user_id.values():
                print('+ %s' % self.db_helper.get_username(user_id))
            print(INDENT + '\n')
        elif command == '@rooms':
            print('\n' + INDENT)
            for room in self.db_helper.get_user_rooms():
                print('+ %s' % room)
            print(INDENT + '\n')
        elif command == '@exit':
            self.exit()
        elif user_parse != None:
            username = user_parse.group(1)
            if self.db_helper.user_exists(username):
                UserChat(username=username, client=self.client).open()
            else:
                print('[-] No such user in the chat\n')
        elif room_parse != None:
            room_name = room_parse.group(1)
            if self.db_helper.room_exists(room_name):
                RoomChat(room_name=room_name, client=self.client).open()
            else:
                print('[-] No such room in the chat\n')
        elif create_room_parse != None:
            room_name = create_room_parse.group(1)
            if self.db_helper.create_room(room_name):
                print('\n[+] You\'ve created room "{0}"\n'
                      .format(room_name))
            else:
                print('\n[-] Room with this name already exists\n')
        elif username_parse != None:
            self.change_username(username_parse.group(1))
        elif remove_room_parse != None:
            room_name = remove_room_parse.group(1)
            self.remove_room(room_name)
        elif add_user_parse != None:
            username = add_user_parse.group(1)
            room_name = add_user_parse.group(2)
            if not self.add_user2room(username, room_name):
                return
        else:
            print('[-] Invalid command\n')

    def handle_signal(signal, frame):
        self.exit()

    def command_mode(self):
        print('\nType "@help" for list of commands with description')

        while True:
            try:
                command = input('[*] Enter command:> ')
                self.handle_command(command)
            except KeyboardInterrupt as e:
                self.exit()

class UserChat(BaseChat):
    def __init__(self, username, client):
        super().__init__(client)

        self.username = username
        self.user_id = self.db_helper.get_user_id(username)

        self.print_mode_help('message')

        self.stop_printing = False
        threading.Thread(target=self.print_recv_message,
                         args=(self.user_id,)).start()

    def handle_command(self, command):
        if command == '@help':
            self.print_help(commands=self.commands)
        elif command == '@back':
            self.stop_printing = True
            print('\n[*] Switched to command mode\n' + INDENT + '\n')
            raise BreakLoopException
        elif command == '@test':
            print(self.db_helper.get_history(self.username, 1))
        else:
            self.send_message(username=self.username, text=command)

    def open(self):
        print()
        self.print_last_messages(self.user_id)

        while True:
            input()
            try:
                with lock:
                    message = input('%s:> ' % self.client.username)
                self.handle_command(message)
            except BreakLoopException:
                break

    def create_command_descrypt(self):
        return {
            'help': 'Shows this output',
            'back': 'Returns to message mode',
        }


class RoomChat(BaseChat):
    def __init__(self, room_name, client):
        super().__init__(client)

        self.room_name = room_name
        self.room_id = self.db_helper.get_room_id(room_name)

        self.print_mode_help('room message')

        self.stop_printing = False
        threading.Thread(target=self.print_recv_message,
                         args=(None,self.room_name,)).start()

    def handle_command(self, command):
        add_parse = add_patter.match(command)

        if command == '@help':
            self.print_help(commands=self.commands)
        elif command == '@back':
            self.stop_printing = True
            print('\n[*] Switched to command mode\n' + INDENT + '\n')
            raise BreakLoopException
        elif add_parse != None:
            username = add_parse.group(1)
            if not self.add_user2room(username, self.room_name):
                return
        elif command == '@remove_room':
            self.remove_room(self.room_name)
            raise BreakLoopException
        else:
            self.send_room_message(self.room_name, command)


    def open(self):
        print()
        self.print_last_messages(self.room_name, True)

        while True:
            input()
            try:
                with lock:
                    message = input('%s:> ' % self.client.username)
                self.handle_command(message)
            except (KeyboardInterrupt, BreakLoopException) as e:
                break

    def create_command_descrypt(self):
        return {
            'help': 'Shows this output',
            'back': 'Returns to message mode',
            'add_user "username"': 'Adds passed user to the room',
            'remove_room "room_name"': 'Removes room from chat'
        }
>>>>>>> 9adf4a9118c15fd5a1519aa909049eef94c77515


def main():
    logging.basicConfig(filename='app.log', level=logging.DEBUG)

    parser = optparse.OptionParser('usage %prog -H <connected host> ')
    parser.add_option('-H', dest='conn_host', type='string',
                      help='specify connected host')
    (options, args) = parser.parse_args()
    conn_host = options.conn_host

    # TODO check username correctness
    if conn_host is None:
        client = ChatClient()
    else:
        client = ChatClient((conn_host, PORT))

    # Create entity of chat
    chat = MainChat(client=client)
    chat.run()


if __name__ == '__main__':
    main()
