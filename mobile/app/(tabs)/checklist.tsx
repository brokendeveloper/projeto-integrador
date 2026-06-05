import { useState, useCallback } from "react";
import {
  View,
  Text,
  TextInput,
  TouchableOpacity,
  FlatList,
  StyleSheet,
  Alert,
  ActivityIndicator,
} from "react-native";
import { Ionicons } from "@expo/vector-icons";
import { useFocusEffect, useLocalSearchParams } from "expo-router";
import { api } from "../../services/api";
import { Colors, Radius, Spacing, Shadow } from "../../constants/theme";

interface Item {
  id: string;
  categoria: string;
  descricao: string;
  obrigatorio: boolean;
  plano_necessario: string;
  concluido: boolean;
}

interface ChecklistData {
  edital_id: string;
  progresso: number;
  items: Item[];
}

export default function ChecklistScreen() {
  const { editalId: editalIdParam } = useLocalSearchParams<{ editalId?: string }>();
  const [editalId, setEditalId] = useState("");
  const [checklist, setChecklist] = useState<ChecklistData | null>(null);
  const [carregando, setCarregando] = useState(false);
  const [plano, setPlano] = useState("free");

  async function carregarChecklistById(id: string) {
    if (!id.trim()) {
      Alert.alert("Atenção", "Informe o ID do edital.");
      return;
    }
    setCarregando(true);
    try {
      const { data } = await api.get(`/editais/${id.trim()}/checklist`);
      setChecklist(data);
    } catch {
      Alert.alert("Erro", "Edital não encontrado ou sem checklist.");
    } finally {
      setCarregando(false);
    }
  }

  function carregarChecklist() {
    carregarChecklistById(editalId);
  }

  useFocusEffect(
    useCallback(() => {
      api.get("/plano").then(({ data }) => setPlano(data.plano_atual)).catch(() => {});
      if (editalIdParam) {
        setEditalId(editalIdParam);
        carregarChecklistById(editalIdParam);
      }
    }, [editalIdParam])
  );

  async function toggleItem(itemId: string, concluido: boolean) {
    if (!checklist) return;
    try {
      const { data } = await api.patch(`/editais/${editalId}/checklist`, {
        item_id: itemId,
        concluido: !concluido,
      });
      setChecklist(data);
    } catch {
      Alert.alert("Erro", "Não foi possível atualizar o item.");
    }
  }

  const progresso = checklist?.progresso ?? 0;
  const concluidos = checklist?.items.filter((i) => i.concluido).length ?? 0;
  const total = checklist?.items.length ?? 0;

  function renderItem({ item }: { item: Item }) {
    const bloqueado = item.plano_necessario !== "free" && plano === "free";

    return (
      <TouchableOpacity
        style={[styles.item, item.concluido && styles.itemConcluido, bloqueado && styles.itemBloqueado]}
        onPress={() => !bloqueado && toggleItem(item.id, item.concluido)}
        disabled={bloqueado}
        activeOpacity={0.7}
      >
        <View style={styles.checkArea}>
          {bloqueado ? (
            <View style={[styles.checkBox, styles.checkBoxBloqueado]}>
              <Ionicons name="lock-closed" size={12} color={Colors.premium} />
            </View>
          ) : item.concluido ? (
            <View style={[styles.checkBox, styles.checkBoxAtivo]}>
              <Ionicons name="checkmark" size={14} color={Colors.white} />
            </View>
          ) : (
            <View style={[styles.checkBox, styles.checkBoxVazio]} />
          )}
        </View>

        <View style={styles.itemConteudo}>
          <Text
            style={[
              styles.itemTexto,
              item.concluido && styles.itemTextoRiscado,
              bloqueado && styles.itemTextoBloqueado,
            ]}
            numberOfLines={2}
          >
            {item.descricao}
          </Text>
          <View style={styles.itemMeta}>
            <Text style={styles.categoriaTexto}>{item.categoria}</Text>
            {item.obrigatorio && (
              <View style={styles.obrigatorioTag}>
                <Text style={styles.obrigatorioTexto}>Obrigatório</Text>
              </View>
            )}
            {bloqueado && (
              <View style={styles.premiumTag}>
                <Text style={styles.premiumTexto}>Premium</Text>
              </View>
            )}
          </View>
        </View>
      </TouchableOpacity>
    );
  }

  return (
    <View style={styles.container}>
      {/* Search */}
      <View style={styles.searchArea}>
        <View style={styles.searchWrapper}>
          <Ionicons name="search-outline" size={16} color={Colors.textLight} style={{ marginRight: 6 }} />
          <TextInput
            style={styles.searchInput}
            placeholder="ID do edital"
            value={editalId}
            onChangeText={setEditalId}
            autoCapitalize="none"
            placeholderTextColor={Colors.textLight}
            onSubmitEditing={carregarChecklist}
            returnKeyType="search"
          />
        </View>
        <TouchableOpacity style={styles.botaoCarregar} onPress={carregarChecklist} activeOpacity={0.8}>
          <Text style={styles.botaoTexto}>Ver</Text>
        </TouchableOpacity>
      </View>

      {carregando && (
        <ActivityIndicator style={{ margin: 32 }} color={Colors.primary} size="large" />
      )}

      {checklist && !carregando && (
        <>
          {/* Progress card */}
          <View style={styles.progressoCard}>
            <View style={styles.progressoHeader}>
              <Text style={styles.progressoTitulo}>Progresso da habilitação</Text>
              <Text style={styles.progressoPorcentagem}>{progresso}%</Text>
            </View>
            <View style={styles.barraFundo}>
              <View
                style={[
                  styles.barraPreenchida,
                  { width: `${progresso}%` as any },
                  progresso === 100 && styles.barraCompleta,
                ]}
              />
            </View>
            <Text style={styles.progressoSub}>
              {concluidos} de {total} itens concluídos
            </Text>
          </View>

          <FlatList
            data={checklist.items}
            keyExtractor={(item) => item.id}
            renderItem={renderItem}
            contentContainerStyle={styles.lista}
          />
        </>
      )}

      {!checklist && !carregando && (
        <View style={styles.instrucaoContainer}>
          <Ionicons name="checkbox-outline" size={52} color={Colors.border} />
          <Text style={styles.instrucaoTitulo}>Checklist de habilitação</Text>
          <Text style={styles.instrucaoTexto}>
            Informe o ID do edital para verificar os requisitos de habilitação da Lei 14.133/2021.
          </Text>
        </View>
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: Colors.background,
  },
  searchArea: {
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
  searchInput: {
    flex: 1,
    fontSize: 14,
    color: Colors.text,
  },
  botaoCarregar: {
    backgroundColor: Colors.primary,
    borderRadius: Radius.md,
    paddingHorizontal: Spacing.md,
    justifyContent: "center",
    alignItems: "center",
    height: 44,
  },
  botaoTexto: {
    color: Colors.white,
    fontWeight: "700",
    fontSize: 14,
  },
  progressoCard: {
    margin: Spacing.md,
    backgroundColor: Colors.white,
    borderRadius: Radius.lg,
    padding: Spacing.md,
    ...Shadow.sm,
  },
  progressoHeader: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "center",
    marginBottom: Spacing.sm,
  },
  progressoTitulo: {
    fontSize: 14,
    fontWeight: "600",
    color: Colors.text,
  },
  progressoPorcentagem: {
    fontSize: 18,
    fontWeight: "800",
    color: Colors.primary,
  },
  barraFundo: {
    height: 8,
    backgroundColor: Colors.borderLight,
    borderRadius: 4,
    overflow: "hidden",
    marginBottom: Spacing.sm,
  },
  barraPreenchida: {
    height: 8,
    backgroundColor: Colors.primary,
    borderRadius: 4,
  },
  barraCompleta: {
    backgroundColor: Colors.success,
  },
  progressoSub: {
    fontSize: 12,
    color: Colors.textSecondary,
  },
  lista: {
    padding: Spacing.md,
    paddingBottom: 40,
  },
  item: {
    flexDirection: "row",
    backgroundColor: Colors.white,
    borderRadius: Radius.md,
    padding: Spacing.md,
    marginBottom: Spacing.sm,
    borderWidth: 1,
    borderColor: Colors.border,
    ...Shadow.sm,
  },
  itemConcluido: {
    backgroundColor: Colors.surface,
    borderColor: Colors.success + "40",
  },
  itemBloqueado: {
    opacity: 0.6,
  },
  checkArea: {
    marginRight: Spacing.sm,
    marginTop: 1,
  },
  checkBox: {
    width: 22,
    height: 22,
    borderRadius: 6,
    alignItems: "center",
    justifyContent: "center",
  },
  checkBoxVazio: {
    borderWidth: 2,
    borderColor: Colors.border,
  },
  checkBoxAtivo: {
    backgroundColor: Colors.success,
    borderWidth: 0,
  },
  checkBoxBloqueado: {
    backgroundColor: Colors.premiumLight,
    borderWidth: 0,
  },
  itemConteudo: {
    flex: 1,
  },
  itemTexto: {
    fontSize: 13,
    color: Colors.text,
    lineHeight: 18,
    marginBottom: 4,
  },
  itemTextoRiscado: {
    textDecorationLine: "line-through",
    color: Colors.textSecondary,
  },
  itemTextoBloqueado: {
    color: Colors.textSecondary,
  },
  itemMeta: {
    flexDirection: "row",
    alignItems: "center",
    gap: Spacing.xs,
    flexWrap: "wrap",
  },
  categoriaTexto: {
    fontSize: 11,
    color: Colors.textLight,
    fontWeight: "500",
  },
  obrigatorioTag: {
    backgroundColor: Colors.dangerLight,
    borderRadius: 4,
    paddingHorizontal: 6,
    paddingVertical: 1,
  },
  obrigatorioTexto: {
    fontSize: 10,
    color: Colors.danger,
    fontWeight: "700",
  },
  premiumTag: {
    backgroundColor: Colors.premiumLight,
    borderRadius: 4,
    paddingHorizontal: 6,
    paddingVertical: 1,
  },
  premiumTexto: {
    fontSize: 10,
    color: Colors.premium,
    fontWeight: "700",
  },
  instrucaoContainer: {
    flex: 1,
    alignItems: "center",
    justifyContent: "center",
    paddingHorizontal: Spacing.xxl,
    paddingBottom: 60,
  },
  instrucaoTitulo: {
    marginTop: Spacing.md,
    fontSize: 17,
    fontWeight: "700",
    color: Colors.text,
    textAlign: "center",
  },
  instrucaoTexto: {
    marginTop: Spacing.sm,
    fontSize: 14,
    color: Colors.textSecondary,
    textAlign: "center",
    lineHeight: 20,
  },
});
