import unittest
from unittest.mock import Mock, patch
import json
import os
from datetime import datetime, timedelta
from enviodeboletos import AutomacaoBoletos

class TestAutomacaoBoletos(unittest.TestCase):
    def setUp(self):
        """Setup for each test"""
        # Create test data with a vencimento date exactly 15 days from now
        hoje = datetime.now()
        data_vencimento = hoje + timedelta(days=15)
        
        self.dados_teste = {
            'parcelas': [{
                'id': '1',
                'contrato_id': '123',
                'nome': 'Test User',
                'cpf': '12345678900',
                'telefone': '11999999999',
                'contrato': 'CONT001',
                'parcela': 1,
                'total_parcelas': 3,
                'vencimento': data_vencimento.strftime('%Y-%m-%d'),
                'valor': 1000.00,
                'paid': False
            }]
        }
        
        # Save test data
        with open('parcelas.json', 'w', encoding='utf-8') as f:
            json.dump(self.dados_teste, f)
            
        self.automacao = AutomacaoBoletos()

    def tearDown(self):
        """Cleanup after each test"""
        files = ['parcelas.json', 'historico_envios.json']
        for file in files:
            if os.path.exists(file):
                os.remove(file)
                
        # Remove test directory if exists
        pasta_cliente = os.path.join(self.automacao.base_path, 'Test User')
        if os.path.exists(pasta_cliente):
            # Remove files inside folder
            for arquivo in os.listdir(pasta_cliente):
                os.remove(os.path.join(pasta_cliente, arquivo))
            os.rmdir(pasta_cliente)

    def test_carregar_dados(self):
        """Test data loading"""
        dados = self.automacao.carregar_dados()
        self.assertEqual(dados['parcelas'][0]['nome'], 'Test User')
        self.assertEqual(len(dados['parcelas']), 1)

    def test_carregar_historico(self):
        """Test history loading"""
        historico = self.automacao.carregar_historico()
        self.assertIsInstance(historico, dict)

    @patch('selenium.webdriver.Chrome')
    def test_iniciar_whatsapp(self, mock_chrome):
        """Test WhatsApp initialization"""
        # Configure mock
        mock_driver = Mock()
        mock_chrome.return_value = mock_driver
        
        # Mock input function
        with patch('builtins.input', return_value=''):
            resultado = self.automacao.iniciar_whatsapp()
            self.assertTrue(resultado)
            mock_chrome.assert_called_once()

    def test_encontrar_boleto(self):
        """Test invoice finding"""
        parcela = self.dados_teste['parcelas'][0]
        
        # Create test directory and file
        pasta_cliente = os.path.join(self.automacao.base_path, parcela['nome'])
        os.makedirs(pasta_cliente, exist_ok=True)
        
        mes_vencimento = datetime.strptime(parcela['vencimento'], '%Y-%m-%d').strftime('%B%Y')
        caminho_boleto = os.path.join(pasta_cliente, f"{mes_vencimento}.pdf")
        
        with open(caminho_boleto, 'w') as f:
            f.write('test')
        
        # Test finding
        resultado = self.automacao.encontrar_boleto(parcela)
        self.assertEqual(resultado, caminho_boleto)

    @patch('enviodeboletos.AutomacaoBoletos.enviar_aviso_inicial')
    def test_processar_boletos(self, mock_enviar):
        """Test invoice processing"""
        # Configure mock
        mock_enviar.return_value = True
        
        # Set test data with vencimento exactly 15 days from now
        hoje = datetime.now()
        data_vencimento = hoje + timedelta(days=15)
        self.dados_teste['parcelas'][0]['vencimento'] = data_vencimento.strftime('%Y-%m-%d')
        self.dados_teste['parcelas'][0]['paid'] = False  # Ensure it's not marked as paid
        
        # Set test data in the automation instance
        self.automacao.dados = self.dados_teste
        
        # Clear history to ensure method will be called
        self.automacao.historico_envios = {}
        
        # Process invoices
        self.automacao.processar_boletos()
        
        # Verify send_message was called once
        mock_enviar.assert_called_once()

    def test_formatacao_mensagem(self):
        """Test message formatting"""
        parcela = self.dados_teste['parcelas'][0]
        
        # Test initial message
        mensagem = (
            f"Olá, {parcela['nome']} aqui é o Edson da Vai Brasil segue em anexo o seu "
            f"boleto referente aos bloquetes do dia {datetime.strptime(parcela['vencimento'], '%Y-%m-%d').strftime('%d')} "
            f"do mês {datetime.strptime(parcela['vencimento'], '%Y-%m-%d').strftime('%B')}"
        )
        
        self.assertIn(parcela['nome'], mensagem)
        self.assertIn('Edson da Vai Brasil', mensagem)

if __name__ == '__main__':
    unittest.main(verbosity=2)