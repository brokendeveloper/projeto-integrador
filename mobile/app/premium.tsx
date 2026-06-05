import { useState, useEffect, useRef } from "react";
import {
  View,
  Text,
  TouchableOpacity,
  StyleSheet,
  ScrollView,
  ActivityIndicator,
  Animated,
} from "react-native";
import { Ionicons } from "@expo/vector-icons";
import { api } from "../services/api";
import { Colors, Radius, Spacing, Shadow } from "../constants/theme";

interface PlanoInfo {
  nome: string;
  preco: string;
  recursos: string[];
  limite_alertas: number;
}

interface PlanoData {
  plano_atual: string;
  info: PlanoInfo;
  proximo_plano: PlanoInfo;
}

function Toast({ visivel, mensagem, icone }: { visivel: boolean; mensagem: string; icone: string }) {
  const translateY = useRef(new Animated.Value(-80)).current;
  const opacidade = useRef(new Animated.Value(0)).current;

  useEffect(() => {
    if (visivel) {
      Animated.parallel([
        Animated.spring(translateY, {
          toValue: 0,
          useNativeDriver: true,
          tension: 80,
          friction: 10,
        }),
        Animated.timing(opacidade, {
          toValue: 1,
          duration: 200,
          useNativeDriver: true,
        }),
      ]).start();
    } else {
      Animated.parallel([
        Animated.timing(translateY, {
          toValue: -80,
          duration: 250,
          useNativeDriver: true,
        }),
        Animated.timing(opacidade, {
          toValue: 0,
          duration: 200,
          useNativeDriver: true,
        }),
      ]).start();
    }
  }, [visivel]);

  return (
    <Animated.View
      style={[
        styles.toast,
        { transform: [{ translateY }], opacity: opacidade },
      ]}
      pointerEvents="none"
    >
      <Ionicons name={icone as any} size={20} color={Colors.white} />
      <Text style={styles.toastTexto}>{mensagem}</Text>
    </Animated.View>
  );
}

export default function PremiumScreen() {
  const [carregando, setCarregando] = useState(true);
  const [processando, setProcessando] = useState(false);
  const [dados, setDados] = useState<PlanoData | null>(null);
  const [toastVisivel, setToastVisivel] = useState(false);
  const [toastMsg, setToastMsg] = useState("");
  const [toastIcone, setToastIcone] = useState("checkmark-circle");
  const toastTimer = useRef<ReturnType<typeof setTimeout> | null>(null);

  async function carregar() {
    try {
      const { data } = await api.get("/plano");
      setDados(data);
    } catch {
      mostrarToast("Não foi possível carregar o plano.", "alert-circle-outline");
    } finally {
      setCarregando(false);
    }
  }

  useEffect(() => { carregar(); }, []);

  function mostrarToast(msg: string, icone = "checkmark-circle") {
    if (toastTimer.current) clearTimeout(toastTimer.current);
    setToastMsg(msg);
    setToastIcone(icone);
    setToastVisivel(true);
    toastTimer.current = setTimeout(() => setToastVisivel(false), 3000);
  }

  async function handleUpgrade() {
    if (!dados) return;
    const ativando = dados.plano_atual === "free";

    setProcessando(true);
    try {
      // Simula latência de gateway de pagamento
      await new Promise((r) => setTimeout(r, 1400));

      const { data } = await api.post("/plano/upgrade");
      setDados(data);

      if (ativando) {
        mostrarToast("Plano Premium ativado com sucesso!", "diamond");
      } else {
        mostrarToast("Você voltou ao plano Gratuito.", "checkmark-circle-outline");
      }
    } catch {
      mostrarToast("Não foi possível alterar o plano. Tente novamente.", "alert-circle-outline");
    } finally {
      setProcessando(false);
    }
  }

  if (carregando || !dados) {
    return (
      <View style={styles.loading}>
        <ActivityIndicator size="large" color={Colors.primary} />
      </View>
    );
  }

  const isPremium = dados.plano_atual === "premium";

  return (
    <View style={{ flex: 1 }}>
      <Toast visivel={toastVisivel} mensagem={toastMsg} icone={toastIcone} />

      <ScrollView style={styles.container} contentContainerStyle={styles.content}>
        {/* Status atual */}
        <View style={[styles.statusCard, isPremium && styles.statusCardPremium]}>
          <View style={styles.statusIcone}>
            <Ionicons
              name={isPremium ? "diamond" : "person-circle-outline"}
              size={32}
              color={isPremium ? Colors.premium : Colors.primary}
            />
          </View>
          <View>
            <Text style={styles.statusLabel}>Seu plano atual</Text>
            <Text style={[styles.statusNome, isPremium && { color: Colors.premium }]}>
              {dados.info.nome}
            </Text>
            <Text style={styles.statusPreco}>{dados.info.preco}</Text>
          </View>
        </View>

        {/* Recursos do plano atual */}
        <View style={styles.secao}>
          <Text style={styles.secaoTitulo}>
            Incluído no plano {dados.info.nome}
          </Text>
          {dados.info.recursos.map((recurso, i) => (
            <View key={i} style={styles.recursoItem}>
              <Ionicons name="checkmark-circle" size={18} color={isPremium ? Colors.premium : Colors.success} />
              <Text style={styles.recursoTexto}>{recurso}</Text>
            </View>
          ))}
        </View>

        {/* Próximo plano */}
        <View style={[styles.secao, styles.proximoSecao]}>
          <View style={styles.proximoHeader}>
            <Ionicons name="diamond-outline" size={20} color={isPremium ? Colors.textSecondary : Colors.premium} />
            <Text style={[styles.secaoTitulo, { marginBottom: 0, marginLeft: 6 }]}>
              {isPremium ? "Plano Gratuito" : "Plano Premium"}
            </Text>
          </View>
          <Text style={styles.proximoPreco}>{dados.proximo_plano.preco}</Text>
          {dados.proximo_plano.recursos.map((recurso, i) => (
            <View key={i} style={styles.recursoItem}>
              <Ionicons
                name={isPremium ? "close-circle-outline" : "diamond-outline"}
                size={18}
                color={isPremium ? Colors.textLight : Colors.premium}
              />
              <Text style={[styles.recursoTexto, isPremium && { color: Colors.textSecondary }]}>
                {recurso}
              </Text>
            </View>
          ))}
        </View>

        {/* Botão */}
        <TouchableOpacity
          style={[
            styles.botao,
            isPremium ? styles.botaoDowngrade : styles.botaoUpgrade,
            processando && styles.botaoDesabilitado,
          ]}
          onPress={handleUpgrade}
          disabled={processando}
          activeOpacity={0.85}
        >
          {processando ? (
            <View style={styles.processandoRow}>
              <ActivityIndicator color={Colors.white} size="small" />
              <Text style={[styles.botaoTexto, { marginLeft: 10 }]}>
                {isPremium ? "Cancelando..." : "Processando pagamento..."}
              </Text>
            </View>
          ) : (
            <>
              <Ionicons
                name={isPremium ? "arrow-down-circle-outline" : "diamond-outline"}
                size={18}
                color={Colors.white}
              />
              <Text style={styles.botaoTexto}>
                {"  "}
                {isPremium ? "Voltar ao plano Gratuito" : "Ativar Premium — R$ 29,90/mês"}
              </Text>
            </>
          )}
        </TouchableOpacity>

        {!isPremium && (
          <Text style={styles.aviso}>
            Demonstração. Em produção, integraria com gateway de pagamento.
          </Text>
        )}
      </ScrollView>
    </View>
  );
}

