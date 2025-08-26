import ccxt
import pandas as pd
import datetime
import requests
import os
import logging
from ta.trend import EMAIndicator, MACD, ADXIndicator
from ta.momentum import RSIIndicator
from ta.volatility import AverageTrueRange
from ta.volume import OnBalanceVolumeIndicator

# ===============================
# === CONFIGURAÇÕES GITHUB ACTIONS
# ===============================

# Pares para monitorar
PARES_ALVOS = ['BTC/USDT', 'ETH/USDT']
timeframe = '4h'
limite_candles = 100

# Configurações do Telegram (vindas dos GitHub Secrets)
TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

# Verificar se variáveis estão configuradas
if not TOKEN or not CHAT_ID:
    print("❌ ERRO: Configure TELEGRAM_BOT_TOKEN e TELEGRAM_CHAT_ID nos GitHub Secrets")
    exit(1)

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')

# ===============================
# === CONTROLE DE ALERTAS (SIMPLES)
# ===============================

# Arquivo para controlar alertas (GitHub Actions tem workspace temporário)
ARQUIVO_ALERTAS = 'last_alerts.txt'
TEMPO_REENVIO = 60 * 60  # 1 hora entre alertas do mesmo setup

def pode_enviar_alerta(par, setup):
    """Controle simples de reenvio - evita spam"""
    chave = f"{par}_{setup}"
    agora = datetime.datetime.utcnow()
    
    try:
        # Tentar ler últimos alertas
        if os.path.exists(ARQUIVO_ALERTAS):
            with open(ARQUIVO_ALERTAS, 'r') as f:
                lines = f.readlines()
                for line in lines:
                    if chave in line:
                        timestamp_str = line.split('|')[1].strip()
                        ultimo_alerta = datetime.datetime.fromisoformat(timestamp_str)
                        if (agora - ultimo_alerta).total_seconds() < TEMPO_REENVIO:
                            return False
    except Exception:
        pass  # Se houver erro, permite envio
    
    # Registrar novo alerta
    with open(ARQUIVO_ALERTAS, 'a') as f:
        f.write(f"{chave}|{agora.isoformat()}\n")
    
    return True

# ===============================
# === DADOS FUNDAMENTAIS
# ===============================

def obter_dados_fundamentais():
    """Dados do mercado crypto para contexto"""
    try:
        response = requests.get("https://api.coingecko.com/api/v3/global", timeout=10)
        market_data = response.json().get('data', {})
        
        market_cap = market_data.get('total_market_cap', {}).get('usd')
        market_cap_change = market_data.get('market_cap_change_percentage_24h_usd', 0)
        btc_dominance = market_data.get('market_cap_percentage', {}).get('btc')
        
        if market_cap and btc_dominance:
            def abreviar_valor(valor):
                if valor >= 1_000_000_000_000:
                    return f"${valor/1_000_000_000_000:.2f}T"
                elif valor >= 1_000_000_000:
                    return f"${valor/1_000_000_000:.2f}B"
                return f"${valor/1_000_000:.0f}M"
            
            emoji_cap = "📈" if market_cap_change >= 0 else "📉"
            
            try:
                fear_response = requests.get("https://api.alternative.me/fng/?limit=1", timeout=5)
                fear_data = fear_response.json()['data'][0]
                fear_greed = f"{fear_data['value']} ({fear_data['value_classification']})"
            except:
                fear_greed = "N/A"
            
            return (
                f"🌍 *MERCADO CRIPTO:*\n"
                f"• Cap Total: {abreviar_valor(market_cap)} {emoji_cap} ({market_cap_change:+.1f}%)\n"
                f"• Domínio BTC: {btc_dominance:.1f}%\n"
                f"• Fear & Greed: {fear_greed}"
            )
    except Exception as e:
        logging.warning(f"Erro nos dados fundamentais: {e}")
    
    return "⚠️ *Dados de mercado indisponíveis*"
  # ===============================
# === INDICADORES TÉCNICOS
# ===============================

def calcular_supertrend(df, period=10, multiplier=3):
    """Cálculo manual do Supertrend (sem pandas_ta)"""
    try:
        high = df['high']
        low = df['low']
        close = df['close']
        
        # ATR
        atr = AverageTrueRange(high, low, close, period).average_true_range()
        
        # Bandas básicas
        hl2 = (high + low) / 2
        upper_band = hl2 + (multiplier * atr)
        lower_band = hl2 - (multiplier * atr)
        
        # Lógica simples do Supertrend
        supertrend = []
        direction = []
        
        for i in range(len(df)):
            if i == 0:
                supertrend.append(lower_band.iloc[i])
                direction.append(1)
            else:
                if close.iloc[i] > supertrend[i-1]:
                    direction.append(1)
                    supertrend.append(lower_band.iloc[i])
                else:
                    direction.append(-1) 
                    supertrend.append(upper_band.iloc[i])
        
        df['supertrend'] = [d > 0 for d in direction]
        return df
        
    except Exception as e:
        logging.warning(f"Erro no Supertrend: {e}")
        df['supertrend'] = [True] * len(df)  # Fallback
        return df

