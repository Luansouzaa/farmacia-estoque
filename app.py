from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
import pymysql
from pymysql.cursors import DictCursor
from config import Config
from datetime import datetime

app = Flask(__name__)
app.config.from_object(Config)



def get_db_connection():
    return pymysql.connect(
        host=app.config['MYSQL_HOST'],
        port=app.config['MYSQL_PORT'],
        user=app.config['MYSQL_USER'],
        password=app.config['MYSQL_PASSWORD'],
        database=app.config['MYSQL_DB'],
        cursorclass=DictCursor,
        autocommit=False
    )

@app.route('/')
def index():
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("SELECT COUNT(*) AS total FROM produtos WHERE ativo = 1")
            total_produtos = cursor.fetchone()['total']

            cursor.execute("SELECT COUNT(*) AS total FROM fornecedores WHERE ativo = 1")
            total_fornecedores = cursor.fetchone()['total']

            cursor.execute("""
                SELECT COUNT(*) AS total FROM produtos
                WHERE ativo = 1 AND quantidade_estoque <= quantidade_minima
            """)
            total_estoque_baixo = cursor.fetchone()['total']

            cursor.execute("""
                SELECT SUM(quantidade_estoque * preco_custo) AS valor
                FROM produtos WHERE ativo = 1
            """)
            valor_estoque = cursor.fetchone()['valor'] or 0

            cursor.execute("""
                SELECT m.id, m.tipo, m.quantidade, m.motivo, m.data_movimentacao, p.nome AS produto_nome
                FROM movimentacoes m
                JOIN produtos p ON p.id = m.produto_id
                ORDER BY m.data_movimentacao DESC
                LIMIT 8
            """)
            ultimas_movimentacoes = cursor.fetchall()

            cursor.execute("""
                SELECT id, nome, quantidade_estoque, quantidade_minima
                FROM produtos
                WHERE ativo = 1 AND quantidade_estoque <= quantidade_minima
                ORDER BY quantidade_estoque ASC
                LIMIT 5
            """)
            produtos_criticos = cursor.fetchall()
    finally:
        conn.close()

    return render_template('index.html',
                           total_produtos=total_produtos,
                           total_fornecedores=total_fornecedores,
                           total_estoque_baixo=total_estoque_baixo,
                           valor_estoque=valor_estoque,
                           ultimas_movimentacoes=ultimas_movimentacoes,
                           produtos_criticos=produtos_criticos)



@app.route('/fornecedores')
def fornecedores():
    busca = request.args.get('busca', '').strip()
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            if busca:
                cursor.execute("""
                    SELECT * FROM fornecedores
                    WHERE ativo = 1 AND (nome LIKE %s OR cnpj LIKE %s)
                    ORDER BY nome
                """, (f'%{busca}%', f'%{busca}%'))
            else:
                cursor.execute("SELECT * FROM fornecedores WHERE ativo = 1 ORDER BY nome")
            lista = cursor.fetchall()
    finally:
        conn.close()
    return render_template('fornecedores.html', fornecedores=lista, busca=busca)


@app.route('/fornecedores/novo', methods=['GET', 'POST'])
def fornecedor_novo():
    if request.method == 'POST':
        nome = request.form.get('nome', '').strip()
        cnpj = request.form.get('cnpj', '').strip() or None
        telefone = request.form.get('telefone', '').strip()
        email = request.form.get('email', '').strip()
        endereco = request.form.get('endereco', '').strip()

        if not nome:
            flash('O nome do fornecedor é obrigatório.', 'error')
            return render_template('fornecedor_form.html', fornecedor=request.form)

        conn = get_db_connection()
        try:
            with conn.cursor() as cursor:
                cursor.execute("""
                    INSERT INTO fornecedores (nome, cnpj, telefone, email, endereco)
                    VALUES (%s, %s, %s, %s, %s)
                """, (nome, cnpj, telefone, email, endereco))
            conn.commit()
            flash('Fornecedor cadastrado com sucesso!', 'success')
            return redirect(url_for('fornecedores'))
        except pymysql.err.IntegrityError:
            conn.rollback()
            flash('Já existe um fornecedor cadastrado com esse CNPJ.', 'error')
            return render_template('fornecedor_form.html', fornecedor=request.form)
        finally:
            conn.close()

    return render_template('fornecedor_form.html', fornecedor=None)


