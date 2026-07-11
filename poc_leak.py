import sys
from pathlib import Path

# Adiciona a pasta vendor ao path para simular o ambiente de execução real
sys.path.insert(0, str(Path("vendor")))

from predictor_core.replay import replay, PastView, LookaheadError

def handler_malicioso(past: PastView):
    hoje = past.latest
    asof = past.asof_index
    
    # 1. Acesso legal (Interface pública de slicing -> clampada ao passado)
    historico_legal = past[:]
    
    # 2. Acesso ilegal via interface pública (Bloqueado corretamente)
    try:
        futuro_bloqueado = past[asof + 1]
    except LookaheadError:
        pass # A barreira do __getitem__ funcionou
        
    # 3. O EXPLOIT: Acessando a tupla original por referência interna
    tupla_vazada = past._data
    
    # Lendo o "Oráculo" (o último evento de toda a simulação, independente do asof atual)
    oraculo = tupla_vazada[-1]
    
    print(f"[Passo {asof}] Estamos no evento '{hoje}'. "
          f"Mas eu espiei a tupla e sei que no final vai acontecer um '{oraculo}'!")
    
    return f"Apostei tudo em {hoje} porque sei sobre o {oraculo}"

def testar_vazamento():
    eventos = [
        "Dia 1 (Mercado Calmo)", 
        "Dia 2 (Pequena Alta)", 
        "Dia 3 (Estabilidade)", 
        "Dia 4 (CRASH GLOBAL)"
    ]
    
    print("--- INICIANDO BACKTEST REPLAY ---")
    ledger = replay(eventos, handler_malicioso)
    print("--- BACKTEST CONCLUIDO ---\n")

if __name__ == "__main__":
    testar_vazamento()