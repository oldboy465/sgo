import socket
from app import create_app
from app.controllers.notas import notas_bp

# Cria a aplicação no modo de desenvolvimento
app = create_app('development')

# Registra o novo módulo de Notas Orçamentárias no sistema
app.register_blueprint(notas_bp)

def get_ip_address():
    """Detecta o IP da máquina local para exibir no terminal."""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        # Não precisa conectar de verdade, apenas para determinar a rota
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"

if __name__ == '__main__':
    # ==========================================================================
    # CONFIGURAÇÃO DE REDE
    # host='0.0.0.0' -> Escuta em todas as placas de rede (Wi-Fi e Cabo)
    # port=5000      -> Porta padrão do Flask
    # ==========================================================================
    
    # Obtém o IP dinamicamente para não precisar alterar hardcoded
    current_ip = get_ip_address()

    print("------------------------------------------------------------------")
    print("🚀 SERVIDOR RODANDO - AGUARDANDO CONEXÕES")
    print("------------------------------------------------------------------")
    print("💻 Acesso Local:     http://localhost:5000")
    print(f"🌍 Acesso na Rede:   http://{current_ip}:5000") 
    print("------------------------------------------------------------------")
    
    # Se der erro de "Address already in use", mude a port para 5001
    app.run(host='0.0.0.0', port=5000, debug=False)