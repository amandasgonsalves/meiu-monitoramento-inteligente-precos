from flask import Flask, render_template, request, redirect, url_for, flash
import json
import os
from datetime import datetime
import time
import subprocess
import glob
import sys

app = Flask(__name__)
app.secret_key = 'monitoramento_inteligente_precos'

# Diretório onde os relatórios são armazenados
RELATORIOS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), '')

@app.route('/')
def index():
    """Página inicial com formulários de busca"""
    # Encontrar todos os arquivos de relatório
    relatorios = []
    for file in glob.glob(os.path.join(RELATORIOS_DIR, 'relatorio_buscas_*.json')):
        relatorios.append(os.path.basename(file))
    relatorios.sort(reverse=True)  # Mais recente primeiro
    
    return render_template('index.html', relatorios=relatorios)

@app.route('/buscar', methods=['POST'])
def buscar():
    """Processa a busca de produtos e redireciona para resultados"""
    tipo_busca = request.form.get('tipo_busca')
    
    # Preparar lista de produtos para busca
    if tipo_busca == 'individual':
        produtos = [request.form.get('produto')]
    else:
        produtos = request.form.get('produtos').strip().split('\n')
        # Remover linhas vazias
        produtos = [p.strip() for p in produtos if p.strip()]
    
    # Salvar produtos em arquivo temporário
    with open('produtos_temp.txt', 'w', encoding='utf-8') as f:
        for produto in produtos:
            f.write(f"{produto}\n")
    
    # Executar busca (chamando script principal)
    try:
        subprocess.run([sys.executable, 'main.py'], check=True)
        
        # Encontrar o relatório mais recente
        relatorios = sorted(glob.glob(os.path.join(RELATORIOS_DIR, 'relatorio_buscas_*.json')), reverse=True)
        if relatorios:
            ultimo_relatorio = os.path.basename(relatorios[0])
            return redirect(url_for('ver_relatorio', nome_relatorio=ultimo_relatorio))
        else:
            flash('Erro: Nenhum relatório foi gerado')
            return redirect(url_for('index'))
    except subprocess.CalledProcessError:
        flash('Erro ao executar a busca. Verifique o console para mais detalhes.')
        return redirect(url_for('index'))

@app.route('/relatorio/<nome_relatorio>')
def ver_relatorio(nome_relatorio):
    """Exibe um relatório específico"""
    try:
        caminho_relatorio = os.path.join(RELATORIOS_DIR, nome_relatorio)
        with open(caminho_relatorio, 'r', encoding='utf-8') as f:
            relatorio = json.load(f)
        
        return render_template('relatorio.html', relatorio=relatorio, nome_relatorio=nome_relatorio)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        flash(f'Erro ao carregar relatório: {str(e)}')
        return redirect(url_for('index'))

@app.template_filter('format_datetime')
def format_datetime(value):
    """Formata timestamps para exibição"""
    if isinstance(value, str):
        try:
            dt = datetime.fromisoformat(value)
            return dt.strftime('%d/%m/%Y %H:%M:%S')
        except ValueError:
            return value
    return value

if __name__ == '__main__':
    # Criar diretórios necessários se não existirem
    os.makedirs(os.path.join(os.path.dirname(__file__), 'static', 'css'), exist_ok=True)
    os.makedirs(os.path.join(os.path.dirname(__file__), 'static', 'js'), exist_ok=True)
    os.makedirs(os.path.join(os.path.dirname(__file__), 'templates'), exist_ok=True)
    
    # Iniciar aplicação
    app.run(debug=True, host='0.0.0.0', port=5000)
