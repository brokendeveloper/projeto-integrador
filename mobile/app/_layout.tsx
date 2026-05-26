import { Slot, useSegments, useRouter } from "expo-router";
import { useEffect } from "react";
import { useAuth } from "../hooks/useAuth";

export default function RootLayout() {
  const { autenticado } = useAuth();
  const segments = useSegments();
  const router = useRouter();

  useEffect(() => {
    if (autenticado === null) return;

    const inAuthGroup = segments[0] === "(auth)";

    if (!autenticado && !inAuthGroup) {
      router.replace("/(auth)/login");
    } else if (autenticado && inAuthGroup) {
      router.replace("/(tabs)");
    }
  }, [autenticado, segments]);

  return <Slot />;
}
