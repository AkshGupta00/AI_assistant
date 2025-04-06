import sqlite3

def create_database():
    conn = sqlite3.connect('my_database.db')
    cursor = conn.cursor()

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS cmd_tpyes (
            cmd_type_id INTEGER PRIMARY KEY AUTOINCREMENT,
            cmd_type TEXT
        )
    ''')
    cursor.executemany("INSERT INTO cmd_tpyes (cmd_type) VALUES (?)", [("basic",), ("file",)])

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS commands (
            cmd_id INTEGER PRIMARY KEY AUTOINCREMENT,
            raw_cmd TEXT NOT NULL,
            cmd_type_id INTEGER NOT NULL,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(cmd_type_id) REFERENCES cmd_tpyes(cmd_type_id)
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS basic_sys_cmd (
            pro_id INTEGER PRIMARY KEY AUTOINCREMENT,
            cmd_id INTEGER,
            raw_cmd TEXT NOT NULL,
            intent TEXT NOT NULL,
            pro_comp INTEGER NOT NULL,
            fail_reason TEXT,
            FOREIGN KEY(cmd_id) REFERENCES commands(cmd_id)
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS file_intent (
            intent_id INTEGER PRIMARY KEY AUTOINCREMENT,
            intent TEXT NOT NULL
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS file_cmd (
            pro_id INTEGER PRIMARY KEY AUTOINCREMENT,
            cmd_id INTEGER,
            intent_id INTEGER NOT NULL,
            file_name TEXT,
            file_ext TEXT,
            file_path TEXT,
            folders TEXT,
            pro_comp INTEGER NOT NULL,
            fail_reason TEXT,
            FOREIGN KEY(cmd_id) REFERENCES commands(cmd_id),
            FOREIGN KEY(intent_id) REFERENCES file_intent(intent_id)
        )
    ''')
    intents = [("open",), ("search",), ("create",), ("rename",), ("move",),("copy",), ("delete",), ("compress",), ("extract",), ("storage",)]    
    cursor.executemany("INSERT INTO file_intent (intent) VALUES (?)", intents)
    

    conn.commit()
    conn.close()

def cmd_push(raw_cmd,type_id):
    conn = sqlite3.connect('my_database.db')
    cursor = conn.cursor()
    cursor.execute('''INSERT INTO commands (raw_cmd,cmd_type_id) VALUES (?,?)''', (raw_cmd,type_id))
    conn.commit()
    conn.close()

def get_latest_cmd_id():
    conn = sqlite3.connect('my_database.db')
    cursor = conn.cursor()
    cursor.execute("SELECT cmd_id FROM commands ORDER BY cmd_id DESC LIMIT 1")
    result = cursor.fetchone()
    conn.close()
    return result[0] if result else None


#file cmd process database
def filepush(cmd_id,intent,pro_comp,file_name = None,file_ext = None,file_path = None,folders = None ,fail_reason = None):
    # Connect to SQLite database 
    conn = sqlite3.connect('my_database.db')
    
    # Create a cursor object using the cursor() method
    cursor = conn.cursor()
    if pro_comp == False:
        cursor.execute("INSERT INTO file_cmd (cmd_id,intent,file_name,file_ext,file_path,folders,pro_comp,fail_reason) VALUES (?,?,?,?,?,?,?,?)",(cmd_id,intent,file_name,file_ext,file_path,folders,0,fail_reason))
    else:
        cursor.execute("INSERT INTO file_cmd (cmd_id,intent,file_name,file_ext,file_path,folders,pro_comp,fail_reason) VALUES (?,?,?,?,?,?,?,?)",(cmd_id,intent,file_name,file_ext,file_path,folders,1,fail_reason))
     # Commit the changes and close the connection
    conn.commit()
    conn.close()

def check_pre(n):
    # Connect to SQLite database 
    conn = sqlite3.connect('my_database.db')
    
    # Create a cursor object using the cursor() method
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM file_cmd ORDER BY pro_id DESC LIMIT ?", (n,))
    rows = cursor.fetchall()

      # Close the connection
    conn.close()
    return rows
if __name__ == "__main__":
    create_database()
