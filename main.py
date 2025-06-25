#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
import time
import subprocess
import os
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.common.exceptions import TimeoutException, NoSuchElementException

def configurar_driver():
    """Configura e retorna o driver do Chrome com opções otimizadas - MODO INVISÍVEL"""
    chrome_options = Options()
    
    # 🔥 CONFIGURAÇÕES PARA MODO INVISÍVEL (HEADLESS)
    chrome_options.add_argument("--headless=new")  # Modo invisível mais moderno
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")  # Desabilita GPU (importante para headless)
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option('useAutomationExtension', False)
    chrome_options.add_argument("--user-agent=Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
    
    # Configurações adicionais para estabilidade em modo invisível
    chrome_options.add_argument("--disable-extensions")
    chrome_options.add_argument("--disable-web-security")
    chrome_options.add_argument("--allow-running-insecure-content")
    chrome_options.add_argument("--disable-features=VizDisplayCompositor")
    chrome_options.add_argument("--disable-logging")
    chrome_options.add_argument("--silent")
    chrome_options.add_argument("--window-size=1920,1080")  # Define tamanho mesmo invisível
    chrome_options.add_argument("--disable-background-timer-throttling")
    chrome_options.add_argument("--disable-backgrounding-occluded-windows")
    chrome_options.add_argument("--disable-renderer-backgrounding")
    
    # Método 1: Usar WebDriver Manager (recomendado para compatibilidade)
    try:
        print("🔍 Configurando Chrome invisível com WebDriver Manager...")
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=chrome_options)
        return driver
    except Exception as e:
        print(f"Erro com WebDriver Manager: {e}")
    
    # Método 2: Usar método direto do Chrome (Windows)
    try:
        print("🔍 Última tentativa - Chrome invisível com configurações específicas...")
        driver = webdriver.Chrome(options=chrome_options)
        return driver
    except Exception as e:
        print(f"Erro na configuração invisível: {e}")
        
    return None

def buscar_produtos_patrocinados(produto, max_tentativas=2):
    """
    Busca produto no Google Shopping com sistema de retry
    """
    for tentativa in range(max_tentativas):
        driver = None
        try:
            print(f"📡 Tentativa {tentativa + 1} de {max_tentativas}")
            driver = configurar_driver()
            
            resultados = {
                "produto_buscado": produto,
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                "produtos_patrocinados": []
            }
            
            print(f"🌐 Acessando Google Shopping...")
            driver.get("https://www.google.com/shopping?hl=pt-BR")
            
            # Aguarda a página carregar com timeout maior
            wait = WebDriverWait(driver, 20)
            
            print(f"🔍 Procurando campo de busca...")
            # Tenta diferentes seletores para o campo de busca
            campo_busca = None
            seletores_busca = ["#APjFqb", "input[name='q']", "input[type='search']"]
            
            for seletor in seletores_busca:
                try:
                    campo_busca = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, seletor)))
                    break
                except TimeoutException:
                    continue
            
            if not campo_busca:
                raise Exception("Campo de busca não encontrado")
            
            print(f"📝 Digitando: {produto}")
            campo_busca.clear()
            time.sleep(1)
            
            # Digita o produto caractere por caractere para evitar detecção
            for char in produto:
                campo_busca.send_keys(char)
                time.sleep(0.1)
            
            time.sleep(2)
            campo_busca.send_keys(Keys.ENTER)
            
            print("⏳ Aguardando resultados carregarem...")
            time.sleep(8)  # Aumentado o tempo de espera
            
            print("🎯 Procurando produtos patrocinados...")
            
            # Tenta diferentes padrões de produtos
            produtos_encontrados = []
            seletores_produtos = [
                "[id^='vplahcl_']",
                "[data-docid][jscontroller]", 
                ".sh-dgr__content",
                ".PLla-d",
                "[role='listitem']"
            ]
            
            for seletor in seletores_produtos:
                elementos = driver.find_elements(By.CSS_SELECTOR, seletor)
                if elementos:
                    produtos_encontrados = elementos
                    print(f"✅ Encontrados {len(elementos)} elementos com seletor: {seletor}")
                    break
            
            if not produtos_encontrados:
                print("⚠️ Nenhum produto encontrado, tentando busca mais ampla...")
                produtos_encontrados = driver.find_elements(By.CSS_SELECTOR, "div[data-hveid], div[data-ved]")
            
            print(f"📦 Processando {len(produtos_encontrados)} elementos...")
            
            for i, produto_elem in enumerate(produtos_encontrados[:20]):
                try:
                    produto_info = extrair_info_produto_melhorado(produto_elem, driver, i)
                    if produto_info and any(produto_info.values()):
                        resultados["produtos_patrocinados"].append(produto_info)
                        print(f"✅ Produto {i+1}: {produto_info.get('nome', 'N/A')[:50]}...")
                except Exception as e:
                    continue
            
            return resultados
            
        except Exception as e:
            print(f"❌ Erro na tentativa {tentativa + 1}: {e}")
            if tentativa < max_tentativas - 1:
                print("🔄 Tentando novamente em 5 segundos...")
                time.sleep(5)
        finally:
            if driver:
                try:
                    driver.quit()
                except:
                    pass
    
    # Se chegou aqui, todas as tentativas falharam
    return {
        "produto_buscado": produto,
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "produtos_patrocinados": []
    }

