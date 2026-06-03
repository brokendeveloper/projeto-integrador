import { useState } from "react";
import {
  View,
  Text,
  TouchableOpacity,
  StyleSheet,
  ScrollView,
  Linking,
} from "react-native";
import { Ionicons } from "@expo/vector-icons";
import { Colors, Radius, Spacing, Shadow } from "../constants/theme";

const FAQ = [
  {
    pergunta: "O que é o LicitaME?",
    resposta:
      "O LicitaME é uma plataforma que ajuda Microempreendedores Individuais (MEIs) a descobrir, acompanhar e participar de licitações públicas no Brasil, integrando dados em tempo real do PNCP (Portal Nacional de Contratações Públicas).",
  },
  {
    pergunta: "O que é um edital favorável ao MEI?",
    resposta:
      "Editais com valor estimado até R$ 80.000 são considerados favoráveis ao MEI, pois a Lei Complementar 123/2006 (Art. 48) garante tratamento diferenciado e preferência na contratação para MEIs e microempresas nesses valores.",
  },
  {
    pergunta: "Como funciona o checklist de habilitação?",
    resposta:
      "O checklist é baseado na Lei 14.133/2021 (Nova Lei de Licitações) e lista os documentos e requisitos necessários para habilitar seu MEI em um edital específico. Informe o ID do edital para ver o checklist personalizado.",
  },
  {
    pergunta: "Quantos alertas posso criar no plano gratuito?",
    resposta:
      "No plano gratuito você pode criar até 3 alertas. Cada alerta monitora novos editais com os filtros que você definiu (CNAE, valor máximo, UF). O plano Premium oferece alertas ilimitados.",
  },
  {
    pergunta: "Como encontro o ID de um edital?",
    resposta:
      "O ID do edital aparece na listagem de editais ao lado do número de controle PNCP. É o identificador interno usado para acessar o checklist e gerenciar documentos.",
  },
  {
    pergunta: "Meus dados estão seguros?",
    resposta:
      "Sim. O LicitaME segue a LGPD (Lei 13.709/2018). Suas senhas são criptografadas com bcrypt e seus dados podem ser exportados ou excluídos a qualquer momento via solicitação.",
  },
];

function FaqItem({ pergunta, resposta }: { pergunta: string; resposta: string }) {
  const [aberto, setAberto] = useState(false);
  return (
    <View style={styles.faqItem}>
      <TouchableOpacity
        style={styles.faqPergunta}
        onPress={() => setAberto(!aberto)}
        activeOpacity={0.7}
      >
        <Text style={styles.faqPerguntaTexto}>{pergunta}</Text>
        <Ionicons
          name={aberto ? "chevron-up" : "chevron-down"}
          size={18}
          color={Colors.textSecondary}
        />
      </TouchableOpacity>
      {aberto && (
        <Text style={styles.faqResposta}>{resposta}</Text>
      )}
    </View>
  );
}

export default function AjudaScreen() {
  return (
    <ScrollView style={styles.container} contentContainerStyle={styles.content}>
      {/* Base legal */}
      <View style={styles.secao}>
        <Text style={styles.secaoTitulo}>Base Legal</Text>
        {[
          { label: "Lei 14.133/2021", desc: "Nova Lei de Licitações" },
          { label: "LC 123/2006 Art. 48", desc: "Preferência a MEI/ME/EPP" },
          { label: "LGPD — Lei 13.709/2018", desc: "Proteção de dados pessoais" },
        ].map((item, i) => (
          <View key={i} style={[styles.infoRow, i > 0 && styles.infoRowBorder]}>
            <View style={styles.legalIcone}>
              <Ionicons name="document-text-outline" size={16} color={Colors.primary} />
            </View>
            <View>
              <Text style={styles.legalLabel}>{item.label}</Text>
              <Text style={styles.legalDesc}>{item.desc}</Text>
            </View>
          </View>
        ))}
      </View>

      {/* FAQ */}
      <View style={styles.secao}>
        <Text style={styles.secaoTitulo}>Perguntas Frequentes</Text>
        {FAQ.map((item, i) => (
          <FaqItem key={i} pergunta={item.pergunta} resposta={item.resposta} />
        ))}
      </View>

      {/* Contato */}
      <View style={styles.secao}>
        <Text style={styles.secaoTitulo}>Contato & Suporte</Text>
        <TouchableOpacity
          style={styles.contatoItem}
          onPress={() => Linking.openURL("mailto:contato@licitame.com.br")}
          activeOpacity={0.7}
        >
          <View style={styles.contatoIcone}>
            <Ionicons name="mail-outline" size={20} color={Colors.primary} />
          </View>
          <View>
            <Text style={styles.contatoLabel}>E-mail</Text>
            <Text style={styles.contatoValor}>contato@licitame.com.br</Text>
          </View>
          <Ionicons name="open-outline" size={14} color={Colors.textLight} style={{ marginLeft: "auto" }} />
        </TouchableOpacity>
      </View>

      {/* Versão */}
      <Text style={styles.versao}>LicitaME v1.0.0 — Todos os direitos reservados</Text>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: Colors.background,
  },
  content: {
    padding: Spacing.md,
    paddingBottom: 48,
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
  infoRow: {
    flexDirection: "row",
    alignItems: "center",
    gap: Spacing.md,
    paddingVertical: Spacing.sm,
  },
  infoRowBorder: {
    borderTopWidth: 1,
    borderTopColor: Colors.borderLight,
  },
  legalIcone: {
    width: 32,
    height: 32,
    borderRadius: Radius.sm,
    backgroundColor: Colors.primaryLight,
    alignItems: "center",
    justifyContent: "center",
  },
  legalLabel: {
    fontSize: 13,
    fontWeight: "600",
    color: Colors.text,
  },
  legalDesc: {
    fontSize: 11,
    color: Colors.textSecondary,
    marginTop: 1,
  },
  faqItem: {
    borderTopWidth: 1,
    borderTopColor: Colors.borderLight,
    paddingVertical: Spacing.md,
  },
  faqPergunta: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "space-between",
  },
  faqPerguntaTexto: {
    flex: 1,
    fontSize: 14,
    fontWeight: "600",
    color: Colors.text,
    paddingRight: Spacing.sm,
  },
  faqResposta: {
    fontSize: 13,
    color: Colors.textSecondary,
    lineHeight: 20,
    marginTop: Spacing.sm,
  },
  contatoItem: {
    flexDirection: "row",
    alignItems: "center",
    gap: Spacing.md,
    paddingVertical: Spacing.sm,
  },
  contatoIcone: {
    width: 38,
    height: 38,
    borderRadius: Radius.sm,
    backgroundColor: Colors.primaryLight,
    alignItems: "center",
    justifyContent: "center",
  },
  contatoLabel: {
    fontSize: 11,
    color: Colors.textSecondary,
    fontWeight: "600",
  },
  contatoValor: {
    fontSize: 14,
    color: Colors.primary,
    fontWeight: "500",
  },
  versao: {
    fontSize: 11,
    color: Colors.textLight,
    textAlign: "center",
    marginTop: Spacing.sm,
  },
});
