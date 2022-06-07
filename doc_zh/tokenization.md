# sub-word algorithm

## Tokenization

​		在自然语言处理中，大部分的数据都是生语料（文本），但是**机器是无法理解文本的**，我们将句子序列送入模型时，模型仅仅只能看到一串字节，它无法知道一个词从哪里开始，到哪里结束，所以也不知道一个词是由哪些字节组成的。

​		Tokenizer 的作用就是将文本拆分为单词或者子词（sub-word），然后通过词表将它们转换为其 id，这样送入模型的就是一个 id 的序列。如果词表已经存在，把单词或者子词转为 id 是非常容易的，所以 tokenization 这一步的难点在于，如何把文本拆分成词语或者子词。



## word-base tokenization

​		把一段文本切分成 token 的方法有非常多，举个例子，看一下下面这个句子`Let's tokenize! Isn't this easy?`

​		最简单的方法可以根据空格进行切分，结果如下：

```
["Let's", 'tokenize!', "Isn't", 'this', 'easy?']
```

​		这种方法非常直观，但是是有一个问题，我们可以看到在结果中包含这样的 token: `tokenize!` 和 `easy?`，标点连在单词上，这就会导致一个问题，如果我们不把标点连着词的token放入词表，那么这些在词表中未出现的词就会被当做OOV（out of vocabulary）处理，用`<UNK>`等特殊标记替代，这就损失了一部分信息，这样会非常影响模型的表现，但是如果把出现的所有标点连着词的token全部放入词表，那么可以想象词表会非常庞大（进而导致模型非常庞大），产生巨大的计算开销的同时，模型收敛也会变得困难。同时对于在词表中但是出现次数非常少的token，模型也很难学到其表示。

​		所以标点符号也应该被考虑进到切分的规则中，这样就可以避免词表巨大而词表内部词频稀疏的问题。把这个句子进一步切分结果如下：

```
["Let", "'", "s", "tokenize", "!", "Isn", "'", "t", "this", "easy", "?"]
```

​		比直接用空格分割好一点，但是还是有一些瑕疵，比如`Isn't`代表的是`Is not`，所以这个单词最好被切分为`["Is", "n't"]`。这就使得分词变得复杂了，这也是在NLP领域不同的模型使用了各种不同 Tokenizer 的原因之一。这也加大了研究者在复现这些工作的时候的难度。一个句子，使用不同的规则，将有许多种不同的分词结果。我们在使用预训练模型做下游任务的时候，只有使用和它训练时使用的同一种 tokenize 的方法处理数据，才能取得相应的效果。

​		为了解决诸如`Isn't`这类词的分词问题，也出现了一些基于规则的分词方法，比如常用的基于规则的分词器 Spacy，这个句子通过这种分词方法切分的结果如下：

```
["Let", "'s", "tokenize", "!", "Is", "n't", "this", "easy", "?"]
```

​		三种不同的切分方法效果对比如下：

![3 different tokenization scheme: on rules, on punctuaction, on white spaces](img/tokenize.png)

​		上面说的三种分词方法，都是词级别的分词方法（word tokenization），简单来说，就是以词为单位对文本进行切分。尽管这是将文本切分为更小的单位的最直观的方式，但是这种方式在处理大量语料的时候会产生一个非常严重的问题——生成一个巨大的词表（因为大量的语料中会存在大量的只出现一次/少次的token）。

> ​		比如 Transformer-XL 这个模型，就用的是基于空格和标点的分词方式，词表大小是夸张的267,735。这么大的词表会导致模型在输入端需要一个巨大的 embedding 矩阵（token id - embedding），在输出端需要一个巨大的 generator 矩阵（hidden value - token id），这会使得模型参数量剧增，导致大量的内存占用以及预测的时间复杂度。**总之，这一类模型的词表大小基本很少会超过50,000，特别是单语模型**。

​		那么既然词级别的分词方法不理想，能不能基于字符级别来分词呢？



## character-base tokenization

​		基于字符级别的分词方法非常简单，简单来说，就是将每个字符看作一个词，还是上面那个句子，切分效果如下：

```
['L', 'e', 't', "'", 's', ' ', 't', 'o', 'k', 'e', 'n', 'i', 'z', 'e', '!', ' ', 'I', 's', 'n', "'", 't', ' ', 't', 'h', 'i', 's', ' ', 'e', 'a', 's', 'y', '?']
```

​		尽管这字符级别的分词方式非常简单并且能够大大缩小词表的大小（进而缩小模型的大小），并且不用担心未知词汇。但是这种表示方式，对于模型来说要学习出有意义的词表示难度大大增加了（字母本身就没有任何的内在含义）。

>举个例子，从字母“t”中学习到有意义的词表示要比从“today”中学习到有意的词表示难得多。

