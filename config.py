import os

class Config:
    """
    Configurações do banco de dados MySQL.
    Pode usar variáveis de ambiente (recomendado para produção/Railway)
    ou valores padrão para desenvolvimento local (XAMPP/WAMP/MySQL local).
    """
    MYSQL_HOST = os.environ.get('MYSQLHOST', os.environ.get('DB_HOST', 'localhost'))
    MYSQL_PORT = int(os.environ.get('MYSQLPORT', os.environ.get('DB_PORT', 3306)))
    MYSQL_USER = os.environ.get('MYSQLUSER', os.environ.get('DB_USER', 'root'))
    MYSQL_PASSWORD = os.environ.get('MYSQLPASSWORD', os.environ.get('DB_PASSWORD', 'admin123'))
    MYSQL_DB = os.environ.get('MYSQLDATABASE', os.environ.get('DB_NAME', 'farmacia_estoque'))

    SECRET_KEY = os.environ.get('SECRET_KEY', 'chave-secreta-troque-em-producao')
