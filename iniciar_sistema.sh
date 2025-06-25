#!/bin/bash

echo "===================================================="
echo "  Sistema de Monitoramento Inteligente de Precos"
echo "===================================================="
echo ""
echo "Iniciando servidor web..."
echo ""
echo "Aguarde um momento enquanto o sistema inicia..."
echo "Acesse http://localhost:5000 em seu navegador."
echo ""
echo "Para encerrar o servidor, pressione CTRL+C nesta janela."
echo "===================================================="
echo ""

# Verificar se o Python está instalado
if ! command -v python3 &> /dev/null; then
    echo "ERRO: Python não encontrado! Verifique se o Python está instalado."
    exit 1
fi

# Verificar se os pacotes necessários estão instalados
echo "Verificando dependências..."
python3 -m pip install -r requirements.txt

# Criar diretórios necessários se não existirem
mkdir -p static/css
mkdir -p static/js
mkdir -p templates
mkdir -p resultados

# Iniciar o servidor web
python3 app.py
