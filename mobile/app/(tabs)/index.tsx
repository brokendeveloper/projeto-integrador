import { useState, useCallback } from "react";
import {
  View,
  Text,
  TextInput,
  FlatList,
  TouchableOpacity,
  StyleSheet,
  ActivityIndicator,
  Alert,
  RefreshControl,
} from "react-native";
import { api } from "../../services/api";
import { Colors } from "../../constants/theme";
import { useFocusEffect } from "expo-router";

interface Edital {
  id: string;
  numero_controle: string;
  objeto: string;
  orgao: string;
  valor_estimado: number | null;
  data_encerramento: string | null;
  modalidade: string;
  uf: string;
}

interface Pagina {
  items: Edital[];
  total: number;
  pagina: number;
  paginas: number;
}

const MEI_LIMITE = 80000;

function formatarMoeda(valor: number | null): string {
  if (valor === null) return "Valor não informado";
  return valor.toLocaleString("pt-BR", { style: "currency", currency: "BRL" });
}

function formatarData(data: string | null): string {
  if (!data) return "—";
  return new Date(data).toLocaleDateString("pt-BR");
}

export default function EditaisScreen() {
  const [busca, setBusca] = useState("");
  const [valorMax, setValorMax] = useState("");
  const [editais, setEditais] = useState<Edital[]>([]);
  const [carregando, setCarregando] = useState(false);
  const [pagina, setPagina] = useState(1);
  const [totalPaginas, setTotalPaginas] = useState(1);

  async function buscarEditais(pag = 1, reset = false) {
    setCarregando(true);
    try {
      const params: Record<string, any> = { pagina: pag, por_pagina: 10 };
      if (busca.trim()) params.busca = busca.trim();
      if (valorMax.trim()) params.valor_max = Number(valorMax.replace(/\D/g, ""));

      const { data }: { data: Pagina } = await api.get("/editais", { params });
      setEditais(reset ? data.items : [...editais, ...data.items]);
      setPagina(data.pagina);
      setTotalPaginas(data.paginas);
    } catch {
      Alert.alert("Erro", "Não foi possível carregar os editais.");
    } finally {
      setCarregando(false);
    }
  }

  useFocusEffect(
    useCallback(() => {
      buscarEditais(1, true);
    }, [])
  );

  function handleBuscar() {
    buscarEditais(1, true);
  }

  function handleProximaPagina() {
    if (pagina < totalPaginas && !carregando) {
      buscarEditais(pagina + 1, false);
    }
  }

  function renderEdital({ item }: { item: Edital }) {
    const favoravel = item.valor_estimado !== null && item.valor_estimado <= MEI_LIMITE;
    return (
      <View style={[styles.card, favoravel && styles.cardFavoravel]}>
        {favoravel && (
          <View style={styles.badge}>
            <Text style={styles.badgeTexto}>✓ Favorável para MEI</Text>
          </View>
        )}
        <Text style={styles.objeto} numberOfLines={2}>{item.objeto}</Text>
        <Text style={styles.orgao}>{item.orgao} · {item.uf}</Text>
        <View style={styles.rodape}>
          <Text style={styles.valor}>{formatarMoeda(item.valor_estimado)}</Text>
          <Text style={styles.data}>Enc.: {formatarData(item.data_encerramento)}</Text>
        </View>
        <Text style={styles.modalidade}>{item.modalidade}</Text>
      </View>
    );
  }

  return (
    <View style={styles.container}>
      <View style={styles.filtros}>
        <TextInput
          style={styles.inputBusca}
          placeholder="Buscar por objeto ou CNAE..."
          value={busca}
          onChangeText={setBusca}
          onSubmitEditing={handleBuscar}
          placeholderTextColor={Colors.textSecondary}
          returnKeyType="search"
        />
        <TextInput
          style={styles.inputValor}
          placeholder="Valor máx (R$)"
          value={valorMax}
          onChangeText={setValorMax}
          keyboardType="numeric"
          placeholderTextColor={Colors.textSecondary}
        />
        <TouchableOpacity style={styles.botaoBuscar} onPress={handleBuscar}>
          <Text style={styles.botaoBuscarTexto}>Buscar</Text>
        </TouchableOpacity>
      </View>

      <FlatList
        data={editais}
        keyExtractor={(item) => item.id}
        renderItem={renderEdital}
        onEndReached={handleProximaPagina}
        onEndReachedThreshold={0.3}
        refreshControl={
          <RefreshControl refreshing={carregando && pagina === 1} onRefresh={() => buscarEditais(1, true)} />
        }
        ListFooterComponent={
          carregando && pagina > 1 ? <ActivityIndicator style={{ margin: 16 }} color={Colors.primary} /> : null
        }
        ListEmptyComponent={
          !carregando ? (
            <Text style={styles.vazio}>Nenhum edital encontrado.</Text>
          ) : null
        }
        contentContainerStyle={styles.lista}
      />
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: Colors.background },
  filtros: { padding: 12, backgroundColor: Colors.card, borderBottomWidth: 1, borderBottomColor: Colors.border },
  inputBusca: {
    borderWidth: 1, borderColor: Colors.border, borderRadius: 8,
    padding: 10, fontSize: 14, color: Colors.text, marginBottom: 8,
  },
  inputValor: {
    borderWidth: 1, borderColor: Colors.border, borderRadius: 8,
    padding: 10, fontSize: 14, color: Colors.text, marginBottom: 8,
  },
  botaoBuscar: {
    backgroundColor: Colors.primary, borderRadius: 8,
    padding: 12, alignItems: "center",
  },
  botaoBuscarTexto: { color: "#fff", fontWeight: "700", fontSize: 14 },
  lista: { padding: 12, paddingBottom: 32 },
  card: {
    backgroundColor: Colors.card, borderRadius: 10, padding: 14,
    marginBottom: 12, borderWidth: 1, borderColor: Colors.border,
    shadowColor: "#000", shadowOpacity: 0.05, shadowRadius: 4, elevation: 2,
  },
  cardFavoravel: { borderColor: Colors.secondary, borderWidth: 1.5 },
  badge: {
    backgroundColor: "#E6F4EA", borderRadius: 4, paddingHorizontal: 8,
    paddingVertical: 2, alignSelf: "flex-start", marginBottom: 6,
  },
  badgeTexto: { color: Colors.secondary, fontSize: 11, fontWeight: "700" },
  objeto: { fontSize: 14, fontWeight: "600", color: Colors.text, marginBottom: 4 },
  orgao: { fontSize: 12, color: Colors.textSecondary, marginBottom: 8 },
  rodape: { flexDirection: "row", justifyContent: "space-between", marginBottom: 4 },
  valor: { fontSize: 13, fontWeight: "700", color: Colors.primary },
  data: { fontSize: 12, color: Colors.textSecondary },
  modalidade: { fontSize: 11, color: Colors.textSecondary },
  vazio: { textAlign: "center", color: Colors.textSecondary, marginTop: 48, fontSize: 15 },
});
