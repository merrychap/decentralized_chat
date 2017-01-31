#!/usr/bin/env python3

import logging
import argparse
import logging.config
import signal

from args_parser import ArgsParser

from network.client import ChatClient
from network.client import PORT

from database.chat_dbhelper import ChatDBHelper

from chats.console.main_chat import MainChat
from chats.gui.main_chat import GMainChat, gmain


LOG_FILE = 'logging_config.ini'


def main():
    logging.basicConfig(filename='app.log', level=logging.DEBUG)

    parser = ArgsParser()
    gui, host, port, recv_port = parser.get_params()

    if not gui:
        if host is None:
            client = ChatClient(recv_port)
        else:
            client = ChatClient(recv_port, (host, port))
        # Create entity of console chat
        chat = MainChat(client=client)
        chat.run()
    else:
        gmain()


if __name__ == '__main__':
    main()
