import React, { useEffect, useRef } from "react";
import {
  View,
  Text,
  TouchableOpacity,
  StyleSheet,
  Animated,
  Dimensions,
  TouchableWithoutFeedback,
  Alert,
  Modal,
} from "react-native";
import { Ionicons } from "@expo/vector-icons";
import { Colors, Radius, Spacing } from "../constants/theme";

const SCREEN_WIDTH = Dimensions.get("window").width;
const MENU_WIDTH = Math.round(SCREEN_WIDTH * 0.78);

interface SideMenuProps {
  visivel: boolean;
  onFechar: () => void;
  onLogout: () => void;
}

interface ItemMenu {
  icone: string;
  label: string;
  descricao: string;
  onPress: () => void;
  destaque?: string;
}

export function SideMenu({ visivel, onFechar, onLogout }: SideMenuProps) {
  const translateX = useRef(new Animated.Value(-MENU_WIDTH)).current;
  const opacidade = useRef(new Animated.Value(0)).current;

  useEffect(() => {
    if (visivel) {
      translateX.setValue(-MENU_WIDTH);
      opacidade.setValue(0);
      Animated.parallel([
        Animated.spring(translateX, {
          toValue: 0,
          useNativeDriver: true,
          tension: 70,
          friction: 11,
        }),
        Animated.timing(opacidade, {
          toValue: 1,
          duration: 220,
          useNativeDriver: true,
        }),
      ]).start();
    } else {
      Animated.parallel([
        Animated.timing(translateX, {
          toValue: -MENU_WIDTH,
          duration: 220,
          useNativeDriver: true,
        }),
        Animated.timing(opacidade, {
          toValue: 0,
          duration: 180,
          useNativeDriver: true,
        }),
      ]).start();
    }
  }, [visivel]);

  const itens: ItemMenu[] = [
    {
      icone: "person-circle-outline",
      label: "Editar Perfil",
      descricao: "Nome, e-mail e CNPJ",
      onPress: () =>
        Alert.alert("Em breve", "Edição de perfil estará disponível na próxima versão."),
    },
    {
      icone: "settings-outline",
      label: "Configurações",
      descricao: "Notificações e preferências",
      onPress: () =>
        Alert.alert("Em breve", "Configurações estarão disponíveis na próxima versão."),
    },
    {
      icone: "diamond-outline",
      label: "Plano Premium",
      descricao: "Alertas ilimitados + checklist avançado",
      onPress: () =>
        Alert.alert(
          "LicitaME Premium",
          "Com o plano Premium você acessa alertas ilimitados, checklist completo e suporte prioritário."
        ),
      destaque: Colors.premium,
    },
    {
      icone: "help-circle-outline",
      label: "Ajuda & Suporte",
      descricao: "Dúvidas e central de ajuda",
      onPress: () =>
        Alert.alert("Suporte", "Acesse nossa documentação em licita.me/ajuda"),
    },
  ];

  function handleItemPress(item: ItemMenu) {
    onFechar();
    setTimeout(item.onPress, 280);
  }

  function handleLogout() {
    onFechar();
    setTimeout(onLogout, 280);
  }

  return (
    <Modal
      visible={visivel}
      transparent
      animationType="none"
      statusBarTranslucent
      onRequestClose={onFechar}
    >
      <View style={styles.root}>
        {/* Overlay escurecido */}
        <TouchableWithoutFeedback onPress={onFechar}>
          <Animated.View style={[styles.overlay, { opacity: opacidade }]} />
        </TouchableWithoutFeedback>

        {/* Painel do menu */}
        <Animated.View
          style={[styles.painel, { transform: [{ translateX }] }]}
        >
          {/* Cabeçalho */}
          <View style={styles.cabecalho}>
            <View style={styles.avatar}>
              <Ionicons name="person" size={30} color={Colors.white} />
            </View>
            <Text style={styles.cabecalhoNome}>Minha Conta</Text>
            <Text style={styles.cabecalhoApp}>LicitaME</Text>
          </View>

          {/* Itens */}
          <View style={styles.itensContainer}>
            {itens.map((item, index) => (
              <TouchableOpacity
                key={index}
                style={styles.item}
                onPress={() => handleItemPress(item)}
                activeOpacity={0.65}
              >
                <View
                  style={[
                    styles.itemIcone,
                    item.destaque && { backgroundColor: item.destaque + "18" },
                  ]}
                >
                  <Ionicons
                    name={item.icone as any}
                    size={20}
                    color={item.destaque ?? Colors.textSecondary}
                  />
                </View>
                <View style={styles.itemTextos}>
                  <Text
                    style={[
                      styles.itemLabel,
                      item.destaque && { color: item.destaque },
                    ]}
                  >
                    {item.label}
                  </Text>
                  <Text style={styles.itemDescricao}>{item.descricao}</Text>
                </View>
                <Ionicons
                  name="chevron-forward"
                  size={16}
                  color={Colors.borderLight}
                />
              </TouchableOpacity>
            ))}
          </View>

          {/* Separador */}
          <View style={styles.separador} />

          {/* Sair */}
          <TouchableOpacity
            style={styles.item}
            onPress={handleLogout}
            activeOpacity={0.65}
          >
            <View style={[styles.itemIcone, styles.itemIconeSair]}>
              <Ionicons name="log-out-outline" size={20} color={Colors.danger} />
            </View>
            <View style={styles.itemTextos}>
              <Text style={[styles.itemLabel, { color: Colors.danger }]}>Sair</Text>
              <Text style={styles.itemDescricao}>Encerrar sessão</Text>
            </View>
          </TouchableOpacity>

          {/* Rodapé */}
          <View style={styles.rodape}>
            <Text style={styles.rodapeTexto}>LicitaME v1.0.0</Text>
            <Text style={styles.rodapeTexto}>© 2025 LicitaME</Text>
          </View>
        </Animated.View>
      </View>
    </Modal>
  );
}

