# Semana 11.B - E-mail com Flask

Aplicação desenvolvida para a atividade **Semana 11.B**, utilizando Flask, Flask-SQLAlchemy, SQLite e SendGrid Web API, preparada para hospedagem no PythonAnywhere.

## Funcionalidades

- Cadastro de usuários.
- Envio automático para o e-mail institucional da aluna.
- Opção de envio também para `flaskaulasweb@zohomail.com`.
- Corpo do e-mail com prontuário, nome da aluna, usuário cadastrado e função.
- Persistência dos e-mails enviados no SQLite.
- Listagem dos envios em `/emailsEnviados`.

## Dados acadêmicos

- Nome: Taissa Pieri
- Prontuário: PT3038084
- E-mail institucional: p.taissa@aluno.ifsp.edu.br

## Instalação

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python app.py
```

## Configuração

Crie o arquivo `.env` a partir do `.env.example` e informe a chave real do SendGrid.


