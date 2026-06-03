import { useState } from "react";
import { Tabs } from "expo-router";
import { TouchableOpacity } from "react-native";
import { Ionicons } from "@expo/vector-icons";
import { useAuth } from "../../hooks/useAuth";
import { SideMenu } from "../../components/SideMenu";
import { Colors } from "../../constants/theme";

export default function TabsLayout() {
  const { logout } = useAuth();
  const [menuAberto, setMenuAberto] = useState(false);

  function hamburger() {
    return (
      <TouchableOpacity
        onPress={() => setMenuAberto(true)}
        style={{ marginLeft: 16, padding: 4 }}
        hitSlop={{ top: 8, bottom: 8, left: 8, right: 8 }}
      >
        <Ionicons name="menu" size={24} color={Colors.white} />
      </TouchableOpacity>
    );
  }

  return (
    <>
      <Tabs
        screenOptions={{
          tabBarActiveTintColor: Colors.primary,
          tabBarInactiveTintColor: Colors.textLight,
          tabBarStyle: {
            backgroundColor: Colors.white,
            borderTopColor: Colors.border,
            borderTopWidth: 1,
            height: 60,
            paddingBottom: 8,
            paddingTop: 4,
          },
          tabBarLabelStyle: { fontSize: 11, fontWeight: "600" },
          headerStyle: { backgroundColor: Colors.primaryDark },
          headerTintColor: Colors.white,
          headerTitleStyle: { fontWeight: "700", fontSize: 17 },
          headerLeft: hamburger,
        }}
      >
        <Tabs.Screen
          name="index"
          options={{
            title: "Editais",
            tabBarIcon: ({ focused, color }) => (
              <Ionicons
                name={focused ? "document-text" : "document-text-outline"}
                size={22}
                color={color}
              />
            ),
          }}
        />
        <Tabs.Screen
          name="checklist"
          options={{
            title: "Checklist",
            tabBarIcon: ({ focused, color }) => (
              <Ionicons
                name={focused ? "checkbox" : "checkbox-outline"}
                size={22}
                color={color}
              />
            ),
          }}
        />
        <Tabs.Screen
          name="documentos"
          options={{
            title: "Documentos",
            tabBarIcon: ({ focused, color }) => (
              <Ionicons
                name={focused ? "folder" : "folder-outline"}
                size={22}
                color={color}
              />
            ),
          }}
        />
        <Tabs.Screen
          name="alertas"
          options={{
            title: "Alertas",
            tabBarIcon: ({ focused, color }) => (
              <Ionicons
                name={focused ? "notifications" : "notifications-outline"}
                size={22}
                color={color}
              />
            ),
          }}
        />
        <Tabs.Screen
          name="historico"
          options={{
            title: "Histórico",
            tabBarIcon: ({ focused, color }) => (
              <Ionicons
                name={focused ? "stats-chart" : "stats-chart-outline"}
                size={22}
                color={color}
              />
            ),
          }}
        />
      </Tabs>

      <SideMenu
        visivel={menuAberto}
        onFechar={() => setMenuAberto(false)}
        onLogout={logout}
      />
    </>
  );
}