def extrair_info_produto_melhorado(elemento, driver, index):
    """Versão melhorada da extração com mais fallbacks e debug"""
    produto_info = {
        "nome": None,
        "preco": None,
        "loja": None,
        "link": None
    }
    
    try:
        # Debug: imprimir o HTML do elemento para análise
        if index < 3:  # Só para os primeiros elementos para não poluir
            try:
                html_snippet = elemento.get_attribute('outerHTML')[:500]
                print(f"DEBUG - Elemento {index+1} HTML: {html_snippet}...")
            except:
                pass
        
        # Extração do nome - baseado na estrutura real do Google Shopping
        seletores_nome = [
            "span.pymv4e",  # Classe específica vista na imagem
            "span[class*='pymv4e']",
            ".pymv4e",
            "h3", "h4", "h2",
            "[aria-label]",
            "[title]",
            ".sh-np__product-title",
            ".PLla-d",
            "a[href] span",
            "a[href] div",
            "span[role='link']",
            "*[class*='title']",
            "*[class*='name']",
            "*[class*='product']"
        ]
        
        for seletor in seletores_nome:
            try:
                elementos_nome = elemento.find_elements(By.CSS_SELECTOR, seletor)
                for elem in elementos_nome:
                    # Tenta diferentes métodos para extrair o texto
                    textos_possiveis = [
                        elem.text.strip(),
                        elem.get_attribute("textContent"),
                        elem.get_attribute("innerText"),
                        elem.get_attribute("title"),
                        elem.get_attribute("aria-label")
                    ]
                    
                    for texto in textos_possiveis:
                        if texto and len(texto) > 5 and not texto.startswith('R$'):
                            # Filtra textos que claramente não são nomes de produto
                            texto_lower = texto.lower()
                            filtros_invalidos = [
                                'custava', 'reais', 'ver mais', 'comprar', 'classificado como',
                                'estrelas', 'avaliação', 'nota', 'rating', 'review',
                                'de 5', 'promoção', 'desconto', 'frete', 'de amazon',
                                'de mercadolivre', 'de pichau', 'de kabum'
                            ]
                            
                            if not any(filtro in texto_lower for filtro in filtros_invalidos):
                                produto_info["nome"] = texto
                                break
                    
                    if produto_info["nome"]:
                        break
                
                if produto_info["nome"]:
                    break
            except:
                continue
        
        # Extração via JavaScript para casos difíceis
        if not produto_info["nome"]:
            try:
                js_script = """
                function findProductName(element) {
                    // Procura especificamente pela classe pymv4e
                    let nameElement = element.querySelector('span.pymv4e');
                    if (nameElement && nameElement.textContent) {
                        return nameElement.textContent.trim();
                    }
                    
                    // Fallback: procura por spans com texto relevante
                    const spans = element.querySelectorAll('span');
                    for (let span of spans) {
                        const text = span.textContent || span.innerText || '';
                        if (text.length > 10 && 
                            !text.includes('R$') && 
                            !text.includes('Custava') &&
                            !text.includes('De ') &&
                            !text.includes('Classificado') &&
                            !text.includes('estrelas')) {
                            return text.trim();
                        }
                    }
                    
                    return null;
                }
                return findProductName(arguments[0]);
                """
                
                nome_js = driver.execute_script(js_script, elemento)
                if nome_js and len(nome_js) > 5:
                    produto_info["nome"] = nome_js
            except:
                pass
        
        # Se não encontrou nome pelos seletores, analisa todo o texto do elemento
        if not produto_info["nome"]:
            try:
                texto_completo = elemento.text.strip()
                if texto_completo:
                    linhas = [linha.strip() for linha in texto_completo.split('\n') if linha.strip()]
                    
                    # Procura a primeira linha que parece ser um nome de produto
                    for linha in linhas:
                        if (len(linha) > 8 and 
                            not linha.startswith('R$') and 
                            'custava' not in linha.lower() and
                            'reais' not in linha.lower() and
                            not linha.isdigit()):
                            produto_info["nome"] = linha
                            break
            except:
                pass
        
        # Extração do preço - versão melhorada baseado na estrutura real
        if not produto_info["preco"]:
            # Força o carregamento de conteúdo dinâmico
            try:
                driver.execute_script("arguments[0].scrollIntoView(true);", elemento)
                time.sleep(0.5)
            except:
                pass
            
            # Seletores específicos para preços no Google Shopping
            seletores_preco_especificos = [
                "div[class*='qptdjc']",  # Classe comum para preços
                "span[class*='qptdjc']",
                ".qptdjc",
                "div[style*='webkit-line-clamp']",  # Preços com truncamento
                "[class*='13vB']",  # Padrão de classe para preços
                "[class*='RRDx']",  # Outro padrão comum
                "[class*='hdYIY']",  # Classe encontrada no debug
                "div[data-offer-id] span",
                "div[data-offer-id] div"
            ]
            
            for seletor in seletores_preco_especificos:
                try:
                    elementos_preco = elemento.find_elements(By.CSS_SELECTOR, seletor)
                    for elem_preco in elementos_preco:
                        # Tenta diferentes atributos e propriedades
                        textos_possiveis = [
                            elem_preco.text.strip(),
                            elem_preco.get_attribute("textContent"),
                            elem_preco.get_attribute("innerText"),
                            elem_preco.get_attribute("aria-label"),
                            elem_preco.get_attribute("title")
                        ]
                        
                        for texto_preco in textos_possiveis:
                            if texto_preco and 'R$' in texto_preco:
                                import re
                                # Limpa e valida o preço
                                match = re.search(r'R\$\s*[\d,.]+', texto_preco)
                                if match:
                                    produto_info["preco"] = match.group(0)
                                    break
                        
                        if produto_info["preco"]:
                            break
                    
                    if produto_info["preco"]:
                        break
                except:
                    continue
        
        # Extração via JavaScript como alternativa
        if not produto_info["preco"]:
            try:
                # Usa JavaScript para procurar preços no elemento
                js_script = r"""
                function findPriceInElement(element) {
                    // Procura por elementos que contêm R$
                    const allElements = element.querySelectorAll('*');
                    for (let el of allElements) {
                        const text = el.textContent || el.innerText || '';
                        if (text.includes('R$') && text.match(/R\$\s*[\d,.]+/)) {
                            return text.match(/R\$\s*[\d,.]+/)[0];
                        }
                    }
                    return null;
                }
                return findPriceInElement(arguments[0]);
                """
                
                preco_js = driver.execute_script(js_script, elemento)
                if preco_js:
                    produto_info["preco"] = preco_js.strip()
            except:
                pass
        
        # Debug adicional para preços (apenas primeiros elementos)
        if index < 3:
            try:
                # Mostra todos os elementos que contêm R$ para debug
                elementos_com_rs = elemento.find_elements(By.XPATH, ".//*[contains(text(), 'R$')]")
                if elementos_com_rs:
                    print(f"DEBUG - Elementos com R$ encontrados no produto {index+1}:")
                    for i, elem in enumerate(elementos_com_rs[:3]):  # Mostra apenas os 3 primeiros
                        try:
                            texto = elem.text.strip()
                            classe = elem.get_attribute("class")
                            print(f"  - Elemento {i+1}: '{texto}' (classe: {classe})")
                        except:
                            pass
            except:
                pass
        
        # Extração da loja do link se não encontrou por seletores
        try:
            # Primeiro tenta encontrar um link
            link_elem = None
            if elemento.tag_name == "a":
                link_elem = elemento
            else:
                link_elem = elemento.find_element(By.CSS_SELECTOR, "a[href]")
            
            if link_elem:
                link = link_elem.get_attribute("href")
                produto_info["link"] = link
                
                # Extrai loja do domínio
                if link:
                    import re
                    match = re.search(r'https?://(?:www\.)?([^/]+)', link)
                    if match:
                        dominio = match.group(1)
                        if 'amazon' in dominio:
                            produto_info["loja"] = "Amazon"
                        elif 'mercadolivre' in dominio:
                            produto_info["loja"] = "Mercado Livre"
                        elif 'pichau' in dominio:
                            produto_info["loja"] = "Pichau"
                        elif 'kabum' in dominio:
                            produto_info["loja"] = "KaBuM!"
                        else:
                            # Pega o nome principal do domínio
                            nome_loja = dominio.split('.')[0].replace('www', '').strip()
                            if nome_loja:
                                produto_info["loja"] = nome_loja.capitalize()
        except:
            pass
        
        # Se ainda não tem nome, tenta extrair do link
        if not produto_info["nome"] and produto_info["link"]:
            try:
                from urllib.parse import unquote
                link = unquote(produto_info["link"])
                
                # Tenta extrair nome do produto da URL
                import re
                patterns = [
                    r'/([^/]+?)(?:-\d+|/dp/|/p/)',  # Amazon e Mercado Livre
                    r'/([^/]+?)(?:\?|$)',           # Genérico
                ]
                
                for pattern in patterns:
                    match = re.search(pattern, link)
                    if match:
                        nome_url = match.group(1)
                        # Limpa e formata o nome
                        nome_url = nome_url.replace('-', ' ').replace('_', ' ')
                        nome_url = re.sub(r'%[0-9A-F]{2}', ' ', nome_url)  # Remove códigos URL
                        nome_url = ' '.join(nome_url.split())  # Remove espaços extras
                        
                        if len(nome_url) > 5:
                            produto_info["nome"] = nome_url
                            break
            except:
                pass
        
        return produto_info
        
    except Exception as e:
        print(f"Erro ao processar elemento {index}: {e}")
        return produto_info

