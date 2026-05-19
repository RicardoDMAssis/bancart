import tkinter as tk
from tkinter import ttk, messagebox
import sqlite3
from datetime import datetime
import shutil
import os

# --- CORES ---
CORES = {
    'fundo': '#2e2e2e',
    'painel': '#3e3e3e',
    'texto': '#ffffff',
    'verde': '#2ecc71',
    'vermelho': '#e74c3c',
    'azul': '#3498db',
    'laranja': '#e67e22',
    'amarelo': '#f1c40f',
    'busca': '#505050'
}

DB_NAME = "bancart_dados.db"

# --- BANCO DE DADOS (COM MIGRAÇÃO AUTOMÁTICA) ---
def iniciar_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    
    # Cria tabelas básicas
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
    
    # VERIFICA SE A COLUNA 'CODIGO' EXISTE (Para quem já tem o banco antigo)
    try:
        c.execute("SELECT codigo FROM produtos LIMIT 1")
    except sqlite3.OperationalError:
        # Se der erro, é porque a coluna não existe. Vamos criar.
        c.execute("ALTER TABLE produtos ADD COLUMN codigo TEXT")
        print("Coluna 'codigo' adicionada com sucesso!")
        
    conn.commit(); conn.close()

def fazer_backup():
    if os.path.exists(DB_NAME):
        if not os.path.exists("backups"): os.mkdir("backups")
        data = datetime.now().strftime("%Y-%m-%d")
        shutil.copy(DB_NAME, f"backups/backup_{data}.db")

