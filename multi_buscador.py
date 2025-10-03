#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import time
import json
import os
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timedelta
import subprocess
import sys
from queue import Queue

# Importa o script original (assumindo que está salvo como 'busca_shopping.py')
# Se o nome do arquivo for diferente, altere aqui
try:
    from main import main as buscar_produtos_patrocinados
except ImportError:
    print(" Erro: Não foi possível importar o script 'main.py'")
    print("Certifique-se de que o arquivo está no mesmo diretório.")
    sys.exit(1)

class MultiBuscador:
    def __init__(self):
        self.resultados = {}
        self.tempos_individuais = {}
        self.inicio_geral = None
        self.fim_geral = None
        self.lock = threading.Lock()  # Para sincronização de threads
        
    def buscar_produto_com_tempo(self, produto, thread_id):
        """Executa uma busca individual e mede o tempo"""
        print(f" [Thread {thread_id}] Iniciando busca: '{produto}'")
        inicio_produto = time.time()
        
        try:
            # Chama a função do script original
            resultado = buscar_produtos_patrocinados(produto)
            fim_produto = time.time()
            tempo_gasto = fim_produto - inicio_produto
            
            # Thread-safe para armazenar resultados
            with self.lock:
                self.resultados[produto] = resultado
                self.tempos_individuais[produto] = tempo_gasto
            
            print(f" [Thread {thread_id}] Concluída busca: '{produto}' ({tempo_gasto:.2f}s)")
            return {
                'produto': produto,
                'resultado': resultado,
                'tempo': tempo_gasto,
                'thread_id': thread_id,
                'sucesso': True
            }
            
        except Exception as e:
            fim_produto = time.time()
            tempo_gasto = fim_produto - inicio_produto
            
            with self.lock:
                self.tempos_individuais[produto] = tempo_gasto
                self.resultados[produto] = {
                    'erro': str(e),
                    'produto_buscado': produto,
                    'produtos_patrocinados': []
                }
            
            print(f" [Thread {thread_id}] Erro na busca '{produto}': {e} ({tempo_gasto:.2f}s)")
            return {
                'produto': produto,
                'resultado': None,
                'tempo': tempo_gasto,
                'thread_id': thread_id,
                'sucesso': False,
                'erro': str(e)
            }

    def executar_buscas_simultaneas(self, produtos, max_threads=3):
        """Executa múltiplas buscas simultaneamente"""
        print("="*70)
        print(" INICIANDO BUSCAS SIMULTÂNEAS NO GOOGLE SHOPPING")
        print("="*70)
        print(f" Produtos para buscar: {len(produtos)}")
        print(f" Threads simultâneas: {max_threads}")
        print(f" Início: {datetime.now().strftime('%H:%M:%S')}")
        print("-"*70)
        
        self.inicio_geral = time.time()
        resultados_threads = []
        
        # Executa buscas em paralelo
        with ThreadPoolExecutor(max_workers=max_threads) as executor:
            # Submete todas as tarefas
            futures = {
                executor.submit(self.buscar_produto_com_tempo, produto, i+1): produto 
                for i, produto in enumerate(produtos)
            }
            
            # Coleta resultados conforme completam
            for future in as_completed(futures):
                produto = futures[future]
                try:
                    resultado = future.result()
                    resultados_threads.append(resultado)
                except Exception as e:
                    print(f"❌ Erro crítico na thread do produto '{produto}': {e}")
                    resultados_threads.append({
                        'produto': produto,
                        'sucesso': False,
                        'erro': str(e),
                        'tempo': 0
                    })
        
        self.fim_geral = time.time()
        
        return self.gerar_relatorio_final(produtos, resultados_threads)

    def executar_buscas_sequenciais(self, produtos):
        """Executa buscas uma por vez (para comparação)"""
        print("="*70)
        print(" INICIANDO BUSCAS SEQUENCIAIS NO GOOGLE SHOPPING")
        print("="*70)
        print(f" Produtos para buscar: {len(produtos)}")
        print(f" Início: {datetime.now().strftime('%H:%M:%S')}")
        print("-"*70)
        
        self.inicio_geral = time.time()
        resultados_sequenciais = []
        
        for i, produto in enumerate(produtos, 1):
            print(f"\n[{i}/{len(produtos)}] Processando: '{produto}'")
            resultado = self.buscar_produto_com_tempo(produto, i)
            resultados_sequenciais.append(resultado)
        
        self.fim_geral = time.time()
        
        return self.gerar_relatorio_final(produtos, resultados_sequenciais)

    def gerar_relatorio_final(self, produtos, resultados_threads):
        """Gera relatório completo com estatísticas"""
        tempo_total = self.fim_geral - self.inicio_geral
        
        # Estatísticas
        buscas_sucessos = sum(1 for r in resultados_threads if r['sucesso'])
        buscas_falharam = len(produtos) - buscas_sucessos
        tempo_medio = tempo_total / len(produtos) if produtos else 0
        produtos_encontrados_total = 0
        
        # Conta produtos encontrados
        for produto in produtos:
            if produto in self.resultados:
                produtos_encontrados_total += len(self.resultados[produto].get('produtos_patrocinados', []))
        
        print("\n" + "="*70)
        print(" RELATÓRIO FINAL DE BUSCAS")
        print("="*70)
        print(f"  Tempo total gasto: {tempo_total:.2f} segundos ({tempo_total/60:.1f} minutos)")
        print(f" Tempo médio por busca: {tempo_medio:.2f} segundos")
        print(f" Buscas bem-sucedidas: {buscas_sucessos}/{len(produtos)}")
        print(f" Buscas falharam: {buscas_falharam}/{len(produtos)}")
        print(f"  Total de produtos encontrados: {produtos_encontrados_total}")
        print(f" Finalizado em: {datetime.now().strftime('%H:%M:%S')}")
        
        print("\n" + "="*70)
        print("⏱️  TEMPOS INDIVIDUAIS POR PRODUTO")
        print("="*70)
        
        for i, resultado in enumerate(sorted(resultados_threads, key=lambda x: x['tempo']), 1):
            produto = resultado['produto']
            tempo = resultado['tempo']
            status = "✅" if resultado['sucesso'] else "❌"
            produtos_encontrados = 0
            
            if produto in self.resultados:
                produtos_encontrados = len(self.resultados[produto].get('produtos_patrocinados', []))
            
            print(f"{status} [{i:2d}] {produto:<40} | {tempo:6.2f}s | {produtos_encontrados:2d} produtos")
        
        # Salva relatório consolidado
        relatorio_completo = {
            'resumo': {
                'inicio': datetime.fromtimestamp(self.inicio_geral).isoformat(),
                'fim': datetime.fromtimestamp(self.fim_geral).isoformat(),
                'tempo_total_segundos': tempo_total,
                'tempo_total_minutos': tempo_total / 60,
                'tempo_medio_por_busca': tempo_medio,
                'total_produtos_buscados': len(produtos),
                'buscas_sucessos': buscas_sucessos,
                'buscas_falharam': buscas_falharam,
                'total_produtos_encontrados': produtos_encontrados_total
            },
            'tempos_individuais': self.tempos_individuais,
            'resultados_detalhados': self.resultados,
            'produtos_buscados': produtos
        }
        
        nome_arquivo = f"relatorio_buscas_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        try:
            with open(nome_arquivo, 'w', encoding='utf-8') as f:
                json.dump(relatorio_completo, f, indent=2, ensure_ascii=False)
            print(f"\n Relatório completo salvo em: {nome_arquivo}")
        except Exception as e:
            print(f"\n Erro ao salvar relatório: {e}")
        
        return relatorio_completo