def extrair_produtos_generico(driver):
    """Abordagem genérica para extrair produtos quando os seletores específicos falham"""
    produtos = []
    
    try:
        seletores_produtos = [
            ".sh-dgr__content",
            "[data-docid]",
            ".PLla-d",
            ".sh-dlr__list-result"
        ]
        
        for seletor in seletores_produtos:
            elementos = driver.find_elements(By.CSS_SELECTOR, seletor)
            if elementos:
                print(f"Encontrados {len(elementos)} produtos com seletor: {seletor}")
                
                for i, elem in enumerate(elementos[:10]):
                    try:
                        produto = {
                            "nome": None,
                            "preco": None,
                            "loja": None,
                            "link": None
                        }
                        
                        # Tenta extrair nome
                        try:
                            nome = elem.find_element(By.CSS_SELECTOR, "h3, [role='link'], .sh-dlr__list-result-title")
                            produto["nome"] = nome.text.strip()
                        except:
                            pass
                        
                        # Tenta extrair preço
                        try:
                            preco = elem.find_element(By.CSS_SELECTOR, "[aria-label*='R$'], .a-price, .sh-dlr__list-result-price")
                            produto["preco"] = preco.text.strip() or preco.get_attribute("aria-label")
                        except:
                            pass
                        
                        # Tenta extrair loja
                        try:
                            loja = elem.find_element(By.CSS_SELECTOR, ".sh-dlr__list-result-merchant, [data-test-id='merchant-name']")
                            produto["loja"] = loja.text.strip()
                        except:
                            pass
                        
                        # Tenta extrair link
                        try:
                            link = elem.find_element(By.CSS_SELECTOR, "a[href]")
                            produto["link"] = link.get_attribute("href")
                        except:
                            pass
                        
                        if any(produto.values()):
                            produtos.append(produto)
                            
                    except Exception as e:
                        continue
                
                if produtos:
                    break
                    
    except Exception as e:
        print(f"Erro na extração genérica: {e}")
    
    return produtos

