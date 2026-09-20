# WAR Has Changed: A New Way to Measure Wins Above Replacement

[image](https://tdxnsmiepqkbfpbcemdt.supabase.co/functions/v1/article-image?path=authors%2F1787503133987-uor0em.jpg)**Scott Connor**·19 de setembro de 2026·25 min read

**svgShare**

Recently, the [**WAR Machine**](https://www.ddfantasyfootball.com/articles/www.ddfantasyfootball.com/war/sleeper) at DD Fantasy Football changed.

If you have synced one of your leagues and opened the tool, you may not have noticed much at first. The tool itself looks familiar. The buttons are the same. The displays are the same. The options you are used to seeing are still there. You can sync your league, account for the number of teams, starting requirements and scoring settings, and see how WAR changes within the context of your specific format.

But underneath the hood, something significant has changed. More importantly, the core calculation of how we measure WAR has changed.

And before getting into exactly what changed, I want to make something clear because I think it is important context for everything that follows: this is a different way of calculating fantasy football WAR. There are other WAR models in the fantasy space, there are other versions of value above replacement, and there are other tools attempting to quantify how individual players contribute toward winning fantasy football matchups. But this iteration of WAR at DD Fantasy Football is intentionally built differently. We are calculating WAR on a weekly basis, connecting it directly to the replacement levels created by your actual league format, separating the WAR a player makes available from the WAR your fantasy team actually captures, and allowing negative WAR to affect your team only when you actually put that performance into your starting lineup.

To my knowledge, I am not aware of another publicly available fantasy football WAR tool applying this exact combination of weekly replacement value, a weekly zero floor for available player WAR, and positive or negative captured WAR based on actual lineup decisions. If somebody else ultimately approaches it similarly, that's great. The important point is that we are not trying to recreate somebody else's formula or make our number line up with an existing WAR model. We are building our own iteration of WAR around the way we believe dynasty fantasy football is actually played.

That last part is the key. Fantasy football is not played as one giant 17-week matchup. We don't submit one lineup in September and add up everything in January. We make lineup decisions every week. We have starters. We have benches. We have players who are automatic starts. We have players who become useful because somebody gets hurt. We have players who score 28 points on our bench and then seven points the following week when we finally put them into our lineup. We have depth that matters enormously even though it isn't scoring points for us today, and we have expensive dynasty assets that can create surprisingly little weekly advantage because of the position they play and the replacement options available to us.

The more I worked with our new Lineup Optimizer, the more I wanted WAR to reflect those realities. The Lineup Optimizer is trying to tell us how we should optimally allocate resources across a fantasy starting lineup. If WAR is supposed to tell us how much value those players create above replacement, those two tools should correlate. They should be speaking the same language. They should be looking at the same starting requirements, the same positional demand and the same scoring environment. The old WAR calculation didn't always do that as cleanly as I wanted. So we changed it. And I think the easiest place to start is by going all the way back to the beginning and talking about what WAR actually means.

## What Is WAR?

WAR stands for Wins Above Replacement.

At its core, WAR is attempting to answer a pretty simple question: How much value does a player provide compared with the replacement-level player who could occupy that same starting spot? The concept isn't unique to fantasy football. But translating it into fantasy football creates some interesting problems because replacement value is not universal.

There isn't one RB25, WR37 or QB13 that is automatically replacement level in every dynasty league. Your league creates replacement value. Start by looking at your lineup requirements.

Let's say you play in a 12-team league that requires two running backs. Before we account for any flex positions, the league needs 24 running backs to fill those starting spots. In the simplest version of this exercise, RB1 through RB24 fill those positions and the replacement range begins immediately after them. If the same league requires three wide receivers, there are 36 mandatory wide receiver starting spots. The first player outside that group begins around WR37. If you start one tight end, there are 12 mandatory tight end spots. The initial replacement range begins around TE13. If you start one quarterback, there are 12 mandatory quarterback spots. The initial replacement range begins around QB13. That part is pretty straightforward.

But almost nobody plays in a league consisting only of fixed positional starting requirements. We have FLEX positions. We have SUPERFLEX positions. Some leagues have multiple FLEX spots. Some have four wide receiver spots. Some have two tight ends. Some have a dedicated WR/TE flex. The deeper you go into dynasty formats, the more complicated the lineup requirements can become. That matters tremendously.

Let's say our 12-team league has three regular FLEX positions. That's not three additional starting spots. That's 36 additional starting spots across the league. Those 36 spots can potentially be occupied by running backs, wide receivers or tight ends. We don't want to arbitrarily decide ahead of time that 18 of those spots belong to running backs and 18 belong to wide receivers. We want the scoring environment to tell us which players would optimally fill those spots. So after the mandatory positional starters are accounted for, we look at the next available eligible players. The strongest remaining players fill the FLEX positions until all 36 league-wide spots are allocated.

SUPERFLEX works the same way, except quarterbacks are eligible too. If there are 12 SUPERFLEX spots across a 12-team league, the next available quarterbacks, running backs, wide receivers and tight ends compete for those positions. In most conventional Superflex environments, quarterbacks are going to absorb a lot of that demand, which is exactly why the replacement level at quarterback changes so dramatically between 1QB and Superflex.

This process gives us something extremely important. Actual positional demand. And actual positional demand gives us the framework for establishing replacement level. That is where WAR and the Lineup Optimizer start talking to each other. The [**Lineup Optimizer**](https://www.ddfantasyfootball.com/tools/flex-optimization) is telling us, based on the league format and the scoring environment, how those starting positions should optimally be filled. WAR can then take those same positional demands and ask how much production players are generating above the corresponding replacement levels. That's the foundation of the entire model. Your league tells us what matters.

[image](https://tdxnsmiepqkbfpbcemdt.supabase.co/functions/v1/article-image?path=sections%2F1789813548999-lg6eaa.png)

[image](https://tdxnsmiepqkbfpbcemdt.supabase.co/functions/v1/article-image?path=sections%2F1789813586444-gob2yn.png)

## Replacement Value Should Change When Your League Changes

This is one of the reasons I have always been interested in WAR as a fantasy football concept. People want universal answers in dynasty. How many quarterbacks should I roster? How many wide receivers should I start? How valuable is an elite tight end? How much does running back matter? Should I build around wide receivers? How much more valuable is quarterback in Superflex? The problem is that the correct answer to almost all of those questions begins with:

What is your league format?

A 10-team start-8 league is not a 12-team start-12 league.
A 12-team 1QB league is not a 12-team Superflex league.
A league requiring two wide receivers is not the same as one requiring four.
A league with one FLEX isn't the same as one with four FLEX positions.
A league giving tight ends an additional point per reception isn't the same as a standard PPR league.
A four-point passing touchdown league isn't the same scoring environment as a six-point passing touchdown league.

Those aren't minor details.

Those settings change positional demand, replacement level, weekly scoring distributions and ultimately the amount of advantage an elite player can create. So when you sync your league with the WAR tool, we're not trying to fit your league into a universal fantasy football answer. We're trying to calculate the answer for your league. That philosophy hasn't changed. What has changed is what we do with the player performances once replacement level is established.

## How the Previous WAR Calculation Worked

The old WAR formula could assign positive or negative WAR to essentially every player performance. Let's use running back again.

Suppose the format tells us that the relevant replacement level sits around RB25. A player performing like RB23 is above that threshold. A player performing like RB70 is obviously well below it. The old model would calculate the difference. If the player was above replacement, he generated positive WAR. If the player was below replacement, he generated negative WAR. Then we repeated that process across the season.

For the elite players, most of those calculations were positive. For the really poor players, most were negative. For players somewhere in the middle, there might be a combination of both. At the end, the positives and negatives were added together and we ended up with a season-long net WAR number. That's what you would see when you ran the old WAR calculation. And again, that worked in spirit. The best players generally rose to the top. The worst players generally fell toward the bottom. We were measuring performance against replacement and converting that advantage or disadvantage into an expected-win metric.

But there was one problem that became increasingly difficult for me to ignore:

The formula didn't know whether you actually used the player. It knew what the player scored. It knew what replacement scored. It didn't know what you did with that information. It didn't know whether RB23 was locked into your starting lineup every week. It didn't know whether RB70 was your RB8 and never came remotely close to your starting lineup. It didn't know whether your backup quarterback sat on your bench for 15 weeks before becoming an emergency starter for two games. Yet those players could all continue accumulating positive or negative WAR. That made sense if our only goal was creating one season-long statistical value for every player. It made less sense when I tried to connect WAR to how we actually construct and manage dynasty rosters.

## The Missing Piece Was the Starting Lineup

This is where the Lineup Optimizer really forced me to rethink WAR.

We have actual lineup requirements. That sounds almost stupidly obvious, but it's incredibly important. You don't receive the fantasy points scored by every player on your roster. You receive the points scored by the players you start. Your bench matters for all kinds of reasons. It gives you depth. It protects you from injuries. It gives you optionality. It holds future value. It gives you players who may become starters later. But the bench does not score points for your fantasy lineup today.

If my WR7 scores 28 points while sitting on my bench, those 28 points don't count. If he scores four points while sitting on my bench, those four points don't hurt me either. That's the part I wanted WAR to understand. The old formula could look at that four-point performance, compare it with replacement and assign negative value. But my fantasy team didn't capture that negative value. I didn't start him. Nothing happened to my lineup. That's where the new formula fundamentally changes how we're thinking about WAR.

Fantasy Football Happens One Week at a Time. Consider a very simple example. Let's say the replacement-level running back in your league is expected to produce 10 fantasy points.

Your running back scores 30 points in Week 1.
Then he scores five points in Week 2.

If we treat those two weeks as one combined sample, the player scored 35 fantasy points while replacement produced 20. We could say he finished 15 points above replacement. Mathematically, there's nothing wrong with that. But that isn't how you experienced those performances.

In Week 1, your player scored 30.
You received a 20-point advantage over replacement in that specific matchup.

Then Week 2 happened.
He scored five.

You didn't receive 17.5 points in both weeks. You didn't get to move five points from the 30-point performance into the five-point performance to smooth everything out. You got a massive spike in one matchup and a bad performance in another. Those are different fantasy events. That matters.

If we're trying to understand the value a player can make available to a fantasy lineup, I don't want the five-point performance in Week 2 retroactively erasing part of the enormous advantage that existed in Week 1. The spike happened. The value existed. So the new WAR model evaluates these things weekly.

[image](https://tdxnsmiepqkbfpbcemdt.supabase.co/functions/v1/article-image?path=sections%2F1789818820963-z2sfea.png)

[image](https://tdxnsmiepqkbfpbcemdt.supabase.co/functions/v1/article-image?path=sections%2F1789814332618-cm9c6f.png)

Cam Ward in Week 1 - Below Replacement & 0.00 WAR

## Available WAR Now Has a Weekly Zero Floor

For the player-level WAR calculation, we compare the player's weekly score with the replacement threshold for his position. If he exceeds replacement, he generates positive WAR. If he does not exceed replacement, his available WAR for that week is zero.

The simplified concept is:

Weekly Available WAR = Max(0, Player Points − Replacement Points) × Wins Per Point

The Max(0) part is the fundamental change. Go back to our example.

Replacement is 10.
Week 1 is 30.
The player generated 20 points above replacement.

Week 2 is five.
The raw difference is negative five, but for available player WAR, that becomes zero. The Week 1 advantage remains intact.

Now, I want to be careful with the terminology here because this is where there is a really important second layer. This does not mean negative WAR has disappeared. Negative WAR absolutely still matters. But it matters when you capture it.

## Start the Player and You Capture the Result

This is the single biggest idea I want people to take away from this article. If you start a player, you capture his WAR—positive or negative. If you don't start him, your captured WAR from that player is zero. That is the heart of this new model. Let's use a three-week example because I think this explains it better than anything else.

Replacement-level production is 10 fantasy points.
In Week 1, your player scores 25.
You start him.

He produced 15 points above replacement, and you put that performance into your lineup. You capture the positive WAR associated with those 15 points.

Week 2 arrives and he scores six.
But you benched him.

The performance was four points below replacement, but it didn't hurt your fantasy lineup because you didn't use it. Your captured WAR from that player is zero.

Then Week 3 arrives.
He scores seven points.
This time, you started him.

Now the below-replacement performance matters. You chose to put seven points into a starting spot where the league's replacement baseline was 10. You captured the negative. That means your captured WAR for Week 3 is negative. This is much closer to the way fantasy football actually works.

A player doesn't hurt your weekly fantasy score because he had a terrible game on your bench. He hurts you when you start the terrible game. A player doesn't help your weekly fantasy score because he scored 30 on your bench. He helps you when you start the 30.

## Available WAR and Captured WAR Are Not the Same Thing

I think separating these concepts is going to become increasingly important as we continue developing the tool.

Available WAR tells us how much positive above-replacement production a player generated. Captured WAR tells us how much positive or negative WAR actually entered your starting lineup. Those numbers can be very different.

Suppose you own a volatile wide receiver.

Over four weeks he scores:

25
6
27
8

Let's say replacement is 10.

His available WAR comes from the 25-point and 27-point performances. Those are the weeks in which he created meaningful above-replacement value. But what did you capture?

Maybe you started him in Weeks 1 and 3. Fantastic.

You captured the spikes and avoided the bad performances.

Maybe you benched him after Week 1, missed the 27 in Week 3, and started the six and eight. That's a completely different experience.

The player didn't change. His available WAR didn't change. Your captured WAR changed dramatically. That's incredibly interesting to me because now we're not only measuring players. We're beginning to measure how effectively a dynasty roster can convert the value it contains into actual starting-lineup production.

[image](https://tdxnsmiepqkbfpbcemdt.supabase.co/functions/v1/article-image?path=sections%2F1789818368751-d4u4xk.png)

In Week 1, had I started Bo Nix

## Think About the Backup Quarterback

Quarterback is probably the easiest position to use when explaining why the old approach bothered me.

Imagine an NFL backup quarterback who starts two games. For 15 weeks, you aren't starting him in fantasy football. You're not debating him against Josh Allen or Joe Burrow or whoever your normal quarterback is. He isn't starting for his own NFL team. He may technically appear in the weekly data, but from the perspective of your fantasy starting lineup, he's effectively irrelevant.

Under a system that continually measures every performance against replacement and assigns negative WAR, those weeks can drag his season-long number down. Why? You never used him. Then the starter gets hurt and suddenly the backup starts an NFL game. Now everything changes.

He scores 24 fantasy points. You might legitimately start him in Superflex. Now he can generate usable value. If you start him and he beats replacement, you capture positive WAR. If you start him and he gives you eight points when replacement is 15, you capture negative WAR. If you leave him on the bench, your captured WAR is zero. That's exactly how I want the model thinking about these players. It isn't asking whether the backup quarterback was "good" over a 17-week season. It's asking when his production became relevant to a fantasy lineup and what happened when you actually used it.

This concepts provides a more accurate view of how each position group (four positions plus flex) is distributed across an entire season and reflective of how they would be optimally used on a weekly sit/start basis.

[image](https://tdxnsmiepqkbfpbcemdt.supabase.co/functions/v1/article-image?path=sections%2F1789815004523-7uatlt.png)

2025 WAR (Total) Using the New Method

## This Is Also Why the New Graphs Look Completely Different

Once you stop allowing every below-replacement performance to accumulate negative player WAR, the shape of the WAR graph changes.

Dramatically.

Instead of the positional curves eventually continuing into negative territory, they descend toward zero and flatten.

That's intentional.

The player-level graph is showing us where positive above-replacement production existed.

When a player no longer generated any positive above-replacement WAR, the curve reaches zero.

And when we put the positions on the same graph, we get a really interesting picture of how useful production is distributed across the player pool.

[INSERT GRAPH: 2025 WAR PER GAME — QB, RB, WR, TE]

We tested this using a 2025 sample in a 12-team, start-12 format with full PPR, an additional full point of tight end premium and five-point passing touchdowns.

What I found interesting wasn't simply who ranked first.

It was the shape of the curves.

At the very top of that sample, the TE1 season was around 0.159 WAR per game. RB1 was around 0.150. WR1 was around 0.135. QB1 was around 0.090.

Now, please don't take that sentence and turn it into "Scott says tight ends are more valuable than quarterbacks."

That's not what the graph is saying.

It's telling us about the advantage those particular performances created relative to replacement in that particular league environment.

That's exactly what WAR should do.

## The Shape of a Position Matters More Than One Number

As we moved down the running back curve, the elite end was extremely steep.

The top running backs created enormous advantages over replacement, but that advantage fell fairly quickly as we moved deeper into the position. That's useful. It tells us that, in this particular environment, having one of the truly elite running back performances created a very different weekly advantage from simply having another startable running back.

Wide receiver behaved differently.

The top wide receivers obviously created significant value, but the position had a much longer tail of positive WAR. In our sample, positive WR WAR stretched dramatically farther down the positional ranks than it did at quarterback, running back or tight end. Again, I don't interpret that as saying WR120 is suddenly some massively valuable dynasty asset. That's not what we're measuring. What it tells me is that useful wide receiver performances are distributed across a much deeper pool of players.

That matters for lineup decisions.
It matters for best ball.
It matters for roster construction.

And it matters when we start thinking about how much dynasty value we want trapped in our WR5, WR6 and WR7 when we may not have enough starting spots to access all of it.

[image](https://tdxnsmiepqkbfpbcemdt.supabase.co/functions/v1/article-image?path=sections%2F1789818491139-ya8027.png)

DJ Moore (WR29, 0.55 WAR) vs Kayshon Boutte in 2025, Best Ball WAR

[image](https://tdxnsmiepqkbfpbcemdt.supabase.co/functions/v1/article-image?path=sections%2F1789815585711-471tj6.png)

2025 Darren Waller vs Christian Watson (WR23, .046) in a PPR (with +1.0 TE Premium)

## Tight End Gets Really Interesting

Tight end is another position where the graph tells a story that raw fantasy points don't always make obvious.

In a tight end premium league, the very best receiving tight ends can create an enormous advantage over replacement. That's what we saw at the top of the curve. But the curve also falls. That means the question isn't simply, "Do tight ends score a lot of fantasy points?"

The better question is:

How much more does my tight end score than the replacement-level tight end I could otherwise put into that spot? That's the whole idea of WAR.

If TE1 scores 20 points and replacement scores 10, that's a massive advantage.

If WR1 scores 20 and replacement-level WR production is 14 because the player pool is deeper, those identical 20-point raw scores aren't creating the same advantage.

That's why raw points alone aren't enough.

## Quarterback May Be the Most Interesting Change

Quarterback looks different under this methodology, and I'm going to spend more time talking about that on shows and streams because I think there's a lot to unpack.

In the sample we ran, the QB curve reached zero faster than the other positions.

Again, that does not mean quarterbacks don't matter. And it absolutely does not mean quarterbacks don't have dynasty value. It means the distribution of positive weekly value above the league-specific replacement threshold looked different.

Quarterback also provides the cleanest example of why weekly calculation matters. The position contains a relatively small number of players who are actually viable fantasy starters in any given week. Below them are backups who may have essentially no opportunity until something changes.

When opportunity changes, WAR changes. That's much more useful to me than accumulating negative WAR for players we never would have considered starting.

## 2025 QB WAR Per Game in a Super Juiced QB Scoring League

[image](https://tdxnsmiepqkbfpbcemdt.supabase.co/functions/v1/article-image?path=sections%2F1789815915068-yqj7qo.png)

## 2025 QB Points Per Game in a Super Juiced QB Scoring League

[image](https://tdxnsmiepqkbfpbcemdt.supabase.co/functions/v1/article-image?path=sections%2F1789815992648-rtcsbj.png)

## Total WAR Adds Availability Back Into the Equation

### 12 X 10 Superflex League (1/2/2/1/3/1) with .25 Point Per Carry

WAR per game is useful because it tells us the rate at which a player created above-replacement value when he played. But it isn't the entire story. We also need total WAR.

Total WAR simply stacks the weekly WAR performances across the season.

If a player generates:

0.12 WAR in Week 1
0.00 in Week 2
0.18 in Week 3
0.07 in Week 4

those numbers accumulate.

That's his total available WAR.

Because negative available WAR is floored at zero each week, a poor performance doesn't erase the useful value generated by a previous spike. This naturally produces larger season-long positive WAR totals than a model where negative weeks continually subtract from positive weeks.

That's intentional.

We're measuring the cumulative amount of useful above-replacement production a player made available. WAR per game then gives us the rate. Total WAR gives us the accumulation. A player who generates 0.15 WAR per game for eight games may be incredibly impactful when healthy. Another player might generate 0.11 per game but do it for 17 games. The second player can accumulate more total WAR. Availability matters.

I want both numbers because they answer different questions.

[image](https://tdxnsmiepqkbfpbcemdt.supabase.co/functions/v1/article-image?path=sections%2F1789816227181-ovc058.png)

## WAR Does Not Mean Literal Head-to-Head Wins

Another thing I want to make very clear is what the word "wins" means in this context.

If a player produces 2.0 WAR, I'm not saying you can look at your 7-7 fantasy team and say, "Without him, I would've gone 5-9."

That's not how this works.

Fantasy wins are binary. WAR is continuous.

You could have a player score 40 points in a week where you win by 70. You could have him score 40 in a week where your opponent somehow scores 200 and you lose anyway. You could have him generate a relatively small advantage above replacement in a matchup you win by 0.4. The player doesn't control your opponent. So WAR isn't trying to recreate the literal standings.

Instead, we convert points above replacement into expected-win value based on the scoring environment and expected weekly scoring variance of the league. In other words, we're trying to quantify how much that player's production moved the needle toward winning relative to replacement.

So when you see 2.0 WAR, think:

Approximately two wins' worth of expected value above replacement under this model.

Don't think:

This player literally changed exactly two losses into wins.

Those are different statements.

## Now We Can Talk About WAR Capture Rate

This is where I think the concept can get really powerful.

If we know how much useful WAR existed on your roster and we know what actually entered your lineup, we can start calculating a WAR capture rate.

Suppose the players on your roster generated 10 units of available positive WAR over a period of time.

You didn't capture all of it. Maybe you captured eight. Now we can say that, in a simplified sense, you captured 80% of the positive WAR that was available to you.

This starts sounding familiar if you've ever looked at lineup efficiency or potential points.

[image](https://tdxnsmiepqkbfpbcemdt.supabase.co/functions/v1/article-image?path=sections%2F1789816532510-6llofv.png)

## Potential Points Is Already Teaching Us This Lesson

### In 2025, I captured 3216.15 out of 3565.00 for a 90.2% Efficiency

Go into Sleeper or My Fantasy League and look at your potential points compared with your actual points in a Lineup League (not Best Ball).

Maybe your optimal lineup could have scored 2,000 points.
You actually scored 1,600.
That's 80% efficiency.

What happened to the other 400 points?

They existed.
They were on your roster.
You didn't get them into your starting lineup.
That's valuable information.

But raw potential points treats fantasy points as fantasy points. WAR allows us to take that concept and look at it through the lens of replacement value.

Instead of simply asking, "How many points did I leave on the bench?" we can begin asking:

How much meaningful above-replacement value did I leave on the bench? That's a different question. And for dynasty roster construction, I think it may eventually be a more interesting one.

## Your Bench Can Have Great Players and Still Be Inefficient

This is where we get into actual roster construction.

Let's imagine two dynasty teams. Both have roughly the same amount of total market value.

Team A is absolutely loaded at wide receiver. It has seven or eight legitimate starting options, but the league only allows it to start four or five of them in a given week. Every week, there is useful production sitting on the bench.

Team B may not have quite as much raw market value at wide receiver, but its value is distributed differently. It has strong starters at the positions it needs to fill and enough depth to survive injuries without continually leaving huge amounts of usable production on the bench.

Which roster is better?

That's not a question WAR can answer by itself. But WAR can show us something extremely important about the problem.

How much of Team A's value can actually enter the lineup? That's the part of roster construction I want the Lineup Optimizer and WAR to expose.

There is a point where depth becomes redundancy. That doesn't mean depth is bad. It means depth has an opportunity cost. Understand why you have it.

With that said, you still need a bench.

I want to make this incredibly clear because I know how quickly fantasy arguments can turn into extremes. I'm not saying you should have 12 starters and nobody else. Of course you need backups. You need injury insulation. You need backup quarterbacks. You need contingent running backs. You need developmental players. You need rookies who aren't ready yet. You need future value and liquidity. You need players who may not generate any WAR today but could become enormous difference-makers or value-gainers six weeks from now.

Dynasty value and WAR are not the same thing.

A rookie quarterback sitting behind an established starter might have significant dynasty market value and generate zero current WAR. That's completely fine. WAR isn't telling you to cut him. It's telling you what his production is currently doing relative to replacement.

The question becomes whether the value on your bench is serving a purpose.

Is it protecting your lineup?
Is it creating future upside?
Is it appreciating?

Or have you simply accumulated six players who all do the same thing while leaving another starting position weak? That's where this becomes actionable.

## Negative Captured WAR Shows Us the Other Side

We also need to talk about the negative side because I don't want "WAR has a zero floor" to become shorthand for "negative WAR doesn't exist."

It absolutely exists in captured WAR.

Suppose your replacement-level RB is worth 10 points.

Your RB2 scores four.
You started him.
You captured a six-point deficit relative to replacement.
That's negative captured WAR.
If you had left him on the bench?
Zero captured WAR from that player.

That doesn't mean your team magically received replacement production. It means that particular player's performance did not enter your starting lineup. Whatever player you actually started in that spot is the player whose result should be evaluated. That's a crucial distinction. The bench is not producing negative captured WAR. Your starters can.

And this is where we can eventually identify some really interesting roster weaknesses. Maybe you aren't losing efficiency because you keep benching great performances. Maybe you're losing it because you are forced to start below-replacement players every week. That's a completely different problem. One problem is lineup decision-making. The other is roster construction.

WAR can help us separate them.

[image](https://tdxnsmiepqkbfpbcemdt.supabase.co/functions/v1/article-image?path=sections%2F1789817030946-2hzmi0.png)

2025 results, I left way too much production unused (3rd in PF, 8th in Potential Points/Efficiency)

## A Bad Decision and a Bad Roster Aren't the Same Thing

Imagine I have five good wide receivers and can start four.

Every week I choose the wrong one. That's a lineup efficiency problem. The value existed. I failed to capture it.

Now imagine I have to start four wide receivers and only own three who regularly produce above replacement.

That's not primarily a sit-start problem. I don't have enough usable production. That's a roster-construction problem.

Those are different diagnoses.

If we're just looking at final fantasy points, both teams may look inefficient. But once we start looking at available WAR, captured WAR and where the negative captured WAR is coming from, we can begin understanding why. That's where I want these tools to go.

## Best Ball Gives Us the Cleanest Version of Available WAR

Best ball is particularly interesting because the lineup is optimized automatically.

You don't have to predict the spike. Your WR6 scores 31 points? If that score belongs in your optimal lineup, the system captures it.

Your RB5 unexpectedly scores two touchdowns? If he belongs in the optimal lineup, those points count.

That's why weekly WAR works so naturally in best ball. The format itself is trying to capture the best available production.

In managed lineup leagues, however, you have to make the decision before the games.

That's why I think separating available WAR from captured WAR becomes so useful.

Best ball is largely about creating enough available spike value for the lineup mechanism to capture.

Managed leagues require you to create the value and then correctly deploy it.

Same players. Different capture mechanism. That's an incredibly important roster-construction distinction.

## WAR and the Lineup Optimizer Are Finally Speaking the Same Language

This was ultimately the reason I wanted to change the formula.

I didn't want the Lineup Optimizer telling us how a league should optimally distribute starting resources while WAR was evaluating every player as though every weekly performance had equal access to the lineup.

Those ideas don't fit together. Now they do.

The Lineup Optimizer asks:

Where should my resources be deployed based on the requirements of this league?

WAR asks:

How much value did players generate above the replacement levels created by those requirements?

Available WAR asks:

How much useful positive value existed?

Captured WAR asks:

What happened when I actually put players into my lineup?

WAR capture rate asks:

How effectively did I convert the useful production available on my roster into starting-lineup value?

Now we're talking about the same ecosystem. And that's what I wanted. The Goal Is Not Another Player Ranking This may be the most important philosophical point of the entire project. I don't care about creating another number just so we can rank players 1 through 300.

We already have rankings.
We have ADP.
We have market values.
We have trade databases.
We have production metrics.
We have a million different ways to argue that one player should be ranked three spots ahead of another.

That's not what interests me about WAR. I want WAR to help answer roster-construction questions. If I invest heavily at running back, how much weekly advantage can I actually create? How quickly does that advantage disappear as I move down the position? How deep does useful WR production extend? What does TE premium actually do to the difference between an elite tight end and replacement? How much does Superflex move the quarterback baseline? How much of the useful production on my roster am I actually capturing? How much dynasty value do I have sitting in places where I can't regularly use it? Where am I being forced to start below-replacement production?

Those are the questions I care about. Because those questions can change what I do with my dynasty roster.

## Eventually, I Want This to Become Forward-Looking

Right now, a lot of what we're discussing is retrospective. We can look at what happened last week. We can look at the last month. We can look at an entire season. We can look at which players generated WAR, which performances entered your lineup and where you left useful production on the bench.

But eventually, I want to think about this prospectively too.

What does my roster look like next week? What does it look like over the next three weeks? Where am I projected to have more usable production than I can start? Where am I projected to have a lineup hole? Where am I one injury away from being forced to capture negative WAR? Where do I have a player on my bench whose projected usefulness would be much greater on somebody else's roster?

Those are trade questions.
Those are roster-construction questions.

And that is where a metric like WAR becomes much more than a historical leaderboard.

## Play Around With Your Own League

This is probably the best thing you can do after reading this. Sync your teams to the [**Portfolio**](https://www.ddfantasyfootball.com/portfolio/overview).

Don't just look at the WAR results from one league. Sync multiple leagues. Look at a shallow league and then look at a deep one. Look at 1QB and Superflex. Look at start-8 and start-12. Look at standard tight end scoring and then look at tight end premium. Look at what happens when your league requires two wide receivers versus four.

Look at WAR per game.
Look at total WAR.
Look at where the positional curves flatten.
Then look at your own roster.

Look at your actual points versus your potential points. Look at the players who repeatedly created useful performances on your bench. Look at the players you kept putting into your lineup who failed to clear replacement. Those are inefficiencies. Not all inefficiencies are fixable, and not all of them are bad.

Sometimes you have great depth because you're preparing for the playoffs. Sometimes you're holding an injured player's backup because the contingent upside is worth more than the points you're sacrificing today. Sometimes you're rebuilding and don't care about maximizing current-season WAR at all. Context still matters. WAR isn't here to tell you how to play dynasty. It's here to give you better information about what your roster is actually doing.

\#WAR#Roster#Construction#Lineup#Dynasty#Optimizer

## How did this one land?

41 reads · 1 reaction

🔥**1**💯**0**👏**0**😂**0**😮**0**🤔**0**

🔥 💯 👏 😂 😮 🤔

svg

## Comments

**0**

0/4000**Post comment**

No comments yet — be the first.

## About the author

[Scott Connor profile photo](https://tdxnsmiepqkbfpbcemdt.supabase.co/functions/v1/article-image?path=authors%2F1787503133987-uor0em.jpg)

**Scott Connor**

Part of the DD Fantasy Football team — writing dynasty strategy, data breakdowns and roster analysis. Catch more from the crew on the shows, podcasts and in the Discord.

## Subscribe & listen

New episodes and shows every week — subscribe on YouTube and your podcast app.

- [svg](https://www.youtube.com/@DDFantasyFootball)[**DDFB YouTube**](https://www.youtube.com/@DDFantasyFootball)[Daily fantasy football content](https://www.youtube.com/@DDFantasyFootball)
- [svg](https://www.youtube.com/@WakeUpGMGP)[**Wake up with Ray & J**](https://www.youtube.com/@WakeUpGMGP)[Morning show on YouTube](https://www.youtube.com/@WakeUpGMGP)
- [svg](https://podcasts.apple.com/au/podcast/dd-fantasy-football-radio/id1642403980)[**Apple Podcasts**](https://podcasts.apple.com/au/podcast/dd-fantasy-football-radio/id1642403980)[DD Fantasy Football Radio](https://podcasts.apple.com/au/podcast/dd-fantasy-football-radio/id1642403980)
- [svg](https://open.spotify.com/search/DD%20Fantasy%20Football%20Radio)[**Spotify**](https://open.spotify.com/search/DD%20Fantasy%20Football%20Radio)[DD Fantasy Football Radio](https://open.spotify.com/search/DD%20Fantasy%20Football%20Radio)

[DD Fantasy Football](https://www.ddfantasyfootball.com/)[**DD Fantasy Football**](https://www.ddfantasyfootball.com/) ([image](https://www.ddfantasyfootball.com/lovable-uploads/aaf06e67-fc2d-419b-bd44-77a80b03c241.png))

The real game drives every roster decision here. Trust the trinity.

[svg](https://x.com/DestinationDevy "X")[svg](https://www.youtube.com/@RayGQue "YouTube")[svg](https://www.instagram.com/destinationdevy/ "Instagram")[svg](https://podcasts.apple.com/au/podcast/dd-fantasy-football-radio/id1642403980 "Apple Podcasts")[svg](https://open.spotify.com/search/DD%20Fantasy%20Football%20Radio "Spotify")

#### Fantasy

- [Trinity Tracker](https://www.ddfantasyfootball.com/trinity/trinity-score-vs-ppg)
- [Projections](https://www.ddfantasyfootball.com/projections)
- [Portfolio](https://www.ddfantasyfootball.com/portfolio/overview)
- [War Machine](https://www.ddfantasyfootball.com/war/sleeper)
- [Trade Room](https://www.ddfantasyfootball.com/tools/trading)
- [Lineup Optimizer](https://www.ddfantasyfootball.com/tools/flex-optimization)
- [Draft Copilot](https://www.ddfantasyfootball.com/draft-copilot)
- [Leaders](https://www.ddfantasyfootball.com/leaders)
- [Rankings](https://www.ddfantasyfootball.com/rankings)
- [ADP](https://www.ddfantasyfootball.com/adp)
- [Vibes](https://www.ddfantasyfootball.com/tools/vibes)
- [Players](https://www.ddfantasyfootball.com/players)
- [Scout Team](https://www.ddfantasyfootball.com/fantasy/scout-team)
- [Community Lean](https://www.ddfantasyfootball.com/fantasy/community-lean)
- [Scott Fish Bowl](https://www.ddfantasyfootball.com/sfb)

#### Football

- [News](https://www.ddfantasyfootball.com/nfl/news)
- [Matchups](https://www.ddfantasyfootball.com/matchups)
- [College Football](https://www.ddfantasyfootball.com/football/college-football)
- [Depth Chart](https://www.ddfantasyfootball.com/football/depth-charts)
- [Statistics](https://www.ddfantasyfootball.com/football/statistics)
- [Free Agency](https://www.ddfantasyfootball.com/free-agency)
- [Advanced Charting](https://www.ddfantasyfootball.com/football/advanced-charts)
- [Contract Value](https://www.ddfantasyfootball.com/football/contract-value)
- [Strength of Schedule](https://www.ddfantasyfootball.com/nfl/strength-of-schedule)
- [2027 NFL Big Board](https://www.ddfantasyfootball.com/nfl-bigboard-2027)
- [2027 FF Big Board](https://www.ddfantasyfootball.com/ff-bigboard-2027)

#### Community

- [Wake up with Ray & J](https://www.youtube.com/@WakeUpGMGP)
- [RayGQue](https://www.youtube.com/@RayGQue/videos)
- [DDFB Youtube](https://www.ddfantasyfootball.com/media/ddffb)
- [DDFB Radio](https://www.ddfantasyfootball.com/media/podcast)
- [Discord](https://discord.gg/jointhesquad)
- [Tutorials](https://www.ddfantasyfootball.com/community)
- [Advice](https://www.ddfantasyfootball.com/tools/advice)

#### Fun

- [Signal Caller](https://www.ddfantasyfootball.com/fun/trivia)
- [Leaderboard](https://www.ddfantasyfootball.com/fun/leaderboard)
- [Games Hub](https://www.ddfantasyfootball.com/fun)
- [Dynasty Connections](https://www.ddfantasyfootball.com/fun/connections)
- [Red Zone Reveal](https://www.ddfantasyfootball.com/fun/redzone)
- [Survival Draft](https://www.ddfantasyfootball.com/fun/survival)
- [Gridiron Invaders](https://www.ddfantasyfootball.com/fun/invaders)

© 2026 DD Fantasy Football. All rights reserved.

[Terms](https://www.ddfantasyfootball.com/terms-of-use)[Privacy](https://www.ddfantasyfootball.com/privacy-policy)[Gambling](https://www.ddfantasyfootball.com/gambling-disclaimer)