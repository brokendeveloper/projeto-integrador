import { useState, useCallback } from "react";
import {
  View,
  Text,
  TouchableOpacity,
  FlatList,
  StyleSheet,
  Alert,
  ActivityIndicator,
  TextInput,
  Modal,
  ScrollView,
} from "react-native";
import { useFocusEffect } from "expo-router";
import { api } from "../../services/api";
import { Colors } from "../../constants/theme";

interface Resumo {
  total: number;
  vencidas: number;
  em_andamento: number;
  perdidas: number;
}

interface Participacao {
  id: string;
  edital_id: string;
  status: string;
  valor_proposta: number | null;
  data_participacao: string;
}

const STATUS_CORES: Record<string, string> = {
  em_andamento: Colors.primary,
  vencida: Colors.secondary,
  perdida: Colors.danger,
  desistida: Colors.textSecondary,
};

const STATUS_LABELS: Record<string, string> = {
  em_andamento: "Em andamento",
  vencida: "Vencida",
  perdida: "Perdida",
  desistida: "Desistida",
};

function formatarMoeda(valor: number | null): string {
  if (!valor) return "—";
  return valor.toLocaleString("pt-BR", { style: "currency", currency: "BRL" });
}

export default function HistoricoScreen() {
  const [resumo, setResumo] = useState<Resumo | null>(null);
  const [participacoes, setParticipacoes] = useState<Participacao[]>([]);
  const [carregando, setCarregando] = useState(false);
  const [modalVisivel, setModalVisivel] = useState(false);
  const [novoEditalId, setNovoEditalId] = useState("");
  const [novoStatus, setNovoStatus] = useState("em_andamento");
  const [novoValor, setNovoValor] = useState("");
  const [salvando, setSalvando] = useState(false);

  async function carregar() {
    setCarregando(true);
    try {
      const [{ data: res }, { data: hist }] = await Promise.all([
        api.get("/historico/resumo"),
        api.get("/historico"),
      ]);
      setResumo(res);
      setParticipacoes(hist.items ?? hist);
    } catch {
      Alert.alert("Erro", "Não foi possível carregar o histórico.");
    } finally {
      setCarregando(false);
    }
  }

  useFocusEffect(
    useCallback(() => {
      carregar();
    }, [])
  );

  async function handleSalvar() {
    if (!novoEditalId.trim()) {
      Alert.alert("Atenção", "Informe o ID do edital.");
      return;
    }
    setSalvando(true);
    try {
      const payload: Record<string, any> = {
        edital_id: novoEditalId.trim(),
        status: novoStatus,
      };
      if (novoValor.trim()) {
        payload.valor_proposta = Number(novoValor.replace(/\D/g, ""));
      }
      await api.post("/historico", payload);
      setModalVisivel(false);
      setNovoEditalId("");
      setNovoValor("");
      setNovoStatus("em_andamento");
      await carregar();
    } catch {
      Alert.alert("Erro", "Não foi possível registrar a participação.");
    } finally {
      setSalvando(false);
    }
  }

  function renderParticipacao({ item }: { item: Participacao }) {
    const cor = STATUS_CORES[item.status] ?? Colors.textSecondary;
    return (
      <View style={styles.card}>
        <View style={[styles.indicador, { backgroundColor: cor }]} />
        <View style={{ flex: 1 }}>
          <Text style={styles.editalId} numberOfLines={1}>Edital: {item.edital_id}</Text>
          <Text style={[styles.status, { color: cor }]}>{STATUS_LABELS[item.status] ?? item.status}</Text>
          <Text style={styles.meta}>
            {formatarMoeda(item.valor_proposta)} · {new Date(item.data_participacao).toLocaleDateString("pt-BR")}
          </Text>
        </View>
      </View>
    );
  }

  return (
    <View style={styles.container}>
      {resumo && (
        <View style={styles.metricas}>
          <MetricaCard label="Total" valor={resumo.total} cor={Colors.primary} />
          <MetricaCard label="Vencidas" valor={resumo.vencidas} cor={Colors.secondary} />
          <MetricaCard label="Andamento" valor={resumo.em_andamento} cor={Colors.warning} />
          <MetricaCard label="Perdidas" valor={resumo.perdidas} cor={Colors.danger} />
        </View>
      )}

      <TouchableOpacity style={styles.botaoNovo} onPress={() => setModalVisivel(true)}>
        <Text style={styles.botaoNovoTexto}>+ Registrar participação</Text>
      </TouchableOpacity>

      {carregando ? (
        <ActivityIndicator style={{ margin: 24 }} color={Colors.primary} />
      ) : (
        <FlatList
          data={participacoes}
          keyExtractor={(item) => item.id}
          renderItem={renderParticipacao}
          contentContainerStyle={styles.lista}
          ListEmptyComponent={
            <Text style={styles.vazio}>Nenhuma participação registrada ainda.</Text>
          }
        />
      )}

      <Modal visible={modalVisivel} animationType="slide" presentationStyle="pageSheet">
        <View style={styles.modal}>
          <Text style={styles.modalTitulo}>Nova participação</Text>

          <TextInput
            style={styles.input}
            placeholder="ID do edital"
            value={novoEditalId}
            onChangeText={setNovoEditalId}
            autoCapitalize="none"
            placeholderTextColor={Colors.textSecondary}
          />

          <Text style={styles.label}>Status</Text>
          <View style={styles.statusOpcoes}>
            {Object.entries(STATUS_LABELS).map(([key, label]) => (
              <TouchableOpacity
                key={key}
                style={[styles.statusOpcao, novoStatus === key && { borderColor: STATUS_CORES[key], backgroundColor: STATUS_CORES[key] + "22" }]}
                onPress={() => setNovoStatus(key)}
              >
                <Text style={[styles.statusOpcaoTexto, novoStatus === key && { color: STATUS_CORES[key] }]}>
                  {label}
                </Text>
              </TouchableOpacity>
            ))}
          </View>

          <TextInput
            style={styles.input}
            placeholder="Valor da proposta (R$) — opcional"
            value={novoValor}
            onChangeText={setNovoValor}
            keyboardType="numeric"
            placeholderTextColor={Colors.textSecondary}
          />

          <View style={styles.modalBotoes}>
            <TouchableOpacity style={styles.botaoCancelar} onPress={() => setModalVisivel(false)}>
              <Text style={styles.botaoCancelarTexto}>Cancelar</Text>
            </TouchableOpacity>
            <TouchableOpacity
              style={[styles.botaoSalvar, salvando && styles.botaoDesabilitado]}
              onPress={handleSalvar}
              disabled={salvando}
            >
              {salvando ? <ActivityIndicator color="#fff" /> : <Text style={styles.botaoSalvarTexto}>Salvar</Text>}
            </TouchableOpacity>
          </View>
        </View>
      </Modal>
    </View>
  );
}

