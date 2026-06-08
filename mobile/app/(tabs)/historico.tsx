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
import { Ionicons } from "@expo/vector-icons";
import { useFocusEffect } from "expo-router";
import { api } from "../../services/api";
import { Colors, Radius, Spacing, Shadow } from "../../constants/theme";

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

const STATUS_CONFIG: Record<string, { label: string; cor: string; bg: string; icon: string }> = {
  em_andamento: {
    label: "Em andamento",
    cor: Colors.primary,
    bg: Colors.primaryLight,
    icon: "time-outline",
  },
  vencida: {
    label: "Vencida",
    cor: Colors.success,
    bg: Colors.successLight,
    icon: "trophy-outline",
  },
  perdida: {
    label: "Perdida",
    cor: Colors.danger,
    bg: Colors.dangerLight,
    icon: "close-circle-outline",
  },
  desistida: {
    label: "Desistida",
    cor: Colors.textSecondary,
    bg: Colors.surface,
    icon: "remove-circle-outline",
  },
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
    const config = STATUS_CONFIG[item.status] ?? {
      label: item.status,
      cor: Colors.textSecondary,
      bg: Colors.surface,
      icon: "ellipse-outline",
    };

    return (
      <View style={styles.card}>
        <View style={[styles.statusIcone, { backgroundColor: config.bg }]}>
          <Ionicons name={config.icon as any} size={18} color={config.cor} />
        </View>
        <View style={styles.cardInfo}>
          <Text style={styles.editalId} numberOfLines={1}>
            Edital: {item.edital_id}
          </Text>
          <View style={[styles.statusBadge, { backgroundColor: config.bg }]}>
            <Text style={[styles.statusTexto, { color: config.cor }]}>{config.label}</Text>
          </View>
          <Text style={styles.meta}>
            {formatarMoeda(item.valor_proposta)} ·{" "}
            {new Date(item.data_participacao).toLocaleDateString("pt-BR")}
          </Text>
        </View>
      </View>
    );
  }

  return (
    <View style={styles.container}>
      {/* Metrics */}
      {resumo && (
        <View style={styles.metricas}>
          <MetricaCard
            label="Total"
            valor={resumo.total}
            cor={Colors.primary}
            bg={Colors.primaryLight}
            icon="layers-outline"
          />
          <MetricaCard
            label="Vencidas"
            valor={resumo.vencidas}
            cor={Colors.success}
            bg={Colors.successLight}
            icon="trophy-outline"
          />
          <MetricaCard
            label="Andamento"
            valor={resumo.em_andamento}
            cor={Colors.warning}
            bg={Colors.warningLight}
            icon="time-outline"
          />
          <MetricaCard
            label="Perdidas"
            valor={resumo.perdidas}
            cor={Colors.danger}
            bg={Colors.dangerLight}
            icon="close-circle-outline"
          />
        </View>
      )}

      {/* Add button */}
      <TouchableOpacity
        style={styles.botaoNovo}
        onPress={() => setModalVisivel(true)}
        activeOpacity={0.85}
      >
        <Ionicons name="add-circle-outline" size={18} color={Colors.white} />
        <Text style={styles.botaoNovoTexto}>  Registrar participação</Text>
      </TouchableOpacity>

      {carregando ? (
        <ActivityIndicator style={{ margin: 32 }} color={Colors.primary} size="large" />
      ) : (
        <FlatList
          data={participacoes}
          keyExtractor={(item) => item.id}
          renderItem={renderParticipacao}
          contentContainerStyle={styles.lista}
          ListEmptyComponent={
            <View style={styles.vazioContainer}>
              <Ionicons name="stats-chart-outline" size={52} color={Colors.border} />
              <Text style={styles.vazioTexto}>Nenhuma participação registrada.</Text>
              <Text style={styles.vazioSub}>
                Registre suas participações em licitações para acompanhar o histórico.
              </Text>
            </View>
          }
        />
      )}

      {/* Modal */}
      <Modal visible={modalVisivel} animationType="slide" presentationStyle="pageSheet">
        <View style={styles.modal}>
          <View style={styles.modalHeader}>
            <Text style={styles.modalTitulo}>Nova participação</Text>
            <TouchableOpacity onPress={() => setModalVisivel(false)}>
              <Ionicons name="close" size={24} color={Colors.textSecondary} />
            </TouchableOpacity>
          </View>

          <ScrollView showsVerticalScrollIndicator={false}>
            <Text style={styles.label}>ID do edital</Text>
            <TextInput
              style={styles.input}
              placeholder="Ex: 12345678"
              value={novoEditalId}
              onChangeText={setNovoEditalId}
              autoCapitalize="none"
              placeholderTextColor={Colors.textLight}
            />

            <Text style={styles.label}>Status</Text>
            <View style={styles.statusOpcoes}>
              {Object.entries(STATUS_CONFIG).map(([key, cfg]) => (
                <TouchableOpacity
                  key={key}
                  style={[
                    styles.statusOpcao,
                    novoStatus === key && { borderColor: cfg.cor, backgroundColor: cfg.bg },
                  ]}
                  onPress={() => setNovoStatus(key)}
                  activeOpacity={0.7}
                >
                  <Ionicons
                    name={cfg.icon as any}
                    size={14}
                    color={novoStatus === key ? cfg.cor : Colors.textSecondary}
                  />
                  <Text
                    style={[
                      styles.statusOpcaoTexto,
                      novoStatus === key && { color: cfg.cor, fontWeight: "700" },
                    ]}
                  >
                    {"  "}{cfg.label}
                  </Text>
                </TouchableOpacity>
              ))}
            </View>

            <Text style={styles.label}>Valor da proposta (opcional)</Text>
            <TextInput
              style={styles.input}
              placeholder="R$ 0,00"
              value={novoValor}
              onChangeText={setNovoValor}
              keyboardType="numeric"
              placeholderTextColor={Colors.textLight}
            />

            <View style={styles.modalBotoes}>
              <TouchableOpacity
                style={styles.botaoCancelar}
                onPress={() => setModalVisivel(false)}
              >
                <Text style={styles.botaoCancelarTexto}>Cancelar</Text>
              </TouchableOpacity>
              <TouchableOpacity
                style={[styles.botaoSalvar, salvando && styles.botaoDesabilitado]}
                onPress={handleSalvar}
                disabled={salvando}
                activeOpacity={0.85}
              >
                {salvando ? (
                  <ActivityIndicator color={Colors.white} size="small" />
                ) : (
                  <Text style={styles.botaoSalvarTexto}>Salvar</Text>
                )}
              </TouchableOpacity>
            </View>
          </ScrollView>
        </View>
      </Modal>
    </View>
  );
}

