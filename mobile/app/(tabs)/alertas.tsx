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
  ScrollView,
} from "react-native";
import { useFocusEffect } from "expo-router";
import { api } from "../../services/api";
import { Colors } from "../../constants/theme";

interface Alerta {
  id: string;
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
    const partes = [];
    if (item.cnae) partes.push(`CNAE: ${item.cnae}`);
    if (item.valor_max) partes.push(`Até R$ ${item.valor_max.toLocaleString("pt-BR")}`);
    if (item.uf) partes.push(`UF: ${item.uf}`);

    return (
      <View style={styles.card}>
        <View style={{ flex: 1 }}>
          <Text style={styles.filtros}>{partes.join(" · ") || "Todos os editais"}</Text>
          <Text style={styles.data}>Criado em {new Date(item.criado_em).toLocaleDateString("pt-BR")}</Text>
        </View>
        <TouchableOpacity onPress={() => handleExcluir(item.id)}>
          <Text style={{ fontSize: 20 }}>🗑️</Text>
        </TouchableOpacity>
      </View>
    );
  }

  return (
    <View style={styles.container}>
      <View style={styles.contador}>
        <Text style={styles.contadorTexto}>
          {alertas.length}/{LIMITE_FREE} alertas (plano gratuito)
        </Text>
      </View>

      {limiteAtingido && (
        <View style={styles.banner}>
          <Text style={styles.bannerTexto}>
            🔒 Limite atingido. Faça upgrade para o plano Premium e crie alertas ilimitados.
          </Text>
        </View>
      )}

      {!limiteAtingido && (
        <View style={styles.formulario}>
          <Text style={styles.formularioTitulo}>Novo alerta</Text>
          <TextInput
            style={styles.input}
            placeholder="CNAE (ex: 4711302)"
            value={cnae}
            onChangeText={setCnae}
            keyboardType="numeric"
            placeholderTextColor={Colors.textSecondary}
          />
          <TextInput
            style={styles.input}
            placeholder="Valor máximo (R$)"
            value={valorMax}
            onChangeText={setValorMax}
            keyboardType="numeric"
            placeholderTextColor={Colors.textSecondary}
          />
          <TextInput
            style={styles.input}
            placeholder="UF (ex: SP)"
            value={uf}
            onChangeText={setUf}
            maxLength={2}
            autoCapitalize="characters"
            placeholderTextColor={Colors.textSecondary}
          />
          <TouchableOpacity
            style={[styles.botao, criando && styles.botaoDesabilitado]}
            onPress={handleCriar}
            disabled={criando}
          >
            {criando ? (
              <ActivityIndicator color="#fff" />
            ) : (
              <Text style={styles.botaoTexto}>Criar alerta</Text>
            )}
          </TouchableOpacity>
        </View>
      )}

      {carregando ? (
        <ActivityIndicator style={{ margin: 24 }} color={Colors.primary} />
      ) : (
        <FlatList
          data={alertas}
          keyExtractor={(item) => item.id}
          renderItem={renderAlerta}
          contentContainerStyle={styles.lista}
          ListEmptyComponent={
            <Text style={styles.vazio}>Nenhum alerta configurado.</Text>
          }
        />
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: Colors.background },
  contador: {
    padding: 12, backgroundColor: Colors.card,
    borderBottomWidth: 1, borderBottomColor: Colors.border,
  },
  contadorTexto: { fontSize: 13, color: Colors.textSecondary, textAlign: "center" },
  banner: {
    margin: 12, backgroundColor: "#FFF8E1", borderRadius: 8,
    padding: 14, borderWidth: 1, borderColor: Colors.premium,
  },
  bannerTexto: { fontSize: 13, color: "#5D4037", lineHeight: 20 },
  formulario: {
    margin: 12, backgroundColor: Colors.card, borderRadius: 10,
    padding: 14, borderWidth: 1, borderColor: Colors.border,
  },
  formularioTitulo: { fontSize: 15, fontWeight: "700", color: Colors.text, marginBottom: 10 },
  input: {
    borderWidth: 1, borderColor: Colors.border, borderRadius: 8,
    padding: 10, fontSize: 14, color: Colors.text, marginBottom: 10,
  },
  botao: { backgroundColor: Colors.primary, borderRadius: 8, padding: 12, alignItems: "center" },
  botaoDesabilitado: { opacity: 0.6 },
  botaoTexto: { color: "#fff", fontWeight: "700", fontSize: 14 },
  lista: { padding: 12, paddingBottom: 32 },
  card: {
    flexDirection: "row", alignItems: "center", backgroundColor: Colors.card,
    borderRadius: 8, padding: 12, marginBottom: 8,
    borderWidth: 1, borderColor: Colors.border,
  },
  filtros: { fontSize: 13, fontWeight: "600", color: Colors.text },
  data: { fontSize: 11, color: Colors.textSecondary, marginTop: 2 },
  vazio: { textAlign: "center", color: Colors.textSecondary, marginTop: 48, fontSize: 15, padding: 24 },
});
