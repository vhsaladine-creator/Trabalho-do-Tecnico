# SportZone V2

Projeto educacional em Flask com duas áreas:

- **Central esportiva:** eventos, resultados, palpites gratuitos e ranking por pontos.
- **Arcade:** seis minijogos de habilidade/memória com pontuação interna.

> O projeto não usa dinheiro real, R$, depósitos, saques, prêmio monetário ou mecânicas de cassino.

## Recursos

- Cadastro e login com senha protegida por hash
- SQLite criado automaticamente
- Conta demo
- Eventos de futebol, basquete e tênis
- Palpites sem custo de pontos
- +100 pontos em acertos simulados
- Histórico de palpites
- Ranking geral
- 6 minijogos: Tiger Dash, Snake Trail, Dragon Match, Lantern Memory, Panda Tap e Jade Steps
- Layout responsivo para desktop e celular

## Rodar no Windows / VS Code

```powershell
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python app.py
```

Abra: `http://127.0.0.1:5000`

## Conta demo

- E-mail: `demo@sportzone.local`
- Senha: `demo123`

## Estrutura

```text
sportzone_arcade/
├── app.py
├── requirements.txt
├── static/
│   ├── app.js
│   └── style.css
└── templates/
    ├── arcade.html
    ├── base.html
    ├── history.html
    ├── index.html
    ├── leaderboard.html
    ├── login.html
    └── register.html
```
