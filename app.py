import os
from datetime import datetime, timezone

import requests
from dotenv import load_dotenv
from flask import Flask, flash, redirect, render_template, request, url_for
from flask_sqlalchemy import SQLAlchemy

load_dotenv()

app = Flask(__name__)

basedir = os.path.abspath(os.path.dirname(__file__))
instance_dir = os.path.join(basedir, "instance")
os.makedirs(instance_dir, exist_ok=True)

app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "dev-key-semana-11b")
app.config["SQLALCHEMY_DATABASE_URI"] = (
    "sqlite:///" + os.path.join(instance_dir, "app.db")
)
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# SendGrid
app.config["API_URL"] = os.getenv(
    "API_URL",
    "https://api.sendgrid.com/v3/mail/send",
).strip()
app.config["API_KEY"] = os.getenv("API_KEY", "").strip()
app.config["API_FROM"] = os.getenv(
    "API_FROM",
    "p.taissa@aluno.ifsp.edu.br",
).strip()
app.config["FLASKY_ADMIN"] = os.getenv(
    "FLASKY_ADMIN",
    "flaskaulasweb@zohomail.com",
).strip()
app.config["FLASKY_MAIL_SUBJECT_PREFIX"] = "[Flask] "

# Dados acadêmicos
app.config["STUDENT_ID"] = "PT3038084"
app.config["STUDENT_NAME"] = "Taissa Pieri"
app.config["STUDENT_EMAIL"] = "p.taissa@aluno.ifsp.edu.br"

db = SQLAlchemy(app)


class Role(db.Model):
    __tablename__ = "roles"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=True, nullable=False)
    users = db.relationship("User", backref="role", lazy=True)


class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    role_id = db.Column(
        db.Integer,
        db.ForeignKey("roles.id"),
        nullable=False,
    )


class EmailEnviado(db.Model):
    __tablename__ = "emails_enviados"

    id = db.Column(db.Integer, primary_key=True)
    destinatario = db.Column(db.String(120), nullable=False)
    assunto = db.Column(db.String(200), nullable=False)
    usuario = db.Column(db.String(80), nullable=False)
    prontuario = db.Column(db.String(30), nullable=False)
    nome_aluno = db.Column(db.String(120), nullable=False)
    data_envio = db.Column(
        db.DateTime,
        nullable=False,
        default=lambda: datetime.now(timezone.utc).replace(tzinfo=None),
    )


ROLE_NAMES = ("Administrator", "Moderator", "User")


def create_default_roles():
    for role_name in ROLE_NAMES:
        role = Role.query.filter_by(name=role_name).first()
        if role is None:
            db.session.add(Role(name=role_name))
    db.session.commit()


class EmailConfigurationError(Exception):
    pass


class EmailDeliveryError(Exception):
    pass


def validate_email_configuration():
    required = {
        "API_URL": app.config["API_URL"],
        "API_KEY": app.config["API_KEY"],
        "API_FROM": app.config["API_FROM"],
        "FLASKY_ADMIN": app.config["FLASKY_ADMIN"],
    }

    missing = [
        key for key, value in required.items()
        if not value
    ]

    if missing:
        raise EmailConfigurationError(
            "Configuração de e-mail incompleta. "
            "Variáveis ausentes: "
            + ", ".join(missing)
        )


def send_email(to, subject, template, **kwargs):
    validate_email_configuration()

    if isinstance(to, str):
        recipients = [to]
    else:
        recipients = list(to)

    recipients = list(dict.fromkeys(recipients))

    html_body = render_template(
        template + ".html",
        **kwargs,
    )

    full_subject = (
        app.config["FLASKY_MAIL_SUBJECT_PREFIX"]
        + subject
    )

    payload = {
        "personalizations": [
            {
                "to": [
                    {"email": recipient}
                    for recipient in recipients
                ]
            }
        ],
        "from": {
            "email": app.config["API_FROM"],
            "name": "Flask - Semana 11.B",
        },
        "subject": full_subject,
        "content": [
            {
                "type": "text/html",
                "value": html_body,
            }
        ],
    }

    response = requests.post(
        app.config["API_URL"],
        headers={
            "Authorization":
                f"Bearer {app.config['API_KEY']}",
            "Content-Type":
                "application/json",
        },
        json=payload,
        timeout=15,
    )

    if response.status_code != 202:
        raise EmailDeliveryError(
            "O SendGrid não aceitou o envio. "
            f"Status: {response.status_code}. "
            f"Resposta: {response.text}"
        )

    return recipients, full_subject


@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        username = request.form.get(
            "username",
            "",
        ).strip()

        enviar_professor = (
            request.form.get("enviar_professor")
            == "on"
        )

        if not username:
            flash(
                "Informe o nome do usuário.",
                "danger",
            )
            return redirect(url_for("index"))

        role = Role.query.filter_by(
            name="User"
        ).first()

        if role is None:
            flash(
                "A função User não foi encontrada.",
                "danger",
            )
            return redirect(url_for("index"))

        existing_user = User.query.filter_by(
            username=username
        ).first()

        if existing_user:
            flash(
                "Esse usuário já está cadastrado.",
                "warning",
            )
            return redirect(url_for("index"))

        user = User(
            username=username,
            role=role,
        )

        db.session.add(user)
        db.session.flush()

        recipients = [
            app.config["STUDENT_EMAIL"]
        ]

        if enviar_professor:
            recipients.append(
                app.config["FLASKY_ADMIN"]
            )

        assunto = (
            "Novo usuário cadastrado - Semana 11.B"
        )

        try:
            enviados, assunto_completo = send_email(
                recipients,
                assunto,
                "mail/new_user",
                student_id=app.config[
                    "STUDENT_ID"
                ],
                student_name=app.config[
                    "STUDENT_NAME"
                ],
                user=user,
            )

            for destinatario in enviados:
                registro = EmailEnviado(
                    destinatario=destinatario,
                    assunto=assunto_completo,
                    usuario=user.username,
                    prontuario=app.config[
                        "STUDENT_ID"
                    ],
                    nome_aluno=app.config[
                        "STUDENT_NAME"
                    ],
                )
                db.session.add(registro)

            db.session.commit()

            if len(enviados) == 1:
                flash(
                    "Usuário cadastrado e e-mail "
                    "enviado com sucesso.",
                    "success",
                )
            else:
                flash(
                    "Usuário cadastrado e e-mails "
                    "enviados com sucesso.",
                    "success",
                )

        except (
            EmailConfigurationError,
            EmailDeliveryError,
        ) as error:
            db.session.rollback()

            flash(
                f"Erro no envio do e-mail: {error}",
                "danger",
            )

        except Exception as error:
            db.session.rollback()

            flash(
                f"Ocorreu um erro: {error}",
                "danger",
            )

        return redirect(url_for("index"))

    users = User.query.order_by(
        User.id.desc()
    ).all()

    return render_template(
        "index.html",
        users=users,
        total_users=User.query.count(),
        total_roles=Role.query.count(),
        total_emails=EmailEnviado.query.count(),
    )


@app.route("/emailsEnviados")
def emails_enviados():
    emails = EmailEnviado.query.order_by(
        EmailEnviado.id.desc()
    ).all()

    return render_template(
        "emails_enviados.html",
        emails=emails,
    )


with app.app_context():
    db.create_all()
    create_default_roles()


if __name__ == "__main__":
    app.run(debug=True)
