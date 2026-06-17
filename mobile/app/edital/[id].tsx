import { useState, useEffect } from "react";
import {
  View,
  Text,
  ScrollView,
  TouchableOpacity,
  StyleSheet,
  ActivityIndicator,
  Alert,
  Linking,
} from "react-native";
import { Ionicons } from "@expo/vector-icons";
import { useLocalSearchParams, useRouter } from "expo-router";
import { api } from "../../services/api";
import { Colors, Radius, Spacing, Shadow } from "../../constants/theme";

interface EditalDetalhe {
  id: string;
  numero_controle: string;
  objeto: string;
  orgao: string;
  cnpj_orgao: string | null;
  valor_estimado: number | null;
  data_publicacao: string | null;
  data_encerramento: string | null;
  modalidade: string | null;
  uf: string | null;
  favoravel_mei: boolean;
  url_edital: string | null;
}

function formatarMoeda(valor: number | null): string {
  if (valor === null) return "Não informado";
  return valor.toLocaleString("pt-BR", { style: "currency", currency: "BRL" });
}

function formatarData(data: string | null): string {
  if (!data) return "—";
  return new Date(data).toLocaleDateString("pt-BR");
}

export default function EditalDetalheScreen() {
  const { id } = useLocalSearchParams<{ id: string }>();
  const router = useRouter();
  const [edital, setEdital] = useState<EditalDetalhe | null>(null);
  const [carregando, setCarregando] = useState(true);

  useEffect(() => {
    carregarEdital();
  }, [id]);

  async function carregarEdital() {
    try {
      const { data } = await api.get(`/editais/${id}`);
      setEdital(data);
    } catch {
      Alert.alert("Erro", "Não foi possível carregar o edital.", [
        { text: "Voltar", onPress: () => router.back() },
      ]);
    } finally {
      setCarregando(false);
    }
  }

  if (carregando) {
    return (
      <View style={styles.center}>
        <ActivityIndicator size="large" color={Colors.primary} />
      </View>
    );
  }

  if (!edital) return null;

  const favoravel =
    edital.favoravel_mei ||
    (edital.valor_estimado !== null && edital.valor_estimado <= 80000);

  return (
    <View style={styles.container}>
      {/* Header */}
      <View style={styles.header}>
        <TouchableOpacity onPress={() => router.back()} style={styles.btnVoltar}>
          <Ionicons name="arrow-back" size={22} color={Colors.text} />
        </TouchableOpacity>
        <Text style={styles.headerTitulo} numberOfLines={1}>
          Edital
        </Text>
      </View>

      <ScrollView contentContainerStyle={styles.scroll} showsVerticalScrollIndicator={false}>
        {/* Badge MEI */}
        {favoravel && (
          <View style={styles.meiBadge}>
            <Ionicons name="checkmark-circle" size={14} color={Colors.success} />
            <Text style={styles.meiBadgeTexto}>Favorável para MEI</Text>
          </View>
        )}

        {/* Objeto */}
        <Text style={styles.objeto}>{edital.objeto}</Text>

        {/* Número de controle */}
        <Text style={styles.controle}>Nº {edital.numero_controle}</Text>

        {/* Seção: Órgão */}
        <View style={styles.secao}>
          <Text style={styles.secaoTitulo}>Órgão responsável</Text>
          <View style={styles.infoRow}>
            <Ionicons name="business-outline" size={16} color={Colors.primary} />
            <Text style={styles.infoTexto}>{edital.orgao}</Text>
          </View>
          {edital.uf && (
            <View style={styles.infoRow}>
              <Ionicons name="location-outline" size={16} color={Colors.textLight} />
              <Text style={styles.infoTexto}>{edital.uf}</Text>
            </View>
          )}
          {edital.cnpj_orgao && (
            <View style={styles.infoRow}>
              <Ionicons name="card-outline" size={16} color={Colors.textLight} />
              <Text style={styles.infoTexto}>CNPJ: {edital.cnpj_orgao}</Text>
            </View>
          )}
        </View>

        {/* Seção: Valores e datas */}
        <View style={styles.secao}>
          <Text style={styles.secaoTitulo}>Informações do edital</Text>

          <View style={styles.gridInfo}>
            <View style={styles.gridItem}>
              <Text style={styles.gridLabel}>Valor estimado</Text>
              <Text style={[styles.gridValor, favoravel && styles.gridValorFavoravel]}>
                {formatarMoeda(edital.valor_estimado)}
              </Text>
            </View>
            <View style={styles.gridItem}>
              <Text style={styles.gridLabel}>Encerra em</Text>
              <Text style={styles.gridValor}>{formatarData(edital.data_encerramento)}</Text>
            </View>
            <View style={styles.gridItem}>
              <Text style={styles.gridLabel}>Publicado em</Text>
              <Text style={styles.gridValor}>{formatarData(edital.data_publicacao)}</Text>
            </View>
            {edital.modalidade && (
              <View style={styles.gridItem}>
                <Text style={styles.gridLabel}>Modalidade</Text>
                <Text style={styles.gridValor}>{edital.modalidade}</Text>
              </View>
            )}
          </View>
        </View>

        {/* Link PNCP */}
        {edital.url_edital && (
          <TouchableOpacity
            style={styles.linkPncp}
            onPress={() => Linking.openURL(edital.url_edital!)}
            activeOpacity={0.7}
          >
            <Ionicons name="open-outline" size={16} color={Colors.primary} />
            <Text style={styles.linkPncpTexto}>Ver edital original no PNCP</Text>
            <Ionicons name="chevron-forward" size={14} color={Colors.primary} />
          </TouchableOpacity>
        )}

        {/* Ações */}
        <View style={styles.secao}>
          <Text style={styles.secaoTitulo}>Ações</Text>

          <TouchableOpacity
            style={styles.acaoPrimaria}
            onPress={() =>
              router.push({ pathname: "/(tabs)/checklist", params: { editalId: edital.id } })
            }
            activeOpacity={0.85}
          >
            <Ionicons name="checkbox-outline" size={20} color={Colors.white} />
            <Text style={styles.acaoPrimariaTexto}>Ver checklist de habilitação</Text>
            <Ionicons name="chevron-forward" size={16} color={Colors.white} />
          </TouchableOpacity>

          <TouchableOpacity
            style={styles.acaoSecundaria}
            onPress={() =>
              router.push({ pathname: "/(tabs)/documentos", params: { editalId: edital.id } })
            }
            activeOpacity={0.85}
          >
            <Ionicons name="document-attach-outline" size={20} color={Colors.primary} />
            <Text style={styles.acaoSecundariaTexto}>Enviar documentos</Text>
            <Ionicons name="chevron-forward" size={16} color={Colors.primary} />
          </TouchableOpacity>

          <TouchableOpacity
            style={styles.acaoSecundaria}
            onPress={() =>
              router.push({ pathname: "/(tabs)/alertas", params: { editalId: edital.id } })
            }
            activeOpacity={0.85}
          >
            <Ionicons name="notifications-outline" size={20} color={Colors.primary} />
            <Text style={styles.acaoSecundariaTexto}>Criar alerta de prazo</Text>
            <Ionicons name="chevron-forward" size={16} color={Colors.primary} />
          </TouchableOpacity>

          <TouchableOpacity
            style={styles.acaoSecundaria}
            onPress={() =>
              router.push({ pathname: "/(tabs)/historico", params: { editalId: edital.id } })
            }
            activeOpacity={0.85}
          >
            <Ionicons name="trophy-outline" size={20} color={Colors.primary} />
            <Text style={styles.acaoSecundariaTexto}>Registrar participação</Text>
            <Ionicons name="chevron-forward" size={16} color={Colors.primary} />
          </TouchableOpacity>
        </View>
      </ScrollView>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: Colors.background,
  },
  center: {
    flex: 1,
    alignItems: "center",
    justifyContent: "center",
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
  btnVoltar: {
    padding: 4,
  },
  headerTitulo: {
    fontSize: 17,
    fontWeight: "700",
    color: Colors.text,
    flex: 1,
  },
  scroll: {
    padding: Spacing.md,
    paddingBottom: 40,
  },
  meiBadge: {
    flexDirection: "row",
    alignItems: "center",
    gap: 6,
    backgroundColor: Colors.successLight,
    borderRadius: Radius.sm,
    paddingHorizontal: Spacing.sm,
    paddingVertical: 5,
    alignSelf: "flex-start",
    marginBottom: Spacing.sm,
  },
  meiBadgeTexto: {
    color: Colors.success,
    fontSize: 12,
    fontWeight: "700",
  },
  objeto: {
    fontSize: 18,
    fontWeight: "700",
    color: Colors.text,
    lineHeight: 26,
    marginBottom: Spacing.xs,
  },
  controle: {
    fontSize: 12,
    color: Colors.textLight,
    marginBottom: Spacing.lg,
    fontFamily: "monospace" as any,
  },
  secao: {
    backgroundColor: Colors.white,
    borderRadius: Radius.lg,
    padding: Spacing.md,
    marginBottom: Spacing.md,
    borderWidth: 1,
    borderColor: Colors.border,
    ...Shadow.sm,
  },
  secaoTitulo: {
    fontSize: 12,
    fontWeight: "700",
    color: Colors.textLight,
    textTransform: "uppercase",
    letterSpacing: 0.8,
    marginBottom: Spacing.sm,
  },
  infoRow: {
    flexDirection: "row",
    alignItems: "flex-start",
    gap: Spacing.sm,
    marginBottom: 8,
  },
  infoTexto: {
    fontSize: 14,
    color: Colors.text,
    flex: 1,
    lineHeight: 20,
  },
  gridInfo: {
    flexDirection: "row",
    flexWrap: "wrap",
    gap: Spacing.md,
  },
  gridItem: {
    minWidth: "44%",
    flex: 1,
  },
  gridLabel: {
    fontSize: 10,
    color: Colors.textLight,
    fontWeight: "600",
    textTransform: "uppercase",
    letterSpacing: 0.5,
    marginBottom: 3,
  },
  gridValor: {
    fontSize: 14,
    fontWeight: "600",
    color: Colors.text,
  },
  gridValorFavoravel: {
    color: Colors.success,
  },
  linkPncp: {
    flexDirection: "row",
    alignItems: "center",
    gap: Spacing.sm,
    backgroundColor: Colors.primaryLight,
    borderRadius: Radius.md,
    padding: Spacing.md,
    marginBottom: Spacing.md,
    borderWidth: 1,
    borderColor: Colors.primary + "30",
  },
  linkPncpTexto: {
    flex: 1,
    fontSize: 13,
    color: Colors.primary,
    fontWeight: "600",
  },
  acaoPrimaria: {
    flexDirection: "row",
    alignItems: "center",
    gap: Spacing.sm,
    backgroundColor: Colors.primary,
    borderRadius: Radius.md,
    padding: Spacing.md,
    marginBottom: Spacing.sm,
    ...Shadow.sm,
  },
  acaoPrimariaTexto: {
    flex: 1,
    fontSize: 14,
    color: Colors.white,
    fontWeight: "700",
  },
  acaoSecundaria: {
    flexDirection: "row",
    alignItems: "center",
    gap: Spacing.sm,
    backgroundColor: Colors.white,
    borderRadius: Radius.md,
    padding: Spacing.md,
    marginBottom: Spacing.sm,
    borderWidth: 1.5,
    borderColor: Colors.border,
  },
  acaoSecundariaTexto: {
    flex: 1,
    fontSize: 14,
    color: Colors.text,
    fontWeight: "600",
  },
});