def comparar_tempos_sequencial_vs_paralelo(produtos, max_threads=3):
    """Compara execução sequencial vs paralela"""
    print(" INICIANDO COMPARAÇÃO: SEQUENCIAL vs PARALELO")
    print("="*70)
    
    # Teste sequencial
    buscador_seq = MultiBuscador()
    print(" Executando buscas SEQUENCIAIS...")
    relatorio_seq = buscador_seq.executar_buscas_sequenciais(produtos)
    tempo_sequencial = relatorio_seq['resumo']['tempo_total_segundos']
    
    print("\n" + " Aguardando 10 segundos entre testes...\n")
    time.sleep(10)
    
    # Teste paralelo
    buscador_par = MultiBuscador()
    print(" Executando buscas PARALELAS...")
    relatorio_par = buscador_par.executar_buscas_simultaneas(produtos, max_threads)
    tempo_paralelo = relatorio_par['resumo']['tempo_total_segundos']
    
    # Comparação
    economia_tempo = tempo_sequencial - tempo_paralelo
    percentual_melhoria = (economia_tempo / tempo_sequencial) * 100 if tempo_sequencial > 0 else 0
    
    print("\n" + "="*70)
    print(" COMPARAÇÃO FINAL")
    print("="*70)
    print(f"  Tempo sequencial: {tempo_sequencial:.2f}s ({tempo_sequencial/60:.1f}min)")
    print(f" Tempo paralelo:   {tempo_paralelo:.2f}s ({tempo_paralelo/60:.1f}min)")
    print(f" Economia de tempo: {economia_tempo:.2f}s ({economia_tempo/60:.1f}min)")
    print(f" Melhoria:          {percentual_melhoria:.1f}%")
    
    if economia_tempo > 0:
        print(f" Execução paralela foi {percentual_melhoria:.1f}% mais rápida!")
    else:
        print(" Execução sequencial foi mais rápida (possível overhead de threads)")

