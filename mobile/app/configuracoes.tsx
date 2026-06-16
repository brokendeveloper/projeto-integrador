import { useState, useEffect } from "react";
import {
  View,
  Text,
  Switch,
  StyleSheet,
  ScrollView,
  ActivityIndicator,
  Alert,
} from "react-native";
import { api } from "../services/api";
import { Colors, Radius, Spacing, Shadow } from "../constants/theme";
import Constants from 'expo-constants';

interface Config {
  notificacoes_email: boolean;
  notificacoes_push: boolean;
  alertas_mei_apenas: boolean;
}

interface ToggleItemProps {
  label: string;
  descricao: string;
  valor: boolean;
  onChange: (v: boolean) => void;
  desabilitado?: boolean;
}

function ToggleItem({ label, descricao, valor, onChange, desabilitado }: ToggleItemProps) {
  return (
    <View style={styles.toggleItem}>
      <View style={styles.toggleTextos}>
        <Text style={[styles.toggleLabel, desabilitado && styles.textoDesabilitado]}>{label}</Text>
        <Text style={[styles.toggleDescricao, desabilitado && styles.textoDesabilitado]}>{descricao}</Text>
      </View>
      <Switch
        value={valor}
        onValueChange={onChange}
        disabled={desabilitado}
        trackColor={{ false: Colors.border, true: Colors.primaryMid }}
        thumbColor={valor ? Colors.primary : Colors.white}
      />
    </View>
  );
}

export default function ConfiguracoesScreen() {
  const [carregando, setCarregando] = useState(true);
  const [salvando, setSalvando] = useState(false);
  const [config, setConfig] = useState<Config>({
    notificacoes_email: true,
    notificacoes_push: true,
    alertas_mei_apenas: false,
  });

  useEffect(() => {
    api.get("/config").then(({ data }) => {
      setConfig(data);
    }).catch(() => {
      Alert.alert("Erro", "Não foi possível carregar as configurações.");
    }).finally(() => setCarregando(false));
  }, []);

  async function handleToggle(chave: keyof Config, valor: boolean) {
    const anterior = config[chave];
    setConfig((prev) => ({ ...prev, [chave]: valor }));
    setSalvando(true);
    try {
      await api.patch("/config", { [chave]: valor });
    } catch {
      setConfig((prev) => ({ ...prev, [chave]: anterior }));
      Alert.alert("Erro", "Não foi possível salvar a configuração.");
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
    <ScrollView style={styles.container} contentContainerStyle={styles.content}>
      {salvando && (
        <View style={styles.salvandoBanner}>
          <ActivityIndicator size="small" color={Colors.primary} />
          <Text style={styles.salvandoTexto}>  Salvando...</Text>
        </View>
      )}

      {/* Notificações */}
      <View style={styles.secao}>
        <Text style={styles.secaoTitulo}>Notificações</Text>

        <ToggleItem
          label="E-mail"
          descricao="Receba alertas de novos editais por e-mail"
          valor={config.notificacoes_email}
          onChange={(v) => handleToggle("notificacoes_email", v)}
        />
        <View style={styles.separador} />
        <ToggleItem
          label="Push"
          descricao="Notificações no dispositivo (em breve)"
          valor={config.notificacoes_push}
          onChange={(v) => handleToggle("notificacoes_push", v)}
        />
      </View>

      {/* Filtros */}
      <View style={styles.secao}>
        <Text style={styles.secaoTitulo}>Filtros padrão</Text>

        <ToggleItem
          label="Apenas editais favoráveis ao MEI"
          descricao="Mostrar só editais com valor ≤ R$ 80.000"
          valor={config.alertas_mei_apenas}
          onChange={(v) => handleToggle("alertas_mei_apenas", v)}
        />
      </View>

      {/* Conta */}
      <View style={styles.secao}>
        <Text style={styles.secaoTitulo}>Sobre o app</Text>
        <View style={styles.infoRow}>
          <Text style={styles.infoLabel}>Versão</Text>
          <Text style={styles.infoValor}>{Constants.expoConfig?.version ?? "1.0.0"}</Text>
        </View>
        <View style={styles.separador} />
        <View style={styles.infoRow}>
          <Text style={styles.infoLabel}>Ambiente</Text>
          <Text style={styles.infoValor}>Produção</Text>
        </View>
      </View>
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
  salvandoBanner: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "center",
    backgroundColor: Colors.primaryLight,
    borderRadius: Radius.md,
    padding: Spacing.sm,
    marginBottom: Spacing.md,
  },
  salvandoTexto: {
    fontSize: 13,
    color: Colors.primary,
    fontWeight: "600",
  },
  secao: {
    backgroundColor: Colors.white,
    borderRadius: Radius.lg,
    padding: Spacing.md,
    marginBottom: Spacing.md,
    ...Shadow.sm,
  },
  secaoTitulo: {
    fontSize: 13,
    fontWeight: "700",
    color: Colors.textSecondary,
    textTransform: "uppercase",
    letterSpacing: 0.8,
    marginBottom: Spacing.md,
  },
  toggleItem: {
    flexDirection: "row",
    alignItems: "center",
    paddingVertical: Spacing.sm,
  },
  toggleTextos: {
    flex: 1,
    marginRight: Spacing.md,
  },
  toggleLabel: {
    fontSize: 15,
    fontWeight: "500",
    color: Colors.text,
    marginBottom: 2,
  },
  toggleDescricao: {
    fontSize: 12,
    color: Colors.textSecondary,
  },
  textoDesabilitado: {
    color: Colors.textLight,
  },
  separador: {
    height: 1,
    backgroundColor: Colors.borderLight,
    marginVertical: 2,
  },
  infoRow: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "center",
    paddingVertical: Spacing.sm,
  },
  infoLabel: {
    fontSize: 15,
    color: Colors.text,
  },
  infoValor: {
    fontSize: 14,
    color: Colors.textSecondary,
    fontWeight: "500",
  },
});
