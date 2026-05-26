import hashlib

from flask import redirect

from backend.crud import EmailVerificationStatus, verify_user_email_token


def register_auth_routes(server):
    @server.route("/verify-email/<token>")
    def verify_email(token):
        token_hash = hashlib.sha256(token.encode()).hexdigest()
        status = verify_user_email_token(token_hash)
        if status == EmailVerificationStatus.SUCCESS:
            return redirect("/login?verified=1")

        return redirect("/login?verified=0")