def carregar_produtos_do_arquivo(caminho_arquivo):
    """Carrega lista de produtos de um arquivo TXT (um produto por linha)"""
    try:
        produtos = []
        with open(caminho_arquivo, 'r', encoding='utf-8') as f:
            for linha in f:
                produto = linha.strip()
                if produto and not produto.startswith('#'):  # Ignora linhas vazias e comentários
                    produtos.append(produto)
        
        if not produtos:
            print(f" Arquivo '{caminho_arquivo}' está vazio ou não contém produtos válidos.")
            return None
            
        print(f" Carregados {len(produtos)} produtos do arquivo '{caminho_arquivo}'")
        return produtos
        
    except FileNotFoundError:
        print(f" Arquivo não encontrado: '{caminho_arquivo}'")
        return None
    except Exception as e:
        print(f" Erro ao ler arquivo '{caminho_arquivo}': {e}")
        return None

def main():
    """Função principal"""
    # Lista padrão de produtos para buscar
    produtos_para_buscar = [
    "SPLIT PHILCO PAC12000IFM15 INVERTER FRIO",
    "CLIMATIZADOR VENTISOL FRIO 16L CLIN16",
    "PAINEL CAEMMUN ESMERALDA 1,50",
    "CLIMATIZADOR BRITANIA FRIO BCL05FI 4L C/ CONTROLE"
   
]

    
    print(" SISTEMA DE BUSCAS MÚLTIPLAS - GOOGLE SHOPPING")
    print("="*70)
    print("Escolha uma opção:")
    print("1 - Executar buscas SIMULTÂNEAS (mais rápido)")
    print("2 - Executar buscas SEQUENCIAIS (uma por vez)")
    print("3 - COMPARAR ambos os métodos")
    print("4 - Usar lista personalizada de produtos (digitação manual)")
    print("5 - Carregar produtos de arquivo TXT")
    
    try:
        opcao = input("\nDigite sua opção (1-5): ").strip()
        
        if opcao == "4":
            print("\nDigite os produtos separados por vírgula:")
            entrada = input("Produtos: ").strip()
            if entrada:
                produtos_para_buscar = [p.strip() for p in entrada.split(',') if p.strip()]
            else:
                print("Usando lista padrão...")
                
        elif opcao == "5":
            print("\nOpções de arquivo:")
            print("1 - produtos.txt (arquivo padrão)")
            print("2 - Digitar nome do arquivo")
            
            arquivo_opcao = input("Escolha (1-2): ").strip()
            
            if arquivo_opcao == "1":
                caminho_arquivo = "produtos.txt"
            elif arquivo_opcao == "2":
                caminho_arquivo = input("Digite o nome/caminho do arquivo: ").strip()
            else:
                print("Opção inválida, usando produtos.txt")
                caminho_arquivo = "produtos.txt"
            
            produtos_carregados = carregar_produtos_do_arquivo(caminho_arquivo)
            if produtos_carregados:
                produtos_para_buscar = produtos_carregados
            else:
                print("Usando lista padrão...")
        
        max_threads = 3
        if opcao in ["1", "3"]:
            try:
                threads_input = input(f"\nQuantas threads simultâneas usar? (padrão: {max_threads}): ").strip()
                if threads_input:
                    max_threads = int(threads_input)
                    max_threads = max(1, min(max_threads, 10))  # Limita entre 1-10
            except ValueError:
                print(f"Valor inválido, usando padrão: {max_threads}")
        
        print(f"\n📋 Produtos selecionados: {len(produtos_para_buscar)}")
        for i, produto in enumerate(produtos_para_buscar, 1):
            print(f"   {i}. {produto}")
        
        if opcao == "1":
            buscador = MultiBuscador()
            buscador.executar_buscas_simultaneas(produtos_para_buscar, max_threads)
            
        elif opcao == "2":
            buscador = MultiBuscador()
            buscador.executar_buscas_sequenciais(produtos_para_buscar)
            
        elif opcao == "3":
            comparar_tempos_sequencial_vs_paralelo(produtos_para_buscar, max_threads)
            
        else:
            print(" Opção inválida!")
            return
            
    except KeyboardInterrupt:
        print("\n\n⏹️ Operação cancelada pelo usuário.")
    except Exception as e:
        print(f"\n Erro inesperado: {e}")

if __name__ == "__main__":
    main()
