# aba_caixa.py
import tkinter as tk
from tkinter import ttk, messagebox
import sqlite3
import os
from datetime import datetime
from sistema.config import CORES, DB_NAME

class AbaCaixa(tk.Frame):
    def __init__(self, parent, app_principal):
        super().__init__(parent, bg=CORES['fundo'])
        self.app = app_principal
        self.montar_interface()

    def montar_interface(self):
        tk.Label(self, text="Vendas Hoje", font=('Arial', 14), bg=CORES['fundo'], fg=CORES['texto']).pack(pady=5)
        self.tree_hist = ttk.Treeview(self, columns=('Hora','Tipo','Prod','Total','Pgto'), show='headings')
        self.tree_hist.heading('Hora', text='Hora'); self.tree_hist.column('Hora', width=80)
        self.tree_hist.heading('Tipo', text='Origem'); self.tree_hist.column('Tipo', width=100)
        self.tree_hist.heading('Prod', text='Produto'); self.tree_hist.column('Prod', width=200)
        self.tree_hist.heading('Total', text='Total'); self.tree_hist.column('Total', width=80)
        self.tree_hist.heading('Pgto', text='Pgto'); self.tree_hist.column('Pgto', width=100)
        self.tree_hist.pack(fill='both', expand=True, padx=10, pady=5)
        
        self.lbl_fat = tk.Label(self, text="Total: R$ 0.00", font=('Arial', 16, 'bold'), fg=CORES['verde'], bg=CORES['fundo']); self.lbl_fat.pack(pady=10)
        
        fr_botoes = tk.Frame(self, bg=CORES['fundo']); fr_botoes.pack()
        tk.Button(fr_botoes, text="Atualizar Lista", command=self.carregar_historico).pack(side='left', padx=10)
        tk.Button(fr_botoes, text="SALVAR RELATÓRIO DO DIA", bg=CORES['azul'], fg='white', font=('Arial', 10, 'bold'), command=self.salvar_relatorio_txt).pack(side='left', padx=10)

    def carregar_historico(self):
        self.tree_hist.delete(*self.tree_hist.get_children()); dt_hoje = datetime.now().strftime("%Y-%m-%d"); fat = 0
        conn = sqlite3.connect(DB_NAME); vendas = conn.cursor().execute(f"SELECT data_hora, mesa_id, produto_nome, total, pagamento FROM vendas WHERE status='FECHADA' AND data_hora LIKE '{dt_hoje}%' ORDER BY id DESC").fetchall(); conn.close()
        for v in vendas:
            origem = f"Mesa {v[1]}" if v[1] > 0 else "BALCÃO"
            self.tree_hist.insert('', 'end', values=(v[0].split(' ')[1], origem, v[2], f"{v[3]:.2f}", v[4])); fat += v[3]
        self.lbl_fat.config(text=f"Total: R$ {fat:.2f}")

    def salvar_relatorio_txt(self):
        dt_hoje = datetime.now().strftime("%Y-%m-%d")
        nome_arq = f"Relatorio_{dt_hoje}.txt"
        try:
            conn = sqlite3.connect(DB_NAME)
            vendas = conn.cursor().execute(f"SELECT data_hora, mesa_id, produto_nome, qtd, total, pagamento FROM vendas WHERE status='FECHADA' AND data_hora LIKE '{dt_hoje}%' ORDER BY id DESC").fetchall()
            conn.close()
            
            if not vendas:
                messagebox.showinfo("Vazio", "Nenhuma venda hoje para salvar."); return

            total_dia = 0
            with open(nome_arq, "w", encoding='utf-8') as f:
                f.write(f"=== RELATORIO DE VENDAS: {dt_hoje} ===\n\n")
                f.write(f"{'HORA':<10} {'ORIGEM':<10} {'PRODUTO':<20} {'QTD':<5} {'TOTAL':<10} {'PAGAMENTO'}\n")
                f.write("-" * 80 + "\n")
                for v in vendas:
                    hora = v[0].split(' ')[1]; origem = f"Mesa {v[1]}" if v[1] > 0 else "Balcão"; prod = v[2][:20]
                    f.write(f"{hora:<10} {origem:<10} {prod:<20} {v[3]:<5} R${v[4]:<8.2f} {v[5]}\n")
                    total_dia += v[4]
                f.write("-" * 80 + "\n")
                f.write(f"TOTAL DO DIA: R$ {total_dia:.2f}\n")
                f.write("=" * 80)
            
            messagebox.showinfo("Sucesso", f"Relatório saved as:\n{nome_arq}")
            os.startfile(nome_arq) if hasattr(os, 'startfile') else os.system(f'xdg-open "{nome_arq}"')
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao salvar: {e}")