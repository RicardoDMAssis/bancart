# aba_balcao.py
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
        self.tree_avulso.bind("<Double-1>", self.ao_clicar_duplo_balcao)
        tk.Button(self, text="Limpar", command=self.limpar_avulso).pack()
        
        fr_base = tk.Frame(self, bg=CORES['painel'], pady=10); fr_base.pack(fill='x', padx=10, pady=10)
        self.lbl_total_avulso = tk.Label(fr_base, text="TOTAL: R$ 0.00", font=('Arial', 24), fg=CORES['verde'], bg=CORES['painel'])
        self.lbl_total_avulso.pack(side='left', padx=20)
        
        fr_pag = tk.Frame(fr_base, bg=CORES['painel']); fr_pag.pack(side='right', padx=20)
        self.cb_pag_avulso = ttk.Combobox(fr_pag, values=["DINHEIRO", "PIX", "CRÉDITO", "DÉBITO"]); self.cb_pag_avulso.current(0); self.cb_pag_avulso.pack()
        tk.Button(fr_pag, text="FINALIZAR", bg=CORES['verde'], fg='white', font=('Arial', 14), command=self.finalizar_avulso).pack(pady=5)

    def atualizar_combobox(self, lista_cb):
        self.cb_prod_avulso['values'] = lista_cb

    def add_carrinho_avulso(self):
        try:
            prod_txt = self.cb_prod_avulso.get(); qtd = int(self.ent_qtd_avulso.get()); pid = int(prod_txt.split(' - ')[0])
            conn = sqlite3.connect(DB_NAME); res = conn.cursor().execute("SELECT nome, preco, estoque FROM produtos WHERE id=?", (pid,)).fetchone(); conn.close()
            if res[2] < qtd: messagebox.showerror("Erro", "Sem estoque!"); return
            self.carrinho_avulso.append({'id': pid, 'nome': res[0], 'qtd': qtd, 'tot': res[1] * qtd}); self.atualizar_avulso()
        except Exception as e: print(e)

    def atualizar_avulso(self):
        self.tree_avulso.delete(*self.tree_avulso.get_children()); geral = 0
        for i in self.carrinho_avulso: self.tree_avulso.insert('', 'end', values=(i['nome'], i['qtd'], f"{i['tot']:.2f}")); geral += i['tot']
        self.lbl_total_avulso.config(text=f"TOTAL: R$ {geral:.2f}")

    def limpar_avulso(self): 
        self.carrinho_avulso = []; self.atualizar_avulso()

    def ao_clicar_duplo_balcao(self, event):
        sel = self.tree_avulso.selection()
        if not sel:
            return
            
        # Descobre qual índice da lista 'carrinho_avulso' foi clicado com base na linha selecionada
        index_selecionado = self.tree_avulso.index(sel[0])
        item_carrinho = self.carrinho_avulso[index_selecionado]
        
        # Abre a tela flutuante enviando o índice do item no carrinho
        self.abrir_janela_editar_qtd_balcao(index_selecionado, item_carrinho['nome'], item_carrinho['qtd'], item_carrinho['id'])

    def abrir_janela_editar_qtd_balcao(self, index_item, produto_nome, qtd_atual, produto_id):
        janela_qtd = tk.Toplevel(self)
        janela_qtd.title("Editar / Remover do Balcão")
        janela_qtd.geometry("380x220")
        janela_qtd.configure(bg=CORES['painel'])
        janela_qtd.resizable(False, False)

        # 1. Função interna para SALVAR / EDITAR a quantidade
        def salvar_nova_quantidade():
            try:
                nova_qtd = int(ent_nova_qtd.get())
                if nova_qtd <= 0:
                    messagebox.showerror("Erro", "A quantidade deve ser maior que zero. Para apagar, clique em 'Remover'.", parent=janela_qtd)
                    return
            except ValueError:
                messagebox.showerror("Erro", "Insira um número inteiro válido.", parent=janela_qtd)
                return

            if nova_qtd == qtd_atual:
                janela_qtd.destroy()
                return

            # Busca o preço unitário e estoque atual do produto no BD para validação
            conn = sqlite3.connect(DB_NAME)
            res = conn.cursor().execute("SELECT preco, estoque FROM produtos WHERE id=?", (produto_id,)).fetchone()
            conn.close()

            if not res:
                messagebox.showerror("Erro", "Produto não encontrado no banco.", parent=janela_qtd)
                return

            preco_unitario, estoque_atual = res

            # No balcão o produto ainda NÃO saiu do estoque no BD, então precisamos ver se o estoque suporta a nova quantidade total
            if nova_qtd > estoque_atual:
                messagebox.showerror("Erro", f"Estoque insuficiente!\nDisponível: {estoque_atual}", parent=janela_qtd)
                return

            # Atualiza o item diretamente na lista em memória (carrinho)
            self.carrinho_avulso[index_item]['qtd'] = nova_qtd
            self.carrinho_avulso[index_item]['tot'] = preco_unitario * nova_qtd

            # Atualiza a interface
            janela_qtd.destroy()
            self.atualizar_avulso()
            messagebox.showinfo("Sucesso", "Quantidade atualizada no carrinho!")

        # 2. Função interna para REMOVER o produto do carrinho
        def remover_produto_carrinho():
            if messagebox.askyesno("Confirmar Remoção", f"Deseja realmente remover '{produto_nome}' do balcão?", parent=janela_qtd):
                # Remove da lista em memória pelo índice
                self.carrinho_avulso.pop(index_item)
                
                janela_qtd.destroy()
                self.atualizar_avulso()
                messagebox.showinfo("Sucesso", "Item removido do balcão!")

        # 3. Desenho dos componentes na janela (Corrigido para evitar tela em branco no Linux)
        tk.Label(janela_qtd, text="EDITAR OU REMOVER ITEM", font=('Arial', 12, 'bold'), bg=CORES['painel'], fg=CORES['amarelo']).pack(pady=5)
        tk.Label(janela_qtd, text=f"{produto_nome}", font=('Arial', 11), bg=CORES['painel'], fg='white', wraplength=340).pack(pady=2)
        
        tk.Label(janela_qtd, text="Nova Quantidade:", bg=CORES['painel'], fg='white').pack(pady=5)
        ent_nova_qtd = tk.Entry(janela_qtd, font=('Arial', 12), width=10, justify='center')
        ent_nova_qtd.insert(0, str(qtd_atual))
        ent_nova_qtd.pack(pady=2)
        
        fr_botoes_popup = tk.Frame(janela_qtd, bg=CORES['painel'])
        fr_botoes_popup.pack(pady=15)
        
        tk.Button(fr_botoes_popup, text="SALVAR", bg=CORES['verde'], fg='white', font=('Arial', 10, 'bold'), width=14, command=salvar_nova_quantidade).pack(side='left', padx=10)
        tk.Button(fr_botoes_popup, text="REMOVER", bg=CORES['vermelho'], fg='white', font=('Arial', 10, 'bold'), width=14, command=remover_produto_carrinho).pack(side='left', padx=10)
        
        # Sincronização segura com o sistema de janelas do Linux
        janela_qtd.update()
        janela_qtd.grab_set()
        ent_nova_qtd.focus_set()
        ent_nova_qtd.selection_range(0, tk.END)

    def finalizar_avulso(self):
        if not self.carrinho_avulso: return
        if messagebox.askyesno("Confirmar", "Finalizar venda?"):
            conn = sqlite3.connect(DB_NAME); c = conn.cursor(); dt = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            for item in self.carrinho_avulso:
                c.execute("INSERT INTO vendas (mesa_id, produto_nome, qtd, total, data_hora, pagamento, status) VALUES (?,?,?,?,?,?,?)", (0, item['nome'], item['qtd'], item['tot'], dt, self.cb_pag_avulso.get(), 'FECHADA'))
                c.execute("UPDATE produtos SET estoque = estoque - ? WHERE id=?", (item['qtd'], item['id']))
            conn.commit(); conn.close()
            self.limpar_avulso()
            self.app.atualizar_todos_produtos()
            self.app.aba_caixa.carregar_historico()
            messagebox.showinfo("Sucesso", "Venda OK!")