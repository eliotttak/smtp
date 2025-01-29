reboot = True
while reboot :
    reboot = False
    try :
        import smtplib
        import ssl
        from email import encoders
        from email.mime.text import MIMEText
        from email.mime.multipart import MIMEMultipart
        from email.mime.base import MIMEBase
        from email.mime.application import MIMEApplication
        from markdown import markdown
        import json
        import os
        from sys import exit, platform
        import socket
        import atexit
        from colorama import Fore, Back, Style
        is_windows = platform == "win32" or platform == "cygwin" or platform == "msys"
        if is_windows :
            from colorama import just_fix_windows_console
        from pwinput import pwinput
        from stat import S_IRUSR, S_IWUSR
        json_data = {}

        path = os.path.dirname(__file__)
        drafts = []
        used_draft = 0
        drafts.append({})
        content = ""
        need_draft = False
        save_settings = False
        settings = {}
        delete_draft = {}
        NEWLINE = "\n"

        def colored(text, color = "", reset = Style.RESET_ALL) :
            return color + text + reset 

        def colored_print(text, color = "", reset = Style.RESET_ALL, end = NEWLINE) :
            print(colored(text, color, reset), end = end)

        def colored_input(prompt, color = "", reset = Style.RESET_ALL) :
            return input(colored(prompt, color=color, reset=reset))

        def choice_input(prompt, choices = ["o", "n"], color = "", reset = Style.RESET_ALL) :
            r = ""
            while not r in choices :
                r = colored_input(prompt, color=color, reset=reset)
            return r

        def number_input(prompt, color = "", reset = Style.RESET_ALL) :
            r = 0
            while True :
                try :
                    r = int(colored_input(prompt=prompt, color=color, reset=reset))
                    break
                except ValueError :
                    continue
            return r
    

        def on_close() :
            
            if need_draft :
                print("Enregistrement en tant que brouillon.")
                json_data["drafts"].append(drafts[used_draft])
                
            if save_settings :
                print("Enregistrement des paramètres")
                json_data["settings"] = settings
            
            if not delete_draft == {} :
                json_data["drafts"].remove(delete_draft)

            with open(path + ("\\" if is_windows else "/") + "data-smtp.json", "w") as s_to_write :
                s_to_write.write(json.dumps(json_data))
                colored_print("Enregistré.", Fore.GREEN)

        atexit.register(on_close)

        if is_windows :
            just_fix_windows_console()

        with open(path + ("\\" if is_windows else "/") + "data-smtp.json", "r") as s:
            #print(path + "\\data-smtp.json")

            content = s.read()
            #print(content)
            try :   
                json_data = json.loads(content)
                settings = json.loads(content)["settings"]
            except json.decoder.JSONDecodeError :
                settings["email"] = None
                settings["password"] = None
                settings["server"] = None
                settings["port"] = None
                
            if choice_input(f"Voulez-vous modifier les paramètres ({settings['server']} en tant que {settings['email']}) ? (o/n)\n >>> ") == "o" :
                while True :
                    print()
                    setting_to_modify = choice_input(f"Quel paramètre voulez-vous modifier ?\n - Paramètres de Serveur ({settings['server']} avec port {settings['port']})\n - Paramètres d'Identifiants ({settings['email']})\n - Quiter\n (s/i/q) >>> ", choices = ["s", "i", "q"])
                    if setting_to_modify == "s" :
                        settings['server'] = input("Entrer l'adresse du serveur et pressez [Entrée]\n >>> ")
                        settings['port'] = number_input("Entrez le port SMTP du serveur et pressez [Entrée]\n >>> ")
                    elif setting_to_modify == "i" :
                        settings['email'] = input("Entrer votre adresse e-mail et pressez [Entrée]\n >>> ")
                        settings['password'] = pwinput(mask="•", prompt="Entrez votre mot de passe et pressez [Entrée]\n >>> ")
                    elif setting_to_modify == "q" :
                        break
                print()
                if choice_input("Voulez-vous enregistrer ces modifications ? (o/n)\n >>> ") == "o" :
                    save_settings = True
            #open(path + "\\data-smtp.json", "w").close()
            

        sender = settings['email']
        password = settings['password']

        what_to_do_main = choice_input(f"\nQue voulez-vous faire ?\n - Envoyer un Nouveau message{NEWLINE + ' - Regarder, modifier et/ou envoyer un Brouillon' if not json_data['drafts'] == [] else ''}\n - Quitter\n(n{'/b' if not json_data['drafts'] == [] else ''}/q)>>> ", (["n", "b", "q"] if not json_data["drafts"] == [] else ["n", "q"]))
        if what_to_do_main == "b" : 
            colored_print("\nQuel brouillon voulez-vous regarder ?")
            for i_draft, d in enumerate(json_data["drafts"]) :
                if not "Subject" in json_data["drafts"][i_draft] :
                    json_data["drafts"][i_draft]["Subject"] = "<Sans titre>"
                if not "From" in json_data["drafts"][i_draft] :
                    json_data["drafts"][i_draft]["From"] = "<Sans expéditeur>"
                if not "To" in json_data["drafts"][i_draft] :
                    json_data["drafts"][i_draft]["To"] = "<Sans destinataire>"
                try :
                    print(str(i_draft + 1) + " - " + json_data["drafts"][i_draft]["Subject"] + " ==> " + json_data["drafts"][i_draft]["To"])
                except KeyError :
                    pass
            i_show_draft = number_input(f"(1, ..., {len(json_data['drafts'])})>>> ") - 1
            show_draft = json_data["drafts"][i_show_draft]
            try :
                print("\n")
                if "From" in show_draft :
                    print("\nDe : " + show_draft["From"])
                if "To" in show_draft :
                    print("À : " + show_draft["To"])
                if "Subject" in show_draft :
                    print("Sujet : " + show_draft["Subject"])
                if "text_content" in show_draft :
                    print("\n" + show_draft["text_content"])
                elif "list_of_lines_content" in show_draft :
                    print("\n" + "\n".join(show_draft["list_of_lines_content"]))
                print("Que voulez-vous faire ?\n - Envoyer ce brouillon, après éventuelle modification\n - Supprimer ce brouillon\n - Quitter pour envoyer un nouveau message")
                what_to_do_with_draft = choice_input("(e/s/q)>>> ", ["e", "s", "q"])
                if what_to_do_with_draft == "e" :
                    print()
                    print("Création d'un contexte SSL sécurisé en cours...")
                    context = ssl.create_default_context()
                    print("Contexte SSL sécurisé créé")
                    domain = settings['server']
                    print()
                    receiver = show_draft["To"] if not show_draft["To"] == "<Sans destinataire>" else input("À : ")
                    subject = show_draft["Subject"] if not show_draft["Subject"] == "<Sans titre>" else input("Sujet : ")
                    if not show_draft["From"] == settings["email"] :
                        colored_print("L'expéditeur de ce brouillon n'est pas celui configuré dans les paramètres.", Fore.YELLOW)
                        print(f" - Utiiser le mail configuré dans les Paramètres ({settings['email']})\n - Utiliser l'expéditeur de ce Brouillon ({show_draft['From']})")
                        if choice_input("(p/b)>>> ", ["p", "b"]) == "b" :
                            password = pwinput(mask="•", prompt=f"Entrez le mot de passe pour {show_draft['From']} : ", )
                        else :
                            show_draft["From"] = settings['email']
                            password = settings["password"]

                    print("Entrez la fin de votre message. Quand vous avez terminé, entrez trois deux-points (:::) sur une ligne isolée.\n")
                    print("\n".join(show_draft["list_of_lines_content"]))
                    while not show_draft["list_of_lines_content"][len(show_draft["list_of_lines_content"])-1] == ":::" :
                        show_draft["list_of_lines_content"].append(input())
                    show_draft["list_of_lines_content"].remove(":::")
                    show_draft["text_content"] = "\n".join(show_draft["list_of_lines_content"])

                    to_send = "<html>" + markdown(show_draft["text_content"]).replace("\n", "<br />") + "</html>"
                    message = MIMEMultipart("alternative")
                    message["Subject"] = show_draft["Subject"]
                    message["From"] = show_draft["From"]
                    message["To"] = show_draft["To"]
                    message.attach(MIMEText(to_send, "html"))
                    domain = settings["server"]
                    print(f"Connexion à {domain} avec le port {settings['port']} en cours...")
                    try :
                        with smtplib.SMTP_SSL(domain, settings["port"], context=context) as server:
                            print()
                            print(f"Connexion à {domain} en tant que {show_draft['From']} en cours...")
                            try :
                                server.login(show_draft["From"], password)
                            except smtplib.SMTPAuthenticationError :
                                print()
                                colored_print("Erreur : Indentifiant ou mot de passe incorrect.", Fore.RED)
                                input()
                            print()
                            colored_print("Connexion effectuée\n", Fore.GREEN)

                            
                            print(f"Envoi du message à {receiver} en cours...")
                            server.sendmail(sender, receiver, message.as_string())
                            colored_print("Message envoyé", Fore.GREEN)
                            need_draft = False
                            delete_draft = show_draft
                            exit()
                    except TimeoutError :
                        colored_print(f"Le serveur n'a pas répondu à temps. Merci de vérifier que le nom {settings['server']} et le port {settings['port']} sont correct.", Fore.RED)
                        input("Appuyez sur [Entrée] pour terminer.")
                        exit()
                    except socket.gaierror :
                        colored_print("Le serveur n'a pas répondu. Veuillez vérifier votre connexion à Internet.", Fore.RED)
                        input("Appuyez sur [Entrée] pour terminer.")
                        exit()
                if what_to_do_with_draft == "s" :
                    delete_draft = show_draft
                    exit()
            except KeyError :
                pass
        elif what_to_do_main == "n" :
            print()
            # Create a secure SSL context
            print("Création d'un contexte SSL sécurisé en cours...")
            context = ssl.create_default_context()
            print("Contexte SSL sécurisé créé")
            domain = settings['server']
            print()
            receiver = input("Entrez l'adresse du destinataire et pressez [Entrée]\n >>> ")
            need_draft = True
            drafts[used_draft]["To"] = receiver
            message = MIMEMultipart("alternative")
            message["Subject"] = input("Entrez le titre de votre e-mail et pressez [Entrée]\n >>> ")
            drafts[used_draft]["Subject"] = message["Subject"]
            message["From"] = sender
            drafts[used_draft]["From"] = message["From"]
            message["To"] = receiver
            buffer = []
            drafts[used_draft]["list_of_lines_content"] = []
            print("Entrez votre message. Quand vous avez terminé, entrez trois deux-points (:::) sur une ligne isolée.\n")
            while True:
                line = input()
                if line == ":::":
                    break
                buffer.append(line)
                drafts[used_draft]["list_of_lines_content"].append(line)
            text = "\n".join(buffer)
            drafts[used_draft]["text_content"] = text
            text = markdown(text)
            
            text = "<html>" + text.replace("\n", "<br/>") + "</html>"
            
            message.attach(MIMEText(text, "html"))

            if input("Voulez-vous ajouter une pièce jointe ?") == "o" :
                file_name = "./test.txt"
                attachment = open(file_name, 'rb')
                part = MIMEApplication(
                    attachment.read(),
                    Name = os.path.basename(file_name)
                )
                attachment.close()
                part['Content-Disposition'] = 'attachment; filename="%s"' % os.path.basename(file_name)
                message.attach(part)
            

            print(f"Connexion à {domain} avec le port {settings['port']} en cours...")
            try :
                with smtplib.SMTP_SSL(domain, settings["port"], context=context) as server:
                    print()
                    print(f"Connexion à {domain} en tant que {sender} en cours...")
                    try :
                        server.login(sender, password)
                    except smtplib.SMTPAuthenticationError :
                        print()
                        colored_print("Erreur : Indentifiant ou mot de passe incorrect.", Fore.RED)
                        input()
                    print()
                    print("Connexion effectuée\n")

                    
                    print(f"Envoi du message à {receiver} en cours...")
                    server.sendmail(sender, receiver, message.as_string())
                    colored_print("Message envoyé", Fore.GREEN)
                    need_draft = False
            except TimeoutError :
                colored_print(f"Le serveur n'a pas répondu à temps. Merci de vérifier que le nom {settings['server']} et le port {settings['port']} sont correct.", Fore.RED)
                input("Appuyez sur [Entrée] pour terminer.")
                exit()
            except socket.gaierror :
                colored_print("Le serveur n'a pas répondu. Veuillez vérifier votre connexion à Internet.", Fore.RED)
                input("Appuyez sur [Entrée] pour terminer.")
                exit()

        elif what_to_do_main == "q" :
            exit()
    except KeyboardInterrupt :
        colored_print("\nProgramme interrompu.", Fore.RED)
        input()
    except smtplib.SMTPRecipientsRefused :
        colored_print("Adresse e-mail du destinataire invalide.", Fore.RED)
        input()
    except smtplib.SMTPSenderRefused :
        colored_print("Adresse de l'expéditeur invalide.", Fore.RED)
        input()
    except FileNotFoundError :
        colored_print("Fichier de paramètres non trouvé.", Fore.YELLOW)
        print("Création d'un fichier vide en cours.")
        with open(path + ("\\" if is_windows else "/") + "data-smtp.json", "x") as f :
            empty_json = '{"settings":{"server":"","email":"","password":"","port":0},"drafts":[],"contacts":[]}'
            f.write(empty_json)
            colored_print("Fichier vide créé.", Fore.GREEN)
            print("Changement des droits d'accès")
            os.chmod(path + ("\\" if is_windows else "/") + "data-smtp.json", S_IRUSR | S_IWUSR)
        print("Redémarrage en cours")
        reboot = True
    #except Exception as e:
    #   colored_print(f"\nUne erreur inattendue a été détectée. :\n\n{e}", Fore.RED)
    #  input()
    #   exit()