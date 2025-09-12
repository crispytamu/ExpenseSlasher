#Imports
import sqlite3 #SQLite3 for Database
import sys #sys for importing CLI arguments
import os #os for automated DB clearing during debug

#TODO - Transaction template

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
        #enabling foreign keys for cascading deletions
        CURSOR.execute ("PRAGMA foreign_keys = ON;")
        #transaction table
        CURSOR.execute("""
            CREATE TABLE transactions (
                transaction_id INTEGER PRIMARY KEY,
                date TEXT,
                desc TEXT,
                amnt REAL
            );
        """)
        
        #tag table
        CURSOR.execute("""
            CREATE TABLE tags (
                tag_id INTEGER PRIMARY KEY,
                name TEXT UNIQUE
            );
        """)
        
        #transaction_tag joint table
        CURSOR.execute("""
            CREATE TABLE transactions_tags (
                transaction_id INTEGER NOT NULL, 
                tag_id INTEGER NOT NULL, 
                FOREIGN KEY (transaction_id) REFERENCES transactions(transaction_id) ON DELETE CASCADE,
                FOREIGN KEY (tag_id) REFERENCES tags (tag_id) ON DELETE CASCADE,
                UNIQUE (transaction_id, tag_id)
            );
        """)
        DB.commit()
    except sqlite3.OperationalError as e:
        print("Error Creating Tables...")
        print(e)

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
        print("Error writing entry: ",e)
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

def db_edit_transaction (transactionID: int,
                         date: str = None,
                         desc: str = None,
                         amnt: float = None) -> bool:
    """edits a SINGLE transaction of their core data points, which does not
    include tags. Use db_add_transaction_tags or db_del_transaction_tags for 
    tag mutating

    Args:
        transactionID (int): Transaction ID of trans to edit; aquired from 
                             previous fetch calls
        date (str, optional): New date string. Defaults to None.
        desc (str, optional): New desc string. Defaults to None.
        amnt (float, optional): New amnt float. Defaults to None.

    Returns:
        bool: True on successful edit, false on no edit made/unsuccessful edit
    """    
    commands = []
    params = []
    
    if date is not None:
        commands.append("date = ?")
        params.append(date)
    if desc is not None:
        commands.append("desc = ?")
        params.append(desc)
    if amnt is not None:
        commands.append("amnt = ?")
        params.append(amnt)
        
    if not commands:
        print("No data to update.")
        return False
    
    try:
        query = f"""UPDATE transactions
                   SET {",".join(commands)}
                   WHERE ROWID = ?
                """
        params.append(transactionID)
        
        CURSOR.execute(query,tuple(params))
        DB.commit()
        print(f"Transaction with ID {transactionID} updated successfully!")
        return True
    except sqlite3.Error as e:
        print("Error updating transaction: ",e)
        DB.rollback()
        return False

def db_add_transaction_tags (transactionID: int, tags: list[str] = None) -> bool:
    """Adds the list of tags to transaction id

    Args:
        transactionID (int): transaction id, from preivous fetches
        tags (list[str], optional): list of tags as strings to add. Defaults to None.

    Returns:
        bool: returns True on successful/duplicate addition,
              false on no/unsuccessful edit
    """    
    if tags is not None:
        try:
            for tag in tags:
                #First search tags table if tag exists
                CURSOR.execute("SELECT ROWID FROM tags WHERE name = ?", (tag,))
                res = CURSOR.fetchone()
                
                #if tag found, grab id, if not, insert and grab new id
                if res:
                    tag_id = res[0]
                else:
                    CURSOR.execute("INSERT INTO tags (name) VALUES (?)", (tag,))
                    tag_id = CURSOR.lastrowid
                
                #then link transaction to tag in joint table
                CURSOR.execute("""
                    INSERT OR IGNORE INTO transactions_tags (transaction_id, tag_id)
                    VALUES (?,?)
                """, (transactionID,tag_id))
               
            DB.commit()
            print(f"Tags for Transaction ID: {transactionID} added successfully!")
            return True
        except sqlite3.Error as e:
            print("Error adding tag: ",e)
            DB.rollback()
            return False 
    else:
        print("No tags to add")
        return False

