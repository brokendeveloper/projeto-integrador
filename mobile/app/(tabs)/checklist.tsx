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
import { useFocusEffect } from "expo-router";
import { api } from "../../services/api";
import { Colors } from "../../constants/theme";

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

const PLANO_ATUAL = "free";

export default function ChecklistScreen() {
  const [editalId, setEditalId] = useState("");
  const [checklist, setChecklist] = useState<ChecklistData | null>(null);
  const [carregando, setCarregando] = useState(false);

  async function carregarChecklist() {
    if (!editalId.trim()) {
      Alert.alert("Atenção", "Informe o ID do edital.");
      return;
    }
    setCarregando(true);
    try {
      const { data } = await api.get(`/editais/${editalId.trim()}/checklist`);
      setChecklist(data);
    } catch {
      Alert.alert("Erro", "Edital não encontrado ou sem checklist.");
    } finally {
      setCarregando(false);
    }
  }

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

  function renderItem({ item }: { item: Item }) {
    const bloqueado = item.plano_necessario !== "free" && PLANO_ATUAL === "free";

    return (
      <TouchableOpacity
        style={[styles.item, bloqueado && styles.itemBloqueado]}
        onPress={() => !bloqueado && toggleItem(item.id, item.concluido)}
        disabled={bloqueado}
      >
        <View style={styles.itemEsquerda}>
          <Text style={styles.checkbox}>{bloqueado ? "🔒" : item.concluido ? "✅" : "⬜"}</Text>
          <View style={{ flex: 1 }}>
            <Text style={[styles.itemTexto, item.concluido && styles.itemConcluido]}>
              {item.descricao}
            </Text>
            <Text style={styles.categoria}>{item.categoria}</Text>
          </View>
        </View>
        {item.obrigatorio && <Text style={styles.obrigatorio}>Obrigatório</Text>}
        {bloqueado && <Text style={styles.premium}>Premium</Text>}
      </TouchableOpacity>
    );
  }

  return (
    <View style={styles.container}>
      <View style={styles.busca}>
        <TextInput
          style={styles.input}
          placeholder="ID do edital"
          value={editalId}
          onChangeText={setEditalId}
          autoCapitalize="none"
          placeholderTextColor={Colors.textSecondary}
        />
        <TouchableOpacity style={styles.botao} onPress={carregarChecklist}>
          <Text style={styles.botaoTexto}>Carregar</Text>
        </TouchableOpacity>
      </View>

      {carregando && <ActivityIndicator style={{ margin: 24 }} color={Colors.primary} />}

      {checklist && !carregando && (
        <>
          <View style={styles.progressoContainer}>
            <Text style={styles.progressoTexto}>Progresso: {progresso}%</Text>
            <View style={styles.barraFundo}>
              <View style={[styles.barra, { width: `${progresso}%` as any }]} />
            </View>
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
        <Text style={styles.instrucao}>Informe o ID do edital para ver o checklist de habilitação.</Text>
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: Colors.background },
  busca: {
    flexDirection: "row", padding: 12, gap: 8,
    backgroundColor: Colors.card, borderBottomWidth: 1, borderBottomColor: Colors.border,
  },
  input: {
    flex: 1, borderWidth: 1, borderColor: Colors.border, borderRadius: 8,
    padding: 10, fontSize: 14, color: Colors.text,
  },
  botao: { backgroundColor: Colors.primary, borderRadius: 8, padding: 10, justifyContent: "center" },
  botaoTexto: { color: "#fff", fontWeight: "700", fontSize: 13 },
  progressoContainer: { padding: 16, backgroundColor: Colors.card, marginBottom: 8 },
  progressoTexto: { fontSize: 14, fontWeight: "600", color: Colors.text, marginBottom: 6 },
  barraFundo: { height: 8, backgroundColor: Colors.border, borderRadius: 4, overflow: "hidden" },
  barra: { height: 8, backgroundColor: Colors.secondary, borderRadius: 4 },
  lista: { padding: 12, paddingBottom: 32 },
  item: {
    flexDirection: "row", alignItems: "center", justifyContent: "space-between",
    backgroundColor: Colors.card, borderRadius: 8, padding: 12, marginBottom: 8,
    borderWidth: 1, borderColor: Colors.border,
  },
  itemBloqueado: { opacity: 0.6, backgroundColor: "#F5F5F5" },
  itemEsquerda: { flexDirection: "row", alignItems: "flex-start", flex: 1, gap: 8 },
  checkbox: { fontSize: 18, marginTop: 1 },
  itemTexto: { fontSize: 13, color: Colors.text, flexWrap: "wrap" },
  itemConcluido: { textDecorationLine: "line-through", color: Colors.textSecondary },
  categoria: { fontSize: 11, color: Colors.textSecondary, marginTop: 2 },
  obrigatorio: { fontSize: 10, color: Colors.danger, fontWeight: "700" },
  premium: { fontSize: 10, color: Colors.premium, fontWeight: "700" },
  instrucao: { textAlign: "center", color: Colors.textSecondary, marginTop: 48, fontSize: 15, padding: 24 },
});
