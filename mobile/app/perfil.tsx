import { useState, useEffect } from "react";
import {
  View,
  Text,
  TextInput,
  TouchableOpacity,
  StyleSheet,
  ScrollView,
  ActivityIndicator,
  Alert,
} from "react-native";
import { Ionicons } from "@expo/vector-icons";
import { api } from "../services/api";
import { Colors, Radius, Spacing, Shadow } from "../constants/theme";

function formatarCNPJ(digits: string): string {
  const d = digits.replace(/\D/g, "").slice(0, 14);
  return d
    .replace(/^(\d{2})(\d)/, "$1.$2")
    .replace(/^(\d{2})\.(\d{3})(\d)/, "$1.$2.$3")
    .replace(/\.(\d{3})(\d)/, ".$1/$2")
    .replace(/(\d{4})(\d)/, "$1-$2");
}

export default function PerfilScreen() {
  const [carregando, setCarregando] = useState(true);
  const [salvando, setSalvando] = useState(false);

  const [nome, setNome] = useState("");
  const [email, setEmail] = useState("");
  const [cnpj, setCnpj] = useState("");
  const [senhaAtual, setSenhaAtual] = useState("");
  const [senhaNova, setSenhaNova] = useState("");
  const [mostrarSenha, setMostrarSenha] = useState(false);

  useEffect(() => {
    api.get("/perfil").then(({ data }) => {
      setNome(data.nome);
      setEmail(data.email);
      setCnpj(formatarCNPJ(data.cnpj));
    }).catch(() => {
      Alert.alert("Erro", "Não foi possível carregar o perfil.");
    }).finally(() => setCarregando(false));
  }, []);

  async function handleSalvar() {
    setSalvando(true);
    try {
      const payload: Record<string, string> = {};
      if (nome.trim()) payload.nome = nome.trim();
      if (email.trim()) payload.email = email.trim();
      if (cnpj.trim()) payload.cnpj = cnpj.replace(/\D/g, "");
      if (senhaNova.trim()) {
        payload.senha_atual = senhaAtual;
        payload.senha_nova = senhaNova;
      }

      await api.patch("/perfil", payload);
      Alert.alert("Salvo!", "Perfil atualizado com sucesso.");
      setSenhaAtual("");
      setSenhaNova("");
    } catch (e: any) {
      const msg = e?.response?.data?.detail ?? "Erro ao atualizar perfil.";
      Alert.alert("Erro", msg);
    } finally {
      setSalvando(false);
    }
  }

  if (carregando) {
    return (
      <View style={styles.loading}>
        <ActivityIndicator size="large" color={Colors.primary} />
      </View>
    );
  }

  return (
    <ScrollView style={styles.container} contentContainerStyle={styles.content} keyboardShouldPersistTaps="handled">
      {/* Dados pessoais */}
      <View style={styles.secao}>
        <Text style={styles.secaoTitulo}>Dados pessoais</Text>

        <Text style={styles.label}>Nome completo</Text>
        <TextInput
          style={styles.input}
          value={nome}
          onChangeText={setNome}
          autoCapitalize="words"
          placeholderTextColor={Colors.textLight}
        />

        <Text style={styles.label}>E-mail</Text>
        <TextInput
          style={styles.input}
          value={email}
          onChangeText={setEmail}
          keyboardType="email-address"
          autoCapitalize="none"
          placeholderTextColor={Colors.textLight}
        />

        <Text style={styles.label}>CNPJ</Text>
        <TextInput
          style={styles.input}
          value={cnpj}
          onChangeText={(v) => setCnpj(formatarCNPJ(v))}
          keyboardType="numeric"
          placeholderTextColor={Colors.textLight}
        />
      </View>

      {/* Alterar senha */}
      <View style={styles.secao}>
        <Text style={styles.secaoTitulo}>Alterar senha</Text>
        <Text style={styles.secaoSub}>Deixe em branco para não alterar a senha.</Text>

        <Text style={styles.label}>Senha atual</Text>
        <View style={styles.senhaWrapper}>
          <TextInput
            style={styles.senhaInput}
            value={senhaAtual}
            onChangeText={setSenhaAtual}
            secureTextEntry={!mostrarSenha}
            placeholder="Senha atual"
            placeholderTextColor={Colors.textLight}
          />
          <TouchableOpacity onPress={() => setMostrarSenha(!mostrarSenha)} style={styles.senhaIcone}>
            <Ionicons name={mostrarSenha ? "eye-off-outline" : "eye-outline"} size={20} color={Colors.textLight} />
          </TouchableOpacity>
        </View>

        <Text style={styles.label}>Nova senha</Text>
        <TextInput
          style={styles.input}
          value={senhaNova}
          onChangeText={setSenhaNova}
          secureTextEntry={!mostrarSenha}
          placeholder="Mínimo 8 caracteres"
          placeholderTextColor={Colors.textLight}
        />
      </View>

      <TouchableOpacity
        style={[styles.botao, salvando && styles.botaoDesabilitado]}
        onPress={handleSalvar}
        disabled={salvando}
        activeOpacity={0.85}
      >
        {salvando ? (
          <ActivityIndicator color={Colors.white} />
        ) : (
          <>
            <Ionicons name="checkmark-circle-outline" size={18} color={Colors.white} />
            <Text style={styles.botaoTexto}>  Salvar alterações</Text>
          </>
        )}
      </TouchableOpacity>
    </ScrollView>
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
  secao: {
    backgroundColor: Colors.white,
    borderRadius: Radius.lg,
    padding: Spacing.md,
    marginBottom: Spacing.md,
    ...Shadow.sm,
  },
  secaoTitulo: {
    fontSize: 15,
    fontWeight: "700",
    color: Colors.text,
    marginBottom: 4,
  },
  secaoSub: {
    fontSize: 12,
    color: Colors.textSecondary,
    marginBottom: Spacing.md,
  },
  label: {
    fontSize: 12,
    fontWeight: "600",
    color: Colors.textSecondary,
    marginBottom: 5,
    marginTop: Spacing.sm,
    letterSpacing: 0.1,
  },
  input: {
    height: 48,
    borderWidth: 1.5,
    borderColor: Colors.border,
    borderRadius: Radius.md,
    paddingHorizontal: Spacing.md,
    fontSize: 15,
    color: Colors.text,
    backgroundColor: Colors.surface,
  },
  senhaWrapper: {
    flexDirection: "row",
    alignItems: "center",
    borderWidth: 1.5,
    borderColor: Colors.border,
    borderRadius: Radius.md,
    backgroundColor: Colors.surface,
    height: 48,
  },
  senhaInput: {
    flex: 1,
    paddingHorizontal: Spacing.md,
    fontSize: 15,
    color: Colors.text,
  },
  senhaIcone: {
    padding: Spacing.md,
  },
  botao: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "center",
    backgroundColor: Colors.primary,
    borderRadius: Radius.md,
    height: 52,
    marginTop: Spacing.sm,
    ...Shadow.sm,
  },
  botaoDesabilitado: {
    opacity: 0.65,
  },
  botaoTexto: {
    color: Colors.white,
    fontWeight: "700",
    fontSize: 16,
  },
});