function MetricaCard({ label, valor, cor }: { label: string; valor: number; cor: string }) {
  return (
    <View style={[styles.metrica, { borderTopColor: cor }]}>
      <Text style={[styles.metricaValor, { color: cor }]}>{valor}</Text>
      <Text style={styles.metricaLabel}>{label}</Text>
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: Colors.background },
  metricas: {
    flexDirection: "row", padding: 12, gap: 8,
    backgroundColor: Colors.card, borderBottomWidth: 1, borderBottomColor: Colors.border,
  },
  metrica: {
    flex: 1, alignItems: "center", backgroundColor: Colors.background,
    borderRadius: 8, padding: 10, borderTopWidth: 3,
  },
  metricaValor: { fontSize: 22, fontWeight: "800" },
  metricaLabel: { fontSize: 11, color: Colors.textSecondary, marginTop: 2 },
  botaoNovo: {
    margin: 12, backgroundColor: Colors.primary, borderRadius: 8,
    padding: 13, alignItems: "center",
  },
  botaoNovoTexto: { color: "#fff", fontWeight: "700", fontSize: 15 },
  lista: { padding: 12, paddingBottom: 32 },
  card: {
    flexDirection: "row", alignItems: "center", backgroundColor: Colors.card,
    borderRadius: 8, padding: 12, marginBottom: 8,
    borderWidth: 1, borderColor: Colors.border, gap: 10,
  },
  indicador: { width: 4, borderRadius: 2, alignSelf: "stretch" },
  editalId: { fontSize: 13, fontWeight: "600", color: Colors.text },
  status: { fontSize: 12, fontWeight: "600", marginTop: 2 },
  meta: { fontSize: 11, color: Colors.textSecondary, marginTop: 2 },
  vazio: { textAlign: "center", color: Colors.textSecondary, marginTop: 48, fontSize: 15, padding: 24 },
  modal: { flex: 1, padding: 24, backgroundColor: Colors.background },
  modalTitulo: { fontSize: 20, fontWeight: "700", color: Colors.text, marginBottom: 20 },
  input: {
    borderWidth: 1, borderColor: Colors.border, borderRadius: 8,
    padding: 12, fontSize: 14, color: Colors.text, marginBottom: 14,
  },
  label: { fontSize: 13, fontWeight: "600", color: Colors.text, marginBottom: 8 },
  statusOpcoes: { flexDirection: "row", flexWrap: "wrap", gap: 8, marginBottom: 14 },
  statusOpcao: {
    borderWidth: 1, borderColor: Colors.border, borderRadius: 6,
    paddingHorizontal: 12, paddingVertical: 6,
  },
  statusOpcaoTexto: { fontSize: 12, color: Colors.textSecondary },
  modalBotoes: { flexDirection: "row", gap: 12, marginTop: 8 },
  botaoCancelar: {
    flex: 1, borderWidth: 1, borderColor: Colors.border, borderRadius: 8,
    padding: 14, alignItems: "center",
  },
  botaoCancelarTexto: { color: Colors.textSecondary, fontWeight: "600" },
  botaoSalvar: { flex: 1, backgroundColor: Colors.primary, borderRadius: 8, padding: 14, alignItems: "center" },
  botaoDesabilitado: { opacity: 0.6 },
  botaoSalvarTexto: { color: "#fff", fontWeight: "700" },
});
