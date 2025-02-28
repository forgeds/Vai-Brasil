from enviodeboletos import AutomacaoBoletos
import json
import os

def setup_test_data():
    """Criar dados de teste"""
    test_data = {
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
                'vencimento': '2025-03-15',
                'valor': 1000.00,
                'paid': False
            }
        ]
    }
    
    # Salvar dados de teste
    with open('parcelas.json', 'w', encoding='utf-8') as f:
        json.dump(test_data, f, ensure_ascii=False, indent=2)
    
    return test_data

def test_automacao():
    """Testar principais funcionalidades"""
    print("Iniciando testes...")
    
    # 1. Criar instância da classe
    automacao = AutomacaoBoletos()
    print("✓ Classe inicializada")
    
    # 2. Testar carregamento de dados
    dados = automacao.carregar_dados()
    if dados and 'parcelas' in dados:
        print("✓ Carregamento de dados OK")
    else:
        print("✗ Erro no carregamento de dados")
    
    # 3. Testar histórico
    historico = automacao.carregar_historico()
    if isinstance(historico, dict):
        print("✓ Carregamento de histórico OK")
    else:
        print("✗ Erro no carregamento de histórico")
    
    # 4. Testar processamento de boletos
    try:
        automacao.processar_boletos()
        print("✓ Processamento de boletos OK")
    except Exception as e:
        print(f"✗ Erro no processamento de boletos: {e}")
    
    # 5. Testar busca de boletos
    parcela_teste = dados['parcelas'][0]
    boleto = automacao.encontrar_boleto(parcela_teste)
    print(f"✓ Busca de boleto: {boleto if boleto else 'Não encontrado (esperado)'}")

def cleanup():
    """Limpar arquivos de teste"""
    files = ['parcelas.json', 'historico_envios.json']
    for file in files:
        if os.path.exists(file):
            os.remove(file)
    print("\nArquivos de teste removidos")

if __name__ == "__main__":
    print("=== Teste Manual do Sistema de Automação de Boletos ===\n")
    
    # Criar dados de teste
    test_data = setup_test_data()
    print("Dados de teste criados")
    
    # Executar testes
    test_automacao()
    
    # Limpar arquivos de teste
    cleanup()
    
    print("\nTestes concluídos!")