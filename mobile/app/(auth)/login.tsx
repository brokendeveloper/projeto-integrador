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
  Dimensions,
  StatusBar,
  ScrollView,
} from "react-native";
import { Link } from "expo-router";
import { useAuth } from "../../hooks/useAuth";
import { Colors, Radius, Spacing } from "../../constants/theme";

const { height: SCREEN_HEIGHT } = Dimensions.get("window");
const HERO_HEIGHT = Math.round(SCREEN_HEIGHT * 0.4);

export default function LoginScreen() {
  const { login } = useAuth();
  const [email, setEmail] = useState("");
  const [senha, setSenha] = useState("");
  const [carregando, setCarregando] = useState(false);

  async function handleLogin() {
    if (!email || !senha) {
      Alert.alert("Campos obrigatórios", "Preencha e-mail e senha.");
      return;
    }
    setCarregando(true);
    try {
      await login(email.trim().toLowerCase(), senha);
    } catch (e: any) {
      const mensagem = e?.response?.data?.detail ?? "Credenciais inválidas.";
      Alert.alert("Não foi possível entrar", mensagem);
    } finally {
      setCarregando(false);
    }
  }

  return (
    <KeyboardAvoidingView
      style={styles.container}
      behavior={Platform.OS === "ios" ? "padding" : "height"}
    >
      <StatusBar barStyle="light-content" backgroundColor={Colors.primaryDark} />

      <ScrollView
        style={{ flex: 1 }}
        contentContainerStyle={{ flexGrow: 1 }}
        keyboardShouldPersistTaps="handled"
        bounces={false}
      >
        {/* Hero */}
        <View style={[styles.hero, { minHeight: HERO_HEIGHT }]}>
          <View style={styles.circle1} />
          <View style={styles.circle2} />
          <View style={styles.circle3} />
          <View style={styles.heroContent}>
            <Text style={styles.brand}>LicitaME</Text>
            <Text style={styles.tagline}>Licitações públicas para o seu MEI</Text>
          </View>
        </View>

        {/* Form */}
        <View style={styles.form}>
          <Text style={styles.titulo}>Entrar na conta</Text>

          <Text style={styles.label}>E-mail</Text>
          <TextInput
            style={styles.input}
            placeholder="seu@email.com"
            value={email}
            onChangeText={setEmail}
            keyboardType="email-address"
            autoCapitalize="none"
            autoComplete="email"
            placeholderTextColor={Colors.textLight}
          />

          <Text style={styles.label}>Senha</Text>
          <TextInput
            style={styles.input}
            placeholder="••••••••"
            value={senha}
            onChangeText={setSenha}
            secureTextEntry
            placeholderTextColor={Colors.textLight}
          />

          <TouchableOpacity
            style={[styles.botao, carregando && styles.botaoDesabilitado]}
            onPress={handleLogin}
            disabled={carregando}
            activeOpacity={0.85}
          >
            {carregando ? (
              <ActivityIndicator color={Colors.white} />
            ) : (
              <Text style={styles.botaoTexto}>Entrar</Text>
            )}
          </TouchableOpacity>

          <Link href="/(auth)/register" asChild>
            <TouchableOpacity style={styles.linkContainer} activeOpacity={0.7}>
              <Text style={styles.linkTexto}>
                Não tem conta?{" "}
                <Text style={styles.linkDestaque}>Cadastre-se grátis</Text>
              </Text>
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
    backgroundColor: Colors.primaryDark,
  },
  hero: {
    backgroundColor: Colors.primaryDark,
    justifyContent: "flex-end",
    paddingBottom: 40,
    overflow: "hidden",
  },
  circle1: {
    position: "absolute",
    width: 300,
    height: 300,
    borderRadius: 150,
    backgroundColor: "rgba(255,255,255,0.05)",
    top: -90,
    right: -70,
  },
  circle2: {
    position: "absolute",
    width: 220,
    height: 220,
    borderRadius: 110,
    backgroundColor: "rgba(255,255,255,0.06)",
    top: 10,
    left: -60,
  },
  circle3: {
    position: "absolute",
    width: 130,
    height: 130,
    borderRadius: 65,
    backgroundColor: "rgba(59,130,246,0.25)",
    bottom: 60,
    right: 40,
  },
  heroContent: {
    paddingHorizontal: Spacing.xl,
  },
  brand: {
    fontSize: 44,
    fontWeight: "800",
    color: Colors.white,
    letterSpacing: -1,
  },
  tagline: {
    fontSize: 15,
    color: "rgba(255,255,255,0.60)",
    marginTop: 6,
    fontWeight: "400",
    letterSpacing: 0.1,
  },
  form: {
    flex: 1,
    backgroundColor: Colors.white,
    borderTopLeftRadius: 28,
    borderTopRightRadius: 28,
    paddingHorizontal: Spacing.xl,
    paddingTop: 28,
    paddingBottom: Spacing.xxl,
    minHeight: SCREEN_HEIGHT * 0.6,
  },
  titulo: {
    fontSize: 20,
    fontWeight: "700",
    color: Colors.text,
    marginBottom: 24,
  },
  label: {
    fontSize: 13,
    fontWeight: "600",
    color: Colors.textSecondary,
    marginBottom: 6,
    letterSpacing: 0.1,
  },
  input: {
    height: 50,
    borderWidth: 1.5,
    borderColor: Colors.border,
    borderRadius: Radius.md,
    paddingHorizontal: Spacing.md,
    fontSize: 15,
    color: Colors.text,
    backgroundColor: Colors.surface,
    marginBottom: 16,
  },
  botao: {
    height: 52,
    backgroundColor: Colors.primary,
    borderRadius: Radius.md,
    alignItems: "center",
    justifyContent: "center",
    marginTop: 8,
    shadowColor: Colors.primary,
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.3,
    shadowRadius: 8,
    elevation: 4,
  },
  botaoDesabilitado: {
    opacity: 0.65,
    shadowOpacity: 0,
    elevation: 0,
  },
  botaoTexto: {
    color: Colors.white,
    fontWeight: "700",
    fontSize: 16,
    letterSpacing: 0.3,
  },
  linkContainer: {
    marginTop: 22,
    alignItems: "center",
  },
  linkTexto: {
    fontSize: 14,
    color: Colors.textSecondary,
  },
  linkDestaque: {
    color: Colors.primary,
    fontWeight: "700",
  },
});