def salvar_resultados(resultados, nome_arquivo="resultados_google_shopping.json"):
    """Salva os resultados em um arquivo JSON"""
    try:
        with open(nome_arquivo, 'w', encoding='utf-8') as f:
            json.dump(resultados, f, indent=2, ensure_ascii=False)
        print(f"\nResultados salvos em: {nome_arquivo}")
        return True
    except Exception as e:
        print(f"Erro ao salvar arquivo: {e}")
        return False

def main(produto_busca):
    """Função principal"""
    print("=== Buscador de Produtos Google Shopping (Área Patrocinados) ===\n")
    
    #produto_busca = input("Digite o nome do produto que deseja buscar: ").strip()
    
    if not produto_busca:
        print("Erro: Você deve digitar um produto para buscar.")
        return
    
    print(f"\nIniciando busca por: '{produto_busca}'")
    print("Focando na área de produtos patrocinados...")
    print("Isso pode levar alguns segundos...\n")
    
    resultados = buscar_produtos_patrocinados(produto_busca)
    
    print(f"\n" + "="*50)
    print(f"RESULTADOS DA BUSCA")
    print(f"="*50)
    print(f"Produto buscado: {resultados['produto_buscado']}")
    print(f"Produtos encontrados: {len(resultados['produtos_patrocinados'])}")
    print(f"Timestamp: {resultados['timestamp']}")
    
    if resultados['produtos_patrocinados']:
        print(f"\n" + "="*50)
        print("PRODUTOS PATROCINADOS ENCONTRADOS")
        print("="*50)
        
        for i, produto_info in enumerate(resultados['produtos_patrocinados'], 1):
            print(f"\n[PRODUTO {i}]")
            print(f"Nome: {produto_info.get('nome', 'N/A')}")
            print(f"Preço: {produto_info.get('preco', 'N/A')}")
            print(f"Loja: {produto_info.get('loja', 'N/A')}")
            print(f"Link: {produto_info.get('link', 'N/A')}")
            print("-" * 40)
    else:
        print("\n❌ Nenhum produto patrocinado foi encontrado.")
        print("Isso pode acontecer se:")
        print("- Não há produtos patrocinados para este termo")
        print("- O Google mudou a estrutura da página")
        print("- Há bloqueios anti-bot ativos")
    
    nome_arquivo = f"C:\\Users\\amand\\meiu\\monitoramento-inteligente-precos\\resultados\\resultado_{produto_busca.replace(' ', '_').lower().replace('/', '_')}.json"
    if salvar_resultados(resultados, nome_arquivo):
        print(f"\n✅ Busca concluída! Verifique o arquivo '{nome_arquivo}' para todos os resultados.")
    
    return resultados