计算复杂度提升（字母的数目远大于token的数目），输出序列的长度将变大，对于Bert、CNN等限制最大长度的模型将很容易达到最大值。

​		因此，字符级别的分词方式一般很难产生效果好的模型，所以为了兼顾到词级别和字符级别分词方式的好处，产生了一种折中的处理方式，称为子词切分方法（subword tokenization）。



## subword tokenization

​		上面提到的两种分词方式各有各的不足。

​		词级别的分词：1、词表巨大；2、容易出现大量词表外的token（OOV问题）；3、对于相似的词语失去相似度信息（比如dog和dogs在词表中是两个完全不同的词）

​		字符级别的分词：1、文本转为 id 序列之后长度非常长；2、字母本身没有内在含义，从单一的字母中很难学习到有意的词表示。

​		为了改进分词方法，在`<UNK>`数目和词表示含义丰富性之间达到平衡，于是产生了一个折中的算法：子词切分（subword tokenization），子词切分的方法也分好几种，但是它们都遵从两个原则：

​		1、常用的词语不应该被切分为更小的片段

​		2、不常用的词语应该被分解为有意义的子词

> ​		举个例子，`tokenization`这个词，可以被分解为`token`和`ization`，`token`和`ization`作为单独的子词出现的概率更高（比如`token`、`tokens`、`tokenizing`、`tokenization`，或者`tokenization`、`modernization`等等），同时`tokenization`的意思被作为`token`和`ization`的复合意思被保存下来。

​		这种方式在英文上效果不错，在另外一些语言上效果甚至更好，在某些语言中，可以像搭积木一样，通过子词的组合形成几乎任何单词。

​		子词切分方式使得模型能够在保持一个合理的词表大小的情况下，能够学习到更有意义的子词的表示，同时也能让模型拥有更好地处理词表中没有的词语的能力（将词表中没有的词，分解成词表中有的子词）。

​		当前流行的模型中所用到的 subword Tokenizer 主要有三种不同的算法：BPE（Byte-Pair Encoding），WordPiece 和 SentencePiece。不同的模型所使用的 Tokenizer 的类型不同，比如，在 BertTokenizer 中所使用的就是 WordPiece。



## BPE（Byte-Pair Encoding）

