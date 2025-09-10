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

def db_fetch_all () -> list[tuple[int,str,str,float,str]]:
    fetch = []
    """
        First we grab all the cols in transaction table and a col which lists
        all the Tag names in a list related to a single transaction
        
        then we merge the joint table to the trans table, using the
        transaction ids as the common id
        
        we then add the tags table to the joint table, using the tag ids as the
        common id
        
        finally, grouping the entries by rowid will allow the group concat to
        merge duplicate transaction records' tags into a single entry with a
        list of its matching tags and outputs that single transaction record
    """
    CURSOR.execute("""
        SELECT T.ROWID, T.date, T.desc, T.amnt, GROUP_CONCAT(Tag.name) as tags
        FROM transactions as T
        LEFT JOIN transactions_tags as JT on T.ROWID = JT.transaction_id
        LEFT JOIN tags as Tag On JT.tag_id = Tag.ROWID
        GROUP BY T.ROWID
        """)
    fetch = CURSOR.fetchall()
    return fetch
  
def db_fetch_all_tagless () -> list[tuple[int,str,str,float]]:
    """Fetches all transactions in transaction table and retuns list of tuples
    representing each transaction WITHOUT tags

    Returns:
        list[tuple[str,str,float]]: list of tuples representing transactions
    """    
    fetch = []
    for row in CURSOR.execute("""
            SELECT ROWID, date, desc, amnt 
            FROM transactions 
            ORDER BY ROWID
    """):
        fetch.append(row)
    return fetch

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

def db_fetch_set (date:str = None,
                  desc: str = None,
                  amnt: tuple[str,float]|float = None,
                  tags:list[str] = None) -> list[tuple[str,str,str,float,str]]:
    """DB lookup method for a subset of records based on search critera

    Args:
        date (str, optional): date in YYYY-MM-DD format. Defaults to None.
        desc (str, optional): Description of charge, SQLite 3 attempts autofill.
                              Defaults to None.
        amnt (tuple[str,float] | float, optional): Exact value or above/below.
            For Exact: pass float for exact amnt searching for
            For Range: pass tuple[str,float] where str is +/> or -/<
                       results are inclusive
            Defaults to None.
        tags (list[str], optional): List of tags as strings. Defaults to None.

    Returns:
        list[tuple[str,str,str,float,str]]: list of records that match search
            criteria as tuples with following data:
            str: Transaction ID
            str: Date
            str: Description
            float: ammount (+ is debit, - is credit)
            str: string of tags seperated by ','
    """
    
    #Base query
    query = """
        SELECT 
            T.ROWID, T.date, T.desc, T.amnt, GROUP_CONCAT(Tag.name) as tags
        FROM
            transactions AS T
        LEFT JOIN
            transactions_tags AS JT ON T.ROWID = JT.transaction_id
        LEFT JOIN
            tags AS Tag ON JT.tag_id = Tag.ROWID
        WHERE 1=1
        """
    params = []
    
    #dynamically appending to query if search criteria exists
    if date is not None:
        query += " AND T.date = ?"
        params.append(date)
    if desc is not None:
        query += " and T.desc LIKE ?"
        params.append(f"%{desc}%")
    if amnt is not None:
        #checks if single float or tuple for range
        if type(amnt) == float:
            query += " and amnt = ?"
            params.append(amnt)
        else:
            if amnt[0] == '-' or amnt[0] == '<':
                query += " and amnt <= ?"
            elif amnt[0] == '+' or amnt[0] == '>':
                query += " and amnt >= ?"
            else: #invalid tuple symbol results in exact search
                query += " and amnt = ?"
            params.append(amnt[1])
    if tags:
        tmp = ','.join(['?'] * len(tags))
        query += f" AND Tag.name IN ({tmp})"
        params.extend(tags)
        
    query += """
        GROUP BY
            T.ROWID
    """    
    try:
        CURSOR.execute(query,tuple(params))
        return CURSOR.fetchall()
    except sqlite3.Error as e:
        print("DB Error: ",e)

def _db_debug_print (E):
    for i in E:
        print(i)
        
def _db_debug():
    if os.path.exists("debug.db"):
        os.remove("debug.db")
    
    db_init("debug.db")
    db_add_transaction("2000-01-05","McDonalds",12.99,["Fast Food"])
    db_add_transaction("2000-03-19","HEB",249.99,["Groceries","Extra"])
    db_add_transaction("2001-09-13","Taco Bell", 11.46,["Fast Food"])
    db_add_transaction("2000-01-20", "Burger King", 15.50, ["Fast Food", "Lunch"])
    db_add_transaction("2000-02-05", "Exxon Gas Station", 45.00, ["Gas", "Commute"])
    db_add_transaction("2000-04-10", "Amazon", 8.99, [])
    db_add_transaction("2000-05-15", "Movie Theater", 32.75, ["Entertainment", "Date Night"])
    db_add_transaction("2000-06-25", "Whole Foods", 75.00, ["Groceries"])
    db_add_transaction("2000-07-30", "Netflix", 16.99, ["Subscription", "Entertainment"])
    db_add_transaction("2001-01-01", "ZeroTag1", 100.00, [])
    db_add_transaction("2001-01-01", "ZeroTag2", 100.00, [])
    db_add_transaction("2001-01-01", "ZeroTag3", 100.00, [])
    db_add_transaction("2001-01-01", "ZeroTag4", 100.00, [])
    _db_debug_print(db_fetch_all_tagless())
    #_db_debug_print(db_fetch_all())
    #_db_debug_print(db_fetch_set(None,None,None,None))



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