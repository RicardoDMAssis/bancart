# sistema/aba_balcao.py
import tkinter as tk
from tkinter import ttk, messagebox
import sqlite3
import os
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
        tk.Button(fr_pag, text="CORTESIA", bg=CORES['azul'], fg='white', font=('Arial', 11, 'bold'), command=self.finalizar_cortesia).pack(pady=3, fill='x')

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

    # --- NOVO SISTEMA EMISSÃO PDF BALCÃO (REPORTLAB) ---
    def emitir_recibo_balcao_pdf(self, id_comanda_balcao, total_original):
        from reportlab.lib.pagesizes import letter
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib import colors
        from sistema.config import DADOS_EMPRESA

        nome_pdf = f"Recibo_Balcao_{id_comanda_balcao}.pdf"
        
        try:
            dados_tabela = [["PRODUTO", "QTD", "TOTAL"]]
            conn = sqlite3.connect(DB_NAME)
            dados_pai = conn.cursor().execute("SELECT data_fechamento, pagamento FROM atendimentos WHERE id=?", (id_comanda_balcao,)).fetchone()
            itens_fechados = conn.cursor().execute("SELECT produto_nome, qtd, total FROM itens_atendimento WHERE atendimento_id=?", (id_comanda_balcao,)).fetchall()
            conn.close()

            doc = SimpleDocTemplate(nome_pdf, pagesize=letter, rightMargin=30, leftMargin=30, topMargin=30, bottomMargin=30)
            story = []
            styles = getSampleStyleSheet()
            style_titulo = ParagraphStyle('T_B1', parent=styles['Heading1'], fontSize=16, leading=20, alignment=1, textColor=colors.HexColor('#2c3e50'))
            style_empresa = ParagraphStyle('E_B1', parent=styles['Normal'], fontSize=10, leading=14, alignment=1, textColor=colors.HexColor('#7f8c8d'))
            style_normal = ParagraphStyle('N_B1', parent=styles['Normal'], fontSize=10, leading=14)
            style_negrito = ParagraphStyle('B_B1', parent=styles['Normal'], fontName='Helvetica-Bold', fontSize=10, leading=14)

            story.append(Paragraph(f"<b>{DADOS_EMPRESA['nome']}</b>", style_titulo))
            story.append(Spacer(1, 4))
            story.append(Paragraph(f"CNPJ: {DADOS_EMPRESA['cnpj']} | Tel: {DADOS_EMPRESA['telefone']}", style_empresa))
            story.append(Paragraph(f"Endereço: {DADOS_EMPRESA['endereco']}", style_empresa))
            story.append(Spacer(1, 10))
            story.append(Paragraph("<b>RECIBO DE VENDA AVULSA - BALCÃO</b>", ParagraphStyle('SubB', parent=style_titulo, fontSize=12)))
            story.append(Paragraph(f"<b>CUPOM BALCÃO Nº: {id_comanda_balcao}</b>", style_negrito))
            story.append(Paragraph(f"Data Emissão: {dados_pai[0]}", style_normal))
            story.append(Spacer(1, 10))

            for item in itens_fechados:
                dados_tabela.append([item[0], str(item[1]), f"R$ {item[2]:.2f}"])

            tabela_itens = Table(dados_tabela, colWidths=[300, 60, 100])
            tabela_itens.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#e67e22')), # Cor laranja para combinar visualmente com o balcão
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('ALIGN', (1, 0), (-1, -1), 'CENTER'),
                ('LINEBELOW', (0, 0), (-1, -1), 0.5, colors.HexColor('#bdc3c7')),
                ('TOPPADDING', (0, 1), (-1, -1), 4),
                ('BOTTOMPADDING', (0, 1), (-1, -1), 4),
            ]))
            story.append(tabela_itens)
            story.append(Spacer(1, 15))

            story.append(Paragraph(f"<b>TOTAL LÍQUIDO PAGO:</b> R$ {total_original:.2f}", style_negrito))
            story.append(Paragraph(f"<b>FORMA DE PAGAMENTO:</b> {dados_pai[1]}", style_normal))
            
            story.append(Spacer(1, 25))
            story.append(Paragraph("Agradecemos a preferência! Volte Sempre.", ParagraphStyle('R_B1', parent=style_empresa, fontName='Helvetica-Oblique', fontSize=11)))
            doc.build(story)

            if hasattr(os, 'startfile'): os.startfile(nome_pdf)
            else: os.system(f'xdg-open "{nome_pdf}"')
        except Exception as e: 
            messagebox.showerror("Erro PDF Balcão", f"Falha ao gerar recibo: {e}")

    def finalizar_avulso(self):
        if not self.carrinho_avulso: return
        total_venda = sum(item['tot'] for item in self.carrinho_avulso)
        forma_pgto = self.cb_pag_avulso.get()

        def efetivar_venda_balcao():
            conn = sqlite3.connect(DB_NAME); c = conn.cursor(); dt_agora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            try:
                # 1. Abre registro unificado PAI na tabela atendimentos (mesa_id 0 identifica Balcão)
                c.execute("INSERT INTO atendimentos (mesa_id, data_abertura, data_fechamento, desconto, pagamento, status) VALUES (?,?,?,?,?,?)", (0, dt_agora, dt_agora, 0.0, forma_pgto, 'FECHADO'))
                id_balcao_gerado = c.lastrowid

                # 2. Insere os registros FILHOS mapeados no ID correspondente e abate estoque
                for item in self.carrinho_avulso:
                    codigo_prod = c.execute("SELECT codigo FROM produtos WHERE id=?", (item['id'],)).fetchone()[0]
                    from sistema import database
                    database.processar_baixa_estoque_vinculado(c, codigo_prod, item['qtd'])
                    
                    c.execute("INSERT INTO itens_atendimento (atendimento_id, produto_nome, qtd, total) VALUES (?,?,?,?)", (id_balcao_gerado, item['nome'], item['qtd'], item['tot']))
                    c.execute("UPDATE produtos SET estoque = estoque - ? WHERE id=?", (item['qtd'], item['id']))
                
                conn.commit()
                
                # 3. Limpa o fluxo local e atualiza as telas ANTES do prompt para evitar janelas fantasmas
                self.limpar_avulso()
                self.app.atualizar_todos_produtos()
                self.app.aba_caixa.carregar_historico()

                if messagebox.askyesno("Venda Balcão", "Venda realizada com sucesso!\nDeseja emitir o recibo em PDF?"):
                    self.emitir_recibo_balcao_pdf(id_balcao_gerado, total_venda)

            except ValueError as e: 
                conn.rollback(); messagebox.showerror("Erro de Estoque", str(e))
            finally: 
                conn.close()

        if forma_pgto == "DINHEIRO":
            # --- CALCULADORA DE TROCO POPUP RÁPIDO PARA BALCÃO ---
            janela_troco = tk.Toplevel(self); janela_troco.title("Troco - Balcão"); janela_troco.geometry("320x200"); janela_troco.configure(bg=CORES['painel'])
            tk.Label(janela_troco, text="💵 VENDA EM DINHEIRO", font=('Arial', 11, 'bold'), bg=CORES['painel'], fg=CORES['amarelo']).pack(pady=5)
            tk.Label(janela_troco, text=f"Total: R$ {total_venda:.2f}", font=('Arial', 11), bg=CORES['painel'], fg='white').pack()
            ent_recebido = tk.Entry(janela_troco, font=('Arial', 12), width=15, justify='center'); ent_recebido.insert(0, f"{total_venda:.2f}"); ent_recebido.pack()
            ent_recebido.focus_set(); ent_recebido.selection_range(0, tk.END)
            lbl_troco = tk.Label(janela_troco, text="TROCO: R$ 0.00", font=('Arial', 12, 'bold'), bg=CORES['painel'], fg=CORES['verde']); lbl_troco.pack(pady=5)

            def calcular_troco(event=None):
                try:
                    recebido = float(ent_recebido.get().replace(',', '.'))
                    troco = recebido - total_venda
                    lbl_troco.config(text=f"TROCO: R$ {max(0.0, troco):.2f}" if troco >= 0 else "VALOR INSUFICIENTE", fg=CORES['verde'] if troco >= 0 else CORES['vermelho'])
                except ValueError: lbl_troco.config(text="VALOR INVÁLIDO", fg=CORES['vermelho'])

            ent_recebido.bind("<KeyRelease>", calcular_troco)

            def confirmar_e_fechar():
                try:
                    recebido = float(ent_recebido.get().replace(',', '.'))
                    if recebido < total_venda: messagebox.showerror("Erro", "Valor insuficiente!", parent=janela_troco); return
                    troco = recebido - total_venda
                except ValueError: return
                if troco > 0: messagebox.showinfo("Troco", f"Devolver troco de: R$ {troco:.2f}", parent=janela_troco)
                janela_troco.destroy()
                efetivar_venda_balcao()

            fr_bnt = tk.Frame(janela_troco, bg=CORES['painel']); fr_bnt.pack(pady=10)
            tk.Button(fr_bnt, text="PAGO EXATO", bg=CORES['busca'], fg='white', font=('Arial', 9, 'bold'), command=lambda: [ent_recebido.delete(0, tk.END), ent_recebido.insert(0, str(total_venda)), confirmar_e_fechar()]).pack(side='left', padx=5)
            tk.Button(fr_bnt, text="FINALIZAR", bg=CORES['verde'], fg='white', font=('Arial', 9, 'bold'), command=confirmar_e_fechar).pack(side='left', padx=5)
            janela_troco.update(); janela_troco.grab_set()
        else:
            if messagebox.askyesno("Confirmar", f"Finalizar venda no {forma_pgto}?"): efetivar_venda_balcao()

    def finalizar_cortesia(self):
        if not self.carrinho_avulso: return
        janela_nome = tk.Toplevel(self); janela_nome.title("Nome"); janela_nome.geometry("350x180"); janela_nome.configure(bg=CORES['painel'])
        tk.Label(janela_nome, text="Nome do Funcionário / Beneficiário:", bg=CORES['painel'], fg='white', font=('Arial', 10)).pack(pady=10)
        ent_nome_func = tk.Entry(janela_nome, font=('Arial', 11), width=25, justify='center'); ent_nome_func.pack(); ent_nome_func.focus_set()

        def confirmar_gravacao_cortesia():
            nome_recebedor = ent_nome_func.get().strip().upper()
            if not nome_recebedor: messagebox.showerror("Erro", "Nome obrigatório!", parent=janela_nome); return
            
            conn = sqlite3.connect(DB_NAME); c = conn.cursor(); dt_agora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            try:
                # Cria registro PAI como CORTESIA zerada
                c.execute("INSERT INTO atendimentos (mesa_id, data_abertura, data_fechamento, desconto, pagamento, status) VALUES (?,?,?,?,?,?)", (0, dt_agora, dt_agora, 0.0, f"CORTESIA ({nome_recebedor})", 'FECHADO'))
                id_cortesia_gerado = c.lastrowid

                for item in self.carrinho_avulso:
                    codigo_prod = c.execute("SELECT codigo FROM produtos WHERE id=?", (item['id'],)).fetchone()[0]
                    from sistema import database
                    database.processar_baixa_estoque_vinculado(c, codigo_prod, item['qtd'])
                    
                    # Nome do item modificado para auditoria limpa na tabela filho
                    c.execute("INSERT INTO itens_atendimento (atendimento_id, produto_nome, qtd, total) VALUES (?,?,?,?)", (id_cortesia_gerado, f"[CORTESIA] {item['nome']}", item['qtd'], 0.00))
                    c.execute("UPDATE produtos SET estoque = estoque - ? WHERE id=?", (item['qtd'], item['id']))
                
                conn.commit()
                janela_nome.destroy()
                
                self.limpar_avulso()
                self.app.atualizar_todos_produtos()
                self.app.aba_caixa.carregar_historico()
                
                if messagebox.askyesno("Cortesia Concluída", f"Cortesia para {nome_recebedor} gravada!\nDeseja emitir o comprovante em PDF?"):
                    self.emitir_recibo_balcao_pdf(id_cortesia_gerado, 0.00)
                    
            except ValueError as e: 
                conn.rollback(); messagebox.showerror("Erro", str(e), parent=janela_nome)
            finally: 
                conn.close()

        tk.Button(janela_nome, text="LIBERAR CORTESIA", bg=CORES['verde'], fg='white', font=('Arial', 10, 'bold'), command=confirmar_gravacao_cortesia).pack(pady=15)
        janela_nome.update(); janela_nome.grab_set()