def detectar_candle_forte(df):
    """Detecta candle com corpo forte vs sombras"""
    if len(df) < 2:
        return False
    
    candle = df.iloc[-1]
    corpo = abs(candle['close'] - candle['open'])
    sombra_sup = candle['high'] - max(candle['close'], candle['open'])
    sombra_inf = min(candle['close'], candle['open']) - candle['low']
    
    return corpo > (sombra_sup * 1.5) and corpo > (sombra_inf * 1.5)

def detectar_engolfo_alta(df):
    """Detecta padrão de engolfo de alta"""
    if len(df) < 2:
        return False
    
    atual = df.iloc[-1]
    anterior = df.iloc[-2]
    
    return (atual['close'] > atual['open'] and  # Atual de alta
            anterior['close'] < anterior['open'] and  # Anterior de baixa  
            atual['open'] < anterior['close'] and  # Abertura atual < fechamento anterior
            atual['close'] > anterior['open'])  # Fechamento atual > abertura anterior

# ===============================
# === SETUPS DE TRADING
# ===============================

def verificar_setup_github_conservador(r, df):
    """Setup conservador otimizado para GitHub Actions"""
    condicoes = [
        r['rsi'] < 45,
        r['ema9'] > r['ema21'],
        r['macd'] > r['macd_signal'],
        r['adx'] > 18,
        df['volume'].iloc[-1] > df['volume'].mean() * 1.2,
        r['close'] > r['ema200'],
        df['supertrend'].iloc[-1] == True
    ]
    
    if sum(condicoes) >= 5:
        return {
            'setup': '🛡️ SETUP CONSERVADOR',
            'prioridade': '🟢 ALTA QUALIDADE',
            'emoji': '🛡️',
            'id': 'conservador_gh'
        }
    return None

def verificar_setup_github_momentum(r, df):
    """Setup de momentum para capturas rápidas"""
    condicoes = [
        r['rsi'] > 35 and r['rsi'] < 65,  # RSI em zona neutra
        r['ema9'] > r['ema21'],
        r['macd'] > r['macd_signal'],
        df['volume'].iloc[-1] > df['volume'].mean() * 1.5,  # Volume forte
        detectar_candle_forte(df) or detectar_engolfo_alta(df),
        r['adx'] > 15
    ]
    
    if sum(condicoes) >= 4:
        return {
            'setup': '⚡ SETUP MOMENTUM',
            'prioridade': '🟡 OPORTUNIDADE RÁPIDA', 
            'emoji': '⚡',
            'id': 'momentum_gh'
        }
    return None

def verificar_setup_github_reversao(r, df):
    """Setup de reversão em correções"""
    if len(df) < 5:
        return None
    
    # Verificar correção recente
    preco_max_recente = df['close'].iloc[-5:].max()
    correcao_detectada = r['close'] < preco_max_recente * 0.97
    
    condicoes = [
        r['rsi'] < 35,  # Sobrevenda
        correcao_detectada,  # Houve correção
        detectar_engolfo_alta(df),  # Padrão de reversão
        r['obv'] > df['obv'].iloc[-10:].mean(),  # OBV ainda positivo
        df['volume'].iloc[-1] > df['volume'].mean() * 1.3
    ]
    
    if sum(condicoes) >= 3:
        return {
            'setup': '🔄 SETUP REVERSÃO',
            'prioridade': '🟠 CONTRA-TENDÊNCIA',
            'emoji': '🔄', 
            'id': 'reversao_gh'
        }
    return None
  def calcular_score_setup(r, df, setup_id):
    """Score de qualidade do setup (0-10)"""
    score = 0
    total = 10  # Score máximo
    
    # Critérios básicos (1 ponto cada)
    if r['rsi'] > 25 and r['rsi'] < 70: score += 1
    if r['ema9'] > r['ema21']: score += 1
    if r['macd'] > r['macd_signal']: score += 1
    if df['volume'].iloc[-1] > df['volume'].mean(): score += 1
    
    # Critérios importantes (1.5 pontos cada)
    if r['adx'] > 20: score += 1.5
    if r['close'] > r['ema200']: score += 1.5
    if df['supertrend'].iloc[-1]: score += 1.5
    
    # Critérios especiais (2 pontos cada)
    if detectar_candle_forte(df): score += 2
    if df['volume'].iloc[-1] > df['volume'].mean() * 1.5: score += 2
    
    return round(score, 1)