@app.route('/fornecedores/editar/<int:id>', methods=['GET', 'POST'])
def fornecedor_editar(id):
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            if request.method == 'POST':
                nome = request.form.get('nome', '').strip()
                cnpj = request.form.get('cnpj', '').strip() or None
                telefone = request.form.get('telefone', '').strip()
                email = request.form.get('email', '').strip()
                endereco = request.form.get('endereco', '').strip()

                if not nome:
                    flash('O nome do fornecedor é obrigatório.', 'error')
                    return redirect(url_for('fornecedor_editar', id=id))

                cursor.execute("""
                    UPDATE fornecedores
                    SET nome=%s, cnpj=%s, telefone=%s, email=%s, endereco=%s
                    WHERE id=%s
                """, (nome, cnpj, telefone, email, endereco, id))
                conn.commit()
                flash('Fornecedor atualizado com sucesso!', 'success')
                return redirect(url_for('fornecedores'))

            cursor.execute("SELECT * FROM fornecedores WHERE id=%s", (id,))
            fornecedor = cursor.fetchone()
            if not fornecedor:
                flash('Fornecedor não encontrado.', 'error')
                return redirect(url_for('fornecedores'))
    finally:
        conn.close()

    return render_template('fornecedor_form.html', fornecedor=fornecedor)


@app.route('/fornecedores/excluir/<int:id>', methods=['POST'])
def fornecedor_excluir(id):
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            # Verifica se existem produtos vinculados
            cursor.execute("SELECT COUNT(*) AS total FROM produtos WHERE fornecedor_id=%s AND ativo=1", (id,))
            if cursor.fetchone()['total'] > 0:
                flash('Não é possível excluir: existem produtos vinculados a este fornecedor.', 'error')
                return redirect(url_for('fornecedores'))

            cursor.execute("UPDATE fornecedores SET ativo=0 WHERE id=%s", (id,))
        conn.commit()
        flash('Fornecedor removido com sucesso!', 'success')
    finally:
        conn.close()
    return redirect(url_for('fornecedores'))

@app.route('/produtos')
def produtos():
    busca = request.args.get('busca', '').strip()
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            query = """
                SELECT p.*, f.nome AS fornecedor_nome
                FROM produtos p
                LEFT JOIN fornecedores f ON f.id = p.fornecedor_id
                WHERE p.ativo = 1
            """
            params = []
            if busca:
                query += " AND (p.nome LIKE %s OR p.categoria LIKE %s)"
                params += [f'%{busca}%', f'%{busca}%']
            query += " ORDER BY p.nome"
            cursor.execute(query, params)
            lista = cursor.fetchall()

            cursor.execute("SELECT id, nome FROM fornecedores WHERE ativo=1 ORDER BY nome")
            fornecedores_lista = cursor.fetchall()
    finally:
        conn.close()
    return render_template('produtos.html', produtos=lista, busca=busca, fornecedores=fornecedores_lista)


