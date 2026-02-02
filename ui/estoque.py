df = qdf("""
SELECT
    p.id AS product_id,
    p.categoria,
    p.produto,
    COALESCE(m.estoque, 0) AS estoque
FROM products p
LEFT JOIN movimentos m
  ON m.product_id = p.id
 AND m.filial_id = :f
 AND m.data = :d
WHERE p.ativo = TRUE
ORDER BY p.categoria, p.produto;
""", {"f": filial_id, "d": data})