# ===============================
# === COMUNICAÇÃO TELEGRAM
# ===============================

def enviar_telegram(mensagem):
    """Envia mensagem para o Telegram"""
    if not TOKEN or TOKEN == "dummy_token":
        print(f"[TELEGRAM SIMULADO] {mensagem}")
        return True
    
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = {
        "chat_id": CHAT_ID,
        "text": mensagem,
        "parse_mode": "Markdown",
        "disable_web_page_preview": True
    }
    
    try:
        response = requests.post(url, data=payload, timeout=10)
        if response.status_code == 200:
            return True
        else:
            logging.error(f"Erro Telegram: {response.text}")
            return False
    except Exception as e:
        logging.error(f"Erro ao enviar Telegram: {e}")
        return False

def enviar_alerta_github(par, r, setup_info, df):
    """Envia alerta otimizado para GitHub Actions"""
    preco = r['close']
    atr = r['atr']
    
    # Cálculo de alvos adaptativos
    if par == 'BTC/USDT':
        stop = round(preco - (atr * 1.2), 2)
        alvo = round(preco + (atr * 2.5), 2)
    else:  # ETH/USDT
        stop = round(preco - (atr * 1.5), 2) 
        alvo = round(preco + (atr * 3.0), 2)
    
    # Score do setup
    score = calcular_score_setup(r, df, setup_info.get('id', ''))
    
    # Timestamp
    agora_utc = datetime.datetime.utcnow()
    agora_local = agora_utc - datetime.timedelta(hours=3)  # Brasília
    timestamp = agora_local.strftime('%d/%m %H:%M')
    
    # Dados fundamentais
    resumo_mercado = obter_dados_fundamentais()
    
    # Construir mensagem
    mensagem = (
        f"{setup_info['emoji']} *{setup_info['setup']}*\n"
        f"{setup_info['prioridade']}\n\n"
        f"📊 *Par:* `{par}`\n"
        f"💰 *Preço:* `${preco:,.2f}`\n"
        f"🎯 *Alvo:* `${alvo:,.2f}`\n"
        f"🛑 *Stop:* `${stop:,.2f}`\n"
        f"⭐ *Score:* `{score}/10`\n\n"
        f"📈 *Indicadores Técnicos:*\n"
        f"• RSI: {r['rsi']:.1f}\n"
        f"• MACD: {'✅' if r['macd'] > r['macd_signal'] else '❌'}\n"
        f"• ADX: {r['adx']:.1f}\n"
        f"• Volume: {r['volume']:,.0f}\n"
        f"• ATR: ${r['atr']:.2f}\n\n"
        f"🕒 *GitHub Actions:* {timestamp}\n"
        f"🤖 *Executado a cada 15min*\n\n"
        f"{resumo_mercado}\n\n"
        f"📋 *Análise:*\n"
        f"• Tendência: {'Alta' if r['ema9'] > r['ema21'] else 'Baixa'}\n"
        f"• Força: {'💪' if r['adx'] > 20 else '👤'}\n"
        f"• Momentum: {'🚀' if df['volume'].iloc[-1] > df['volume'].mean() * 1.2 else '😴'}\n"
        f"• Supertrend: {'🟢' if df['supertrend'].iloc[-1] else '🔴'}"
    )
    
    # Adicionar explicação para iniciantes
    if score >= 7.5:
        mensagem += f"\n\n💡 *Setup de alta qualidade* com múltiplos indicadores alinhados!"
    elif score >= 6:
        mensagem += f"\n\n⚖️ *Setup moderado* - requer mais confirmação antes de operar."
    else:
        mensagem += f"\n\n⚠️ *Setup fraco* - aguardar melhores oportunidades."
    
    # Enviar se permitido
    if pode_enviar_alerta(par, setup_info['setup']):
        if enviar_telegram(mensagem):
            logging.info(f"✅ Alerta enviado: {par} - {setup_info['setup']} (score: {score})")
            print(f"✅ ALERTA: {par} - {setup_info['setup']} (score: {score})")
            return True
        else:
            logging.error(f"❌ Falha ao enviar: {par} - {setup_info['setup']}")
            return False
    else:
        logging.info(f"⏳ Alerta recente ignorado: {par} - {setup_info['setup']}")
        return False

# ===============================
# === ANÁLISE PRINCIPAL
# ===============================

