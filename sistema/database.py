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

def processar_baixa_estoque_vinculado(cursor, codigo_produto_vendido, qtd_vendida):
    """
    Regra de Negócio: Se vender Jantinha (código '001'), 
    subtrai automaticamente a mesma quantidade de Espetos (código '100') do estoque.
    """
    if not codigo_produto_vendido:
        return

    codigo_limpo = str(codigo_produto_vendido).strip()
    
    if codigo_limpo in ["001", "1"]:
        espeto = cursor.execute("SELECT id, estoque, nome FROM produtos WHERE codigo = '100'").fetchone()
        
        if espeto:
            espeto_id, espeto_estoque, espeto_nome = espeto
            
            if espeto_estoque < qtd_vendida:
                raise ValueError(f"Estoque insuficiente de '{espeto_nome}' para compor a Jantinha!")
            
            cursor.execute(
                "UPDATE produtos SET estoque = estoque - ? WHERE id = ?",
                (qtd_vendida, espeto_id)
            )
            print(f"-> Vínculo ativado: {qtd_vendida} espeto(s) debitado(s) devido à venda da Jantinha.")