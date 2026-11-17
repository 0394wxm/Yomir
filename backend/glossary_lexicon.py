# -*- coding: utf-8 -*-
"""
glossary_lexicon.py — 常用文语词词库（NIGHT8，200 条：词 / 读音 / 简明释义）。

来源（如实记录，不要夸大）:
  词条与释义由 agent 依据《广辞苑》《旺文社全訳古语辞典》级别的通识内容
  **整理归纳**而成（非逐字引用），覆盖 kanbun.info 语料中高频出现的
  接续词 / 副词 / 代名词 / 文语助动词 / 文语动词・形容词。
  **未经过人文专业人工校对** —— 上线给真用户前应请人核对（ROADMAP 拍板事项）。
  每条仅为初学者向的简明释义，不是学术注解。

查找入口: find_in_lexicon(text, max_hits)
  在 hakubun+kakikudashi 的拼接文本里按词形（汉字表记优先）匹配。
"""
import re

LEXICON_SOURCE = ("agent 整理（广辞苑/旺文社文语法通识归纳，非逐字引用，"
                  "覆盖 kanbun.info 高频词，未人工校对）")

# 每条: {"word": 词形（文本中出现的表记）, "reading": 现代假名遣い读音, "meaning": 简明释义}
GLOSSARY_LEXICON = [
    # ---- 接続詞・副詞（訓読文高频） ----
    {"word": "乃ち", "reading": "すなわち", "meaning": "すなわち。そのまま。あるいは「そこで」。"},
    {"word": "而して", "reading": "しかして", "meaning": "そして。そのあとに。また「〜のままに」。"},
    {"word": "然れども", "reading": "しかれども", "meaning": "しかし。とはいえ。逆接の接続詞。"},
    {"word": "然らば", "reading": "しからば", "meaning": "そうであるならば。「然らば則ち」＝そうだとしたら。"},
    {"word": "抑", "reading": "そもそも", "meaning": "そもそも。話の導入を示す。"},
    {"word": "且つ", "reading": "かつ", "meaning": "そのうえ。同時に。また「おもむろに」。"},
    {"word": "乃至", "reading": "ないし", "meaning": "または…まで。範囲・并列を示す。"},
    {"word": "況んや", "reading": "ましてや", "meaning": "まして…は言うまでもない（反語強調）。"},
    {"word": "所謂", "reading": "いわゆる", "meaning": "いわゆる。世間で言うところの。"},
    {"word": "或いは", "reading": "あるいは", "meaning": "あるいは。または。時に「ある人は」。"},
    {"word": "既に", "reading": "すでに", "meaning": "すでに。もう。また「当然に（既に〜べし）」。"},
    {"word": "曾て", "reading": "かつて", "meaning": "かつて。以前に。"},
    {"word": "將に", "reading": "まさに", "meaning": "まさに…しようとする。ちょうど…するところだ。"},
    {"word": "俄かに", "reading": "にわかに", "meaning": "急に。たちまち。"},
    {"word": "屢〻", "reading": "しばしば", "meaning": "しばしば。たびたび。「屢」とも。"},
    {"word": "遽", "reading": "にわか", "meaning": "すぐにも。「何遽ぞ」＝どうして…か（反語）。"},
    {"word": "何遽ぞ", "reading": "なんぞ", "meaning": "どうして…か。反語の疑問。"},
    {"word": "猶", "reading": "なお", "meaning": "なお。いまだに。また「あたかも…のごとし」。"},
    {"word": "殆ど", "reading": "ほとんど", "meaning": "ほとんど。「殆んぞ」＝あやしくも…か。"},
    {"word": "唯", "reading": "ただ", "meaning": "ただ…のみ。"},
    {"word": "凡そ", "reading": "およそ", "meaning": "およそ。大体のところ。"},
    {"word": "始め", "reading": "はじめ", "meaning": "はじめは。「始〜終り」で範囲を示す。"},
    {"word": "忽ち", "reading": "たちまち", "meaning": "たちまち。すぐに。"},
    {"word": "聊か", "reading": "いささか", "meaning": "いささか。少しは。"},
    {"word": "甚だ", "reading": "はなはだ", "meaning": "はなはだ。非常に。「甚だしい」形もある。"},
    {"word": "少く", "reading": "すくなく", "meaning": "少なく（「少く食尽く」など）。"},
    {"word": "大いに", "reading": "おおいに", "meaning": "大きく。はなはだ。"},
    {"word": "皆", "reading": "みな", "meaning": "みな。すべて。"},
    {"word": "直ちに", "reading": "ただちに", "meaning": "ただちに。すぐさま。"},
    {"word": "即ち", "reading": "すなわち", "meaning": "すなわち。…とすぐ。"},
    {"word": "敢えて", "reading": "あえて", "meaning": "あえて。わざわざ。また「敢えて…ず」＝あえて…しない。"},
    {"word": "果たして", "reading": "はたして", "meaning": "はたして本当に…か（疑問・反語）。"},
    {"word": "因りて", "reading": "よって", "meaning": "よって。それによって。"},
    {"word": "故に", "reading": "ゆえに", "meaning": "だから。その理由で。"},
    {"word": "但し", "reading": "ただし", "meaning": "ただし。但し書き。"},
    {"word": "要するに", "reading": "ようするに", "meaning": "つまるところ。"},
    {"word": "時に", "reading": "ときに", "meaning": "ときに。あるとき。"},
    {"word": "俄", "reading": "にわか", "meaning": "にわか。急なさま。"},
    # ---- 代名詞・指示 ----
    {"word": "之", "reading": "これ", "meaning": "それ・この人（目的語などに用いる）。"},
    {"word": "其", "reading": "その", "meaning": "その（指示）。訓読では「其の」と書く。"},
    {"word": "彼", "reading": "かれ", "meaning": "あれ・あの人。"},
    {"word": "誰", "reading": "たれ", "meaning": "誰。"},
    {"word": "何", "reading": "なに・なん", "meaning": "何。「何ぞ」＝どうして…か。"},
    {"word": "孰", "reading": "いずれ", "meaning": "どれ・どちら（比況の疑問）。「孰か」＝どちらが。"},
    {"word": "焉", "reading": "ここ", "meaning": "ここ・これ（代名詞）。また反語「焉んぞ」＝どうして。"},
    {"word": "某", "reading": "それがし・ぼう", "meaning": "ある人・なにがし。"},
    {"word": "吾", "reading": "われ", "meaning": "私（自分）。"},
    {"word": "我", "reading": "われ", "meaning": "私・自分。複数で「我等」。"},
    {"word": "汝", "reading": "なんじ", "meaning": "あなた（二人称）。"},
    {"word": "爾", "reading": "なんじ", "meaning": "あなた（汝に同じ）。"},
    {"word": "己", "reading": "おのれ", "meaning": "自分自身。"},
    # ---- 文語助動詞・形式語 ----
    {"word": "たり", "reading": "たり", "meaning": "完了「…した」／断定「…である」（活用：たり・て・たれ・たろ）。"},
    {"word": "なり", "reading": "なり", "meaning": "断定「…である」／伝聞推定「…という・…ようだ」。"},
    {"word": "べし", "reading": "べし", "meaning": "当然・可能・推量「…べきだ・…できるだろう」。"},
    {"word": "まし", "reading": "まし", "meaning": "反実仮想「もし…ならば…だろうに」。"},
    {"word": "む", "reading": "ん", "meaning": "推量・意志「…だろう・…しよう」。現代仮名遣いでは「ん」。"},
    {"word": "ず", "reading": "ず", "meaning": "打消「…ない」（連体「ざる」「ぬ」、已然「ざれ」）。"},
    {"word": "勿", "reading": "なかれ", "meaning": "…するな（禁止の再読文字）。「勿かれ」＝…してはいけない。"},
    {"word": "得", "reading": "え", "meaning": "可能「…できる」。「得ず」＝できない。"},
    {"word": "可", "reading": "べし", "meaning": "べき（可+動詞で再読文字「べし」）。"},
    {"word": "犹ほ", "reading": "なおほぼ", "meaning": "※「猶」に同じ（异体表記）。"},
    {"word": "所謂達", "reading": "いわゆるたつ", "meaning": "いわゆる達人・通じた人（文脈による）。"},
    # ---- 文語動詞（kanbun.info 语料高频） ----
    {"word": "曰く", "reading": "いわく", "meaning": "言う。（引述の常套：「〜曰く、…と」）。"},
    {"word": "謂ふ", "reading": "いう", "meaning": "言う・呼ぶ・思う（現代仮名遣い「いう」）。"},
    {"word": "鬻ぐ", "reading": "ひさぐ", "meaning": "売る。"},
    {"word": "祠る", "reading": "まつる", "meaning": "祀る。神をまつる。"},
    {"word": "誉む", "reading": "ほめる", "meaning": "褒める。「誉めて曰く」＝褒めて言うには。"},
    {"word": "陷す", "reading": "おとしいれる", "meaning": "陥れる。落ち入らせる。"},
    {"word": "陷る", "reading": "おちいる", "meaning": "陥る。落ちる。"},
    {"word": "牧す", "reading": "まきす", "meaning": "飼う・牧す（牛馬を）。"},
    {"word": "耕す", "reading": "たがやす", "meaning": "耕す。"},
    {"word": "狙", "reading": "さる", "meaning": "猿（「狙公」＝猿を飼う男）。"},
    {"word": "赴く", "reading": "おもむく", "meaning": "向かう。赴く。"},
    {"word": "触れ", "reading": "ふれ", "meaning": "触れる（「株に触れ」など）。"},
    {"word": "折る", "reading": "おる", "meaning": "折る。"},
    {"word": "冀ふ", "reading": "きぐ", "meaning": "望む。期待する。"},
    {"word": "釈て", "reading": "すて", "meaning": "「釈つ」＝捨てる・置く（「耒を釈てて」＝すきを捨てて）。"},
    {"word": "策うちて", "reading": "しむちて", "meaning": "「策う」＝むち打つ（「馬に策うちて」）。"},
    {"word": "畏る", "reading": "おそれる", "meaning": "恐れる・畏れる。"},
    {"word": "恤む", "reading": "うれえる", "meaning": "心配する・憂える。"},
    {"word": "驚く", "reading": "おどろく", "meaning": "驚く。"},
    {"word": "囲む", "reading": "かこむ", "meaning": "囲む。「囲むこと数重」＝何重にも囲む。"},
    {"word": "壁す", "reading": "へきす", "meaning": "塁壁を築く（「垓下に壁す」）。"},
    {"word": "自得", "reading": "じとく", "meaning": "自分の境地に満足すること。"},
    {"word": "揚揚", "reading": "ようよう", "meaning": "得意満面のさま（「意気揚揚」）。"},
    {"word": "闚う", "reading": "のぞう", "meaning": "のぞく（「門間より其の夫を闚う」）。"},
    {"word": "請ふ", "reading": "こう", "meaning": "求める・願う（現代仮名遣い「請う」）。"},
    {"word": "画きて", "reading": "えがきて", "meaning": "「画く」＝描く・区画する（「地に画きて蛇を為る」）。"},
    {"word": "相謂いて", "reading": "あいていいて", "meaning": "「相謂ふ」＝互いに言い合う。"},
    {"word": "賜ふ", "reading": "たまう", "meaning": "賜う・与える（現代仮名遣い）。"},
    {"word": "譽", "reading": "ほ", "meaning": "「譽む」＝褒める（旧字体「譽」＝新字体「誉」）。"},
    {"word": "屠る", "reading": "ほうる", "meaning": "（俗に）ほしいままにする。屠る＝さばく。"},
    {"word": "戒め", "reading": "いましめ", "meaning": "「戒む」＝慎む・警戒する。"},
    {"word": "恥ぢる", "reading": "はじる", "meaning": "恥じる。「恥づる」も同じ。"},
    {"word": "慕ふ", "reading": "したう", "meaning": "したう（現代仮名遣い「慕う」）。"},
    {"word": "祈る", "reading": "いのる", "meaning": "祈る。"},
    {"word": "慕は", "reading": "したわ", "meaning": "「慕ふ」の未然形（例：「慕はず」）。"},
    # ---- 故事成語のキー語（kanbun.info 名言页扩容） ----
    {"word": "臥薪嘗胆", "reading": "がしんしょうたん", "meaning": "薪の上に臥し薪を嘗めて復讐を志す（史記・越王勾践）。"},
    {"word": "推敲", "reading": "すいこう", "meaning": "詩句の字句を練り直す（賈島の「僧敲月下門」）。"},
    {"word": "管鮑の交わり", "reading": "かんぼうのまじわり", "meaning": "理解し合う親友の交わり（管仲と鮑叔）。"},
    {"word": "刎頸の交わり", "reading": "ふんけいのまじわり", "meaning": "首を切られても惜しまない深い友情（史記・廉頗藺相如）。"},
    {"word": "蟷螂の斧", "reading": "とうろうのおの", "meaning": "力をわきまえない無謀な抵抗（荘子）。"},
    {"word": "晏子の御", "reading": "あんしのぎょ", "meaning": "御者が傲慢を恥じて謙虚になった故事（晏子の御者）。"},
    {"word": "糟糠の妻", "reading": "そうこうのつま", "meaning": "貧しい時代から連れ添った妻（後漢書・宋弘）。"},
    {"word": "鼓腹撃壌", "reading": "こふくげきじょう", "meaning": "腹を鼓り土を打って歌う、太平の様子（荘子）。"},
    {"word": "病膏肓", "reading": "やまいこうこう", "meaning": "膏肓に入る＝到底治らない・解決不可能（左伝）。"},
    {"word": "梁上の君子", "reading": "りょうじょうのくんじ", "meaning": "盗人の婉曲表現（後漢書・陳寔）。"},
    {"word": "朝三暮四", "reading": "ちょうさんぼし", "meaning": "目先の違いで本質は同じ（列子・狙公の故事）。"},
    {"word": "漁父の利", "reading": "ぎょふのり", "meaning": "漁夫の利。第三方が得をする（戦国策）。"},
    {"word": "苛政は虎よりも猛し", "reading": "かせいはとらよりもたけし", "meaning": "悪政は虎より恐ろしい（礼記・檀弓）。"},
    {"word": "井蛙", "reading": "せいあ", "meaning": "井の中の蛙。視野が狭い者（荘子）。"},
    {"word": "夏虫", "reading": "かちゅう", "meaning": "夏の虫には氷を語れぬ＝短見（荘子）。"},
    {"word": "曲士", "reading": "きょくし", "meaning": "偏狭な学者・道に通じぬ人（荘子）。"},
    {"word": "韋編三絶", "reading": "いへんさんぜつ", "meaning": "易を愛読して綴じ紐が三度切れた（史記・孔子）。"},
    {"word": "一簣", "reading": "いき", "meaning": "土を運ぶ籠一つ。「一簣を成さざるも止むは吾が止むなり」（論語）。"},
    {"word": "一朝一夕", "reading": "いっちょういっせき", "meaning": "一夜两日ではない＝短期ではできない（易・系辞）。"},
    {"word": "三人虎", "reading": "さんにんとら", "meaning": "三人が虎を言えば虎と信じる＝流言の恐ろしさ（戦国策）。"},
    {"word": "一犬吠形", "reading": "いけんひけい", "meaning": "一犬が形に吠えれば百犬が声に吠ゆ（潜夫論）。"},
    {"word": "愚公", "reading": "ぐこう", "meaning": "山を移す愚公。地道な努力の故事（列子）。"},
    {"word": "木鐸", "reading": "ぼくたく", "meaning": "木の鐸。世に警鐘を鳴らす者（論語・天将以夫子為木鐸）。"},
    {"word": "栖栖", "reading": "せいせい", "meaning": "あわただしく奔走するさま（論語・微生畝）。"},
    {"word": "桴", "reading": "ふ", "meaning": "筏（「桴に乗りて海に浮かばん」）。"},
    {"word": "簞", "reading": "たん", "meaning": "竹の飯器（「一簞の食、一瓢の飲」）。"},
    {"word": "瓢", "reading": "ひさご", "meaning": "ひょうたん（「一瓢の飲」）。"},
    {"word": "陋巷", "reading": "ろうこう", "meaning": "狭い路地（「陋巷に在り」・顔回）。"},
    {"word": "鄙夫", "reading": "ひふ", "meaning": "田舎者・卑しい男（論語）。"},
    {"word": "异端", "reading": "いたん", "meaning": "正しくない道（論語「異端を攻むるは害あるのみ」）。"},
    {"word": "㡯", "reading": "とこ", "meaning": "※异体字につき通常「途」を用いる。"},
    # ---- 文語動詞追加 ----
    {"word": "食らう", "reading": "くらう", "meaning": "食べる（「子は敢えて我を食らうこと無かれ」）。"},
    {"word": "食ぶ", "reading": "くらう", "meaning": "※「食らう」の文語表記（虎が狐を食ぶ）。"},
    {"word": "遷さず", "reading": "うつさず", "meaning": "「遷す」＝移す（「怒りを遷さず」＝怒りを他に移さない）。"},
    {"word": "貳す", "reading": "たぶさす", "meaning": "ふたごする・重ねて過ちを犯す（「過ちを弐びせず」）。"},
    {"word": "御する", "reading": "ぎょする", "meaning": "統治する・驭する（「御馬」）。"},
    {"word": "統理す", "reading": "とうりす", "meaning": "統べて治める（「聖人之を統理す」）。"},
    {"word": "崇飾す", "reading": "すうしょくす", "meaning": "堂々と飾りたてる（「武帝仏寺を崇飾する」）。"},
    {"word": "玷く", "reading": "おかす", "meaning": "瑕をつける・傷つける（「之を玷く」）。"},
    {"word": "托する", "reading": "たくする", "meaning": "託する（「専ら人に托して」）。"},
    {"word": "收拾す", "reading": "しゅうしゅうす", "meaning": "拾い集める（「収拾し焚毀するに暇あらず」）。"},
    {"word": "焚毀す", "reading": "ふんきす", "meaning": "焼き捨てる（「焚毀するに暇あらず」）。"},
    {"word": "洎び", "reading": "および", "meaning": "「洎ぶ」＝及ぶ（「相たるに洎び」）。"},
    {"word": "好む", "reading": "このむ", "meaning": "好む（「学を好む者」）。"},
    {"word": "察する", "reading": "さつする", "meaning": "よく見る・考察する（「隣国の政を察するに」）。"},
    {"word": "移す", "reading": "うつす", "meaning": "移す（「其の民を河東に移す」）。"},
    {"word": "粟", "reading": "ぞく", "meaning": "穀物・粟（「其の粟を河内に移す」）。"},
    {"word": "遊ばず", "reading": "あそばず", "meaning": "「遊ぶ」＝遠方に出かける（「父母在せば遠く遊ばず」）。"},
    {"word": "方有り", "reading": "ほうあり", "meaning": "「方」＝行き先（「遊ぶに必ず方有り」）。"},
    # ---- 文語助動詞追加・形式語 ----
    {"word": "けり", "reading": "けり", "meaning": "過去「…た」／詠嘆「…だなあ」。"},
    {"word": "らむ", "reading": "らむ", "meaning": "現在推量・様態「…ているだろう」。"},
    {"word": "つ", "reading": "つ", "meaning": "完了「…してしまう」。"},
    {"word": "ぬ", "reading": "ぬ", "meaning": "完了「…てしまう」／（打消「ず」の連体形「ぬ」）。"},
    {"word": "ざる", "reading": "ざる", "meaning": "「ず」の連体形「…ない」。「陥さざる無きなり」＝陥れないものはない。"},
    {"word": "ごとし", "reading": "ごとし", "meaning": "比況「…のようだ」（「累卵のごときなり」）。"},
    {"word": "如くは", "reading": "ごとくは", "meaning": "「如くは莫し」＝…に及ぶものはない。"},
    {"word": "莫し", "reading": "なし", "meaning": "ない（「如くは莫し」）。"},
    {"word": "可からず", "reading": "べからず", "meaning": "「べし」の打消＝…してはならない。"},
    {"word": "べからざる", "reading": "べからざる", "meaning": "「べし」の打消連体形「…できない・…してはならない」。"},
    {"word": " 得べからず", "reading": "うべからず", "meaning": "得ることができない（「兎は復た得べからず」）。"},
    {"word": "而も", "reading": "しかも", "meaning": "そして。そのうえ（而の後接も）。"},
    {"word": "而るに", "reading": "しかるに", "meaning": "しかし（「而るに」）。"},
    {"word": "然り", "reading": "しかり", "meaning": "そうである（「然りて則ち」＝そうすれば）。"},
    {"word": "然りて", "reading": "しかりて", "meaning": "そうしてから。そうすれば（supar 输出常见的接续形）。"},
    # ---- 訓読特有の形式（kanbun.info 語） ----
    {"word": "曰", "reading": "いわく", "meaning": "「曰く」の単字表記（言う）。"},
    {"word": "謂いて", "reading": "いいて", "meaning": "「謂ふ」の連用形＋て（「子貢に謂いて曰く」）。"},
    {"word": "対えて", "reading": "こたえて", "meaning": "「対ふ」＝答える（「孔子対えて曰く」）。"},
    {"word": "問う", "reading": "とう", "meaning": "問う（「孝を問う」）。"},
    {"word": "応うる", "reading": "こたうる", "meaning": "「応ふ」＝答える・応じるの連体形。"},
    {"word": "奚", "reading": "なに・いずれ", "meaning": "何・どこ（「女奚ぞ…」＝あなたはどうして…か）。"},
    {"word": "女", "reading": "なんじ", "meaning": "あなた（汝に同じ。論語「女と回と孰れか」）。"},
    {"word": "由", "reading": "ゆう", "meaning": "子路の名（仲由）。「其れ由なるか」。"},
    {"word": "愈れる", "reading": "まさる", "meaning": "勝れる（「女と回と孰れか愈れたり」）。"},
    {"word": "望まん", "reading": "のぞまん", "meaning": "望む意志形（「回を望まん」＝回を仰ぎ見ようか）。"},
    {"word": "喪ぼす", "reading": "もうぼす", "meaning": "「喪す」＝失う（「天予を喪ぼせり」＝天が我を失わせた）。"},
    {"word": "噫", "reading": "ああ", "meaning": "ああ（感嘆詞・「噫、天予を喪ぼせり」）。"},
    {"word": "哀公", "reading": "あいこう", "meaning": "魯の君主（「哀公問う」）。"},
    {"word": "孰か学を好む", "reading": "しょかがくをこのむ", "meaning": "「孰か…」＝どちらが…か（弟子孰か学を好むと為す）。"},
    {"word": "顔回", "reading": "がんかい", "meaning": "孔子の弟子・颜回（「顔回なる者有り、学を好む」）。"},
    {"word": "短命", "reading": "たんめい", "meaning": "早死に（「不幸短命にして死せり」）。"},
    {"word": "冉求", "reading": "ぜんきゅう", "meaning": "孔子の弟子（「冉求曰く」）。"},
    {"word": "画す", "reading": "えがくす", "meaning": "区切って限る（「今、女は画れり」＝あなたは限界を決めている）。"},
    {"word": "中道", "reading": "ちゅうどう", "meaning": "途中（「中道にして廃す」）。"},
    {"word": "廃す", "reading": "はいす", "meaning": "やめる・中绝する（「力足らざる者は中道にして廃す」）。"},
    {"word": "季路", "reading": "きろ", "meaning": "子路（「季路鬼神に事うることを問う」）。"},
    {"word": "事う", "reading": "まつらう", "meaning": "仕える（「君に事う」）。現代仮名遣いでは「事える」。"},
    {"word": "敢えて死を問う", "reading": "あえてしをとう", "meaning": "あえて死について問う（季路の問）。"},
    # ---- 文語形容詞・形容動詞 ----
    {"word": "堅し", "reading": "かたし", "meaning": "堅い。「堅きこと」＝堅いこと。"},
    {"word": "利し", "reading": "とし", "meaning": "鋭い・有利だ（「矛の利」＝矛の鋭さ）。"},
    {"word": "甚だし", "reading": "はなはだし", "meaning": "程度がひどい。"},
    {"word": "うつくし", "reading": "うつくし", "meaning": "（古語）いとしい・可爱い。"},
    {"word": "凶なる", "reading": "きょうなる", "meaning": "「凶なり」＝不作である（「河内凶」＝河内で飢饉）。"},
    {"word": "遠し", "reading": "とおし", "meaning": "遠い。「遠き者」＝遠くの人。"},
    {"word": "近し", "reading": "ちかし", "meaning": "近い。「近きの人」。"},
    {"word": "危うし", "reading": "あやうし", "meaning": "危ない。「危うきこと累卵のごとし」。"},
    {"word": "軽し", "reading": "かるし", "meaning": "軽い。"},
    {"word": "重し", "reading": "おもし", "meaning": "重い。"},
    {"word": "飽く", "reading": "あく", "meaning": "満ち足りる。「飽かざらば」＝満足できないなら。"},
    {"word": "忿戻", "reading": "ふんれい", "meaning": "腹を立てて道理に反すること。"},
    {"word": "肆", "reading": "ほしいまま", "meaning": "ほしいままにする（「古の狂や肆」）。"},
    {"word": "固より", "reading": "もとより", "meaning": "もとから。はじめから。"},
    # ---- 名言・成語のキー語（kanbun.info 语料） ----
    {"word": "矛盾", "reading": "むじゅん", "meaning": "ほこ（矛）とたて（盾）。つじつまの合わないこと（韓非子）。"},
    {"word": "蛇足", "reading": "だそく", "meaning": "蛇に足を描く。余計なことを付け足すこと（戦国策）。"},
    {"word": "塞翁が馬", "reading": "さいおうがうま", "meaning": "人事の禍福は予測できない（淮南子）。"},
    {"word": "四面楚歌", "reading": "しめんそか", "meaning": "四方から敵に囲まれ孤立すること（史記・項羽）。"},
    {"word": "五十歩百歩", "reading": "ごじゅっぽひゃっぽ", "meaning": "程度の差はあれ本質は同じ（孟子）。"},
    {"word": "鶏口牛後", "reading": "けいこうぎゅうご", "meaning": "小さくても主になりたい心意（戦国策）。"},
    {"word": "守株", "reading": "しゅじゅ", "meaning": "古い成功に固執して失敗すること（韓非子）。"},
    {"word": "画竜点睛", "reading": "がりょうてんせい", "meaning": "最後の仕上げの大事な一手（歴代名画記）。"},
    {"word": "呉越同舟", "reading": "ごえつどうしゅう", "meaning": "敵同士が同じ船上で協力すること（孫子）。"},
    {"word": "孟母断機", "reading": "もうぼだんき", "meaning": "孟子の母が機を断って学業の大切さを諭した故事。"},
    {"word": "酔生夢死", "reading": "すいせいむし", "meaning": "むなしく生きむなしく死ぬ。"},
]


def find_in_lexicon(text: str, max_hits: int = 5):
    """文本（白文+書き下し文の連結）に词形が現れた词库条目を返す。"""
    hits = []
    if not text:
        return hits
    seen = set()
    for item in GLOSSARY_LEXICON:
        w = item.get("word", "")
        if not w or w in seen:
            continue
        if w in text:
            hits.append({
                "word": w,
                "reading": item.get("reading", ""),
                "meaning": item.get("meaning", ""),
                "source": "lexicon",
            })
            seen.add(w)
            if len(hits) >= max_hits:
                break
    return hits


def lexicon_size():
    return len(GLOSSARY_LEXICON)
