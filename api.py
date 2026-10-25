import sqlite3

from fastapi import FastAPI, HTTPException
from banco import conectar_banco, criar_tabela_loja, criar_tabela_vendas
from pydantic import BaseModel
from datetime import datetime

app = FastAPI()

conexao = conectar_banco()
criar_tabela_loja(conexao)
criar_tabela_vendas(conexao)

conexao.close()

class EntradaCriarProduto(BaseModel):
    nome_produto: str
    preco: float
    quantidade_do_estoque: int
    categoria: str

class SaidaCriarProduto(BaseModel):
    mensagem: str
    id: int
    nome: str
    preco: float
    estoque: int
    categoria: str

@app.post("/produtos", response_model=SaidaCriarProduto)
def criar_produto(produto: EntradaCriarProduto):
    conexao = conectar_banco()

    try:
        cursor = conexao.cursor()

        cursor.execute(
            "SELECT * FROM produtos WHERE nome = ?",
            (produto.nome_produto,)
        )

        produto_encontrado = cursor.fetchone()
        if produto_encontrado is not None:
            raise HTTPException(
                status_code=409,
                detail="ja existe um produto com este nome"
            )

        if produto.preco <= 0:
            raise HTTPException(
                status_code=400,
                detail="Digite algo maior que zero"
            )

        if produto.quantidade_do_estoque <= 0:
            raise HTTPException(
                status_code=400,
                detail="O estoque precisa ser maior que zero"
            )

        cursor.execute("""
        INSERT INTO produtos (nome, preco, estoque, ativo, categoria)
        VALUES (?, ?, ?, ?, ?)
        """, (produto.nome_produto, produto.preco, produto.quantidade_do_estoque, 1, produto.categoria))

        produto_id = cursor.lastrowid

        conexao.commit()

        return {
            "mensagem": "Produto criado com sucesso",
            "id": produto_id,
            "nome": produto.nome_produto,
            "preco": produto.preco,
            "estoque": produto.quantidade_do_estoque,
            "categoria": produto.categoria
        }

    except sqlite3.Error as erro:
        conexao.rollback()

        print(f"Erro no criar produto: {erro}")

        raise HTTPException(
            status_code=500,
            detail="Erro interno no SQLITE"
        )

    finally:
        conexao.close()


class SaidaListarProdutos(BaseModel):
    id: int
    nome: str
    preco: float
    estoque: int
    ativo: int
    categoria: str


@app.get("/produtos", response_model=list[SaidaListarProdutos])
def listar_produtos(categoria: str | None = None, ativo: int | None = None):
    conexao = conectar_banco()

    try:
        cursor = conexao.cursor()

        if categoria is not None and ativo is not None:
            cursor.execute(
                "SELECT * FROM produtos WHERE categoria = ? AND ativo = ?",
                (categoria, ativo)
            )

        elif categoria is not None:
            cursor.execute(
                "SELECT * FROM produtos WHERE categoria = ?",
                (categoria,)
            )

        elif ativo is not None:
            cursor.execute(
                "SELECT * FROM produtos WHERE ativo = ?",
                (ativo,)
            )

        else:
            cursor.execute("SELECT * FROM produtos")


        produtos_encontrados = cursor.fetchall()
        if produtos_encontrados == []:
            raise HTTPException(
                status_code=404,
                detail="Nenhum produto encontrado"
            )

        resultado = []

        for produto in produtos_encontrados:
            resultado.append({
                "id": produto[0],
                "nome": produto[1],
                "preco": produto[2],
                "estoque": produto[3],
                "ativo": produto[4],
                "categoria": produto[5]
            })

        return resultado

    except sqlite3.Error as erro:
        print(f"Erro no listar produtos: {erro}")

        raise HTTPException(
            status_code=500,
            detail="Erro interno no SQLITE"
        )

    finally:
        conexao.close()

class SaidaListarProdutoEspecifico(BaseModel):
    mensagem: str
    id: int
    nome: str
    preco: float
    estoque: int
    ativo: int
    categoria: str

