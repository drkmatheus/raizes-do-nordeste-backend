# Propostas futuras (nao implementadas)

---

## 1. Desconto / Promocoes

**Situacao atual.** O dominio ja expoe `Pedido.aplicarDesconto(valor)` e o campo
`valorDesconto`, mas nenhum fluxo de aplicacao chama esse metodo hoje — o desconto
e sempre `0`.

**Proposta.** Introduzir um fluxo de promocoes/cupons:

- Entidade `Promocao` (codigo, tipo percentual/fixo, validade, unidade/canal elegiveis).
- Endpoint para aplicar cupom a um pedido `AGUARDANDO_PAGAMENTO`, chamando
  `aplicarDesconto` e recalculando o total.
- Regras de acumulo (cupom + pontos de fidelidade) e limites.

**Por que nao agora.** Abre um fluxo de negocio novo (cadastro e validacao de
promocoes, regras de elegibilidade) que extrapola o escopo atual. O metodo de
dominio ja esta pronto para quando o fluxo for priorizado.

---

## 2. Estorno de pontos ao cancelar pedido pago

**Situacao atual.** O enum `TipoPontos.ESTORNO` existe mas nunca e referenciado.
Ao cancelar um pedido que ja havia sido pago e creditado pontos, o `_cancelar`
devolve o estoque mas **nao** estorna os pontos de fidelidade creditados.

**Proposta.** No cancelamento de um pedido que gerou credito:

- Localizar o `HistoricoFidelidade` de tipo `GANHO` vinculado ao pedido.
- Debitar os pontos correspondentes do saldo do cliente, gerando um lancamento
  `TipoPontos.ESTORNO`.
- Tratar saldo insuficiente (cliente ja resgatou os pontos): definir se o saldo
  pode ficar negativo ou se o estorno e parcial/bloqueado.

**Por que nao agora.** A regra de saldo negativo e de estorno parcial precisa de
decisao de negocio. O `CheckConstraint("saldo_pontos >= 0")` no modelo `Usuario`
impede saldo negativo hoje, entao o estorno exige politica explicita antes de
implementar.

---

## 3. Base legal do consentimento LGPD

**Situacao atual.** `consentimentoLgpd` tem default `False` e nao bloqueia o
cadastro. O consentimento declarado passou a ser **registrado em auditoria**
(`CONSENTIMENTO_REGISTRADO`), mas o cadastro nao e barrado por ele.

**Proposta / base legal sugerida.**

- **Cadastro e operacao do pedido:** base legal de _execucao de contrato_
  (LGPD Art. 7, V) — nao exige consentimento explicito para processar o pedido.
- **Programa de fidelidade:** base legal de _consentimento_ (Art. 7, I) — por isso
  `consentimentoFidelidade` ja e pre-condicao para acumular/resgatar pontos no
  codigo (`Usuario.acumularPontos` / `resgatarPontos`).

**Por que nao bloquear o cadastro.** Exigir `consentimentoLgpd=True` para cadastrar
mudaria a UX e nao e necessario sob a base de execucao de contrato. Recomendacao:
manter como esta e, se o roteiro exigir, adicionar validacao no
`UsuarioService.criar`.

---
