### Cálculo da Tabela de Benefícios
- Cada requisição possui uma latência máxima desejada e um uplink mínimo desejado
- Cada fog possui um valor de latência e um uplink


O cálculo da benefício requisição x fog é feito da seguinte forma:

```py
diferença_latência = latência_request - latência_fog
diferença_uplink = uplink_fog - uplink_request

benefício = diferença_latência + diferença_uplink
```

Veja que o valor do benefício pode ser negativo, o que não é permitido no algoritmo de leilão. Dessa forma, caso haja valor negativo, é feita uma correção na tabela de benefícios onde cada valor da tabela é somado ao módulo do menor valor negativo de benefício.