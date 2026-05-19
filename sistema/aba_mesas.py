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
        tk.Label(fr_det, text="Pagamento do Saldo Restante:", bg=CORES['fundo'], fg='white').pack()
        self.cb_pag_mesa = ttk.Combobox(fr_det, values=["DINHEIRO", "PIX", "CRÉDITO", "DÉBITO"]); self.cb_pag_mesa.current(0); self.cb_pag_mesa.pack(pady=2)
        tk.Button(fr_det, text="FECHAR MESA", bg=CORES['vermelho'], fg='white', font=('Arial', 12, 'bold'), width=25, command=self.fechar_mesa).pack(pady=10)
        self.atualizar_cores_mesas()

    def atualizar_combobox(self, lista_cb):
        self.cb_prod_mesa['values'] = lista_cb

    def selecionar_mesa(self, m):
        self.mesa_atual = m
        self.lbl_mesa_sel.config(text=f"MESA {m:02d} - EM ABERTO")
        self.carregar_mesa()

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

    def atualizar_cores_mesas(self):
        conn = sqlite3.connect(DB_NAME)
        ocupadas = [x[0] for x in conn.cursor().execute("SELECT DISTINCT mesa_id FROM vendas WHERE status='ABERTA'").fetchall()]
        conn.close()
        for i in range(1, 21): 
            self.btns_mesa[i].config(bg=CORES['vermelho'] if i in ocupadas else CORES['verde'])

    def add_item_mesa(self):
        if not self.mesa_atual: 
            messagebox.showwarning("!","Selecione uma mesa"); return
        try:
            prod = self.cb_prod_mesa.get()
            if not prod: return
            
            qtd = int(self.ent_qtd_mesa.get())
            pid = int(prod.split(' - ')[0])
            
            conn = sqlite3.connect(DB_NAME)
            cursor = conn.cursor()
            
            res = cursor.execute("SELECT nome, preco, estoque, codigo FROM produtos WHERE id=?",(pid,)).fetchone()
            
            if not res:
                messagebox.showerror("Erro", "Produto não encontrado."); conn.close(); return
                
            nome_prod, preco_prod, estoque_prod, codigo_prod = res
            
            if estoque_prod < qtd: 
                messagebox.showerror("Erro", f"Sem estoque suficiente de {nome_prod}!"); conn.close(); return
            
            # --- REGRA DE VÍNCULO (JANTINHA -> ESPETO) ---
            try:
                from sistema import database
                database.processar_baixa_estoque_vinculado(cursor, codigo_prod, qtd)
            except ValueError as e:
                messagebox.showerror("Estoque Insuficiente", str(e))
                conn.close()
                return
            # ---------------------------------------------
                
            total = preco_prod * qtd
            dt = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            cursor.execute("INSERT INTO vendas (mesa_id,produto_nome,qtd,total,data_hora,status) VALUES (?,?,?,?,?,?)",(self.mesa_atual,nome_prod,qtd,total,dt,'ABERTA'))
            cursor.execute("UPDATE produtos SET estoque=estoque-? WHERE id=?",(qtd,pid))
            
            conn.commit()
            conn.close()
            
            self.carregar_mesa()
            self.app.atualizar_todos_produtos() 
            self.atualizar_cores_mesas()
        except Exception as e: 
            print("Erro ao lançar item na mesa:", e)

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
        janela_desc.title(f"Fechamento / Divisão - Mesa {self.mesa_atual:02d}")
        janela_desc.geometry("520x380")
        janela_desc.configure(bg=CORES['painel'])
        janela_desc.resizable(False, False)

        self.saldo_restante = total_original

        # Componentes estruturados no topo para evitar bugs de definição
        tk.Label(janela_desc, text=f"FECHAMENTO DA MESA {self.mesa_atual:02d}", font=('Arial', 13, 'bold'), bg=CORES['painel'], fg=CORES['amarelo']).pack(pady=5)
        lbl_saldo = tk.Label(janela_desc, text=f"SALDO RESTANTE: R$ {total_original:.2f}", font=('Arial', 14, 'bold'), bg=CORES['painel'], fg=CORES['verde'])
        lbl_saldo.pack(pady=5)

        fr_divisao = tk.LabelFrame(janela_desc, text=" Receber Pagamento Parcial (Dividir Conta) ", bg=CORES['painel'], fg='white', font=('Arial', 10, 'bold'), padx=10, pady=10)
        fr_divisao.pack(fill='x', padx=15, pady=5)
        tk.Label(fr_divisao, text="Valor a pagar agora (R$):", bg=CORES['painel'], fg='white').grid(row=0, column=0, sticky='w', pady=2)
        ent_valor_pagar = tk.Entry(fr_divisao, font=('Arial', 11), width=14, justify='center')
        ent_valor_pagar.insert(0, f"{total_original:.2f}")
        ent_valor_pagar.grid(row=0, column=1, pady=2, padx=5)
        tk.Label(fr_divisao, text="Forma de Pagamento:", bg=CORES['painel'], fg='white').grid(row=1, column=0, sticky='w', pady=2)
        cb_forma_parcial = ttk.Combobox(fr_divisao, values=["DINHEIRO", "PIX", "CRÉDITO", "DÉBITO"], width=12, state="readonly")
        cb_forma_parcial.current(0); cb_forma_parcial.grid(row=1, column=1, pady=2, padx=5)

        fr_total = tk.LabelFrame(janela_desc, text=" Encerrar Saldo Restante / Aplicar Desconto ", bg=CORES['painel'], fg='white', font=('Arial', 10, 'bold'), padx=10, pady=10)
        fr_total.pack(fill='x', padx=15, pady=10)
        tk.Label(fr_total, text="Conceder Desconto (R$):", bg=CORES['painel'], fg='white').pack(side='left', padx=5)
        ent_desc = tk.Entry(fr_total, font=('Arial', 11), width=12, justify='center')
        ent_desc.insert(0, "0.00"); ent_desc.pack(side='left', padx=5)

        # Funções internas da janela de fechamento
        def emitir_recibo_comanda(numero_mesa, total_original_comanda):
            import os
            data_atual = datetime.now().strftime("%Y-%m-%d")
            hora_atual = datetime.now().strftime("%H:%M:%S")
            nome_arq = f"Comanda_Mesa_{numero_mesa}_{datetime.now().strftime('%H%M%S')}.txt"
            
            try:
                conn = sqlite3.connect(DB_NAME)
                itens_fechados = conn.cursor().execute(
                    "SELECT produto_nome, qtd, total, pagamento FROM vendas WHERE mesa_id=? AND data_hora LIKE ? ORDER BY id ASC",
                    (numero_mesa, f"{data_atual}%")
                ).fetchall()
                conn.close()

                if not itens_fechados:
                    messagebox.showinfo("Vazio", "Nenhum item localizado no histórico recente desta mesa para impressão.", parent=janela_desc)
                    return

                with open(nome_arq, "w", encoding='utf-8') as f:
                    f.write("================================================\n")
                    f.write("               BANCART PRO 5.0                  \n")
                    f.write(f"            CUPOM DE CONSUMO - MESA {numero_mesa:02d}      \n")
                    f.write("================================================\n")
                    f.write(f"Data: {data_atual}   Hora: {hora_atual}\n")
                    f.write("------------------------------------------------\n")
                    f.write(f"{'PRODUTO':<24} {'QTD':<5} {'TOTAL':<10}\n")
                    f.write("------------------------------------------------\n")
                    
                    subtotal_produtos = 0
                    descontos_e_ajustes = 0
                    pagamentos_registrados = []

                    for item in itens_fechados:
                        nome, qtd, total, pgto = item
                        if "PAG. PARCIAL" in nome:
                            pagamentos_registrados.append((pgto, total))
                        elif "DESCONTO" in nome or "ABATIMENTO" in nome:
                            f.write(f"{nome[:24]:<24} {qtd:<5} R${total:<8.2f}\n")
                            descontos_e_ajustes += total
                        else:
                            f.write(f"{nome[:24]:<24} {qtd:<5} R${total:<8.2f}\n")
                            subtotal_produtos += total
                    
                    f.write("------------------------------------------------\n")
                    f.write(f"SUBTOTAL DOS ITENS:                   R$ {total_original_comanda:.2f}\n")
                    if descontos_e_ajustes != 0:
                        f.write(f"DESCONTOS/ABATIMENTOS:                R$ {descontos_e_ajustes:.2f}\n")
                    f.write(f"TOTAL LÍQUIDO DA COMANDA:             R$ {total_original_comanda + descontos_e_ajustes:.2f}\n")
                    f.write("================================================\n")
                    
                    if pagamentos_registrados:
                        f.write("HISTÓRICO DE PAGAMENTOS:\n")
                        for pgto_tipo, valor in pagamentos_registrados:
                            f.write(f" -> {pgto_tipo:<15}:                   R$ {valor:.2f}\n")
                        f.write("================================================\n")
                    
                    f.write("          Obrigado pela preferência!            \n")
                    f.write("================================================\n")

                if hasattr(os, 'startfile'):
                    os.startfile(nome_arq)
                else:
                    os.system(f'xdg-open "{nome_arq}"')
            except Exception as e:
                messagebox.showerror("Erro Impressão", f"Não foi possível gerar o cupom: {e}", parent=janela_desc)

        def receber_pagamento_parcial():
            try:
                valor_pago = float(ent_valor_pagar.get().replace(',', '.'))
                if valor_pago <= 0:
                    messagebox.showerror("Erro", "O valor a pagar deve ser maior que zero.", parent=janela_desc)
                    return
                if valor_pago > self.saldo_restante + 0.01:
                    messagebox.showerror("Erro", "O valor informado é maior que o saldo restante!", parent=janela_desc)
                    return
            except ValueError:
                messagebox.showerror("Erro", "Insira um valor numérico válido.", parent=janela_desc)
                return

            forma_pgto = cb_forma_parcial.get()
            if messagebox.askyesno("Confirmar", f"Receber R$ {valor_pago:.2f} no {forma_pgto}?", parent=janela_desc):
                conn = sqlite3.connect(DB_NAME)
                cursor = conn.cursor()
                dt_agora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                cursor.execute("INSERT INTO vendas (mesa_id, produto_nome, qtd, total, data_hora, pagamento, status) VALUES (?,?,?,?,?,?,?)", (self.mesa_atual, f"PAG. PARCIAL MESA {self.mesa_atual}", 1, valor_pago, dt_agora, forma_pgto, 'FECHADA'))
                cursor.execute("INSERT INTO vendas (mesa_id, produto_nome, qtd, total, data_hora, status) VALUES (?,?,?,?,?,?)", (self.mesa_atual, f"ABATIMENTO ({forma_pgto})", 1, -valor_pago, dt_agora, 'ABERTA'))
                conn.commit(); conn.close()

                self.saldo_restante -= valor_pago
                lbl_saldo.config(text=f"SALDO RESTANTE: R$ {self.saldo_restante:.2f}", fg=CORES['vermelho'] if self.saldo_restante > 0 else CORES['verde'])
                self.carregar_mesa()
                self.app.aba_caixa.carregar_historico()

                if self.saldo_restante <= 0.01:
                    finalizar_mesa_totalmente(deve_perguntar=False)
                else:
                    ent_valor_pagar.delete(0, tk.END)
                    ent_valor_pagar.insert(0, f"{self.saldo_restante:.2f}")
                    messagebox.showinfo("Sucesso", f"Pagamento de R$ {valor_pago:.2f} recebido!", parent=janela_desc)

        def finalizar_mesa_totalmente(deve_perguntar=True):
            try:
                desconto = float(ent_desc.get().replace(',', '.'))
                if desconto < 0: raise ValueError
                if desconto > self.saldo_restante:
                    messagebox.showerror("Erro", "O desconto não pode ser maior que o saldo restante!", parent=janela_desc)
                    return
            except ValueError:
                messagebox.showerror("Erro", "Insira um valor de desconto válido.", parent=janela_desc)
                return

            total_final = self.saldo_restante - desconto
            forma_pgto_final = self.cb_pag_mesa.get()
            texto_confirma = f"Total Restante: R$ {self.saldo_restante:.2f}\nDesconto: R$ {desconto:.2f}\nValor Final: R$ {total_final:.2f}\nFechar mesa no {forma_pgto_final}?"
            
            if not deve_perguntar or messagebox.askyesno("Confirmar Encerramento", texto_confirma, parent=janela_desc):
                conn = sqlite3.connect(DB_NAME); cursor = conn.cursor()
                if desconto > 0:
                    dt_agora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    cursor.execute("INSERT INTO vendas (mesa_id, produto_nome, qtd, total, data_hora, status) VALUES (?,?,?,?,?,?)", (self.mesa_atual, f"DESCONTO MANUAL", 1, -desconto, dt_agora, 'ABERTA'))
                
                cursor.execute("UPDATE vendas SET status='FECHADA', pagamento=? WHERE mesa_id=? AND status='ABERTA'", (forma_pgto_final, self.mesa_atual))
                conn.commit(); conn.close()
                
                mesa_fechada = self.mesa_atual
                janela_desc.destroy()
                self.carregar_mesa()
                self.atualizar_cores_mesas()
                self.app.aba_caixa.carregar_historico()
                
                if messagebox.askyesno("Mesa Encerrada", f"Mesa {mesa_fechada:02d} fechada com sucesso!\nDeseja emitir o relatório de consumo desta comanda?"):
                    emitir_recibo_comanda(mesa_fechada, total_original)

        # Vinculação tardia dos comandos aos botões criados
        tk.Button(fr_divisao, text="RECEBER PARTE", bg=CORES['azul'], fg='white', font=('Arial', 9, 'bold'), command=receber_pagamento_parcial).grid(row=0, column=2, rowspan=2, padx=10, ipady=4)
        tk.Button(fr_total, text="FECHAR CONTA", bg=CORES['verde'], fg='white', font=('Arial', 10, 'bold'), command=lambda: finalizar_mesa_totalmente(deve_perguntar=True)).pack(side='right', padx=5, ipady=2)

        janela_desc.update(); janela_desc.grab_set()
        ent_valor_pagar.focus_set(); ent_valor_pagar.selection_range(0, tk.END)

    def ao_clicar_duplo_comanda(self, event):
        sel = self.tree_mesa.selection()
        if not sel: return
        item_valores = self.tree_mesa.item(sel[0])['values']
        self.abrir_janela_editar_qtd(item_valores[0], item_valores[1], item_valores[2])

    def abrir_janela_editar_qtd(self, venda_id, produto_nome, qtd_atual):
        janela_qtd = tk.Toplevel(self)
        janela_qtd.title("Editar / Remover Item")
        janela_qtd.geometry("380x220")
        janela_qtd.configure(bg=CORES['painel'])
        janela_qtd.resizable(False, False)

        tk.Label(janela_qtd, text="EDITAR OU REVERTER ITEM", font=('Arial', 12, 'bold'), bg=CORES['painel'], fg=CORES['amarelo']).pack(pady=5)
        tk.Label(janela_qtd, text=f"{produto_nome}", font=('Arial', 11), bg=CORES['painel'], fg='white', wraplength=340).pack(pady=2)
        tk.Label(janela_qtd, text="Nova Quantidade:", bg=CORES['painel'], fg='white').pack(pady=5)
        
        ent_nova_qtd = tk.Entry(janela_qtd, font=('Arial', 12), width=10, justify='center')
        ent_nova_qtd.insert(0, str(qtd_atual)); ent_nova_qtd.pack(pady=2)
        fr_botoes_popup = tk.Frame(janela_qtd, bg=CORES['painel']); fr_botoes_popup.pack(pady=15)

        def salvar_nova_quantidade():
            try:
                nova_qtd = int(ent_nova_qtd.get())
                if nova_qtd <= 0:
                    messagebox.showerror("Erro", "A quantidade deve ser maior que zero.", parent=janela_qtd)
                    return
            except ValueError:
                messagebox.showerror("Erro", "Insira um número inteiro válido.", parent=janela_qtd)
                return

            if nova_qtd == qtd_atual:
                janela_qtd.destroy(); return

            conn = sqlite3.connect(DB_NAME); cursor = conn.cursor()
            prod_info = cursor.execute("SELECT id, preco, estoque, codigo FROM produtos WHERE nome=?", (produto_nome,)).fetchone()
            if not prod_info:
                messagebox.showerror("Erro", "Produto não encontrado.", parent=janela_qtd); conn.close(); return
                
            prod_id, preco_unitario, estoque_atual, codigo_prod = prod_info
            diferenca_qtd = nova_qtd - qtd_atual 
            
            if str(codigo_prod).strip() in ["001", "1"] and diferenca_qtd > 0:
                espeto = cursor.execute("SELECT estoque FROM produtos WHERE codigo = '100'").fetchone()
                if espeto and espeto[0] < diferenca_qtd:
                    messagebox.showerror("Erro", f"Estoque de Espeto insuficiente para aumentar a Jantinha!\nDisponível: {espeto[0]}", parent=janela_qtd)
                    conn.close(); return

            if diferenca_qtd > estoque_atual:
                messagebox.showerror("Erro", f"Estoque insuficiente!\nDisponível: {estoque_atual}", parent=janela_qtd); conn.close(); return
                
            novo_total_venda = preco_unitario * nova_qtd
            cursor.execute("UPDATE vendas SET qtd=?, total=? WHERE id=?", (nova_qtd, novo_total_venda, venda_id))
            cursor.execute("UPDATE produtos SET estoque = estoque - ? WHERE id=?", (diferenca_qtd, prod_id))
            
            if str(codigo_prod).strip() in ["001", "1"]:
                cursor.execute("UPDATE produtos SET estoque = estoque - ? WHERE codigo = '100'", (diferenca_qtd,))

            conn.commit(); conn.close()
            janela_qtd.destroy(); self.carregar_mesa(); self.app.atualizar_todos_produtos()
            messagebox.showinfo("Sucesso", "Quantidade atualizada!")

        def remover_produto_completamente():
            if messagebox.askyesno("Confirmar Exclusão", f"Deseja remover '{produto_nome}'?", parent=janela_qtd):
                conn = sqlite3.connect(DB_NAME); cursor = conn.cursor()
                prod_info = cursor.execute("SELECT id, codigo FROM produtos WHERE nome=?", (produto_nome,)).fetchone()
                if prod_info:
                    prod_id, codigo_prod = prod_info
                    cursor.execute("UPDATE produtos SET estoque = estoque + ? WHERE id=?", (qtd_atual, prod_id))
                    if str(codigo_prod).strip() in ["001", "1"]:
                        cursor.execute("UPDATE produtos SET estoque = estoque + ? WHERE codigo = '100'", (qtd_atual,))
                        
                cursor.execute("DELETE FROM vendas WHERE id=?", (venda_id,))
                conn.commit(); conn.close()
                janela_qtd.destroy(); self.carregar_mesa(); self.app.atualizar_todos_produtos()
                messagebox.showinfo("Sucesso", "Item removido!")

        tk.Button(fr_botoes_popup, text="SALVAR", bg=CORES['verde'], fg='white', font=('Arial', 10, 'bold'), width=14, command=salvar_nova_quantidade).pack(side='left', padx=10)
        tk.Button(fr_botoes_popup, text="EXCLUIR ITEM", bg=CORES['vermelho'], fg='white', font=('Arial', 10, 'bold'), width=14, command=remover_produto_completamente).pack(side='left', padx=10)
        
        janela_qtd.update(); janela_qtd.grab_set()
        ent_nova_qtd.focus_set(); ent_nova_qtd.selection_range(0, tk.END)