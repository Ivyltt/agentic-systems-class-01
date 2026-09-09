# Agentic Systems Studio — 讲稿 / Teaching Script

**用法** · 英文段落是照着念的正文。每段英文上面的中文是同一段的完整翻译,方便快速读。括号里是操作:点哪里、滚到哪里、等什么。

**时间** · 按 130 词/分钟加每次点击约 15 秒估算,正文约 50 分钟,留 10 分钟给提问、慢讲和意外:开场 2 · Part I 26 · Part II 10 · Part III 11 · 收尾 1。Part I 的机制部分是重点,一分钟都没砍;每节末尾有一行「如果时间不够」的跳过点,三处全跳可再省约 6 分钟。

**贯穿的例子** · 我全程管它叫 **the answer box**:社交 app 里那个 AI 问答框 —— 用户打一句话,它结合平台上的帖子和模型自己的知识给答案。小红书、Reddit、X 都有这种功能。不点名、不猜任何一家的内部实现;讲的是任何这类系统都必须做的事。

**数字** · 稿子里每一个数字都是页面上显示的数字,页面上每一个数字都是跑出来的。念的时候可以直接指着屏幕。文末有一张「数字在哪」的备查表。

---

## 开场 · 2 分钟

(打开页面,停在左栏 **00 Agency, in five rungs**。先别往下滚。)

> 随便打开一个社交 app —— 小红书、Reddit、X —— 顶上都有一个框,可以打一句问题。"东京五天,第一次去,该怎么玩?"你得到的不是一堆链接,而是一个答案,下面还引用了平台上的帖子。我把这个东西叫做 **the answer box**,这一个小时我会不停地回到它,因为这个框本身就是一个 agentic 系统,而今天我们看的每一样东西,都是它必须处理的问题。

Open any social app — Xiaohongshu, Reddit, X — and there's a box at the top where you type a question. "Five days in Tokyo, first time, what should I do?" Instead of links, you get an answer, with posts from the platform cited under it. I'll call that thing **the answer box**, and I'll keep coming back to it all hour, because that box is an agentic system, and everything we look at today is something it has to deal with.

> 三页。先把一个 agent 完整看懂;然后看多了一个模型之后什么变了;最后看一个真实应用,从头到尾。还有一个问题,我会问到你们烦为止:**在这一步,谁被允许做决定 —— 模型,还是你的代码?** 只带走这一个问题,这门课就算学到了。

Three pages. One agent, understood completely. Then what changes when there's more than one. Then a real application, end to end. And one question I'll ask until you're sick of it: **at this point, who is allowed to decide — the model, or your code?** Leave with only that, and you've got the course.

> 关于这个页面的一条规则:上面没有任何东西是"说说而已"。每一个数字都是跑出来的 —— 真 Python、真 AutoGen,最后一页还有真的航空网站和真的模型。你们读过的关于 agent 的东西大多是图和形容词。这里是计数。

One rule about this page: nothing on it is asserted. Every number was produced by running something — real Python, real AutoGen, and on the last page a real airline site and a real model. Most of what you've read about agents is diagrams and adjectives. This is counts.

---

## Part I · Agency, in five rungs · 26 分钟

(左栏已经在 **00**。往下滚到 **CONCEPT · READ THIS FIRST**。)

> 问十个人什么是 agent,你会得到十个答案。这里有个更好的问题,而且永远有答案:**哪些决定是模型做的,哪些是你的代码做的?** 按这个来给系统排序,它们会排成五级:你决定一切;模型可以要一次工具;模型决定要几次、什么时候算完;模型给自己写计划;多个模型分工。

Ask ten people what an agent is and you get ten answers. Here's a better question, and it always has an answer: **which decisions does the model make, and which does your code make?** Sort systems by that and they line up in five steps: you decide everything; the model may ask for a tool once; the model decides how many times and when it's done; the model writes itself a plan; several models split the work.

> 这个阶梯就是 answer box 真实的发展史:第一版靠记忆回答;第二版搜一次;第三版可以再搜。每个团队都在爬这个梯子,每上一级都有代价。我们接下来要数的就是代价。

That ladder is the actual history of the answer box: version one answers from memory; version two searches once; version three may search again. Every team climbs it, and every step costs something. We're going to count what.

(滚到 **What the model can and cannot do**。)

> 有一件事要牢牢记住,因为它是这个领域里最常见的误解。**模型从来不执行任何东西。** 当它写出 `ACTION: get_weather(Boston)`,它只是生成了一段文字,文字里提到了一个函数名。就这样。是一个程序读到这段文字,决定要不要照办,然后去调真正的函数 —— 这个程序可能是你写的,也可能是框架或厂商替你做的。永远不是模型。哪怕是那种看起来像“模型自己跑了”的托管工具,也是包在模型外面的一层程序。模型提了要求,代码做了动作。

One thing to hold onto, because it's the most common misunderstanding in the field. **The model never runs anything.** When it writes `ACTION: get_weather(Boston)`, it produced a piece of text that names a function. That's all. A program reads that text, decides whether to honour it, and calls the real function — your code, or a framework or provider doing it for you. Never the model. Even a hosted tool that looks like "the model ran it" is a program wrapped around the model. The model asked. Code acted.

> 所以下面每个 prompt 开头那一行 —— "Tools you may call: get_weather, get_forecast" —— 就是模型能提的要求的完整清单。在 answer box 里,那一行写的是:搜帖子、取帖子。没写的是:替用户发帖、发消息、删东西。最安全的能力,是你从来没写上去的那个。

So the line at the top of every prompt below — "Tools you may call: get_weather, get_forecast" — is the complete list of what the model can ask for. In the answer box it says: search posts, fetch a post. Not: post on the user's behalf, send a message, delete anything. The safest capability is the one you never wrote down.

(滚到 **Who decides when to stop**。)

> 从第三级起,是模型决定什么时候算完。所以如果这个任务*完不成*,没有东西能停下它 —— 它会一直搜,直到服务商拒绝请求,你为每一步付钱,用户看到一个转圈。停止规则得你自己写,一共四道检查:步数上限;重复检查 —— 同一个搜索搜了两遍就是卡住了;预算,按 token 或按分钱算,一天一千万个问题的时候这是财务真正关心的数;还有,强制给答案。

From the third step up, the model decides when it's finished. So if the job *can't* be finished, nothing stops it — it searches until your provider refuses, you pay for every step, the user sees a spinner. You write the stopping rule yourself, and it's four checks: a step limit; a repeat check — same search twice means it's stuck; a budget in tokens or cents, which at ten million questions a day is the number finance cares about; and a forced answer.

> 第四道是大家最容易漏的。不管因为什么原因停下来,都要再多打一次调用,把已经找到的东西变成一句话:"那家酒店我没找到,不过附近有三家。"停住失控的循环省的是你的钱。强制给出最终答案救的是你的用户。

The fourth is the one people leave out. Whenever you stop, for any reason, make one more call that turns what you found into a sentence: "I couldn't find that hotel, but here are three nearby." Stopping a runaway loop saves your money. Forcing a final answer saves your user.

(滚到 **FIGURE · THREE PARTS, IN ORDER**,指一下颜色说明。)