@app.route('/produtos/novo', methods=['GET', 'POST'])
def produto_novo():
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("SELECT id, nome FROM fornecedores WHERE ativo=1 ORDER BY nome")
            fornecedores_lista = cursor.fetchall()

            if request.method == 'POST':
                nome = request.form.get('nome', '').strip()
                descricao = request.form.get('descricao', '').strip()
                categoria = request.form.get('categoria', '').strip()
                fornecedor_id = request.form.get('fornecedor_id') or None
                lote = request.form.get('lote', '').strip()
                data_validade = request.form.get('data_validade') or None
                unidade_medida = request.form.get('unidade_medida', 'un').strip()
                preco_custo = request.form.get('preco_custo', '0').replace(',', '.')
                preco_venda = request.form.get('preco_venda', '0').replace(',', '.')
                quantidade_estoque = request.form.get('quantidade_estoque', '0')
                quantidade_minima = request.form.get('quantidade_minima', '5')

                if not nome:
                    flash('O nome do produto é obrigatório.', 'error')
                    return render_template('produto_form.html', produto=request.form, fornecedores=fornecedores_lista)

                cursor.execute("""
                    INSERT INTO produtos
                    (nome, descricao, categoria, fornecedor_id, lote, data_validade,
                     unidade_medida, preco_custo, preco_venda, quantidade_estoque, quantidade_minima)
                    VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                """, (nome, descricao, categoria, fornecedor_id, lote, data_validade,
                      unidade_medida, preco_custo, preco_venda, quantidade_estoque, quantidade_minima))
                conn.commit()
                flash('Produto cadastrado com sucesso!', 'success')
                return redirect(url_for('produtos'))
    finally:
        conn.close()

    return render_template('produto_form.html', produto=None, fornecedores=fornecedores_lista)


@app.route('/produtos/editar/<int:id>', methods=['GET', 'POST'])
def produto_editar(id):
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("SELECT id, nome FROM fornecedores WHERE ativo=1 ORDER BY nome")
            fornecedores_lista = cursor.fetchall()

            if request.method == 'POST':
                nome = request.form.get('nome', '').strip()
                descricao = request.form.get('descricao', '').strip()
                categoria = request.form.get('categoria', '').strip()
                fornecedor_id = request.form.get('fornecedor_id') or None
                lote = request.form.get('lote', '').strip()
                data_validade = request.form.get('data_validade') or None
                unidade_medida = request.form.get('unidade_medida', 'un').strip()
                preco_custo = request.form.get('preco_custo', '0').replace(',', '.')
                preco_venda = request.form.get('preco_venda', '0').replace(',', '.')
                quantidade_minima = request.form.get('quantidade_minima', '5')

                if not nome:
                    flash('O nome do produto é obrigatório.', 'error')
                    return redirect(url_for('produto_editar', id=id))

                # Observação: a quantidade_estoque NÃO é editada diretamente aqui.
                # Ela só muda através de movimentações de entrada/saída,
                # para manter o histórico e a integridade do estoque.
                cursor.execute("""
                    UPDATE produtos
                    SET nome=%s, descricao=%s, categoria=%s, fornecedor_id=%s, lote=%s,
                        data_validade=%s, unidade_medida=%s, preco_custo=%s, preco_venda=%s,
                        quantidade_minima=%s
                    WHERE id=%s
                """, (nome, descricao, categoria, fornecedor_id, lote, data_validade,
                      unidade_medida, preco_custo, preco_venda, quantidade_minima, id))
                conn.commit()
                flash('Produto atualizado com sucesso!', 'success')
                return redirect(url_for('produtos'))

            cursor.execute("SELECT * FROM produtos WHERE id=%s", (id,))
            produto = cursor.fetchone()
            if not produto:
                flash('Produto não encontrado.', 'error')
                return redirect(url_for('produtos'))
    finally:
        conn.close()

    return render_template('produto_form.html', produto=produto, fornecedores=fornecedores_lista)


@app.route('/produtos/excluir/<int:id>', methods=['POST'])
def produto_excluir(id):
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("UPDATE produtos SET ativo=0 WHERE id=%s", (id,))
        conn.commit()
        flash('Produto removido com sucesso!', 'success')
    finally:
        conn.close()
    return redirect(url_for('produtos'))

