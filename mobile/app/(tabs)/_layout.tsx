import { Tabs } from "expo-router";
import { Text } from "react-native";
import { Colors } from "../../constants/theme";

function IconTab({ emoji }: { emoji: string }) {
  return <Text style={{ fontSize: 20 }}>{emoji}</Text>;
}

export default function TabsLayout() {
  return (
    <Tabs
      screenOptions={{
        tabBarActiveTintColor: Colors.primary,
        tabBarInactiveTintColor: Colors.textSecondary,
        tabBarStyle: { borderTopColor: Colors.border },
        headerStyle: { backgroundColor: Colors.primary },
        headerTintColor: "#fff",
        headerTitleStyle: { fontWeight: "700" },
      }}
    >
      <Tabs.Screen
        name="index"
        options={{
          title: "Editais",
          tabBarIcon: ({ focused }) => (
            <IconTab emoji={focused ? "📋" : "📄"} />
          ),
        }}
      />
      <Tabs.Screen
        name="checklist"
        options={{
          title: "Checklist",
          tabBarIcon: ({ focused }) => (
            <IconTab emoji={focused ? "✅" : "☑️"} />
          ),
        }}
      />
      <Tabs.Screen
        name="documentos"
        options={{
          title: "Documentos",
          tabBarIcon: ({ focused }) => (
            <IconTab emoji={focused ? "📁" : "🗂️"} />
          ),
        }}
      />
      <Tabs.Screen
        name="alertas"
        options={{
          title: "Alertas",
          tabBarIcon: ({ focused }) => (
            <IconTab emoji={focused ? "🔔" : "🔕"} />
          ),
        }}
      />
      <Tabs.Screen
        name="historico"
        options={{
          title: "Histórico",
          tabBarIcon: ({ focused }) => (
            <IconTab emoji={focused ? "📊" : "📈"} />
          ),
        }}
      />
    </Tabs>
  );
}
