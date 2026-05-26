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
} from "react-native";
import { Link } from "expo-router";
import { useAuth } from "../../hooks/useAuth";
import { Colors } from "../../constants/theme";

export default function LoginScreen() {
  const { login } = useAuth();
  const [email, setEmail] = useState("");
  const [senha, setSenha] = useState("");
  const [carregando, setCarregando] = useState(false);

  async function handleLogin() {
    if (!email || !senha) {
      Alert.alert("Erro", "Preencha e-mail e senha.");
      return;
    }
    setCarregando(true);
    try {
      await login(email.trim().toLowerCase(), senha);
    } catch (e: any) {
      const mensagem = e?.response?.data?.detail ?? "Credenciais inválidas.";
      Alert.alert("Erro ao entrar", mensagem);
    } finally {
      setCarregando(false);
    }
  }

  return (
    <KeyboardAvoidingView
      style={styles.container}
      behavior={Platform.OS === "ios" ? "padding" : undefined}
    >
      <View style={styles.card}>
        <Text style={styles.titulo}>MEI Licitações</Text>
        <Text style={styles.subtitulo}>Acesse sua conta</Text>

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
          placeholder="Senha"
          value={senha}
          onChangeText={setSenha}
          secureTextEntry
          placeholderTextColor={Colors.textSecondary}
        />

        <TouchableOpacity
          style={[styles.botao, carregando && styles.botaoDesabilitado]}
          onPress={handleLogin}
          disabled={carregando}
        >
          {carregando ? (
            <ActivityIndicator color="#fff" />
          ) : (
            <Text style={styles.botaoTexto}>Entrar</Text>
          )}
        </TouchableOpacity>

        <Link href="/(auth)/register" asChild>
          <TouchableOpacity style={styles.linkContainer}>
            <Text style={styles.link}>Não tem conta? Cadastre-se</Text>
          </TouchableOpacity>
        </Link>
      </View>
    </KeyboardAvoidingView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: Colors.background,
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
