#!/usr/bin/env python3
import sys
import os
import html
import sqlite3

con = sqlite3.connect('file:unique.sqlite?mode=ro', uri=True, isolation_level=None, check_same_thread=False)
db = con.cursor()

urls = {}
db.execute("SELECT rowid, r_url FROM urls_seen ORDER BY rowid ASC")
while row := db.fetchone():
	urls[row[0]] = row[1]

db.execute("SELECT rowid, r_url, r_stamp, r_piece FROM html_pieces ORDER BY r_url ASC, rowid ASC")
while row := db.fetchone():
	url = html.escape(urls[row[1]], quote=True)
	print(f'<s id="{row[0]}" url="{url}" stamp="{row[2]}">\n{row[3]}\n</s>\n\n')
