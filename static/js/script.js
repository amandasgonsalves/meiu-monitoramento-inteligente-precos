// Script para o Sistema de Monitoramento de Preços

document.addEventListener('DOMContentLoaded', function() {
    // Exibir modal de carregamento durante submissão de formulários
    const forms = document.querySelectorAll('form');
    forms.forEach(form => {
        form.addEventListener('submit', function() {
            const loadingModal = new bootstrap.Modal(document.getElementById('loadingModal'));
            loadingModal.show();
        });
    });
    
    // Ordenar tabelas de produtos
    const sortTables = () => {
        document.querySelectorAll('.sort-header').forEach(header => {
            header.addEventListener('click', function() {
                const tableBody = this.closest('table').querySelector('tbody');
                const rows = Array.from(tableBody.querySelectorAll('tr'));
                const index = Array.from(this.parentNode.children).indexOf(this);
                const direction = this.classList.contains('sort-asc') ? -1 : 1;
                
                // Alternar classes para indicar direção da ordenação
                if (this.classList.contains('sort-asc')) {
                    this.classList.remove('sort-asc');
                    this.classList.add('sort-desc');
                } else {
                    document.querySelectorAll('.sort-header').forEach(el => {
                        el.classList.remove('sort-asc', 'sort-desc');
                    });
                    this.classList.add('sort-asc');
                }
                
                // Ordenar linhas
                const sortedRows = rows.sort((a, b) => {
                    const cellA = a.querySelectorAll('td')[index].textContent.trim();
                    const cellB = b.querySelectorAll('td')[index].textContent.trim();
                    
                    // Verificar se é um preço
                    if (cellA.startsWith('R$') && cellB.startsWith('R$')) {
                        const priceA = parseFloat(cellA.replace('R$', '').replace('.', '').replace(',', '.').trim());
                        const priceB = parseFloat(cellB.replace('R$', '').replace('.', '').replace(',', '.').trim());
                        return direction * (priceA - priceB);
                    }
                    
                    // Ordenação de texto comum
                    return direction * cellA.localeCompare(cellB);
                });
                
                // Reordenar a tabela
                tableBody.innerHTML = '';
                sortedRows.forEach(row => tableBody.appendChild(row));
            });
        });
    };
    
    // Inicializar funções se as elementos existirem
    if (document.querySelector('.sort-header')) {
        sortTables();
    }
    
    // Adicionar funcionalidade de copiar links
    document.querySelectorAll('.copy-link').forEach(button => {
        button.addEventListener('click', function(e) {
            e.preventDefault();
            const link = this.getAttribute('data-link');
            navigator.clipboard.writeText(link)
                .then(() => {
                    // Alterar texto do botão temporariamente
                    const originalText = this.textContent;
                    this.textContent = 'Copiado!';
                    this.classList.add('btn-success');
                    this.classList.remove('btn-outline-secondary');
                    
                    setTimeout(() => {
                        this.textContent = originalText;
                        this.classList.remove('btn-success');
                        this.classList.add('btn-outline-secondary');
                    }, 2000);
                })
                .catch(err => {
                    console.error('Erro ao copiar: ', err);
                });
        });
    });
});
