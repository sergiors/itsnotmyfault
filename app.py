import re
import requests
import os

from flask import Flask
from flask import Response
from flask import render_template, url_for, redirect, request, flash
from functools import wraps
from pyf import map
from pipe import concat
from Postgres import Postgres
from CloudSQLProxy import CloudSQLProxy

proxy = CloudSQLProxy('./cloud_sql_proxy', 'inbep-185414-2607f469165a.json')
proxy.run()

dsn = os.environ.get('PGSQL_DSN', None)
app = Flask(__name__)
app.secret_key = 's0m3_s3c43t'


def authorization(f):
    @wraps(f)
    def wrapped(**kwargs):
        r = requests.post('https://api.inbep.com.br/auth/token', json=request.authorization)

        if r.status_code == 200:
            return f(**kwargs)

        return Response(None, 401, {
            'WWW-Authenticate': 'Basic realm="Login Required"'
        })

    return wrapped


@app.route('/', methods=['GET', 'POST'])
@authorization
def home():
    db = Postgres(dsn)

    if request.method == 'POST':
        ids = re.findall(r'\d+', request.form['textarea']) | map(int) | concat
        items = db.fetchall(f"""
            SELECT
                r.matricula_id,
                u.usuario_nome,
                c.curso_nome,
                r.progress,
                r.metadata->'pageviews',
                r.metadata->'freezed_content_ids',
                r.metadata->'managed_by'->>'name'
            FROM usuario_matriculas r
            LEFT JOIN usuarios u ON usuario_id = matricula_usuario_id
            LEFT JOIN cursos c ON curso_id = matricula_curso_id
            WHERE matricula_id IN ({ids})
            """)
        return render_template('index.html', registrations=items)

    return render_template('index.html')


@app.route('/actions', methods=['POST'])
def actions():
    db = Postgres(dsn)
    ids = request.form.getlist('items[]') | map(int) | concat(',')
    action = request.form['type']
    queries = {
        'set_free': f'UPDATE usuario_matriculas SET matricula_usuario_id = null WHERE matricula_id IN ({ids})',
        'mark_as_complete': f'UPDATE usuario_matriculas SET progress = 100 WHERE matricula_id IN ({ids})',
        'delete': f'DELETE FROM usuario_matriculas WHERE matricula_id IN ({ids})',
        'fix_pagination': "UPDATE usuario_matriculas SET metadata = metadata || row_to_json(t)::jsonb FROM (SELECT metadata->'freezed_content_ids' AS pageviews FROM usuario_matriculas WHERE matricula_id = {}) t WHERE matricula_id = {}"
    
    }
    messages = {
        'set_free': 'As matrículas foram liberadas',
        'mark_as_complete': 'As matrículas foram marcadas como completas',
        'delete': 'As matrículas foram excluidas',
        'fix_pagination': 'As paginações foram corrigidas'
    }

    if 'fix_pagination' == action:
        new_queries = [queries['fix_pagination'].format(x, x) for x in ids.split(',')]
        db.execute(new_queries | concat(';'))
    else:
        db.execute(queries.get(action))

    flash(messages.get(action))

    return redirect(url_for('home'))
