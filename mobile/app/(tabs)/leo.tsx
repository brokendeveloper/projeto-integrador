import { useState, useCallback, useRef } from "react";
import {
  View,
  Text,
  TextInput,
  TouchableOpacity,
  FlatList,
  StyleSheet,
  ActivityIndicator,
  KeyboardAvoidingView,
  Platform,
} from "react-native";
import { Ionicons } from "@expo/vector-icons";
import { useFocusEffect, useRouter } from "expo-router";
import { api } from "../../services/api";
import { Colors, Radius, Spacing, Shadow } from "../../constants/theme";

interface Mensagem {
  id: string;
  role: "user" | "assistant";
  content: string;
}

interface HistoricoItem {
  role: "user" | "assistant";
  content: string;
}

const SUGESTOES = [
  "Quais editais são favoráveis para MEI?",
  "Quais órgãos publicam mais contratos?",
  "Quantos contratos temos na base?",
];

export default function LeoScreen() {
  const router = useRouter();
  const [isPremium, setIsPremium] = useState<boolean | null>(null);
  const [mensagens, setMensagens] = useState<Mensagem[]>([]);
  const [texto, setTexto] = useState("");
  const [enviando, setEnviando] = useState(false);
  const flatListRef = useRef<FlatList>(null);

  useFocusEffect(
    useCallback(() => {
      verificarPlano();
    }, [])
  );

  async function verificarPlano() {
    try {
      const { data } = await api.get("/plano");
      setIsPremium(data.plano_atual === "premium");
    } catch {
      setIsPremium(false);
    }
  }

  async function enviarMensagem(texto_input?: string) {
    const conteudo = (texto_input ?? texto).trim();
    if (!conteudo || enviando) return;

    const novaMensagem: Mensagem = {
      id: Date.now().toString(),
      role: "user",
      content: conteudo,
    };

    const historicoAtual = mensagens.map<HistoricoItem>((m) => ({
      role: m.role,
      content: m.content,
    }));

    setMensagens((prev) => [...prev, novaMensagem]);
    setTexto("");
    setEnviando(true);

    try {
      const { data } = await api.post("/chat/mensagem", {
        mensagem: conteudo,
        historico: historicoAtual,
      });

      setMensagens((prev) => [
        ...prev,
        {
          id: (Date.now() + 1).toString(),
          role: "assistant",
          content: data.resposta,
        },
      ]);
    } catch {
      setMensagens((prev) => [
        ...prev,
        {
          id: (Date.now() + 1).toString(),
          role: "assistant",
          content:
            "Desculpe, ocorreu um erro ao processar sua mensagem. Tente novamente.",
        },
      ]);
    } finally {
      setEnviando(false);
    }
  }

  // ── Loading ──────────────────────────────────────────────────────────────
  if (isPremium === null) {
    return (
      <View style={styles.center}>
        <ActivityIndicator size="large" color={Colors.primary} />
      </View>
    );
  }

  // ── Paywall (free) ────────────────────────────────────────────────────────
  if (!isPremium) {
    return (
      <View style={styles.paywallBg}>
        <View style={styles.paywallCard}>
          <View style={styles.paywallIconeCircle}>
            <Ionicons name="lock-closed" size={34} color={Colors.premium} />
          </View>

          <Text style={styles.paywallTitulo}>Conheça o Léo</Text>
          <Text style={styles.paywallDescricao}>
            Seu assistente inteligente de licitações. Disponível exclusivamente
            no plano Premium.
          </Text>

          <View style={styles.paywallFeatures}>
            {[
              "Análise de editais por CNAE",
              "Oportunidades para MEIs em tempo real",
              "Busca e filtro por voz",
              "Contexto de conversa persistente",
            ].map((f, i) => (
              <View key={i} style={styles.featureRow}>
                <Ionicons
                  name="checkmark-circle"
                  size={16}
                  color={Colors.premium}
                />
                <Text style={styles.featureTexto}>{f}</Text>
              </View>
            ))}
          </View>

          <TouchableOpacity
            style={styles.paywallBotao}
            onPress={() => router.push("/premium")}
            activeOpacity={0.85}
          >
            <Ionicons name="diamond-outline" size={18} color={Colors.white} />
            <Text style={styles.paywallBotaoTexto}>  Ativar Premium</Text>
          </TouchableOpacity>

          <Text style={styles.paywallPreco}>
            R$ 29,90/mês · Cancele quando quiser
          </Text>
        </View>
      </View>
    );
  }

  // ── Chat (premium) ────────────────────────────────────────────────────────
  function renderMensagem({ item }: { item: Mensagem }) {
    const isUser = item.role === "user";
    return (
      <View style={[styles.msgRow, isUser && styles.msgRowUser]}>
        {!isUser && (
          <View style={styles.msgAvatar}>
            <Ionicons name="sparkles" size={13} color={Colors.premium} />
          </View>
        )}
        <View
          style={[
            styles.msgBolha,
            isUser ? styles.msgBolhaUser : styles.msgBolhaLeo,
          ]}
        >
          <Text
            style={[styles.msgTexto, isUser && styles.msgTextoUser]}
          >
            {item.content}
          </Text>
        </View>
      </View>
    );
  }

  return (
    <KeyboardAvoidingView
      style={styles.container}
      behavior={Platform.OS === "ios" ? "padding" : undefined}
      keyboardVerticalOffset={90}
    >
      {/* Cabeçalho */}
      <View style={styles.header}>
        <View style={styles.headerAvatar}>
          <Ionicons name="sparkles" size={20} color={Colors.premium} />
        </View>
        <View style={styles.headerInfo}>
          <Text style={styles.headerNome}>Léo</Text>
          <Text style={styles.headerSub}>Assistente de licitações</Text>
        </View>
        <View style={styles.headerBadge}>
          <Ionicons name="diamond" size={10} color={Colors.premium} />
          <Text style={styles.headerBadgeTexto}> Premium</Text>
        </View>
      </View>

      {/* Mensagens */}
      <FlatList
        ref={flatListRef}
        data={mensagens}
        keyExtractor={(item) => item.id}
        renderItem={renderMensagem}
        contentContainerStyle={styles.listaContent}
        onContentSizeChange={() =>
          flatListRef.current?.scrollToEnd({ animated: true })
        }
        ListEmptyComponent={
          <View style={styles.emptyContainer}>
            <View style={styles.emptyIcone}>
              <Ionicons name="sparkles" size={38} color={Colors.premium} />
            </View>
            <Text style={styles.emptyTitulo}>Olá! Sou o Léo</Text>
            <Text style={styles.emptySub}>
              Pergunte sobre editais, valores, órgãos e oportunidades para MEIs.
            </Text>
            <View style={styles.sugestoesContainer}>
              {SUGESTOES.map((s, i) => (
                <TouchableOpacity
                  key={i}
                  style={styles.sugestaoChip}
                  onPress={() => enviarMensagem(s)}
                  activeOpacity={0.7}
                >
                  <Text style={styles.sugestaoTexto}>{s}</Text>
                </TouchableOpacity>
              ))}
            </View>
          </View>
        }
      />

      {/* Typing indicator */}
      {enviando && (
        <View style={styles.typingRow}>
          <View style={styles.msgAvatar}>
            <Ionicons name="sparkles" size={13} color={Colors.premium} />
          </View>
          <View style={styles.typingBolha}>
            <ActivityIndicator size="small" color={Colors.textSecondary} />
            <Text style={styles.typingTexto}>Léo está pensando…</Text>
          </View>
        </View>
      )}

      {/* Input */}
      <View style={styles.inputBar}>
        <TextInput
          style={styles.input}
          placeholder="Pergunte ao Léo…"
          placeholderTextColor={Colors.textLight}
          value={texto}
          onChangeText={setTexto}
          multiline
          maxLength={500}
          returnKeyType="send"
          blurOnSubmit
          onSubmitEditing={() => enviarMensagem()}
        />
        <TouchableOpacity
          style={[
            styles.sendBtn,
            (!texto.trim() || enviando) && styles.sendBtnDisabled,
          ]}
          onPress={() => enviarMensagem()}
          disabled={!texto.trim() || enviando}
          activeOpacity={0.8}
        >
          <Ionicons name="send" size={17} color={Colors.white} />
        </TouchableOpacity>
      </View>
    </KeyboardAvoidingView>
  );
}

