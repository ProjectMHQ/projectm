class WebsocketMessagesFactory():
    def __init__(self, language='it-IT'):
        self.language = language

    def get_motd(self):
        return """

#########################################################################

██████╗ ██████╗  ██████╗      ██╗███████╗ ██████╗████████╗    ███╗   ███╗
██╔══██╗██╔══██╗██╔═══██╗     ██║██╔════╝██╔════╝╚══██╔══╝    ████╗ ████║
██████╔╝██████╔╝██║   ██║     ██║█████╗  ██║        ██║       ██╔████╔██║
██╔═══╝ ██╔══██╗██║   ██║██   ██║██╔══╝  ██║        ██║       ██║╚██╔╝██║
██║     ██║  ██║╚██████╔╝╚█████╔╝███████╗╚██████╗   ██║       ██║ ╚═╝ ██║
╚═╝     ╚═╝  ╚═╝ ╚═════╝  ╚════╝ ╚══════╝ ╚═════╝   ╚═╝       ╚═╝     ╚═╝

#########################################################################
                                                                         
                                                        Ver 0.0.1

                                                    ##################





                                                                      
"""

    def get_login_message(self):
        return \
"                                                    Waiting for login... "