> 今天所有的图用同一套颜色:**琥珀色,模型在决定;钢蓝色,你的代码在决定。**

One colour code for every diagram today: **amber, a model decides; steel blue, your code decides.**

(滚到 **MECHANISM · PICK A STEP, CLICK THROUGH ITS CALLS, THEN COMPARE ALL FIVE**。这一块是全课的重点,下面大约 15 分钟都在这里。先看上面那个卡片组 **THE AUTONOMY LADDER · PICK A RUNG**。)

> 这里是我们要花真功夫的地方。两样东西上下叠着:五张卡,每级一张,说的是每一级*是什么*;卡片下面,是同一个问题在五级上真跑,一次调用一次调用地看,说的是每一级*做了什么*。卡片快过,跑的部分慢讲。

This is where we spend real time. Two things stacked: five cards, one per rung, saying what each rung *is* — and below them, the same question actually running on all five, one call at a time, showing what each rung *does*. Cards quickly, then the runs slowly.

### 五张卡 · The five cards

(点 **L0 · Prompt → completion**。指卡片右边的六个字段。)

> L0。一次请求,一次回复;世界上什么都没改变。每张卡右边都是同样的六个字段 —— 就靠它们来比较。谁控制下一步:你。交给模型的决定:零。新增的故障方式:答错 —— 这是唯一*可能*出错的地方。什么时候用它:一次就够的时候。这就是 answer box 还不能搜索的时候。

L0. One request, one reply; nothing in the world changes. Every card has the same six fields on the right — that's how you compare them. Who controls the next step: you. Decisions handed to the model: zero. New failure mode: wrong answer — the only thing that *can* go wrong. Reach for it when one shot is enough. The answer box before it could search.

(点 **▶ Animate control flow** 一次,让箭头动一下:you → model → answer。)

> 你写 prompt,模型生成,答案出来。三个框,没有回路。后面每一级都是往这个形状上加东西。

You write the prompt, the model generates, out comes the answer. Three boxes, no loop back. Every rung from here adds something to that shape.

(点 **L1 · Model + tools, one hop**。)

> L1。你给模型一张工具清单;它回一个工具名和参数;你的代码去执行。把这一行画下来:*模型获得的是"够得着",不是"控制权"。* 谁控制下一步:模型挑工具,你决定什么时候停。交出去的决定:一个。新增故障:选错工具、参数畸形 —— L0 只能答错,现在它可以要一些不存在的东西。answer box 第二版:搜一次,然后回答。

L1. You hand the model a list of tools; it replies with a tool name and arguments; your code runs it. Underline this line: *the model has gained reach, not control.* Who controls the next step: the model picks a tool, you decide when to stop. Decisions handed over: one. New failure mode: wrong tool, malformed arguments — at L0 it could only be wrong, now it can ask for nonsense. The answer box, version two: search once, then answer.

(点 **L2 · The agent loop**。指 "first rung where a system can loop forever"。)

> L2。同样的循环,但重复到模型*自己*说完成为止。交出去的决定 —— 读一下 —— *n 次(工具,参数),外加什么时候停。* 最后那一项就是全部的区别。新增故障:无限循环、跑偏、失控的成本。这是模型第一次掌握控制流的一级;也是系统第一次可能永远循环的一级。可以再搜一次的 answer box 就是 L2,每个上线过它的团队都在第一周碰到这个故障。

L2. The same cycle, repeated until the model *itself* says it's finished. Decisions handed over — read it — *n times (tool, args), plus when to stop.* That last item is the whole difference. New failure mode: infinite loops, drift, runaway cost. First rung where the model controls the control flow; first rung where a system can loop forever. The answer box that may search again is L2, and every team that ships one meets this failure in week one.

(点 **L3 · Planning and memory**。)

> L3。先有一个计划步骤,把子任务写下来;再有一个记忆存储,把找到的东西放在对话之外。它买到的 —— 这一行马上就会用到 —— *它不再提前停下来:模型之外有个东西在追踪还没做完的事。* 新增故障:自信地执行一个坏计划,以及过期的记忆。"东京五天"正是这种情况:没有计划,answer box 会把第一天写得很好,然后忘了还有四天。

L3. A planning step writes subtasks down first, and a memory store keeps findings outside the conversation. What it buys — the line that matters in a minute — *it stops stopping early: something outside the model tracks what is still unfinished.* New failure mode: bad plans executed confidently, stale memory. "Five days in Tokyo" is exactly this: without a plan, the answer box writes a great day one and forgets there were four more.

(点 **L4 · Multiple agents**。指 "Something must now decide who speaks next"。)

> L4。职责拆到多个 agent,各有自己的指令和上下文。它买到的:*检查答案的标准,和写答案的标准分开了。* 新增故障:互相踢皮球、成本翻倍。还有最后一行 —— *现在必须有个东西来决定下一个谁说话* —— 那就是第二页。在 answer box 里:一个 writer,一个 checker,checker 在发布前对着帖子核对草稿。

L4. Responsibilities split across agents with their own instructions and context. What it buys: *the standard that checks the answer is separate from the one that wrote it.* New failure mode: ping-pong, multiplied cost. And the last line — *something must now decide who speaks next* — that's page two. In the answer box: a writer, and a checker that reads the draft against the posts before it ships.

> 五张卡,一个规律:每上一级,就多交给模型一种决定,也就多一种出错的方式。新的故障*就是*新交出去的那个决定出了错。

Five cards, one pattern: every step up hands the model one more kind of decision and adds one new way to fail. The new failure *is* the new decision, going wrong.

### 五个 harness · One question, five harnesses

(往下滚到 **ONE QUESTION, FIVE HARNESSES**。指 TASK 那一行,念一遍问题。)

> 现在是同一个想法在跑。任务:"我今天在波士顿,航班晚上八点。我该带外套吗?该提前去机场吗?"一句话里两个问题。整个故事就是:哪几级记得第二个问题。

Now the same idea running. The task: "I'm in Boston today, my flight leaves at 8pm. Should I bring a coat, and should I leave for the airport early?" Two questions in one sentence. The whole story is which rungs remember the second one.

> 布局:左边是*你的代码* —— 这一级真实的 Python,新增的行有高亮。右边是*线上传过去的东西* —— 每一次调用真正发出的 prompt 和收到的回复;箭头一次翻一个调用,标题告诉你现在是第几个、大约多少 token。我会把每一次调用都点一遍。故意慢。

Layout: left, *your code* — the actual Python for that rung, new lines highlighted. Right, *what crossed the wire* — the exact prompt and reply, one call at a time; the arrows step, the header says which call and roughly how many tokens. I'll click through every call. Slow on purpose.

(点 chip **L0 · prompt -> completion**。指左边代码:一行。指右边 CALL 1 / 1 · ≈28 TOK。)

> L0。一行代码:`return ask(QUESTION)`。一次调用,28 个 token,prompt 就是那个问题本身 —— 没有工具清单。回复:"波士顿这个季节通常挺冷,大概带件外套是个好主意。""大概" —— 它在猜,它没法去查任何东西。而机场那个问题干脆消失了。这就是搜索之前的 answer box:自信、模糊,而且只回答你问题里它想回答的那一半。

