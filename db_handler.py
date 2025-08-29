#Imports
import sqlite3 #SQLite3 for Database
import sys #sys for importing CLI arguments
import os #os for automated DB clearing during debug


#Global Vars
DB = None #DB variable
CURSOR = None #DB Cursor variable


def db_init(db_name: str = "data.db"):
    """Intializes the database with default name or function provided name
       Attempts to create the base table with rows and cols and gracefully
       skips if the database w/ the table already exists

    Args:
        db_name (str, optional): File name for database; Defaults to "data.db".
    """
    global DB
    global CURSOR
    DB = sqlite3.connect(db_name)
    CURSOR = DB.cursor()
    
    try:
        CURSOR.execute("CREATE TABLE transactions(date, descrip, amnt, tags)")
    except sqlite3.OperationalError:
        print("Table already exists, skipping...")
    
def _db_testFetch ():
    fetch = []
    for row in CURSOR.execute("SELECT date, descrip, amnt, tags FROM transactions"):
        fetch.append(row)
    fetch.sort(key=_db_sortByDate)
    print(fetch)

def _db_testAdd ():
    CURSOR.execute("""
        INSERT INTO transactions VALUES
            ('1/5/2000','McDonalds', 13.75, 'Fast Food'),
            ('1/2/2000','Exxon Gas Station', 25.00, 'Gas'),
            ('1/16/2000','Target Supercenter', 81.66, 'None')
    """)
    DB.commit()

def _db_testEdit():
    pass

def _db_testRemove():
    pass

def _db_sortByDate(e: str) -> int:
    arr = e[0].split('/')
    sum = 0
    for val in arr:
        sum += int(val)
    return sum
    
def _db_debug():
    try:
        open("debug.db","r")
        os.system("del debug.db")
    except FileNotFoundError:
        pass
    db_init("debug.db")
    _db_testAdd()
    _db_testFetch()



if __name__ == "__main__":
    if len(sys.argv) > 1:
        if sys.argv.count("--debug") == 1:
            print("Starting db_handler in debug mode")
            _db_debug()
        else:
            print("Unrecognized flags, please use debug flags when executing")
    else:
        print("Improper Module Use. Please import with \"import db_handle.py\"")
else:
    print("Loading database handler module...")
    db_init()
    print("Database handler initialized")