@app.get("/produtos/{id}", response_model=SaidaListarProdutoEspecifico)
def listar_produto_especifico(id: int):
    conexao = conectar_banco()

    try:
        cursor = conexao.cursor()

        cursor.execute(
            "SELECT * FROM produtos WHERE id = ?",
            (id,)
        )

        produto_encontrado = cursor.fetchone()
        if produto_encontrado is None:
            raise HTTPException(
                status_code=404,
                detail="Nenhum produto encontrado"
            )

        return {
            "mensagem": "Produto encontrado",
            "id": produto_encontrado[0],
            "nome": produto_encontrado[1],
            "preco": produto_encontrado[2],
            "estoque": produto_encontrado[3],
            "ativo": produto_encontrado[4],
            "categoria": produto_encontrado[5]
        }

    except sqlite3.Error as erro:
        print(f"Erro no listar produto especifico: {erro}")

        raise HTTPException(
            status_code=500,
            detail="Erro interno no SQLITE"
        )

    finally:
        conexao.close()


class EntradaMovimentarEstoque(BaseModel):
    tipo: str
    quantidade: int

class SaidaMovimentarEstoque(BaseModel):
    mensagem: str
    id: int
    estoque_atual: int

@app.patch("/produtos/{id}/estoque", response_model=SaidaMovimentarEstoque)
def movimentar_estoque(produto: EntradaMovimentarEstoque, id: int):
    conexao = conectar_banco()

    try:
        cursor = conexao.cursor()

        cursor.execute(
            "SELECT * FROM produtos WHERE id = ?",
            (id,)
        )

        produto_encontrado = cursor.fetchone()
        if produto_encontrado is None:
            raise HTTPException(
                status_code=404,
                detail="Nenhum produto encontrado"
            )

        if produto.quantidade <= 0:
            raise HTTPException(
                status_code=400,
                detail="A quantidade precisa ser maior que zero"
            )

        if produto.tipo not in ["entrada", "saida"]:
            raise HTTPException(
                status_code=409,
                detail="O tipo precisa ser entrada ou saida"
            )

        estoque_atual = produto_encontrado[3]

        if produto.tipo == "entrada":
            estoque_novo = estoque_atual + produto.quantidade

        if produto.tipo == "saida":
            if produto.quantidade > estoque_atual:
                raise HTTPException(
                    status_code=400,
                    detail="Estoque insuficiente"
                )

            estoque_novo = estoque_atual - produto.quantidade


        cursor.execute("""
        UPDATE produtos
        SET estoque = ? WHERE id = ?
        """, (estoque_novo, id)
        )

        conexao.commit()

        return {
            "mensagem": "Estoque atualizado com sucesso",
            "id": id,
            "estoque_atual": estoque_novo
        }

    except sqlite3.Error as erro:
        conexao.rollback()

        print(f"Erro no movimentar estoque: {erro}")

        raise HTTPException(
            status_code=500,
            detail="Erro interno no SQLITE"
        )

    finally:
        conexao.close()


class EntradaMudarAtivo(BaseModel):
    tipo: str

class SaidaMudarAtivo(BaseModel):
    mensagem: str
    id: int

@app.patch("/produtos/{id}/ativo", response_model=SaidaMudarAtivo)
def mudar_ativo(valor: EntradaMudarAtivo, id: int):
    conexao = conectar_banco()

    try:
        cursor = conexao.cursor()

        cursor.execute(
            "SELECT * FROM produtos WHERE id = ?",
            (id,)
        )

        produto_encontrado = cursor.fetchone()
        if produto_encontrado is None:
            raise HTTPException(
                status_code=404,
                detail="Nenhum produto encontrado"
            )

        if valor.tipo not in ["ativado", "desativado"]:
            raise HTTPException(
                status_code=409,
                detail="O tipo precisa ser 'ativado' ou 'desativado'"
            )

        if valor.tipo == "ativado":
            valor_tipo = 1

        elif valor.tipo == "desativado":
            valor_tipo = 0

        cursor.execute("""
        UPDATE produtos
        SET ativo = ? WHERE id = ?
        """, (valor_tipo, id)
        )

        conexao.commit()

        if valor.tipo == "ativado":
            return {
                "mensagem": "Produto atualizado para ATIVADO",
                "id": id
            }

        elif valor.tipo == "desativado":
            return {
                "mensagem": "Produto atualizado para DESATIVADO",
                "id": id
            }

    except sqlite3.Error as erro:
        conexao.rollback()

        print(f"Erro no mudar ativo: {erro}")

        raise HTTPException(
            status_code=500,
            detail="Erro interno no SQLITE"
        )

    finally:
        conexao.close()


