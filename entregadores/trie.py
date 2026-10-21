#Trie compacta 


class No:
    __slots__ = ("rotulo", "filhos", "valores")

    def __init__(self, rotulo=""):
        self.rotulo = rotulo
        self.filhos = {}
        self.valores = []  # ids de entregadores em que o geohash termina neste nó


class TrieCompacta:
    def __init__(self):
        self.raiz = No()
        self.tamanho = 0

    def inserir(self, chave, valor):
        no = self.raiz
        i = 0
        while True:
            if i == len(chave):
                no.valores.append(valor)
                self.tamanho += 1
                return
            c = chave[i]
            filho = no.filhos.get(c)
            if filho is None:
                novo = No(chave[i:])
                novo.valores.append(valor)
                no.filhos[c] = novo
                self.tamanho += 1
                return
            # tamanho do prefixo comum entre o rótulo da aresta e o resto da chave
            j = 0
            while (j < len(filho.rotulo) and i + j < len(chave)
                   and filho.rotulo[j] == chave[i + j]):
                j += 1
            if j == len(filho.rotulo):  # aresta inteira casou: desce
                no = filho
                i += j
                continue
            # casamento parcial: divide a aresta em duas
            meio = No(filho.rotulo[:j])
            filho.rotulo = filho.rotulo[j:]
            meio.filhos[filho.rotulo[0]] = filho
            no.filhos[c] = meio
            no = meio
            i += j

    def buscar_prefixo(self, prefixo):
        #Todos os valores cujas chaves começam com o prefixo
        no = self.raiz
        i = 0
        while i < len(prefixo):
            filho = no.filhos.get(prefixo[i])
            if filho is None:
                return []
            restante = prefixo[i:]
            n = min(len(filho.rotulo), len(restante))
            if filho.rotulo[:n] != restante[:n]:
                return []
            i += n  # se o prefixo termina no meio da aresta, o laço acaba aqui
            no = filho
        return self._coletar(no)

    @staticmethod
    def _coletar(no):
        resultado = []
        pilha = [no]
        while pilha:
            atual = pilha.pop()
            resultado.extend(atual.valores)
            pilha.extend(atual.filhos.values())
        return resultado

    def contar_nos(self):
        total = 0
        pilha = [self.raiz]
        while pilha:
            atual = pilha.pop()
            total += 1
            pilha.extend(atual.filhos.values())
        return total
