# aba_estoque.py
import tkinter as tk
from tkinter import ttk, messagebox
import sqlite3
from sistema.config import CORES, DB_NAME

class AbaEstoque(tk.Frame):
    def __init__(self, parent, app_principal):
        super().__init__(parent, bg=CORES['fundo'])
        self.app = app_principal
        self.id_produto_selecionado = None
        self.montar_interface()

    def montar_interface(self):
        # 1. BARRA DE PESQUISA
        fr_busca = tk.Frame(self, bg=CORES['painel'], pady=10); fr_busca.pack(fill='x')
        tk.Label(fr_busca, text="🔍 BUSCAR / BIPAR:", bg=CORES['painel'], fg=CORES['amarelo'], font=('Arial', 12, 'bold')).pack(side='left', padx=10)
        self.ent_busca_estoque = tk.Entry(fr_busca, width=40, font=('Arial', 12), bg=CORES['busca'], fg='white')
        self.ent_busca_estoque.pack(side='left', padx=5)
        self.ent_busca_estoque.bind("<KeyRelease>", self.filtrar_estoque_digitacao)
        tk.Button(fr_busca, text="LIMPAR", command=self.limpar_busca_estoque).pack(side='left', padx=5)

        # 2. FORMULÁRIO DE CADASTRO
        fr_form = tk.Frame(self, bg=CORES['painel'], pady=10); fr_form.pack(fill='x', pady=5)
        fr_l1 = tk.Frame(fr_form, bg=CORES['painel']); fr_l1.pack(pady=2)
        tk.Label(fr_l1, text="Cód. Barras:", bg=CORES['painel'], fg='white').pack(side='left')
        self.ent_cod = tk.Entry(fr_l1, width=15, bg='#505050', fg='white'); self.ent_cod.pack(side='left', padx=5)
        tk.Label(fr_l1, text="Nome:", bg=CORES['painel'], fg='white').pack(side='left')
        self.ent_nome = tk.Entry(fr_l1, width=30); self.ent_nome.pack(side='left', padx=5)
        
        fr_l2 = tk.Frame(fr_form, bg=CORES['painel']); fr_l2.pack(pady=5)
        tk.Label(fr_l2, text="Preço R$:", bg=CORES['painel'], fg='white').pack(side='left')
        self.ent_preco = tk.Entry(fr_l2, width=10); self.ent_preco.pack(side='left', padx=5)
        tk.Label(fr_l2, text="Estoque:", bg=CORES['painel'], fg='white').pack(side='left')
        self.ent_est = tk.Entry(fr_l2, width=10); self.ent_est.pack(side='left', padx=5)
        
        fr_btns = tk.Frame(fr_form, bg=CORES['painel']); fr_btns.pack(pady=5)
        tk.Button(fr_btns, text="SALVAR NOVO", bg=CORES['azul'], fg='white', command=self.salvar_produto).pack(side='left', padx=10)
        tk.Button(fr_btns, text="ATUALIZAR", bg=CORES['laranja'], fg='white', command=self.atualizar_produto).pack(side='left', padx=5)
        tk.Button(fr_btns, text="EXCLUIR", bg=CORES['vermelho'], fg='white', command=self.excluir_produto).pack(side='left', padx=10)
        tk.Button(fr_btns, text="Limpar Campos", command=self.limpar_campos_estoque).pack(side='left', padx=5)

        # 3. TABELA
        self.tree_est = ttk.Treeview(self, columns=('ID','Cod','Nome','Preço','Estoque'), show='headings')
        self.tree_est.heading('ID', text='ID'); self.tree_est.column('ID', width=40)
        self.tree_est.heading('Cod', text='Cód. Barras'); self.tree_est.column('Cod', width=100)
        self.tree_est.heading('Nome', text='Produto'); self.tree_est.column('Nome', width=250)
        self.tree_est.heading('Preço', text='Preço'); self.tree_est.column('Preço', width=80)
        self.tree_est.heading('Estoque', text='Estoque'); self.tree_est.column('Estoque', width=80)
        self.tree_est.tag_configure('baixo', background=CORES['vermelho'], foreground='white')
        self.tree_est.bind("<<TreeviewSelect>>", self.ao_clicar_tabela)
        
        sb = ttk.Scrollbar(self, orient="vertical", command=self.tree_est.yview)
        self.tree_est.configure(yscroll=sb.set)
        sb.pack(side='right', fill='y')
        self.tree_est.pack(fill='both', expand=True, padx=10, pady=5)

    def atualizar_tabela(self, lista_itens):
        self.tree_est.delete(*self.tree_est.get_children())
        for i in lista_itens:
            tag = 'baixo' if i[3] < 5 else ''
            cod_show = i[4] if i[4] else "" 
            self.tree_est.insert('', 'end', values=(i[0], cod_show, i[1], f"{i[2]:.2f}", i[3]), tags=(tag,))

    def filtrar_estoque_digitacao(self, event):
        termo = self.ent_busca_estoque.get().lower()
        if not termo:
            self.atualizar_tabela(self.app.lista_produtos_cache)
            return
        
        filtrados = []
        for item in self.app.lista_produtos_cache:
            nome = str(item[1]).lower()
            codigo = str(item[4]).lower() if item[4] else ""
            if termo in nome or termo == codigo:
                filtrados.append(item)
        self.atualizar_tabela(filtrados)

    def limpar_busca_estoque(self):
        self.ent_busca_estoque.delete(0, 'end')
        self.atualizar_tabela(self.app.lista_produtos_cache)

    def ao_clicar_tabela(self, event):
        sel = self.tree_est.selection()
        if sel:
            item = self.tree_est.item(sel[0])['values']
            self.id_produto_selecionado = item[0]
            self.ent_cod.delete(0, 'end'); self.ent_cod.insert(0, item[1])
            self.ent_nome.delete(0,'end'); self.ent_nome.insert(0,item[2])
            preco_limpo = str(item[3]).replace('R$ ', '').replace(',','.')
            self.ent_preco.delete(0,'end'); self.ent_preco.insert(0, preco_limpo)
            self.ent_est.delete(0,'end'); self.ent_est.insert(0,item[4])

    def limpar_campos_estoque(self): 
        self.id_produto_selecionado = None
        self.ent_cod.delete(0, 'end'); self.ent_nome.delete(0,'end')
        self.ent_preco.delete(0,'end'); self.ent_est.delete(0,'end')
    
    def salvar_produto(self):
        try:
            n = self.ent_nome.get()
            p = float(self.ent_preco.get().replace(',','.'))
            e = int(self.ent_est.get())
            cod = self.ent_cod.get()
            if not n: return
            
            conn = sqlite3.connect(DB_NAME)
            conn.cursor().execute("INSERT INTO produtos (nome,preco,estoque,codigo) VALUES (?,?,?,?)",(n,p,e,cod))
            conn.commit(); conn.close()
            
            self.limpar_campos_estoque()
            self.app.atualizar_todos_produtos()
            messagebox.showinfo("OK","Salvo!")
        except: messagebox.showerror("Erro","Dados inválidos")

    def atualizar_produto(self):
        if not self.id_produto_selecionado: return
        try:
            n = self.ent_nome.get(); p = float(self.ent_preco.get().replace(',','.')); e = int(self.ent_est.get()); cod = self.ent_cod.get()
            conn = sqlite3.connect(DB_NAME)
            conn.cursor().execute("UPDATE produtos SET nome=?,preco=?,estoque=?,codigo=? WHERE id=?",(n,p,e,cod,self.id_produto_selecionado))
            conn.commit(); conn.close()
            
            self.limpar_campos_estoque()
            self.app.atualizar_todos_produtos()
            self.limpar_busca_estoque()
            messagebox.showinfo("OK","Atualizado!")
        except: messagebox.showerror("Erro","Erro ao atualizar")

    def excluir_produto(self):
        if self.id_produto_selecionado and messagebox.askyesno("Excluir","Apagar produto?"):
            conn = sqlite3.connect(DB_NAME); conn.cursor().execute("DELETE FROM produtos WHERE id=?",(self.id_produto_selecionado,)); conn.commit(); conn.close()
            self.limpar_campos_estoque()
            self.app.atualizar_todos_produtos()