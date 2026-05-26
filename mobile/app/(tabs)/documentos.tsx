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
  Platform,
} from "react-native";
import * as DocumentPicker from "expo-document-picker";
import { useFocusEffect } from "expo-router";
import { api } from "../../services/api";
import { Colors } from "../../constants/theme";

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
    return (
      <View style={styles.card}>
        <View style={styles.cardInfo}>
          <Text style={styles.nome} numberOfLines={1}>{item.nome}</Text>
          <Text style={styles.meta}>
            {formatarBytes(item.tamanho)} · {new Date(item.criado_em).toLocaleDateString("pt-BR")}
          </Text>
        </View>
        <TouchableOpacity onPress={() => handleExcluir(item.id, item.nome)} style={styles.botaoExcluir}>
          <Text style={styles.excluirTexto}>🗑️</Text>
        </TouchableOpacity>
      </View>
    );
  }

  return (
    <View style={styles.container}>
      <View style={styles.topo}>
        <TextInput
          style={styles.input}
          placeholder="ID do edital"
          value={editalId}
          onChangeText={setEditalId}
          autoCapitalize="none"
          placeholderTextColor={Colors.textSecondary}
        />
        <TouchableOpacity style={styles.botaoCarregar} onPress={carregarDocumentos}>
          <Text style={styles.botaoTexto}>Ver</Text>
        </TouchableOpacity>
      </View>

      <TouchableOpacity
        style={[styles.botaoUpload, enviando && styles.botaoDesabilitado]}
        onPress={handleUpload}
        disabled={enviando}
      >
        {enviando ? (
          <ActivityIndicator color="#fff" />
        ) : (
          <Text style={styles.uploadTexto}>+ Enviar documento</Text>
        )}
      </TouchableOpacity>

      {carregando ? (
        <ActivityIndicator style={{ margin: 24 }} color={Colors.primary} />
      ) : (
        <FlatList
          data={documentos}
          keyExtractor={(item) => item.id}
          renderItem={renderDocumento}
          contentContainerStyle={styles.lista}
          ListEmptyComponent={
            <Text style={styles.vazio}>Nenhum documento enviado para este edital.</Text>
          }
        />
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: Colors.background },
  topo: {
    flexDirection: "row", padding: 12, gap: 8,
    backgroundColor: Colors.card, borderBottomWidth: 1, borderBottomColor: Colors.border,
  },
  input: {
    flex: 1, borderWidth: 1, borderColor: Colors.border, borderRadius: 8,
    padding: 10, fontSize: 14, color: Colors.text,
  },
  botaoCarregar: { backgroundColor: Colors.primary, borderRadius: 8, padding: 10, justifyContent: "center" },
  botaoTexto: { color: "#fff", fontWeight: "700", fontSize: 13 },
  botaoUpload: {
    margin: 12, backgroundColor: Colors.secondary, borderRadius: 8,
    padding: 14, alignItems: "center",
  },
  botaoDesabilitado: { opacity: 0.6 },
  uploadTexto: { color: "#fff", fontWeight: "700", fontSize: 15 },
  lista: { padding: 12, paddingBottom: 32 },
  card: {
    flexDirection: "row", alignItems: "center", backgroundColor: Colors.card,
    borderRadius: 8, padding: 12, marginBottom: 8,
    borderWidth: 1, borderColor: Colors.border,
  },
  cardInfo: { flex: 1, marginRight: 8 },
  nome: { fontSize: 13, fontWeight: "600", color: Colors.text },
  meta: { fontSize: 11, color: Colors.textSecondary, marginTop: 2 },
  botaoExcluir: { padding: 4 },
  excluirTexto: { fontSize: 20 },
  vazio: { textAlign: "center", color: Colors.textSecondary, marginTop: 48, fontSize: 15, padding: 24 },
});
