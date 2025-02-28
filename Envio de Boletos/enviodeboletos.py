import os
import json
import time
from datetime import datetime, timedelta
from selenium import webdriver
from selenium.webdriver.chrome.options import Options  # Changed from Edge to Chrome
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import schedule

class AutomacaoBoletos:
    def __init__(self):
        self.driver = None
        self.base_path = "contratos/"
        self.dados = self.carregar_dados()
        self.historico_envios = self.carregar_historico()

    def carregar_dados(self):
        """Carrega dados das parcelas do localStorage"""
        try:
            with open('parcelas.json', 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            return {'parcelas': []}

    def carregar_historico(self):
        """Carrega histórico de envios"""
        try:
            with open('historico_envios.json', 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            return {}

    def salvar_historico(self):
        """Salva histórico de envios"""
        with open('historico_envios.json', 'w') as f:
            json.dump(self.historico_envios, f)

    def iniciar_whatsapp(self):
        """Inicia o Chrome e faz login no WhatsApp Web"""
        try:
            # Configurar opções do Chrome
            chrome_options = Options()
            chrome_options.add_experimental_option("useAutomationExtension", False)
            chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
            
            # Iniciar Chrome WebDriver - forma simplificada sem passar timeout
            self.driver = webdriver.Chrome(options=chrome_options)
            self.driver.set_page_load_timeout(30)  # 30 segundos de timeout
            self.driver.maximize_window()
            self.driver.get("https://web.whatsapp.com")
            
            print("Por favor, escaneie o código QR do WhatsApp Web")
            input("Após fazer o login, pressione Enter para continuar...")
            return True
        except Exception as e:
            print(f"Erro ao iniciar o Chrome: {e}")
            return False

    def encontrar_boleto(self, parcela):
        """Encontra o boleto do cliente"""
        mes_vencimento = datetime.strptime(parcela['vencimento'], '%Y-%m-%d').strftime('%B%Y')
        pasta_cliente = os.path.join(self.base_path, parcela['nome'])
        nome_arquivo = f"{mes_vencimento}.pdf"
        caminho_boleto = os.path.join(pasta_cliente, nome_arquivo)
        
        return caminho_boleto if os.path.exists(caminho_boleto) else None

    def processar_boletos(self):
        """Processa os boletos e envia mensagens conforme regras definidas"""
        hoje = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        
        for parcela in self.dados['parcelas']:
            if parcela.get('paid', False):
                continue

            data_vencimento = datetime.strptime(parcela['vencimento'], '%Y-%m-%d')
            dias_ate_vencimento = (data_vencimento - hoje).days
            
            if not parcela.get('contrato_id'):
                continue

            chave_historico = f"{parcela['id']}_{hoje.strftime('%Y%m%d')}"
            if chave_historico in self.historico_envios:
                continue

            # Enviar boleto 15 dias antes do vencimento
            if dias_ate_vencimento == 15:
                if self.enviar_aviso_inicial(parcela):
                    self.historico_envios[chave_historico] = datetime.now().isoformat()
                    self.salvar_historico()
            
            # Avisar a cada 5 dias antes do vencimento (10, 5 dias)
            elif dias_ate_vencimento > 0 and dias_ate_vencimento % 5 == 0:
                if self.enviar_aviso_vencimento(parcela):
                    self.historico_envios[chave_historico] = datetime.now().isoformat()
                    self.salvar_historico()
            
            # Avisar no dia do vencimento
            elif dias_ate_vencimento == 0:
                if self.enviar_aviso_dia_vencimento(parcela):
                    self.historico_envios[chave_historico] = datetime.now().isoformat()
                    self.salvar_historico()
            
            # Avisar a cada 5 dias após vencer (5, 10, 15... dias de atraso)
            elif dias_ate_vencimento < 0 and abs(dias_ate_vencimento) % 5 == 0:
                if self.enviar_aviso_atraso(parcela):
                    self.historico_envios[chave_historico] = datetime.now().isoformat()
                    self.salvar_historico()

    def enviar_mensagem(self, parcela, mensagem, anexar_boleto=False):
        """Envia mensagem pelo WhatsApp"""
        try:
            numero = f"55{parcela['telefone'].replace('(','').replace(')','').replace('-','').replace(' ','')}"
            url = f"https://web.whatsapp.com/send?phone={numero}"
            
            self.driver.get(url)
            WebDriverWait(self.driver, 20).until(
                EC.presence_of_element_located((By.XPATH, '//div[@contenteditable="true"]'))
            )

            campo_mensagem = self.driver.find_element(By.XPATH, '//div[@contenteditable="true"]')
            campo_mensagem.send_keys(mensagem)
            campo_mensagem.send_keys("\n")

            if anexar_boleto:
                boleto = self.encontrar_boleto(parcela)
                if boleto:
                    input_arquivo = self.driver.find_element(By.CSS_SELECTOR, 'input[type="file"]')
                    input_arquivo.send_keys(boleto)
                    time.sleep(2)
                    botao_enviar = self.driver.find_element(By.XPATH, '//span[@data-icon="send"]')
                    botao_enviar.click()

            time.sleep(3)
            return True
        except Exception as e:
            print(f"Erro ao enviar mensagem: {e}")
            return False

    def enviar_aviso_inicial(self, parcela):
        """Envia primeiro aviso com boleto (15 dias antes)"""
        mes_vencimento = datetime.strptime(parcela['vencimento'], '%Y-%m-%d').strftime('%B')
        dia_vencimento = datetime.strptime(parcela['vencimento'], '%Y-%m-%d').strftime('%d')
        
        mensagem = (
            f"Olá, {parcela['nome']} aqui é o Edson da Vai Brasil segue em anexo o seu "
            f"boleto referente aos bloquetes do dia {dia_vencimento} do mês {mes_vencimento}"
        )
        
        return self.enviar_mensagem(parcela, mensagem, anexar_boleto=True)

    def enviar_aviso_vencimento(self, parcela):
        """Envia aviso de vencimento próximo (a cada 5 dias)"""
        mes_vencimento = datetime.strptime(parcela['vencimento'], '%Y-%m-%d').strftime('%B')
        dias_ate_vencimento = (datetime.strptime(parcela['vencimento'], '%Y-%m-%d') - datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)).days
        
        mensagem = (
            f"Olá, {parcela['nome']} aqui é o Edson da Vai Brasil seu boleto referente "
            f"ao mês {mes_vencimento} vai vencer em {dias_ate_vencimento} dias."
        )
        
        return self.enviar_mensagem(parcela, mensagem)

    def enviar_aviso_dia_vencimento(self, parcela):
        """Envia aviso no dia do vencimento"""
        mes_vencimento = datetime.strptime(parcela['vencimento'], '%Y-%m-%d').strftime('%B')
        
        mensagem = (
            f"Olá, {parcela['nome']} aqui é o Edson da Vai Brasil seu boleto referente "
            f"ao mês {mes_vencimento} vence hoje."
        )
        
        return self.enviar_mensagem(parcela, mensagem)

    def enviar_aviso_atraso(self, parcela):
        """Envia aviso de atraso (a cada 5 dias após vencimento)"""
        mes_vencimento = datetime.strptime(parcela['vencimento'], '%Y-%m-%d').strftime('%B')
        dias_atraso = abs((datetime.now().replace(hour=0, minute=0, second=0, microsecond=0) - datetime.strptime(parcela['vencimento'], '%Y-%m-%d')).days)
        
        mensagem = (
            f"Olá, {parcela['nome']} aqui é o Edson da Vai Brasil seu boleto do mês "
            f"{mes_vencimento} está vencido há {dias_atraso} dias, por favor entre em "
            f"contato para negociar com a gente"
        )
        
        return self.enviar_mensagem(parcela, mensagem)

    def executar(self):
        """Executa o processo de automação"""
        if self.iniciar_whatsapp():
            print("WhatsApp Web iniciado com sucesso!")
            schedule.every().day.at("09:00").do(self.processar_boletos)
            
            while True:
                schedule.run_pending()
                time.sleep(60)

if __name__ == "__main__":
    automacao = AutomacaoBoletos()
    automacao.executar()