class EntradaAtualizarDados(BaseModel):
    nome: str
    preco: float
    categoria: str
class SaidaAtualizarDados(BaseModel):
    mensagem: str
    id: int
    nome: str
    preco: float
    categoria: str

@app.patch("/produtos/{id}/atualizar", response_model=SaidaAtualizarDados)
def atualizar_dados(produto: EntradaAtualizarDados, id: int):
    conexao = conectar_banco()

    try:
        cursor = conexao.cursor()

        cursor.execute(
            "SELECT * FROM produtos WHERE id = ?",
            (id,)
        )

        produto_encontrado = cursor.fetchone()
        if produto_encontrado is None:
            raise HTTPException(
                status_code=404,
                detail="Nenhum produto encontrado"
            )

        if produto.preco <= 0:
            raise HTTPException(
                status_code=400,
                detail="Digite algo maior que zero"
            )

        cursor.execute(
            "SELECT * FROM produtos WHERE nome = ? AND id != ?",
            (produto.nome, id)
        )

        produto2_encontrado = cursor.fetchone()
        if produto2_encontrado is not None:
            raise HTTPException(
                status_code=409,
                detail="Ja existe um produto com este mesmo nome"
            )

        cursor.execute("""
        UPDATE produtos
        SET nome = ?, preco = ?, categoria = ?
        WHERE id = ?
        """, (produto.nome, produto.preco, produto.categoria, id)
        )

        conexao.commit()

        return {
            "mensagem": "Produto atualizado com sucesso",
            "id": id,
            "nome": produto.nome,
            "preco": produto.preco,
            "categoria": produto.categoria
        }

    except sqlite3.Error as erro:
        conexao.rollback()

        print(f"Erro no atualizar dados: {erro}")

        raise HTTPException(
            status_code=500,
            detail="Erro interno no SQLITE"
        )

    finally:
        conexao.close()


class EntradaRegistrarVenda(BaseModel):
    produto_id: int
    quantidade: int

class SaidaRegistrarVenda(BaseModel):
    mensagem: str
    venda_id: int
    id: int
    quantidade: int

@app.post("/vendas", response_model=SaidaRegistrarVenda)
def registrar_venda(venda: EntradaRegistrarVenda):
    conexao = conectar_banco()

    try:
        cursor = conexao.cursor()

        cursor.execute(
            "SELECT * FROM produtos WHERE id = ?",
            (venda.produto_id,)
        )

        produto_encontrado = cursor.fetchone()
        if produto_encontrado is None:
            raise HTTPException(
                status_code=404,
                detail="Nenhum produto encontrado"
            )

        if venda.quantidade <= 0:
            raise HTTPException(
                status_code=400,
                detail="A quantidade precisa ser maior que zero"
            )

        if venda.quantidade > produto_encontrado[3]:
            raise HTTPException(
                status_code=400,
                detail="Estoque insuficiente"
            )

        if produto_encontrado[4] == 0:
            raise HTTPException(
                status_code=409,
                detail="O produto esta desativado"
            )

        preco_do_produto = produto_encontrado[2]

        valor_total = preco_do_produto * venda.quantidade

        data_hora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        cursor.execute("""
        INSERT INTO vendas (produto_id, quantidade, valor_unitario, valor_total, data_hora)
        VALUES (?, ?, ?, ?, ?)
        """, (venda.produto_id, venda.quantidade, preco_do_produto, valor_total, data_hora)
        )

        venda_id = cursor.lastrowid

        cursor.execute("""
        UPDATE produtos
        SET estoque = estoque - ? WHERE id = ? AND estoque >= ?
        """, (venda.quantidade, venda.produto_id, venda.quantidade)
        )

        if cursor.rowcount == 0:
            conexao.rollback()

            raise HTTPException(
                status_code=400,
                detail="O estoque acabou de ser alterado por uma venda"
            )

        conexao.commit()

        return {
            "mensagem": "Compra realizada com sucesso",
            "venda_id": venda_id,
            "id": venda.produto_id,
            "quantidade": venda.quantidade
        }

    except sqlite3.Error as erro:
        conexao.rollback()

        print(f"Erro no regitrar venda: {erro}")

        raise HTTPException(
            status_code=500,
            detail="Erro interno no SQLITE"
        )

    finally:
        conexao.close()