L0. One line of code: `return ask(QUESTION)`. One call, twenty-eight tokens, and the prompt is just the question — no tools line. Reply: "Boston in this season is usually chilly, so a coat is probably a good idea." "Probably" — it's guessing, it can't look anything up. And the airport question is simply gone. The answer box before search: confident, vague, and it answers the half of your question it feels like answering.

(点 chip **L1 · one tool hop, decided by you**。指左边四行代码,读注释。)

> L1。四行,注释就是故事。带着 SYSTEM —— 工具清单那行 —— 去 ask,*模型挑工具*。用正则把工具名抠出来。跑它 —— *你的代码来跑*。把结果贴进去再 ask 一次,返回 —— *你的代码在这里结束这一轮*。最后这条注释就是 L1 的完整定义。

L1. Four lines, and the comments are the story. Ask with SYSTEM — the tools line — *the model picks a tool*. Pull the name out with a regex. Run it — *your code runs it*. Ask again with the result pasted in, return — *your code ends the turn here*. That last comment is the entire definition of L1.

(右边翻到 CALL 1 / 2 · ≈62 TOK。指 prompt 顶部两行。)

> 调用一,62 个 token。顶上多了两行:工具清单,和协议 —— "回 ACTION 来调一个,或者回 DONE。"回复:`ACTION: get_weather(Boston)`。工具是模型挑的。这就是我们交出去的那一个决定。

Call one, sixty-two tokens. Two new lines at the top: the tools, and the protocol — "reply ACTION to call one, or DONE." Reply: `ACTION: get_weather(Boston)`. The model chose the tool. That's the one decision we handed over.

(▶ 翻到 CALL 2 / 2 · ≈38 TOK。指 prompt:工具清单没了,多了一行 [now: Boston 4C…]。)

> 调用二,38 个 token —— 更小了。看这个 prompt:工具清单*没了*。只有问题,加方括号里的一条事实,"now: Boston 4C"。你的代码决定了模型只拿到一条事实,而且没有再要的机会。回复:"带外套,现在 4 度。"一个真实的温度,不是猜的。机场问题还是没答。够得着,但没有控制权。answer box 第二版:一次搜索,一个答案,结束。

Call two, thirty-eight tokens — smaller. Look at this prompt: the tools line is *gone*. Just the question and one fact in brackets, "now: Boston 4C." Your code decided the model gets one fact and no further chances. Reply: "Wear a coat, it is 4C right now." A real temperature, not a guess. Still no airport. Reach, not control. Answer box version two: one search, one answer, done.

(点 chip **L2 · an agent loop**。指左边代码头:"rewritten since L1"。)

> L2。八行,*相对 L1 重写了* —— 形状不一样了。一个叫 `context` 的列表。一个循环,`for _ in range(6)` —— 先停在这里:这个 6 就是步数上限,第一道栅栏,已经在代码里了。循环里面:带着*整个* context 去 ask;如果是 DONE 就返回;否则跑工具,把回复*和*结果都追加进 context。这个追加就是让它成为 agent 的那一行:对话记录在增长,而模型下一次会看到全部。

L2. Eight lines, *rewritten since L1* — a different shape. A list called `context`. A loop, `for _ in range(6)` — stop there: that six is a step limit, the first fence, already in the code. Inside: ask with the *whole* context; if DONE, return; otherwise run the tool and append *both* the reply and the result to the context. That append is what makes this an agent: the transcript grows, and the model sees all of it next time.

(右边 CALL 1 / 3 · ≈62 TOK。)

> 调用一:和 L1 的第一次一模一样。62 个 token,`get_weather`。

Call one: identical to L1's first call. Sixty-two tokens, `get_weather`.

(▶ CALL 2 / 3 · ≈78 TOK。指 prompt 底部高亮的两行。)

> 调用二,78 个 token。高亮的行是新的:上一轮的 ACTION 和它的结果。而且工具清单*还在* —— 和 L1 不一样,它可以再要。它也真的要了:`get_forecast`。没人叫它要。

Call two, seventy-eight tokens. The highlighted lines are new: last turn's ACTION and its result. And the tools line is *still there* — unlike L1, it may ask again. It does: `get_forecast`. Nobody told it to.

(▶ CALL 3 / 3 · ≈96 TOK。指回复开头的 DONE。)

> 调用三,96 个 token,两条读数都在 prompt 里。回复:DONE —— "带外套,现在 4 度,晚上 1 度,带把伞。"比 L1 好多了。现在看它*没*做的事:`get_traffic` 三次都在清单上。一次都没叫。它答完外套就说 DONE 了。这不是 bug —— 这正是我们在 L2 交给它的那个决定。两个问题:还是 NO。

Call three, ninety-six tokens, both readings in the prompt. Reply: DONE — "wear a coat, 4C now, 1C tonight, take an umbrella." Much better than L1. Now look at what it *didn't* do: `get_traffic` was on the list all three times. Never called. It answered the coat and said DONE. Not a bug — that's the decision we handed it at L2. Both questions: still NO.

> 再看 token:62、78、96。每一次调用都把整段对话重发一遍。对话记录*就是*模型的记忆,而你每一轮都要为全部重新付钱。在 answer box 里,每一次新搜索都会把之前所有的帖子重新发一遍 —— 这就是真实产品要限制搜索次数的原因。

And the tokens: sixty-two, seventy-eight, ninety-six. Every call re-sends the whole conversation. The transcript *is* the model's memory, and you pay for all of it every round. In the answer box, every previous post gets re-sent with every new search — which is why real products cap the number of searches.

(点 chip **L3 · it writes a plan first, and the plan is still there at the end**。指左边代码第一行 ROLE: planner,和 notes 那一行的注释。)

> L3。九行。第一行是新的:单独一次调用,"ROLE: planner,写个计划。"然后是 `notes` —— *找到的东西放在对话记录之外*。再看每一轮发出去的是什么:工具清单、计划、一行 NOTES 带着目前为止找到的全部、还有问题。不是原始的来回对话。是计划,加一份紧凑的事实清单。

L3. Nine lines. Line one is new: a separate call, "ROLE: planner, write a plan." Then `notes` — *findings kept outside the transcript*. And look at what's sent each round: the tools, the plan, a NOTES line with everything found so far, the question. Not the raw back-and-forth. The plan, and a compact list of facts.

(右边 CALL 1 / 5 · ≈55 TOK。指回复的 PLAN。)

> 调用一,55 个 token。回复就是计划:"1) get_weather,2) get_forecast,3) get_traffic,4) 回答外套问题和机场问题两个。"读第四步。这句话马上会在每一次调用里被重发。

Call one, fifty-five tokens. The reply is the plan: "1) get_weather, 2) get_forecast, 3) get_traffic, 4) answer BOTH the coat question and the airport question." Read step four. That sentence is about to be re-sent on every call.

(▶ CALL 2 / 5 · ≈94 TOK。指 prompt 里的 PLAN 行和 "NOTES: (empty)"。)

> 调用二:计划在 prompt 里,NOTES 是空的。回复 `get_weather` —— 计划的第一步。

Call two: the plan is in the prompt, NOTES is empty. Reply `get_weather` — step one of the plan.

