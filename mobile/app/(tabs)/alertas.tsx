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
import { useFocusEffect } from "expo-router";
import { api } from "../../services/api";
import { Colors, Radius, Spacing, Shadow } from "../../constants/theme";

interface Alerta {
  id: string;
  nome?: string;
  cnae: string | null;
  valor_max: number | null;
  uf: string | null;
  criado_em: string;
}

const LIMITE_FREE = 3;

export default function AlertasScreen() {
  const [alertas, setAlertas] = useState<Alerta[]>([]);
  const [carregando, setCarregando] = useState(false);
  const [cnae, setCnae] = useState("");
  const [valorMax, setValorMax] = useState("");
  const [uf, setUf] = useState("");
  const [criando, setCriando] = useState(false);

  async function carregarAlertas() {
    setCarregando(true);
    try {
      const { data } = await api.get("/alertas");
      setAlertas(data);
    } catch {
      Alert.alert("Erro", "Não foi possível carregar os alertas.");
    } finally {
      setCarregando(false);
    }
  }

  useFocusEffect(
    useCallback(() => {
      carregarAlertas();
    }, [])
  );

  async function handleCriar() {
    if (alertas.length >= LIMITE_FREE) return;
    if (!cnae.trim() && !valorMax.trim() && !uf.trim()) {
      Alert.alert("Atenção", "Preencha ao menos um filtro.");
      return;
    }
    setCriando(true);
    try {
      const payload: Record<string, any> = {};
      if (cnae.trim()) payload.cnae = cnae.trim();
      if (valorMax.trim()) payload.valor_max = Number(valorMax.replace(/\D/g, ""));
      if (uf.trim()) payload.uf = uf.trim().toUpperCase().slice(0, 2);

      await api.post("/alertas", payload);
      setCnae("");
      setValorMax("");
      setUf("");
      await carregarAlertas();
    } catch {
      Alert.alert("Erro", "Não foi possível criar o alerta.");
    } finally {
      setCriando(false);
    }
  }

  async function handleExcluir(id: string) {
    Alert.alert("Excluir alerta", "Tem certeza?", [
      { text: "Cancelar", style: "cancel" },
      {
        text: "Excluir",
        style: "destructive",
        onPress: async () => {
          try {
            await api.delete(`/alertas/${id}`);
            setAlertas((prev) => prev.filter((a) => a.id !== id));
          } catch {
            Alert.alert("Erro", "Não foi possível excluir.");
          }
        },
      },
    ]);
  }

  const limiteAtingido = alertas.length >= LIMITE_FREE;

  function renderAlerta({ item }: { item: Alerta }) {
    const partes: string[] = [];
    if (item.cnae) partes.push(`CNAE ${item.cnae}`);
    if (item.valor_max)
      partes.push(`Até ${item.valor_max.toLocaleString("pt-BR", { style: "currency", currency: "BRL" })}`);
    if (item.uf) partes.push(`UF: ${item.uf}`);

    return (
      <View style={styles.alertaCard}>
        <View style={styles.alertaIcone}>
          <Ionicons name="notifications" size={18} color={Colors.primary} />
        </View>
        <View style={styles.alertaInfo}>
          <Text style={styles.alertaTitulo}>
            {item.nome || partes.join(" · ") || "Todos os editais"}
          </Text>
          <Text style={styles.alertaFiltros}>
            {partes.length > 0 ? partes.join(" · ") : "Sem filtros específicos"}
          </Text>
          <Text style={styles.alertaData}>
            Criado em {new Date(item.criado_em).toLocaleDateString("pt-BR")}
          </Text>
        </View>
        <TouchableOpacity
          onPress={() => handleExcluir(item.id)}
          hitSlop={{ top: 8, bottom: 8, left: 8, right: 8 }}
        >
          <Ionicons name="trash-outline" size={18} color={Colors.danger} />
        </TouchableOpacity>
      </View>
    );
  }

  return (
    <View style={styles.container}>
      {/* Uso header */}
      <View style={styles.usoHeader}>
        <View style={styles.usoInfo}>
          <Text style={styles.usoTitulo}>Alertas ativos</Text>
          <Text style={styles.usoContador}>
            <Text style={styles.usoNumero}>{alertas.length}</Text>
            <Text style={styles.usoTotal}>/{LIMITE_FREE} (plano gratuito)</Text>
          </Text>
        </View>
        <View style={styles.usoBarras}>
          {Array.from({ length: LIMITE_FREE }).map((_, i) => (
            <View
              key={i}
              style={[styles.usoBarra, i < alertas.length && styles.usoBarraAtiva]}
            />
          ))}
        </View>
      </View>

      {/* Premium banner */}
      {limiteAtingido && (
        <View style={styles.premiumBanner}>
          <Ionicons name="lock-closed" size={16} color={Colors.premium} />
          <Text style={styles.premiumTexto}>
            {"  "}Limite atingido. Faça upgrade para alertas ilimitados.
          </Text>
        </View>
      )}

      {/* Form */}
      {!limiteAtingido && (
        <View style={styles.formulario}>
          <Text style={styles.formularioTitulo}>Novo alerta</Text>
          <Text style={styles.formularioSub}>Receba notificações de editais com esses filtros.</Text>

          <Text style={styles.label}>CNAE</Text>
          <TextInput
            style={styles.input}
            placeholder="Ex: 4711302"
            value={cnae}
            onChangeText={setCnae}
            keyboardType="numeric"
            placeholderTextColor={Colors.textLight}
          />

          <Text style={styles.label}>Valor máximo (R$)</Text>
          <TextInput
            style={styles.input}
            placeholder="Ex: 80000"
            value={valorMax}
            onChangeText={setValorMax}
            keyboardType="numeric"
            placeholderTextColor={Colors.textLight}
          />

          <Text style={styles.label}>Estado (UF)</Text>
          <TextInput
            style={styles.input}
            placeholder="Ex: SP"
            value={uf}
            onChangeText={setUf}
            maxLength={2}
            autoCapitalize="characters"
            placeholderTextColor={Colors.textLight}
          />

          <TouchableOpacity
            style={[styles.botao, criando && styles.botaoDesabilitado]}
            onPress={handleCriar}
            disabled={criando}
            activeOpacity={0.85}
          >
            {criando ? (
              <ActivityIndicator color={Colors.white} size="small" />
            ) : (
              <>
                <Ionicons name="add-circle-outline" size={16} color={Colors.white} />
                <Text style={styles.botaoTexto}>  Criar alerta</Text>
              </>
            )}
          </TouchableOpacity>
        </View>
      )}

      {carregando ? (
        <ActivityIndicator style={{ margin: 32 }} color={Colors.primary} size="large" />
      ) : (
        <FlatList
          data={alertas}
          keyExtractor={(item) => item.id}
          renderItem={renderAlerta}
          contentContainerStyle={styles.lista}
          ListEmptyComponent={
            <View style={styles.vazioContainer}>
              <Ionicons name="notifications-off-outline" size={52} color={Colors.border} />
              <Text style={styles.vazioTexto}>Nenhum alerta configurado.</Text>
              <Text style={styles.vazioSub}>
                Crie alertas para ser notificado de novos editais relevantes.
              </Text>
            </View>
          }
        />
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: Colors.background,
  },
  usoHeader: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "space-between",
    backgroundColor: Colors.white,
    paddingHorizontal: Spacing.md,
    paddingVertical: Spacing.md,
    borderBottomWidth: 1,
    borderBottomColor: Colors.border,
  },
  usoInfo: {},
  usoTitulo: {
    fontSize: 13,
    fontWeight: "600",
    color: Colors.text,
    marginBottom: 2,
  },
  usoContador: {},
  usoNumero: {
    fontSize: 18,
    fontWeight: "800",
    color: Colors.primary,
  },
  usoTotal: {
    fontSize: 13,
    color: Colors.textSecondary,
  },
  usoBarras: {
    flexDirection: "row",
    gap: 6,
  },
  usoBarra: {
    width: 28,
    height: 8,
    borderRadius: 4,
    backgroundColor: Colors.border,
  },
  usoBarraAtiva: {
    backgroundColor: Colors.primary,
  },
  premiumBanner: {
    flexDirection: "row",
    alignItems: "center",
    margin: Spacing.md,
    backgroundColor: Colors.premiumLight,
    borderRadius: Radius.md,
    padding: Spacing.md,
    borderWidth: 1,
    borderColor: Colors.premium + "40",
  },
  premiumTexto: {
    flex: 1,
    fontSize: 13,
    color: Colors.premium,
    fontWeight: "500",
    lineHeight: 18,
  },
  formulario: {
    margin: Spacing.md,
    backgroundColor: Colors.white,
    borderRadius: Radius.lg,
    padding: Spacing.md,
    ...Shadow.sm,
  },
  formularioTitulo: {
    fontSize: 15,
    fontWeight: "700",
    color: Colors.text,
    marginBottom: 2,
  },
  formularioSub: {
    fontSize: 12,
    color: Colors.textSecondary,
    marginBottom: Spacing.md,
  },
  label: {
    fontSize: 12,
    fontWeight: "600",
    color: Colors.textSecondary,
    marginBottom: 5,
    letterSpacing: 0.1,
  },
  input: {
    height: 44,
    borderWidth: 1.5,
    borderColor: Colors.border,
    borderRadius: Radius.md,
    paddingHorizontal: Spacing.md,
    fontSize: 14,
    color: Colors.text,
    backgroundColor: Colors.surface,
    marginBottom: Spacing.sm + 2,
  },
  botao: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "center",
    backgroundColor: Colors.primary,
    borderRadius: Radius.md,
    padding: 13,
    marginTop: 4,
  },
  botaoDesabilitado: {
    opacity: 0.65,
  },
  botaoTexto: {
    color: Colors.white,
    fontWeight: "700",
    fontSize: 14,
  },
  lista: {
    padding: Spacing.md,
    paddingBottom: 40,
  },
  alertaCard: {
    flexDirection: "row",
    alignItems: "center",
    backgroundColor: Colors.white,
    borderRadius: Radius.md,
    padding: Spacing.md,
    marginBottom: Spacing.sm,
    borderWidth: 1,
    borderColor: Colors.border,
    ...Shadow.sm,
  },
  alertaIcone: {
    width: 38,
    height: 38,
    borderRadius: Radius.sm,
    backgroundColor: Colors.primaryLight,
    alignItems: "center",
    justifyContent: "center",
    marginRight: Spacing.md,
  },
  alertaInfo: {
    flex: 1,
    marginRight: Spacing.sm,
  },
  alertaTitulo: {
    fontSize: 13,
    fontWeight: "700",
    color: Colors.text,
    marginBottom: 2,
  },
  alertaFiltros: {
    fontSize: 11,
    color: Colors.textSecondary,
    marginBottom: 2,
  },
  alertaData: {
    fontSize: 10,
    color: Colors.textLight,
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
});