# --- SISTEMA ---
class BancartApp:
    def __init__(self, root):
        self.root = root
        self.root.title("BANCART PRO 5.0 - Gestão Inteligente")
        self.root.geometry("1100x700")
        self.root.configure(bg=CORES['fundo'])
        
        style = ttk.Style()
        style.theme_use('clam')
        style.configure("TFrame", background=CORES['fundo'])
        style.configure("TLabel", background=CORES['fundo'], foreground=CORES['texto'], font=('Arial', 11))
        style.configure("Treeview", background="#404040", foreground="white", fieldbackground="#404040", rowheight=25)
        style.map("Treeview", background=[('selected', CORES['azul'])])

        self.carrinho_avulso = [] 
        self.mesa_atual = None
        self.id_produto_selecionado = None
        self.lista_produtos_cache = [] # Cache para busca rápida

        self.abas = ttk.Notebook(root)
        self.abas.pack(fill='both', expand=True, padx=5, pady=5)

        self.aba_mesas = tk.Frame(self.abas, bg=CORES['fundo']); self.abas.add(self.aba_mesas, text=" 🍽️  MESAS ")
        self.aba_avulsa = tk.Frame(self.abas, bg=CORES['fundo']); self.abas.add(self.aba_avulsa, text=" 🛒  BALCÃO ")
        self.aba_estoque = tk.Frame(self.abas, bg=CORES['fundo']); self.abas.add(self.aba_estoque, text=" 📦  ESTOQUE ")
        self.aba_historico = tk.Frame(self.abas, bg=CORES['fundo']); self.abas.add(self.aba_historico, text=" 📅  CAIXA ")

        self.montar_aba_mesas()
        self.montar_aba_avulsa()
        self.montar_aba_estoque()
        self.montar_aba_historico()

    # --- ABA MESAS ---
    def montar_aba_mesas(self):
        fr_btn = tk.Frame(self.aba_mesas, bg=CORES['painel'], bd=2, relief='groove')
        fr_btn.place(relx=0.01, rely=0.02, relwidth=0.48, relheight=0.96)
        tk.Label(fr_btn, text="MAPA DE MESAS", bg=CORES['painel'], fg='white', font=('Arial', 12, 'bold')).pack(pady=10)
        
        fr_grid = tk.Frame(fr_btn, bg=CORES['painel']); fr_grid.pack()
        self.btns_mesa = {}
        for i in range(1, 21):
            btn = tk.Button(fr_grid, text=f"MESA {i:02d}", width=9, height=3, bg=CORES['verde'], fg='white', font=('Arial', 9, 'bold'), command=lambda m=i: self.selecionar_mesa(m))
            r, c = divmod(i-1, 4)
            btn.grid(row=r, column=c, padx=5, pady=5)
            self.btns_mesa[i] = btn
        
        fr_det = tk.Frame(self.aba_mesas, bg=CORES['fundo'])
        fr_det.place(relx=0.5, rely=0.02, relwidth=0.49, relheight=0.96)
        self.lbl_mesa_sel = tk.Label(fr_det, text="Selecione uma Mesa", font=('Arial', 16, 'bold'), fg=CORES['amarelo'], bg=CORES['fundo']); self.lbl_mesa_sel.pack(pady=5)
        
        self.tree_mesa = ttk.Treeview(fr_det, columns=('id','Item','Qtd','Total'), show='headings', height=10)
        self.tree_mesa.heading('id', text='ID'); self.tree_mesa.column('id', width=30)
        self.tree_mesa.heading('Item', text='Produto'); self.tree_mesa.column('Item', width=200)
        self.tree_mesa.heading('Qtd', text='Qtd'); self.tree_mesa.column('Qtd', width=50)
        self.tree_mesa.heading('Total', text='R$'); self.tree_mesa.column('Total', width=80)
        self.tree_mesa.pack(fill='x')

        fr_add = tk.Frame(fr_det, bg=CORES['painel'], pady=5); fr_add.pack(fill='x', pady=5)
        self.cb_prod_mesa = ttk.Combobox(fr_add, width=22); self.cb_prod_mesa.pack(side='left', padx=5)
        self.ent_qtd_mesa = tk.Entry(fr_add, width=5); self.ent_qtd_mesa.insert(0,"1"); self.ent_qtd_mesa.pack(side='left', padx=5)
        tk.Button(fr_add, text="ADD", bg=CORES['azul'], fg='white', command=self.add_item_mesa).pack(side='left')

        self.lbl_total_mesa = tk.Label(fr_det, text="TOTAL: R$ 0.00", font=('Arial', 18, 'bold'), fg=CORES['verde'], bg=CORES['fundo']); self.lbl_total_mesa.pack(pady=10)
        tk.Label(fr_det, text="Pagamento:", bg=CORES['fundo'], fg='white').pack()
        self.cb_pag_mesa = ttk.Combobox(fr_det, values=["DINHEIRO", "PIX", "CRÉDITO", "DÉBITO"]); self.cb_pag_mesa.current(0); self.cb_pag_mesa.pack(pady=2)
        tk.Button(fr_det, text="FECHAR MESA", bg=CORES['vermelho'], fg='white', font=('Arial', 12, 'bold'), width=25, command=self.fechar_mesa).pack(pady=10)
        self.atualizar_cores_mesas()

    # --- ABA BALCÃO ---
    def montar_aba_avulsa(self):
        fr_topo = tk.Frame(self.aba_avulsa, bg=CORES['painel'], pady=10); fr_topo.pack(fill='x')
        tk.Label(fr_topo, text="BALCÃO RÁPIDO", font=('Arial', 18, 'bold'), fg=CORES['laranja'], bg=CORES['painel']).pack()
        fr_inp = tk.Frame(fr_topo, bg=CORES['painel']); fr_inp.pack(pady=5)
        self.cb_prod_avulso = ttk.Combobox(fr_inp, width=30, font=('Arial', 12)); self.cb_prod_avulso.pack(side='left', padx=5)
        self.ent_qtd_avulso = tk.Entry(fr_inp, width=5, font=('Arial', 12)); self.ent_qtd_avulso.insert(0,"1"); self.ent_qtd_avulso.pack(side='left', padx=5)
        tk.Button(fr_inp, text="LANÇAR", bg=CORES['azul'], fg='white', command=self.add_carrinho_avulso).pack(side='left', padx=10)
        self.tree_avulso = ttk.Treeview(self.aba_avulsa, columns=('Prod','Qtd','Total'), show='headings', height=10)
        self.tree_avulso.heading('Prod', text='Produto'); self.tree_avulso.heading('Qtd', text='Qtd'); self.tree_avulso.heading('Total', text='Total')
        self.tree_avulso.pack(fill='both', expand=True, padx=10, pady=5)
        tk.Button(self.aba_avulsa, text="Limpar", command=self.limpar_avulso).pack()
        fr_base = tk.Frame(self.aba_avulsa, bg=CORES['painel'], pady=10); fr_base.pack(fill='x', padx=10, pady=10)
        self.lbl_total_avulso = tk.Label(fr_base, text="TOTAL: R$ 0.00", font=('Arial', 24), fg=CORES['verde'], bg=CORES['painel']); self.lbl_total_avulso.pack(side='left', padx=20)
        fr_pag = tk.Frame(fr_base, bg=CORES['painel']); fr_pag.pack(side='right', padx=20)
        self.cb_pag_avulso = ttk.Combobox(fr_pag, values=["DINHEIRO", "PIX", "CRÉDITO", "DÉBITO"]); self.cb_pag_avulso.current(0); self.cb_pag_avulso.pack()
        tk.Button(fr_pag, text="FINALIZAR", bg=CORES['verde'], fg='white', font=('Arial', 14), command=self.finalizar_avulso).pack(pady=5)

    # --- ABA ESTOQUE (ATUALIZADA) ---
    def montar_aba_estoque(self):
        # 1. BARRA DE PESQUISA INTELIGENTE
        fr_busca = tk.Frame(self.aba_estoque, bg=CORES['painel'], pady=10)
        fr_busca.pack(fill='x')
        tk.Label(fr_busca, text="🔍 BUSCAR / BIPAR:", bg=CORES['painel'], fg=CORES['amarelo'], font=('Arial', 12, 'bold')).pack(side='left', padx=10)
        self.ent_busca_estoque = tk.Entry(fr_busca, width=40, font=('Arial', 12), bg=CORES['busca'], fg='white')
        self.ent_busca_estoque.pack(side='left', padx=5)
        self.ent_busca_estoque.bind("<KeyRelease>", self.filtrar_estoque_digitacao) # Busca enquanto digita
        tk.Button(fr_busca, text="LIMPAR", command=self.limpar_busca_estoque).pack(side='left', padx=5)

        # 2. FORMULÁRIO DE CADASTRO (COM CÓDIGO)
        fr_form = tk.Frame(self.aba_estoque, bg=CORES['painel'], pady=10); fr_form.pack(fill='x', pady=5)
        
        # Linha 1 do form
        fr_l1 = tk.Frame(fr_form, bg=CORES['painel']); fr_l1.pack(pady=2)
        tk.Label(fr_l1, text="Cód. Barras:", bg=CORES['painel'], fg='white').pack(side='left')
        self.ent_cod = tk.Entry(fr_l1, width=15, bg='#505050', fg='white'); self.ent_cod.pack(side='left', padx=5)
        tk.Label(fr_l1, text="Nome:", bg=CORES['painel'], fg='white').pack(side='left')
        self.ent_nome = tk.Entry(fr_l1, width=30); self.ent_nome.pack(side='left', padx=5)
        
        # Linha 2 do form
        fr_l2 = tk.Frame(fr_form, bg=CORES['painel']); fr_l2.pack(pady=5)
        tk.Label(fr_l2, text="Preço R$:", bg=CORES['painel'], fg='white').pack(side='left')
        self.ent_preco = tk.Entry(fr_l2, width=10); self.ent_preco.pack(side='left', padx=5)
        tk.Label(fr_l2, text="Estoque:", bg=CORES['painel'], fg='white').pack(side='left')
        self.ent_est = tk.Entry(fr_l2, width=10); self.ent_est.pack(side='left', padx=5)
        
        # Botões
        fr_btns = tk.Frame(fr_form, bg=CORES['painel']); fr_btns.pack(pady=5)
        tk.Button(fr_btns, text="SALVAR NOVO", bg=CORES['azul'], fg='white', command=self.salvar_produto).pack(side='left', padx=10)
        tk.Button(fr_btns, text="ATUALIZAR", bg=CORES['laranja'], fg='white', command=self.atualizar_produto).pack(side='left', padx=5)
        tk.Button(fr_btns, text="EXCLUIR", bg=CORES['vermelho'], fg='white', command=self.excluir_produto).pack(side='left', padx=10)
        tk.Button(fr_btns, text="Limpar Campos", command=self.limpar_campos_estoque).pack(side='left', padx=5)

        # 3. TABELA
        self.tree_est = ttk.Treeview(self.aba_estoque, columns=('ID','Cod','Nome','Preço','Estoque'), show='headings')
        self.tree_est.heading('ID', text='ID'); self.tree_est.column('ID', width=40)
        self.tree_est.heading('Cod', text='Cód. Barras'); self.tree_est.column('Cod', width=100)
        self.tree_est.heading('Nome', text='Produto'); self.tree_est.column('Nome', width=250)
        self.tree_est.heading('Preço', text='Preço'); self.tree_est.column('Preço', width=80)
        self.tree_est.heading('Estoque', text='Estoque'); self.tree_est.column('Estoque', width=80)
        
        self.tree_est.tag_configure('baixo', background=CORES['vermelho'], foreground='white')
        self.tree_est.bind("<<TreeviewSelect>>", self.ao_clicar_tabela)
        
        # Scrollbar
        sb = ttk.Scrollbar(self.aba_estoque, orient="vertical", command=self.tree_est.yview)
        self.tree_est.configure(yscroll=sb.set)
        sb.pack(side='right', fill='y')
        self.tree_est.pack(fill='both', expand=True, padx=10, pady=5)

    def montar_aba_historico(self):
        tk.Label(self.aba_historico, text="Vendas Hoje", font=('Arial', 14), bg=CORES['fundo'], fg=CORES['texto']).pack(pady=5)
        self.tree_hist = ttk.Treeview(self.aba_historico, columns=('Hora','Tipo','Prod','Total','Pgto'), show='headings')
        self.tree_hist.heading('Hora', text='Hora'); self.tree_hist.column('Hora', width=80)
        self.tree_hist.heading('Tipo', text='Origem'); self.tree_hist.column('Tipo', width=100)
        self.tree_hist.heading('Prod', text='Produto'); self.tree_hist.column('Prod', width=200)
        self.tree_hist.heading('Total', text='Total'); self.tree_hist.column('Total', width=80)
        self.tree_hist.heading('Pgto', text='Pgto'); self.tree_hist.column('Pgto', width=100)
        self.tree_hist.pack(fill='both', expand=True, padx=10, pady=5)
        self.lbl_fat = tk.Label(self.aba_historico, text="Total: R$ 0.00", font=('Arial', 16, 'bold'), fg=CORES['verde'], bg=CORES['fundo']); self.lbl_fat.pack(pady=10)
        
        fr_botoes = tk.Frame(self.aba_historico, bg=CORES['fundo'])
        fr_botoes.pack()
        tk.Button(fr_botoes, text="Atualizar Lista", command=self.carregar_historico).pack(side='left', padx=10)
        tk.Button(fr_botoes, text="📄 SALVAR RELATÓRIO DO DIA", bg=CORES['azul'], fg='white', font=('Arial', 10, 'bold'), command=self.salvar_relatorio_txt).pack(side='left', padx=10)

    # --- FUNÇÕES ---
    def carregar_produtos(self):
        conn=sqlite3.connect(DB_NAME); c=conn.cursor()
        # Carrega codigo também
        itens=c.execute("SELECT id, nome, preco, estoque, codigo FROM produtos").fetchall()
        conn.close()
        
        self.lista_produtos_cache = itens # Salva na memória para busca rápida
        self.atualizar_tabela_estoque(itens)
        
        # Atualiza comboboxes
        lista_cb = [f"{i[0]} - {i[1]} | R$ {i[2]:.2f}" for i in itens]
        self.cb_prod_mesa['values'] = lista_cb
        self.cb_prod_avulso['values'] = lista_cb

    def atualizar_tabela_estoque(self, lista_itens):
        self.tree_est.delete(*self.tree_est.get_children())
        for i in lista_itens:
            # i = (id, nome, preco, estoque, codigo)
            tag = 'baixo' if i[3] < 5 else ''
            # Tratamento caso codigo seja None
            cod_show = i[4] if i[4] else "" 
            self.tree_est.insert('', 'end', values=(i[0], cod_show, i[1], f"{i[2]:.2f}", i[3]), tags=(tag,))

    def filtrar_estoque_digitacao(self, event):
        termo = self.ent_busca_estoque.get().lower()
        if not termo:
            self.atualizar_tabela_estoque(self.lista_produtos_cache)
            return
        
        filtrados = []
        for item in self.lista_produtos_cache:
            # item[1] é nome, item[4] é código
            nome = str(item[1]).lower()
            codigo = str(item[4]).lower() if item[4] else ""
            
            # Se o termo estiver no nome OU for igual ao código
            if termo in nome or termo == codigo:
                filtrados.append(item)
        
        self.atualizar_tabela_estoque(filtrados)

    def limpar_busca_estoque(self):
        self.ent_busca_estoque.delete(0, 'end')
        self.atualizar_tabela_estoque(self.lista_produtos_cache)

    def ao_clicar_tabela(self, event):
        sel=self.tree_est.selection()
        if sel:
            # Pega valores da linha clicada
            item=self.tree_est.item(sel[0])['values']
            self.id_produto_selecionado=item[0]
            
            # Preenche campos
            self.ent_cod.delete(0, 'end'); self.ent_cod.insert(0, item[1]) # Codigo
            self.ent_nome.delete(0,'end'); self.ent_nome.insert(0,item[2]) # Nome
            
            # Limpa R$ do preço
            preco_limpo = str(item[3]).replace('R$ ', '').replace(',','.')
            self.ent_preco.delete(0,'end'); self.ent_preco.insert(0, preco_limpo)
            
            self.ent_est.delete(0,'end'); self.ent_est.insert(0,item[4]) # Estoque

    def limpar_campos_estoque(self): 
        self.id_produto_selecionado=None
        self.ent_cod.delete(0, 'end')
        self.ent_nome.delete(0,'end')
        self.ent_preco.delete(0,'end')
        self.ent_est.delete(0,'end')
    
    def salvar_produto(self):
        try:
            n=self.ent_nome.get()
            p=float(self.ent_preco.get().replace(',','.'))
            e=int(self.ent_est.get())
            cod=self.ent_cod.get() # Pega o código
            
            if not n: return
            
            conn=sqlite3.connect(DB_NAME)
            conn.cursor().execute("INSERT INTO produtos (nome,preco,estoque,codigo) VALUES (?,?,?,?)",(n,p,e,cod))
            conn.commit(); conn.close()
            
            self.limpar_campos_estoque()
            self.carregar_produtos()
            messagebox.showinfo("OK","Salvo!")
        except: messagebox.showerror("Erro","Dados inválidos")

    def atualizar_produto(self):
        if not self.id_produto_selecionado: return
        try:
            n=self.ent_nome.get()
            p=float(self.ent_preco.get().replace(',','.'))
            e=int(self.ent_est.get())
            cod=self.ent_cod.get()
            
            conn=sqlite3.connect(DB_NAME)
            conn.cursor().execute("UPDATE produtos SET nome=?,preco=?,estoque=?,codigo=? WHERE id=?",(n,p,e,cod,self.id_produto_selecionado))
            conn.commit(); conn.close()
            
            self.limpar_campos_estoque()
            self.carregar_produtos()
            self.limpar_busca_estoque() # Limpa a busca para ver a alteração
            messagebox.showinfo("OK","Atualizado!")
        except: messagebox.showerror("Erro","Erro ao atualizar")

    def excluir_produto(self):
        if self.id_produto_selecionado and messagebox.askyesno("Excluir","Apagar produto?"):
            conn=sqlite3.connect(DB_NAME); conn.cursor().execute("DELETE FROM produtos WHERE id=?",(self.id_produto_selecionado,)); conn.commit(); conn.close()
            self.limpar_campos_estoque(); self.carregar_produtos()

    def selecionar_mesa(self, m):
        self.mesa_atual=m; self.lbl_mesa_sel.config(text=f"MESA {m:02d} - EM ABERTO"); self.carregar_mesa()

    def add_item_mesa(self):
        if not self.mesa_atual: messagebox.showwarning("!","Selecione uma mesa"); return
        try:
            prod=self.cb_prod_mesa.get(); qtd=int(self.ent_qtd_mesa.get()); pid=int(prod.split(' - ')[0])
            conn=sqlite3.connect(DB_NAME); res=conn.cursor().execute("SELECT nome,preco,estoque FROM produtos WHERE id=?",(pid,)).fetchone()
            if res[2]<qtd: messagebox.showerror("Erro","Sem estoque"); conn.close(); return
            total=res[1]*qtd; dt=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            conn.cursor().execute("INSERT INTO vendas (mesa_id,produto_nome,qtd,total,data_hora,status) VALUES (?,?,?,?,?,?)",(self.mesa_atual,res[0],qtd,total,dt,'ABERTA'))
            conn.cursor().execute("UPDATE produtos SET estoque=estoque-? WHERE id=?",(qtd,pid))
            conn.commit(); conn.close(); self.carregar_mesa(); self.carregar_produtos(); self.atualizar_cores_mesas()
        except: pass

    def carregar_mesa(self):
        self.tree_mesa.delete(*self.tree_mesa.get_children()); total=0
        conn=sqlite3.connect(DB_NAME); itens=conn.cursor().execute("SELECT id,produto_nome,qtd,total FROM vendas WHERE mesa_id=? AND status='ABERTA'",(self.mesa_atual,)).fetchall(); conn.close()
        for i in itens: self.tree_mesa.insert('','end',values=i); total+=i[3]
        self.lbl_total_mesa.config(text=f"TOTAL: R$ {total:.2f}")

    def fechar_mesa(self):
        if not self.mesa_atual or not self.tree_mesa.get_children(): return
        if messagebox.askyesno("Fechar", f"Fechar conta da Mesa {self.mesa_atual}?"):
            conn=sqlite3.connect(DB_NAME)
            conn.cursor().execute("UPDATE vendas SET status='FECHADA', pagamento=? WHERE mesa_id=? AND status='ABERTA'", (self.cb_pag_mesa.get(), self.mesa_atual))
            conn.commit(); conn.close()
            self.carregar_mesa(); self.atualizar_cores_mesas(); self.carregar_historico()
            messagebox.showinfo("Sucesso", "Mesa fechada!")

    def atualizar_cores_mesas(self):
        conn = sqlite3.connect(DB_NAME); ocupadas = [x[0] for x in conn.cursor().execute("SELECT DISTINCT mesa_id FROM vendas WHERE status='ABERTA'").fetchall()]; conn.close()
        for i in range(1, 21): self.btns_mesa[i].config(bg=CORES['vermelho'] if i in ocupadas else CORES['verde'])

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

    def limpar_avulso(self): self.carrinho_avulso = []; self.atualizar_avulso()

    def finalizar_avulso(self):
        if not self.carrinho_avulso: return
        if messagebox.askyesno("Confirmar", "Finalizar venda?"):
            conn = sqlite3.connect(DB_NAME); c = conn.cursor(); dt = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            for item in self.carrinho_avulso:
                c.execute("INSERT INTO vendas (mesa_id, produto_nome, qtd, total, data_hora, pagamento, status) VALUES (?,?,?,?,?,?,?)", (0, item['nome'], item['qtd'], item['tot'], dt, self.cb_pag_avulso.get(), 'FECHADA'))
                c.execute("UPDATE produtos SET estoque = estoque - ? WHERE id=?", (item['qtd'], item['id']))
            conn.commit(); conn.close(); self.limpar_avulso(); self.carregar_produtos(); self.carregar_historico(); messagebox.showinfo("Sucesso", "Venda OK!")

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
                messagebox.showinfo("Vazio", "Nenhuma venda hoje para salvar.")
                return

            total_dia = 0
            with open(nome_arq, "w", encoding='utf-8') as f:
                f.write(f"=== RELATORIO DE VENDAS: {dt_hoje} ===\n\n")
                f.write(f"{'HORA':<10} {'ORIGEM':<10} {'PRODUTO':<20} {'QTD':<5} {'TOTAL':<10} {'PAGAMENTO'}\n")
                f.write("-" * 80 + "\n")
                
                for v in vendas:
                    hora = v[0].split(' ')[1]
                    origem = f"Mesa {v[1]}" if v[1] > 0 else "Balcão"
                    prod = v[2][:20]
                    f.write(f"{hora:<10} {origem:<10} {prod:<20} {v[3]:<5} R${v[4]:<8.2f} {v[5]}\n")
                    total_dia += v[4]
                
                f.write("-" * 80 + "\n")
                f.write(f"TOTAL DO DIA: R$ {total_dia:.2f}\n")
                f.write("=" * 80)
            
            messagebox.showinfo("Sucesso", f"Relatório salvo como:\n{nome_arq}")
            os.startfile(nome_arq)
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao salvar: {e}")

if __name__ == "__main__":
    iniciar_db(); fazer_backup(); root = tk.Tk(); app = BancartApp(root); app.carregar_produtos(); root.mainloop()
