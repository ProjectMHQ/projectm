import json


LINE = '=='*50


class WebsocketMessagesFactory():
    def __init__(self, language='it-IT'):
        self.language = language

    def get_motd(self):
        return """{}\n\n

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
            




                                                                      
""".format(LINE)

    def get_login_message(self, request):
        return 'User %s' % request.user_token['user']['user_id']

    def echo(self, value) -> str:
        return str(value)

    def greet_character(self, data):
        res = "\n\nAhoy, {} !\n\n".format(data['data']['name'])
        res += "\n\n"
        res += "~~~~ Nel bel mezzo del niente ~~~~\n\n\n"
        res += "Sei nel bel mezzo del niente. Qui non c'è niente.\n"
        res += "Attorno a te non vedi niente, perché... non c'è niente.\n"
        res += "Se vuoi però... puoi parlare. Da solo. Ovviamente.\n"
        res += "Perché nel niente, nessuno può sentirti.\n\n"
        return res

    def wait_for_auth(self):
        return '\n\n\nAuthenticating...\n\n\n'
