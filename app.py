from twitter_autobase import app, db
from twitter_autobase.models import User, Autobase

@app.shell_context_processor
def make_shell():
    return {'db': db, 'User': User, 'Autobase': Autobase}
