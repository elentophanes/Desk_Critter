# Desk_Critter — https://github.com/elentophanes/Desk_Critter
# Copyright (c) 2026 Elentophanes and contributors
# Licensed under the PolyForm Noncommercial License 1.0.0 (see LICENSE).
# Commercial use requires a separate license — see COMMERCIAL.md.
# Required Notice: Copyright (c) 2026 Elentophanes (https://github.com/elentophanes/Desk_Critter)
"""Read-only probe: which apps have recent Windows notifications, and what Claude's look like."""

__author__ = "Elentophanes"
__project_id__ = "6075ff8b1744"
import os, sqlite3

src = os.path.expandvars(r"%LOCALAPPDATA%\Microsoft\Windows\Notifications\wpndatabase.db")
print("exists:", os.path.exists(src))
con = sqlite3.connect("file:" + src + "?mode=ro", uri=True)
cur = con.cursor()
print("tables:", [r[0] for r in cur.execute("select name from sqlite_master where type='table'")])
print("\nRecent notifications per app:")
q = """select h.PrimaryId, count(*), max(n.Id), max(n.ArrivalTime)
       from Notification n join NotificationHandler h on h.RecordId = n.HandlerId
       group by h.PrimaryId order by 4 desc limit 8"""
for r in cur.execute(q):
    print(" ", r)
print("\nLatest Claude notifications:")
q = """select n.Id, n.ArrivalTime, substr(cast(n.Payload as text), 1, 300)
       from Notification n join NotificationHandler h on h.RecordId = n.HandlerId
       where h.PrimaryId like '%Claude%' order by n.Id desc limit 4"""
for r in cur.execute(q):
    print(" ", r)
