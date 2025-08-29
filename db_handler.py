import sqlite3
import sys

def db_init(db_name: str = "data.db"):
    db = sqlite3.connect(db_name)
    cursor = db.cursor()
    
    cursor.execute("CREATE TABLE transactions(date, descrip, amnt, tags)")
    
#def db_testFetch ():
    
def _db_debug():
    db_init("debug.db")

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