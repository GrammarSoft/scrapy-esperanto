#!/usr/bin/env python3
import sys
import os
import tempfile
import html
import subprocess
import sqlite3
import hashlib
import regex as re
from pathlib import Path

tmpdir = tempfile.gettempdir()

subprocess.run(['sqlite3', 'unique.sqlite', '-init', 'unique-schema.sql'], input='')
d_con = sqlite3.connect('unique.sqlite')
d_db = d_con.cursor()

s_con = sqlite3.connect('file:' + sys.argv[1] + '?mode=ro', uri=True, isolation_level=None, check_same_thread=False)
s_db = s_con.cursor()

todo = []

def process_todo():
	global d_con, d_db, todo
	if len(todo) == 0:
		return

	sh = '#!/bin/bash\n'
	for i in range(0,len(todo)):
		row = todo[i]
		row[2] = re.sub(r'<!--.*?-->', r'', row[2], flags=re.DOTALL)
		row[2] = re.sub(r'<\?xml.*?\?>', r'', row[2], flags=re.DOTALL)
		Path(tmpdir + f'/uniq-input{i}.html').write_text(row[2])
		Path(tmpdir + f'/uniq-output{i}.html').write_text('')
		sh += f'timeout 2m tf-extract -s visl -d {tmpdir}/uniq-extract{i} -K {tmpdir}/uniq-input{i}.html {tmpdir}/uniq-output{i}.html &\n'

	sh += '''
for job in `jobs -p`
do
	wait $job
done
'''

	Path(tmpdir+'/unique.sh').write_text(sh)
	subprocess.run(['/bin/bash', tmpdir+'/unique.sh'], input='')

	for i in range(0,len(todo)):
		row = todo[i]
		ps = Path(tmpdir + f'/uniq-output{i}.html').read_text(encoding='UTF-8')
		ss = re.findall(r'<s id="[^"]+">(.+?)</s>', ps, flags=re.DOTALL)
		for s in ss:
			s = s.strip()
			h = hashlib.sha1(bytes(s, 'UTF-8')).hexdigest()
			d_db.execute("INSERT OR IGNORE INTO html_pieces (r_hash, r_url, r_piece, r_stamp) VALUES (?, ?, ?, ?)", [h, row[4], s, row[3]])

		d_con.commit()

	todo = []

s_db.execute("SELECT r_url, r_headers, r_body, r_stamp FROM sc_results")
while row := s_db.fetchone():
	row = list(row)
	d_db.execute("SELECT rowid FROM urls_seen WHERE r_url = ?", [row[0]])
	if d_db.fetchall():
		continue
	'''
	# Check if a URL yielded any unique segments
	rows = d_db.fetchall()
	if rows:
		d_db.execute("SELECT r_url FROM html_pieces WHERE r_url = ? LIMIT 1", [rows[0][0]])
		if d_db.fetchall():
			continue
	'''

	d_db.execute("INSERT OR IGNORE INTO urls_seen (r_url) VALUES (?)", [row[0]])
	d_con.commit()

	d_db.execute("SELECT rowid FROM urls_seen WHERE r_url = ?", [row[0]])
	row.append(d_db.fetchone()[0])

	stamp = re.search(r"b'Last-Modified': \[b'(.+?)'\]", row[1])
	if stamp:
		stamp = stamp[1]
	else:
		stamp = row[3]
	row[3] = stamp
	print(f'Parsing {row[4]} ({row[3]}): {row[0]}')

	todo.append(row)
	if len(todo) >= 16:
		process_todo()

process_todo()