def db_delete_transaction_tags (transactionID: int, tags: list[str] = None) -> bool:
    """deletes tags from a transaction via removing relational entry in joint
    table, and prunes the tag table as needed

    Args:
        transactionID (int): transaction id, from previous fetches
        tags (list[str], optional): list of tags to remove from transaction.
            Defaults to None.

    Returns:
        bool: returns True on successful remove, even if tag is not present for
            transaction id; returns false if tag array is empty or error on
            removal
    """    
    #checks for tags in tag list
    if tags is not None:
        try:
            for tag in tags:
                for tag in tags:
                    #checks for entries in joint table with tag name
                    CURSOR.execute("SELECT ROWID FROM tags WHERE name = ?",(tag,))
                    res = CURSOR.fetchone()
                    
                    #if tag exists, remove relational entry
                    if res:
                        tag_id = res[0]
                        
                        CURSOR.execute("""
                            DELETE FROM transactions_tags
                            WHERE transaction_id = ? AND tag_id = ?
                        """,(transactionID,tag_id))
                        
                        #check if tag has no other transactions relating to it
                        CURSOR.execute("""
                            SELECT COUNT(*) FROM transactions_tags
                            WHERE tag_id = ?
                            """,(tag_id,))
                        otherLinks = CURSOR.fetchone()[0]
                        
                        #if no other trans, prune tag from tag table
                        if otherLinks == 0:
                            CURSOR.execute("""
                                DELETE FROM tags
                                WHERE ROWID = ?
                                """,(tag_id,))
            DB.commit()
            print(f"Tags for transaction ID {transactionID} removed successfully")
            return True
        except sqlite3.Error as e:
            print("Error removing tags: ",e)
            return False    
    else:
        print("No passed tags to remove")
        return False

def db_delete_transaction (transactionID: int = None) -> bool:
    """function to remove a single transaction by transaction ID

    Args:
        transactionID (int): transaction ID, from preivous fetches

    Returns:
        bool: returns true on a successful removal; false on non matching entry
            or database error
    """
    #find entry in transactions table
    if transactionID is not None:
        try:
            CURSOR.execute ("""
                SELECT ROWID 
                FROM transactions
                WHERE ROWID = ?
                """,(transactionID,))
            res = CURSOR.fetchone()
            if res:
                #if found, delete transaction
                CURSOR.execute ("""
                    DELETE
                    FROM transactions
                    WHERE ROWID = ?
                    """,(transactionID,))
                
                #THEN prune tag table for orphaned tags
                CURSOR.execute("""
                    SELECT T.tag_id
                    FROM tags AS T
                    LEFT JOIN transactions_tags AS JT
                    ON T.tag_id = JT.tag_id
                    WHERE JT.tag_id IS NULL
                """)
                orphaned_tags = CURSOR.fetchall()
                
                if orphaned_tags:
                    print("Orphaned tags found, pruning...")
                    orphaned_ids = [tag[0] for tag in orphaned_tags]
                    
                    tmp = ','.join('?' * len(orphaned_ids))
                    CURSOR.execute(f"""
                        DELETE
                        FROM tags
                        WHERE tag_id
                        IN ({tmp})
                    """,tuple(orphaned_ids))
                
                DB.commit()
                print(f"Transaction ID {transactionID} has bee successfully deleted")
                return True
            else:
                print(f"No transaction with ID {transactionID} found")
                return False
        except sqlite3.Error as e:
            print("Error deleting transaction: ",e)
            DB.rollback()
            return False
    else:
        print("No transaction ID provided")
        return False
        
def db_delete_tag (tags: list[str] = None) -> bool:
    """function to delete tags from tag list and removes those tags from ALL
        transactions

    Args:
        tags (list[str], optional): list of tags to remove. Defaults to None.

    Returns:
        bool: returns true when ALL tags in list have been removed
            returns false if atleast one removal fails, empty tag list, or db error
    """
    if tags is not None:
        try:
            for tag in tags:
                CURSOR.execute("""
                    DELETE
                    FROM tags
                    WHERE name = ?
                    """, (tag,))
            
            DB.commit()
            print("Tags successfully deleted")
            return True
        except sqlite3.Error as e:
            print("Error deleting tags: ",e)
            DB.rollback()
            return False
    else:
        print("Tag list is empty")
        return False

