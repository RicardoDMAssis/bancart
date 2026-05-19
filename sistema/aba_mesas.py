# aba_mesas.py
import tkinter as tk
from tkinter import ttk, messagebox
import sqlite3
from datetime import datetime
from sistema.config import CORES, DB_NAME

class AbaMesas(tk.Frame):
    def __init__(self, parent, app_principal):
        super().__init__(parent, bg=CORES['fundo'])
        self.app = app_principal  # Referência para acessar caches e recarregar outras abas
        self.mesa_atual = None
        self.montar_interface()
        
    def montar_interface(self):
        fr_btn = tk.Frame(self, bg=CORES['painel'], bd=2, relief='groove')
        fr_btn.place(relx=0.01, rely=0.02, relwidth=0.48, relheight=0.96)
        tk.Label(fr_btn, text="MAPA DE MESAS", bg=CORES['painel'], fg='white', font=('Arial', 12, 'bold')).pack(pady=10)
        
        fr_grid = tk.Frame(fr_btn, bg=CORES['painel'])
        fr_grid.pack()
        self.btns_mesa = {}
        for i in range(1, 21):
            btn = tk.Button(fr_grid, text=f"MESA {i:02d}", width=9, height=3, bg=CORES['verde'], fg='white', font=('Arial', 9, 'bold'), command=lambda m=i: self.selecionar_mesa(m))
            r, c = divmod(i-1, 4)
            btn.grid(row=r, column=c, padx=5, pady=5)
            self.btns_mesa[i] = btn
        
        fr_det = tk.Frame(self, bg=CORES['fundo'])
        fr_det.place(relx=0.5, rely=0.02, relwidth=0.49, relheight=0.96)
        self.lbl_mesa_sel = tk.Label(fr_det, text="Selecione uma Mesa", font=('Arial', 16, 'bold'), fg=CORES['amarelo'], bg=CORES['fundo'])
        self.lbl_mesa_sel.pack(pady=5)
        
        self.tree_mesa = ttk.Treeview(fr_det, columns=('id','Item','Qtd','Total'), show='headings', height=10)
        self.tree_mesa.heading('id', text='ID'); self.tree_mesa.column('id', width=30)
        self.tree_mesa.heading('Item', text='Produto'); self.tree_mesa.column('Item', width=200)
        self.tree_mesa.heading('Qtd', text='Qtd'); self.tree_mesa.column('Qtd', width=50)
        self.tree_mesa.heading('Total', text='R$'); self.tree_mesa.column('Total', width=80)
        self.tree_mesa.pack(fill='x')
        self.tree_mesa.bind("<Double-1>", self.ao_clicar_duplo_comanda)

        fr_add = tk.Frame(fr_det, bg=CORES['painel'], pady=5); fr_add.pack(fill='x', pady=5)
        self.cb_prod_mesa = ttk.Combobox(fr_add, width=22); self.cb_prod_mesa.pack(side='left', padx=5)
        self.ent_qtd_mesa = tk.Entry(fr_add, width=5); self.ent_qtd_mesa.insert(0,"1"); self.ent_qtd_mesa.pack(side='left', padx=5)
        tk.Button(fr_add, text="ADD", bg=CORES['azul'], fg='white', command=self.add_item_mesa).pack(side='left')

        self.lbl_total_mesa = tk.Label(fr_det, text="TOTAL: R$ 0.00", font=('Arial', 18, 'bold'), fg=CORES['verde'], bg=CORES['fundo'])
        self.lbl_total_mesa.pack(pady=10)
        tk.Label(fr_det, text="Pagamento:", bg=CORES['fundo'], fg='white').pack()
        self.cb_pag_mesa = ttk.Combobox(fr_det, values=["DINHEIRO", "PIX", "CRÉDITO", "DÉBITO"]); self.cb_pag_mesa.current(0); self.cb_pag_mesa.pack(pady=2)
        tk.Button(fr_det, text="FECHAR MESA", bg=CORES['vermelho'], fg='white', font=('Arial', 12, 'bold'), width=25, command=self.fechar_mesa).pack(pady=10)
        self.atualizar_cores_mesas()

    def atualizar_combobox(self, lista_cb):
        self.cb_prod_mesa['values'] = lista_cb

    def selecionar_mesa(self, m):
        self.mesa_atual = m
        self.lbl_mesa_sel.config(text=f"MESA {m:02d} - EM ABERTO")
        self.carregar_mesa()

    def add_item_mesa(self):
        if not self.mesa_atual: 
            messagebox.showwarning("!","Selecione uma mesa"); return
        try:
            prod = self.cb_prod_mesa.get()
            qtd = int(self.ent_qtd_mesa.get())
            pid = int(prod.split(' - ')[0])
            
            conn = sqlite3.connect(DB_NAME)
            res = conn.cursor().execute("SELECT nome,preco,estoque FROM produtos WHERE id=?",(pid,)).fetchone()
            if res[2] < qtd: 
                messagebox.showerror("Erro","Sem estoque"); conn.close(); return
                
            total = res[1] * qtd
            dt = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            conn.cursor().execute("INSERT INTO vendas (mesa_id,produto_nome,qtd,total,data_hora,status) VALUES (?,?,?,?,?,?)",(self.mesa_atual,res[0],qtd,total,dt,'ABERTA'))
            conn.cursor().execute("UPDATE produtos SET estoque=estoque-? WHERE id=?",(qtd,pid))
            conn.commit(); conn.close()
            
            self.carregar_mesa()
            self.app.atualizar_todos_produtos() 
            self.atualizar_cores_mesas()
        except Exception as e: 
            print(e)

    def carregar_mesa(self):
        self.tree_mesa.delete(*self.tree_mesa.get_children())
        total = 0
        conn = sqlite3.connect(DB_NAME)
        itens = conn.cursor().execute("SELECT id,produto_nome,qtd,total FROM vendas WHERE mesa_id=? AND status='ABERTA'",(self.mesa_atual,)).fetchall()
        conn.close()
        for i in itens: 
            self.tree_mesa.insert('','end',values=i)
            total += i[3]
        self.lbl_total_mesa.config(text=f"TOTAL: R$ {total:.2f}")

    def fechar_mesa(self):
        if not self.mesa_atual or not self.tree_mesa.get_children(): 
            return
            
        conn = sqlite3.connect(DB_NAME)
        total_atual = conn.cursor().execute(
            "SELECT SUM(total) FROM vendas WHERE mesa_id=? AND status='ABERTA'",
            (self.mesa_atual,)
        ).fetchone()[0]
        conn.close()
        
        if not total_atual:
            total_atual = 0.0

        self.abrir_janela_desconto(total_atual)

    def abrir_janela_desconto(self, total_original):
        janela_desc = tk.Toplevel(self)
        janela_desc.title(f"Desconto - Mesa {self.mesa_atual:02d}")
        janela_desc.geometry("350x250")
        janela_desc.configure(bg=CORES['painel'])
        janela_desc.resizable(False, False)

        # 1. Escopo de Função Interna
        def processar_fechamento():
            try:
                desconto = float(ent_desc.get().replace(',', '.'))
                if desconto < 0:
                    raise ValueError
                if desconto > total_original:
                    messagebox.showerror("Erro", "O desconto não pode ser maior que o total!", parent=janela_desc)
                    return
            except ValueError:
                messagebox.showerror("Erro", "Insira um valor de desconto válido.", parent=janela_desc)
                return

            total_final = total_original - desconto
            
            if messagebox.askyesno("Confirmar", f"Total com desconto: R$ {total_final:.2f}\nFechar conta?", parent=janela_desc):
                conn = sqlite3.connect(DB_NAME)
                cursor = conn.cursor()
                
                if desconto > 0:
                    dt_agora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    cursor.execute(
                        "INSERT INTO vendas (mesa_id, produto_nome, qtd, total, data_hora, status) VALUES (?,?,?,?,?,?)",
                        (self.mesa_atual, f"DESCONTO MANUAL", 1, -desconto, dt_agora, 'ABERTA')
                    )

                cursor.execute(
                    "UPDATE vendas SET status='FECHADA', pagamento=? WHERE mesa_id=? AND status='ABERTA'", 
                    (self.cb_pag_mesa.get(), self.mesa_atual)
                )
                
                conn.commit()
                conn.close()
                
                janela_desc.destroy()
                self.carregar_mesa()
                self.atualizar_cores_mesas()
                self.app.aba_caixa.carregar_historico()
                messagebox.showinfo("Sucesso", "Mesa fechada com sucesso!")

        # 2. Renderização Visual dos Componentes
        tk.Label(janela_desc, text=f"MESA {self.mesa_atual:02d}", font=('Arial', 14, 'bold'), bg=CORES['painel'], fg=CORES['amarelo']).pack(pady=5)
        tk.Label(janela_desc, text=f"Subtotal: R$ {total_original:.2f}", font=('Arial', 12), bg=CORES['painel'], fg='white').pack(pady=5)
        
        tk.Label(janela_desc, text="Valor do Desconto (R$):", bg=CORES['painel'], fg='white').pack(pady=2)
        ent_desc = tk.Entry(janela_desc, font=('Arial', 12), width=15, justify='center')
        ent_desc.insert(0, "")
        ent_desc.pack(pady=5)
        
        tk.Button(janela_desc, text="CONFIRMAR FECHAMENTO", bg=CORES['verde'], fg='white', font=('Arial', 11, 'bold'), command=processar_fechamento, pady=5).pack(pady=15)
        
        # Correção para Linux/Tkinter: Força o update visual antes do grab
        janela_desc.update()
        janela_desc.grab_set() 
        ent_desc.focus_set()

    def atualizar_cores_mesas(self):
        conn = sqlite3.connect(DB_NAME)
        ocupadas = [x[0] for x in conn.cursor().execute("SELECT DISTINCT mesa_id FROM vendas WHERE status='ABERTA'").fetchall()]
        conn.close()
        for i in range(1, 21): 
            self.btns_mesa[i].config(bg=CORES['vermelho'] if i in ocupadas else CORES['verde'])

    def ao_clicar_duplo_comanda(self, event):
        sel = self.tree_mesa.selection()
        if not sel:
            return
            
        item_valores = self.tree_mesa.item(sel[0])['values']
        venda_id = item_valores[0]
        produto_nome = item_valores[1]
        qtd_atual = item_valores[2]
        
        self.abrir_janela_editar_qtd(venda_id, produto_nome, qtd_atual)

    def abrir_janela_editar_qtd(self, venda_id, produto_nome, qtd_atual):
        janela_qtd = tk.Toplevel(self)
        janela_qtd.title("Editar / Remover Item")
        janela_qtd.geometry("380x220")  # Aumentada um pouco a largura para acomodar os dois botões lado a lado
        janela_qtd.configure(bg=CORES['painel'])
        janela_qtd.resizable(False, False)

        # 1. Escopo de Função Interna para SALVAR/EDITAR
        def salvar_nova_quantidade():
            try:
                nova_qtd = int(ent_nova_qtd.get())
                if nova_qtd <= 0:
                    messagebox.showerror("Erro", "A quantidade deve ser maior que zero. Para apagar, clique em 'Excluir Item'.", parent=janela_qtd)
                    return
            except ValueError:
                messagebox.showerror("Erro", "Insira um número inteiro válido.", parent=janela_qtd)
                return

            if nova_qtd == qtd_atual:
                janela_qtd.destroy()
                return

            conn = sqlite3.connect(DB_NAME)
            cursor = conn.cursor()
            
            prod_info = cursor.execute("SELECT id, preco, estoque FROM produtos WHERE nome=?", (produto_nome,)).fetchone()
            if not prod_info:
                messagebox.showerror("Erro", "Produto não encontrado no cadastro.", parent=janela_qtd)
                conn.close()
                return
                
            prod_id, preco_unitario, estoque_atual = prod_info
            diferenca_qtd = nova_qtd - qtd_atual 
            
            if diferenca_qtd > estoque_atual:
                messagebox.showerror("Erro", f"Estoque insuficiente!\nDisponível: {estoque_atual}", parent=janela_qtd)
                conn.close()
                return
                
            novo_total_venda = preco_unitario * nova_qtd
            cursor.execute("UPDATE vendas SET qtd=?, total=? WHERE id=?", (nova_qtd, novo_total_venda, venda_id))
            cursor.execute("UPDATE produtos SET estoque = estoque - ? WHERE id=?", (diferenca_qtd, prod_id))
            
            conn.commit()
            conn.close()
            
            janela_qtd.destroy()
            self.carregar_mesa()              
            self.app.atualizar_todos_produtos() 
            messagebox.showinfo("Sucesso", "Quantidade atualizada!")

        # 2. Escopo de Função Interna para APAGAR / REMOVER PRODUTO
        def remover_produto_completamente():
            if messagebox.askyesno("Confirmar Exclusão", f"Deseja realmente remover '{produto_nome}' desta comanda?\nA quantidade ({qtd_atual}) voltará ao estoque.", parent=janela_qtd):
                conn = sqlite3.connect(DB_NAME)
                cursor = conn.cursor()
                
                # Encontra o produto no cadastro para devolver o estoque
                prod_info = cursor.execute("SELECT id FROM produtos WHERE nome=?", (produto_nome,)).fetchone()
                
                if prod_info:
                    prod_id = prod_info[0]
                    # Devolve a quantidade total que estava na mesa de volta para o estoque
                    cursor.execute("UPDATE produtos SET estoque = estoque + ? WHERE id=?", (qtd_atual, prod_id))
                
                # Deleta o registro de venda da mesa
                cursor.execute("DELETE FROM vendas WHERE id=?", (venda_id,))
                
                conn.commit()
                conn.close()
                
                janela_qtd.destroy()
                self.carregar_mesa()
                self.app.atualizar_todos_produtos()
                messagebox.showinfo("Sucesso", "Item removido da mesa!")

        # 3. Renderização Visual dos Componentes
        tk.Label(janela_qtd, text="EDITAR OU REVERTER ITEM", font=('Arial', 12, 'bold'), bg=CORES['painel'], fg=CORES['amarelo']).pack(pady=5)
        tk.Label(janela_qtd, text=f"{produto_nome}", font=('Arial', 11), bg=CORES['painel'], fg='white', wraplength=340).pack(pady=2)
        
        tk.Label(janela_qtd, text="Nova Quantidade:", bg=CORES['painel'], fg='white').pack(pady=5)
        ent_nova_qtd = tk.Entry(janela_qtd, font=('Arial', 12), width=10, justify='center')
        ent_nova_qtd.insert(0, str(qtd_atual))
        ent_nova_qtd.pack(pady=2)
        
        # Frame container para os botões ficarem perfeitamente alinhados lado a lado
        fr_botoes_popup = tk.Frame(janela_qtd, bg=CORES['painel'])
        fr_botoes_popup.pack(pady=15)
        
        # Botão Salvar (Verde)
        tk.Button(fr_botoes_popup, text="SALVAR", bg=CORES['verde'], fg='white', font=('Arial', 10, 'bold'), width=14, command=salvar_nova_quantidade).pack(side='left', padx=10)
        
        # Botão Excluir (Vermelho)
        tk.Button(fr_botoes_popup, text="EXCLUIR ITEM", bg=CORES['vermelho'], fg='white', font=('Arial', 10, 'bold'), width=14, command=remover_produto_completamente).pack(side='left', padx=10)
        
        # Correção específica para compatibilidade Linux/Gnome/Tkinter
        janela_qtd.update()
        janela_qtd.grab_set()
        ent_nova_qtd.focus_set()
        ent_nova_qtd.selection_range(0, tk.END)