const styles = StyleSheet.create({
  loading: {
    flex: 1,
    alignItems: "center",
    justifyContent: "center",
    backgroundColor: Colors.background,
  },
  container: {
    flex: 1,
    backgroundColor: Colors.background,
  },
  content: {
    padding: Spacing.md,
    paddingBottom: 48,
  },
  toast: {
    position: "absolute",
    top: 56,
    left: Spacing.md,
    right: Spacing.md,
    backgroundColor: Colors.premium,
    borderRadius: Radius.md,
    paddingVertical: 14,
    paddingHorizontal: Spacing.md,
    flexDirection: "row",
    alignItems: "center",
    gap: Spacing.sm,
    zIndex: 100,
    ...Shadow.lg,
  },
  toastTexto: {
    flex: 1,
    color: Colors.white,
    fontWeight: "700",
    fontSize: 14,
  },
  statusCard: {
    flexDirection: "row",
    alignItems: "center",
    gap: Spacing.md,
    backgroundColor: Colors.primaryLight,
    borderRadius: Radius.lg,
    padding: Spacing.lg,
    marginBottom: Spacing.md,
    borderWidth: 1.5,
    borderColor: Colors.primary + "40",
  },
  statusCardPremium: {
    backgroundColor: Colors.premiumLight,
    borderColor: Colors.premium + "40",
  },
  statusIcone: {
    width: 56,
    height: 56,
    borderRadius: 28,
    backgroundColor: Colors.white,
    alignItems: "center",
    justifyContent: "center",
  },
  statusLabel: {
    fontSize: 11,
    color: Colors.textSecondary,
    fontWeight: "600",
    textTransform: "uppercase",
    letterSpacing: 0.5,
    marginBottom: 2,
  },
  statusNome: {
    fontSize: 20,
    fontWeight: "800",
    color: Colors.primary,
  },
  statusPreco: {
    fontSize: 13,
    color: Colors.textSecondary,
    marginTop: 2,
  },
  secao: {
    backgroundColor: Colors.white,
    borderRadius: Radius.lg,
    padding: Spacing.md,
    marginBottom: Spacing.md,
    ...Shadow.sm,
  },
  proximoSecao: {
    borderWidth: 1.5,
    borderColor: Colors.premiumLight,
  },
  proximoHeader: {
    flexDirection: "row",
    alignItems: "center",
    marginBottom: Spacing.xs,
  },
  proximoPreco: {
    fontSize: 20,
    fontWeight: "800",
    color: Colors.premium,
    marginBottom: Spacing.md,
  },
  secaoTitulo: {
    fontSize: 13,
    fontWeight: "700",
    color: Colors.textSecondary,
    textTransform: "uppercase",
    letterSpacing: 0.5,
    marginBottom: Spacing.md,
  },
  recursoItem: {
    flexDirection: "row",
    alignItems: "flex-start",
    gap: Spacing.sm,
    paddingVertical: 5,
  },
  recursoTexto: {
    flex: 1,
    fontSize: 14,
    color: Colors.text,
    lineHeight: 20,
  },
  botao: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "center",
    borderRadius: Radius.md,
    height: 52,
    marginBottom: Spacing.md,
  },
  botaoUpgrade: {
    backgroundColor: Colors.premium,
    ...Shadow.md,
  },
  botaoDowngrade: {
    backgroundColor: Colors.textSecondary,
  },
  botaoDesabilitado: {
    opacity: 0.75,
  },
  processandoRow: {
    flexDirection: "row",
    alignItems: "center",
  },
  botaoTexto: {
    color: Colors.white,
    fontWeight: "700",
    fontSize: 15,
  },
  aviso: {
    fontSize: 11,
    color: Colors.textLight,
    textAlign: "center",
    lineHeight: 16,
    paddingHorizontal: Spacing.md,
  },
});