if __name__ == "__main__":
    # Verificar se o arquivo produtos_temp.txt existe e usá-lo para buscas
    try:
        from multi_buscador import MultiBuscador
        
        # Carregar produtos do arquivo
        produtos_para_buscar = []
        arquivo_produtos = 'produtos_temp.txt'
        
        # Se arquivo temporário existe, usar ele, senão usar produtos.txt padrão
        if os.path.exists(arquivo_produtos):
            with open(arquivo_produtos, 'r', encoding='utf-8') as f:
                produtos_para_buscar = [linha.strip() for linha in f if linha.strip()]
        else:
            # Verificar se produtos.txt existe
            if os.path.exists('produtos.txt'):
                with open('produtos.txt', 'r', encoding='utf-8') as f:
                    produtos_para_buscar = [linha.strip() for linha in f if linha.strip()]
            else:
                produtos_para_buscar = ['PAINEL CAEMMUN ESMERALDA 1,50']
        
        print(f"Iniciando busca para {len(produtos_para_buscar)} produtos...")
        
        # Usando o MultiBuscador para processar múltiplos produtos
        buscador = MultiBuscador()
        if len(produtos_para_buscar) == 1:
            # Para um único produto, executar diretamente
            main(produto_busca=produtos_para_buscar[0])
        else:
            # Para múltiplos produtos, usar o buscador multithreaded
            buscador.executar_buscas_simultaneas(produtos_para_buscar, max_threads=3)
            
        # Remover arquivo temporário após processamento
        if os.path.exists('produtos_temp.txt'):
            try:
                os.remove('produtos_temp.txt')
            except:
                pass
            
    except Exception as e:
        print(f"Erro ao executar buscas: {e}")
        # Se ocorrer erro, tentar executar pelo menos um produto padrão
        main(produto_busca='PAINEL CAEMMUN ESMERALDA 1,50')