def analisar_par_github(exchange, par):
    """Análise otimizada para GitHub Actions"""
    try:
        print(f"🔍 Analisando {par}...")
        
        # Buscar dados OHLCV
        ohlcv = exchange.fetch_ohlcv(par, timeframe, limit=limite_candles)
        if len(ohlcv) < limite_candles:
            print(f"⚠️ Dados insuficientes para {par}")
            return None
        
        # Criar DataFrame
        df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        
        # Calcular indicadores
        close = df['close']
        high = df['high']
        low = df['low']
        volume = df['volume']
        
        df['ema9'] = EMAIndicator(close, 9).ema_indicator()
        df['ema21'] = EMAIndicator(close, 21).ema_indicator()
        df['ema200'] = EMAIndicator(close, 200).ema_indicator()
        df['rsi'] = RSIIndicator(close, 14).rsi()
        df['atr'] = AverageTrueRange(high, low, close, 14).average_true_range()
        
        macd = MACD(close)
        df['macd'] = macd.macd()
        df['macd_signal'] = macd.macd_signal()
        
        df['adx'] = ADXIndicator(high, low, close, 14).adx()
        df['obv'] = OnBalanceVolumeIndicator(close, volume).on_balance_volume()
        
        df = calcular_supertrend(df)
        
        # Verificar se temos dados suficientes
        if df['ema200'].isna().any() or df['adx'].isna().any():
            print(f"⚠️ Indicadores incompletos para {par}")
            return None
        
        # Dados da linha atual
        r = df.iloc[-1]
        
        # Verificar setups em ordem de prioridade
        setups = [
            verificar_setup_github_conservador,
            verificar_setup_github_momentum, 
            verificar_setup_github_reversao
        ]
        
        for verificar_setup in setups:
            setup_info = verificar_setup(r, df)
            if setup_info:
                return enviar_alerta_github(par, r, setup_info, df)
        
        print(f"   💭 {par}: Nenhum setup detectado")
        return None
        
    except Exception as e:
        logging.error(f"❌ Erro na análise de {par}: {e}")
        print(f"❌ Erro com {par}: {e}")
        return None

# ===============================
# === FUNÇÃO PRINCIPAL
# ===============================

def executar_scanner_github():
    """Função principal do scanner GitHub Actions"""
    try:
        print("🚀 INICIANDO SCANNER GITHUB ACTIONS")
        print(f"⏰ Executado em: {datetime.datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}")
        print(f"📊 Pares: {', '.join(PARES_ALVOS)}")
        print(f"📈 Timeframe: {timeframe}")
        
        # Inicializar exchange
        exchange = ccxt.okx({'enableRateLimit': True})
        exchange.load_markets()
        
        # Verificar se pares existem
        for par in PARES_ALVOS:
            if par not in exchange.markets:
                print(f"❌ Par {par} não encontrado na OKX")
                continue
        
        # Analisar cada par
        alertas_enviados = 0
        for par in PARES_ALVOS:
            if par in exchange.markets:
                resultado = analisar_par_github(exchange, par)
                if resultado:
                    alertas_enviados += 1
        
        # Resumo final
        print(f"\n✅ SCANNER FINALIZADO")
        print(f"📨 Alertas enviados: {alertas_enviados}")
        print(f"🕒 Próxima execução: em 15 minutos")
        
        # Enviar resumo se não houve alertas
        if alertas_enviados == 0:
            agora = datetime.datetime.utcnow().strftime('%H:%M UTC')
            mensagem_resumo = (
                f"🤖 *Scanner GitHub Actions*\n\n"
                f"⏰ Executado às {agora}\n"
                f"📊 Pares analisados: {', '.join(PARES_ALVOS)}\n"
                f"📈 Status: Mercado sem sinais claros\n"
                f"🔄 Próxima verificação: 15 minutos\n\n"
                f"💤 *Aguardando oportunidades...*"
            )
            
            # Enviar resumo apenas uma vez por hora (para não spam)
            hora_atual = datetime.datetime.utcnow().hour
            if hora_atual % 4 == 0:  # A cada 4 horas
                enviar_telegram(mensagem_resumo)
        
        return True
        
    except Exception as e:
        logging.error(f"❌ Erro crítico no scanner: {e}")
        print(f"❌ ERRO CRÍTICO: {e}")
        
        # Enviar alerta de erro
        if TOKEN and TOKEN != "dummy_token":
            mensagem_erro = (
                f"🚨 *ERRO NO SCANNER*\n\n"
                f"❌ {str(e)[:100]}...\n"
                f"⏰ {datetime.datetime.utcnow().strftime('%H:%M UTC')}\n"
                f"🔧 Verifique os logs do GitHub Actions"
            )
            enviar_telegram(mensagem_erro)
        
        return False

# ===============================
# === EXECUÇÃO
# ===============================

if __name__ == "__main__":
    # Executar scanner
    sucesso = executar_scanner_github()
    
    if sucesso:
        print("🎉 Scanner executado com sucesso!")
        exit(0)
    else:
        print("💥 Scanner falhou!")
        exit(1)
