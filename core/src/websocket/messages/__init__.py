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
        return "\n\n{line}\n\nWelcome user! It has been a while...\n\n{data}\n\n{line}".format(
            data=json.dumps(request.user_token, indent=4),
            line=LINE
        )

    def echo(self, value) -> str:
        return str(value)
