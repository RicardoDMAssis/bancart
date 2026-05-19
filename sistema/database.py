# database.py
import sqlite3
import os
import shutil
from datetime import datetime
from sistema.config import DB_NAME

def iniciar_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    
    c.execute("""CREATE TABLE IF NOT EXISTS produtos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nome TEXT, preco REAL, estoque INTEGER, codigo TEXT
    )""")
    
    c.execute("""CREATE TABLE IF NOT EXISTS vendas (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        mesa_id INTEGER,
        produto_nome TEXT, qtd INTEGER, total REAL,
        data_hora TEXT, pagamento TEXT, status TEXT
    )""")
    
    try:
        c.execute("SELECT codigo FROM produtos LIMIT 1")
    except sqlite3.OperationalError:
        c.execute("ALTER TABLE produtos ADD COLUMN codigo TEXT")
        print("Coluna 'codigo' adicionada com sucesso!")
        
    conn.commit()
    conn.close()

def fazer_backup():
    if os.path.exists(DB_NAME):
        if not os.path.exists("backups"): 
            os.mkdir("backups")
        data = datetime.now().strftime("%Y-%m-%d")
        shutil.copy(DB_NAME, f"backups/backup_{data}.db")