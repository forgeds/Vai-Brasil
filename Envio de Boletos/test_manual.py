import unittest
from enviodeboletos import AutomacaoBoletos
import json
import os
from datetime import datetime, timedelta

class TestAutomacaoBoletos(unittest.TestCase):
    def setUp(self):
        # Criar dados de teste com vencimento exatamente em 15 dias
        hoje = datetime.now()
        data_vencimento = hoje + timedelta(days=15)
        
        self.dados_teste = {
            'parcelas': [
                {
                    'id': '1',
                    'contrato_id': '123',
                    'nome': 'Teste Cliente',
                    'cpf': '12345678900',
                    'telefone': '11999999999',
                    'contrato': 'CONT001',
                    'parcela': 1,
                    'total_parcelas': 3,
                    'vencimento': data_vencimento.strftime('%Y-%m-%d'),
                    'valor': 1000.00,
                    'paid': False
                }
            ]
        }
        
        # Salvar dados de teste
        with open('parcelas.json', 'w') as f:
            json.dump(self.dados_teste, f)
            
        self.automacao = AutomacaoBoletos()

    def tearDown(self):
        # Limpar arquivos de teste
        if os.path.exists('parcelas.json'):
            os.remove('parcelas.json')
        if os.path.exists('historico_envios.json'):
            os.remove('historico_envios.json')
            
        # Remover diretório de teste se existir
        pasta_cliente = os.path.join(self.automacao.base_path, 'Teste Cliente')
        if os.path.exists(pasta_cliente):
            # Remover arquivos dentro da pasta
            for arquivo in os.listdir(pasta_cliente):
                os.remove(os.path.join(pasta_cliente, arquivo))
            os.rmdir(pasta_cliente)

    def test_carregar_dados(self):
        dados = self.automacao.carregar_dados()
        self.assertEqual(dados['parcelas'][0]['nome'], 'Teste Cliente')
        self.assertEqual(len(dados['parcelas']), 1)

    def test_encontrar_boleto(self):
        parcela = self.dados_teste['parcelas'][0]
        
        # Criar diretório e arquivo de teste
        pasta_cliente = os.path.join(self.automacao.base_path, parcela['nome'])
        os.makedirs(pasta_cliente, exist_ok=True)
        
        mes_vencimento = datetime.strptime(parcela['vencimento'], '%Y-%m-%d').strftime('%B%Y')
        caminho_boleto = os.path.join(pasta_cliente, f"{mes_vencimento}.pdf")
        
        with open(caminho_boleto, 'w') as f:
            f.write('test')
            
        boleto = self.automacao.encontrar_boleto(parcela)
        self.assertEqual(boleto, caminho_boleto)
        
        # Limpeza no tearDown

    def test_processar_boletos(self):
        # Simular processamento
        self.automacao.dados = self.dados_teste
        
        # Limpar histórico para garantir que o método será chamado
        self.automacao.historico_envios = {}
        
        # Patch temporário para o método enviar_aviso_inicial
        original_enviar = self.automacao.enviar_aviso_inicial
        chamado = {'valor': False}
        
        def mock_enviar(parcela):
            chamado['valor'] = True
            return True
            
        try:
            self.automacao.enviar_aviso_inicial = mock_enviar
            self.automacao.processar_boletos()
            self.assertTrue(chamado['valor'], "O método enviar_aviso_inicial deve ser chamado")
        finally:
            self.automacao.enviar_aviso_inicial = original_enviar

    def test_formatacao_mensagem(self):
        parcela = self.dados_teste['parcelas'][0]
        
        # Testar formatação da mensagem inicial
        mensagem = (
            f"Olá, {parcela['nome']} aqui é o Edson da Vai Brasil segue em anexo o seu "
            f"boleto referente aos bloquetes do dia {datetime.strptime(parcela['vencimento'], '%Y-%m-%d').strftime('%d')} "
            f"do mês {datetime.strptime(parcela['vencimento'], '%Y-%m-%d').strftime('%B')}"
        )
        
        self.assertIn(parcela['nome'], mensagem)
        self.assertIn('Edson da Vai Brasil', mensagem)

if __name__ == '__main__':
    unittest.main()