import { useState } from "react";
import {
  View,
  Text,
  TextInput,
  TouchableOpacity,
  StyleSheet,
  ActivityIndicator,
  Alert,
  KeyboardAvoidingView,
  Platform,
  ScrollView,
} from "react-native";
import { Link } from "expo-router";
import { useAuth } from "../../hooks/useAuth";
import { Colors } from "../../constants/theme";

function aplicarMascaraCNPJ(valor: string): string {
  const numeros = valor.replace(/\D/g, "").slice(0, 14);
  return numeros
    .replace(/^(\d{2})(\d)/, "$1.$2")
    .replace(/^(\d{2})\.(\d{3})(\d)/, "$1.$2.$3")
    .replace(/\.(\d{3})(\d)/, ".$1/$2")
    .replace(/(\d{4})(\d)/, "$1-$2");
}

export default function RegisterScreen() {
  const { registrar } = useAuth();
  const [nome, setNome] = useState("");
  const [email, setEmail] = useState("");
  const [cnpj, setCnpj] = useState("");
  const [senha, setSenha] = useState("");
  const [carregando, setCarregando] = useState(false);

  function handleCnpjChange(valor: string) {
    setCnpj(aplicarMascaraCNPJ(valor));
  }

  async function handleRegistrar() {
    if (!nome || !email || !cnpj || !senha) {
      Alert.alert("Erro", "Preencha todos os campos.");
      return;
    }
    if (senha.length < 8) {
      Alert.alert("Erro", "A senha deve ter pelo menos 8 caracteres.");
      return;
    }
    setCarregando(true);
    try {
      await registrar(nome.trim(), email.trim().toLowerCase(), cnpj, senha);
    } catch (e: any) {
      const mensagem = e?.response?.data?.detail ?? "Erro ao criar conta.";
      Alert.alert("Erro no cadastro", mensagem);
    } finally {
      setCarregando(false);
    }
  }

  return (
    <KeyboardAvoidingView
      style={styles.container}
      behavior={Platform.OS === "ios" ? "padding" : undefined}
    >
      <ScrollView contentContainerStyle={styles.scroll} keyboardShouldPersistTaps="handled">
        <View style={styles.card}>
          <Text style={styles.titulo}>Criar conta</Text>
          <Text style={styles.subtitulo}>Cadastre seu MEI</Text>

          <TextInput
            style={styles.input}
            placeholder="Nome completo"
            value={nome}
            onChangeText={setNome}
            autoCapitalize="words"
            placeholderTextColor={Colors.textSecondary}
          />

          <TextInput
            style={styles.input}
            placeholder="E-mail"
            value={email}
            onChangeText={setEmail}
            keyboardType="email-address"
            autoCapitalize="none"
            placeholderTextColor={Colors.textSecondary}
          />

          <TextInput
            style={styles.input}
            placeholder="CNPJ (00.000.000/0000-00)"
            value={cnpj}
            onChangeText={handleCnpjChange}
            keyboardType="numeric"
            placeholderTextColor={Colors.textSecondary}
          />

          <TextInput
            style={styles.input}
            placeholder="Senha (mín. 8 caracteres)"
            value={senha}
            onChangeText={setSenha}
            secureTextEntry
            placeholderTextColor={Colors.textSecondary}
          />

          <TouchableOpacity
            style={[styles.botao, carregando && styles.botaoDesabilitado]}
            onPress={handleRegistrar}
            disabled={carregando}
          >
            {carregando ? (
              <ActivityIndicator color="#fff" />
            ) : (
              <Text style={styles.botaoTexto}>Cadastrar</Text>
            )}
          </TouchableOpacity>

          <Link href="/(auth)/login" asChild>
            <TouchableOpacity style={styles.linkContainer}>
              <Text style={styles.link}>Já tem conta? Entre aqui</Text>
            </TouchableOpacity>
          </Link>
        </View>
      </ScrollView>
    </KeyboardAvoidingView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: Colors.background,
  },
  scroll: {
    flexGrow: 1,
    justifyContent: "center",
    padding: 24,
  },
  card: {
    backgroundColor: Colors.card,
    borderRadius: 12,
    padding: 24,
    shadowColor: "#000",
    shadowOpacity: 0.08,
    shadowRadius: 8,
    elevation: 3,
  },
  titulo: {
    fontSize: 26,
    fontWeight: "700",
    color: Colors.primary,
    textAlign: "center",
    marginBottom: 4,
  },
  subtitulo: {
    fontSize: 15,
    color: Colors.textSecondary,
    textAlign: "center",
    marginBottom: 24,
  },
  input: {
    borderWidth: 1,
    borderColor: Colors.border,
    borderRadius: 8,
    padding: 12,
    fontSize: 15,
    color: Colors.text,
    marginBottom: 14,
  },
  botao: {
    backgroundColor: Colors.primary,
    borderRadius: 8,
    padding: 14,
    alignItems: "center",
    marginTop: 4,
  },
  botaoDesabilitado: {
    opacity: 0.6,
  },
  botaoTexto: {
    color: "#fff",
    fontWeight: "700",
    fontSize: 16,
  },
  linkContainer: {
    marginTop: 18,
    alignItems: "center",
  },
  link: {
    color: Colors.primary,
    fontSize: 14,
  },
});