function MetricaCard({
  label,
  valor,
  cor,
  bg,
  icon,
}: {
  label: string;
  valor: number;
  cor: string;
  bg: string;
  icon: string;
}) {
  return (
    <View style={[styles.metrica, { backgroundColor: bg }]}>
      <Ionicons name={icon as any} size={16} color={cor} style={{ marginBottom: 4 }} />
      <Text style={[styles.metricaValor, { color: cor }]}>{valor}</Text>
      <Text style={styles.metricaLabel}>{label}</Text>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: Colors.background,
  },
  metricas: {
    flexDirection: "row",
    gap: Spacing.sm,
    padding: Spacing.md,
    backgroundColor: Colors.white,
    borderBottomWidth: 1,
    borderBottomColor: Colors.border,
  },
  metrica: {
    flex: 1,
    alignItems: "center",
    borderRadius: Radius.md,
    paddingVertical: Spacing.md,
    paddingHorizontal: Spacing.xs,
  },
  metricaValor: {
    fontSize: 22,
    fontWeight: "800",
  },
  metricaLabel: {
    fontSize: 10,
    color: Colors.textSecondary,
    marginTop: 2,
    fontWeight: "600",
    textTransform: "uppercase",
    letterSpacing: 0.3,
  },
  botaoNovo: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "center",
    margin: Spacing.md,
    backgroundColor: Colors.primary,
    borderRadius: Radius.md,
    padding: 13,
    ...Shadow.sm,
  },
  botaoNovoTexto: {
    color: Colors.white,
    fontWeight: "700",
    fontSize: 15,
  },
  lista: {
    padding: Spacing.md,
    paddingBottom: 40,
  },
  card: {
    flexDirection: "row",
    alignItems: "center",
    backgroundColor: Colors.white,
    borderRadius: Radius.md,
    padding: Spacing.md,
    marginBottom: Spacing.sm,
    borderWidth: 1,
    borderColor: Colors.border,
    ...Shadow.sm,
    gap: Spacing.md,
  },
  statusIcone: {
    width: 40,
    height: 40,
    borderRadius: Radius.sm,
    alignItems: "center",
    justifyContent: "center",
  },
  cardInfo: {
    flex: 1,
  },
  editalId: {
    fontSize: 13,
    fontWeight: "600",
    color: Colors.text,
    marginBottom: 4,
  },
  statusBadge: {
    borderRadius: 4,
    paddingHorizontal: 8,
    paddingVertical: 2,
    alignSelf: "flex-start",
    marginBottom: 4,
  },
  statusTexto: {
    fontSize: 11,
    fontWeight: "700",
  },
  meta: {
    fontSize: 11,
    color: Colors.textSecondary,
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
    lineHeight: 20,
  },
  modal: {
    flex: 1,
    padding: Spacing.xl,
    backgroundColor: Colors.background,
  },
  modalHeader: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "center",
    marginBottom: Spacing.xl,
  },
  modalTitulo: {
    fontSize: 20,
    fontWeight: "700",
    color: Colors.text,
  },
  label: {
    fontSize: 13,
    fontWeight: "600",
    color: Colors.textSecondary,
    marginBottom: 6,
    letterSpacing: 0.1,
  },
  input: {
    height: 50,
    borderWidth: 1.5,
    borderColor: Colors.border,
    borderRadius: Radius.md,
    paddingHorizontal: Spacing.md,
    fontSize: 15,
    color: Colors.text,
    backgroundColor: Colors.white,
    marginBottom: Spacing.md,
  },
  statusOpcoes: {
    flexWrap: "wrap",
    flexDirection: "row",
    gap: Spacing.sm,
    marginBottom: Spacing.md,
  },
  statusOpcao: {
    flexDirection: "row",
    alignItems: "center",
    borderWidth: 1.5,
    borderColor: Colors.border,
    borderRadius: Radius.md,
    paddingHorizontal: Spacing.md,
    paddingVertical: Spacing.sm,
    backgroundColor: Colors.white,
  },
  statusOpcaoTexto: {
    fontSize: 13,
    color: Colors.textSecondary,
  },
  modalBotoes: {
    flexDirection: "row",
    gap: Spacing.md,
    marginTop: Spacing.sm,
    marginBottom: Spacing.xxl,
  },
  botaoCancelar: {
    flex: 1,
    borderWidth: 1.5,
    borderColor: Colors.border,
    borderRadius: Radius.md,
    padding: 14,
    alignItems: "center",
    backgroundColor: Colors.white,
  },
  botaoCancelarTexto: {
    color: Colors.textSecondary,
    fontWeight: "600",
    fontSize: 15,
  },
  botaoSalvar: {
    flex: 1,
    backgroundColor: Colors.primary,
    borderRadius: Radius.md,
    padding: 14,
    alignItems: "center",
    ...Shadow.sm,
  },
  botaoDesabilitado: {
    opacity: 0.65,
  },
  botaoSalvarTexto: {
    color: Colors.white,
    fontWeight: "700",
    fontSize: 15,
  },
});
