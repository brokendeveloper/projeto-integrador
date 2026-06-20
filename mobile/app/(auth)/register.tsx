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
const HERO_HEIGHT = Math.round(SCREEN_HEIGHT * 0.32);

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
  const [aceitouTermos, setAceitouTermos] = useState(false);

  function handleCnpjChange(valor: string) {
    setCnpj(aplicarMascaraCNPJ(valor));
  }

  async function handleRegistrar() {
    if (!nome || !email || !cnpj || !senha) {
      Alert.alert("Campos obrigatórios", "Preencha todos os campos.");
      return;
    }
    if (cnpj.replace(/\D/g, "").length !== 14) {
      Alert.alert("CNPJ inválido", "Digite um CNPJ completo com 14 dígitos.");
      return;
    }
    if (!aceitouTermos) {
      Alert.alert("Termos obrigatórios", "Você precisa aceitar os Termos de Uso para criar uma conta.");
      return;
    }
    if (senha.length < 8) {
      Alert.alert("Senha fraca", "A senha deve ter pelo menos 8 caracteres.");
      return;
    }
    setCarregando(true);
    try {
      await registrar(nome.trim(), email.trim().toLowerCase(), cnpj, senha);
    } catch (e: any) {
      const raw = e?.response?.data?.detail;
      const mensagem = typeof raw === "string"
        ? raw
        : Array.isArray(raw)
        ? raw.map((d: any) => d.msg ?? "Campo inválido").join("\n")
        : "Erro ao criar conta.";
      Alert.alert("Erro no cadastro", mensagem);
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
          <View style={styles.heroContent}>
            <Text style={styles.brand}>LicitaME</Text>
            <Text style={styles.tagline}>Crie sua conta de MEI gratuita</Text>
          </View>
        </View>

        {/* Form */}
        <View style={styles.form}>
          <Text style={styles.titulo}>Criar conta</Text>

          <Text style={styles.label}>Nome completo</Text>
          <TextInput
            style={styles.input}
            placeholder="Seu nome"
            value={nome}
            onChangeText={setNome}
            autoCapitalize="words"
            autoComplete="name"
            placeholderTextColor={Colors.textLight}
          />

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

          <Text style={styles.label}>CNPJ</Text>
          <TextInput
            style={styles.input}
            placeholder="00.000.000/0000-00"
            value={cnpj}
            onChangeText={handleCnpjChange}
            keyboardType="numeric"
            placeholderTextColor={Colors.textLight}
          />

          <Text style={styles.label}>Senha</Text>
          <TextInput
            style={styles.input}
            placeholder="Mínimo 8 caracteres"
            value={senha}
            onChangeText={setSenha}
            secureTextEntry
            placeholderTextColor={Colors.textLight}
          />

          <TouchableOpacity
            style={styles.checkboxRow}
            onPress={() => setAceitouTermos(v => !v)}
            activeOpacity={0.7}
          >
            <View style={[styles.checkbox, aceitouTermos && styles.checkboxMarcado]}>
              {aceitouTermos && <Text style={styles.checkboxTick}>✓</Text>}
            </View>
            <Text style={styles.checkboxTexto}>
              Li e aceito os{" "}
              <Text style={styles.checkboxLink}>Termos de Uso e Política de Privacidade</Text>
            </Text>
          </TouchableOpacity>

          <TouchableOpacity
            style={[styles.botao, carregando && styles.botaoDesabilitado]}
            onPress={handleRegistrar}
            disabled={carregando}
            activeOpacity={0.85}
          >
            {carregando ? (
              <ActivityIndicator color={Colors.white} />
            ) : (
              <Text style={styles.botaoTexto}>Criar conta grátis</Text>
            )}
          </TouchableOpacity>

          <Link href="/(auth)/login" asChild>
            <TouchableOpacity style={styles.linkContainer} activeOpacity={0.7}>
              <Text style={styles.linkTexto}>
                Já tem conta?{" "}
                <Text style={styles.linkDestaque}>Entre aqui</Text>
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
    paddingBottom: 36,
    overflow: "hidden",
  },
  circle1: {
    position: "absolute",
    width: 260,
    height: 260,
    borderRadius: 130,
    backgroundColor: "rgba(255,255,255,0.05)",
    top: -70,
    right: -60,
  },
  circle2: {
    position: "absolute",
    width: 180,
    height: 180,
    borderRadius: 90,
    backgroundColor: "rgba(59,130,246,0.2)",
    bottom: 30,
    right: 20,
  },
  heroContent: {
    paddingHorizontal: Spacing.xl,
  },
  brand: {
    fontSize: 38,
    fontWeight: "800",
    color: Colors.white,
    letterSpacing: -1,
  },
  tagline: {
    fontSize: 14,
    color: "rgba(255,255,255,0.60)",
    marginTop: 6,
    fontWeight: "400",
  },
  form: {
    flex: 1,
    backgroundColor: Colors.white,
    borderTopLeftRadius: 28,
    borderTopRightRadius: 28,
    paddingHorizontal: Spacing.xl,
    paddingTop: 28,
    paddingBottom: Spacing.xxl,
  },
  titulo: {
    fontSize: 20,
    fontWeight: "700",
    color: Colors.text,
    marginBottom: 20,
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
    marginBottom: 14,
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
    marginTop: 20,
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
  checkboxRow: {
    flexDirection: "row",
    alignItems: "flex-start",
    gap: 10,
    marginBottom: 14,
    marginTop: 4,
  },
  checkbox: {
    width: 20,
    height: 20,
    borderRadius: 4,
    borderWidth: 2,
    borderColor: Colors.border,
    alignItems: "center",
    justifyContent: "center",
    marginTop: 1,
    flexShrink: 0,
  },
  checkboxMarcado: {
    backgroundColor: Colors.primary,
    borderColor: Colors.primary,
  },
  checkboxTick: {
    color: Colors.white,
    fontSize: 12,
    fontWeight: "700",
    lineHeight: 14,
  },
  checkboxTexto: {
    flex: 1,
    fontSize: 13,
    color: Colors.textSecondary,
    lineHeight: 19,
  },
  checkboxLink: {
    color: Colors.primary,
    fontWeight: "600",
  },
});
