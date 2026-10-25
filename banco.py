import sqlite3

def conectar_banco():
    conexao = sqlite3.connect("BancoLoja.db")

    conexao.execute("PRAGMA foreign_keys = ON")

    return conexao

def criar_tabela_loja(conexao: sqlite3.Connection):
    cursor = conexao.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS produtos (
    id INTEGER PRIMARY KEY,
    nome TEXT,
    preco REAL,
    estoque INTEGER,
    ativo INTEGER,
    categoria TEXT
    )
    """)

    conexao.commit()

def criar_tabela_vendas(conexao: sqlite3.Connection):
    cursor = conexao.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS vendas (
    id INTEGER PRIMARY KEY,
    produto_id INTEGER,
    quantidade INTEGER,
    valor_unitario REAL,
    valor_total REAL,
    data_hora TEXT,

    FOREIGN KEY(produto_id) REFERENCES produtos(id)
    )
    """)

    conexao.commit()