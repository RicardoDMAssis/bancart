# sistema/database.py
import sqlite3
import os
import shutil
from datetime import datetime
from sistema.config import DB_NAME

def iniciar_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    
    # 1. Tabela de Produtos (Cadastro do Estoque)
    c.execute("""CREATE TABLE IF NOT EXISTS produtos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nome TEXT, 
        preco REAL, 
        estoque INTEGER, 
        codigo TEXT
    )""")
    
    # 2. TABELA PAI: Atendimentos (Comandas de Mesas)
    c.execute("""CREATE TABLE IF NOT EXISTS atendimentos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        mesa_id INTEGER,
        data_abertura TEXT,
        data_fechamento TEXT,
        desconto REAL DEFAULT 0.0,
        pagamento TEXT,
        status TEXT -- 'ABERTO' ou 'FECHADO'
    )""")
    
    # 3. TABELA FILHO: Itens do Atendimento (Produtos consumidos na comanda)
    c.execute("""CREATE TABLE IF NOT EXISTS itens_atendimento (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        atendimento_id INTEGER, -- Liga direta com a tabela pai
        produto_nome TEXT,
        qtd INTEGER,
        total REAL,
        FOREIGN KEY(atendimento_id) REFERENCES atendimentos(id) ON DELETE CASCADE
    )""")
    
    # 4. Tabela de Vendas Avulsas (Balcão Rápido) - Mantida simples e direta
    c.execute("""CREATE TABLE IF NOT EXISTS vendas_balcao (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        produto_nome TEXT,
        qtd INTEGER,
        total REAL,
        data_hora TEXT,
        pagamento TEXT
    )""")
    
    # 5. Tabela do Controle do Fluxo de Caixa
    c.execute("""CREATE TABLE IF NOT EXISTS controle_caixa (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        data TEXT,
        valor_abertura REAL,
        valor_fechamento REAL,
        status TEXT
    )""")
    
    # Verificação de compatibilidade de colunas antigas
    try:
        c.execute("SELECT codigo FROM produtos LIMIT 1")
    except sqlite3.OperationalError:
        c.execute("ALTER TABLE produtos ADD COLUMN codigo TEXT")
        
    conn.commit()
    conn.close()

def fazer_backup():
    if os.path.exists(DB_NAME):
        if not os.path.exists("backups"): 
            os.mkdir("backups")
        data = datetime.now().strftime("%Y-%m-%d")
        shutil.copy(DB_NAME, f"backups/backup_{data}.db")

def processar_baixa_estoque_vinculado(cursor, codigo_produto_vendido, qtd_vendida):
    """Regra de Negócio: Jantinha (001) consome 1 Espeto (100)"""
    if not codigo_produto_vendido:
        return

    codigo_limpo = str(codigo_produto_vendido).strip()
    if codigo_limpo in ["001", "1"]:
        espeto = cursor.execute("SELECT id, estoque, nome FROM produtos WHERE codigo = '100'").fetchone()
        if espeto:
            espeto_id, espeto_estoque, espeto_nome = espeto
            if espeto_estoque < qtd_vendida:
                raise ValueError(f"Estoque insuficiente de '{espeto_nome}' para compor a Jantinha!")
            cursor.execute("UPDATE produtos SET estoque = estoque - ? WHERE id = ?", (qtd_vendida, espeto_id))