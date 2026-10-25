# API de Estoque e Vendas

API REST desenvolvida com Python, FastAPI e SQLite para gerenciamento de produtos, estoque e vendas.

O projeto foi criado com foco no aprendizado de Backend, regras de negócio, integração com banco de dados e desenvolvimento de APIs REST.

## Tecnologias utilizadas

- Python
- FastAPI
- SQLite
- Pydantic
- Uvicorn

## Funcionalidades

### Produtos

- Criar produtos
- Listar produtos
- Filtrar produtos por categoria e status
- Buscar produto por ID
- Atualizar dados do produto
- Ativar e desativar produtos
- Realizar entrada e saída de estoque

### Vendas

- Registrar vendas
- Verificar estoque antes da venda
- Impedir venda de produtos desativados
- Atualizar o estoque automaticamente
- Listar vendas
- Filtrar vendas por produto e data
- Exibir o nome do produto utilizando JOIN
- Consultar resumo de vendas
- Calcular quantidade de vendas, itens vendidos e faturamento

## Banco de dados

O projeto utiliza duas tabelas principais:

- `produtos`
- `vendas`

A tabela `vendas` possui uma chave estrangeira (`FOREIGN KEY`) que relaciona `produto_id` com o `id` da tabela `produtos`.

## Regras de negócio

- Produtos novos são cadastrados como ativos.
- Não é permitido cadastrar dois produtos com o mesmo nome.
- O preço do produto deve ser maior que zero.
- Não é possível realizar uma venda sem estoque suficiente.
- Produtos desativados não podem ser vendidos.
- Uma venda registra o preço do produto no momento da compra.
- A venda e a atualização do estoque fazem parte da mesma transação.
- O estoque é protegido contra alterações concorrentes durante uma venda.

## Principais rotas

| Método | Rota | Descrição |
|---|---|---|
| POST | `/produtos` | Criar produto |
| GET | `/produtos` | Listar e filtrar produtos |
| GET | `/produtos/{id}` | Buscar produto por ID |
| PATCH | `/produtos/{id}/estoque` | Movimentar estoque |
| PATCH | `/produtos/{id}/ativo` | Ativar ou desativar produto |
| PATCH | `/produtos/{id}/atualizar` | Atualizar produto |
| POST | `/vendas` | Registrar venda |
| GET | `/vendas` | Listar e filtrar vendas |
| GET | `/vendas/resumo` | Consultar resumo das vendas |

## Como executar

Clone o repositório e entre na pasta do projeto.

Instale as dependências:

```bash
pip install -r requirements.txt
```

Execute a API:

```bash
uvicorn api:app --reload
```

Depois acesse a documentação automática do FastAPI em:

```text
http://127.0.0.1:8000/docs
```

O banco SQLite e suas tabelas são criados automaticamente ao iniciar o projeto.

## Objetivo do projeto

Este projeto faz parte do meu portfólio de estudos em desenvolvimento Backend com Python.

Durante o desenvolvimento foram praticados conceitos como:

- CRUD
- APIs REST
- SQL
- JOIN
- FOREIGN KEY
- filtros com query parameters
- transações
- commit e rollback
- tratamento de erros
- regras de negócio
- controle de estoque
- funções de agregação como COUNT e SUM