#TODO    
def db_bulk_add_transaction (transaction_list:list[str,str,float,list[str]] = None) -> bool:
    """bulk adds transactions from a list of transactions

    Args:
        transaction_list (list[str,str,float,list[str]], optional): 
        list of transaction data to add. Defaults to None.

    Returns:
        bool: returns true on successful add of ALL transactions;
            false on atleast one failed add, empty transaction list, or db error
    """
    #TODO
    pass

def db_bulk_remove_transaction(transaction_list: list[int] = None) -> bool:
    """removes several transactions based on transaction list

    Args:
        transaction_list (list[int], optional): list of transaction IDs.
            Defaults to None.

    Returns:
        bool: returns True on successful removal of ALL transactions;
            false if atleast one removal fails, empty id list, or db error
    """
    #TODO
    pass

def db_bulk_add_tag (transaction_list: list[int] = None, tags: list[str] = None) -> bool:
    """adds a list of tags to ALL transactions in transaction list

    Args:
        transaction_list (list[int]): list of transaction ids
        tags (list[str]): list of tags to add to ALL transactions in list

    Returns:
        bool: returns true on successful addition to ALL transactions;
            false on at least one failed add, empty id or tag list, or db error
    """
    #TODO
    pass

def db_bulk_delete_tag (transaction_list: list[int] = None, tags: list[str] = None) -> bool:
    """removes tags in list from ALL transactions in provided list

    Args:
        transaction_list (list[int], optional): list of transaction ids.
        tags (list[str], optional): list of tags to remove from transactions.

    Returns:
        bool: returns true on successful removal of ALL tags from ALL 
            transactions; false on atleast one failed removal, empty lists, or 
            db error
    """
    #TODO
    pass

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
    _db_debug_print(db_fetch_all())
    print()
    
    db_delete_transaction(2)
    _db_debug_print(db_fetch_all())
    print()
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
    _db_debug_print(db_fetch_all())
    print()
    #_db_debug_print(db_fetch_all())
    #_db_debug_print(db_fetch_set(None,None,None,None))
    db_edit_transaction(4,amnt=69.69)
    db_edit_transaction(6,desc="Amazon-Weekly shipment")
    db_add_transaction_tags(6,["Travel","Out-Of-Country"])
    db_add_transaction_tags(10,["Fast Food"])
    db_add_transaction_tags(13,["Date Night"])
    _db_debug_print(db_fetch_all())
    print()
    db_delete_transaction_tags(5,["Commute"])
    db_delete_transaction_tags(7,["Bunga"])
    db_delete_transaction_tags(11,["Fast Food"])
    _db_debug_print(db_fetch_all())
    print()
    return
    db_delete_transaction_tags(9,["Subscription","Entertainment"])
    _db_debug_print(db_fetch_all())
    print()
    db_delete_transaction(3)
    db_delete_transaction(6)
    _db_debug_print(db_fetch_all())
    print()
    
    db_add_transaction_tags(1,["Howdy"])
    db_add_transaction_tags(4,["Howdy"])
    db_add_transaction_tags(5,["Howdy"])
    db_add_transaction_tags(7,["Howdy"])
    db_add_transaction_tags(8,["Howdy"])
    db_add_transaction_tags(9,["Howdy"])
    db_add_transaction_tags(10,["Howdy"])
    db_add_transaction_tags(11,["Howdy"])
    db_add_transaction_tags(12,["Howdy"])
    db_add_transaction_tags(13,["Howdy"])
    _db_debug_print(db_fetch_all())
    print()
    
    db_delete_tag(["howdy"])
    db_delete_tag(["Howdy"])
    _db_debug_print(db_fetch_all())
    



if __name__ == "__main__":
    if len(sys.argv) > 1:
        if sys.argv.count("--debug") == 1:
            print("Starting db_handler in debug mode")
            _db_debug()
        else:
            print("Unrecognized flags, please use debug flags when executing")
    else:
        print("Improper Module Use. Please import with \"import db_handler.py\"")
else:
    print("Loading database handler module...")
    db_init()
    print("Database handler initialized")