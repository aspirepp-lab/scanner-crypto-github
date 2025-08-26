# 🤖 Scanner Crypto ETH/BTC - GitHub Actions

Scanner automático de criptomoedas que monitora **Bitcoin** e **Ethereum** a cada 15 minutos, **100% gratuito** via GitHub Actions!

## 🚀 Como Funciona

- ⏰ **Execução automática** a cada 15 minutos
- 📊 **Monitora BTC/USDT e ETH/USDT** na OKX
- 🔍 **3 tipos de setups** técnicos
- 📱 **Alertas via Telegram** instantâneos
- 🆓 **Totalmente gratuito** para sempre
- 🌐 **Sem servidor** necessário

## 📋 Setups Detectados

### 🛡️ Setup Conservador
- RSI < 45 (sem sobrecompra)
- EMA9 > EMA21 (tendência de alta)
- MACD > Signal (momentum positivo)
- ADX > 18 (tendência definida)
- Volume acima da média
- Preço > EMA200 (tendência de longo prazo)
- Supertrend ativo

### ⚡ Setup Momentum  
- RSI entre 35-65 (zona neutra)
- Volume forte (>50% da média)
- Padrões de candle forte ou engolfo
- MACD e EMAs alinhados

### 🔄 Setup Reversão
- RSI < 35 (sobrevenda)
- Correção recente detectada
- Padrão de reversão (engolfo de alta)
- OBV ainda positivo
- Volume de confirmação

## 📊 Exemplo de Alerta

```
🛡️ SETUP CONSERVADOR
🟢 ALTA QUALIDADE

📊 Par: BTC/USDT
💰 Preço: $67,245.50
🎯 Alvo: $69,128.30
🛑 Stop: $65,891.20
⭐ Score: 8.2/10

📈 Indicadores Técnicos:
• RSI: 38.5
• MACD: ✅
• ADX: 24.1
• Volume: 1,245,678
• ATR: $625.40

🕒 GitHub Actions: 25/08 14:30
🤖 Executado a cada 15min

🌍 MERCADO CRIPTO:
• Cap Total: $2.45T 📈 (+1.2%)
• Domínio BTC: 54.3%
• Fear & Greed: 65 (Greed)

📋 Análise:
• Tendência: Alta
• Força: 💪
• Momentum: 🚀
• Supertrend: 🟢

💡 Setup de alta qualidade com múltiplos indicadores alinhados!
```

## 🛠️ Como Configurar

### 1. Fork este Repositório
- Clique em **"Fork"** no GitHub
- Mantenha público (necessário para Actions gratuitas)

### 2. Criar Bot Telegram
```
1. Abra @BotFather no Telegram
2. /newbot
3. Nome: Scanner Crypto Actions  
4. Username: scanner_crypto_123_bot
5. Copie o TOKEN recebido
```

### 3. Obter Chat ID
```
1. Envie qualquer mensagem para seu bot
2. Acesse: https://api.telegram.org/botSEU_TOKEN/getUpdates
3. Procure: "chat":{"id":123456789
4. Copie o número (seu chat_id)
```

### 4. Configurar GitHub Secrets
No seu repositório GitHub:
```
1. Settings → Secrets and variables → Actions
2. New repository secret:
   - Name: TELEGRAM_BOT_TOKEN
   - Value: seu_token_completo

3. New repository secret:
   - Name: TELEGRAM_CHAT_ID  
   - Value: seu_chat_id_numerico
```

### 5. Ativar GitHub Actions
```
1. Aba "Actions" do repositório
2. "I understand my workflows, go ahead and enable them"
3. Actions será ativado automaticamente
```

### 6. Testar Execução Manual
```
1. Actions → "🤖 Scanner Crypto ETH/BTC"
2. "Run workflow" → "Run workflow"  
3. Aguarde ~2 minutos
4. Verifique logs e Telegram
```

## ⏰ Cronograma de Execução

- **A cada 15 minutos**, 24 horas por dia
- **96 execuções** por dia
- **2.880 execuções** por mês
- **Totalmente gratuito** (limites GitHub: 2.000 minutos/mês)

## 📊 Recursos e Limites