const styles = StyleSheet.create({
  root: {
    flex: 1,
    flexDirection: "row",
  },
  overlay: {
    ...StyleSheet.absoluteFillObject,
    backgroundColor: "rgba(15, 23, 42, 0.55)",
  },
  painel: {
    width: MENU_WIDTH,
    height: "100%",
    backgroundColor: Colors.white,
    shadowColor: "#000",
    shadowOffset: { width: 4, height: 0 },
    shadowOpacity: 0.15,
    shadowRadius: 16,
    elevation: 16,
  },
  cabecalho: {
    backgroundColor: Colors.primaryDark,
    paddingTop: 56,
    paddingBottom: Spacing.xl,
    paddingHorizontal: Spacing.xl,
  },
  avatar: {
    width: 60,
    height: 60,
    borderRadius: 30,
    backgroundColor: "rgba(255,255,255,0.15)",
    alignItems: "center",
    justifyContent: "center",
    marginBottom: Spacing.md,
  },
  cabecalhoNome: {
    fontSize: 18,
    fontWeight: "700",
    color: Colors.white,
  },
  cabecalhoApp: {
    fontSize: 13,
    color: "rgba(255,255,255,0.55)",
    marginTop: 2,
  },
  itensContainer: {
    paddingTop: Spacing.sm,
  },
  item: {
    flexDirection: "row",
    alignItems: "center",
    paddingHorizontal: Spacing.xl,
    paddingVertical: Spacing.md,
    gap: Spacing.md,
  },
  itemIcone: {
    width: 38,
    height: 38,
    borderRadius: Radius.sm,
    backgroundColor: Colors.surface,
    alignItems: "center",
    justifyContent: "center",
  },
  itemIconeSair: {
    backgroundColor: Colors.dangerLight,
  },
  itemTextos: {
    flex: 1,
  },
  itemLabel: {
    fontSize: 14,
    fontWeight: "600",
    color: Colors.text,
    marginBottom: 1,
  },
  itemDescricao: {
    fontSize: 11,
    color: Colors.textLight,
  },
  separador: {
    height: 1,
    backgroundColor: Colors.borderLight,
    marginHorizontal: Spacing.xl,
    marginVertical: Spacing.sm,
  },
  rodape: {
    position: "absolute",
    bottom: Spacing.xl,
    left: Spacing.xl,
    right: Spacing.xl,
  },
  rodapeTexto: {
    fontSize: 11,
    color: Colors.textLight,
    lineHeight: 18,
  },
});
