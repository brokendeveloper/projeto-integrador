import { Slot, useSegments, useRouter } from "expo-router";
import { useEffect } from "react";
import { AuthProvider, useAuth } from "../context/AuthContext";

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

  return <Slot />;
}

export default function RootLayout() {
  return (
    <AuthProvider>
      <RootNavigation />
    </AuthProvider>
  );
}
