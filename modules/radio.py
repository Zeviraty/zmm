import os
import sqlite3
from main import build_page
from zws import response

class Radio():
    def __init__(self):
        if not os.path.exists("config/radio.db"):
            con = sqlite3.connect("config/radio.db")
            cur = con.cursor()
            cur.execute("CREATE TABLE station(id INTEGER PRIMARY KEY AUTOINCREMENT,name TEXT,url TEXT);")
            con.commit()
            con.close()
        self.name = "Radio"
        self.main_page = "radio"
        self.pages = {
            "/radio": self.radio_page,
            "/radio/add-station": self.add_station,
            "/radio/station": [self.display_station, "startswith"],
            "/radio/edit-station": [self.edit_station, "startswith"],
            "/radio/delete-station": [self.delete_station, "startswith"],
        }

    def radio_page(self,connection,data):
        content = "=== Radio stations ===\n"
        con = sqlite3.connect("config/radio.db")
        cur = con.cursor()
        stations = cur.execute("SELECT * FROM station").fetchall()
        for i in stations:
            content += f"<a href='/radio/station/{i[0]}'>{i[1]}</a>\n"
        content += "\n=== Options ===\n"
        content += "<a href='/radio/add-station'># Add station</a>\n"
        content += "<a href='/'># Back</a>\n"


        content = build_page(content,boot=False)
        connection.send(response("200 OK", content, content_type="text/html"))

    def add_station(self,connection,data):
        if "body" in data.keys():
            if not ("name" in data["body"] and "url" in data["body"]):
                return
            if not (data["body"]["url"].startswith("https://") or data["body"]["url"].startswith("http://")):
                data["body"]["url"] = "https://"+data["body"]["url"]
            con = sqlite3.connect("config/radio.db")
            cur = con.cursor()
            cur.execute("INSERT INTO station (name,url) VALUES (?,?)",(data["body"]["name"],data["body"]["url"]))
            con.commit()
            con.close()
            connection.send(b"HTTP/1.1 302 Found\r\nLocation: /radio\r\n\r\n")
            return

        content = "=== Add Station ===\n"

        onkeypress = 'onkeypress="this.style.minWidth = ((this.value.length + 1) * 10) + \'px\';"'
        
        content += "<form action='/radio/add-station' method='post'>"
        content += f'<label>Name: <input type="text" id="name" name="name" autocomplete="off" placeholder="________" {onkeypress}/></label><br>'
        content += f'<label>Url: <input type="text" id="url" name="url" autocomplete="off" placeholder="________" {onkeypress}/></label><br>'
        content +=  '<br><input type="submit" value="# Add">'
        content += '</form>'

        content += "<a href='/radio'># Back</a>\n"

        content = build_page(content,boot=False)
        connection.send(response("200 OK", content, content_type="text/html"))

    def display_station(self,connection,data):
        station_id = data["path"].split("/")[-1]
        
        con = sqlite3.connect("config/radio.db")
        cur = con.cursor()
        station = cur.execute("SELECT * FROM station WHERE id = ?",(station_id,)).fetchone()
        
        if station == None:
            connection.send(b"HTTP/1.1 302 Found\r\nLocation: /radio\r\n\r\n")
            return

        content = f"=== {station[1]} ===\n"
        content += f"url: <a href='{station[2]}'>{station[2]}</a>\n"
        content += f"<audio id=\"player\" autoplay><source src=\"{station[2]}\" type=\"audio/mpeg\"> Your browser does not support the audio element. </audio>"
        content += '''<div> 
<button onclick="document.getElementById('player').play()">Play</button> 
<button onclick="document.getElementById('player').pause()">Pause</button> 
<button onclick="document.getElementById('player').volume += 0.1">Vol +</button> 
<button onclick="document.getElementById('player').volume -= 0.1">Vol -</button> 
</div>
'''
        content += f"<a href='/radio/edit-station/{station_id}'># Settings</a>\n"
        content += "\n"
        content += "<a href='/radio'># Back</a>\n"
        content += "\n"

        content = build_page(content,boot=False)
        connection.send(response("200 OK", content, content_type="text/html"))


    def edit_station(self,connection,data):
        station_id = data["path"].split("/")[-1]

        if "body" in data.keys():
            if not ("name" in data["body"] and "url" in data["body"]):
                return
            if not (data["body"]["url"].startswith("https://") or data["body"]["url"].startswith("http://")):
                data["body"]["url"] = "https://"+data["body"]["url"]
            con = sqlite3.connect("config/radio.db")
            cur = con.cursor()
            cur.execute(
                "UPDATE station SET name = ?, url = ? WHERE id = ?",
                (data["body"]["name"], data["body"]["url"], station_id)
            )
            con.commit()
            con.close()
            connection.send(f"HTTP/1.1 302 Found\r\nLocation: /radio/station/{station_id}\r\n\r\n".encode())
            return

        
        con = sqlite3.connect("config/radio.db")
        cur = con.cursor()
        station = cur.execute("SELECT * FROM station WHERE id = ?",(station_id,)).fetchone()
        con.close()
        
        if station == None:
            connection.send(b"HTTP/1.1 302 Found\r\nLocation: /radio\r\n\r\n")
            return

        content = f"=== Edit station {station[1]} ===\n"

        onkeypress = 'onkeypress="this.style.minWidth = ((this.value.length + 1) * 10) + \'px\';"'
        
        content += f"<form action='/radio/edit-station/{station_id}' method='post'>"
        content += f'<label>Name: <input type="text" id="name" name="name" autocomplete="off" value={station[1]} {onkeypress}/></label><br>'
        content += f'<label>Url: <input type="text" id="url" name="url" autocomplete="off" value={station[2]} {onkeypress}/></label><br>'
        content +=  '<br><input type="submit" value="# Submit">'
        content += '</form>'
        
        content += f"<a href='/radio/delete-station/{station_id}'># DELETE</a>\n"
        content += f"<a href='/radio/station/{station_id}'># Back</a>\n"

        content = build_page(content,boot=False)
        connection.send(response("200 OK", content, content_type="text/html"))

    def delete_station(self,connection,data):
        station_id = data["path"].split("/")[-1]

        con = sqlite3.connect("config/radio.db")
        cur = con.cursor()
        cur.execute("DELETE FROM station WHERE id = ?",(station_id,))
        con.commit()
        con.close()

        connection.send(f"HTTP/1.1 302 Found\r\nLocation: /radio\r\n\r\n".encode())

def register():
    return Radio()
