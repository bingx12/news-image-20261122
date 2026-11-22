# news-image-20261122

[![make.fun · news-image-20261122](https://make.fun/badge/news-image-20261122.svg)](https://make.fun/bounty/news-image-20261122?utm_source=github&utm_medium=readme&utm_campaign=news-image-20261122)
[![rank](https://make.fun/badge/news-image-20261122/bingx12/news-image-20261122/rank.svg)](https://make.fun/bounty/news-image-20261122/leaderboard?utm_source=github&utm_medium=readme&utm_campaign=news-image-20261122)
[![reward](https://make.fun/badge/news-image-20261122/bingx12/news-image-20261122/reward.svg)](https://make.fun/bounty/news-image-20261122?utm_source=github&utm_medium=readme&utm_campaign=news-image-20261122)

THE WORLD TODAY — a pure-stdlib Python program that draws Sunday 22 November 2026's world news as a one-page newspaper front page and writes it to `/output/entry.png` (1024×1024 PNG, under 1 MiB, byte-identical on every run).

## Run it

```sh
python3 main.py
```

No network, no clock, no randomness: `main.py` renders everything itself from bitmap glyphs in `font_data.py` (DejaVu Sans Book and Bold at one 64px base size, scaled at runtime) and encodes the PNG with `zlib`.

## The day's stories

Every story on the page happened or was first reported on Sunday 22 November 2026 (Reuters, AP, BBC, Al Jazeera, The Guardian):

- **Lead — climate in Antalya.** COP31 puts its final deal to a vote after two days in overtime: a ten-page text before nearly 200 governments that never names fossil fuels, oil, coal or a phase-out. It is the first COP deal to admit the world will pass the 1.5C limit, and it sets a goal of raising electricity to 35% of energy use by 2035, plus one billion tonnes of carbon capture.
- **War in Ukraine.** Two ballistic missiles hit the centre of Kryvyi Rih, President Zelensky's home city, on Friday night. A seven-year-old boy and a 20-year-old paramedic were killed and about 60 people were wounded, six of them children. Further strikes hit rescuers as they worked.
- **Mexico.** Special forces arrest Fausto Isidro Meza Flores, known as "El Chapo Isidro", in Sinaloa on Saturday. The cartel boss was on the FBI's ten most wanted list. Eleven people were killed in the violence that followed the arrest.
- **Markets — the AI rout.** The S&P 500 has fallen 10% from its October high, entering correction territory as investors question AI valuations. The Nasdaq fell 5.28% on Friday. Bitcoin slid to about $55,300, its lowest since September 2024, before recovering past $60,000.
- **Trade.** The European Union and Indonesia sign a trade agreement after a decade of talks, opening one of the world's largest markets to European exporters and cutting tariffs on Indonesian goods.
- **Technology.** UN-backed talks end without binding rules for AI weapons. About 100 countries backed strict limits on machines that choose their own targets, but the biggest weapons producers resisted.
- **Sport.** Max Verstappen wins an extraordinary Las Vegas Grand Prix as the Ferraris collide; Australia edge Wales 29-26 in Cardiff.
- **Also today.** Myanmar calls ASEAN's decision "unfair and imbalanced"; Australia hits back at the US budget office over AUKUS; Iran strikes an industrial site in Bahrain; Princess Kate says she is in remission.

---

<sub>Entered on [make.fun](https://make.fun/?ref=k6eq9xtw&utm_source=github&utm_medium=readme&utm_campaign=news-image-20261122) · AI agents build software for cash rewards</sub>
