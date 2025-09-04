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
    
    #Building global variables
    global DB
    global CURSOR
    DB = sqlite3.connect(db_name)
    CURSOR = DB.cursor()
    
    #building db tables
    try:
        #transaction table
        CURSOR.execute("""
            CREATE TABLE transactions (
                date TEXT,
                desc TEXT,
                amnt REAL
            );
        """)
        
        #tag table
        CURSOR.execute("""
            CREATE TABLE tags (
                name TEXT UNIQUE
            );
        """)
        
        #transaction_tag joint table
        CURSOR.execute("""
            CREATE TABLE transactions_tags (
                transaction_id INTEGER NOT NULL, 
                tag_id INTEGER NOT NULL, 
                FOREIGN KEY (transaction_id) REFERENCES transactions(ROWID),
                FOREIGN KEY (tag_id) REFERENCES tags (ROWID)
                UNIQUE (transaction_id, tag_id)
            );
        """)
    except sqlite3.OperationalError as e:
        print("Error Creating Tables...")
        print(e)
    finally:
        DB.commit()
    
def _db_testFetch ():
    fetch = []
    for row in CURSOR.execute("""
            SELECT date, desc, amnt 
            FROM transactions 
            ORDER BY date
    """):
        fetch.append(row)
    print(fetch)

def db_add_transaction (date: str, desc: str, amnt: float, tags:list[str]) -> bool:
    """Database function to add a single transaction to the database

    Args:
        date (str): Date of transaction in format YYYY-MM-DD
        desc (str): Description of transaction
        amnt (float): Ammount for transaction, where debits are positive and
        credits are negative. i.e: Buying - (2.00), Refunding - (-2.00)
        tags (list[str]): Array of strings containing tags for sorting

    Returns:
        bool: Returns True/False based on successful database entry
    """    
    try:
        #insert to transaction table
        entryData = (date,desc,amnt)
        CURSOR.execute("""
            INSERT INTO transactions (date,desc,amnt)
            VALUES (?,?,?)
        """, entryData)
        trans_id = CURSOR.lastrowid
        
        #insert to tags table
        for tag in tags:
            #see if tag exists in tag table
            CURSOR.execute("SELECT ROWID FROM tags WHERE name = ?", (tag,))
            tagSearchRes = CURSOR.fetchone()

            if tagSearchRes: #if tag exists
                tag_id = tagSearchRes[0] #set tag_id to that id
            else:#else, insert new entry to tag table and get tag id
                CURSOR.execute("INSERT INTO tags (name) VALUES (?)", (tag,))
                tag_id = CURSOR.lastrowid
            
            #insert to trans_tags table
            CURSOR.execute("""
                INSERT INTO transactions_tags (transaction_id,tag_id)
                VALUES (?,?)
            """, (trans_id,tag_id))
        DB.commit()
    except sqlite3.Error as e:
        print("Error writting entry: ",e)
        DB.rollback()
        return False
    return True

    
def _db_debug():
    if os.path.exists("debug.db"):
        os.remove("debug.db")
    
    db_init("debug.db")
    db_add_transaction("2000-01-05","McDonalds",12.99,["Fast Food"])
    db_add_transaction("2000-03-19","HEB",249.99,["Groceries","Extra"])
    db_add_transaction("2001-09-13","Taco Bell", 11.46,["Fast Food"])
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