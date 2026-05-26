# aba_estoque.py
import tkinter as tk
from tkinter import ttk, messagebox
import sqlite3
from sistema.config import CORES, DB_NAME
import csv
from tkinter import filedialog

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

        # Exemplo de inserção junto aos seus botões atuais (ajuste o frame conforme seu layout)
        self.btn_importar_csv = tk.Button(
            fr_btns, # Substitua pelo nome do seu frame de botões da aba estoque
            text="📥 IMPORTAR CSV", 
            bg=CORES['azul'], 
            fg='white', 
            font=('Arial', 10, 'bold'),
            command=self.importar_produtos_csv
        )
        self.btn_importar_csv.pack(side='left', padx=10, ipady=3)

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

    def importar_produtos_csv(self):
        # 1. Abre o gerenciador de arquivos do Linux/Windows filtrando apenas por arquivos .csv
        caminho_arquivo = filedialog.askopenfilename(
            title="Selecionar Lista de Produtos em CSV",
            filetypes=[("Arquivos CSV", "*.csv"), ("Todos os arquivos", "*.*")]
        )
        
        if not caminho_arquivo:
            return # Usuário cancelou a seleção

        try:
            conn = sqlite3.connect(DB_NAME)
            cursor = conn.cursor()
            
            produtos_inseridos = 0
            produtos_atualizados = 0
            
            # 2. Abre e lê o arquivo tratando codificação UTF-8 padrão
            with open(caminho_arquivo, mode='r', encoding='utf-8') as f:
                # Detecta automaticamente se o separador é vírgula (,) ou ponto-e-vírgula (;)
                conteudo_inicial = f.read(2048)
                separador = ';' if ';' in conteudo_inicial else ','
                f.seek(0) # Volta para o início do arquivo
                
                leitor_csv = csv.DictReader(f, delimiter=separador)
                
                # Validação rápida de cabeçalho
                campos_obrigatorios = ['codigo', 'nome', 'preco', 'estoque']
                if not all(campo in leitor_csv.fieldnames for campo in campos_obrigatorios):
                    messagebox.showerror("Erro de Formato", "O arquivo CSV deve conter exatamente as colunas:\ncodigo, nome, preco, estoque")
                    conn.close()
                    return

                for linha in leitor_csv:
                    # Limpa e valida os dados de cada linha
                    codigo = str(linha['codigo']).strip()
                    nome = str(linha['nome']).strip().upper()
                    
                    try:
                        preco = float(linha['preco'].replace(',', '.'))
                        estoque = int(linha['estoque'])
                    except ValueError:
                        # Pula linhas com valores quebrados ou inválidos (proteção de dados)
                        continue

                    if not nome or not codigo:
                        continue

                    # 3. Verifica se o produto com esse código já existe no banco de dados
                    produto_existente = cursor.execute("SELECT id FROM produtos WHERE codigo = ?", (codigo,)).fetchone()
                    
                    if produto_existente:
                        # Se já existe, apenas SOMA o novo estoque importado e atualiza o preço
                        cursor.execute(
                            "UPDATE produtos SET preco = ?, estoque = estoque + ? WHERE id = ?",
                            (preco, estoque, produto_existente[0])
                        )
                        produtos_atualizados += 1
                    else:
                        # Se for um produto novo, insere o registro do zero
                        cursor.execute(
                            "INSERT INTO produtos (codigo, nome, preco, estoque) VALUES (?, ?, ?, ?)",
                            (codigo, nome, preco, estoque)
                        )
                        produtos_inseridos += 1
            
            # Confirma todas as alterações no banco de uma só vez
            conn.commit()
            conn.close()
            
            # 4. Atualiza os componentesvisuais e avisa o operador
            self.salvar_produto() # Recarrega a tabela (Treeview) da AbaEstoque
            if hasattr(self.app, 'atualizar_todos_produtos'):
                self.app.atualizar_todos_produtos() # Atualiza os caches de busca das outras abas (balcão, mesas...)
                
            messagebox.showinfo("Importação Concluída", 
                                f"Operação realizada com sucesso!\n\n"
                                f"📦 Novos produtos cadastrados: {produtos_inseridos}\n"
                                f"🔄 Estoques/Preços atualizados: {produtos_atualizados}")
                                
        except Exception as e:
            messagebox.showerror("Erro Crítico", f"Falha ao processar o arquivo CSV:\n{e}")

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