class SaidaListarVendas(BaseModel):
    id: int
    produto_id: int
    produto_nome: str
    quantidade: int
    valor_unitario: float
    valor_total: float
    data_hora: str


@app.get("/vendas", response_model=list[SaidaListarVendas])
def listar_vendas(produto_id: int | None = None, data: str | None = None):
    conexao = conectar_banco()

    try:
        cursor = conexao.cursor()

        if produto_id is not None and data is not None:
            cursor.execute("""
            SELECT vendas.*, produtos.nome FROM vendas JOIN produtos ON vendas.produto_id = produtos.id WHERE vendas.produto_id = ? AND vendas.data_hora LIKE ?""",
            (produto_id, f"{data}%")
            )

        elif produto_id is not None:
            cursor.execute("""
            SELECT vendas.*, produtos.nome FROM vendas JOIN produtos ON vendas.produto_id = produtos.id WHERE vendas.produto_id = ?""",
            (produto_id,)
            )

        elif data is not None:
            cursor.execute("""
            SELECT vendas.*, produtos.nome FROM vendas JOIN produtos ON vendas.produto_id = produtos.id WHERE data_hora LIKE ?""",
            (f"{data}%",)
            )

        else:
            cursor.execute("""SELECT vendas.*, produtos.nome FROM vendas JOIN produtos ON vendas.produto_id = produtos.id""")


        vendas_encontradas = cursor.fetchall()
        if vendas_encontradas == []:
            raise HTTPException(
                status_code=404,
                detail="Nenhuma venda encontrada"
            )

        resultado = []


        for venda in vendas_encontradas:
            resultado.append({
                "id": venda[0],
                "produto_id": venda[1],
                "produto_nome": venda[6],
                "quantidade": venda[2],
                "valor_unitario": venda[3],
                "valor_total": venda[4],
                "data_hora": venda[5]
            })

        return resultado

    except sqlite3.Error as erro:
        print(f"Erro no listar vendas: {erro}")

        raise HTTPException(
            status_code=500,
            detail="Erro interno no SQLITE"
        )

    finally:
        conexao.close()



class SaidaResumoDasVendas(BaseModel):
    total_vendas: int
    total_itens_vendidos: int
    faturamento_total: float

@app.get("/vendas/resumo", response_model=SaidaResumoDasVendas)
def resumo_das_vendas(produto_id: int | None = None, data: str | None = None):
    conexao = conectar_banco()

    try:
        cursor = conexao.cursor()

        if produto_id is not None and data is not None:
            cursor.execute(
                "SELECT COUNT(*), SUM(quantidade), SUM(valor_total) FROM vendas WHERE produto_id = ? AND data_hora LIKE ?",
                (produto_id, f"{data}%")
            )

        elif produto_id is not None:
            cursor.execute(
                "SELECT COUNT(*), SUM(quantidade), SUM(valor_total) FROM vendas WHERE produto_id = ?",
                (produto_id,)
            )

        elif data is not None:
            cursor.execute(
                "SELECT COUNT(*), SUM(quantidade), SUM(valor_total) FROM vendas WHERE data_hora LIKE ?",
                (f"{data}%",)
            )

        else:
            cursor.execute(
                "SELECT COUNT(*), SUM(quantidade), SUM(valor_total) FROM vendas"
            )

        resumo = cursor.fetchone()

        total_vendas = resumo[0]
        total_itens_vendidos = resumo[1]
        faturamento_total = resumo[2]

        if total_itens_vendidos is None:
            total_itens_vendidos = 0

        if faturamento_total is None:
            faturamento_total = 0.0


        return {
            "total_vendas": total_vendas,
            "total_itens_vendidos": total_itens_vendidos,
            "faturamento_total": faturamento_total
        }

    except sqlite3.Error as erro:
        print(f"Erro no resumo das vendas: {erro}")

        raise HTTPException(
            status_code=500,
            detail="Erro interno no SQLITE"
        )

    finally:
        conexao.close()