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
            file_found TEXT,
            file_ext TEXT,
            file_path TEXT,
            folders TEXT,
            pro_comp INTEGER NOT NULL,
            message TEXT,
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

def format_for_db(value):
    """
    Formats the input value for consistent database storage.

    - Converts None to an empty string.
    - Converts lists to comma-separated strings.
    - Leaves other data types unchanged.

    Parameters:
    - value: The input value to be formatted.

    Returns:
    - The formatted value as a string.
    """
    if value is None:
        return ''
    elif isinstance(value, list):
        return ', '.join(map(str, value))
    else:
        return str(value)

#file cmd process database
def filepush(cmd_id,intent,pro_comp,file_name = None,file_found = None,file_path = None,folders = None ,message = None,file_ext = None):
    # Connect to SQLite database 
    conn = sqlite3.connect('my_database.db')
    intent = format_for_db(intent)
    pro_comp = format_for_db(pro_comp)
    file_name = format_for_db(file_name)
    file_found = format_for_db(file_found)
    file_path = format_for_db(file_path)
    folders = format_for_db(folders)
    message = format_for_db(message)
    file_ext = format_for_db(file_ext)
    
    # Create a cursor object using the cursor() method
    cursor = conn.cursor()
    if pro_comp == False:
        cursor.execute("INSERT INTO file_cmd (cmd_id,intent_id,file_name,file_found,file_ext,file_path,folders,pro_comp,message) VALUES (?,?,?,?,?,?,?,?,?)",(cmd_id,intent,file_name,file_found,file_ext,file_path,folders,0,message))
    else:
        cursor.execute("INSERT INTO file_cmd (cmd_id,intent_id,file_name,file_found,file_ext,file_path,folders,pro_comp,message) VALUES (?,?,?,?,?,?,?,?,?)",(cmd_id,intent,file_name,file_found,file_ext,file_path,folders,1,message))
     # Commit the changes and close the connection
    conn.commit()
    conn.close()

def check_pre_file(n):
    # Connect to SQLite database 
    conn = sqlite3.connect('my_database.db')
    
    # Create a cursor object using the cursor() method
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM file_cmd ORDER BY pro_id DESC LIMIT ?", (n,))
    rows = cursor.fetchall()

      # Close the connection
    conn.close()
    return rows
def is_latest_cmd_type(cmd_type_id):
    conn = sqlite3.connect('my_database.db')
    cursor = conn.cursor()
    cursor.execute("SELECT cmd_type_id FROM commands ORDER BY cmd_id DESC LIMIT 1")
    result = cursor.fetchone()
    conn.close()
    if result[0] is None:
        return None
    return True if result[0] == cmd_type_id else False


def get_intent_type(intent_id):
    conn = sqlite3.connect('my_database.db')
    cursor = conn.cursor()
    cursor.execute("SELECT intent FROM file_intent WHERE intent_id = ?", (intent_id,))
    result = cursor.fetchone()
    conn.close()
    return result[0] if result else None

