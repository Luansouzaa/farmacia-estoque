# Sistema de Controle de Estoque - Farmácia
LINK PARA VISUALIZAÇÃO DO SISTEMA: https://web-production-4c8fb.up.railway.app/




 INTEGRANTES: Breno Augusto
              Cauã Henrique
              Gustavo 
              Luan Souza
              Robson Roberto
              Vitor Hugo
              
## Sistema web para gestão de estoque de farmácia, com cadastro de produtos, fornecedores, controle de movimentações (entrada/saída) e consulta de estoque em tempo real.

## Tecnologias

- **Backend:** Python + Flask
- **Banco de dados:** MySQL (via PyMySQL)
- **Frontend:** HTML, CSS e JavaScript puro (Jinja2 para templates)

## Funcionalidades

- **Produtos:** cadastro, edição, exclusão (lógica) e busca por nome/categoria
- **Fornecedores:** cadastro, edição, exclusão (lógica) e busca por nome/CNPJ
- **Movimentações:** registro de entradas e saídas, com atualização automática do estoque e bloqueio de saída quando não há quantidade suficiente
- **Consulta de estoque:** listagem com filtro por estoque baixo, situação (normal/baixo/esgotado) e validade
- **Dashboard:** indicadores gerais (total de produtos, fornecedores, itens críticos, valor total em estoque) e últimas movimentações

## Estrutura do projeto

```
farmacia_estoque/
├── app.py                 # Aplicação Flask (rotas e lógica)
├── config.py               # Configuração de conexão com o banco
├── database.sql            # Script de criação das tabelas + dados de exemplo
├── requirements.txt         # Dependências Python
├── templates/               # Páginas HTML (Jinja2)
└── static/
    ├── css/style.css        # Estilos
    └── js/script.js         # Interações (confirmação, toasts)
```

## Modelo de dados

- **fornecedores** (id, nome, cnpj, telefone, email, endereco, ativo, ...)
- **produtos** (id, nome, descricao, categoria, fornecedor_id [FK], lote, data_validade, preco_custo, preco_venda, quantidade_estoque, quantidade_minima, ativo, ...)
- **movimentacoes** (id, produto_id [FK], tipo ['entrada'|'saida'], quantidade, motivo, responsavel, data_movimentacao)

A quantidade em estoque de cada produto **só é alterada através de movimentações** (nunca editada diretamente na tela de produto), garantindo que o histórico sempre reflita a realidade do estoque.

## Como rodar localmente

### 1. Criar o banco de dados

No MySQL (Workbench, phpMyAdmin, ou terminal):

```bash
mysql -u root -p < database.sql
```

Isso cria o banco `farmacia_estoque`, as tabelas e alguns dados de exemplo.

### 2. Configurar variáveis de ambiente (opcional)

Por padrão o sistema tenta conectar em `localhost`, usuário `root`, senha vazia. Se seu MySQL local usa outras credenciais, defina as variáveis antes de rodar:

```bash
export DB_HOST=localhost
export DB_USER=root
export DB_PASSWORD=sua_senha
export DB_NAME=farmacia_estoque
export SECRET_KEY=uma-chave-secreta
```

No Windows (PowerShell): use `$env:DB_HOST="localhost"` etc.

### 3. Instalar dependências

```bash
python -m venv venv
source venv/bin/activate      # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 4. Rodar a aplicação

```bash
python app.py
```

Acesse em `http://localhost:5000`.

## Deploy no Railway

Já que você já tem experiência com deploy no Railway (como no Fale Fácil):

1. Suba o projeto para um repositório GitHub.
2. Crie um novo projeto no Railway e adicione um serviço **MySQL**.
3. Adicione um serviço a partir do repositório (Flask).
4. Nas variáveis de ambiente do serviço Flask, referencie as variáveis do MySQL do Railway:
   - `MYSQLHOST` → `${{MySQL.MYSQLHOST}}`
   - `MYSQLPORT` → `${{MySQL.MYSQLPORT}}`
   - `MYSQLUSER` → `${{MySQL.MYSQLUSER}}`
   - `MYSQLPASSWORD` → `${{MySQL.MYSQLPASSWORD}}`
   - `MYSQLDATABASE` → `${{MySQL.MYSQLDATABASE}}`
   - `SECRET_KEY` → uma string aleatória
5. Configure o start command: `gunicorn app:app`
6. Rode o script `database.sql` no banco do Railway (pode usar o cliente MySQL apontando para o host/porta públicos do Railway).

## Possíveis melhorias futuras

- Autenticação de usuários (login/permissões), como no Fale Fácil
- Relatórios em PDF/Excel de movimentações por período
- Alertas de produtos próximos do vencimento
- Código de barras / QR Code para consulta rápida de produtos