### ✅ GitHub Actions Gratuito Oferece:
- **2.000 minutos** por mês (suficiente para 4.000 execuções)
- **500 MB** de storage para artifacts
- **Execução paralela** em múltiplos jobs
- **Logs detalhados** de cada execução

### 🔄 Controle de Spam:
- **1 hora** entre alertas do mesmo setup
- **Resumo a cada 4 horas** quando sem sinais
- **Alertas de erro** se algo falhar

## 📈 Monitoramento

### Ver Execuções:
1. **Aba Actions** → Últimas execuções
2. **Clique em execução** → Ver logs detalhados  
3. **Status**: ✅ Sucesso / ❌ Falha

### Telegram:
- **Alertas** de setups detectados
- **Resumos** periódicos de status
- **Notificações** de erro se necessário

## 🔧 Personalização

### Alterar Frequência:
Edite `.github/workflows/scanner.yml`:
```yaml
schedule:
  - cron: '*/30 * * * *'  # A cada 30 minutos
  - cron: '0 */1 * * *'   # A cada 1 hora  
  - cron: '0 */4 * * *'   # A cada 4 horas
```

### Adicionar Mais Pares:
Edite `scanner_github_actions.py`:
```python
PARES_ALVOS = ['BTC/USDT', 'ETH/USDT', 'ADA/USDT', 'SOL/USDT']
```

### Ajustar Timeframe:
```python
timeframe = '1h'  # 1 hora
timeframe = '2h'  # 2 horas  
timeframe = '1d'  # 1 dia
```

## 🛡️ Segurança

- **Secrets** protegidos pelo GitHub
- **Tokens** nunca expostos nos logs
- **Repositório público** (necessário para gratuidade)
- **Código aberto** para auditoria

## ❗ Troubleshooting

### Scanner não executa:
1. **Verificar** se Actions está ativado
2. **Confirmar** secrets configurados corretamente
3. **Checar** se repositório é público

### Bot não responde:
1. **Testar** token manualmente: `https://api.telegram.org/botSEU_TOKEN/getMe`
2. **Verificar** chat_id correto
3. **Confirmar** bot não foi bloqueado

### Muitos erros nos logs:
1. **API OKX** pode ter limite de rate
2. **Conexão** internet instável
3. **Dependências** podem ter conflito

## 🎯 Vantagens vs Soluções Pagas

| Recurso | GitHub Actions | Railway ($5/mês) | Render ($7/mês) |
|---------|----------------|------------------|-----------------|
| **Custo** | 🆓 Gratuito | 💰 $60/ano | 💰 $84/ano |
| **Uptime** | ✅ 24/7 | ✅ 24/7 | ✅ 24/7 |
| **Manutenção** | ❌ GitHub gerencia | ❌ Plataforma gerencia | ❌ Plataforma gerencia |
| **Controle** | ✅ Código aberto | ⚠️ Black box | ⚠️ Black box |
| **Escalabilidade** | ✅ Ilimitada | ⚠️ Baseada em uso | ⚠️ Plano fixo |
| **Logs** | ✅ Completos | ✅ Completos | ✅ Completos |

## 🚀 Próximos Passos

### Melhorias Futuras:
- 📊 **Dashboard web** com histórico
- 📈 **Backtesting** automático  
- 🔔 **Múltiplos canais** de notificação
- 🤖 **AI/ML** para otimização de setups
- 📱 **App mobile** para controle

### Comunidade:
- 🐛 **Issues** para reportar bugs
- 💡 **Discussions** para sugestões
- 🔄 **Pull requests** bem-vindos
- ⭐ **Star** se útil!

## 📄 Licença

MIT License - Use livremente, modifique e distribua!

## 🙏 Créditos

- **ccxt**: Interface para exchanges
- **pandas**: Manipulação de dados
- **ta**: Indicadores técnicos
- **GitHub Actions**: Execução gratuita
- **Telegram**: Notificações instantâneas

---

## ⚡ Quick Start

```bash
# 1. Fork este repo
# 2. Configure secrets (TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID)  
# 3. Actions → Enable workflows
# 4. Aguarde próxima execução (máx 15min)
# 5. Receba alertas no Telegram! 🎉
```

**🎯 Scanner profissional, gratuito e automático em menos de 10 minutos!** 

---

*Desenvolvido com ❤️ para a comunidade crypto brasileira*
