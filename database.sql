
CREATE DATABASE IF NOT EXISTS farmacia_estoque
  CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

USE farmacia_estoque;


CREATE TABLE IF NOT EXISTS fornecedores (
    id INT AUTO_INCREMENT PRIMARY KEY,
    nome VARCHAR(150) NOT NULL,
    cnpj VARCHAR(18) UNIQUE,
    telefone VARCHAR(20),
    email VARCHAR(150),
    endereco VARCHAR(255),
    ativo TINYINT(1) NOT NULL DEFAULT 1,
    criado_em DATETIME DEFAULT CURRENT_TIMESTAMP,
    atualizado_em DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB;


CREATE TABLE IF NOT EXISTS produtos (
    id INT AUTO_INCREMENT PRIMARY KEY,
    nome VARCHAR(150) NOT NULL,
    descricao VARCHAR(255),
    categoria VARCHAR(80),
    fornecedor_id INT,
    lote VARCHAR(50),
    data_validade DATE,
    unidade_medida VARCHAR(20) NOT NULL DEFAULT 'un',
    preco_custo DECIMAL(10,2) NOT NULL DEFAULT 0.00,
    preco_venda DECIMAL(10,2) NOT NULL DEFAULT 0.00,
    quantidade_estoque INT NOT NULL DEFAULT 0,
    quantidade_minima INT NOT NULL DEFAULT 5,
    ativo TINYINT(1) NOT NULL DEFAULT 1,
    criado_em DATETIME DEFAULT CURRENT_TIMESTAMP,
    atualizado_em DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    CONSTRAINT fk_produto_fornecedor
        FOREIGN KEY (fornecedor_id) REFERENCES fornecedores(id)
        ON DELETE SET NULL
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS movimentacoes (
    id INT AUTO_INCREMENT PRIMARY KEY,
    produto_id INT NOT NULL,
    tipo ENUM('entrada', 'saida') NOT NULL,
    quantidade INT NOT NULL,
    motivo VARCHAR(255),
    responsavel VARCHAR(100),
    data_movimentacao DATETIME DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_movimentacao_produto
        FOREIGN KEY (produto_id) REFERENCES produtos(id)
        ON DELETE CASCADE
) ENGINE=InnoDB;

-- Índices para melhorar performance de consultas
CREATE INDEX idx_produtos_categoria ON produtos(categoria);
CREATE INDEX idx_produtos_fornecedor ON produtos(fornecedor_id);
CREATE INDEX idx_movimentacoes_produto ON movimentacoes(produto_id);
CREATE INDEX idx_movimentacoes_data ON movimentacoes(data_movimentacao);


INSERT INTO fornecedores (nome, cnpj, telefone, email, endereco) VALUES
('Distribuidora Saúde Total', '12.345.678/0001-90', '(31) 3333-1111', 'contato@saudetotal.com.br', 'Rua das Farmácias, 100 - Betim/MG'),
('Farmaco Distribuição', '98.765.432/0001-10', '(31) 3333-2222', 'vendas@farmaco.com.br', 'Av. Industrial, 500 - Contagem/MG');

INSERT INTO produtos (nome, descricao, categoria, fornecedor_id, lote, data_validade, unidade_medida, preco_custo, preco_venda, quantidade_estoque, quantidade_minima) VALUES
('Dipirona Sódica 500mg', 'Caixa com 10 comprimidos', 'Analgésico', 1, 'L2026A', '2027-06-30', 'cx', 3.50, 7.90, 50, 10),
('Paracetamol 750mg', 'Caixa com 20 comprimidos', 'Analgésico', 1, 'L2026B', '2027-08-15', 'cx', 5.20, 11.50, 30, 10),
('Amoxicilina 500mg', 'Caixa com 21 cápsulas', 'Antibiótico', 2, 'L2026C', '2026-12-01', 'cx', 12.00, 24.90, 15, 5),
('Álcool Gel 70% 500ml', 'Frasco higienizador', 'Higiene', 2, 'L2026D', '2028-01-10', 'un', 6.00, 12.90, 8, 10);
