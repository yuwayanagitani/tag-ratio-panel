# Tag Ratio Panel

## ui_target
- "main": メイン画面（Deck Browser）にパネルを差し込み
- "dialog": ダイアログのみ

## search_scope
Anki標準検索クエリで母集団を指定（例: deck:医学 -is:suspended）

## tags
対象タグ（複数）

## tag_mode
- "OR": いずれかのタグを含む
- "AND": すべてのタグを含む

## min_cards
分母（そのデッキの対象カード数）がこれ未満なら非表示

## max_rows
表示するデッキ行数の上限（多いときの抑制）

## pct_bands
パーセント帯→色の対応。

- 判定: min <= pct < max
- 例:
[
  {"min":0,"max":40,"color":"#e53935"},
  {"min":40,"max":70,"color":"#fb8c00"},
  {"min":70,"max":90,"color":"#43a047"},
  {"min":90,"max":101,"color":"#1e88e5"}
]
