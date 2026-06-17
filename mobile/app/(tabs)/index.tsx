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
import { Ionicons } from "@expo/vector-icons";
import { api } from "../../services/api";
import { Colors, Radius, Spacing, Shadow } from "../../constants/theme";
import { useFocusEffect, useRouter } from "expo-router";

interface Edital {
  id: string;
  numero_controle: string;
  objeto: string;
  orgao: string;
  valor_estimado: number | null;
  data_encerramento: string | null;
  modalidade: string;
  uf: string;
  favoravel_mei: boolean;
}

interface Pagina {
  items: Edital[];
  total: number;
  pagina: number;
  paginas: number;
}

const MEI_LIMITE = 80000;

function formatarMoeda(valor: number | null): string {
  if (valor === null) return "Não informado";
  return valor.toLocaleString("pt-BR", { style: "currency", currency: "BRL" });
}

function formatarData(data: string | null): string {
  if (!data) return "—";
  return new Date(data).toLocaleDateString("pt-BR");
}

export default function EditaisScreen() {
  const router = useRouter();
  const [busca, setBusca] = useState("");
  const [editais, setEditais] = useState<Edital[]>([]);
  const [carregando, setCarregando] = useState(false);
  const [pagina, setPagina] = useState(1);
  const [totalPaginas, setTotalPaginas] = useState(1);
  const [total, setTotal] = useState(0);
  const [refreshing, setRefreshing] = useState(false);

const onRefresh = useCallback(async () => {
    setRefreshing(true);
    await buscarEditais(1, true);
    setRefreshing(false);
  }, []);

  async function buscarEditais(pag = 1, reset = false) {
    setCarregando(true);
    try {
      const params: Record<string, any> = { pagina: pag, por_pagina: 15 };
      if (busca.trim()) params.busca = busca.trim();

      const { data }: { data: Pagina } = await api.get("/editais", { params });
      setEditais(reset ? data.items : [...editais, ...data.items]);
      setPagina(data.pagina);
      setTotalPaginas(data.paginas);
      setTotal(data.total);
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
    const favoravel =
      item.favoravel_mei ||
      (item.valor_estimado !== null && item.valor_estimado <= MEI_LIMITE);

    return (
      <TouchableOpacity
        style={[styles.card, favoravel && styles.cardFavoravel]}
        onPress={() => router.push(`/edital/${item.id}`)}
        activeOpacity={0.75}
      >
        {favoravel && (
          <View style={styles.badge}>
            <Ionicons name="checkmark-circle" size={12} color={Colors.success} />
            <Text style={styles.badgeTexto}> Favorável para MEI</Text>
          </View>
        )}

        <Text style={styles.objeto} numberOfLines={2}>
          {item.objeto}
        </Text>

        <View style={styles.orgaoRow}>
          <Ionicons name="business-outline" size={12} color={Colors.textLight} />
          <Text style={styles.orgao} numberOfLines={1}>
            {" "}{item.orgao}
            {item.uf ? ` · ${item.uf}` : ""}
          </Text>
        </View>

        <View style={styles.cardFooter}>
          <View style={styles.valorContainer}>
            <Text style={styles.valorLabel}>Valor estimado</Text>
            <Text style={[styles.valor, favoravel && styles.valorFavoravel]}>
              {formatarMoeda(item.valor_estimado)}
            </Text>
          </View>
          <View style={styles.dataContainer}>
            <Text style={styles.dataLabel}>Encerra</Text>
            <Text style={styles.data}>{formatarData(item.data_encerramento)}</Text>
          </View>
        </View>

        {item.modalidade ? (
          <View style={styles.modalidadeBadge}>
            <Text style={styles.modalidadeTexto}>{item.modalidade}</Text>
          </View>
        ) : null}

        <View style={styles.checklistHint}>
          <Ionicons name="eye-outline" size={12} color={Colors.primary} />
          <Text style={styles.checklistHintTexto}>Ver detalhes do edital</Text>
          <Ionicons name="chevron-forward" size={12} color={Colors.primary} />
        </View>
      </TouchableOpacity>
    );
  }

  return (
    <View style={styles.container}>
      {/* Search bar */}
      <View style={styles.searchContainer}>
        <View style={styles.searchWrapper}>
          <Ionicons
            name="search-outline"
            size={18}
            color={Colors.textLight}
            style={styles.searchIcon}
          />
          <TextInput
            style={styles.searchInput}
            placeholder="Buscar por objeto ou palavra-chave..."
            value={busca}
            onChangeText={setBusca}
            onSubmitEditing={handleBuscar}
            placeholderTextColor={Colors.textLight}
            returnKeyType="search"
          />
          {busca.length > 0 && (
            <TouchableOpacity
              onPress={() => {
                setBusca("");
                buscarEditais(1, true);
              }}
            >
              <Ionicons name="close-circle" size={18} color={Colors.textLight} />
            </TouchableOpacity>
          )}
        </View>
        <TouchableOpacity style={styles.searchButton} onPress={handleBuscar} activeOpacity={0.8}>
          <Text style={styles.searchButtonText}>Buscar</Text>
        </TouchableOpacity>
      </View>

      {total > 0 && (
        <View style={styles.resultInfo}>
          <Text style={styles.resultText}>
            {total.toLocaleString("pt-BR")} editais encontrados
          </Text>
        </View>
      )}

      <FlatList
        data={editais}
        keyExtractor={(item) => item.id}
        renderItem={renderEdital}
        onEndReached={handleProximaPagina}
        onEndReachedThreshold={0.4}
        refreshControl={
          <RefreshControl 
            refreshing={refreshing} 
            onRefresh={onRefresh}
            colors={[Colors.primary]}
            tintColor={Colors.primary}
          />
        }
        ListFooterComponent={
          carregando && pagina > 1 ? (
            <ActivityIndicator style={{ margin: 20 }} color={Colors.primary} />
          ) : null
        }
        ListEmptyComponent={
          !carregando ? (
            <View style={styles.vazioContainer}>
              <Ionicons name="document-text-outline" size={48} color={Colors.border} />
              <Text style={styles.vazioTexto}>Nenhum edital encontrado.</Text>
              <Text style={styles.vazioSub}>Tente ajustar os filtros de busca.</Text>
            </View>
          ) : null
        }
        contentContainerStyle={styles.lista}
      />
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: Colors.background,
  },
  searchContainer: {
    flexDirection: "row",
    gap: Spacing.sm,
    padding: Spacing.md,
    backgroundColor: Colors.white,
    borderBottomWidth: 1,
    borderBottomColor: Colors.border,
  },
  searchWrapper: {
    flex: 1,
    flexDirection: "row",
    alignItems: "center",
    backgroundColor: Colors.surface,
    borderWidth: 1.5,
    borderColor: Colors.border,
    borderRadius: Radius.md,
    paddingHorizontal: Spacing.sm + 4,
    height: 44,
  },
  searchIcon: {
    marginRight: 6,
  },
  searchInput: {
    flex: 1,
    fontSize: 14,
    color: Colors.text,
  },
  searchButton: {
    backgroundColor: Colors.primary,
    borderRadius: Radius.md,
    paddingHorizontal: Spacing.md,
    justifyContent: "center",
    alignItems: "center",
    height: 44,
  },
  searchButtonText: {
    color: Colors.white,
    fontWeight: "700",
    fontSize: 14,
  },
  resultInfo: {
    paddingHorizontal: Spacing.md,
    paddingVertical: Spacing.sm,
    backgroundColor: Colors.white,
    borderBottomWidth: 1,
    borderBottomColor: Colors.borderLight,
  },
  resultText: {
    fontSize: 12,
    color: Colors.textSecondary,
    fontWeight: "500",
  },
  lista: {
    padding: Spacing.md,
    paddingBottom: 40,
  },
  card: {
    backgroundColor: Colors.white,
    borderRadius: Radius.lg,
    padding: Spacing.md,
    marginBottom: Spacing.md,
    borderWidth: 1,
    borderColor: Colors.border,
    ...Shadow.sm,
  },
  cardFavoravel: {
    borderColor: Colors.success,
    borderWidth: 1.5,
  },
  badge: {
    flexDirection: "row",
    alignItems: "center",
    backgroundColor: Colors.successLight,
    borderRadius: Radius.sm,
    paddingHorizontal: Spacing.sm,
    paddingVertical: 3,
    alignSelf: "flex-start",
    marginBottom: Spacing.sm,
  },
  badgeTexto: {
    color: Colors.success,
    fontSize: 11,
    fontWeight: "700",
  },
  objeto: {
    fontSize: 14,
    fontWeight: "600",
    color: Colors.text,
    lineHeight: 20,
    marginBottom: Spacing.xs,
  },
  orgaoRow: {
    flexDirection: "row",
    alignItems: "center",
    marginBottom: Spacing.md,
  },
  orgao: {
    fontSize: 12,
    color: Colors.textSecondary,
    flex: 1,
  },
  cardFooter: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "flex-end",
    paddingTop: Spacing.sm,
    borderTopWidth: 1,
    borderTopColor: Colors.borderLight,
  },
  valorContainer: {},
  valorLabel: {
    fontSize: 10,
    color: Colors.textLight,
    fontWeight: "500",
    textTransform: "uppercase",
    letterSpacing: 0.5,
    marginBottom: 2,
  },
  valor: {
    fontSize: 15,
    fontWeight: "700",
    color: Colors.text,
  },
  valorFavoravel: {
    color: Colors.success,
  },
  dataContainer: {
    alignItems: "flex-end",
  },
  dataLabel: {
    fontSize: 10,
    color: Colors.textLight,
    fontWeight: "500",
    textTransform: "uppercase",
    letterSpacing: 0.5,
    marginBottom: 2,
  },
  data: {
    fontSize: 13,
    color: Colors.textSecondary,
    fontWeight: "500",
  },
  modalidadeBadge: {
    marginTop: Spacing.sm,
    backgroundColor: Colors.primaryLight,
    borderRadius: Radius.sm,
    paddingHorizontal: Spacing.sm,
    paddingVertical: 2,
    alignSelf: "flex-start",
  },
  modalidadeTexto: {
    fontSize: 10,
    color: Colors.primaryMid,
    fontWeight: "600",
  },
  checklistHint: {
    flexDirection: "row",
    alignItems: "center",
    gap: 4,
    marginTop: Spacing.sm,
    paddingTop: Spacing.xs,
    borderTopWidth: 1,
    borderTopColor: Colors.primaryLight,
  },
  checklistHintTexto: {
    flex: 1,
    fontSize: 11,
    color: Colors.primary,
    fontWeight: "500",
  },
  vazioContainer: {
    alignItems: "center",
    paddingTop: 60,
    paddingHorizontal: Spacing.xl,
  },
  vazioTexto: {
    marginTop: Spacing.md,
    fontSize: 16,
    fontWeight: "600",
    color: Colors.textSecondary,
  },
  vazioSub: {
    marginTop: Spacing.xs,
    fontSize: 13,
    color: Colors.textLight,
    textAlign: "center",
  },
});