​		BPE 算法最早是[Neural Machine Translation of Rare Words with Subword Units (Sennrich et al., 2015)](https://arxiv.org/abs/1508.07909)提出的，是最早的一种数据压缩算法之一。BPE 是一个子词分词方法，本身需要依赖于预分词（pre-tokenization），也就是把文本先切分成词语（BPE算法接收的输入是一个词语的列表，而不是一个生语料）。这个预分词可以是简单的基于空格的分词方法，比如 GPT-2 和 RoBERTa；也可以是更复杂的比如基于规则的分词方法，比如 XLM 和 FlauBERT 用的是 Moses；再比如 GPT 用的是 Spacy。

​		在将文本切分成词语之后，就得到了一个词表，以及这个词表中所有词语的词频。接下来，BPE 创建一个基本词表，这个词表中包含语料中所有出现的字符（在英文中就是26个字母和各种符号），然后统计语料中相邻单元对（这里的单元要在基本词表中）的频数，选取频数最高的单元对合成新的子词单元，加入基本词表中，重复进行直到词表大小达到预设值（词表的大小是个超参数，在训练前就设定好了的）。

​		举个例子，假设在预分词之后，我们得到下面这个词表以及它们相应的词频：

```
("hug", 10), ("pug", 5), ("pun", 12), ("bun", 4), ("hugs", 5)
```

​		同时，取出语料中所有出现的字符作为基本词表：

```
["b", "g", "h", "n", "p", "s", "u"]
```

​		将第一个词表按照基本词表进行切分：

```
("h" "u" "g", 10), ("p" "u" "g", 5), ("p" "u" "n", 12), ("b" "u" "n", 4), ("h" "u" "g" "s", 5)
```

​		计算所有相邻单元对的频率，并且选择频率最高的单元对

```
"ug": 10 + 5 + 5
```

​		`ug`被加入词表，并且语料所有的`ug`相连的部分都被组合

```
("h" "ug", 10), ("p" "ug", 5), ("p" "u" "n", 12), ("b" "u" "n", 4), ("h" "ug" "s", 5)
```

​		然后是`un`和`hug`，这时候的词表为：

```
["b", "g", "h", "n", "p", "s", "u", "ug", "un", "hug"]
```

​		语料表示为：

```
("hug", 10), ("p" "ug", 5), ("p" "un", 12), ("b" "un", 4), ("hug" "s", 5)
```

​		假设此时词表大小已经达到预设值，于是训练停止，这时候模型学到的这个词表（其实就是组合的规则）就会被应用在新遇到的词上，比如这时候遇到一个词`bug`就会被分解为`["b", "ug"]`，但是如果新遇到的词中存在基本词表中都没有的字符，则还是会用`<UNK>`表示，比如`mug`就会被表示为`["<UNK>", "ug"]`。在实际的训练数据中，每个正常应该用到的字符都会出现至少一次，所以它们都应该包含在基础词表中，但是对于一些非常特殊的符号（比如表情符号），这种情况仍然有可能发生。

​		词表的大小（基础词表的大小 + BPE 算法执行的轮数）是一个超参数，比如 GPT 的词表大小是40478，因为基础词表大小是478，然后算法运行了40000轮。

​		上面的做法其实是 BPE 算法的简化版本，真正的在做 BPE 时还有一些关键的细节需要注意：

​		1、在将单词拆分成最小单元时，会在单词序列后加上”</w>”(具体实现上可以使用其它符号)来表示中止符。在子词解码时，中止符可以区分单词边界。

​		2、每次合并后词表大小可能出现3种变化：

- +1，表明加入合并后的新子词，同时原来的2个子词还保留（2个字词分开出现在语料中）。
- +0，表明加入合并后的新子词，同时原来的2个子词中一个保留，一个被消解（一个子词完全随着另一个子词的出现而紧跟着出现）。
- -1，表明加入合并后的新子词，同时原来的2个子词都被消解（2个字词同时连续出现）。

​		3、实际上，随着合并的次数增加，词表大小通常先增加后减小

​		4、得到最终词表后，使用时的编码方式（最大长度匹配）：

- 将词典中的所有子词按照长度由大到小进行排序；
- 对于单词w，依次遍历排好序的词典。查看当前子词是否是该单词的子字符串，如果是，则输出当前子词，并对剩余单词字符串继续匹配。
- 如果遍历完字典后，仍然有子字符串没有匹配，则将剩余字符串替换为特殊符号输出，如”<unk>”。

​		5、解码：如果相邻子词间没有中止符，则将两子词直接拼接，否则两子词之间添加分隔符

***

- **BBPE（Byte-level BPE）**

​		在生成基础词表这一步的时候，如果这个基础词表包含了所有可能的字符，那么这个基础词表会非常大，比如用所有的 unicode 字符来当做基础词表。

​		为了能够缩减基础词表的大小，GPT-2 在生成基础词表的时候，用了字节（一个字节有256种不同的组合）来作为基础词表。这是一个非常巧妙的技巧，它把基础词表的大小限制在了256，同时能够确保所有的基本字符都包含在基础词表中（一个字符可以由多个字节组成）。

​		GPT2 的分词器能够在不需要 `<UNK>`的情况下对所有的文本进行分词（还用了一些额外的规则来处理标点符号）。GPT-2 的词表大小是 50257，其中包括256个字节基本词表，一个特殊的文本结束符号，以及算法运行50000轮产生的子词。

***



## WordPiece

​		WordPiece 算法最早发表于 [Japanese and Korean Voice Search (Schuster et al., 2012)](https://static.googleusercontent.com/media/research.google.com/ja//pubs/archive/37842.pdf)，它和 BPE 算法非常相似。也有一些预训练模型的分词器用的是这个算法，比如 BERT、DistilBERT 和 Electra。与 BPE 算法类似，WordPiece 算法也是初始化一个基础词表，然后每次从词表中选出两个子词合并成新的子词。

​		与 BPE 的主要区别在于，选择两个子词进行合并的规则：BPE 选择频数最高的相邻子词合并，而 WordPiece 使用的是通过语言模型来计算合并两个单词可能造成的影响，然后选择使得似然函数提升最大的字符对。这个提升是通过结合后的字符对减去结合前的字符对之和得到的。

​		假设句子$ S=（t1,t2,...,t_n）$由 n 个 token 组成，$t_i$表示第$i$个 token，假设各个 token 之间是相互独立的，则句子$S$的语言模型似然值等于所有子词概率的乘积

<img src="https://render.githubusercontent.com/render/math?math={logP(S) = \sum^n_{i=1}logP(t_i)}} = -1">
`$ logP(S) = \sum^n_{i=1}logP(t_i) $`

<img src="https://render.githubusercontent.com/render/math?math={\color{white}\L = -\sum_{j}[T_{j}ln(O_{j})] + \frac{\lambda W_{ij}^{2}}{2} \rightarrow \text{one-hot} \rightarrow -ln(O_{c}) + \frac{\lambda W_{ij}^{2}}{2}}">

​		假设把相邻位置的两个 token $x$ 和 $y$ 进行合并，合并后的 token 记为 $z$，此时句子 $S$ 的似然值变化可以表示为：
`$
logP(t_z)-(logP(t_x)+logP(t_y)) = log(\frac{P(t_z)}{P(t_x)P(T_y)})
$`
​		也就是说，判断`tokenization`相较于`token` + `ization`是否更适合出现。选择能够提升语言模型概率最大的相邻子词加入词表。



## Unigram

​		Unigram 算法最早发表于  [Subword Regularization: Improving Neural Network Translation Models with Multiple Subword Candidates (Kudo, 2018)](https://arxiv.org/pdf/1804.10959.pdf)。与 WordPiece 一样，Unigram Language Model(ULM) 同样使用语言模型来挑选子词。不同之处在于，BPE 和 WordPiece 算法的词表大小都是从小到大增加的。而 ULM 则是先初始化一个大词表，这个基础词表包含了所有预分词结果中的 token 以及所有常用的子词（也可以通过 BPE 算法初始化），根据评估准则不断丢弃里边的词，直到满足预设条件。ULM 算法考虑了句子的不同分词可能，因而能够输出带概率的多个分词序列。

​		并没有预训练模型单独使用 ULM 作为分词的算法，但是它常与 SentencePiece 一起使用。

​		对于句子$S$，$\mathop{x}\limits ^{\rightarrow} = (x_1,x_2,...,x_m)$为句子的一个分词结果，由 m 个子词组成。所以，当前分词下句子$S$的似然值可以表示为：
$$
P(\mathop{x}\limits ^{\rightarrow}) = \prod^m_{i=1}P(x_i)
$$
​		对于句子$S$，挑选似然值最大的作为分词结果，则可以表示为：
$$
x^* = \mathop{argmax}\limits_{x \in U(x)}~P(\mathop{x}\limits ^{\rightarrow})
$$
​		这里的$U(x)$包含了句子的所有分词结果。在实际应用中，词表大小有上万个，直接罗列所有的分词组合不具有操作性。针对这个问题，可以通过维特比算法得到 $x^*$来解决。

​		ULM 通过 EM 算法来估计每个子词的概率$P(x_i)$，假设当前词表为V，训练数据为|D|，则当前训练数据中所有句子的所有分词组合形成的概率相加，表示为：
$$
L = \sum^{|D|}_{s=1}log(P(X^{(s)}))=\sum^{|D|}_{s=1}log(\mathop{\sum_{x \in U(X^{(s)})}}P(x))
$$
​		在训练的开始阶段，ULM 初始化一个巨大的基础词表，然后针对当前词表，用上面的算法计算每个子词在训练数据上的概率，然后计算移除每个子词时，语言模型整体的损失上升了多少，记为这个子词的损失值。然后通过排序，按照一定比例移除掉词表中损失值最低的一部分子词（这个比例一般是10%或者20%），这些子词的损失值最低，意味着他们对语言模型的影响最小。每训练一步，都会移除掉部分的子词，直到词表大小达到预设值为止。（ULM 算法训练的过程中会保留基础的字符以保证任何词语都能被处理）。

​		训练完成的 UML 模型对一个句子给出多种的分词可能，比如说一个训练好的 ULM 分词器的词表如下：

```
["b", "g", "h", "n", "p", "s", "u", "ug", "un", "hug"]
```

​		那么 `"hugs"` 就有这么几种分词方法： `["hug", "s"]`， `["h", "ug", "s"]` ， `["h", "u", "g", "s"]`。ULM 在训练的过程中，在保存词表的同时会保存每个词表中 token 的概率，在实际使用的时候，一般会选取概率值最高的分词序列，如果需要也能够输出带有概率的不同分词序列。

​		

## SentencePiece

​		上面提到的所有分词算法都存在同一个问题：这些分词方式都是建立在原文本通过空格来分隔词语的。但是并不是所有语言词和词之间都是有空格的。还有就是，将分词结果解码到原来的句子中时，会在不同的词之间添加空格，这样解码出来的标点符号就不会和词语连着。

> Raw text: Hello world. 
>
> Tokenized: [Hello] [world] [.]
>
> Decoded text: Hello world .

​		这就是编码解码出现的歧义性，因此需要特别定义规则来实现互逆。还有一个例子是，在解码阶段，欧洲语言词之间要添加空格，而中文等语言则不应添加空格。一种解决方案是，给不同的语言定制不同的预分词算法和解码算法，比如 XLM 就在中文、日文和泰文上做了尝试。		

​		为了能够更好地解决这个问题，谷歌在 [SentencePiece: A simple and language independent subword tokenizer and detokenizer for Neural Text Processing (Kudo et al., 2018)](https://arxiv.org/pdf/1808.06226.pdf)中提出，把将所有的字符都转化成 Unicode 编码，空格用`_`来代替，然后进行分词操作。这样空格也不需要特别定义规则了，然后在解码结束后恢复即可。然后还是用 BPE 或者 ULM 算法来构建词表。

​		SentencePiece 集成了BPE、ULM 算法，除此之外，它也能支持字符和词级别的分词。使用 SentencePiece + ULM 的模型有 ALBERT、XLNet、T5。

​		