@app.route('/movimentacoes')
def movimentacoes():
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT m.*, p.nome AS produto_nome, p.unidade_medida
                FROM movimentacoes m
                JOIN produtos p ON p.id = m.produto_id
                ORDER BY m.data_movimentacao DESC
                LIMIT 200
            """)
            lista = cursor.fetchall()

            cursor.execute("SELECT id, nome, quantidade_estoque, unidade_medida FROM produtos WHERE ativo=1 ORDER BY nome")
            produtos_lista = cursor.fetchall()
    finally:
        conn.close()
    return render_template('movimentacoes.html', movimentacoes=lista, produtos=produtos_lista)


@app.route('/movimentacoes/nova', methods=['POST'])
def movimentacao_nova():
    produto_id = request.form.get('produto_id')
    tipo = request.form.get('tipo')
    quantidade = request.form.get('quantidade')
    motivo = request.form.get('motivo', '').strip()
    responsavel = request.form.get('responsavel', '').strip()

    if not produto_id or tipo not in ('entrada', 'saida'):
        flash('Dados inválidos para a movimentação.', 'error')
        return redirect(url_for('movimentacoes'))

    try:
        quantidade = int(quantidade)
        if quantidade <= 0:
            raise ValueError
    except (ValueError, TypeError):
        flash('A quantidade deve ser um número inteiro maior que zero.', 'error')
        return redirect(url_for('movimentacoes'))

    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("SELECT quantidade_estoque, nome FROM produtos WHERE id=%s AND ativo=1 FOR UPDATE", (produto_id,))
            produto = cursor.fetchone()

            if not produto:
                flash('Produto não encontrado.', 'error')
                conn.rollback()
                return redirect(url_for('movimentacoes'))

            if tipo == 'saida' and quantidade > produto['quantidade_estoque']:
                flash(f"Estoque insuficiente para \"{produto['nome']}\". Disponível: {produto['quantidade_estoque']}.", 'error')
                conn.rollback()
                return redirect(url_for('movimentacoes'))

            # Atualiza estoque
            if tipo == 'entrada':
                cursor.execute("UPDATE produtos SET quantidade_estoque = quantidade_estoque + %s WHERE id=%s",
                               (quantidade, produto_id))
            else:
                cursor.execute("UPDATE produtos SET quantidade_estoque = quantidade_estoque - %s WHERE id=%s",
                               (quantidade, produto_id))

            # Registra a movimentação
            cursor.execute("""
                INSERT INTO movimentacoes (produto_id, tipo, quantidade, motivo, responsavel)
                VALUES (%s, %s, %s, %s, %s)
            """, (produto_id, tipo, quantidade, motivo, responsavel))

        conn.commit()
        flash(f"{'Entrada' if tipo == 'entrada' else 'Saída'} registrada com sucesso!", 'success')
    except Exception as e:
        conn.rollback()
        flash(f'Erro ao registrar movimentação: {str(e)}', 'error')
    finally:
        conn.close()

    return redirect(url_for('movimentacoes'))

@app.route('/estoque')
def estoque():
    busca = request.args.get('busca', '').strip()
    filtro = request.args.get('filtro', '').strip()  # 'baixo' = estoque baixo

    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            query = """
                SELECT p.*, f.nome AS fornecedor_nome
                FROM produtos p
                LEFT JOIN fornecedores f ON f.id = p.fornecedor_id
                WHERE p.ativo = 1
            """
            params = []
            if busca:
                query += " AND (p.nome LIKE %s OR p.categoria LIKE %s)"
                params += [f'%{busca}%', f'%{busca}%']
            if filtro == 'baixo':
                query += " AND p.quantidade_estoque <= p.quantidade_minima"
            query += " ORDER BY p.nome"
            cursor.execute(query, params)
            lista = cursor.fetchall()
    finally:
        conn.close()

    return render_template('estoque.html', produtos=lista, busca=busca, filtro=filtro)


# API simples (JSON) para consultar estoque de um produto - útil para integrações
@app.route('/api/estoque/<int:id>')
def api_estoque(id):
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT id, nome, quantidade_estoque, quantidade_minima, unidade_medida
                FROM produtos WHERE id=%s AND ativo=1
            """, (id,))
            produto = cursor.fetchone()
    finally:
        conn.close()

    if not produto:
        return jsonify({'erro': 'Produto não encontrado'}), 404
    return jsonify(produto)


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
