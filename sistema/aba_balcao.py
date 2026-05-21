# sistema/aba_balcao.py
import tkinter as tk
from tkinter import ttk, messagebox
import sqlite3
from datetime import datetime
from sistema.config import CORES, DB_NAME

class AbaBalcao(tk.Frame):
    def __init__(self, parent, app_principal):
        super().__init__(parent, bg=CORES['fundo'])
        self.app = app_principal
        self.carrinho_avulso = []
        self.montar_interface()

    def montar_interface(self):
        fr_topo = tk.Frame(self, bg=CORES['painel'], pady=10); fr_topo.pack(fill='x')
        tk.Label(fr_topo, text="BALCÃO RÁPIDO", font=('Arial', 18, 'bold'), fg=CORES['laranja'], bg=CORES['painel']).pack()
        fr_inp = tk.Frame(fr_topo, bg=CORES['painel']); fr_inp.pack(pady=5)
        self.cb_prod_avulso = ttk.Combobox(fr_inp, width=30, font=('Arial', 12)); self.cb_prod_avulso.pack(side='left', padx=5)
        self.ent_qtd_avulso = tk.Entry(fr_inp, width=5, font=('Arial', 12)); self.ent_qtd_avulso.insert(0,"1"); self.ent_qtd_avulso.pack(side='left', padx=5)
        tk.Button(fr_inp, text="LANÇAR", bg=CORES['azul'], fg='white', command=self.add_carrinho_avulso).pack(side='left', padx=10)
        
        self.tree_avulso = ttk.Treeview(self, columns=('Prod','Qtd','Total'), show='headings', height=10)
        self.tree_avulso.heading('Prod', text='Produto'); self.tree_avulso.heading('Qtd', text='Qtd'); self.tree_avulso.heading('Total', text='Total')
        self.tree_avulso.pack(fill='both', expand=True, padx=10, pady=5)
        tk.Button(self, text="Limpar", command=self.limpar_avulso).pack()
        
        fr_base = tk.Frame(self, bg=CORES['painel'], pady=10); fr_base.pack(fill='x', padx=10, pady=10)
        self.lbl_total_avulso = tk.Label(fr_base, text="TOTAL: R$ 0.00", font=('Arial', 24), fg=CORES['verde'], bg=CORES['painel'])
        self.lbl_total_avulso.pack(side='left', padx=20)
        
        fr_pag = tk.Frame(fr_base, bg=CORES['painel']); fr_pag.pack(side='right', padx=20)
        self.cb_pag_avulso = ttk.Combobox(fr_pag, values=["DINHEIRO", "PIX", "CRÉDITO", "DÉBITO"]); self.cb_pag_avulso.current(0); self.cb_pag_avulso.pack()
        
        tk.Button(fr_pag, text="FINALIZAR VENDA", bg=CORES['verde'], fg='white', font=('Arial', 12, 'bold'), command=self.finalizar_avulso).pack(pady=3, fill='x')
        tk.Button(fr_pag, text="🎁 CORTESIA FUNC.", bg=CORES['azul'], fg='white', font=('Arial', 11, 'bold'), command=self.finalizar_cortesia).pack(pady=3, fill='x')

    def atualizar_combobox(self, lista_cb):
        self.cb_prod_avulso['values'] = lista_cb

    def add_carrinho_avulso(self):
        try:
            prod_txt = self.cb_prod_avulso.get(); qtd = int(self.ent_qtd_avulso.get()); pid = int(prod_txt.split(' - ')[0])
            conn = sqlite3.connect(DB_NAME); res = conn.cursor().execute("SELECT nome, preco, estoque FROM produtos WHERE id=?", (pid,)).fetchone(); conn.close()
            if res[2] < qtd: messagebox.showerror("Erro", "Sem estoque!"); return
            self.carrinho_avulso.append({'id': pid, 'nome': res[0], 'qtd': qtd, 'tot': res[1] * qtd}); self.atualizar_avulso()
        except: pass

    def atualizar_avulso(self):
        self.tree_avulso.delete(*self.tree_avulso.get_children()); geral = 0
        for i in self.carrinho_avulso: self.tree_avulso.insert('', 'end', values=(i['nome'], i['qtd'], f"{i['tot']:.2f}")); geral += i['tot']
        self.lbl_total_avulso.config(text=f"TOTAL: R$ {geral:.2f}")

    def limpar_avulso(self): 
        self.carrinho_avulso = []; self.atualizar_avulso()

    def finalizar_avulso(self):
        if not self.carrinho_avulso: return
        total_venda = sum(item['tot'] for item in self.carrinho_avulso)
        forma_pgto = self.cb_pag_avulso.get()

        def efetivar_venda_balcao():
            conn = sqlite3.connect(DB_NAME); c = conn.cursor(); dt = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            try:
                for item in self.carrinho_avulso:
                    codigo_prod = c.execute("SELECT codigo FROM produtos WHERE id=?", (item['id'],)).fetchone()[0]
                    from sistema import database
                    database.processar_baixa_estoque_vinculado(c, codigo_prod, item['qtd'])
                    # Salva na tabela dedicada de vendas avulsas
                    c.execute("INSERT INTO vendas_balcao (produto_nome, qtd, total, data_hora, pagamento) VALUES (?,?,?,?,?)", (item['nome'], item['qtd'], item['tot'], dt, forma_pgto))
                    c.execute("UPDATE produtos SET estoque = estoque - ? WHERE id=?", (item['qtd'], item['id']))
                conn.commit(); messagebox.showinfo("Sucesso", "Venda Balcão Concluída!")
            except ValueError as e: conn.rollback(); messagebox.showerror("Erro", str(e))
            finally:
                conn.close(); self.limpar_avulso(); self.app.atualizar_todos_produtos(); self.app.aba_caixa.carregar_historico()

        if forma_pgto == "DINHEIRO":
            # Abre pop-up simplificado de troco direto
            if messagebox.askyesno("Dinheiro", f"Confirmar recebimento de R$ {total_venda:.2f} em espécie?"): efetivar_venda_balcao()
        else:
            if messagebox.askyesno("Confirmar", f"Finalizar venda no {forma_pgto}?"): efetivar_venda_balcao()

    def finalizar_cortesia(self):
        if not self.carrinho_avulso: return
        janela_nome = tk.Toplevel(self); janela_nome.title("Nome"); janela_nome.geometry("350x180"); janela_nome.configure(bg=CORES['painel'])
        tk.Label(janela_nome, text="Nome do Funcionário:", bg=CORES['painel'], fg='white').pack(pady=10)
        ent_nome_func = tk.Entry(janela_nome, font=('Arial', 11), width=25, justify='center'); ent_nome_func.pack()

        def confirmar_gravacao_cortesia():
            nome_recebedor = ent_nome_func.get().strip().upper()
            if not nome_recebedor: return
            conn = sqlite3.connect(DB_NAME); c = conn.cursor(); dt = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            try:
                for item in self.carrinho_avulso:
                    codigo_prod = c.execute("SELECT codigo FROM produtos WHERE id=?", (item['id'],)).fetchone()[0]
                    from sistema import database
                    database.processar_baixa_estoque_vinculado(c, codigo_prod, item['qtd'])
                    
                    c.execute("INSERT INTO vendas_balcao (produto_nome, qtd, total, data_hora, pagamento) VALUES (?,?,?,?,?)", (f"[CORTESIA] {item['nome']}", item['qtd'], 0.00, dt, f"CORTESIA ({nome_recebedor})"))
                    c.execute("UPDATE produtos SET estoque = estoque - ? WHERE id=?", (item['qtd'], item['id']))
                conn.commit(); janela_nome.destroy(); messagebox.showinfo("Sucesso", "Registrado!")
            except ValueError as e: conn.rollback(); messagebox.showerror("Erro", str(e))
            finally: conn.close(); self.limpar_avulso(); self.app.atualizar_todos_produtos(); self.app.aba_caixa.carregar_historico()

        tk.Button(janela_nome, text="LIBERAR", bg=CORES['verde'], fg='white', command=confirmar_gravacao_cortesia).pack(pady=15)
        janela_nome.update(); janela_nome.grab_set()