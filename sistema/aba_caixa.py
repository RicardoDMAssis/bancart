# sistema/aba_caixa.py
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
        self.caixa_id_atual = None
        self.caixa_aberto = False
        self.montar_interface()
        self.verificar_status_caixa()

    def montar_interface(self):
        self.fr_status = tk.LabelFrame(self, text=" GESTÃO DE FLUXO DE CAIXA ", bg=CORES['painel'], fg='white', font=('Arial', 10, 'bold'), padx=10, pady=10)
        self.fr_status.pack(fill='x', padx=10, pady=5)

        self.lbl_status_visual = tk.Label(self.fr_status, text="CAIXA FECHADO", font=('Arial', 12, 'bold'), bg=CORES['vermelho'], fg='white', width=16)
        self.lbl_status_visual.grid(row=0, column=0, padx=5, pady=5)

        self.lbl_abertura = tk.Label(self.fr_status, text="Abertura: R$ 0.00", font=('Arial', 11), bg=CORES['painel'], fg='white')
        self.lbl_abertura.grid(row=0, column=1, padx=15)

        self.lbl_dinheiro_gaveta = tk.Label(self.fr_status, text="Em Dinheiro: R$ 0.00", font=('Arial', 12, 'bold'), bg=CORES['painel'], fg=CORES['verde'])
        self.lbl_dinheiro_gaveta.grid(row=0, column=2, padx=15)

        self.btn_abrir = tk.Button(self.fr_status, text="🔑 ABRIR CAIXA", bg=CORES['verde'], fg='white', font=('Arial', 9, 'bold'), command=self.janela_abrir_caixa)
        self.btn_abrir.grid(row=0, column=3, padx=5)

        self.btn_sangria = tk.Button(self.fr_status, text="💸 SANGRIA (RETIRAR)", bg=CORES['laranja'], fg='white', font=('Arial', 9, 'bold'), command=self.janela_sangria, state='disabled')
        self.btn_sangria.grid(row=0, column=4, padx=5)

        self.btn_fechar = tk.Button(self.fr_status, text="🔒 FECHAR CAIXA", bg=CORES['vermelho'], fg='white', font=('Arial', 9, 'bold'), command=self.processar_fechamento_caixa, state='disabled')
        self.btn_fechar.grid(row=0, column=5, padx=5)

        tk.Label(self, text="Movimentações Consolidadas do Dia", font=('Arial', 12, 'bold'), bg=CORES['fundo'], fg=CORES['texto']).pack(pady=5)
        
        self.tree_hist = ttk.Treeview(self, columns=('Hora','Tipo','Prod','Total','Pgto'), show='headings')
        self.tree_hist.heading('Hora', text='Hora'); self.tree_hist.column('Hora', width=80)
        self.tree_hist.heading('Tipo', text='Origem'); self.tree_hist.column('Tipo', width=100)
        self.tree_hist.heading('Prod', text='Descrição/Produto'); self.tree_hist.column('Prod', width=250)
        self.tree_hist.heading('Total', text='Total'); self.tree_hist.column('Total', width=90)
        self.tree_hist.heading('Pgto', text='Forma Pgto'); self.tree_hist.column('Pgto', width=130)
        self.tree_hist.pack(fill='both', expand=True, padx=10, pady=5)
        
        self.lbl_fat = tk.Label(self, text="FATURAMENTO TOTAL HOJE: R$ 0.00", font=('Arial', 14, 'bold'), fg=CORES['amarelo'], bg=CORES['fundo'])
        self.lbl_fat.pack(pady=5)
        
        fr_botoes = tk.Frame(self, bg=CORES['fundo']); fr_botoes.pack(pady=5)
        tk.Button(fr_botoes, text="🔄 Atualizar Painel", command=self.carregar_historico, font=('Arial', 10)).pack(side='left', padx=10)
        tk.Button(fr_botoes, text="📄 SALVAR RELATÓRIO DO DIA", bg=CORES['azul'], fg='white', font=('Arial', 10, 'bold'), command=self.salvar_relatorio_txt).pack(side='left', padx=10)

    def verificar_status_caixa(self):
        dt_hoje = datetime.now().strftime("%Y-%m-%d")
        conn = sqlite3.connect(DB_NAME)
        caixa = conn.cursor().execute("SELECT id, valor_abertura FROM controle_caixa WHERE data=? AND status='ABERTO'", (dt_hoje,)).fetchone()
        conn.close()

        if  caixa:
            self.caixa_id_atual = caixa[0]; self.caixa_aberto = True
            self.lbl_status_visual.config(text="CAIXA ABERTO", bg=CORES['verde'])
            self.lbl_abertura.config(text=f"Abertura: R$ {caixa[1]:.2f}")
            self.btn_abrir.config(state='disabled'); self.btn_sangria.config(state='normal'); self.btn_fechar.config(state='normal')
        else:
            self.caixa_id_atual = None; self.caixa_aberto = False
            self.lbl_status_visual.config(text="CAIXA FECHADO", bg=CORES['vermelho'])
            self.lbl_abertura.config(text="Abertura: R$ 0.00")
            self.btn_abrir.config(state='normal'); self.btn_sangria.config(state='disabled'); self.btn_fechar.config(state='disabled')
        self.carregar_historico()

    def janela_abrir_caixa(self):
        janela = tk.Toplevel(self); janela.title("Abertura"); janela.geometry("320x160"); janela.configure(bg=CORES['painel'])
        tk.Label(janela, text="Fundo de Troco Inicial (R$):", bg=CORES['painel'], fg='white', font=('Arial', 11)).pack(pady=15)
        ent_valor = tk.Entry(janela, font=('Arial', 12), width=15, justify='center'); ent_valor.insert(0, "100.00"); ent_valor.pack(); ent_valor.focus_set()
        def confirmar():
            try: valor = float(ent_valor.get().replace(',', '.'))
            except: return
            dt_hoje = datetime.now().strftime("%Y-%m-%d")
            conn = sqlite3.connect(DB_NAME)
            conn.cursor().execute("INSERT INTO controle_caixa (data, valor_abertura, valor_fechamento, status) VALUES (?,?,?,?)", (dt_hoje, valor, 0.0, 'ABERTO'))
            conn.commit(); conn.close(); janela.destroy(); self.verificar_status_caixa()
        tk.Button(janela, text="ABRIR", bg=CORES['verde'], fg='white', command=confirmar).pack(pady=15)
        janela.update(); janela.grab_set()

    def janela_sangria(self):
        janela = tk.Toplevel(self); janela.title("Sangria"); janela.geometry("350x200"); janela.configure(bg=CORES['painel'])
        tk.Label(janela, text="Valor da Retirada (R$):", bg=CORES['painel'], fg='white').pack()
        ent_valor = tk.Entry(janela, justify='center'); ent_valor.pack()
        tk.Label(janela, text="Motivo:", bg=CORES['painel'], fg='white').pack()
        ent_motivo = tk.Entry(janela, justify='center'); ent_motivo.pack()
        def confirmar():
            try: val = float(ent_valor.get().replace(',','.')); mot = ent_motivo.get().strip().upper()
            except: return
            if val <=0 or not mot: return
            conn = sqlite3.connect(DB_NAME); dt = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            # Inserido na tabela avulsa de balcão com sinal negativo de dinheiro para dedução limpa
            conn.cursor().execute("INSERT INTO vendas_balcao (produto_nome, qtd, total, data_hora, pagamento) VALUES (?,?,?,?,?)", (f"[SANGRIA] {mot}", 1, -val, dt, 'DINHEIRO'))
            conn.commit(); conn.close(); janela.destroy(); self.carregar_historico()
        tk.Button(janela, text="RETIRAR", bg=CORES['vermelho'], fg='white', command=confirmar).pack(pady=15)
        janela.update(); janela.grab_set()

    def carregar_historico(self):
        self.tree_hist.delete(*self.tree_hist.get_children())
        dt_hoje = datetime.now().strftime("%Y-%m-%d")
        faturamento_total = 0.0
        dinheiro_em_gaveta = 0.0

        conn = sqlite3.connect(DB_NAME)
        abertura = conn.cursor().execute("SELECT valor_abertura FROM controle_caixa WHERE id=?", (self.caixa_id_atual,)).fetchone()[0] if self.caixa_id_atual else 0.0
        
        # 1. Carrega o faturamento das Mesas Fechadas no dia
        mesas = conn.cursor().execute(
            "SELECT data_fechamento, id, mesa_id, pagamento, (SELECT SUM(total) FROM itens_atendimento WHERE atendimento_id=atendimentos.id) FROM atendimentos WHERE status='FECHADO' AND data_fechamento LIKE ?", (f"{dt_hoje}%",)
        ).fetchall()
        
        # 2. Carrega as movimentações do Balcão e Sangrias
        balcao = conn.cursor().execute("SELECT data_hora, produto_nome, total, pagamento FROM vendas_balcao WHERE data_hora LIKE ?", (f"{dt_hoje}%",)).fetchall()
        conn.close()

        # Injeta Mesas na interface
        for m in mesas:
            hora = m[0].split(' ')[1]; total_comanda = m[4] if m[4] else 0.0
            self.tree_hist.insert('', 'end', values=(hora, f"Mesa {m[2]}", f"Comanda Finalizada nº {m[1]}", f"{total_comanda:.2f}", m[3]))
            if total_comanda > 0: faturamento_total += total_comanda
            if m[3] == "DINHEIRO": dinheiro_em_gaveta += total_comanda

        # Injeta Balcão na interface
        for b in balcao:
            hora = b[0].split(' ')[1]
            origem = "RETIRADA" if "[SANGRIA]" in b[1] else "BALCÃO"
            self.tree_hist.insert('', 'end', values=(hora, origem, b[1], f"{b[2]:.2f}", b[3]))
            if b[2] > 0 and "[SANGRIA]" not in b[1]: faturamento_total += b[2]
            if b[3] == "DINHEIRO": dinheiro_em_gaveta += b[2]

        self.lbl_fat.config(text=f"FATURAMENTO BRUTO HOJE: R$ {faturamento_total:.2f}")
        self.lbl_dinheiro_gaveta.config(text=f"Dinheiro na Gaveta: R$ {(abertura + dinheiro_em_gaveta):.2f}")

    def processar_fechamento_caixa(self):
        self.carregar_historico()
        if messagebox.askyesno("Fechar Caixa", "Deseja encerrar e blindar as movimentações do dia?"):
            conn = sqlite3.connect(DB_NAME)
            conn.cursor().execute("UPDATE controle_caixa SET status='FECHADO' WHERE id=?", (self.caixa_id_atual,))
            conn.commit(); conn.close(); self.verificar_status_caixa()

    def salvar_relatorio_txt(self): 
        messagebox.showinfo("Sucesso", "Dados consolidados no banco!")