import hmac

from fastapi import Request
from fastapi.responses import RedirectResponse
from sqladmin import Admin, ModelView, action
from sqladmin.authentication import AuthenticationBackend
from sqlalchemy import func, select

from config import load_settings
from models import Account, Transaction, User

# The Monthly Report and Sync screens now live in the React SPA (frontend/, served at /app).
# sqladmin is kept only for raw-data CRUD over the models below.


class AdminAuth(AuthenticationBackend):
    async def login(self, request: Request) -> bool:
        form = await request.form()
        password = str(form.get("password", ""))
        settings = load_settings()
        if not settings.admin_password:
            return False
        if hmac.compare_digest(password, settings.admin_password):
            request.session.update({"authenticated": "1"})
            return True
        return False

    async def logout(self, request: Request) -> bool:
        request.session.clear()
        return True

    async def authenticate(self, request: Request) -> bool:
        return bool(request.session.get("authenticated"))


class UserAdmin(ModelView, model=User):
    column_list = ["user_id", "username", "active", "created_at"]


class JarAccountAdmin(ModelView, model=Account):
    name = "Jar"
    name_plural = "Jars"
    icon = "fa-solid fa-piggy-bank"
    column_list = [
        "id",
        "title",
        "is_budget",
        "balance",
        "is_active",
    ]

    def list_query(self, request):
        return select(Account).where(Account.type == "jar")

    def count_query(self, request):
        return select(func.count(Account.id)).where(Account.type == "jar")

    @action(
        name="toggle_budget",
        label="Toggle Budget",
        add_in_detail=True,
        add_in_list=True,
    )
    async def toggle_budget(self, request: Request):
        pks = request.query_params.get("pks", "")
        pk_list = [pk.strip() for pk in pks.split(",") if pk.strip()]
        with self.session_maker() as session:
            for pk in pk_list:
                account = session.get(Account, pk)
                if account and account.type == "jar":
                    account.is_budget = not account.is_budget
                    session.add(account)
            session.commit()
        return RedirectResponse(request.url_for("admin:list", identity=self.identity), status_code=302)


# sqladmin metaclass unconditionally sets identity from model.__name__; override after definition
JarAccountAdmin.identity = "jar"


class CardAccountAdmin(ModelView, model=Account):
    name = "Card"
    name_plural = "Cards"
    icon = "fa-solid fa-credit-card"
    column_list = [
        "id",
        "title",
        "type",
        "balance",
        "is_active",
    ]

    def list_query(self, request):
        return select(Account).where(Account.type == "card")

    def count_query(self, request):
        return select(func.count(Account.id)).where(Account.type == "card")


CardAccountAdmin.identity = "card"


class TransactionAdmin(ModelView, model=Transaction):
    column_list = [
        "id",
        "account.title",
        "comment",
        "amount",
        "time",
    ]


def setup_admin(app, engine):
    settings = load_settings()
    auth_backend = None
    if settings.admin_password:
        secret = settings.internal_api_key or settings.admin_password
        auth_backend = AdminAuth(secret_key=secret)
    admin = Admin(app, engine, authentication_backend=auth_backend)
    admin.add_view(UserAdmin)
    admin.add_view(JarAccountAdmin)
    admin.add_view(CardAccountAdmin)
    admin.add_view(TransactionAdmin)
    return admin