(▶ CALL 3 / 5 · ≈101,▶ CALL 4 / 5 · ≈112。指 NOTES 那一行变长,PLAN 不变。)

> 调用三和四。NOTES 在变长 —— 一条读数,两条。PLAN 一字没变。到了调用四:`get_traffic`。L2 从来没要过这个。L3 要了,因为计划说第三步是它,而计划就在它眼前。

Calls three and four. NOTES grows — one reading, two. PLAN doesn't change. And on call four: `get_traffic`. L2 never asked for that. L3 does, because the plan says step three, and the plan is right in front of it.

(▶ CALL 5 / 5 · ≈126 TOK。指回复:两句话。)

> 调用五:DONE,两句话 —— 外套那句,加"早点走,I-90 下午五点后堵,留 70 分钟。"两个问题。YES,第一次。

Call five: DONE, two sentences — the coat sentence, and "leave early, I-90 is heavy after 5pm, allow 70 minutes." Both questions. YES, for the first time.

> 为什么翻转发生在*这里*?模型没有变聪明 —— 每一级都是同一个函数。它在调用一写下的计划,每一次调用都被重新放回它眼前,而计划上写着"两个都要回答"。是模型之外的东西在追踪还没做完的事。这就是"不再提前停下来",在一个 prompt 里的样子。还有,token 涨得比 L2 温和 —— 五次调用从 55 涨到 126 —— 因为 NOTES 是紧凑的清单,不是原始对话。这就是"记忆放在上下文之外"用钱衡量的好处。

Why did the flip happen *here*? The model didn't get smarter — same function on every rung. The plan it wrote at call one was put back in front of it on every call, and the plan said "answer BOTH." Something outside the model is tracking what's unfinished. That's *it stops stopping early*, in a prompt. And the tokens grow more gently than L2's — fifty-five up to a hundred and twenty-six over five calls — because NOTES is a compact list, not the raw transcript. That's what memory outside the context buys you in money.

(点 chip **L4 · a second reader with a different standard**。指代码头 "every line is new"。指第二行的元组:("weather", WEATHER_TOOLS), ("logistics", TRAFFIC_TOOLS)。)

> L4。十五行,*每一行都是新的*。第二行:两个角色,各自有一张*不同的*工具清单 —— weather 拿天气和预报,logistics 只拿路况。各自循环到 DONE,把找到的事实放进一个共享列表。然后最多三轮:advice 写草稿,critic 评判,APPROVED 就返回,否则把结论退回给 writer。

L4. Fifteen lines, *every line is new*. Second line: two roles, each with a *different* tools line — weather gets weather and forecast, logistics gets traffic only. Each loops until DONE and adds its facts to a shared list. Then at most three rounds of: advice writes a draft, critic judges, APPROVED returns, otherwise the verdict goes back to the writer.

(右边 CALL 1 / 9 · ≈61 TOK。指 prompt 第一行 "ROLE: weather" 和工具清单只有两个。)

> 调用一。"ROLE: weather",两个工具,不是三个。这个 agent *要不到*路况 —— 因为清单上没有。这就是工具边界,在干真活。

Call one. "ROLE: weather," and two tools, not three. This agent *cannot* ask for traffic — it isn't on the line. The tool boundary, doing real work.

(▶ 翻 CALL 2、3。指调用 3 的回复 "DONE: readings collected."。)

> 调用二和三:两条读数,然后"DONE:读数收集完毕。"它不回答问题。收集就是它的全部工作。

Calls two and three: two readings, then "DONE: readings collected." It doesn't answer the question. Collecting is its whole job.

(▶ CALL 4 / 9 · ≈76,CALL 5 / 9 · ≈89。指 "ROLE: logistics" 和只有一个工具。)

> 调用四和五:"ROLE: logistics",一个工具。路况,DONE。共享列表里有了三条事实,而没有任何一个 agent 被允许把三条全取到。

Calls four and five: "ROLE: logistics," one tool. Traffic, DONE. Three facts in the shared list, and no single agent was allowed to fetch all three.

(▶ CALL 6 / 9 · ≈64 TOK。指 "ROLE: advice",prompt 里没有工具清单,只有问题和三条事实。指回复只有外套那句。)

> 调用六。"ROLE: advice"。没有工具清单 —— 它只能写。它拿到问题和三条事实,写出的草稿是:外套那句。只有外套那句,而路况那条事实就摆在它的 prompt 里。

Call six. "ROLE: advice." No tools line — it can only write. It gets the question and the three facts, and drafts: the coat sentence. Only the coat sentence, with the traffic fact sitting right there in its prompt.

(▶ CALL 7 / 9 · ≈26 TOK。指 prompt 只有两行:ROLE: critic 和 DRAFT。指回复 RETRY。)

> 调用七。"ROLE: critic. DRAFT:"加上草稿。整个 prompt 就这些 —— 26 个 token,页面上最小的一次调用。没有事实,没有推理,只有草稿,和一个问题:整件事都答了吗?回复:"RETRY —— 草稿回答了外套问题,没回答机场问题。"writer 没有在找不满意的理由。critic 在找。

Call seven. "ROLE: critic. DRAFT:" and the draft. That's the whole prompt — twenty-six tokens, the smallest call on the page. No facts, no reasoning, just the draft, and one question: was the whole thing answered? Reply: "RETRY — the draft answers the coat question but not the airport question." The writer wasn't looking for reasons to be unsatisfied. The critic was.

(▶ CALL 8 / 9 · ≈82 TOK。指 prompt 底部追加的 RETRY 那一行,指回复变成两句话。)

> 调用八:writer 再来,同样的 prompt,底部多了那条 RETRY。这次两句话都有了。

Call eight: the writer again, same prompt plus the RETRY at the bottom. Now both sentences.

(▶ CALL 9 / 9 · ≈42 TOK。指回复 APPROVED。)

> 调用九:APPROVED。九次调用,两个问题:YES。

Call nine: APPROVED. Nine calls, both questions: YES.

> L4 买到两样东西,你刚才两样都看到了:每个角色一道工具边界;检查的标准和写作的标准分开。在 answer box 里,checker 看到的是草稿和引用的帖子 —— 不是 writer 的推理 —— 所以它评判的是答案,不是论证。

L4 bought two things and you watched both: a tool boundary per role, and a checking standard separate from the writing standard. In the answer box, the checker is shown the draft and the cited posts — not the writer's reasoning — so it judges the answer, not the argument.

### 五个一起比 · Compare all five

(点右上角 **compare all five**,让表格显示出来。如果表格已经在,就直接指。)

> 表。模型调用:1、2、3、5、9。token:28、100、236、488、590。代码行数:1、4、8、9、15。两个问题都答了:NO、NO、NO、YES、YES。

The table. Model calls: one, two, three, five, nine. Tokens: twenty-eight, a hundred, two thirty-six, four eighty-eight, five ninety. Lines of code: one, four, eight, nine, fifteen. Both questions answered: NO, NO, NO, YES, YES.

> 三种读法。一:翻转在 L2 和 L3 之间,而你现在确切知道为什么 —— 不是模型更聪明,是一个每次调用都重发、写着"两个都答"的计划。整个阶梯的论点,就在这一行里。

