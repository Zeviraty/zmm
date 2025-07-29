from zws import response
from main import build_page
import xml.etree.ElementTree as ET
import sqlite3
import os
import requests
from pprint import pp
import re

class RSS():
    def __init__(self):
        if not os.path.exists("config/rss.db"):
            con = sqlite3.connect("config/rss.db")
            cur = con.cursor()
            cur.execute("CREATE TABLE feed(id INTEGER PRIMARY KEY AUTOINCREMENT,name TEXT,url TEXT);")
            cur.execute("CREATE TABLE post(id INTEGER PRIMARY KEY AUTOINCREMENT,name TEXT,description TEXT,url TEXT,pubdate TEXT, feed_id INTEGER, FOREIGN KEY (feed_id) REFERENCES feed(id) ON DELETE CASCADE)")
            con.commit()
            con.close()
        self.name = "Rss"
        self.main_page = "rss"
        self.pages = {
            "/rss": self.rss_page,
            "/rss/add-feed": self.add_feed,
            "/rss/feed": [self.display_feed, "startswith"],
            "/rss/edit-feed": [self.edit_feed, "startswith"],
            "/rss/update-feed": [self.update_feed, "startswith"],
            "/rss/delete-feed": [self.delete_feed, "startswith"],
        }

    def rss_page(self,connection,data):
        content = "=== RSS Feeds ===\n"
        con = sqlite3.connect("config/rss.db")
        cur = con.cursor()
        feeds = cur.execute("SELECT * FROM feed").fetchall()
        for i in feeds:
            content += f"<a href='/rss/feed/{i[0]}'>{i[1]}: Unread 0</a>\n"
        content += "\n=== Options ===\n"
        content += "<a href='/rss/add-feed'># Add feed</a>\n"
        content += "<a href='/'># Back</a>\n"


        content = build_page(content,boot=False)
        connection.send(response("200 OK", content, content_type="text/html"))

    def add_feed(self,connection,data):
        if "body" in data.keys():
            if not ("name" in data["body"] and "url" in data["body"]):
                return
            if not (data["body"]["url"].startswith("https://") or data["body"]["url"].startswith("http://")):
                data["body"]["url"] = "https://"+data["body"]["url"]
            con = sqlite3.connect("config/rss.db")
            cur = con.cursor()
            cur.execute("INSERT INTO feed (name,url) VALUES (?,?)",(data["body"]["name"],data["body"]["url"]))
            con.commit()
            con.close()
            connection.send(b"HTTP/1.1 302 Found\r\nLocation: /rss\r\n\r\n")
            return

        content = "=== Add Feed ===\n"

        onkeypress = 'onkeypress="this.style.minWidth = ((this.value.length + 1) * 10) + \'px\';"'
        
        content += "<form action='/rss/add-feed' method='post'>"
        content += f'<label>Name: <input type="text" id="name" name="name" autocomplete="off" placeholder="________" {onkeypress}/></label><br>'
        content += f'<label>Url: <input type="text" id="url" name="url" autocomplete="off" placeholder="________" {onkeypress}/></label><br>'
        content +=  '<br><input type="submit" value="# Add">'
        content += '</form>'

        content += "<a href='/rss'># Back</a>\n"

        content = build_page(content,boot=False)
        connection.send(response("200 OK", content, content_type="text/html"))

    def display_feed(self,connection,data):
        feed_id = data["path"].split("/")[-1]
        
        con = sqlite3.connect("config/rss.db")
        cur = con.cursor()
        feed = cur.execute("SELECT * FROM feed WHERE id = ?",(feed_id,)).fetchone()
        
        if feed == None:
            connection.send(b"HTTP/1.1 302 Found\r\nLocation: /rss\r\n\r\n")
            return

        content = f"=== {feed[1]} ===\n"
        content += f"url: <a href='{feed[2]}'>{feed[2]}</a>\n"
        content += f"<a href='/rss/update-feed/{feed_id}'># Update feed</a>\n"
        content += f"<a href='/rss/edit-feed/{feed_id}'># Settings</a>\n"
        content += "\n"
        content += "<a href='/rss'># Back</a>\n"
        content += "\n"

        content += "=== Posts ===\n"
        for post in cur.execute("SELECT * FROM post WHERE feed_id = ?",(feed_id,)).fetchall().__reversed__():
            content += f"<a href='{post[3]}'>=== {post[1]} ===</a>\n"
            content += post[2]+"\n\n"
        content = build_page(content,boot=False)
        connection.send(response("200 OK", content, content_type="text/html"))

    def update_feed(self,connection,data):
        feed_id = data["path"].split("/")[-1]
        
        con = sqlite3.connect("config/rss.db")
        cur = con.cursor()
        feed = cur.execute("SELECT * FROM feed WHERE id = ?",(feed_id,)).fetchone()
        
        if feed == None:
            connection.send(b"HTTP/1.1 302 Found\r\nLocation: /rss\r\n\r\n")
            return

        try:
            ATOM_NS = '{http://www.w3.org/2005/Atom}'
            text = requests.get(feed[2]).text
            root = ET.fromstring(text)
            channel = root.find('channel')
            if len(root.findall('item')) != 0:
                channel = root
            if len(root.findall(f'{ATOM_NS}entry')) != 0:
                channel = root
            elif channel is None:
                print("Invalid RSS feed: no <channel> found")
                connection.send(b"HTTP/1.1 302 Found\r\nLocation: /rss\r\n\r\n")
                return

            for item in channel.findall('item'):
                title = item.findtext('title')
                if cur.execute("SELECT * FROM post WHERE name = ?",(title,)).fetchone() != None:
                    continue
                link = item.findtext('link')
                description = item.findtext('description')
                pub_date = item.findtext('pubDate')
                cur.execute("INSERT INTO post (name, description, url, pubdate, feed_id) VALUES (?,?,?,?,?)",(title,description,link,pub_date,feed_id))

            for entry in channel.findall(f'{ATOM_NS}entry'):
                title = entry.findtext(f'{ATOM_NS}title', default='(No title)')
                link_el = entry.find(f"{ATOM_NS}link[@rel='alternate']") or entry.find(f"{ATOM_NS}link")
                link = link_el.attrib['href'] if link_el is not None else ''
                updated = entry.findtext(f'{ATOM_NS}updated', default='')
                content = entry.findtext(f'{ATOM_NS}content', default='')

                cur.execute("INSERT INTO post (name, description, url, pubdate, feed_id) VALUES (?,?,?,?,?)",(title,content,link,updated,feed_id))

            con.commit()
            con.close()
                
        except KeyboardInterrupt as e:
            print("Error while parsing feed:")
            print(e)

        connection.send(f"HTTP/1.1 302 Found\r\nLocation: /rss/feed/{feed_id}\r\n\r\n".encode())

    def edit_feed(self,connection,data):
        feed_id = data["path"].split("/")[-1]

        if "body" in data.keys():
            if not ("name" in data["body"] and "url" in data["body"]):
                return
            if not (data["body"]["url"].startswith("https://") or data["body"]["url"].startswith("http://")):
                data["body"]["url"] = "https://"+data["body"]["url"]
            con = sqlite3.connect("config/rss.db")
            cur = con.cursor()
            cur.execute(
                "UPDATE feed SET name = ?, url = ? WHERE id = ?",
                (data["body"]["name"], data["body"]["url"], feed_id)
            )
            con.commit()
            con.close()
            connection.send(f"HTTP/1.1 302 Found\r\nLocation: /rss/feed/{feed_id}\r\n\r\n".encode())
            return

        
        con = sqlite3.connect("config/rss.db")
        cur = con.cursor()
        feed = cur.execute("SELECT * FROM feed WHERE id = ?",(feed_id,)).fetchone()
        con.close()
        
        if feed == None:
            connection.send(b"HTTP/1.1 302 Found\r\nLocation: /rss\r\n\r\n")
            return

        content = f"=== Edit feed {feed[1]} ===\n"

        onkeypress = 'onkeypress="this.style.minWidth = ((this.value.length + 1) * 10) + \'px\';"'
        
        content += f"<form action='/rss/edit-feed/{feed_id}' method='post'>"
        content += f'<label>Name: <input type="text" id="name" name="name" autocomplete="off" value={feed[1]} {onkeypress}/></label><br>'
        content += f'<label>Url: <input type="text" id="url" name="url" autocomplete="off" value={feed[2]} {onkeypress}/></label><br>'
        content +=  '<br><input type="submit" value="# Submit">'
        content += '</form>'
        
        content += f"<a href='/rss/delete-feed/{feed_id}'># DELETE</a>\n"
        content += f"<a href='/rss/feed/{feed_id}'># Back</a>\n"

        content = build_page(content,boot=False)
        connection.send(response("200 OK", content, content_type="text/html"))

    def delete_feed(self,connection,data):
        feed_id = data["path"].split("/")[-1]

        con = sqlite3.connect("config/rss.db")
        cur = con.cursor()
        cur.execute("DELETE FROM feed WHERE id = ?",(feed_id,))
        con.commit()
        con.close()

        connection.send(f"HTTP/1.1 302 Found\r\nLocation: /rss\r\n\r\n".encode())

def register():
    return RSS()
