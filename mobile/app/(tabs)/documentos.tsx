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
import * as DocumentPicker from "expo-document-picker";
import { useFocusEffect } from "expo-router";
import { api } from "../../services/api";
import { Colors, Radius, Spacing, Shadow } from "../../constants/theme";

interface Documento {
  id: string;
  nome: string;
  tamanho: number;
  tipo: string;
  criado_em: string;
}

function formatarBytes(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

function getFileIcon(tipo: string): string {
  if (tipo?.includes("pdf")) return "document-text";
  if (tipo?.includes("image")) return "image";
  if (tipo?.includes("word") || tipo?.includes("document")) return "document";
  if (tipo?.includes("sheet") || tipo?.includes("excel")) return "grid";
  return "attach";
}

export default function DocumentosScreen() {
  const [editalId, setEditalId] = useState("");
  const [documentos, setDocumentos] = useState<Documento[]>([]);
  const [carregando, setCarregando] = useState(false);
  const [enviando, setEnviando] = useState(false);

  async function carregarDocumentos() {
    if (!editalId.trim()) return;
    setCarregando(true);
    try {
      const { data } = await api.get(`/editais/${editalId.trim()}/documentos`);
      setDocumentos(data);
    } catch {
      Alert.alert("Erro", "Não foi possível carregar os documentos.");
    } finally {
      setCarregando(false);
    }
  }

  async function handleUpload() {
    if (!editalId.trim()) {
      Alert.alert("Atenção", "Informe o ID do edital antes de enviar.");
      return;
    }
    const resultado = await DocumentPicker.getDocumentAsync({ copyToCacheDirectory: true });
    if (resultado.canceled) return;

    const arquivo = resultado.assets[0];
    setEnviando(true);
    try {
      const form = new FormData();
      form.append("arquivo", {
        uri: arquivo.uri,
        name: arquivo.name,
        type: arquivo.mimeType ?? "application/octet-stream",
      } as any);

      await api.post(`/editais/${editalId.trim()}/documentos`, form, {
        headers: { "Content-Type": "multipart/form-data" },
      });
      await carregarDocumentos();
    } catch {
      Alert.alert("Erro", "Falha ao enviar o documento.");
    } finally {
      setEnviando(false);
    }
  }

  async function handleExcluir(docId: string, nome: string) {
    Alert.alert("Excluir documento", `Remover "${nome}"?`, [
      { text: "Cancelar", style: "cancel" },
      {
        text: "Excluir",
        style: "destructive",
        onPress: async () => {
          try {
            await api.delete(`/editais/${editalId}/documentos/${docId}`);
            setDocumentos((prev) => prev.filter((d) => d.id !== docId));
          } catch {
            Alert.alert("Erro", "Não foi possível excluir.");
          }
        },
      },
    ]);
  }

  function renderDocumento({ item }: { item: Documento }) {
    const iconName = getFileIcon(item.tipo ?? "");
    return (
      <View style={styles.card}>
        <View style={styles.fileIcon}>
          <Ionicons name={iconName as any} size={22} color={Colors.primary} />
        </View>
        <View style={styles.cardInfo}>
          <Text style={styles.nome} numberOfLines={1}>
            {item.nome}
          </Text>
          <Text style={styles.meta}>
            {formatarBytes(item.tamanho)}
            {item.criado_em
              ? ` · ${new Date(item.criado_em).toLocaleDateString("pt-BR")}`
              : ""}
          </Text>
        </View>
        <TouchableOpacity
          onPress={() => handleExcluir(item.id, item.nome)}
          style={styles.excluirButton}
          hitSlop={{ top: 8, bottom: 8, left: 8, right: 8 }}
        >
          <Ionicons name="trash-outline" size={18} color={Colors.danger} />
        </TouchableOpacity>
      </View>
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
            onSubmitEditing={carregarDocumentos}
            returnKeyType="search"
          />
        </View>
        <TouchableOpacity style={styles.botaoVer} onPress={carregarDocumentos} activeOpacity={0.8}>
          <Text style={styles.botaoVerTexto}>Ver</Text>
        </TouchableOpacity>
      </View>

      {/* Upload button */}
      <TouchableOpacity
        style={[styles.uploadButton, enviando && styles.uploadButtonDesabilitado]}
        onPress={handleUpload}
        disabled={enviando}
        activeOpacity={0.85}
      >
        {enviando ? (
          <ActivityIndicator color={Colors.white} size="small" />
        ) : (
          <>
            <Ionicons name="cloud-upload-outline" size={18} color={Colors.white} />
            <Text style={styles.uploadTexto}>  Enviar documento</Text>
          </>
        )}
      </TouchableOpacity>

      {carregando ? (
        <ActivityIndicator style={{ margin: 32 }} color={Colors.primary} size="large" />
      ) : (
        <FlatList
          data={documentos}
          keyExtractor={(item) => item.id}
          renderItem={renderDocumento}
          contentContainerStyle={styles.lista}
          ListEmptyComponent={
            <View style={styles.vazioContainer}>
              <Ionicons name="folder-open-outline" size={52} color={Colors.border} />
              <Text style={styles.vazioTexto}>Nenhum documento enviado.</Text>
              <Text style={styles.vazioSub}>
                Carregue um edital e envie os documentos de habilitação.
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
  botaoVer: {
    backgroundColor: Colors.primary,
    borderRadius: Radius.md,
    paddingHorizontal: Spacing.md,
    justifyContent: "center",
    alignItems: "center",
    height: 44,
  },
  botaoVerTexto: {
    color: Colors.white,
    fontWeight: "700",
    fontSize: 14,
  },
  uploadButton: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "center",
    margin: Spacing.md,
    backgroundColor: Colors.success,
    borderRadius: Radius.md,
    padding: 14,
    ...Shadow.sm,
  },
  uploadButtonDesabilitado: {
    opacity: 0.65,
  },
  uploadTexto: {
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
  },
  fileIcon: {
    width: 40,
    height: 40,
    borderRadius: Radius.sm,
    backgroundColor: Colors.primaryLight,
    alignItems: "center",
    justifyContent: "center",
    marginRight: Spacing.md,
  },
  cardInfo: {
    flex: 1,
    marginRight: Spacing.sm,
  },
  nome: {
    fontSize: 13,
    fontWeight: "600",
    color: Colors.text,
    marginBottom: 2,
  },
  meta: {
    fontSize: 11,
    color: Colors.textSecondary,
  },
  excluirButton: {
    padding: 4,
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