const styles = StyleSheet.create({
  center: {
    flex: 1,
    alignItems: "center",
    justifyContent: "center",
    backgroundColor: Colors.background,
  },

  // ── Paywall ───────────────────────────────────────────────────────────────
  paywallBg: {
    flex: 1,
    backgroundColor: Colors.background,
    alignItems: "center",
    justifyContent: "center",
    padding: Spacing.md,
  },
  paywallCard: {
    backgroundColor: Colors.white,
    borderRadius: Radius.xl,
    padding: Spacing.xl,
    width: "100%",
    alignItems: "center",
    ...Shadow.lg,
    borderWidth: 1.5,
    borderColor: Colors.premiumLight,
  },
  paywallIconeCircle: {
    width: 72,
    height: 72,
    borderRadius: 36,
    backgroundColor: Colors.premiumLight,
    alignItems: "center",
    justifyContent: "center",
    marginBottom: Spacing.md,
  },
  paywallTitulo: {
    fontSize: 22,
    fontWeight: "800",
    color: Colors.text,
    marginBottom: Spacing.xs,
  },
  paywallDescricao: {
    fontSize: 14,
    color: Colors.textSecondary,
    textAlign: "center",
    lineHeight: 20,
    marginBottom: Spacing.md,
  },
  paywallFeatures: {
    alignSelf: "stretch",
    marginBottom: Spacing.lg,
    gap: 10,
  },
  featureRow: {
    flexDirection: "row",
    alignItems: "center",
    gap: Spacing.sm,
  },
  featureTexto: {
    fontSize: 14,
    color: Colors.text,
    flex: 1,
  },
  paywallBotao: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "center",
    backgroundColor: Colors.premium,
    borderRadius: Radius.md,
    height: 52,
    alignSelf: "stretch",
    marginBottom: Spacing.sm,
    ...Shadow.md,
  },
  paywallBotaoTexto: {
    color: Colors.white,
    fontWeight: "700",
    fontSize: 16,
  },
  paywallPreco: {
    fontSize: 12,
    color: Colors.textLight,
    textAlign: "center",
  },

  // ── Chat ──────────────────────────────────────────────────────────────────
  container: {
    flex: 1,
    backgroundColor: Colors.background,
  },
  header: {
    flexDirection: "row",
    alignItems: "center",
    backgroundColor: Colors.white,
    paddingHorizontal: Spacing.md,
    paddingVertical: 12,
    borderBottomWidth: 1,
    borderBottomColor: Colors.border,
    gap: Spacing.sm,
    ...Shadow.sm,
  },
  headerAvatar: {
    width: 40,
    height: 40,
    borderRadius: 20,
    backgroundColor: Colors.premiumLight,
    alignItems: "center",
    justifyContent: "center",
  },
  headerInfo: {
    flex: 1,
  },
  headerNome: {
    fontSize: 16,
    fontWeight: "700",
    color: Colors.text,
  },
  headerSub: {
    fontSize: 11,
    color: Colors.textSecondary,
  },
  headerBadge: {
    flexDirection: "row",
    alignItems: "center",
    backgroundColor: Colors.premiumLight,
    borderRadius: Radius.full,
    paddingHorizontal: 10,
    paddingVertical: 4,
    borderWidth: 1,
    borderColor: Colors.premium + "30",
  },
  headerBadgeTexto: {
    fontSize: 11,
    fontWeight: "700",
    color: Colors.premium,
  },
  listaContent: {
    padding: Spacing.md,
    paddingBottom: Spacing.sm,
    flexGrow: 1,
  },

  // Mensagens
  msgRow: {
    flexDirection: "row",
    alignItems: "flex-end",
    marginBottom: Spacing.sm,
    gap: Spacing.xs,
  },
  msgRowUser: {
    justifyContent: "flex-end",
  },
  msgAvatar: {
    width: 28,
    height: 28,
    borderRadius: 14,
    backgroundColor: Colors.premiumLight,
    alignItems: "center",
    justifyContent: "center",
    marginBottom: 2,
  },
  msgBolha: {
    maxWidth: "78%",
    borderRadius: Radius.lg,
    paddingHorizontal: 14,
    paddingVertical: 10,
  },
  msgBolhaUser: {
    backgroundColor: Colors.primary,
    borderBottomRightRadius: 4,
  },
  msgBolhaLeo: {
    backgroundColor: Colors.white,
    borderBottomLeftRadius: 4,
    borderWidth: 1,
    borderColor: Colors.border,
    ...Shadow.sm,
  },
  msgTexto: {
    fontSize: 14,
    color: Colors.text,
    lineHeight: 20,
  },
  msgTextoUser: {
    color: Colors.white,
  },

  // Typing
  typingRow: {
    flexDirection: "row",
    alignItems: "flex-end",
    paddingHorizontal: Spacing.md,
    paddingBottom: Spacing.xs,
    gap: Spacing.xs,
  },
  typingBolha: {
    flexDirection: "row",
    alignItems: "center",
    gap: Spacing.xs,
    backgroundColor: Colors.white,
    borderRadius: Radius.lg,
    borderBottomLeftRadius: 4,
    paddingHorizontal: 14,
    paddingVertical: 10,
    borderWidth: 1,
    borderColor: Colors.border,
    ...Shadow.sm,
  },
  typingTexto: {
    fontSize: 13,
    color: Colors.textSecondary,
    fontStyle: "italic",
  },

  // Vazio / sugestões
  emptyContainer: {
    flex: 1,
    alignItems: "center",
    paddingTop: 40,
    paddingHorizontal: Spacing.md,
  },
  emptyIcone: {
    width: 72,
    height: 72,
    borderRadius: 36,
    backgroundColor: Colors.premiumLight,
    alignItems: "center",
    justifyContent: "center",
    marginBottom: Spacing.md,
  },
  emptyTitulo: {
    fontSize: 20,
    fontWeight: "800",
    color: Colors.text,
    marginBottom: Spacing.xs,
  },
  emptySub: {
    fontSize: 14,
    color: Colors.textSecondary,
    textAlign: "center",
    lineHeight: 20,
    marginBottom: Spacing.lg,
  },
  sugestoesContainer: {
    alignSelf: "stretch",
    gap: Spacing.sm,
  },
  sugestaoChip: {
    backgroundColor: Colors.white,
    borderRadius: Radius.md,
    padding: Spacing.md,
    borderWidth: 1.5,
    borderColor: Colors.premium + "40",
    ...Shadow.sm,
  },
  sugestaoTexto: {
    fontSize: 13,
    color: Colors.premium,
    fontWeight: "500",
    textAlign: "center",
  },

  // Input
  inputBar: {
    flexDirection: "row",
    alignItems: "flex-end",
    backgroundColor: Colors.white,
    borderTopWidth: 1,
    borderTopColor: Colors.border,
    paddingHorizontal: Spacing.md,
    paddingVertical: Spacing.sm,
    gap: Spacing.sm,
  },
  input: {
    flex: 1,
    minHeight: 44,
    maxHeight: 100,
    borderWidth: 1.5,
    borderColor: Colors.border,
    borderRadius: Radius.xl,
    paddingHorizontal: Spacing.md,
    paddingVertical: 10,
    fontSize: 14,
    color: Colors.text,
    backgroundColor: Colors.surface,
  },
  sendBtn: {
    width: 44,
    height: 44,
    borderRadius: 22,
    backgroundColor: Colors.primary,
    alignItems: "center",
    justifyContent: "center",
    ...Shadow.sm,
  },
  sendBtnDisabled: {
    backgroundColor: Colors.textLight,
  },
});
