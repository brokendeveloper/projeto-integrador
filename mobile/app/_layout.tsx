import { Stack, useSegments, useRouter } from "expo-router";
import { useEffect } from "react";
import { AuthProvider, useAuth } from "../context/AuthContext";
import { Colors } from "../constants/theme";

const HEADER_DARK = {
  headerStyle: { backgroundColor: Colors.primaryDark },
  headerTintColor: Colors.white,
  headerTitleStyle: { fontWeight: "700" as const, fontSize: 17 },
};

function RootNavigation() {
  const { autenticado } = useAuth();
  const segments = useSegments();
  const router = useRouter();

  useEffect(() => {
    if (autenticado === null) return; // ainda carregando

    const inAuthGroup = segments[0] === "(auth)";

    if (!autenticado && !inAuthGroup) {
      router.replace("/(auth)/login");
    } else if (autenticado && inAuthGroup) {
      router.replace("/(tabs)");
    }
  }, [autenticado, segments]);

  return (
    <Stack>
      <Stack.Screen name="(auth)" options={{ headerShown: false }} />
      <Stack.Screen name="(tabs)" options={{ headerShown: false }} />
      <Stack.Screen
        name="perfil"
        options={{ title: "Editar Perfil", ...HEADER_DARK }}
      />
      <Stack.Screen
        name="configuracoes"
        options={{ title: "Configurações", ...HEADER_DARK }}
      />
      <Stack.Screen
        name="premium"
        options={{ title: "Plano Premium", ...HEADER_DARK }}
      />
      <Stack.Screen
        name="ajuda"
        options={{ title: "Ajuda & Suporte", ...HEADER_DARK }}
      />
      <Stack.Screen
        name="edital/[id]"
        options={{ headerShown: false }}
      />
    </Stack>
  );
}

export default function RootLayout() {
  return (
    <AuthProvider>
      <RootNavigation />
    </AuthProvider>
  );
}