Three readings. One: the flip is between L2 and L3, and you now know exactly why — not a smarter model, a plan re-sent on every call saying "answer both." That's the whole argument for the ladder in one row.

> 二:每上一级,调用更多、代码更多,每次都是。你在买一种能力,付出的是调用次数、你要维护的代码行、和新的出错方式。

Two: every step up costs more calls and more code, every time. You're buying a capability and paying in calls, in lines you maintain, and in new ways to fail.

> 三 —— 最容易漏掉的一条。L3 到 L4:调用几乎翻倍,5 到 9,但 token 只从 488 涨到 590。因为 L4 的每个 agent 看到的*更少* —— critic 只看草稿,别的什么都不看,26 个 token。缩小一个 agent 能看到的范围,就缩小了每次调用的开销。第二页记得这一点。

Three — the one people miss. L3 to L4: calls nearly double, five to nine, but tokens only go four eighty-eight to five ninety. Because every L4 agent sees *less* — the critic sees a draft and nothing else, twenty-six tokens. Narrow what an agent can see and you narrow what each call costs. Remember that on page two.

> 所以当有人说"我们把这个做成 agentic 的吧",有用的回答是:哪一级?挑能真正解决问题的最低那一级。这就是本事。

So when someone says "let's make this agentic," the useful reply is: which rung? Pick the lowest one that actually solves the problem. That's the skill.

(滚到底部 **ACCEPTANCE**。点 **Accept & record evidence**。左栏 00 打勾。)

*如果时间不够:五张卡只点 L0、L2、L4;五个 harness 里 L1 只看调用 2(工具清单消失),L4 只看调用 6、7、8(草稿→RETRY→重写)。表格三种读法保留。*

---

## Part II · Routing: who speaks next · 10 分钟

(点左栏 **01 Routing: who speaks next**。停在 lede。)

> 把一件事拆给几个模型做,会制造一个你以前没有的问题:每一条消息之后,得有个东西来挑下一个谁说话。挑错了,两个 agent 就会把活儿推来推去,直到某个上限把它们停下。一分钟后我们在真 AutoGen 里看这件事发生。

Splitting a job across several models creates a problem you didn't have before: after every message, something has to pick who talks next. Get it wrong and two agents hand work back and forth until a limit stops them. We'll watch that happen in real AutoGen in a minute.

(滚到 **First: why use more than one model at all?**)

> 四个好理由,每一个在 answer box 里都有对应。两个互相拉扯的任务 —— 一个乐于助人的 writer 和一个专挑毛病的 checker;放在一个 prompt 里,你得到一个温吞的答案,温吞地批评自己。不同的 agent 看到不同的东西 —— 只给 checker 看答案和帖子,它评判的就是答案,不是推理。不同角色不同工具 —— 一个能搜,另一个能发布,靠工具清单强制执行。还有可以并行的独立工作 —— "东京美食"和"东京酒店"同时搜。

Four good reasons, each with a face in the answer box. Two jobs that pull against each other — a helpful writer and a fault-finding checker; in one prompt you get a mild answer that mildly criticises itself. Different things visible to different agents — show the checker only the answer and the posts, and it judges the answer, not the reasoning. Different tools per role — one can search, another can publish, enforced by the tool list. And independent work in parallel — "Tokyo food" and "Tokyo hotels" at once.

> 还有一个坏理由,也是最常见的:把本来就不能分开的步骤硬拆开。如果各块需要看到彼此的工作才说得通,你不是分解了任务,你只是加了交接。

And one bad reason, the common one: splitting steps that were never separate. If the pieces need each other's work to make sense, you've added handovers, not divided the task.

(滚到 **Then: something has to pick who talks next**。)

> dispatcher 在每条消息之后挑下一个说话的人。做它有三种办法。让模型选:能用,但每一轮之前都要多一次模型调用 —— 而这些调用不产生任何消息,所以只有账单能看到它们。写死规则:免费、可测试,但它会对"东京现在几点"也跑一遍 checker。或者规则优先,规则管不了的地方才问模型。

The dispatcher picks the next speaker after every message. Three ways to build one. Let the model choose: works, but costs a model call before every turn — and those calls produce no message, so only the bill shows them. Fixed rules: free and testable, but it'll run the checker on "what time is it in Tokyo." Or rules first, and the model only where the rules run out.

> 在 AutoGen 里这是两个函数加一个 prompt,按顺序来。`candidate_func` 先缩小谁有资格。`selector_func` —— 规则能不能直接定?返回一个名字,就不会有模型调用;返回 None,问题往下传。只有到这时才轮到 selector prompt:模型拿到一个很小的问题,两个名字和一条写好的规则。

In AutoGen that's two functions and a prompt, in order. `candidate_func` narrows who's even allowed. `selector_func` — can a rule decide? Return a name and no model call happens; return None and the question moves on. Only then the selector prompt: a model gets a small question, two names and a written rule.

> 在 answer box 里:如果草稿提到了价格、医疗或安全方面的说法,送给 checker;否则直接发布。一行规则,处理掉大部分流量;只有规则分不清的问题才去问模型。我们马上就来数一数这省了多少。

In the answer box: if the draft mentions a price, a medical or a safety claim, send it to the checker; otherwise publish. One line, handles most traffic; the model is only asked what the rule can't classify. We're about to count what that saves.

(滚到 **FIGURE · THREE CHECKS, STRICTEST FIRST**。指一下三层。)

> 三道检查,最严格的在前。两道免费而且确定;第三道每次运行都花钱。最后才问模型。

Three checks, strictest first. Two are free and deterministic; the third costs money every time. Ask the model last.

(滚到 **Four ways to wire a team, and who decides the order**。四张卡。)

> 四种标准形状,一个问题就能把它们分开:**谁决定顺序?** 三种在你写程序的时候决定一次。最后一种每一轮都重新决定。

Four standard shapes, one question tells them apart: **who decides the order?** Three answer it once, when you write the program. The last answers it again on every turn.

> Pipeline:A、B、C,写在源码里 —— 这就是 answer box 本身,检索、重排、生成。Manager 和 workers:deep research 类产品;Anthropic 公布过自家的价格,大约是普通聊天 token 的十五倍,而单个 agent 是四倍。Round-robin:每个人轮流说,没人决定 —— 两个成员的时候就是 writer 和 critic 的循环。Dispatcher:每条消息之后有个东西来选。把下面两张卡并排看 —— 同样的 agent、同样的共享 transcript、同样的箭头。唯一的差别是底下那个框,和一根虚线箭头:selector 在选之前要*读*一遍 transcript,而 rotation 什么都不读。那一次读,就是你付钱的 routing call。这是 FlightFinder 的形状。

Pipeline: A, B, C, in the source — that's literally the answer box, retrieve, rerank, generate. Manager and workers: deep-research products; Anthropic published the price of theirs, about fifteen times the tokens of a plain chat against four for a single agent. Round-robin: everyone speaks in turn, nobody decides — with two members it's the writer-and-critic loop. Dispatcher: something chooses after every message. Look at the two bottom cards side by side — same agents, same shared transcript, same arrows. The only differences are the box at the bottom, and one dashed arrow: the selector *reads* the transcript before it chooses, and the rotation reads nothing. That read is the routing call you pay for. FlightFinder's shape.

