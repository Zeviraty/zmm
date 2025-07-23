from zws import Server, response
from random import choice
import json
import os

banners = [
        "====================================\nd88888P   88bd8b,d88b   88bd8b,d88b \n   d8P'   88P'`?8P'?8b  88P'`?8P'?8b\n d8P'    d88  d88  88P d88  d88  88P\nd88888P'd88' d88'  88bd88' d88'  88b\n====================================",
        '=========================\n   ____  __  __  __  __  \n  |_  / |  \\/  ||  \\/  | \n   / /  | |\\/| || |\\/| | \n  /___| |_|__|_||_|__|_| \n_|"""""|_|"""""|_|"""""| \n"`-0-0-\'"`-0-0-\'"`-0-0-\'\n=========================',
        '======================================\n8888888888P888b     d888888b     d888 \n      d88P 8888b   d88888888b   d8888 \n     d88P  88888b.d8888888888b.d88888 \n    d88P   888Y88888P888888Y88888P888 \n   d88P    888 Y888P 888888 Y888P 888 \n  d88P     888  Y8P  888888  Y8P  888 \n d88P      888   "   888888   "   888 \nd8888888888888       888888       888\n======================================',
        '==============================\n███████╗███╗   ███╗███╗   ███╗\n╚══███╔╝████╗ ████║████╗ ████║\n  ███╔╝ ██╔████╔██║██╔████╔██║\n ███╔╝  ██║╚██╔╝██║██║╚██╔╝██║\n███████╗██║ ╚═╝ ██║██║ ╚═╝ ██║\n╚══════╝╚═╝     ╚═╝╚═╝     ╚═╝\n==============================',
        '===============================================================\n      ,##############Wf.       ,W,     .Et          ,W,     .Et\n       ........jW##Wt         t##,    ,W#t         t##,    ,W#t\n             tW##Kt          L###,   j###t        L###,   j###t\n           tW##E;          .E#j##,  G#fE#t      .E#j##,  G#fE#t\n         tW##E;           ;WW; ##,:K#i E#t     ;WW; ##,:K#i E#t\n      .fW##D,            j#E.  ##f#W,  E#t    j#E.  ##f#W,  E#t\n    .f###D,            .D#L    ###K:   E#t  .D#L    ###K:   E#t\n  .f####Gfffffffffff; :K#t     ##D.    E#t :K#t     ##D.    E#t\n .fLLLLLLLLLLLLLLLLLi ...      #G      ..  ...      #G      ..\n===============================================================',
        '============================================\n███████████ ██████   ██████ ██████   ██████\n░█░░░░░░███ ░░██████ ██████ ░░██████ ██████ \n░     ███░   ░███░█████░███  ░███░█████░███ \n     ███     ░███░░███ ░███  ░███░░███ ░███ \n    ███      ░███ ░░░  ░███  ░███ ░░░  ░███ \n  ████     █ ░███      ░███  ░███      ░███ \n ███████████ █████     █████ █████     █████\n░░░░░░░░░░░ ░░░░░     ░░░░░ ░░░░░     ░░░░░\n============================================'
]

boot_messages = [
        "[BOOT] Initializing system\n",
        "[INIT] Media stack cold boot...\n",
        "[ZMM] Spinning up index modules...\n",
        "[BOOT] Installing python & git...\n",
]

ok_messages = [
        "[OK] System Ready. Awaiting user input.\n",
        "[SUCCESS] Loaded in 0.013s\n",
        "[READY] Listening on port 8080\n",
        "[DONE] Starting shell...\n",
]

run_messages = [
        "> zmm --start\n",
        "> run zmm\n",
        "> start\n",
        "> git clone https://github.com/zeviraty/zmm-core/\nCloning into 'zmm-core'...\nremote: Enumerating objects: 527, done.\nremote: Counting objects: 100% (18/18), done.\nremote: Compressing objects: 100% (14/14), done.\nremote: Total 527 (delta 5), reused 9 (delta 4), pack-reused 509 (from 1)\nReceiving objects: 100% (527/527), 91.45 KiB | 321.00 KiB/s, done.\nResolving deltas: 100% (251/251), done.\n> cd zmm-core\n> python3 main.py\n"
]

def build_page(page_content,script="",boot=True):
    settings = json.load(open("config/zmm.json"))
    content = ""
    content += "<!DOCTYPE html>\n"
    content += "<html>\n"
    content += "<head> <link rel='stylesheet' href='style.css'> <meta charset='UTF-8'> </head>\n"

    content += "<body>\n"

    if boot == True and settings["boot_message"] == True:
        boot_msg = choice(boot_messages)+choice(ok_messages)+choice(run_messages)
        content += f"<pre class='boot'>{boot_msg}</pre>\n"

    if settings["banner"] == True and boot == True:
        ascii_art = choice(banners)
        content += f"<div class='ascii'>{ascii_art}</div>\n"

    content += page_content

    content += "</body>\n"
    content += f"<script src='{script}'></script>\n" if script != "" else ""
    content += "</html>"

    return content

def index(connection,data):
    options = ["settings"]
    page_content = ""
    for i in options: page_content += f"<a href='{i}'><b># {i}</b></a>\n"
    content = build_page(page_content,boot=True)
    connection.send(response("200 OK", content, content_type="text/html"))

def settings_page(connection,data):
    settings = json.load(open("config/zmm.json"))
    if "body" in data.keys():
        for k, v in settings.items():
            match type(v):
                case bool:
                    if k in data["body"]:
                        settings[k] = data["body"][k] == "on"
                    else:
                        settings[k] = False
        json.dump(settings,open("config/zmm.json",'w'))
    settings = json.load(open("config/zmm.json"))
    content = "=== Settings ===\n\n"
    content += '<form action="/settings">'
    for k,v in settings.items():
        match type(v):
            case bool:
                content += f'<label class="checkbox"><input type="checkbox" name="{k}" value="on"{" checked" if v else ""} />{k}: <span></span> </label><br>'
    content += '<br><input type="submit" value="# Submit">'
    content += "</form>"
    content += "<a href='/'># Back</a>\n"
    content = build_page(content,boot=False)
    connection.send(response("200 OK", content,content_type="text/html"))

def main():
    server = Server()
    server.start("0.0.0.0",8080)

    if not os.path.exists("config/zmm.json"):
        settings = {"boot_message": True,"banner":True}
        open("config/zmm.json",'w').write(json.dumps(settings))

    server.bind_path("/",index)
    server.bind_path("/settings",settings_page)
    server.bind_file("style.css")
    server.bind_file("script.js")

if __name__ == "__main__":
    main()
