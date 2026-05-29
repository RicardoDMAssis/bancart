# main.py
import tkinter as tk
from tkinter import ttk
import sqlite3

# Importações dos nossos novos módulos
from sistema.config import CORES, DB_NAME
import sistema.database as database
from sistema.aba_mesas import AbaMesas
from sistema.aba_balcao import AbaBalcao
from sistema.aba_estoque import AbaEstoque
from sistema.aba_caixa import AbaCaixa

import os
import sys

def obter_caminho_recurso(caminho_relativo):
    """ Retorna o caminho absoluto para o recurso, funcionando no desenvolvimento e no PyInstaller """
    try:
        # O PyInstaller cria uma pasta temporária e armazena o caminho em _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, caminho_relativo)

# --- EXEMPLO DE USO ---
# Se antes você abria um arquivo assim:
# com open("sistema/dados.csv") as f:

# Agora você deve abrir assim:
caminho_do_arquivo = obter_caminho_recurso("sistema/dados.csv")
with open(caminho_do_arquivo, "r") as f:
    conteudo = f.read()

class BancartApp:
    def __init__(self, root):
        self.root = root
        self.root.title("BANCART PRO 5.0 - Gestão Inteligente")
        self.root.geometry("1100x700")
        self.root.configure(bg=CORES['fundo'])
        
        # Configuração de Estilos Visuais
        style = ttk.Style()
        style.theme_use('clam')
        style.configure("TFrame", background=CORES['fundo'])
        style.configure("TLabel", background=CORES['fundo'], foreground=CORES['texto'], font=('Arial', 11))
        style.configure("Treeview", background="#404040", foreground="white", fieldbackground="#404040", rowheight=25)
        style.map("Treeview", background=[('selected', CORES['azul'])])

        self.lista_produtos_cache = [] # Cache centralizado compartilhado

        # Criando o Notebook de abas
        self.abas = ttk.Notebook(root)
        self.abas.pack(fill='both', expand=True, padx=5, pady=5)

        # Inicializando cada objeto de interface importado
        self.aba_mesas = AbaMesas(self.abas, self)
        self.aba_balcao = AbaBalcao(self.abas, self)
        self.aba_estoque = AbaEstoque(self.abas, self)
        self.aba_caixa = AbaCaixa(self.abas, self)

        # Inserindo as abas construídas no Notebook principal
        self.abas.add(self.aba_mesas, text=" 🍽️  MESAS ")
        self.abas.add(self.aba_balcao, text=" 🛒  BALCÃO ")
        self.abas.add(self.aba_estoque, text=" 📦  ESTOQUE ")
        self.abas.add(self.aba_caixa, text=" 📅  CAIXA ")

    def atualizar_todos_produtos(self):
        """Busca dados no BD uma vez e sincroniza todas as abas necessitadas"""
        conn = sqlite3.connect(DB_NAME)
        itens = conn.cursor().execute("SELECT id, nome, preco, estoque, codigo FROM produtos").fetchall()
        conn.close()
        
        self.lista_produtos_cache = itens
        
        # Sincroniza a tabela do Estoque
        self.aba_estoque.atualizar_tabela(itens)
        
        # Sincroniza os dropdowns de seleção nas abas de vendas
        lista_cb = [f"{i[0]} - {i[1]} | R$ {i[2]:.2f}" for i in itens]
        self.aba_mesas.atualizar_combobox(lista_cb)
        self.aba_balcao.atualizar_combobox(lista_cb)

if __name__ == "__main__":
    database.iniciar_db()
    database.fazer_backup()
    
    root = tk.Tk()
    app = BancartApp(root)
    app.atualizar_todos_produtos()  # Primeira carga dos dados
    app.aba_caixa.carregar_historico() # Primeira carga do histórico de caixa
    
    root.mainloop()