(指卡片下面那段 **14×** 的说明。)

> 卡片下面那段说明:四个 agent 的 round-robin 比最便宜的形状贵十四倍,因为每一轮所有人都说话、都重读整个对话记录。两个 agent 加一个停止条件的时候,它反而是最便宜的。代价不在形状本身;在于这个形状让多少个 agent 开口。

The note under the cards: round-robin with four agents costs fourteen times the cheapest shape, because everyone speaks every round and re-reads the whole transcript. With two agents and a stop condition it's the cheapest thing there is. The cost isn't in the shape; it's in how many agents the shape makes speak.

(滚到 **Two of AutoGen's own examples, running**。看到 **REAL RUN** 那个绿条。)

> 两个例子直接来自 AutoGen 的文档。绿条:真的 AutoGen,真的终止条件,真的工具调用。只有模型是固定的脚本。

Two examples straight from AutoGen's docs. Green bar: real AutoGen, real terminations, real tool calls. Only the model is a fixed script.

(确认在 **RoundRobinGroupChat · Round-robin** 标签。第一个 chip **the critic approves, and the run ends**。用 ▶ 翻 4 步,指着中间的 **ROUTING CALLS** 计数器。)

> 诗:writer、critic,轮流,直到 critic 打出 APPROVE。一步步翻,盯着中间那个计数器 —— 它一直不动。零次路由调用,因为从来没有谁在选。这个设计里剩下的唯一决定,是什么时候停。

The poem: writer, critic, alternating until the critic types APPROVE. Step through and watch the middle counter — it never moves. Zero routing calls, because nothing ever chooses. The only decision left in this design is when to stop.

(点第二个 chip **the same pair, with a critic that is never satisfied**。翻到最后,STEP 8 / 8。指最后一条消息。)

> 同样的一对,换一个永远不满意的 critic。翻到最后:八轮,被消息上限截停,最后一行是 critic 在抱怨。没人把诗交给用户。这就是 answer box 一直在"改进"草稿,直到请求超时。停止规则必须是你写的 —— 而且它必须以一个答案结束,而不只是结束。

Same pair, a critic that's never satisfied. Step to the end: eight turns, stopped by a message limit, and the last line is the critic complaining. Nobody handed the user a poem. That's the answer box "improving" its draft until the request times out. The stopping rule has to be yours — and it has to end with an answer, not just an ending.

(点上面的标签 **SelectorGroupChat · Dispatcher**。第一个 chip **as the docs first show it - a model picks every time**。)

> 篮球问题:2006–07 赛季热火队谁得分最多,后来他的篮板怎么变的?你得先找到这个球员,才能去查他的篮板,所以固定顺序做不到 —— 每条消息之后必须有东西来选。在 answer box 里:"那条爆款帖子里的餐厅还开着吗,附近有什么?"第二次搜索取决于第一次。

The basketball question: who scored most for the Heat in 2006–07, and how did his rebounds change later? You have to find the player before you can look up his rebounds, so no fixed order works — something must choose after every message. In the answer box: "is the restaurant in that viral post still open, and what's near it?" The second search depends on the first.

(不逐步翻。用 ▶ 快速跳到最后一步,指 **ROUTING CALLS** 终值 9 和 **MODEL CALLS, TOTAL** 18;顺手指一下对话里的 85.98。)

> 没有规则,所以每条消息之后都问一次模型:九轮 agent 发言,九次路由调用,十八次模型调用。对话里那个 85.98,是真的 Python 算出来的,不是模型写的。

No rules, so a model is asked after every message: nine agent turns, nine routing calls, eighteen model calls. And that 85.98 in the conversation was computed by real Python, not written by a model.

(点第二个 chip **plus the one-line selector_func from the docs**。指左边代码面板里高亮的那一行,再指 **ROUTING CALLS** 终值 4。)

> 现在加四行 Python —— AutoGen 自己的 `selector_func`:如果上一个说话的不是 planner,就回到 planner。同样的问题,同样的 agent。agent 轮数:两边都是九。路由调用:九,然后是**四**。一半以上的"下一个谁"本来就有显而易见的答案,一旦写下来,就不用再问模型。翻几步,代码面板每一次都会告诉你,是规则定的还是模型定的。

Now four lines of Python — AutoGen's own `selector_func`: if the last speaker wasn't the planner, go back to the planner. Same question, same agents. Agent turns: nine either way. Routing calls: nine, then **four**. More than half the "who's next" questions had an obvious answer, and once it's written down, no model is asked. Step through a few and the code panel tells you, each time, whether a rule or a model decided.

> 代码回答它能回答的;模型只拿到那个悬而未决的问题 —— 下一个子任务需要哪个专家。一个问题省五次调用不算什么。一天一千万个问题,那就是账上的一行。

Code answers what it can; the model gets only the open question — which specialist the next subtask needs. Five saved calls on one question is nothing. On ten million questions a day it's a line item.

(滚到底部,点 **Accept & record evidence**。)

*如果时间不够:四张形状卡只念 pipeline 和 dispatcher 两张;诗的第一个 chip 不翻,直接看第二个的结尾。*

---

## Part III · FlightFinder Pro · 11 分钟

(点左栏 **02 FlightFinder Pro**。停在顶部的流水线条 **WHERE YOU ARE**。)

> 一个真实的应用 —— 把它当成机票版的 answer box 来读。一句话进去,一份校验过的报告出来。看这条流水线:`query_parser` 是查询理解;fan-out plan 是代码在决定跑几次搜索,一到三次;`search_flights` 是检索,只不过取的是 Kayak 页面而不是帖子;`extractors` 读取回来的内容,一个日期一个;`merge_ranker` 重排;`budget_critic` 是 checker;`summarizer` 按固定格式写答案,因为 UI 是用字段来渲染卡片的。琥珀色是模型,钢蓝色是代码。

A real application — read it as the answer box for flights. One sentence in, a validated report out. The strip: `query_parser` is query understanding; the fan-out plan is code deciding how many searches to run, one to three; `search_flights` is retrieval, a Kayak page instead of posts; `extractors` read what came back, one per date; `merge_ranker` reranks; `budget_critic` is the checker; `summarizer` writes the answer in a fixed shape, because the UI renders cards from fields. Amber is a model, steel is code.

(滚到 **Two points where a model is asked how to proceed**。)

> 这个系统只在两个点上问模型"接下来怎么办"。第一:用户的措辞允许哪些日期?—— 一个偏好日,如果措辞是松的,再加一个窗口:"early November" 变成 1 号到 7 号。第二:排好序之后,候选要不要再看一眼?—— 走 critic,还是直接总结。critic 的结论也会影响流程,但没有模型对它采取行动:一条规则读它的第一个词 —— APPROVED、RETRY、NO_DATA —— 一个"最多重试一次"的上限决定能持续多久。其他一切都是确定性代码。它之所以能自适应,是因为几个小小的判断被接进了一套能执行、能守护、能测试、能计价的机器里。

This system asks a model how to proceed at exactly two points. One: what dates does the user's wording allow? — a preferred date, and if the wording is loose, a window: "early November" becomes the 1st to the 7th. Two: once ranked, do the candidates need a second look? — critic, or straight to the summary. The critic's verdict also steers the run, but no model acts on it: a rule reads its first word — APPROVED, RETRY, NO_DATA — and a cap of one retry decides how long. Everything else is deterministic code. It's adaptive because a few small judgements are wired into machinery that can act on them, guard them, test them and price them.

> 而最清楚的证据是那个*不存在*的东西:在整个代码库里搜 `tools=`,一个都没有。没有任何 agent 被交给工具;Python 去抓取,再把文本递过去。模型从来不决定*要不要*搜。answer box 里也一样:检索是流水线的一个阶段,不是模型可调可不调的工具。

And the clearest evidence is what's *missing*: search the codebase for `tools=` and you find nothing. No agent is handed a tool; Python fetches and hands the text over. The model never decides *whether* to search. Same in the answer box: retrieval is a pipeline stage, not a tool the model may or may not call.

(滚到 **The model gets an opinion; code keeps the veto**。)

> 模型有意见;代码有否决权。一个七天的窗口可能意味着七次浏览器会话,而浏览器会话是这个程序里最贵的东西。所以窗口交给 `plan_search_dates`,由代码决定:最多留三个日期 —— 第一天、最后一天、偏好日;已经过去的日期一律丢掉;如果模型交回来的根本不是日期,就只搜一次、不扇出。模型说的是用户能接受什么。代码决定的是公司愿意为什么付钱。

The model gets an opinion; code keeps the veto. A seven-day window could mean seven browser sessions, and a browser session is the most expensive thing this program does. So the window goes into `plan_search_dates`, and code decides: keep at most three dates — the first, the last, the preferred one; drop any date already in the past; and if the model handed back something that isn't a date, one search, no fan-out. The model said what the user would accept. Code decided what the company will pay for.

(滚过 **Three panels, three kinds of evidence**,不停。)

> 三种证据的说明页面上写着,不念;每块面板到了再一句话说明。

(滚到表格 **EVERYTHING IN THIS APPLICATION, AND WHERE YOU MET IT**。点第二行 **Tools, and who may call them**。)

> 十三个部件,第三列告诉你在哪里见过每一个 —— 其中八个在前面两页。"Tools, and who may call them":就是 `tools=` 那一点,在代码库里。

Thirteen parts, and the third column says where you met each one — eight of them on the two pages before this. "Tools, and who may call them": the `tools=` point, in the codebase.

(点 **Guards and termination** 行,让大家看展开文字。)

> "Guards and termination":第一页四道栅栏里的三道在同一个文件里,`fanout.py` 里还多一道 —— `MAX_SEARCH_DATES = 3`,浏览器会话数的上限。说明也写了仍然缺的是哪一道:没有 token 预算。成本会被报告出来;但没有任何东西因为超支而停下一次运行。一个真实的缺口,而且你能看见它。

"Guards and termination": three of page one's four fences in one file, plus one more in `fanout.py` — `MAX_SEARCH_DATES = 3`, the cap on browser sessions. And the note says which fence is still missing: no token budget. The cost is reported; nothing stops a run for exceeding it. A real gap, and you can see it.

(滚到 **CHANGE ONE THING, MEASURE WHAT MOVED**。)

> 对照组:真实的 team 离线跑,模型回复是脚本化的,每一组只改一个输入 —— 因为单跑一次只能告诉你系统能用,说明不了任何一个部件是干什么的。琥珀色标出变动的地方。

The comparisons: the real team run offline with scripted model replies, and each one changes exactly one input — because a single run tells you the system works, not what any part is *for*. Amber marks what moved.

(点 **E** 展开。)

> E。三行都是 flexible;变的只有日期和它的窗口。一个在未来的七天窗口:代码把它采样成三个会话 —— 第一天、偏好日、最后一天。一个三天窗口,其中两天已经过去:裁成一个会话。"Nov 5" —— parser 本该把它转成 ISO 日期,在这个假设场景里没转,原始字符串直接到了代码手里:一个会话,不会在一个解析不了的字符串上扇出。同样的模型判断,三种结果。

E. Flexible in all three rows; only the date and its window change. A seven-day window in the future: code sampled it down to three sessions — first day, preferred day, last day. A three-day window with two days already gone: clipped to one session. "Nov 5" — the parser was supposed to turn that into an ISO date and, in this what-if, did not, so the raw string reached the code: one session, no fan-out on a string it can't parse. Same model judgement, three outcomes.

(点 **B** 展开。指 tokens 832 → 590 和 "who spoke" 两列。)

> B。只改一个从句:有没有预算。有:ranker、critic、summarizer。没有:ranker、summarizer。整个审核轮消失了 —— 少一次调用,token 少百分之二十七 —— 而没有人写过一个 `if`。是 dispatcher 读了请求。在 answer box 里:问题提到价格,checker 就跑;"天气怎么样",就不跑。

B. One clause changes: is there a budget. With one: ranker, critic, summarizer. Without: ranker, summarizer. The review round vanished — one fewer call, twenty-seven percent fewer tokens — and nobody wrote an `if`. The dispatcher read the request. In the answer box: the question mentions a price, the checker runs; "what's the weather," it doesn't.

(点 **C** 展开。指 agent turns 3 → 5,tokens 832 → 1,583,within_budget true → false。)

> C。两百对九十。不可能的预算买到一次重排,然后上限把它截断:五轮而不是三轮,将近两倍的 token,而它仍然返回找到的最便宜的票价,带着 `within_budget = false`。不是空的,不是循环 —— 这就是第一页那个"强制给出最终答案",在生产环境里。

C. Two hundred against ninety. The impossible budget buys one rerank before the cap cuts it: five turns instead of three, nearly twice the tokens, and it still returns the cheapest fare with `within_budget = false`. Not empty, not a loop — the forced final answer from page one, in production.

(点 **D** 展开。指"who spoke"两列完全一样是灰的,只有 options 1 → 0 是琥珀。)

> D,最值得盯着看的一组。两条路径完全一样 —— 同样的路由,同样的调用。变的是内容:NO_DATA 不是 RETRY,所以报告里是**零**个选项,而不是一班编出来的航班。在 answer box 里,这就是"我没找到相关帖子"和一段凭空编出来的自信文字的区别。同一条流水线;唯一的区别是系统能不能说它什么都没找到。

D, the one to look at hardest. The two paths are identical — same routing, same calls. What changed is the content: NO_DATA is not RETRY, so the report carries **zero** options rather than an invented flight. In the answer box, that's "I found no posts about this" versus a confident paragraph made from nothing. Same pipeline; the only difference is whether the system may say it found nothing.

(滚到 **THE SAME PROGRAM, AGAINST REAL KAYAK AND A REAL MODEL**。指来源说明和 5 行汇总表。)

> 现在什么都不替换了:真的 Kayak 页面,`gpt-4o-mini` 回答每一个 prompt,五次运行,每个数字都从程序自己的输出里读出来。把 token 那一列对着第一列看:七天的窗口花了一万六千 token,固定日期不到七千。扇出的宽度就是账单。

Now nothing stubbed: real Kayak pages, `gpt-4o-mini` answering every prompt, five runs, every number read from the program's own output. Read the tokens column against the first column: the seven-day window cost sixteen thousand tokens, the fixed date under seven thousand. The width of the fan-out is the bill.

(点 **L1** 展开。指 "what the code planned" 和 "what Kayak sent back" 两行。)

> L1。模型把 "early November" 读成 1 号到 7 号 —— 七天。代码留了三个:1 号、4 号、7 号。三个浏览器会话同时开,三个真实页面 —— 第一个一万四千字符、八十个价格标记。三个 extractor,一次合并,报告里每个选项都写着它属于哪一天。光第二阶段就九千多 token。钱就花在这儿,所以扇出的宽度是代码里的常量,不是模型的选择。再看路由那一行:一千三百个 token,只为了规则留给模型的那一次说话人选择。第二页那笔看不见的账单,出现在了一次真实运行里。

L1. The model read "early November" as the first to the seventh — seven days. Code kept three: the first, the fourth, the seventh. Three browser sessions at once, three real pages — fourteen thousand characters, eighty price markers on the first. Three extractors, one merge, and every option in the report says which day it belongs to. Stage two alone: over nine thousand tokens. That's where the money goes, and that's why the width is a constant in the code and not a model's choice. And the routing row: thirteen hundred tokens for the one speaker choice the rules left to a model. The invisible bill from page two, on a real run.

(点 **L2** 展开。指 "what the parser returned" 和 "what the code planned" 两行。)

> L2。"今天或明天;这周早些时候也行。"模型给的窗口从昨天开始。代码在任何人为它花掉一个浏览器会话之前就把昨天丢了,跑了两个,结果更便宜的票在明天 —— 348 美元,报告也这么写了。没说预算,所以 dispatcher 跳过了 critic。这就是对照 E 里的裁剪,发生在真实的日期和真实的页面上。模型有意见;代码有否决权。

L2. "Today or tomorrow; earlier this week would also have been fine." The model gave a window that started yesterday. Code dropped yesterday before anyone spent a browser session on it, ran two, and the cheaper fare turned out to be tomorrow's — three forty-eight, and the report says so. No budget was stated, so the dispatcher skipped the critic. That's the clip from comparison E, on a real date and a real page. The model has an opinion; the code keeps the veto.

(滚到底部 **MAIN_ADVANCED.PY, PORTED TO RUN IN THIS PAGE**。指绿色说明条。)

> 最后一块面板,留给你们自己玩:逻辑逐行移植进了页面,模型用替身,数据是合成的。是用来看机制怎么动的,不是用来测量的。

Last panel, for you to play with: the logic ported line for line into the page, stand-ins for the model, synthetic data. For seeing the mechanism move, not for measuring.

(先点第一个预设 **early November, flexible + $200**,点 **▶ Run**,指控制台 "code planned 3 search paths" 和三个 [Strategy] 标签。再点最后一个预设 **the window is already behind us**,点 **▶ Run**,指 **[note]** 行。)

> 第一个预设:early November,一个七天的窗口。看控制台 —— "code planned 3 search paths",然后是三个带标签的策略:第一天、偏好日、最后一天。模型说七天;代码只为三天付钱。再看最后一个预设:日期是今天,窗口大部分已经过去。"[note] Flexible-date planning produced one usable date."这句话不是模型写的。代码把过去的日子从窗口里裁掉,发现只剩一天。一次搜索而不是三次,用户照样拿到航班。这就是否决权,你刚刚看着它触发了两次。

First preset: early November, a seven-day window. Watch the console — "code planned 3 search paths," then three labelled strategies, first day, preferred day, last day. The model said seven days; code paid for three. Now the last preset: the date is today and the window is mostly behind us. "[note] Flexible-date planning produced one usable date." No model wrote that. Code clipped the past off the window and found one day left. One search instead of three, and the user still gets flights. That's the veto, and you just watched it fire twice.

(滚到底部,点 **Accept & record evidence**。左栏三个都打勾,进度 3 / 3。)

*如果时间不够:对照只开 B 和 D;真跑只开 L1。*

---

## 收尾 · 1 分钟

(回到左栏 **00**,停在 THE IDEA 那段黄框。)

> 一个问题,三页。哪些决定是模型做的,哪些是你的代码做的?当有不止一个模型的时候,谁来决定下一个谁说话 —— 而在你为一次调用付钱之前,规则能不能先回答?还有一个真实系统:模型只在两个点上被问到,其余的全是你能测试的代码。

One question, three pages. Which decisions does the model make, and which does your code? When there's more than one model, who decides who speaks next — and can a rule answer before you pay for a call? And a real system where a model is asked at exactly two points, and everything else is code you can test.

> 再说回 answer box。下次你往里面打字的时候,你知道背后是什么了:一个 parser,一次由代码而不是模型执行的检索,一个 ranker,也许还有一个 checker —— 如果规则说需要的话,一条某人写下的停止规则,一个让你永远看不到转圈的强制最终答案,以及每一次调用的账单,包括那些看不见的。每一处都是有人做了决定的地方:模型,还是代码。现在你可以问他们是哪个。

And the answer box. Next time you type into one, you know what's behind it: a parser, retrieval that code runs, a ranker, maybe a checker if a rule said so, a stopping rule someone wrote, a forced final answer so you never see a spinner, and a bill for every call including the invisible ones. Every one is a place where someone decided: model, or code. Now you can ask them which.

> 这一小时就到这里。谢谢大家。

That's the hour. Thank you.

---

## 备查:稿子里出现的每个数字,页面上在哪

| 数字 | 页面位置 | 来源 |
|---|---|---|
| 1·2·3·5·9 次调用;1·4·8·9·15 行;NO·NO·NO·YES·YES | 00 · ONE QUESTION, FIVE HARNESSES 表格 | `d00_ladder.py` 实跑,本地确定性模型(页面内嵌其输出;脚本不在仓库里) |
| 诗:4 轮 / 0 路由;永不满意:8 轮 | 01 · RoundRobinGroupChat 两个 chip | 真 AutoGen,脚本模型 |
| 篮球:9 轮;路由 9 → 4;模型调用 18 → 13;85.98% | 01 · SelectorGroupChat 两个 chip | 真 AutoGen,真 Python 工具 |
| round-robin 14× | 01 · 四张卡下面的说明 | `d07_topology_cost.py`,4 字符/token 估算(页面内嵌其输出;脚本不在仓库里) |
| Anthropic 4× / 15× | 01 · Manager and workers 卡 "SEEN IN" | Anthropic 工程博客原文 |
| B:3 → 2 轮,888 → 646 token(−27%) | 02 · 对照 B | `flightfinder/examples/run_comparisons.py`,真 AutoGen 离线 |
| C:3 → 5 轮,888 → 1,673 token | 02 · 对照 C | 同上 |
| D:路径相同,options 1 → 0 | 02 · 对照 D | 同上 |
| L1:窗口 11-01→11-07,规划 3 个日期;14,025 字符 / 80 价格标记;9,324 token 在第二阶段;16,096 总,1,327 路由 | 02 · 真跑 L1 | `flightfinder/main_advanced.py` 真跑 stdout,存在 `examples/live_runs.json` |
| L2:窗口 09-07→09-09 裁成 2 个日期;最便宜 $348 在明天;11,640 token | 02 · 真跑 L2 | 同上 |
